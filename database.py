import os
import requests
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict

# Firebase configuration
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

def get_firestore_url(collection: str, document_id: str = None):
    """Generate Firestore REST API URL with API key"""
    base_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/{collection}"
    if document_id:
        base_url += f"/{document_id}"
    base_url += f"?key={FIREBASE_API_KEY}"
    return base_url

def make_firestore_request(method: str, url: str, data: Dict = None) -> Dict:
    """Make request to Firestore REST API"""
    headers = {'Content-Type': 'application/json'}
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        
        response.raise_for_status()
        return response.json() if response.content else {}
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Firestore API error: {e}")
        return {}

def firestore_value(value):
    """Convert Python value to Firestore format"""
    if value is None:
        return {"nullValue": None}
    elif isinstance(value, str):
        return {"stringValue": value}
    elif isinstance(value, bool):
        return {"booleanValue": value}
    else:
        return {"stringValue": str(value)}

def parse_firestore_doc(doc: Dict) -> Dict:
    """Parse Firestore document to Python dict"""
    if not doc or 'fields' not in doc:
        return {}
    
    result = {}
    for key, value_obj in doc['fields'].items():
        if 'stringValue' in value_obj:
            result[key] = value_obj['stringValue']
        elif 'booleanValue' in value_obj:
            result[key] = value_obj['booleanValue']
        elif 'nullValue' in value_obj:
            result[key] = None
        else:
            result[key] = str(value_obj)
    
    if 'name' in doc:
        result['id'] = doc['name'].split('/')[-1]
    
    return result

def insert_article(title: str, description: str, source: str, link: str, 
                  published_at: str, summary: str = None, sentiment: str = None) -> bool:
    """Insert article into Firestore"""
    try:
        print(f"💾 DEBUG: Inserting article '{title[:50]}...' from {source}")
        
        doc_id = hashlib.md5(link.encode()).hexdigest()
        
        doc_data = {
            "fields": {
                "title": firestore_value(title),
                "description": firestore_value(description),
                "source": firestore_value(source),
                "link": firestore_value(link),
                "published_at": firestore_value(published_at),
                "summary": firestore_value(summary),
                "sentiment": firestore_value(sentiment),
                "alerted": firestore_value(False),
                "created_at": firestore_value(datetime.now(timezone.utc).isoformat())
            }
        }
        
        url = get_firestore_url("articles", doc_id)
        result = make_firestore_request("PATCH", url, doc_data)
        
        if result and 'name' in result:
            print(f"✅ Insert succeeded")
            return True
        else:
            print(f"❌ Insert failed")
            return False
            
    except Exception as e:
        print(f"❌ Exception during insert: {e}")
        return False

def get_recent_articles(limit: int = 50) -> List[Dict]:
    """Get recent articles from Firestore"""
    try:
        print(f"📚 DEBUG: Querying Firestore for {limit} articles...")
        
        url = get_firestore_url("articles")
        result = make_firestore_request("GET", url)
        
        if not result or 'documents' not in result:
            print(f"📚 No articles found")
            return []
        
        articles = []
        for doc in result['documents']:
            article = parse_firestore_doc(doc)
            if article:
                articles.append(article)
        
        # Sort by published_at (newest first)
        articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        print(f"📚 Retrieved {len(articles)} articles")
        return articles[:limit]
        
    except Exception as e:
        print(f"❌ Exception during get_recent_articles: {e}")
        return []

def check_article_exists(link: str) -> bool:
    """Check if article exists"""
    try:
        doc_id = hashlib.md5(link.encode()).hexdigest()
        url = get_firestore_url("articles", doc_id)
        result = make_firestore_request("GET", url)
        
        exists = bool(result and 'name' in result)
        print(f"🔎 Article exists: {exists}")
        return exists
        
    except Exception as e:
        print(f"❌ Exception during check_article_exists: {e}")
        return False

def update_article_summary(article_id: str, summary: str, sentiment: str) -> bool:
    """Update article with AI summary"""
    try:
        update_data = {
            "fields": {
                "summary": firestore_value(summary),
                "sentiment": firestore_value(sentiment)
            }
        }
        
        url = get_firestore_url("articles", article_id)
        result = make_firestore_request("PATCH", url, update_data)
        
        return bool(result and 'name' in result)
        
    except Exception as e:
        print(f"❌ Exception during update: {e}")
        return False

def get_unalerted_articles() -> List[Dict]:
    """Get unalerted articles"""
    try:
        all_articles = get_recent_articles(1000)
        unalerted = [
            article for article in all_articles 
            if not article.get('alerted', False) and article.get('sentiment') != 'Neutral'
        ]
        return unalerted
    except Exception as e:
        print(f"❌ Exception during get_unalerted_articles: {e}")
        return []

def mark_article_alerted(article_id: str) -> bool:
    """Mark article as alerted"""
    try:
        update_data = {
            "fields": {
                "alerted": firestore_value(True)
            }
        }
        
        url = get_firestore_url("articles", article_id)
        result = make_firestore_request("PATCH", url, update_data)
        
        return bool(result and 'name' in result)
        
    except Exception as e:
        print(f"❌ Exception during mark_article_alerted: {e}")
        return False

def test_database_connection() -> bool:
    """Test Firestore connection"""
    try:
        print("🔍 Testing Firebase Firestore connection...")
        
        if not FIREBASE_PROJECT_ID or not FIREBASE_API_KEY:
            print("❌ Missing Firebase credentials")
            return False
        
        # Test basic query
        url = get_firestore_url("articles")
        result = make_firestore_request("GET", url)
        
        if 'error' in result:
            print(f"❌ Connection failed: {result['error']}")
            return False
        
        print(f"✅ Connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
        

        
      
