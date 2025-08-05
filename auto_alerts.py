#!/usr/bin/env python3
"""
CrudeIntel 2.0 Automated Alerts for Render Scheduled Job (15-minute run)
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Ensure current folder is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_fetcher import fetch_news_live
from newsapi_fetcher import fetch_newsapi_articles_live
from summarizer import analyze_article_live
from telegram_alerts import send_automatic_alerts

def filter_last_hour_articles(articles):
    """Keep only articles published within last hour."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = []
    for article in articles:
        try:
            published_at = article.get('published_at', '')
            if not published_at:
                continue
            published_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            if published_dt > cutoff:
                recent.append(article)
        except Exception as e:
            print(f"Date parse error: {e}")
    return recent

async def main():
    print(f"CrudeIntel Auto Alert Job started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        print("Fetching RSS Feed Articles...")
        rss_articles = fetch_news_live()
        print(f"Fetched {len(rss_articles)} RSS articles")
        
        print("Fetching NewsAPI Articles...")
        newsapi_articles = fetch_newsapi_articles_live()
        print(f"Fetched {len(newsapi_articles)} NewsAPI articles")
        
        all_articles = rss_articles + newsapi_articles
        
        # Filter to last one hour only
        recent_articles = filter_last_hour_articles(all_articles)
        print(f"{len(recent_articles)} articles published in last one hour")
        
        if not recent_articles:
            print("No recent articles to send alerts for.")
            return
        
        # Deduplicate articles by title + link
        unique = {}
        for article in recent_articles:
            key = article.get('title', '') + article.get('link', '')
            if key not in unique:
                unique[key] = article
        
        unique_articles = list(unique.values())
        print(f"{len(unique_articles)} unique recent articles")
        
        # AI Analyze articles
        print("Running AI analysis on articles...")
        analyzed_count = 0
        for i, article in enumerate(unique_articles):
            try:
                print(f"Analyzing article {i+1}/{len(unique_articles)}: {article.get('title', '')[:50]}")
                summary, sentiment = analyze_article_live(article.get('title', ''), article.get('description', ''))
                article['summary'] = summary
                article['sentiment'] = sentiment
                analyzed_count += 1
            except Exception as e:
                print(f"AI analysis error: {e}")
        
        print(f"Analyzed {analyzed_count} articles")
        
        # Send Telegram alerts for articles
        print("Sending Telegram alerts for relevant articles...")
        alerts_sent = await send_automatic_alerts(unique_articles)
        print(f"Sent {alerts_sent} alerts")
    
    except Exception as e:
        print(f"Auto alert job failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
