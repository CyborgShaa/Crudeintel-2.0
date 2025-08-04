import sqlite3
import json
from datetime import datetime
import os

# Database file path
DB_PATH = "crudeintel.db"

def init_database():
    """Initialize SQLite database with news_articles table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            source TEXT,
            link TEXT UNIQUE,
            published_at TEXT,
            summary TEXT,
            sentiment TEXT,
            alerted BOOLEAN DEFAULT FALSE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ SQLite database initialized successfully")

def insert_article(title, description, source, link, published_at, summary=None, sentiment=None):
    """Insert a new article into the database with debug logging"""
    try:
        print(f"💾 DEBUG: Inserting article '{title[:50]}...' from {source}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO news_articles 
            (title, description, source, link, published_at, summary, sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, source, link, published_at, summary, sentiment))
        
        if cursor.rowcount > 0:
            print(f"✅ Insert succeeded: 1 record added")
            conn.commit()
            conn.close()
            return True
        else:
            print(f"📋 Article already exists (duplicate link)")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Exception during insert_article: {e}")
        return False

def get_recent_articles(limit=50):
    """Get recent articles from database with debug logging"""
    try:
        print(f"📚 DEBUG: Querying SQLite for {limit} recent articles...")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news_articles 
            ORDER BY published_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        articles = [dict(row) for row in rows]
        
        print(f"📚 Retrieved {len(articles)} articles from SQLite database")
        conn.close()
        return articles
        
    except Exception as e:
        print(f"❌ Exception during get_recent_articles: {e}")
        return []

def check_article_exists(link):
    """Check if article already exists in database with debug logging"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM news_articles WHERE link = ?', (link,))
        exists = cursor.fetchone()[0] > 0
        
        print(f"🔎 Article exists check for '{link[:50]}...': {exists}")
        conn.close()
        return exists
        
    except Exception as e:
        print(f"❌ Exception during check_article_exists: {e}")
        return False

def update_article_summary(article_id, summary, sentiment):
    """Update article with AI-generated summary and sentiment with debug logging"""
    try:
        print(f"🤖 DEBUG: Updating article {article_id} with AI summary and sentiment")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE news_articles 
            SET summary = ?, sentiment = ? 
            WHERE id = ?
        ''', (summary, sentiment, article_id))
        
        if cursor.rowcount > 0:
            print(f"✅ Article {article_id} summary updated successfully")
            conn.commit()
            conn.close()
            return True
        else:
            print(f"❌ No article found with ID {article_id}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Exception during update_article_summary: {e}")
        return False

def get_unalerted_articles():
    """Get articles that haven't been alerted yet with debug logging"""
    try:
        print(f"📢 DEBUG: Querying for unalerted articles...")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news_articles 
            WHERE alerted = FALSE AND sentiment != 'Neutral'
            ORDER BY published_at DESC
        ''')
        
        rows = cursor.fetchall()
        articles = [dict(row) for row in rows]
        
        print(f"📢 Found {len(articles)} unalerted articles")
        conn.close()
        return articles
        
    except Exception as e:
        print(f"❌ Exception during get_unalerted_articles: {e}")
        return []

def mark_article_alerted(article_id):
    """Mark article as alerted with debug logging"""
    try:
        print(f"📱 DEBUG: Marking article {article_id} as alerted")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE news_articles 
            SET alerted = TRUE 
            WHERE id = ?
        ''', (article_id,))
        
        if cursor.rowcount > 0:
            print(f"✅ Article {article_id} marked as alerted")
            conn.commit()
            conn.close()
            return True
        else:
            print(f"❌ No article found with ID {article_id}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Exception during mark_article_alerted: {e}")
        return False

def test_database_connection():
    """Test database connection and operations for debugging"""
    try:
        print("🔍 Testing SQLite database connection...")
        
        # Initialize database
        init_database()
        
        # Test basic query
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM news_articles')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Connection successful - found {count} existing articles")
        
        # Test insert with cleanup
        test_article_data = {
            'title': f'Test Article {datetime.now().strftime("%H:%M:%S")}',
            'description': 'Test description',
            'source': 'Test Source',
            'link': f'https://test.com/{datetime.now().timestamp()}',
            'published_at': datetime.now().isoformat()
        }
        
        result = insert_article(**test_article_data)
        
        if result:
            print(f"✅ Test insert successful")
            
            # Clean up test data
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM news_articles WHERE source = "Test Source"')
            conn.commit()
            conn.close()
            print("🧹 Test data cleaned up")
            
            return True
        else:
            print(f"❌ Test insert failed")
            return False
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

# Initialize database on import
init_database()

        
      
