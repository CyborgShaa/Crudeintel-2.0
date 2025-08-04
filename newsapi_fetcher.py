# newsapi_fetcher.py

import os
import requests
from datetime import datetime, timezone
import pytz
from database import insert_article, check_article_exists

tz = pytz.timezone("Asia/Kolkata")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def fetch_newsapi_articles(query="crude oil OR OPEC OR inventory", limit=5):
    print(f"🔍 DEBUG: Starting NewsAPI fetch with query: '{query}', limit: {limit}")
    
    if not NEWSAPI_KEY:
        print("❌ NEWSAPI_KEY not found in environment.")
        return 0

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
            return 0
            
        data = response.json()

        if data.get("status") != "ok":
            print(f"❌ NewsAPI error: {data.get('message')}")
            return 0

        articles_added = 0
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

                # Check if article already exists
                exists = check_article_exists(link)
                print(f"🔄 Duplicate check result: {'EXISTS' if exists else 'NEW'}")
                
                if exists:
                    print(f"📋 Article already exists - SKIPPED")
                    continue

                # Parse published date
                try:
                    published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
                    published_at = published_at.replace(tzinfo=timezone.utc)
                    print(f"📅 Published date: {published_at}")
                except Exception as e:
                    published_at = datetime.now(timezone.utc)
                    print(f"⚠️ Date parse failed, using current time: {e}")

                # Insert article into database
                print(f"💾 Attempting database insert for NewsAPI article...")
                result = insert_article(
                    title=title,
                    description=description,
                    source=source,
                    link=link,
                    published_at=published_at.isoformat()
                )

                if result:
                    articles_added += 1
                    print(f"✅ SUCCESS: NewsAPI article inserted!")
                else:
                    print(f"❌ FAILED: Database insert returned False")

            except Exception as e:
                print(f"❌ Error processing NewsAPI article: {e}")
                continue

        print(f"\n🏁 NewsAPI FINAL RESULT: {articles_added} articles successfully added")
        return articles_added

    except Exception as e:
        print(f"❌ Error fetching NewsAPI data: {e}")
        return 0
        
