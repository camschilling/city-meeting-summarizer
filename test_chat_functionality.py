#!/usr/bin/env python3
"""
Test script to verify the chat functionality works with OpenAI
"""

import os
from dotenv import load_dotenv
from summarizer_service import SummarizerService

# Load environment variables
load_dotenv()

def test_chat_functionality():
    """Test the chat functionality independently."""
    
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if not openai_key:
        print("❌ OpenAI API key not found")
        return False
    
    try:
        # Initialize summarizer
        summarizer = SummarizerService(openai_key)
        
        # Test sample meeting summary
        sample_summary = """
        City Council Meeting - November 6, 2024
        
        Key Decisions:
        1. Approved budget allocation for park renovation ($250,000)
        2. Discussed new traffic light installation on Main Street
        3. Public comment period addressed noise complaints
        
        Action Items:
        - Staff to research traffic light costs
        - Schedule public hearing for budget review
        """
        
        # Test chat messages
        messages = [
            {"role": "system", "content": f"You are an AI assistant helping analyze a city meeting. The meeting summary is: {sample_summary}. Answer questions about the meeting based on this summary."},
            {"role": "user", "content": "What was the main budget decision made?"}
        ]
        
        # Test API call
        response = summarizer.client.chat.completions.create(
            model=summarizer.model,
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        print("✅ Chat functionality test successful!")
        print(f"📝 Sample response: {ai_response}")
        return True
        
    except Exception as e:
        print(f"❌ Chat functionality test failed: {e}")
        return False

if __name__ == "__main__":
    test_chat_functionality()