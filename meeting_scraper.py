import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re


class MeetingScraper:
    """Scraper for fetching meeting information from Snoqualmie's municode meetings site."""
    
    def __init__(self, base_url: str = "https://snoqualmie-wa.municodemeetings.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_meetings(self) -> List[Dict[str, str]]:
        """
        Fetch list of available meetings.
        
        Returns:
            List of meeting dictionaries with title, date, video_url, and documents
        """
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            meetings = []
            
            # Find meeting entries - this will need to be adjusted based on actual HTML structure
            meeting_items = soup.find_all('div', class_='meeting-item') or soup.find_all('a', href=re.compile(r'/meetings/'))
            
            for item in meeting_items:
                meeting = self._parse_meeting_item(item)
                if meeting:
                    meetings.append(meeting)
            
            return meetings
        except Exception as e:
            print(f"Error fetching meetings: {e}")
            return []
    
    def _parse_meeting_item(self, item) -> Optional[Dict[str, str]]:
        """Parse a meeting item from HTML."""
        try:
            # Extract meeting details - adjust selectors based on actual HTML
            title = item.get_text(strip=True) if item else "Unknown Meeting"
            href = item.get('href', '')
            
            if href and not href.startswith('http'):
                href = self.base_url + href
            
            return {
                'title': title,
                'url': href,
                'date': '',  # Will be populated when meeting details are fetched
                'video_url': '',
                'documents': []
            }
        except Exception as e:
            print(f"Error parsing meeting item: {e}")
            return None
    
    def get_meeting_details(self, meeting_url: str) -> Dict[str, any]:
        """
        Fetch detailed information for a specific meeting.
        
        Args:
            meeting_url: URL of the meeting page
            
        Returns:
            Dictionary with meeting details including video URL and documents
        """
        try:
            response = self.session.get(meeting_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = {
                'title': '',
                'date': '',
                'video_url': '',
                'documents': []
            }
            
            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                details['title'] = title_elem.get_text(strip=True)
            
            # Extract date
            date_elem = soup.find(class_='meeting-date') or soup.find(string=re.compile(r'\d{1,2}/\d{1,2}/\d{4}'))
            if date_elem:
                details['date'] = date_elem if isinstance(date_elem, str) else date_elem.get_text(strip=True)
            
            # Extract video URL - look for video player or video links
            video_elem = soup.find('video') or soup.find('iframe', src=re.compile(r'video|vimeo|youtube'))
            if video_elem:
                details['video_url'] = video_elem.get('src', '')
            else:
                # Look for video links
                video_link = soup.find('a', href=re.compile(r'\.(mp4|webm|ogg)$', re.I))
                if video_link:
                    details['video_url'] = video_link.get('href', '')
            
            # Extract document links
            doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
            for link in doc_links:
                doc_url = link.get('href', '')
                if doc_url and not doc_url.startswith('http'):
                    doc_url = self.base_url + doc_url
                details['documents'].append({
                    'title': link.get_text(strip=True),
                    'url': doc_url
                })
            
            return details
        except Exception as e:
            print(f"Error fetching meeting details: {e}")
            return {}
    
    def download_document(self, doc_url: str) -> Optional[bytes]:
        """
        Download a document from the given URL.
        
        Args:
            doc_url: URL of the document
            
        Returns:
            Document content as bytes or None if failed
        """
        try:
            response = self.session.get(doc_url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading document: {e}")
            return None
