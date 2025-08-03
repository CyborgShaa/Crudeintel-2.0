import feedparser
import requests
from datetime import datetime, timezone
import pytz
import os
from database import insert_article, check_article_exists

# RSS Feeds for crude oil news
RSS_FEEDS = [
    'https://feeds.feedburner.com/ndtvprofit/commodity',
    'https://www.moneycontrol.com/rss/commodity.xml',
    'https://economictimes.indiatimes.com/commoditiesxml/commodity/name/crude_oil.xml',
    'https://www.cnbc.com/id/10000727/device/rss/rss.html',
    'https://feeds.reuters.com/reuters/commoditiesNews'
]

def fetch_rss_news():
    """Fetch news from RSS feeds"""
    articles_added = 0
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"Fetching from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:5]:  # Limit to 5 most recent per feed
                # Check if article already exists
                if check_article_exists(entry.link):
                    continue
                
                # Parse published date
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                else:
                    published_at = datetime.now(timezone.utc)
                
                # Extract source name
                source = feed.feed.title if hasattr(feed.feed, 'title') else 'RSS Feed'
                
                # Insert article
                result = insert_article(
                    title=entry.title,
                    description=entry.description if hasattr(entry, 'description') else '',
                    source=source,
                    link=entry.link,
                    published_at=published_at.isoformat()
                )
                
                if result:
                    articles_added += 1
                    print(f"Added: {entry.title[:50]}...")
                    
        except Exception as e:
            print(f"Error fetching from {feed_url}: {e}")
            continue
    
    return articles_added

def fetch_newsapi_news():
    """Fetch news from News API"""
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key:
        print("NewsAPI key not found")
        return 0
    
    articles_added = 0
    
    # Search queries for crude oil related news
    queries = [
        'crude oil',
        'OPEC',
        'oil inventory',
        'petroleum prices',
        'oil production'
    ]
    
    for query in queries:
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 10,
                'from': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                for article in data['articles']:
                    # Check if article already exists
                    if check_article_exists(article['url']):
                        continue
                    
                    # Parse published date
                    published_at = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    
                    # Insert article
                    result = insert_article(
                        title=article['title'],
                        description=article['description'] or '',
                        source=article['source']['name'],
                        link=article['url'],
                        published_at=published_at.isoformat()
                    )
                    
                    if result:
                        articles_added += 1
                        print(f"Added: {article['title'][:50]}...")
                        
        except Exception as e:
            print(f"Error fetching NewsAPI data for '{query}': {e}")
            continue
    
    return articles_added

if __name__ == "__main__":
    print("Starting news fetch...")
    rss_count = fetch_rss_news()
    api_count = fetch_newsapi_news()
    print(f"Total articles added: {rss_count + api_count}")
  
