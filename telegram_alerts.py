import os
from telegram import Bot
from datetime import datetime, timezone
import asyncio
import hashlib

# Global cache for duplicate alert prevention (in-memory)
alerted_articles_cache = set()

async def send_telegram_alert(article):
    """Send Telegram alert for a single article"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not found")
            return False
        
        bot = Bot(token=bot_token)
        
        # Safe access with defaults
        title = article.get('title', 'No Title')
        summary = article.get('summary', 'No summary available')
        sentiment = article.get('sentiment', 'Unknown')
        source = article.get('source', 'Unknown')
        published_at = article.get('published_at', 'Unknown')
        link = article.get('link', '')
        
        # Sentiment emoji mapping
        sentiment_emoji = {
            'Bullish': '🟢',
            'Bearish': '🔴', 
            'Neutral': '⚪'
        }
        emoji = sentiment_emoji.get(sentiment, '⚪')
        
        # Format alert message
        message = f"""
🛢️ *CrudeIntel Alert* {emoji}

*{title}*

*🤖 AI Summary:*
{summary}

*📊 Market Impact:* {sentiment}
*📡 Source:* {source}
*⏰ Published:* {published_at}

[📖 Read Full Article]({link})

---
_CrudeIntel 2.0 Live Alert System_
        """
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        print(f"✅ Alert sent: {title[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")
        return False

def get_article_id(article):
    """Generate unique ID for article to prevent duplicates"""
    unique_string = article.get('title', '') + article.get('link', '')
    return hashlib.md5(unique_string.encode()).hexdigest()

def is_recent_article(published_at_str, hours_limit=1):
    """Check if article is within the specified hours limit"""
    try:
        if not published_at_str or published_at_str == 'Unknown':
            return False
        
        published_date = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        time_diff = datetime.now(timezone.utc) - published_date
        return time_diff.total_seconds() / 3600 <= hours_limit
        
    except Exception as e:
        print(f"❌ Error parsing date {published_at_str}: {e}")
        return False

async def send_alert_live(article):
    """Send single article alert (for app.py compatibility)"""
    return await send_telegram_alert(article)

async def send_alerts_for_recent(articles):
    """Send alerts for recent articles only (last 1 hour) with duplicate prevention"""
    if not articles:
        print("📪 No articles provided for alerts")
        return 0
    
    alerts_sent = 0
    
    print(f"📱 Processing {len(articles)} articles for potential alerts...")
    
    for i, article in enumerate(articles):
        try:
            # Check if article is recent (last 1 hour only)
            if not is_recent_article(article.get('published_at')):
                print(f"⏰ Article {i+1} not recent - skipped")
                continue
            
            # Check sentiment - only alert for Bullish/Bearish
            sentiment = article.get('sentiment', '')
            if sentiment.lower() not in ['bullish', 'bearish']:
                print(f"😐 Article {i+1} neutral sentiment - skipped")
                continue
            
            # Generate unique ID for duplicate prevention
            article_id = get_article_id(article)
            
            # Skip if already alerted
            if article_id in alerted_articles_cache:
                print(f"📋 Article {i+1} already alerted - skipped")
                continue
            
            print(f"📱 Sending alert for article {i+1}: {article.get('title', 'No Title')[:50]}...")
            
            # Send the alert
            success = await send_telegram_alert(article)
            
            if success:
                # Mark as alerted to prevent duplicates
                alerted_articles_cache.add(article_id)
                alerts_sent += 1
                
                # Rate limiting - wait between alerts
                await asyncio.sleep(2)
            else:
                print(f"❌ Failed to send alert for article {i+1}")
                
        except Exception as e:
            print(f"❌ Error processing article {i+1} for alert: {e}")
            continue
    
    print(f"📱 Alert summary: {alerts_sent} alerts sent successfully")
    return alerts_sent

async def send_alerts(articles=None):
    """Main alerts function - backward compatibility"""
    if articles is None:
        print("⚠️ No articles provided for alerts")
        return 0
    
    return await send_alerts_for_recent(articles)

async def send_test_alert():
    """Send a test alert to verify Telegram integration"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not found")
            return False
        
        bot = Bot(token=bot_token)
        
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        message = f"""
🔧 *CrudeIntel Test Alert*

This is a test message to verify your Telegram bot integration is working correctly.

✅ *System Status:* Online - Live Mode
🕒 *Test Time:* {current_time}
🛢️ *Service:* CrudeIntel 2.0
📡 *Mode:* Database-Free Architecture

If you receive this message, your Telegram alerts are configured properly!

---
_Automated test from CrudeIntel 2.0_
        """
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        
        print("✅ Test alert sent successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test alert failed: {e}")
        return False

def clear_alert_cache():
    """Clear the alerted articles cache (useful for testing)"""
    global alerted_articles_cache
    alerted_articles_cache.clear()
    print("🗑️ Alert cache cleared")

def get_alert_cache_size():
    """Get the current size of alert cache"""
    return len(alerted_articles_cache)

# For backward compatibility and direct execution
if __name__ == "__main__":
    print("🧪 Testing Telegram integration...")
    result = asyncio.run(send_test_alert())
    print(f"Test result: {'✅ Success' if result else '❌ Failed'}")
        
