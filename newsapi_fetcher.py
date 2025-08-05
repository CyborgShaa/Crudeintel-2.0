# newsapi_fetcher.py

import os
import requests
from datetime import datetime, timezone
import pytz

tz = pytz.timezone("Asia/Kolkata")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def fetch_newsapi_articles_live(query="crude oil OR OPEC OR inventory", limit=5):
    """Fetch NewsAPI articles live and return as list of dicts (database-free)"""
    print(f"🔍 DEBUG: Starting NewsAPI live fetch with query: '{query}', limit: {limit}")
    
    if not NEWSAPI_KEY:
        print("❌ NEWSAPI_KEY not found in environment.")
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": NEWSAPI_KEY
    }

    try:
        print(f"📡 Fetching from NewsAPI with query: {query}")
        print(f"🔗 URL: {url}")
        
        response = requests.get(url, params=params, timeout=15)
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return []
            
        data = response.json()

        if data.get("status") != "ok":
            print(f"❌ NewsAPI error: {data.get('message')}")
            return []

        articles_collected = []
        total_found = len(data.get("articles", []))
        print(f"✅ Found {total_found} articles from NewsAPI")

        for i, article in enumerate(data["articles"]):
            try:
                print(f"\n--- Processing NewsAPI Article {i+1} ---")
                
                title = article.get("title", "").strip()
                link = article.get("url", "").strip()
                source = f"NewsAPI - {article.get('source', {}).get('name', 'Unknown')}"
                description = article.get("description", "").strip()
                published_at_str = article.get("publishedAt", "")

                print(f"📰 Title: {title}")
                print(f"🔗 Link: {link[:80]}...")
                print(f"📡 Source: {source}")

                if not title or not link:
                    print(f"❌ Missing title or link - SKIPPED")
                    continue

                # Parse published date
                try:
                    published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
                    published_at = published_at.replace(tzinfo=timezone.utc)
                    print(f"📅 Published date: {published_at}")
                except Exception as e:
                    published_at = datetime.now(timezone.utc)
                    print(f"⚠️ Date parse failed, using current time: {e}")

                # Create article object (no database insertion)
                article_dict = {
                    'title': title,
                    'description': description,
                    'link': link,
                    'published_at': published_at.isoformat(),
                    'source': source
                }

                articles_collected.append(article_dict)
                print(f"✅ SUCCESS: NewsAPI article collected in memory!")

            except Exception as e:
                print(f"❌ Error processing NewsAPI article: {e}")
                continue

        print(f"\n🏁 NewsAPI FINAL RESULT: {len(articles_collected)} articles collected")
        return articles_collected

    except Exception as e:
        print(f"❌ Error fetching NewsAPI data: {e}")
        return []

# Backward compatibility alias - keeps old function name working
fetch_newsapi_articles = fetch_newsapi_articles_live
