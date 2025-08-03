import os
import google.generativeai as genai
from database import get_recent_articles, update_article_summary

def configure_gemini():
    """Configure Gemini AI"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Please set GEMINI_API_KEY environment variable")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def analyze_article(title, description):
    """Analyze article and return summary + sentiment"""
    try:
        model = configure_gemini()
        
        prompt = f"""
        Analyze this crude oil related news article and provide:
        1. A concise 2-sentence summary
        2. Market sentiment: Bullish, Bearish, or Neutral
        
        Title: {title}
        Description: {description}
        
        Format your response as:
        Summary: [your summary]
        Sentiment: [Bullish/Bearish/Neutral]
        """
        
        response = model.generate_content(prompt)
        
        # Parse response
        text = response.text
        lines = text.strip().split('\n')
        
        summary = ""
        sentiment = "Neutral"
        
        for line in lines:
            if line.startswith('Summary:'):
                summary = line.replace('Summary:', '').strip()
            elif line.startswith('Sentiment:'):
                sentiment = line.replace('Sentiment:', '').strip()
        
        return summary, sentiment
        
    except Exception as e:
        print(f"Error analyzing article: {e}")
        return "Analysis failed", "Neutral"

def process_unanalyzed_articles():
    """Process articles that don't have summaries yet"""
    try:
        # Get articles without summaries
        articles = get_recent_articles(20)
        processed = 0
        
        for article in articles:
            if not article.get('summary'):
                print(f"Processing: {article['title'][:50]}...")
                
                summary, sentiment = analyze_article(
                    article['title'], 
                    article['description']
                )
                
                update_article_summary(
                    article['id'],
                    summary,
                    sentiment
                )
                
                processed += 1
        
        print(f"Processed {processed} articles")
        return processed
        
    except Exception as e:
        print(f"Error processing articles: {e}")
        return 0

if __name__ == "__main__":
    print("Starting article analysis...")
    count = process_unanalyzed_articles()
    print(f"Analysis complete. Processed {count} articles.")
  
