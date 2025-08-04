import feedparser
import requests
from datetime import datetime, timezone
import pytz
from database import insert_article, check_article_exists

# Set timezone for India
tz = pytz.timezone("Asia/Kolkata")

# ✅ Complete RSS feeds with all our additions
RSS_FEEDS = {
    # Tier 1 - High-volume industry sources
    "Rigzone": "https://www.rigzone.com/news/rss.asp",
    "Oil & Gas Journal": "https://www.ogj.com/rss",
    "World Oil": "https://www.worldoil.com/rss",
    "Oil & Gas 360": "https://oilandgas360.com/feed/",
    
    # Tier 2 - Market and financial sources  
    "OilPrice": "https://oilprice.com/rss/main",
    "Reuters Energy": "https://feeds.reuters.com/reuters/USenergyNews",
    "Energy Watch": "https://energywatch.com/service/rss",
    
    # Tier 3 - Government and official sources
    "EIA Today in Energy": "https://www.eia.gov/rss/todayinenergy.xml",
    "API News": "https://www.api.org/news-policy-and-issues/rss",
    
    # Tier 4 - Regional sources
    "Economic Times Oil & Gas": "https://energy.economictimes.indiatimes.com/rss/oil-and-gas"
}

# ✅ Expanded crude oil keywords
CRUDE_KEYWORDS = [
    "crude oil", "crude", "oil", "brent", "wti", "opec", "opec+",
    "oil price", "oil futures", "oil market", "petroleum", "barrel",
    "oil production", "oil supply", "oil inventories", "oil drilling",
    "oil refinery", "oil rig", "oil pipeline", "shale oil"
]

def is_crude_related(text: str) -> bool:
    """Check if text contains crude oil related keywords"""
    return any(keyword in text.lower() for keyword in CRUDE_KEYWORDS)

def fetch_rss_news(limit_per_feed=6):  # ✅ FIXED FUNCTION NAME
    """Fetch crude oil news and save to database"""
    articles_added = 0
    total_processed = 0
    
    # Headers to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"🛢️ Starting news fetch from {len(RSS_FEEDS)} sources...")
    
    for source_name, url in RSS_FEEDS.items():
        try:
            print(f"📡 Fetching from {source_name}: {url}")
            
            # Use requests with headers to avoid blocking
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse the RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                print(f"⚠️ No entries found in {source_name}")
                continue
                
            print(f"✅ Found {len(feed.entries)} entries in {source_name}")
            
            for entry in feed.entries[:limit_per_feed]:
                try:
                    title = entry.get('title', '').strip()
                    description = entry.get('description', entry.get('summary', '')).strip()
                    link = entry.get('link', '').strip()
                    
                    if not title or not link:
                        continue
                    
                    # Filter for crude oil related content
                    combined_text = title + " " + description
                    if not is_crude_related(combined_text):
                        continue
                    
                    total_processed += 1
                    
                    # Check if article already exists
                    if check_article_exists(link):
                        print(f"📋 Already exists: {title[:50]}...")
                        continue
                    
                    # Parse published date
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        else:
                            published_at = datetime.now(timezone.utc)
                    except:
                        published_at = datetime.now(timezone.utc)
                    
                    # Insert article into database
                    result = insert_article(
                        title=title,
                        description=description,
                        source=source_name,
                        link=link,
                        published_at=published_at.isoformat()
                    )
                    
                    if result:
                        articles_added += 1
                        print(f"✅ Added: {title[:60]}...")
                    else:
                        print(f"❌ Failed to insert: {title[:50]}...")
                        
                except Exception as e:
                    print(f"❌ Error processing entry: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error fetching from {source_name}: {e}")
            continue
    
    print(f"🏁 Fetch complete: {articles_added} new articles added from {total_processed} processed")
    return articles_added

# Keep the old function name as an alias for backward compatibility
fetch_news = fetch_rss_news
