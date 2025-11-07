import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Optional, List

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False


class YouTubeTranscriptService:
    """Service to get transcripts from YouTube videos using multiple methods"""
    
    def __init__(self):
        self.base_url = "https://youtubetotranscript.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_transcript(self, youtube_url: str) -> Optional[str]:
        """
        Get transcript from a YouTube URL using multiple methods
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Transcript text or None if failed
        """
        try:
            # Check if it's a valid YouTube URL
            if not self._is_youtube_url(youtube_url):
                print("Error: Not a valid YouTube URL")
                return None
            
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                print("Error: Could not extract video ID")
                return None
            
            # Try YouTube Transcript API first (most reliable)
            if YOUTUBE_API_AVAILABLE:
                transcript = self._get_transcript_via_api(video_id)
                if transcript:
                    return transcript
            
            # Fallback to manual instructions
            return self._get_manual_instructions(youtube_url)
        
        except Exception as e:
            print(f"Error getting YouTube transcript: {e}")
            return None
    
    def _get_transcript_via_api(self, video_id: str) -> Optional[str]:
        """Get transcript using youtube-transcript-api"""
        try:
            print(f"Attempting to get transcript for video ID: {video_id}")
            
            # Create API instance
            api = YouTubeTranscriptApi()
            
            # Get available transcripts
            transcript_list = api.list(video_id)
            
            # Try to get English transcript first
            try:
                # Find English transcript
                for transcript in transcript_list:
                    if transcript.language_code in ['en', 'en-US', 'en-GB']:
                        transcript_data = transcript.fetch()
                        # Extract text from FetchedTranscriptSnippet objects
                        full_text = ' '.join([snippet.text for snippet in transcript_data])
                        print(f"✅ Successfully retrieved transcript ({len(full_text)} characters)")
                        return full_text
                
                # If no English, get the first available
                for transcript in transcript_list:
                    try:
                        transcript_data = transcript.fetch()
                        # Extract text from FetchedTranscriptSnippet objects
                        full_text = ' '.join([snippet.text for snippet in transcript_data])
                        print(f"✅ Successfully retrieved transcript in {transcript.language} ({len(full_text)} characters)")
                        return full_text
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"Error fetching transcript: {e}")
                return None
            
            print("No transcripts could be fetched")
            return None
            
        except Exception as e:
            print(f"Error using YouTube Transcript API: {e}")
            return None
    
    
    def _get_manual_instructions(self, youtube_url: str) -> str:
        """Return manual transcription instructions"""
        return f"""
📋 MANUAL TRANSCRIPTION OPTIONS

🤖 **Option 1: YouTube Auto-Captions (if available)**
1. Go to: {youtube_url}
2. Click the "CC" button to enable captions
3. Click the "⚙️" settings button
4. Select "Open transcript"
5. Copy the transcript text

🌐 **Option 2: YouTubeToTranscript.com**
1. Go to: https://youtubetotranscript.com/
2. Paste this URL: {youtube_url}
3. Click "Get Transcript"
4. Copy the result and paste it into the app

💡 **Note:** Some videos may not have transcripts available.
"""
    
    def get_available_languages(self, youtube_url: str) -> List[str]:
        """Get list of available transcript languages for a YouTube video"""
        try:
            if not YOUTUBE_API_AVAILABLE:
                return []
            
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                return []
            
            available_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            languages = []
            
            for transcript in available_transcripts:
                languages.append(transcript.language)
            
            return languages
            
        except Exception as e:
            print(f"Error getting available languages: {e}")
            return []
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'youtube\.com/embed/'
        ]
        return any(re.search(pattern, url, re.I) for pattern in youtube_patterns)
    
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url, re.I)
            if match:
                return match.group(1)
        return None


# Example usage
if __name__ == "__main__":
    service = YouTubeTranscriptService()
    
    # Test with a YouTube URL
    test_url = "https://www.youtube.com/watch?v=5fujbzcLG5M"
    transcript = service.get_transcript(test_url)
    
    if transcript:
        print("Transcript retrieved:")
        print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
    else:
        print("Failed to get transcript")