import os
import hashlib
from telegram import Bot
from datetime import datetime, timezone, timedelta
import asyncio

# Global cache for duplicate prevention (persistent during app runtime)
alerted_articles_cache = set()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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

async def send_enhanced_telegram_alert(article) -> bool:
    """Send beautifully formatted Telegram alert"""
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("❌ Telegram credentials not found")
            return False

        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
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
        
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        print(f"✅ Enhanced alert sent: {title[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced alert error: {e}")
        return False

async def send_automatic_alerts(articles) -> int:
    """Send alerts for recent articles (last 1 hour) with duplicate prevention"""
    if not articles:
        print("📪 No articles to process for alerts")
        return 0
    
    alerts_sent = 0
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    print(f"📱 Processing {len(articles)} articles for automatic alerts...")
    print(f"⏰ Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
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
            
            print(f"📱 Sending automatic alert {i+1}: {article.get('title', 'No Title')[:50]}...")
            
            # Send the enhanced alert
            success = await send_enhanced_telegram_alert(article)
            
            if success:
                # Mark as alerted to prevent duplicates
                alerted_articles_cache.add(article_id)
                alerts_sent += 1
                
                # Rate limiting between alerts
                await asyncio.sleep(3)
            else:
                print(f"❌ Failed to send alert for article {i+1}")
                
        except Exception as e:
            print(f"❌ Error processing article {i+1}: {e}")
            continue
    
    print(f"🎯 Automatic alerts summary: {alerts_sent} alerts sent")
    return alerts_sent

# Backward compatibility functions
async def send_alert_live(article):
    """Single article alert (backward compatibility)"""
    return await send_enhanced_telegram_alert(article)

async def send_test_alert():
    """Send enhanced test alert"""
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        current_time = datetime.now(timezone.utc).strftime('%b %d, %I:%M %p')
        
        message = f"""🚨 CrudeIntel 2.0 Test Alert
📰 System Test | 🕒 {current_time}

📊 *Summary:* This is a test of the enhanced alert system with beautiful formatting.
📈 *Impact:* 🟢 Bullish
🧠 *Effect:* This test confirms your Telegram integration is working perfectly!
🔗 [CrudeIntel Dashboard](https://your-app-url.com)

✅ *Enhanced alert system is operational!*
        """
        
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
        
        return True
    except Exception as e:
        print(f"❌ Test alert error: {e}")
        return False

def get_alert_stats():
    """Get current alert statistics"""
    return {
        'total_alerted': len(alerted_articles_cache),
        'cache_size': len(alerted_articles_cache)
    }

def clear_alert_cache():
    """Clear alert cache (useful for testing)"""
    global alerted_articles_cache
    alerted_articles_cache.clear()
    print("🗑️ Alert cache cleared")
