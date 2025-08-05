import os
import requests
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Firebase Firestore configuration
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

def get_firestore_url(collection: str, document_id: str = None):
    """Generate Firestore REST API URL"""
    base_url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/{collection}"
    if document_id:
        base_url += f"/{document_id}"
    return base_url

def make_firestore_request(method: str, url: str, data: Dict = None) -> Dict:
    """Make authenticated request to Firestore REST API"""
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Add API key to URL for authentication
    separator = '&' if '?' in url else '?'
    url_with_key = f"{url}{separator}key={FIREBASE_API_KEY}"
    
    try:
        if method == 'GET':
            response = requests.get(url_with_key, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url_with_key, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url_with_key, headers=headers, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        
        if response.content:
            return response.json()
        else:
            return {}
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Firestore API error: {e}")
        return {}

def firestore_value(value):
    """Convert Python value to Firestore value format"""
    if value is None:
        return {"nullValue": None}
    elif isinstance(value, str):
        return {"stringValue": value}
    elif isinstance(value, int):
        return {"integerValue": str(value)}
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
        elif 'integerValue' in value_obj:
            result[key] = int(value_obj['integerValue'])
        elif 'booleanValue' in value_obj:
            result[key] = value_obj['booleanValue']
        elif 'nullValue' in value_obj:
            result[key] = None
        else:
            result[key] = str(value_obj)
    
    # Add document ID
    if 'name' in doc:
        doc_id = doc['name'].split('/')[-1]
        result['id'] = doc_id
    
    return result

def insert_article(title: str, description: str, source: str, link: str, 
                  published_at: str, summary: str = None, sentiment: str = None) -> bool:
    """Insert a new article into Firestore with debug logging"""
    try:
        print(f"💾 DEBUG: Inserting article '{title[:50]}...' from {source}")
        
        # Use link hash as document ID to prevent duplicates
        doc_id = hashlib.md5(link.encode()).hexdigest()
        
        # Create document data in Firestore format
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
            print(f"✅ Insert succeeded: Article stored in Firestore")
            return True
        else:
            print(f"❌ Insert failed: No valid response from Firestore")
            return False
            
    except Exception as e:
        print(f"❌ Exception during insert_article: {e}")
        return False

def get_recent_articles(limit: int = 50) -> List[Dict]:
    """Get recent articles from Firestore with debug logging"""
    try:
        print(f"📚 DEBUG: Querying Firestore for {limit} recent articles...")
        
        url = get_firestore_url("articles")
        params = f"?pageSize={limit}&orderBy=published_at desc"
        
        result = make_firestore_request("GET", url + params)
        
        if not result or 'documents' not in result:
            print(f"📚 No articles found in Firestore")
            return []
        
        articles = []
        for doc in result['documents']:
            article = parse_firestore_doc(doc)
            if article:
                articles.append(article)
        
        print(f"📚 Retrieved {len(articles)} articles from Firestore")
        return articles
        
    except Exception as e:
        print(f"❌ Exception during get_recent_articles: {e}")
        return []

def check_article_exists(link: str) -> bool:
    """Check if article already exists in Firestore with debug logging"""
    try:
        # Use link hash as document ID
        doc_id = hashlib.md5(link.encode()).hexdigest()
        
        url = get_firestore_url("articles", doc_id)
        result = make_firestore_request("GET", url)
        
        exists = bool(result and 'name' in result)
        print(f"🔎 Article exists check for '{link[:50]}...': {exists}")
        return exists
        
    except Exception as e:
        print(f"❌ Exception during check_article_exists: {e}")
        return False

def update_article_summary(article_id: str, summary: str, sentiment: str) -> bool:
    """Update article with AI-generated summary and sentiment"""
    try:
        print(f"🤖 DEBUG: Updating article {article_id} with AI summary")
        
        update_data = {
            "fields": {
                "summary": firestore_value(summary),
                "sentiment": firestore_value(sentiment)
            }
        }
        
        url = get_firestore_url("articles", article_id)
        result = make_firestore_request("PATCH", url, update_data)
        
        if result and 'name' in result:
            print(f"✅ Article {article_id} summary updated successfully")
            return True
        else:
            print(f"❌ Failed to update article {article_id}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during update_article_summary: {e}")
        return False

def get_unalerted_articles() -> List[Dict]:
    """Get articles that haven't been alerted yet"""
    try:
        print(f"📢 DEBUG: Querying for unalerted articles...")
        
        # Get all articles and filter in Python (simpler than complex Firestore queries)
        all_articles = get_recent_articles(1000)
        unalerted = [
            article for article in all_articles 
            if not article.get('alerted', False) and article.get('sentiment') != 'Neutral'
        ]
        
        print(f"📢 Found {len(unalerted)} unalerted articles")
        return unalerted
        
    except Exception as e:
        print(f"❌ Exception during get_unalerted_articles: {e}")
        return []

def mark_article_alerted(article_id: str) -> bool:
    """Mark article as alerted"""
    try:
        print(f"📱 DEBUG: Marking article {article_id} as alerted")
        
        update_data = {
            "fields": {
                "alerted": firestore_value(True)
            }
        }
        
        url = get_firestore_url("articles", article_id)
        result = make_firestore_request("PATCH", url, update_data)
        
        if result and 'name' in result:
            print(f"✅ Article {article_id} marked as alerted")
            return True
        else:
            print(f"❌ Failed to mark article {article_id} as alerted")
            return False
            
    except Exception as e:
        print(f"❌ Exception during mark_article_alerted: {e}")
        return False

def test_database_connection() -> bool:
    """Test Firestore connection and operations"""
    try:
        print("🔍 Testing Firebase Firestore connection...")
        
        # Check environment variables
        print(f"🔑 FIREBASE_PROJECT_ID exists: {bool(FIREBASE_PROJECT_ID)}")
        print(f"🔑 FIREBASE_API_KEY exists: {bool(FIREBASE_API_KEY)}")
        
        if not FIREBASE_PROJECT_ID or not FIREBASE_API_KEY:
            print("❌ Missing Firebase credentials in environment")
            return False
        
        # Test basic query
        url = get_firestore_url("articles")
        result = make_firestore_request("GET", url + "?pageSize=1")
        
        if 'documents' in result:
            count = len(result.get('documents', []))
            print(f"📊 Connection successful - found {count} sample articles")
        elif 'error' in result:
            print(f"❌ Connection failed: {result['error']}")
            return False
        else:
            print(f"📊 Connection successful - empty collection")
        
        # Test insert with cleanup
        test_article = {
            'title': f'Test Article {datetime.now().strftime("%H:%M:%S")}',
            'description': 'Test description',
            'source': 'Test Source',
            'link': f'https://test.com/{datetime.now().timestamp()}',
            'published_at': datetime.now(timezone.utc).isoformat()
        }
        
        success = insert_article(**test_article)
        
        if success:
            print(f"✅ Test insert successful")
            return True
        else:
            print(f"❌ Test insert failed")
            return False
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False
        

        
      
