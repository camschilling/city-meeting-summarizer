import requests
import time
from typing import Optional, Dict
import os


class TranscriptService:
    """Service for transcribing videos using transcriptapi.com."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.transcriptapi.com/v1"  # Placeholder URL
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def transcribe_video(self, video_url: str, language: str = "en") -> Optional[Dict]:
        """
        Submit a video for transcription.
        
        Args:
            video_url: URL of the video to transcribe
            language: Language code (default: en)
            
        Returns:
            Dictionary with job_id and status or None if failed
        """
        try:
            # Note: This is a generic implementation. The actual API endpoints
            # and parameters may differ based on transcriptapi.com documentation
            payload = {
                'video_url': video_url,
                'language': language
            }
            
            response = requests.post(
                f'{self.base_url}/transcribe',
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Error submitting video for transcription: {e}")
            return None
    
    def get_transcript_status(self, job_id: str) -> Optional[Dict]:
        """
        Check the status of a transcription job.
        
        Args:
            job_id: ID of the transcription job
            
        Returns:
            Dictionary with status information or None if failed
        """
        try:
            response = requests.get(
                f'{self.base_url}/transcribe/{job_id}',
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Error checking transcript status: {e}")
            return None
    
    def wait_for_transcript(self, job_id: str, max_wait_time: int = 3600, poll_interval: int = 30) -> Optional[str]:
        """
        Wait for transcription to complete and return the transcript.
        
        Args:
            job_id: ID of the transcription job
            max_wait_time: Maximum time to wait in seconds (default: 1 hour)
            poll_interval: Time between status checks in seconds (default: 30)
            
        Returns:
            Transcript text or None if failed or timed out
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_transcript_status(job_id)
            
            if not status:
                return None
            
            if status.get('status') == 'completed':
                return status.get('transcript', '')
            elif status.get('status') == 'failed':
                print(f"Transcription failed: {status.get('error', 'Unknown error')}")
                return None
            
            time.sleep(poll_interval)
        
        print(f"Transcription timed out after {max_wait_time} seconds")
        return None
    
    def transcribe_and_wait(self, video_url: str, language: str = "en") -> Optional[str]:
        """
        Convenience method to submit video and wait for transcript.
        
        Args:
            video_url: URL of the video to transcribe
            language: Language code (default: en)
            
        Returns:
            Transcript text or None if failed
        """
        result = self.transcribe_video(video_url, language)
        
        if not result or 'job_id' not in result:
            return None
        
        return self.wait_for_transcript(result['job_id'])
