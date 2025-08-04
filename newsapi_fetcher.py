# newsapi_fetcher.py

import os
import requests
from datetime import datetime
import pytz

tz = pytz.timezone("Asia/Kolkata")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def fetch_newsapi_articles(query="crude oil OR OPEC OR inventory", limit=5):
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
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("status") != "ok":
            print(f"❌ NewsAPI error: {data.get('message')}")
            return []

        articles = []
        for article in data["articles"]:
            articles.append({
                "title": article["title"],
                "link": article["url"],
                "source": article["source"]["name"],
                "timestamp": datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").astimezone(tz),
                "impact": "Neutral"
            })

        return articles

    except Exception as e:
        print(f"❌ Error fetching NewsAPI data: {e}")
        return []
