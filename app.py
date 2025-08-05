import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import streamlit as st
import asyncio
from datetime import datetime, timezone, timedelta
import time

# Page config MUST be first Streamlit command
st.set_page_config(
    page_title="CrudeIntel 2.0 - Multi-Bot Enhanced",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modules
try:
    from news_fetcher import fetch_news_live
    from newsapi_fetcher import fetch_newsapi_articles_live
    from summarizer import analyze_article_live
    from telegram_alerts import send_automatic_alerts, send_test_alert, get_alert_stats
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Initialize session state
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
        st.write(f"⏰ Recent (last 3 hour): {len(recent_articles)} articles")
        
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
st.title("🛢️ CrudeIntel 2.0 Multi-Bot Enhanced")
st.markdown("**Real-time Crude Oil Intelligence - Multi-Bot Telegram Alerts**")

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
st.sidebar.header("🎛️ Multi-Bot Controls")

# Auto-alerts toggle
st.session_state.auto_alerts_enabled = st.sidebar.checkbox(
    "🚨 Auto Multi-Bot Alerts", 
    value=st.session_state.auto_alerts_enabled,
    help="Automatically send alerts to all configured Telegram bots for Bullish/Bearish news"
)

# Manual fetch and alert button
if st.sidebar.button("🔄 Fetch & Send Multi-Bot Alerts"):
    articles = fetch_and_analyze_news()
    st.session_state.articles_cache = articles
    st.session_state.last_fetch_time = datetime.now()
    
    # Send automatic alerts if enabled
    if st.session_state.auto_alerts_enabled and articles:
        with st.spinner("📱 Sending multi-bot alerts..."):
            alerts_sent = asyncio.run(send_automatic_alerts(articles))
            if alerts_sent > 0:
                st.sidebar.success(f"📱 Sent {alerts_sent} alerts across all bots!")
            else:
                st.sidebar.info("📱 No alerts needed (neutral/old articles)")

# Manual test alert to all bots
if st.sidebar.button("🧪 Test All Bots"):
    with st.spinner("📱 Testing all telegram bots..."):
        success = asyncio.run(send_test_alert())
        if success:
            st.sidebar.success("✅ Test alerts sent to all configured bots!")
        else:
            st.sidebar.error("❌ Some or all test alerts failed")

# Enhanced Alert statistics with multi-bot info
try:
    alert_stats = get_alert_stats()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Multi-Bot Alert Stats")
    st.sidebar.caption(f"• Total alerted: {alert_stats['total_alerted']}")
    st.sidebar.caption(f"• Configured bots: {alert_stats['configured_bots']}")
    st.sidebar.caption(f"• Cache size: {alert_stats['cache_size']}")
    
    # Bot status indicators
    if alert_stats['configured_bots'] > 0:
        st.sidebar.success(f"🤖 {alert_stats['configured_bots']} bots ready")
    else:
        st.sidebar.error("⚠️ No bots configured")
        
except Exception as e:
    st.sidebar.error(f"Stats error: {e}")

# Auto-fetch on page load (controlled, only once per session or every 15 minutes)
current_time = datetime.now()
should_auto_fetch = False

if not st.session_state.articles_cache:
    should_auto_fetch = True
    reason = "No cached articles"
elif not st.session_state.last_fetch_time:
    should_auto_fetch = True
    reason = "No previous fetch time"
elif (current_time - st.session_state.last_fetch_time).total_seconds() > 900:  # 15 minutes
    should_auto_fetch = True
    reason = "Cache expired (15+ minutes old)"

if should_auto_fetch:
    st.info(f"🔄 Auto-fetching latest news ({reason})...")
    articles = fetch_and_analyze_news()
    st.session_state.articles_cache = articles
    st.session_state.last_fetch_time = current_time
    
    # Auto-send multi-bot alerts if enabled
    if st.session_state.auto_alerts_enabled and articles:
        try:
            alerts_sent = asyncio.run(send_automatic_alerts(articles))
            if alerts_sent > 0:
                st.success(f"📱 Auto-sent {alerts_sent} alerts to all configured bots!")
        except Exception as e:
            st.error(f"Auto-alert error: {e}")

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
        st.metric("🚨 Multi-Bot Ready", alertable)
    
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
                        st.caption("🚨 **Multi-Bot Alert**")
                    else:
                        st.caption("😐 **No Alert**")
    else:
        st.info("🔍 No articles match current filters.")

else:
    st.info("🔄 No recent articles found. Click 'Fetch & Send Multi-Bot Alerts' to load fresh news!")

# Enhanced cache info with multi-bot status
if st.session_state.last_fetch_time:
    cache_age = (datetime.now() - st.session_state.last_fetch_time).total_seconds() / 60
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⏰ Cache & Bot Info")
    st.sidebar.caption(f"• Last fetch: {cache_age:.1f} min ago")
    st.sidebar.caption(f"• Articles cached: {len(st.session_state.articles_cache)}")
    
    # Show environment status
    bot_tokens = [
        ("Bot 1", "TELEGRAM_BOT_TOKEN_1"),
        ("Bot 2", "TELEGRAM_BOT_TOKEN_2"), 
        ("Bot 3", "TELEGRAM_BOT_TOKEN_3")
    ]
    
    st.sidebar.markdown("### 🤖 Bot Status")
    for bot_name, env_var in bot_tokens:
        if os.getenv(env_var):
            st.sidebar.caption(f"• {bot_name}: ✅ Configured")
        else:
            st.sidebar.caption(f"• {bot_name}: ❌ Missing")

# Enhanced footer
st.markdown("---")
st.markdown("### 🚀 Multi-Bot Enhanced Features")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - **⏰ Last Hour Focus**: Only shows news from past 60 minutes
    - **🚨 Multi-Bot Alerts**: Simultaneous alerts to 3+ bots
    - **🤖 Real-time AI**: Gemini analysis on every article
    """)

with col2:
    st.markdown("""
    - **🚫 Zero Duplicates**: Smart duplicate prevention across all bots
    - **📱 Professional Format**: Beautiful alert styling for all bots
    - **🛡️ Redundant Delivery**: Multiple bots ensure alert delivery
    """)

# Auto-refresh info with multi-bot mention
st.caption(f"🔄 Auto-refresh: Every 15 minutes with multi-bot alerting | Manual refresh available anytime")
