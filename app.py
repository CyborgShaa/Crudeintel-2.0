import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import streamlit as st
import asyncio
from datetime import datetime, timezone, timedelta
import time
import hashlib
import json

# Import your custom modules
try:
    from news_fetcher import fetch_news_live
    from newsapi_fetcher import fetch_newsapi_articles_live  
    from summarizer import analyze_article_live
    from telegram_alerts import send_alert_live, send_test_alert
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

# Global variables for session state
if 'articles_cache' not in st.session_state:
    st.session_state.articles_cache = []
if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = None
if 'alerted_articles' not in st.session_state:
    st.session_state.alerted_articles = set()

def get_article_id(article):
    """Generate unique ID for article to prevent duplicates"""
    return hashlib.md5((article.get('title', '') + article.get('link', '')).encode()).hexdigest()

def is_recent_article(published_at_str, hours_limit=1):
    """Check if article is within the specified hours limit"""
    try:
        if not published_at_str:
            return False
        
        published_date = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        time_diff = datetime.now(timezone.utc) - published_date
        return time_diff.total_seconds() / 3600 <= hours_limit
    except:
        return False

def fetch_and_analyze_news():
    """Fetch news from all sources and analyze with AI"""
    with st.spinner("🔄 Fetching latest crude oil news..."):
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
        
        # Remove duplicates based on article ID
        unique_articles = {}
        for article in all_articles:
            article_id = get_article_id(article)
            if article_id not in unique_articles:
                unique_articles[article_id] = article
        
        final_articles = list(unique_articles.values())
        st.write(f"📊 Total unique articles: {len(final_articles)}")
        
        # AI Analysis for all articles
        if final_articles:
            with st.spinner("🤖 Analyzing articles with AI..."):
                analyzed_count = 0
                for i, article in enumerate(final_articles):
                    try:
                        # Show progress
                        if i % 5 == 0:
                            st.write(f"🧠 Analyzing article {i+1}/{len(final_articles)}...")
                        
                        # Get AI analysis
                        summary, sentiment = analyze_article_live(
                            article.get('title', ''),
                            article.get('description', '')
                        )
                        
                        if summary and sentiment:
                            article['summary'] = summary
                            article['sentiment'] = sentiment
                            analyzed_count += 1
                        
                    except Exception as e:
                        st.write(f"AI analysis error for article {i+1}: {e}")
                        continue
                
                st.write(f"🤖 AI Analysis complete: {analyzed_count} articles processed")
        
        return final_articles

# Title and header
st.title("🛢️ CrudeIntel 2.0")
st.markdown("**Real-time Crude Oil News Monitoring & Analysis - Live Mode**")

# System status
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("### System Status")
with col2:
    st.success("🟢 Online - Live Fetching")
with col3:
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Sidebar controls
st.sidebar.header("🎛️ Controls")

# Fetch button
if st.sidebar.button("🔄 Fetch Latest News"):
    articles = fetch_and_analyze_news()
    st.session_state.articles_cache = articles
    st.session_state.last_fetch_time = datetime.now()
    st.rerun()

# Auto-fetch on page load if cache is empty or old
if (not st.session_state.articles_cache or 
    not st.session_state.last_fetch_time or 
    (datetime.now() - st.session_state.last_fetch_time).seconds > 1800):  # 30 minutes
    
    st.info("🔄 Auto-fetching latest news...")
    articles = fetch_and_analyze_news()
    st.session_state.articles_cache = articles
    st.session_state.last_fetch_time = datetime.now()
    st.rerun()

# Get articles from cache
articles = st.session_state.articles_cache

# Send alerts for recent articles
if st.sidebar.button("📱 Send Recent Alerts"):
    if articles:
        recent_articles = [a for a in articles if is_recent_article(a.get('published_at'))]
        alert_count = 0
        
        with st.spinner("📱 Sending alerts for recent news..."):
            for article in recent_articles:
                article_id = get_article_id(article)
                
                # Skip if already alerted
                if article_id in st.session_state.alerted_articles:
                    continue
                
                # Only alert for non-neutral sentiment
                sentiment = article.get('sentiment', '').lower()
                if sentiment in ['bullish', 'bearish']:
                    try:
                        success = asyncio.run(send_alert_live(article))
                        if success:
                            st.session_state.alerted_articles.add(article_id)
                            alert_count += 1
                    except Exception as e:
                        st.sidebar.error(f"Alert error: {e}")
        
        if alert_count > 0:
            st.sidebar.success(f"✅ Sent {alert_count} alerts")
        else:
            st.sidebar.info("ℹ️ No new alerts to send")
    else:
        st.sidebar.warning("No articles available for alerts")

# Test Telegram
if st.sidebar.button("🧪 Test Telegram"):
    try:
        success = asyncio.run(send_test_alert())
        if success:
            st.sidebar.success("✅ Test alert sent!")
        else:
            st.sidebar.error("❌ Test alert failed")
    except Exception as e:
        st.sidebar.error(f"Telegram test error: {e}")

# Clear cache
if st.sidebar.button("🗑️ Clear Cache"):
    st.session_state.articles_cache = []
    st.session_state.alerted_articles = set()
    st.sidebar.success("Cache cleared!")
    st.rerun()

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ System Info")
st.sidebar.caption("• Live fetching - no database")
st.sidebar.caption("• Auto-fetch on page load")
st.sidebar.caption("• AI analysis in real-time")
st.sidebar.caption("• Alerts for last 1 hour news only")
st.sidebar.caption("• Duplicate prevention enabled")

# Main content
st.markdown("---")

# Statistics
if articles:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📰 Total Articles", len(articles))
    
    with col2:
        analyzed = len([a for a in articles if a.get('summary')])
        st.metric("🤖 Analyzed", analyzed)
    
    with col3:
        recent = len([a for a in articles if is_recent_article(a.get('published_at'))])
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
            ["All", "Bullish", "Bearish", "Neutral", "Unanalyzed"]
        )
    
    with col2:
        sources = ["All"] + sorted(list(set([a.get('source', 'Unknown') for a in articles])))
        source_filter = st.selectbox("📡 Filter by Source", sources)
    
    with col3:
        limit = st.selectbox("📊 Show Articles", [10, 25, 50, 100], index=1)
    
    # Apply filters
    filtered_articles = articles
    
    if sentiment_filter != "All":
        if sentiment_filter == "Unanalyzed":
            filtered_articles = [a for a in filtered_articles if not a.get('summary')]
        else:
            filtered_articles = [a for a in filtered_articles if a.get('sentiment') == sentiment_filter]
    
    if source_filter != "All":
        filtered_articles = [a for a in filtered_articles if a.get('source') == source_filter]
    
    # Sort by published date
    try:
        filtered_articles = sorted(filtered_articles, 
                                 key=lambda x: datetime.fromisoformat(x.get('published_at', '1970-01-01T00:00:00Z').replace('Z', '+00:00')), 
                                 reverse=True)
    except:
        pass
    
    filtered_articles = filtered_articles[:limit]
    
    # Display articles
    if filtered_articles:
        st.markdown(f"📊 Showing **{len(filtered_articles)}** articles")
        
        for i, article in enumerate(filtered_articles):
            title = article.get('title', 'No Title')
            link = article.get('link', '#')
            sentiment = article.get('sentiment', 'Pending')
            summary = article.get('summary', '')
            description = article.get('description', '')
            source = article.get('source', 'Unknown')
            published_at = article.get('published_at', 'Unknown')
            
            # Recent article indicator
            is_recent = is_recent_article(published_at)
            recent_badge = "🔥 RECENT" if is_recent else ""
            
            sentiment_emoji = {'Bullish': '🟢', 'Bearish': '🔴', 'Neutral': '⚪'}
            emoji = sentiment_emoji.get(sentiment, '⚪')
            
            with st.container():
                if i > 0:
                    st.markdown("---")
                
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if link and link != '#':
                        st.markdown(f"### [{title}]({link}) {recent_badge}")
                    else:
                        st.markdown(f"### {title} {recent_badge}")
                
                with col2:
                    st.markdown(f"## {emoji} {sentiment}")
                
                if summary:
                    st.markdown(f"**🤖 AI Summary:** {summary}")
                elif description:
                    if len(description) > 300:
                        description = description[:300] + "..."
                    st.markdown(f"**📝 Description:** {description}")
                else:
                    st.markdown("*No description available*")
                
                # Metadata
                try:
                    if published_at != 'Unknown':
                        published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        time_ago = datetime.now(timezone.utc) - published_date
                        
                        col1, col2, col3 = st.columns(3)
                        col1.caption(f"📡 **Source:** {source}")
                        col2.caption(f"🕒 **Published:** {published_date.strftime('%b %d, %Y %H:%M UTC')}")
                        
                        if time_ago.days > 0:
                            col3.caption(f"⏰ **Age:** {time_ago.days} day{'s' if time_ago.days != 1 else ''} ago")
                        elif time_ago.seconds > 3600:
                            hours = time_ago.seconds // 3600
                            col3.caption(f"⏰ **Age:** {hours} hour{'s' if hours != 1 else ''} ago")
                        else:
                            minutes = max(1, time_ago.seconds // 60)
                            col3.caption(f"⏰ **Age:** {minutes} min ago")
                except:
                    st.caption(f"📡 **Source:** {source}")
    else:
        st.info("🔍 No articles found with current filters.")

else:
    st.info("🔄 Click 'Fetch Latest News' to load articles or refresh the page!")

# Footer
st.markdown("---")
st.markdown("### 💡 Live Mode Features")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - **🔄 Auto-fetch**: Fresh news on every page load
    - **🤖 Real-time AI**: Instant analysis and sentiment
    - **🔥 Recent alerts**: Only last 1 hour news
    """)

with col2:
    st.markdown("""
    - **🚫 No duplicates**: Smart duplicate prevention
    - **💾 No database**: Zero storage complexity
    - **⚡ Super fast**: Direct memory operations
    """)
    
        
                            
                        
                    
        
    
        
