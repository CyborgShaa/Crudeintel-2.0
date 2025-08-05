import os
import hashlib
from telegram import Bot
from datetime import datetime, timezone, timedelta
import asyncio

# Global cache for duplicate prevention (persistent during app runtime)
alerted_articles_cache = set()

# Configure multiple Telegram bots
TELEGRAM_BOTS = [
    {
        "name": "Bot 1",
        "token": os.getenv('TELEGRAM_BOT_TOKEN_1'),
        "chat_id": os.getenv('TELEGRAM_CHAT_ID_1')
    },
    {
        "name": "Bot 2", 
        "token": os.getenv('TELEGRAM_BOT_TOKEN_2'),
        "chat_id": os.getenv('TELEGRAM_CHAT_ID_2')
    },
    {
        "name": "Bot 3",
        "token": os.getenv('TELEGRAM_BOT_TOKEN_3'), 
        "chat_id": os.getenv('TELEGRAM_CHAT_ID_3')
    }
]

def get_article_id(title: str, link: str) -> str:
    """Generate unique ID to prevent duplicate alerts"""
    return hashlib.md5((title + link).encode()).hexdigest()

def format_published_time(published_at: str) -> str:
    """Format published time to match your desired format"""
    try:
        dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        return dt.strftime("%b %d, %I:%M %p")
    except:
        return "Unknown time"

def get_impact_description(sentiment: str) -> str:
    """Get impact description based on sentiment"""
    impact_map = {
        "Bullish": "This may lead to price increases due to positive market sentiment, supply constraints, or strong demand signals.",
        "Bearish": "This may lead to a drop in prices due to oversupply, demand concerns, or bearish economic signals.",
        "Neutral": "This news provides market information but may have limited immediate price impact."
    }
    return impact_map.get(sentiment, "Market impact assessment pending.")

async def send_enhanced_telegram_alert_multi(article) -> int:
    """Send beautifully formatted Telegram alert to all configured bots"""
    successful_sends = 0
    
    # Extract article data safely
    title = article.get('title', 'No Title')
    source = article.get('source', 'Unknown Source')
    summary = article.get('summary', 'Summary pending analysis')
    sentiment = article.get('sentiment', 'Neutral')
    published_at = article.get('published_at', '')
    link = article.get('link', '')
    
    # Format components
    sentiment_emoji = {
        'Bullish': '🟢',
        'Bearish': '🔴',
        'Neutral': '⚪'
    }
    emoji = sentiment_emoji.get(sentiment, '⚪')
    formatted_time = format_published_time(published_at)
    impact_description = get_impact_description(sentiment)
    
    # Create the enhanced alert message
    message = f"""🚨 {title}
📰 {source} | 🕒 {formatted_time}

📊 *Summary:* {summary}
📈 *Impact:* {emoji} {sentiment}
🧠 *Effect:* {impact_description}
🔗 [Read full article]({link})
    """
    
    # Send to all configured bots
    for bot_config in TELEGRAM_BOTS:
        bot_name = bot_config.get('name', 'Unknown Bot')
        token = bot_config.get('token')
        chat_id = bot_config.get('chat_id')
        
        if not token or not chat_id:
            print(f"⚠️ {bot_name}: Missing credentials - skipped")
            continue
        
        try:
            bot = Bot(token=token)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            print(f"✅ {bot_name}: Alert sent successfully")
            successful_sends += 1
            
        except Exception as e:
            print(f"❌ {bot_name}: Error sending alert - {e}")
            continue
    
    return successful_sends

async def send_automatic_alerts(articles) -> int:
    """Send alerts for recent articles (last 1 hour) with duplicate prevention to all bots"""
    if not articles:
        print("📪 No articles to process for alerts")
        return 0
    
    total_alerts_sent = 0
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    print(f"📱 Processing {len(articles)} articles for automatic multi-bot alerts...")
    print(f"⏰ Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Count valid bots
    valid_bots = len([bot for bot in TELEGRAM_BOTS if bot.get('token') and bot.get('chat_id')])
    print(f"🤖 Configured bots: {valid_bots}")
    
    for i, article in enumerate(articles):
        try:
            # Check if article is from last 1 hour
            published_at = article.get('published_at', '')
            if not published_at:
                continue
                
            published_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            if published_dt <= cutoff_time:
                print(f"⏰ Article {i+1} too old - skipped")
                continue
            
            # Check sentiment - only alert for Bullish/Bearish
            sentiment = article.get('sentiment', '')
            if sentiment.lower() not in ['bullish', 'bearish']:
                print(f"😐 Article {i+1} neutral sentiment - skipped")
                continue
            
            # Check for duplicates
            article_id = get_article_id(article.get('title', ''), article.get('link', ''))
            if article_id in alerted_articles_cache:
                print(f"📋 Article {i+1} already alerted - skipped")
                continue
            
            print(f"📱 Sending multi-bot alert {i+1}: {article.get('title', 'No Title')[:50]}...")
            
            # Send the enhanced alert to all bots
            successful_sends = await send_enhanced_telegram_alert_multi(article)
            
            if successful_sends > 0:
                # Mark as alerted to prevent duplicates
                alerted_articles_cache.add(article_id)
                total_alerts_sent += 1
                print(f"🎯 Alert sent to {successful_sends}/{valid_bots} bots")
                
                # Rate limiting between alerts
                await asyncio.sleep(3)
            else:
                print(f"❌ Failed to send alert to any bot for article {i+1}")
                
        except Exception as e:
            print(f"❌ Error processing article {i+1}: {e}")
            continue
    
    print(f"🎯 Multi-bot alerts summary: {total_alerts_sent} alerts sent across all bots")
    return total_alerts_sent

async def send_test_alert():
    """Send enhanced test alert to all bots"""
    successful_tests = 0
    current_time = datetime.now(timezone.utc).strftime('%b %d, %I:%M %p')
    
    message = f"""🚨 CrudeIntel 2.0 Multi-Bot Test Alert
📰 System Test | 🕒 {current_time}

📊 *Summary:* This is a test of the enhanced multi-bot alert system with beautiful formatting.
📈 *Impact:* 🟢 Bullish
🧠 *Effect:* This test confirms all your Telegram bots are working perfectly!
🔗 [CrudeIntel Dashboard](https://your-app-url.com)

✅ *Enhanced multi-bot alert system is operational!*
    """
    
    for bot_config in TELEGRAM_BOTS:
        bot_name = bot_config.get('name', 'Unknown Bot')
        token = bot_config.get('token')
        chat_id = bot_config.get('chat_id')
        
        if not token or not chat_id:
            print(f"⚠️ {bot_name}: Missing credentials - skipped")
            continue
        
        try:
            bot = Bot(token=token)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            print(f"✅ {bot_name}: Test alert sent successfully")
            successful_tests += 1
            
        except Exception as e:
            print(f"❌ {bot_name}: Test alert failed - {e}")
            continue
    
    return successful_tests > 0

def get_alert_stats():
    """Get current alert statistics"""
    valid_bots = len([bot for bot in TELEGRAM_BOTS if bot.get('token') and bot.get('chat_id')])
    return {
        'total_alerted': len(alerted_articles_cache),
        'cache_size': len(alerted_articles_cache),
        'configured_bots': valid_bots
    }

def clear_alert_cache():
    """Clear alert cache (useful for testing)"""
    global alerted_articles_cache
    alerted_articles_cache.clear()
    print("🗑️ Alert cache cleared")

# Backward compatibility functions
async def send_alert_live(article):
    """Single article alert (backward compatibility)"""
    return await send_enhanced_telegram_alert_multi(article)

async def send_alerts_for_recent(articles):
    """Backward compatibility wrapper"""
    return await send_automatic_alerts(articles)
