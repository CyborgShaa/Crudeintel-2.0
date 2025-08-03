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
    """Insert a new article into the database"""
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
        
        response = supabase.table('news_articles').insert(data).execute()
        return response.data
    except Exception as e:
        print(f"Error inserting article: {e}")
        return None

def get_recent_articles(limit=50):
    """Get recent articles from database"""
    try:
        response = supabase.table('news_articles').select('*').order('published_at', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching articles: {e}")
        return []

def check_article_exists(link):
    """Check if article already exists in database"""
    try:
        response = supabase.table('news_articles').select('id').eq('link', link).execute()
        return len(response.data) > 0
    except Exception as e:
        print(f"Error checking article existence: {e}")
        return False

def update_article_summary(article_id, summary, sentiment):
    """Update article with AI-generated summary and sentiment"""
    try:
        response = supabase.table('news_articles').update({
            'summary': summary,
            'sentiment': sentiment
        }).eq('id', article_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating article: {e}")
        return None

def get_unalerted_articles():
    """Get articles that haven't been alerted yet"""
    try:
        response = supabase.table('news_articles').select('*').eq('alerted', False).neq('sentiment', 'Neutral').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching unalerted articles: {e}")
        return []

def mark_article_alerted(article_id):
    """Mark article as alerted"""
    try:
        response = supabase.table('news_articles').update({'alerted': True}).eq('id', article_id).execute()
        return response.data
    except Exception as e:
        print(f"Error marking article as alerted: {e}")
        return None
      
