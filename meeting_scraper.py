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
            
            # Find the meetings table
            meetings_table = soup.find('table')
            if meetings_table and meetings_table.find('caption', string=re.compile(r'Meetings Directory', re.IGNORECASE)):
                # Process table rows (skip header row)
                rows = meetings_table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 7:  # Ensure we have all expected columns
                        # Extract meeting info from table row
                        # Column structure: Date, Meeting, Agenda, Agenda Packet, Minutes, Video, View
                        date_text = cells[0].get_text(strip=True)
                        meeting_title = cells[1].get_text(strip=True)
                        
                        # Get "View Details" link from last column
                        view_link = cells[6].find('a')
                        meeting_url = ''
                        if view_link:
                            href = view_link.get('href', '')
                            if href and not href.startswith('http'):
                                meeting_url = self.base_url + href
                            else:
                                meeting_url = href
                        
                        # Skip if we don't have essential info
                        if not meeting_title or not meeting_url:
                            continue
                        
                        meeting = {
                            'title': meeting_title,
                            'url': meeting_url,
                            'date': date_text,
                            'video_url': '',
                            'documents': []
                        }
                        
                        # Extract document links from agenda, packet, and minutes columns
                        doc_columns = [
                            (cells[2], "Agenda"),       # Column 3: Agenda
                            (cells[3], "Packet"),       # Column 4: Agenda Packet  
                            (cells[4], "Minutes")       # Column 5: Minutes
                        ]
                        
                        for cell, doc_type in doc_columns:
                            doc_links = cell.find_all('a')
                            for doc_link in doc_links:
                                doc_url = doc_link.get('href', '')
                                if doc_url:
                                    if not doc_url.startswith('http'):
                                        doc_url = self.base_url + doc_url
                                    
                                    # Determine if it's PDF or HTML version
                                    link_type = "PDF" if doc_url.endswith('.pdf') else "HTML"
                                    doc_title = f"{doc_type} ({link_type})"
                                    
                                    meeting['documents'].append({
                                        'title': doc_title,
                                        'url': doc_url
                                    })
                        
                        meetings.append(meeting)
            
            # Fallback: look for meeting-related links if table method fails
            if not meetings:
                meeting_links = soup.find_all('a', href=re.compile(r'(meeting|council|commission)', re.IGNORECASE))
                
                for link in meeting_links:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    # Skip if it's a document link or empty
                    if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx']) or not title:
                        continue
                    
                    # Convert relative URLs to absolute
                    if href and not href.startswith('http'):
                        href = self.base_url + href
                    
                    meeting = {
                        'title': title,
                        'url': href,
                        'date': '',
                        'video_url': '',
                        'documents': []
                    }
                    meetings.append(meeting)
            
            return meetings
        except Exception as e:
            print(f"Error fetching meetings: {e}")
            return []
    
    def _parse_meeting_item(self, item) -> Optional[Dict[str, str]]:
        """Parse a meeting item from HTML."""
        try:
            if not item:
                return {
                    'title': "Unknown Meeting",
                    'url': '',
                    'date': '',
                    'video_url': '',
                    'documents': []
                }
            
            # Check if item is a div with an anchor inside, or an anchor itself
            if item.name == 'div' and item.find('a'):
                # Item is a div containing an anchor
                anchor = item.find('a')
                title = anchor.get_text(strip=True)
                href = anchor.get('href', '')
            else:
                # Item is an anchor itself
                title = item.get_text(strip=True)
                href = item.get('href', '')
            
            # Convert relative URLs to absolute
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
            
            # Extract date - look for various date patterns
            date_elem = soup.find(class_=re.compile(r'date', re.I)) or soup.find(string=re.compile(r'\d{1,2}/\d{1,2}/\d{4}'))
            if date_elem:
                details['date'] = date_elem if isinstance(date_elem, str) else date_elem.get_text(strip=True)
            
            # Extract video URL with improved logic
            video_url = self._extract_video_url(soup)
            if video_url:
                details['video_url'] = video_url
            
            # Extract document links
            doc_links = soup.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.I))
            for link in doc_links:
                doc_url = link.get('href', '')
                if doc_url and not doc_url.startswith('http'):
                    doc_url = self.base_url + doc_url
                
                # Get link text or determine type from URL
                link_text = link.get_text(strip=True)
                if not link_text:
                    if 'agenda' in doc_url.lower():
                        link_text = "Agenda"
                    elif 'packet' in doc_url.lower():
                        link_text = "Packet"
                    elif 'minutes' in doc_url.lower():
                        link_text = "Minutes"
                    else:
                        link_text = "Document"
                
                details['documents'].append({
                    'title': link_text,
                    'url': doc_url
                })
            
            return details
        except Exception as e:
            print(f"Error fetching meeting details: {e}")
            return {}
    
    def _extract_video_url(self, soup) -> str:
        """
        Extract video URL from meeting page HTML.
        Handles various video hosting platforms and embed formats.
        """
        try:
            # 1. Look for YouTube embeds
            youtube_iframe = soup.find('iframe', src=re.compile(r'youtube\.com/embed/([a-zA-Z0-9_-]+)', re.I))
            if youtube_iframe:
                src = youtube_iframe.get('src', '')
                # Extract video ID from embed URL
                match = re.search(r'youtube\.com/embed/([a-zA-Z0-9_-]+)', src)
                if match:
                    video_id = match.group(1)
                    # Convert to YouTube watch URL (note: this still requires special handling for transcription)
                    return f"https://www.youtube.com/watch?v={video_id}"
            
            # 2. Look for Vimeo embeds
            vimeo_iframe = soup.find('iframe', src=re.compile(r'player\.vimeo\.com/video/(\d+)', re.I))
            if vimeo_iframe:
                src = vimeo_iframe.get('src', '')
                match = re.search(r'player\.vimeo\.com/video/(\d+)', src)
                if match:
                    video_id = match.group(1)
                    return f"https://vimeo.com/{video_id}"
            
            # 3. Look for direct video file links
            video_link = soup.find('a', href=re.compile(r'\.(mp4|webm|ogg|avi|mov)$', re.I))
            if video_link:
                href = video_link.get('href', '')
                if href and not href.startswith('http'):
                    href = self.base_url + href
                return href
            
            # 4. Look for HTML5 video elements
            video_elem = soup.find('video')
            if video_elem:
                src = video_elem.get('src', '')
                if src:
                    if not src.startswith('http'):
                        src = self.base_url + src
                    return src
                
                # Check for source elements within video
                source_elem = video_elem.find('source')
                if source_elem:
                    src = source_elem.get('src', '')
                    if src:
                        if not src.startswith('http'):
                            src = self.base_url + src
                        return src
            
            # 5. Look for other iframe embeds (generic)
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src', '')
                if src and any(domain in src.lower() for domain in ['video', 'player', 'stream']):
                    if not src.startswith('http'):
                        if src.startswith('//'):
                            src = 'https:' + src
                        else:
                            src = self.base_url + src
                    return src
            
            # 6. Look for data attributes that might contain video URLs
            elements_with_video_data = soup.find_all(attrs=lambda x: x and isinstance(x, dict) and any(
                attr.lower() in ['data-video', 'data-src', 'data-url', 'data-video-url'] 
                for attr in x.keys()
            ))
            
            for elem in elements_with_video_data:
                for attr, value in elem.attrs.items():
                    if 'video' in attr.lower() or ('src' in attr.lower() and 'video' in str(value).lower()):
                        if value and isinstance(value, str):
                            if not value.startswith('http'):
                                if value.startswith('//'):
                                    value = 'https:' + value
                                else:
                                    value = self.base_url + value
                            return value
            
            return ''
            
        except Exception as e:
            print(f"Error extracting video URL: {e}")
            return ''
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if the URL is a YouTube URL."""
        return 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
    
    def is_vimeo_url(self, url: str) -> bool:
        """Check if the URL is a Vimeo URL.""" 
        return 'vimeo.com' in url.lower()
    
    def get_video_platform(self, url: str) -> str:
        """Determine the video hosting platform."""
        if self.is_youtube_url(url):
            return "YouTube"
        elif self.is_vimeo_url(url):
            return "Vimeo"
        elif any(ext in url.lower() for ext in ['.mp4', '.webm', '.ogg', '.avi', '.mov']):
            return "Direct Video File"
        else:
            return "Unknown"
    
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
    
    def get_document_context(self, documents: List[Dict[str, str]], max_docs: int = 3) -> str:
        """
        Format document URLs to provide as additional context for OpenAI.
        OpenAI can access and parse these URLs directly.
        
        Args:
            documents: List of document dictionaries with 'title' and 'url'
            max_docs: Maximum number of documents to include
            
        Returns:
            Formatted list of document URLs for OpenAI to access
        """
        if not documents:
            return ""
        
        context_parts = []
        context_parts.append("Meeting Documents Available:")
        
        # Prioritize HTML documents over PDFs for better accessibility
        html_docs = [doc for doc in documents if 'HTML' in doc.get('title', '')]
        pdf_docs = [doc for doc in documents if 'PDF' in doc.get('title', '')]
        other_docs = [doc for doc in documents if doc not in html_docs and doc not in pdf_docs]
        
        # Process in order of preference: HTML, PDF, others
        doc_count = 0
        for doc_list in [html_docs, pdf_docs, other_docs]:
            for doc in doc_list:
                if doc_count >= max_docs:
                    break
                
                context_parts.append(f"- {doc['title']}: {doc['url']}")
                doc_count += 1
                
            if doc_count >= max_docs:
                break
        
        if len(context_parts) > 1:  # More than just the header
            context_parts.append("\nPlease access and review these documents to provide additional context for the meeting summary.")
            return "\n".join(context_parts)
        else:
            return ""
