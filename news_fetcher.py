import feedparser
import requests
from datetime import datetime, timezone
import pytz

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

    # Geopolitical, policy & infrastructure
    "oil sanctions", "oil embargo", "oil pipeline", "crude demand",
    "oil refinery", "oil rig", "petroleum", "middle east", "iran", "usa crude"
]

def is_crude_related(text: str) -> bool:
    """Check if text contains crude oil related keywords with debug logging"""
    result = any(keyword in text.lower() for keyword in CRUDE_KEYWORDS)
    print(f"🔍 Keyword filter check for: '{text[:75]}...' → Result: {result}")
    return result

def fetch_news_live(limit_per_feed=6):
    """Fetch crude oil news and return articles directly (no database)"""
    articles_collected = []
    total_processed = 0
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"🛢️ DEBUG: Starting news fetch from {len(RSS_FEEDS)} sources...")
    print(f"🔍 DEBUG: RSS sources: {list(RSS_FEEDS.keys())}")
    
    for source_name, url in RSS_FEEDS.items():
        try:
            print(f"\n📡 FETCHING: {source_name}")
            print(f"🔗 URL: {url}")
            
            response = requests.get(url, headers=headers, timeout=15)
            print(f"📊 HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ HTTP Error for {source_name}: {response.status_code}")
                continue
            
            feed = feedparser.parse(response.content)
            print(f"📰 Raw entries found: {len(feed.entries)}")
            
            if not feed.entries:
                print(f"⚠️ No entries in feed for {source_name}")
                continue
            
            crude_related_count = 0
            for i, entry in enumerate(feed.entries[:limit_per_feed]):
                try:
                    print(f"\n--- Processing Article {i+1} from {source_name} ---")
                    
                    title = entry.get('title', '').strip()
                    description = entry.get('description', entry.get('summary', '')).strip()
                    link = entry.get('link', '').strip()
                    
                    print(f"📰 Title: {title}")
                    print(f"🔗 Link: {link[:80]}...")
                    
                    if not title or not link:
                        print(f"❌ Missing title or link - SKIPPED")
                        continue
                    
                    # Test keyword filter with debug output
                    combined_text = title + " " + description
                    if not is_crude_related(combined_text):
                        print(f"❌ Failed keyword filter - SKIPPED")
                        continue
                    
                    crude_related_count += 1
                    total_processed += 1
                    
                    # Parse published date
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                        else:
                            published_at = datetime.now(timezone.utc)
                    except:
                        published_at = datetime.now(timezone.utc)
                    
                    print(f"📅 Published date: {published_at}")
                    
                    # Create article object (no database insertion)
                    article = {
                        'title': title,
                        'description': description,
                        'link': link,
                        'published_at': published_at.isoformat(),
                        'source': f"RSS - {source_name}"
                    }
                    
                    articles_collected.append(article)
                    print(f"✅ SUCCESS: Article collected in memory!")
                        
                except Exception as e:
                    print(f"❌ Error processing entry: {e}")
                    continue
            
            print(f"📊 {source_name} SUMMARY: {crude_related_count} crude-related out of {len(feed.entries[:limit_per_feed])} articles")
                    
        except Exception as e:
            print(f"❌ Error fetching from {source_name}: {e}")
            continue
    
    print(f"\n🏁 RSS FINAL RESULT: {len(articles_collected)} articles collected from RSS sources")
    print(f"📊 TOTAL PROCESSED: {total_processed} articles passed all filters")
    return articles_collected

# Backward compatibility aliases
fetch_news = fetch_news_live
fetch_rss_news = fetch_news_live
