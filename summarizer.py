import os
import google.generativeai as genai
from typing import Tuple

# Configure Gemini AI
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("⚠️ GEMINI_API_KEY not found - AI analysis will be limited")
    GEMINI_AVAILABLE = False
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    GEMINI_AVAILABLE = True

def analyze_article_live(title: str, description: str) -> Tuple[str, str]:
    """Analyze article with Gemini AI and return summary and sentiment (database-free)"""
    try:
        if not GEMINI_AVAILABLE:
            return analyze_article_fallback(title, description)
        
        print(f"🤖 Analyzing with Gemini AI: {title[:50]}...")
        
        prompt = f"""
        Analyze this crude oil market news article and provide:
        1. A concise 2-sentence summary focusing on key market impact
        2. Market sentiment: Bullish, Bearish, or Neutral
        
        Title: {title}
        Description: {description}
        
        Format your response as:
        Summary: [your summary]
        Sentiment: [Bullish/Bearish/Neutral]
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        lines = text.split('\n')
        
        summary = ""
        sentiment = "Neutral"
        
        for line in lines:
            line = line.strip()
            if line.startswith('Summary:'):
                summary = line.replace('Summary:', '').strip()
            elif line.startswith('Sentiment:'):
                sentiment_text = line.replace('Sentiment:', '').strip()
                # Clean up sentiment to ensure it's one of our expected values
                if 'bullish' in sentiment_text.lower():
                    sentiment = "Bullish"
                elif 'bearish' in sentiment_text.lower():
                    sentiment = "Bearish"
                else:
                    sentiment = "Neutral"
        
        # Fallback if parsing failed
        if not summary:
            summary = "AI analysis completed - see full article for details."
        
        print(f"✅ AI Analysis complete: {sentiment} sentiment")
        return summary, sentiment
        
    except Exception as e:
        print(f"❌ Gemini AI error: {e}")
        return analyze_article_fallback(title, description)

def analyze_article_fallback(title: str, description: str) -> Tuple[str, str]:
    """Fallback keyword-based analysis when AI is unavailable"""
    try:
        print(f"🔄 Using fallback analysis for: {title[:50]}...")
        
        # Combine title and description for analysis
        text = (title + " " + description).lower()
        
        # Enhanced keyword lists for crude oil market
        bullish_keywords = [
            "rise", "rising", "up", "increase", "increasing", "boost", "surge", "rally", 
            "gains", "higher", "growing", "positive", "strong", "bullish", "recovery",
            "demand", "growth", "expansion", "optimistic", "upward", "improved"
        ]
        
        bearish_keywords = [
            "fall", "falling", "down", "decrease", "decreasing", "drop", "decline", 
            "crash", "losses", "lower", "negative", "weak", "bearish", "recession",
            "oversupply", "glut", "concerns", "worries", "downward", "slump", "plunge"
        ]
        
        # Count keyword occurrences
        bullish_count = sum(1 for word in bullish_keywords if word in text)
        bearish_count = sum(1 for word in bearish_keywords if word in text)
        
        # Determine sentiment with confidence threshold
        if bullish_count > bearish_count and bullish_count > 0:
            sentiment = "Bullish"
        elif bearish_count > bullish_count and bearish_count > 0:
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"
        
        # Generate basic summary
        if sentiment == "Bullish":
            summary = f"Market indicators suggest positive outlook for crude oil. Key factors driving bullish sentiment identified."
        elif sentiment == "Bearish":
            summary = f"Market analysis indicates potential downward pressure on crude oil. Bearish factors present in current conditions."
        else:
            summary = f"Market sentiment remains neutral with mixed signals. No clear directional bias identified."
        
        print(f"📊 Fallback analysis complete: {sentiment} sentiment")
        return summary, sentiment
        
    except Exception as e:
        print(f"❌ Fallback analysis error: {e}")
        return "Analysis unavailable", "Neutral"

def process_unanalyzed_articles():
    """Dummy function for backward compatibility with database-free architecture"""
    print("📝 Note: process_unanalyzed_articles called in live mode - returning 0")
    return 0

# For testing purposes
if __name__ == "__main__":
    print("🧪 Testing Gemini AI integration...")
    
    test_title = "Crude Oil Prices Rise on OPEC+ Production Cuts"
    test_description = "Oil futures gained 3% after OPEC+ announced extension of production cuts, supporting market sentiment amid strong demand outlook."
    
    summary, sentiment = analyze_article_live(test_title, test_description)
    
    print(f"✅ Test Results:")
    print(f"   Title: {test_title}")
    print(f"   Summary: {summary}")
    print(f"   Sentiment: {sentiment}")
    print("🎯 Gemini AI integration test complete!")
    
