import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import streamlit as st
import asyncio
from datetime import datetime, timezone, timedelta
import time
import hashlib

# Import your custom modules (no database needed)
try:
    from news_fetcher import fetch_all_news
    from summarizer import analyze_article_sentiment
    from telegram_alerts import send_recent_alerts
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="CrudeIntel 2.0",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for caching and auto-refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = 0
if 'cached_articles' not in st.session_state:
    st.session_state.cached_articles = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Title and header
st.title("🛢️ CrudeIntel 2.0")
st.markdown("**Real-time Crude Oil News Monitoring & Analysis - Live Fetch**")

# Add system status indicator
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("### System Status")
with col2:
    st.success("🟢 Online - Live Data")
with col3:
    last_update = datetime.now().strftime("%H:%M:%S")
    st.caption(f"Last updated: {last_update}")

# Sidebar controls
st.sidebar.header("🎛️ Controls")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5 min)", value=True)

# Fetch and analyze button
if st.sidebar.button("🔄 Fetch & Analyze News") or len(st.session_state.cached_articles) == 0:
    with st.spinner("Fetching latest crude oil news..."):
        try:
            st.sidebar.write("📡 Fetching from all sources...")
            
            # Fetch fresh news from all sources
            articles = fetch_all_news()
            
            st.sidebar.write(f"📰 Found {len(articles)} articles")
            st.sidebar.write("🤖 Processing with AI...")
            
            # Process articles with AI immediately
            processed_articles = []
            progress_bar = st.sidebar.progress(0)
            
            for i, article in enumerate(articles):
                # Add AI analysis
                try:
                    sentiment, summary = analyze_article_sentiment(
                        article.get('title', ''),
                        article.get('description', '')
                    )
                    article['sentiment'] = sentiment
                    article['summary'] = summary
                except Exception as e:
                    article['sentiment'] = 'Neutral'
                    article['summary'] = 'AI analysis unavailable'
                
                processed_articles.append(article)
                progress_bar.progress((i + 1) / len(articles))
            
            # Cache the processed articles
            st.session_state.cached_articles = processed_articles
            st.session_state.processing_complete = True
            st.session_state.last_refresh = time.time()
            
            st.sidebar.success(f"✅ Processed {len(processed_articles)} articles")
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")

# Send alerts for recent news
if st.sidebar.button("📱 Send Recent Alerts"):
    with st.spinner("Sending alerts for recent news..."):
        try:
            if st.session_state.cached_articles:
                alerts_sent = asyncio.run(send_recent_alerts(st.session_state.cached_articles))
                if alerts_sent > 0:
                    st.sidebar.success(f"✅ Sent {alerts_sent} alerts")
                else:
                    st.sidebar.info("ℹ️ No new alerts to send")
            else:
                st.sidebar.warning("⚠️ Fetch news first")
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")

# Manual refresh
if st.sidebar.button("🔄 Manual Refresh"):
    st.session_state.cached_articles = []
    st.rerun()

# Add sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ System Info")
st.sidebar.caption("• Live data fetch - no storage")
st.sidebar.caption("• Instant AI analysis")
st.sidebar.caption("• 1-hour alert window")
st.sidebar.caption("• Duplicate prevention")

# Main content
st.markdown("---")

# Get articles from cache
articles = st.session_state.cached_articles

if not articles:
    st.info("🔍 Click 'Fetch & Analyze News' to load the latest crude oil news!")
else:
    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📰 Live Articles", len(articles))

    with col2:
        analyzed = len([a for a in articles if a.get('summary') and a.get('summary') != 'AI analysis unavailable'])
        st.metric("🤖 AI Analyzed", analyzed)

    with col3:
        recent = len([a for a in articles if a.get('published_at') and 
                     (datetime.now(timezone.utc) - datetime.fromisoformat(a.get('published_at', '').replace('Z', '+00:00'))).total_seconds() < 3600])
        st.metric("📅 Last Hour", recent)

    with col4:
        bullish_count = len([a for a in articles if a.get('sentiment') == 'Bullish'])
        bearish_count = len([a for a in articles if a.get('sentiment') == 'Bearish'])
        if bullish_count > bearish_count:
            st.metric("📊 Market Mood", "🟢 Bullish", bullish_count)
        elif bearish_count > bullish_count:
            st.metric("📊 Market Mood", "🔴 Bearish", bearish_count)
        else:
            st.metric("📊 Market Mood", "⚪ Neutral", "Balanced")

    # Filters
    st.subheader("📰 Latest Crude Oil News")

    col1, col2, col3 = st.columns(3)

    with col1:
        sentiment_filter = st.selectbox(
            "🎭 Filter by Sentiment",
            ["All", "Bullish", "Bearish", "Neutral"]
        )

    with col2:
        sources = ["All"] + sorted(list(set([a.get('source', 'Unknown') for a in articles])))
        source_filter = st.selectbox("📡 Filter by Source", sources)

    with col3:
        time_filter = st.selectbox("⏰ Filter by Time", 
                                  ["All", "Last Hour", "Last 6 Hours", "Last 24 Hours"])

    # Apply filters
    filtered_articles = articles

    if sentiment_filter != "All":
        filtered_articles = [a for a in filtered_articles if a.get('sentiment') == sentiment_filter]

    if source_filter != "All":
        filtered_articles = [a for a in filtered_articles if a.get('source') == source_filter]

    if time_filter != "All":
        now = datetime.now(timezone.utc)
        hours = {"Last Hour": 1, "Last 6 Hours": 6, "Last 24 Hours": 24}[time_filter]
        cutoff = now - timedelta(hours=hours)
        filtered_articles = [a for a in filtered_articles if a.get('published_at') and 
                           datetime.fromisoformat(a.get('published_at', '').replace('Z', '+00:00')) > cutoff]

    # Sort by published date (newest first)
    try:
        filtered_articles = sorted(filtered_articles, 
                                 key=lambda x: datetime.fromisoformat(x.get('published_at', '1970-01-01T00:00:00Z').replace('Z', '+00:00')), 
                                 reverse=True)
    except:
        pass

    # Display articles
    if filtered_articles:
        st.markdown(f"📊 Showing **{len(filtered_articles)}** articles")
        
        for i, article in enumerate(filtered_articles[:50]):  # Limit to 50 for performance
            title = article.get('title', 'No Title')
            link = article.get('link', '#')
            sentiment = article.get('sentiment', 'Neutral')
            summary = article.get('summary', '')
            description = article.get('description', '')
            source = article.get('source', 'Unknown')
            published_at = article.get('published_at', 'Unknown')
            
            # Sentiment emoji
            sentiment_emoji = {'Bullish': '🟢', 'Bearish': '🔴', 'Neutral': '⚪'}
            emoji = sentiment_emoji.get(sentiment, '⚪')
            
            with st.container():
                if i > 0:
                    st.markdown("---")
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if link and link != '#':
                        st.markdown(f"### [{title}]({link})")
                    else:
                        st.markdown(f"### {title}")
                
                with col2:
                    st.markdown(f"## {emoji} {sentiment}")
                
                # AI Summary or description
                if summary and summary != 'AI analysis unavailable':
                    st.markdown(f"**🤖 AI Summary:** {summary}")
                elif description:
                    if len(description) > 300:
                        description = description[:300] + "..."
                    st.markdown(f"**📝 Description:** {description}")
                
                # Metadata
                try:
                    if published_at != 'Unknown':
                        pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        time_ago = datetime.now(timezone.utc) - pub_date
                        
                        col1, col2, col3 = st.columns(3)
                        col1.caption(f"📡 **Source:** {source}")
                        col2.caption(f"🕒 **Published:** {pub_date.strftime('%b %d, %H:%M UTC')}")
                        
                        if time_ago.total_seconds() < 3600:
                            minutes = max(1, int(time_ago.total_seconds() // 60))
                            col3.caption(f"⏰ **{minutes} min ago** 🔥")
                        elif time_ago.days == 0:
                            hours = int(time_ago.total_seconds() // 3600)
                            col3.caption(f"⏰ **{hours}h ago**")
                        else:
                            col3.caption(f"⏰ **{time_ago.days}d ago**")
                except:
                    st.caption(f"📡 **Source:** {source}")

    else:
        st.info("🔍 No articles match your filters. Try adjusting the criteria.")

# Auto-refresh logic
if auto_refresh and len(st.session_state.cached_articles) > 0:
    current_time = time.time()
    if current_time - st.session_state.last_refresh > 300:  # 5 minutes
        st.session_state.cached_articles = []
        st.rerun()
    else:
        time_left = 300 - (current_time - st.session_state.last_refresh)
        minutes_left = int(time_left // 60)
        seconds_left = int(time_left % 60)
        st.caption(f"🔄 Auto-refresh in: {minutes_left}:{seconds_left:02d}")
        
                            
                        
                    
        
    
        
