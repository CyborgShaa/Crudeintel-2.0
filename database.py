import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError("Please set SUPABASE_URL and SUPABASE_KEY environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

def insert_article(title, description, source, link, published_at, summary=None, sentiment=None):
    """Insert a new article into the database with debug logging"""
    try:
        data = {
            'title': title,
            'description': description,
            'source': source,
            'link': link,
            'published_at': published_at,
            'summary': summary,
            'sentiment': sentiment
        }
        
        print(f"💾 DEBUG: Inserting article '{title[:50]}...' from {source}")
        response = supabase.table('news_articles').insert(data).execute()
        
        if response.error:
            print(f"❌ Insert failed: {response.error.message}")
            return None
        else:
            print(f"✅ Insert succeeded: {len(response.data)} records added")
            return response.data
            
    except Exception as e:
        print(f"❌ Exception during insert_article: {e}")
        return None

def get_recent_articles(limit=50):
    """Get recent articles from database with debug logging"""
    try:
        print(f"📚 DEBUG: Querying database for {limit} recent articles...")
        response = supabase.table('news_articles').select('*').order('published_at', desc=True).limit(limit).execute()
        
        if response.error:
            print(f"❌ Error fetching articles: {response.error.message}")
            return []
            
        print(f"📚 Retrieved {len(response.data)} articles from database")
        return response.data
        
    except Exception as e:
        print(f"❌ Exception during get_recent_articles: {e}")
        return []

def check_article_exists(link):
    """Check if article already exists in database with debug logging"""
    try:
        response = supabase.table('news_articles').select('id').eq('link', link).execute()
        
        if response.error:
            print(f"❌ Error checking article existence: {response.error.message}")
            return False
            
        exists = len(response.data) > 0
        print(f"🔎 Article exists check for '{link[:50]}...': {exists}")
        return exists
        
    except Exception as e:
        print(f"❌ Exception during check_article_exists: {e}")
        return False

def update_article_summary(article_id, summary, sentiment):
    """Update article with AI-generated summary and sentiment with debug logging"""
    try:
        print(f"🤖 DEBUG: Updating article {article_id} with AI summary and sentiment")
        response = supabase.table('news_articles').update({
            'summary': summary,
            'sentiment': sentiment
        }).eq('id', article_id).execute()
        
        if response.error:
            print(f"❌ Update failed: {response.error.message}")
            return None
            
        print(f"✅ Article {article_id} summary updated successfully")
        return response.data
        
    except Exception as e:
        print(f"❌ Exception during update_article_summary: {e}")
        return None

def get_unalerted_articles():
    """Get articles that haven't been alerted yet with debug logging"""
    try:
        print(f"📢 DEBUG: Querying for unalerted articles...")
        response = supabase.table('news_articles').select('*').eq('alerted', False).neq('sentiment', 'Neutral').execute()
        
        if response.error:
            print(f"❌ Error fetching unalerted articles: {response.error.message}")
            return []
            
        print(f"📢 Found {len(response.data)} unalerted articles")
        return response.data
        
    except Exception as e:
        print(f"❌ Exception during get_unalerted_articles: {e}")
        return []

def mark_article_alerted(article_id):
    """Mark article as alerted with debug logging"""
    try:
        print(f"📱 DEBUG: Marking article {article_id} as alerted")
        response = supabase.table('news_articles').update({'alerted': True}).eq('id', article_id).execute()
        
        if response.error:
            print(f"❌ Mark alerted failed: {response.error.message}")
            return None
            
        print(f"✅ Article {article_id} marked as alerted")
        return response.data
        
    except Exception as e:
        print(f"❌ Exception during mark_article_alerted: {e}")
        return None

def test_database_connection():
    """Test database connection and operations for debugging"""
    try:
        print("🔍 Testing Supabase database connection...")
        
        # Check environment variables
        print(f"🔑 SUPABASE_URL exists: {bool(supabase_url)}")
        print(f"🔑 SUPABASE_KEY exists: {bool(supabase_key)}")
        
        # Test basic query
        response = supabase.table('news_articles').select('*').limit(3).execute()
        
        if response.error:
            print(f"❌ Connection test failed: {response.error.message}")
            return False
            
        print(f"📊 Connection successful - found {len(response.data)} existing articles")
        
        # Test insert with cleanup
        test_article = {
            'title': f'Test Article {datetime.now().strftime("%H:%M:%S")}',
            'description': 'Test description',
            'source': 'Test Source',
            'link': f'https://test.com/{datetime.now().timestamp()}',
            'published_at': datetime.now().isoformat()
        }
        
        insert_response = supabase.table('news_articles').insert(test_article).execute()
        
        if insert_response.error:
            print(f"❌ Test insert failed: {insert_response.error.message}")
            return False
            
        print(f"✅ Test insert successful")
        
        # Clean up test data
        supabase.table('news_articles').delete().eq('source', 'Test Source').execute()
        print("🧹 Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False
        
      
