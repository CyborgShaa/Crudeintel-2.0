import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import streamlit as st
import asyncio
from datetime import datetime, timedelta, timezone
import time

# Import your custom modules
try:
    from database import get_recent_articles
    from news_fetcher import fetch_rss_news, fetch_newsapi_news
    from summarizer import process_unanalyzed_articles
    from telegram_alerts import send_alerts, send_test_alert
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

# Initialize session state for auto-refresh
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Title and header
st.title("🛢️ CrudeIntel 2.0")
st.markdown("**Real-time Crude Oil News Monitoring & Analysis**")

# Add system status indicator
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown("### System Status")
with col2:
    st.success("🟢 Online")
with col3:
    last_update = datetime.now().strftime("%H:%M:%S")
    st.caption(f"Last updated: {last_update}")

# Sidebar controls
st.sidebar.header("🎛️ Controls")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5 min)", value=True)

if st.sidebar.button("🔄 Fetch New Articles"):
    with st.spinner("Fetching latest news..."):
        try:
            rss_count = fetch_rss_news()
            api_count = fetch_newsapi_news()
            total_added = rss_count + api_count
            if total_added > 0:
                st.sidebar.success(f"✅ Added {total_added} new articles")
                st.rerun()  # Refresh to show new articles
            else:
                st.sidebar.info("ℹ️ No new articles found")
        except Exception as e:
            st.sidebar.error(f"❌ Error fetching articles: {str(e)}")

if st.sidebar.button("🤖 Process with AI"):
    with st.spinner("Analyzing articles with AI..."):
        try:
            processed = process_unanalyzed_articles()
            if processed > 0:
                st.sidebar.success(f"✅ Processed {processed} articles")
                st.rerun()  # Refresh to show updated summaries
            else:
                st.sidebar.info("ℹ️ No articles to process")
        except Exception as e:
            st.sidebar.error(f"❌ Error processing articles: {str(e)}")

if st.sidebar.button("📱 Send Alerts"):
    with st.spinner("Sending Telegram alerts..."):
        try:
            alerts = asyncio.run(send_alerts())
            if alerts > 0:
                st.sidebar.success(f"✅ Sent {alerts} alerts")
            else:
                st.sidebar.info("ℹ️ No new alerts to send")
        except Exception as e:
            st.sidebar.error(f"❌ Error sending alerts: {str(e)}")

if st.sidebar.button("🧪 Test Telegram"):
    with st.spinner("Testing Telegram connection..."):
        try:
            success = asyncio.run(send_test_alert())
            if success:
                st.sidebar.success("✅ Test alert sent!")
            else:
                st.sidebar.error("❌ Test alert failed")
        except Exception as e:
            st.sidebar.error(f"❌ Telegram test error: {str(e)}")

# Add sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ System Info")
st.sidebar.caption("• Auto-fetch every 5 minutes")
st.sidebar.caption("• AI analysis on demand")
st.sidebar.caption("• Instant Telegram alerts")

# Main content
st.markdown("---")

# Get recent articles with error handling
try:
    articles = get_recent_articles(100)  # Get more articles for better filtering
except Exception as e:
    st.error(f"Error loading articles: {e}")
    articles = []

# Statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📰 Total Articles", len(articles))

with col2:
    analyzed = len([a for a in articles if a.get('summary')])
    st.metric("🤖 Analyzed", analyzed)

with col3:
    if articles:
        try:
            recent = len([a for a in articles if (datetime.now(timezone.utc) - datetime.fromisoformat(a['published_at'].replace('Z', '+00:00'))).days < 1])
            st.metric("📅 Last 24h", recent)
        except:
            st.metric("📅 Last 24h", "N/A")
    else:
        st.metric("📅 Last 24h", 0)

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
    if articles:
        sources = ["All"] + sorted(list(set([a['source'] for a in articles if a.get('source')])))
    else:
        sources = ["All"]
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

# Sort by published date (newest first)
try:
    filtered_articles = sorted(filtered_articles, 
                             key=lambda x: datetime.fromisoformat(x['published_at'].replace('Z', '+00:00')), 
                             reverse=True)
except:
    pass  # Keep original order if sorting fails

# Limit results
filtered_articles = filtered_articles[:limit]

# Display articles
if filtered_articles:
    st.markdown(f"📊 Showing **{len(filtered_articles)}** articles")
    
    for i, article in enumerate(filtered_articles):
        # Sentiment emoji
        sentiment_emoji = {
            'Bullish': '🟢',
            'Bearish': '🔴',
            'Neutral': '⚪'
        }
        
        emoji = sentiment_emoji.get(article.get('sentiment'), '⚪')
        
        # Article container with better styling
        with st.container():
            if i > 0:  # Don't add divider before first article
                st.markdown("---")
            
            # Title and sentiment
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if article.get('link'):
                    st.markdown(f"### [{article['title']}]({article['link']})")
                else:
                    st.markdown(f"### {article['title']}")
            
            with col2:
                if article.get('sentiment'):
                    st.markdown(f"## {emoji} {article['sentiment']}")
                else:
                    st.markdown("## ⚪ Pending")
            
            # Summary or description
            if article.get('summary'):
                st.markdown(f"**🤖 AI Summary:** {article['summary']}")
            elif article.get('description'):
                description = article['description']
                if len(description) > 300:
                    description = description[:300] + "..."
                st.markdown(f"**📝 Description:** {description}")
            else:
                st.markdown("*No description available*")
            
            # Metadata with better formatting
            try:
                published_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                time_ago = datetime.now(timezone.utc) - published_date
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.caption(f"📡 **Source:** {article.get('source', 'Unknown')}")
                
                with col2:
                    st.caption(f"🕒 **Published:** {published_date.strftime('%b %d, %Y %H:%M UTC')}")
                
                with col3:
                    if time_ago.days > 0:
                        st.caption(f"⏰ **Age:** {time_ago.days} day{'s' if time_ago.days != 1 else ''} ago")
                    elif time_ago.seconds > 3600:
                        hours = time_ago.seconds // 3600
                        st.caption(f"⏰ **Age:** {hours} hour{'s' if hours != 1 else ''} ago")
                    else:
                        minutes = max(1, time_ago.seconds // 60)
                        st.caption(f"⏰ **Age:** {minutes} min ago")
            except Exception as e:
                st.caption(f"📅 **Published:** {article.get('published_at', 'Unknown')}")

else:
    st.info("🔍 No articles found with the selected filters. Try adjusting your filter criteria or fetch new articles.")

# Footer
st.markdown("---")
st.markdown("### 💡 Tips")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - **🔄 Fetch Articles**: Get latest crude oil news from multiple sources
    - **🤖 AI Analysis**: Generate summaries and sentiment analysis
    """)

with col2:
    st.markdown("""
    - **📱 Alerts**: Send important news via Telegram
    - **🧪 Test**: Verify your Telegram bot connection
    """)

# Auto-refresh logic (improved)
if auto_refresh:
    current_time = time.time()
    if current_time - st.session_state.last_refresh > 300:  # 5 minutes = 300 seconds
        st.session_state.last_refresh = current_time
        st.rerun()
    else:
        # Show countdown to next refresh
        time_left = 300 - (current_time - st.session_state.last_refresh)
        minutes_left = int(time_left // 60)
        seconds_left = int(time_left % 60)
        st.caption(f"🔄 Next auto-refresh in: {minutes_left}:{seconds_left:02d}")
        
        # Use a placeholder to refresh the countdown
        time.sleep(1)
        st.rerun()
        
