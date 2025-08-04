# newsapi_fetcher.py

import os
import requests
from datetime import datetime, timezone
import pytz
from database import insert_article, check_article_exists

tz = pytz.timezone("Asia/Kolkata")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def fetch_newsapi_articles(query="crude oil OR OPEC OR inventory", limit=5):
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
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            print(f"❌ NewsAPI error: {data.get('message')}")
            return 0

        articles_added = 0
        total_found = len(data.get("articles", []))
        print(f"✅ Found {total_found} articles from NewsAPI")

        for article in data["articles"]:
            try:
                title = article.get("title", "").strip()
                link = article.get("url", "").strip()
                source = f"NewsAPI - {article.get('source', {}).get('name', 'Unknown')}"
                description = article.get("description", "").strip()
                published_at_str = article.get("publishedAt", "")

                if not title or not link:
                    continue

                # Check if article already exists
                if check_article_exists(link):
                    print(f"📋 Already exists: {title[:50]}...")
                    continue

                # Parse published date
                try:
                    published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ")
                    published_at = published_at.replace(tzinfo=timezone.utc)
                except Exception:
                    published_at = datetime.now(timezone.utc)

                # Insert article into database
                result = insert_article(
                    title=title,
                    description=description,
                    source=source,
                    link=link,
                    published_at=published_at.isoformat()
                )

                if result:
                    articles_added += 1
                    print(f"✅ Added NewsAPI article: {title[:60]}...")
                else:
                    print(f"❌ Failed to insert: {title[:50]}...")

            except Exception as e:
                print(f"❌ Error processing NewsAPI article: {e}")
                continue

        print(f"🏁 NewsAPI fetch complete: {articles_added} articles added")
        return articles_added

    except Exception as e:
        print(f"❌ Error fetching NewsAPI data: {e}")
        return 0
        
