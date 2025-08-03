import os
from telegram import Bot
from datetime import datetime, timedelta, timezone
from database import get_unalerted_articles, mark_article_alerted
import asyncio

async def send_telegram_alert(article):
    """Send Telegram alert for an article"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("Telegram credentials not found")
            return False
        
        bot = Bot(token=bot_token)
        
        # Format message
        sentiment_emoji = {
            'Bullish': '🟢',
            'Bearish': '🔴',
            'Neutral': '⚪'
        }
        
        emoji = sentiment_emoji.get(article['sentiment'], '⚪')
        
        message = f"""
{emoji} *CrudeIntel Alert*

*{article['title']}*

*Summary:* {article['summary']}

*Impact:* {article['sentiment']}
*Source:* {article['source']}
*Time:* {article['published_at']}

[Read Full Article]({article['link']})
        """
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")
        return False

async def send_alerts():
    """Send alerts for unalerted articles"""
    try:
        articles = get_unalerted_articles()
        alerts_sent = 0
        
        for article in articles:
            # Check if article is recent (within 60 minutes)
            published_at = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            if (now - published_at).total_seconds() <= 3600:  # 60 minutes
                success = await send_telegram_alert(article)
                
                if success:
                    mark_article_alerted(article['id'])
                    alerts_sent += 1
                    print(f"Alert sent: {article['title'][:50]}...")
                    
                    # Add delay between messages to avoid rate limiting
                    await asyncio.sleep(1)
        
        print(f"Sent {alerts_sent} alerts")
        return alerts_sent
        
    except Exception as e:
        print(f"Error sending alerts: {e}")
        return 0

async def send_test_alert():
    """Send a test alert"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            return False
        
        bot = Bot(token=bot_token)
        
        message = """
🔧 *CrudeIntel Test Alert*

This is a test message to verify your Telegram bot is working correctly.

System Status: ✅ Online
Time: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        
        return True
        
    except Exception as e:
        print(f"Test alert failed: {e}")
        return False

if __name__ == "__main__":
    print("Sending alerts...")
    result = asyncio.run(send_alerts())
    print(f"Alert process complete. Sent {result} alerts.")
  
