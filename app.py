import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import streamlit as st
import asyncio
from datetime import datetime, timezone, timedelta
import time

if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = 0

AUTO_REFRESH_INTERVAL = 300  # 5 mins
auto_refresh = st.sidebar.checkbox("Auto-refresh (5 min)", True)

current_time = time.time()
time_since_last = current_time - st.session_state['last_refresh']

# Conditionally rerun, but **call rerun only once and then stop execution immediately**
if auto_refresh and time_since_last > AUTO_REFRESH_INTERVAL:
    st.session_state['last_refresh'] = current_time
    st.experimental_rerun()

# Show countdown if not rerunning
if auto_refresh and time_since_last <= AUTO_REFRESH_INTERVAL:
    time_left = AUTO_REFRESH_INTERVAL - time_since_last
    minutes = int(time_left // 60)
    seconds = int(time_left % 60)
    st.sidebar.caption(f"Next auto-refresh in: {minutes}:{seconds:02d}")

# Put any further code **after** this block, NOT below the rerun call

# Import modules
try:
    from news_fetcher import fetch_news_live
    from newsapi_fetcher import fetch_newsapi_articles_live
    from summarizer import analyze_article_live
    from telegram_alerts import send_automatic_alerts, send_test_alert, get_alert_stats
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="CrudeIntel 2.0 - Enhanced",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if 'articles_cache' not in st.session_state:
    st.session_state.articles_cache = []
if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = None
if 'auto_alerts_enabled' not in st.session_state:
    st.session_state.auto_alerts_enabled = True

def filter_last_hour_articles(articles):
    """Filter articles to only include those from the last hour"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_articles = []
    
    for article in articles:
        try:
            published_at = article.get('published_at', '')
            if not published_at:
                continue
            published_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            if published_dt > cutoff_time:
                recent_articles.append(article)
        except:
            continue
    
    return recent_articles

def fetch_and_analyze_news():
    """Fetch news and analyze with AI - only last 1 hour"""
    with st.spinner("🔄 Fetching latest crude oil news (last 1 hour)..."):
        all_articles = []
        
        # Fetch from RSS sources
        st.write("📡 Fetching RSS sources...")
        try:
            rss_articles = fetch_news_live()
            all_articles.extend(rss_articles)
            st.write(f"📰 RSS: {len(rss_articles)} articles")
        except Exception as e:
            st.error(f"RSS fetch error: {e}")
        
        # Fetch from NewsAPI
        st.write("📡 Fetching NewsAPI...")
        try:
            api_articles = fetch_newsapi_articles_live()
            all_articles.extend(api_articles)
            st.write(f"📰 NewsAPI: {len(api_articles)} articles")
        except Exception as e:
            st.error(f"NewsAPI fetch error: {e}")
        
        # Filter to last 1 hour only
        recent_articles = filter_last_hour_articles(all_articles)
        st.write(f"⏰ Recent (last 1 hour): {len(recent_articles)} articles")
        
        # Remove duplicates
        unique_articles = {}
        for article in recent_articles:
            article_key = article.get('title', '') + article.get('link', '')
            if article_key not in unique_articles:
                unique_articles[article_key] = article
        
        final_articles = list(unique_articles.values())
        st.write(f"📊 Unique articles: {len(final_articles)}")
        
        # AI Analysis
        if final_articles:
            with st.spinner("🤖 Analyzing with Gemini AI..."):
                analyzed_count = 0
                for i, article in enumerate(final_articles):
                    try:
                        if i % 3 == 0:
                            st.write(f"🧠 Analyzing {i+1}/{len(final_articles)}...")
                        
                        summary, sentiment = analyze_article_live(
                            article.get('title', ''),
                            article.get('description', '')
                        )
                        
                        if summary and sentiment:
                            article['summary'] = summary
                            article['sentiment'] = sentiment
                            analyzed_count += 1
                        
                    except Exception as e:
                        st.write(f"AI error for article {i+1}: {e}")
                        continue
                
                st.write(f"🤖 AI Analysis: {analyzed_count} articles processed")
        
        return final_articles

# Title and header
st.title("🛢️ CrudeIntel 2.0 Enhanced")
st.markdown("**Real-time Crude Oil Intelligence - Last 1 Hour Focus**")

# Enhanced status
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.markdown("### System Status")
with col2:
    st.success("🟢 Live Mode")
with col3:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    st.info(f"⏰ Since {cutoff.strftime('%H:%M UTC')}")
with col4:
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

# Sidebar controls
st.sidebar.header("🎛️ Enhanced Controls")

# Auto-alerts toggle
st.session_state.auto_alerts_enabled = st.sidebar.checkbox(
    "🚨 Auto Telegram Alerts", 
    value=st.session_state.auto_alerts_enabled,
    help="Automatically send alerts for recent Bullish/Bearish news"
)

# Fetch and Alert button
if st.sidebar.button("🔄 Fetch & Auto Alert"):
    articles = fetch_and_analyze_news()
    st.session_state.articles_cache = articles
    st.session_state.last_fetch_time = datetime.now()
    
    # Send automatic alerts if enabled
    if st.session_state.auto_alerts_enabled and articles:
        with st.spinner("📱 Sending automatic alerts..."):
            alerts_sent = asyncio.run(send_automatic_alerts(articles))
            if alerts_sent > 0:
                st.sidebar.success(f"📱 Sent {alerts_sent} automatic alerts!")
            else:
                st.sidebar.info("📱 No alerts needed (neutral/old articles)")
    
    st.rerun()

# Manual test alert
if st.sidebar.button("🧪 Test Enhanced Alert"):
    with st.spinner("📱 Testing enhanced alert format..."):
        success = asyncio.run(send_test_alert())
        if success:
            st.sidebar.success("✅ Enhanced test alert sent!")
        else:
            st.sidebar.error("❌ Test alert failed")

# Alert statistics
alert_stats = get_alert_stats()
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Alert Stats")
st.sidebar.caption(f"• Total alerted: {alert_stats['total_alerted']}")
st.sidebar.caption(f"• Cache size: {alert_stats['cache_size']}")

# Auto-fetch on page load (but only if cache is empty or very old)
if (not st.session_state.articles_cache or 
    not st.session_state.last_fetch_time or 
    (datetime.now() - st.session_state.last_fetch_time).seconds > 900):  # 15 minutes
    
    st.info("🔄 Auto-fetching latest news from last 1 hour...")
    articles = fetch_and_analyze_news()
    st.session_state.articles_cache = articles
    st.session_state.last_fetch_time = datetime.now()
    
    # Auto-send alerts if enabled
    if st.session_state.auto_alerts_enabled and articles:
        alerts_sent = asyncio.run(send_automatic_alerts(articles))
        if alerts_sent > 0:
            st.success(f"📱 Auto-sent {alerts_sent} alerts for recent news!")
    
    st.rerun()

# Get articles from cache
articles = st.session_state.articles_cache

# Enhanced statistics
if articles:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📰 Last Hour Articles", len(articles))
    
    with col2:
        analyzed = len([a for a in articles if a.get('summary')])
        st.metric("🤖 AI Analyzed", analyzed)
    
    with col3:
        alertable = len([a for a in articles if a.get('sentiment') in ['Bullish', 'Bearish']])
        st.metric("🚨 Alert Worthy", alertable)
    
    with col4:
        bullish = len([a for a in articles if a.get('sentiment') == 'Bullish'])
        bearish = len([a for a in articles if a.get('sentiment') == 'Bearish'])
        if bullish > bearish:
            st.metric("📊 Hourly Mood", "🟢 Bullish", bullish)
        elif bearish > bullish:
            st.metric("📊 Hourly Mood", "🔴 Bearish", bearish)
        else:
            st.metric("📊 Hourly Mood", "⚪ Balanced", "Even")

    # Enhanced filters
    st.subheader("📰 Latest Hour Intelligence")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sentiment_filter = st.selectbox(
            "🎭 Sentiment Filter",
            ["All", "Bullish", "Bearish", "Neutral", "Unanalyzed"]
        )
    
    with col2:
        sources = ["All"] + sorted(list(set([a.get('source', 'Unknown') for a in articles])))
        source_filter = st.selectbox("📡 Source Filter", sources)
    
    with col3:
        limit = st.selectbox("📊 Show Count", [5, 10, 20, 50], index=1)
    
    # Apply filters
    filtered_articles = articles
    
    if sentiment_filter != "All":
        if sentiment_filter == "Unanalyzed":
            filtered_articles = [a for a in filtered_articles if not a.get('summary')]
        else:
            filtered_articles = [a for a in filtered_articles if a.get('sentiment') == sentiment_filter]
    
    if source_filter != "All":
        filtered_articles = [a for a in filtered_articles if a.get('source') == source_filter]
    
    # Sort by published date (newest first)
    try:
        filtered_articles = sorted(filtered_articles, 
                                 key=lambda x: datetime.fromisoformat(x.get('published_at', '1970-01-01T00:00:00Z').replace('Z', '+00:00')), 
                                 reverse=True)
    except:
        pass
    
    filtered_articles = filtered_articles[:limit]
    
    # Enhanced article display
    if filtered_articles:
        st.markdown(f"📊 Showing **{len(filtered_articles)}** recent articles")
        
        for i, article in enumerate(filtered_articles):
            title = article.get('title', 'No Title')
            link = article.get('link', '#')
            sentiment = article.get('sentiment', 'Pending')
            summary = article.get('summary', '')
            description = article.get('description', '')
            source = article.get('source', 'Unknown')
            published_at = article.get('published_at', 'Unknown')
            
            # Time since published
            try:
                pub_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                time_ago = datetime.now(timezone.utc) - pub_dt
                minutes_ago = max(1, int(time_ago.total_seconds() / 60))
                time_badge = f"🕒 {minutes_ago}min ago"
            except:
                time_badge = "🕒 Recent"
            
            sentiment_emoji = {'Bullish': '🟢', 'Bearish': '🔴', 'Neutral': '⚪'}
            emoji = sentiment_emoji.get(sentiment, '⚪')
            
            with st.container():
                if i > 0:
                    st.markdown("---")
                
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    if link and link != '#':
                        st.markdown(f"### [{title}]({link}) {time_badge}")
                    else:
                        st.markdown(f"### {title} {time_badge}")
                
                with col2:
                    st.markdown(f"## {emoji} {sentiment}")
                
                if summary:
                    st.markdown(f"**🤖 AI Summary:** {summary}")
                elif description:
                    if len(description) > 300:
                        description = description[:300] + "..."
                    st.markdown(f"**📝 Description:** {description}")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"📡 **Source:** {source}")
                with col2:
                    if sentiment in ['Bullish', 'Bearish']:
                        st.caption("🚨 **Alert Sent**")
                    else:
                        st.caption("😐 **No Alert**")
    else:
        st.info("🔍 No articles match current filters.")

else:
    st.info("🔄 No recent articles found. News will auto-fetch on next page load!")

# Enhanced footer
st.markdown("---")
st.markdown("### 🚀 Enhanced Features")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - **⏰ Last Hour Focus**: Only shows news from past 60 minutes
    - **🚨 Auto Telegram Alerts**: Beautiful formatted alerts
    - **🤖 Real-time AI**: Gemini analysis on every article
    """)

with col2:
    st.markdown("""
    - **🚫 Zero Duplicates**: Smart duplicate prevention
    - **📱 Enhanced Format**: Professional alert styling
    - **⚡ 15-min Ready**: Perfect for cron job automation
    """)

# Auto-refresh info
st.caption(f"🔄 Auto-fetch enabled - checks every 15 minutes for fresh news")
