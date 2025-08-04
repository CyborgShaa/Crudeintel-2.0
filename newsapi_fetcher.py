import requests
import os
from datetime import datetime, timezone

def fetch_newsapi_news():
    """Fetch crude oil news from NewsAPI"""
    
    # Get NewsAPI key from environment variables
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key:
        print("❌ NewsAPI key not found in environment variables")
        return 0
    
    articles_added = 0
    
    # NewsAPI endpoint for everything endpoint
    url = "https://newsapi.org/v2/everything"
    
    # Search parameters for crude oil news
    params = {
        'q': 'crude oil OR "oil prices" OR "oil market" OR OPEC OR "petroleum" OR "oil production"',
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 20,  # Limit to 20 articles
        'apiKey': api_key
    }
    
    try:
        print("📡 Fetching from NewsAPI...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 'ok':
            print(f"❌ NewsAPI error: {data.get('message', 'Unknown error')}")
            return 0
        
        articles = data.get('articles', [])
        print(f"✅ Found {len(articles)} articles from NewsAPI")
        
        for article in articles:
            try:
                # Extract article data
                title = article.get('title', '').strip()
                description = article.get('description', '').strip()
                url = article.get('url', '').strip()
                source_name = article.get('source', {}).get('name', 'NewsAPI')
                published_at = article.get('publishedAt', '')
                
                if not title or not url:
                    continue
                
                # Check if article already exists
                if check_article_exists(url):
                    print(f"📋 Already exists: {title[:50]}...")
                    continue
                
                # Parse published date
                try:
                    published_datetime = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    published_datetime = datetime.now(timezone.utc)
                
                # Insert article into database
                result = insert_article(
                    title=title,
                    description=description,
                    source=f"NewsAPI - {source_name}",
                    link=url,
                    published_at=published_datetime.isoformat()
                )
                
                if result:
                    articles_added += 1
                    print(f"✅ Added: {title[:60]}...")
                
            except Exception as e:
                print(f"❌ Error processing NewsAPI article: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error fetching from NewsAPI: {e}")
        return 0
    
    print(f"🏁 NewsAPI fetch complete: {articles_added} articles added")
    return articles_added
  
