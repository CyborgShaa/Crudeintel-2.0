import streamlit as st
import asyncio
from datetime import datetime, timedelta
from database import get_recent_articles
from news_fetcher import fetch_rss_news, fetch_newsapi_news
from summarizer import process_unanalyzed_articles
from telegram_alerts import send_alerts, send_test_alert

# Page config
st.set_page_config(
    page_title="CrudeIntel 2.0",
    page_icon="🛢️",
    layout="wide"
)

# Title and header
st.title("🛢️ CrudeIntel 2.0")
st.markdown("**Real-time Crude Oil News Monitoring & Analysis**")

# Sidebar controls
st.sidebar.header("Controls")

if st.sidebar.button("🔄 Fetch New Articles"):
    with st.spinner("Fetching latest news..."):
        rss_count = fetch_rss_news()
        api_count = fetch_newsapi_news()
        st.sidebar.success(f"Added {rss_count + api_count} new articles")

if st.sidebar.button("🤖 Process with AI"):
    with st.spinner("Analyzing articles with AI..."):
        processed = process_unanalyzed_articles()
        st.sidebar.success(f"Processed {processed} articles")

if st.sidebar.button("📱 Send Alerts"):
    with st.spinner("Sending Telegram alerts..."):
        alerts = asyncio.run(send_alerts())
        st.sidebar.success(f"Sent {alerts} alerts")

if st.sidebar.button("🧪 Test Telegram"):
    with st.spinner("Testing Telegram connection..."):
        success = asyncio.run(send_test_alert())
        if success:
            st.sidebar.success("✅ Test alert sent!")
        else:
            st.sidebar.error("❌ Test alert failed")

# Main content
col1, col2, col3 = st.columns(3)

# Get recent articles
articles = get_recent_articles(50)

# Statistics
with col1:
    st.metric("Total Articles", len(articles))

with col2:
    analyzed = len([a for a in articles if a.get('summary')])
    st.metric("Analyzed Articles", analyzed)

with col3:
    recent = len([a for a in articles if (datetime.now() - datetime.fromisoformat(a['published_at'].replace('Z', '+00:00'))).days < 1])
    st.metric("Last 24 Hours", recent)

# Filters
st.subheader("📰 Latest News")

col1, col2, col3 = st.columns(3)

with col1:
    sentiment_filter = st.selectbox(
        "Filter by Sentiment",
        ["All", "Bullish", "Bearish", "Neutral", "Unanalyzed"]
    )

with col2:
    source_filter = st.selectbox(
        "Filter by Source",
        ["All"] + list(set([a['source'] for a in articles if a['source']]))
    )

with col3:
    limit = st.selectbox("Show Articles", [10, 25, 50, 100], index=1)

# Apply filters
filtered_articles = articles

if sentiment_filter != "All":
    if sentiment_filter == "Unanalyzed":
        filtered_articles = [a for a in filtered_articles if not a.get('summary')]
    else:
        filtered_articles = [a for a in filtered_articles if a.get('sentiment') == sentiment_filter]

if source_filter != "All":
    filtered_articles = [a for a in filtered_articles if a['source'] == source_filter]

# Limit results
filtered_articles = filtered_articles[:limit]

# Display articles
if filtered_articles:
    for article in filtered_articles:
        # Sentiment emoji
        sentiment_emoji = {
            'Bullish': '🟢',
            'Bearish': '🔴',
            'Neutral': '⚪'
        }
        
        emoji = sentiment_emoji.get(article.get('sentiment', 'Neutral'), '⚪')
        
        # Article container
        with st.container():
            st.markdown("---")
            
            # Title and sentiment
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if article['link']:
                    st.markdown(f"### [{article['title']}]({article['link']})")
                else:
                    st.markdown(f"### {article['title']}")
            
            with col2:
                if article.get('sentiment'):
                    st.markdown(f"## {emoji} {article['sentiment']}")
                else:
                    st.markdown("## ⚪ Unanalyzed")
            
            # Summary
            if article.get('summary'):
                st.markdown(f"**Summary:** {article['summary']}")
            else:
                st.markdown(f"**Description:** {article['description'][:200]}...")
            
            # Metadata
            published_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
            time_ago = datetime.now() - published_date.replace(tzinfo=None)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.caption(f"**Source:** {article['source']}")
            
            with col2:
                st.caption(f"**Published:** {published_date.strftime('%Y-%m-%d %H:%M UTC')}")
            
            with col3:
                if time_ago.days > 0:
                    st.caption(f"**Age:** {time_ago.days} days ago")
                elif time_ago.seconds > 3600:
                    st.caption(f"**Age:** {time_ago.seconds // 3600} hours ago")
                else:
                    st.caption(f"**Age:** {time_ago.seconds // 60} minutes ago")

else:
    st.info("No articles found with the selected filters.")

# Auto-refresh
st.markdown("---")
st.caption("💡 **Tip:** Use the sidebar controls to fetch new articles and analyze them with AI. The system automatically sends Telegram alerts for important news.")

# Auto-refresh every 5 minutes (for demo purposes)
import time
time.sleep(1)  # Small delay to prevent too frequent refreshes
st.rerun()
                  
