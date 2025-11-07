import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path to import meeting_scraper
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from meeting_scraper import MeetingScraper


class TestMeetingScraper:
    """Test suite for MeetingScraper class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.scraper = MeetingScraper()
        self.base_url = "https://snoqualmie-wa.municodemeetings.com"
    
    def test_init_default_url(self):
        """Test initialization with default URL."""
        scraper = MeetingScraper()
        assert scraper.base_url == "https://snoqualmie-wa.municodemeetings.com"
        assert scraper.session is not None
        assert "Mozilla/5.0" in scraper.session.headers['User-Agent']
    
    def test_init_custom_url(self):
        """Test initialization with custom URL."""
        custom_url = "https://example.com"
        scraper = MeetingScraper(custom_url)
        assert scraper.base_url == custom_url
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meetings_success(self, mock_get):
        """Test successful meeting list retrieval."""
        # Mock HTML response
        mock_html = """
        <html>
            <body>
                <div class="meeting-item">
                    <a href="/meetings/123">City Council Meeting - Jan 15, 2024</a>
                </div>
                <div class="meeting-item">
                    <a href="/meetings/124">Planning Commission - Jan 20, 2024</a>
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        meetings = self.scraper.get_meetings()
        
        assert len(meetings) == 2
        assert meetings[0]['title'] == "City Council Meeting - Jan 15, 2024"
        assert meetings[0]['url'] == f"{self.base_url}/meetings/123"
        assert meetings[1]['title'] == "Planning Commission - Jan 20, 2024"
        assert meetings[1]['url'] == f"{self.base_url}/meetings/124"
        mock_get.assert_called_once_with(self.base_url)
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meetings_with_href_pattern(self, mock_get):
        """Test meeting retrieval when using href pattern fallback."""
        # Mock HTML without meeting-item class but with href pattern
        mock_html = """
        <html>
            <body>
                <a href="/meetings/125">Board Meeting - Feb 1, 2024</a>
                <a href="/other/page">Not a meeting</a>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        meetings = self.scraper.get_meetings()
        
        assert len(meetings) == 1
        assert meetings[0]['title'] == "Board Meeting - Feb 1, 2024"
        assert meetings[0]['url'] == f"{self.base_url}/meetings/125"
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meetings_network_error(self, mock_get):
        """Test handling of network errors during meeting retrieval."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        meetings = self.scraper.get_meetings()
        
        assert meetings == []
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meetings_empty_response(self, mock_get):
        """Test handling of empty HTML response."""
        mock_html = "<html><body></body></html>"
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        meetings = self.scraper.get_meetings()
        
        assert meetings == []
    
    def test_parse_meeting_item_with_text_and_href(self):
        """Test parsing meeting item with text and href."""
        html = '<a href="/meetings/123">City Council - Jan 15</a>'
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.find('a')
        
        result = self.scraper._parse_meeting_item(item)
        
        assert result is not None
        assert result['title'] == "City Council - Jan 15"
        assert result['url'] == f"{self.base_url}/meetings/123"
        assert result['date'] == ''
        assert result['video_url'] == ''
        assert result['documents'] == []
    
    def test_parse_meeting_item_with_full_url(self):
        """Test parsing meeting item with full URL."""
        html = '<a href="https://example.com/meetings/123">Meeting Title</a>'
        soup = BeautifulSoup(html, 'html.parser')
        item = soup.find('a')
        
        result = self.scraper._parse_meeting_item(item)
        
        assert result['url'] == "https://example.com/meetings/123"
    
    def test_parse_meeting_item_none(self):
        """Test parsing None meeting item."""
        result = self.scraper._parse_meeting_item(None)
        
        assert result is not None
        assert result['title'] == "Unknown Meeting"
        assert result['url'] == ""
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meeting_details_success(self, mock_get):
        """Test successful meeting details retrieval."""
        mock_html = """
        <html>
            <head><title>City Council Meeting - January 15, 2024</title></head>
            <body>
                <h1>City Council Meeting</h1>
                <div class="meeting-date">01/15/2024</div>
                <video src="/videos/meeting123.mp4"></video>
                <a href="/docs/agenda.pdf">Meeting Agenda</a>
                <a href="/docs/minutes.pdf">Meeting Minutes</a>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        details = self.scraper.get_meeting_details("https://example.com/meeting/123")
        
        assert details['title'] == "City Council Meeting"
        assert details['date'] == "01/15/2024"
        # Video URL should be converted to absolute URL
        assert details['video_url'] == f"{self.base_url}/videos/meeting123.mp4"
        assert len(details['documents']) == 2
        assert details['documents'][0]['title'] == "Meeting Agenda"
        assert details['documents'][0]['url'] == f"{self.base_url}/docs/agenda.pdf"
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meeting_details_with_iframe_video(self, mock_get):
        """Test meeting details with iframe video."""
        mock_html = """
        <html>
            <body>
                <h1>Meeting Title</h1>
                <iframe src="https://vimeo.com/player/123456"></iframe>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        details = self.scraper.get_meeting_details("https://example.com/meeting/123")
        
        assert details['video_url'] == "https://vimeo.com/player/123456"
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meeting_details_with_video_link(self, mock_get):
        """Test meeting details with video link."""
        mock_html = """
        <html>
            <body>
                <h1>Meeting Title</h1>
                <a href="/videos/meeting.mp4">Watch Video</a>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = mock_html.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        details = self.scraper.get_meeting_details("https://example.com/meeting/123")
        
        # Video URL should be converted to absolute URL
        assert details['video_url'] == f"{self.base_url}/videos/meeting.mp4"
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meeting_details_network_error(self, mock_get):
        """Test handling of network errors during meeting details retrieval."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        details = self.scraper.get_meeting_details("https://example.com/meeting/123")
        
        assert details == {}
    
    @patch('meeting_scraper.requests.Session.get')
    def test_download_document_success(self, mock_get):
        """Test successful document download."""
        mock_content = b"PDF file content"
        mock_response = Mock()
        mock_response.content = mock_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        content = self.scraper.download_document("https://example.com/doc.pdf")
        
        assert content == mock_content
        mock_get.assert_called_once_with("https://example.com/doc.pdf")
    
    @patch('meeting_scraper.requests.Session.get')
    def test_download_document_network_error(self, mock_get):
        """Test handling of network errors during document download."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        content = self.scraper.download_document("https://example.com/doc.pdf")
        
        assert content is None
    
    @patch('meeting_scraper.requests.Session.get')
    def test_download_document_http_error(self, mock_get):
        """Test handling of HTTP errors during document download."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        content = self.scraper.download_document("https://example.com/doc.pdf")
        
        assert content is None
    
    def test_get_document_context_with_documents(self):
        """Test document context generation with various document types."""
        documents = [
            {'title': 'Meeting Agenda', 'url': 'https://example.com/agenda.html'},
            {'title': 'Council Packet', 'url': 'https://example.com/packet.pdf'},
            {'title': 'Meeting Minutes', 'url': 'https://example.com/minutes.html'}
        ]
        
        context = self.scraper.get_document_context(documents)
        
        # Check basic structure
        assert context.startswith("Meeting Documents Available:")
        assert "- Meeting Agenda: https://example.com/agenda.html" in context
        assert "- Council Packet: https://example.com/packet.pdf" in context
        assert "- Meeting Minutes: https://example.com/minutes.html" in context
        assert "Please access and review these documents" in context
    
    def test_get_document_context_no_documents(self):
        """Test document context generation with no documents."""
        documents = []
        
        context = self.scraper.get_document_context(documents)
        
        assert context == ""
    
    def test_get_document_context_missing_documents_key(self):
        """Test document context generation when documents key is missing."""
        # Test with empty dictionary as input since method expects a list
        context = self.scraper.get_document_context({})
        
        assert context == ""
    
    def test_get_document_context_with_type_detection(self):
        """Test document context with automatic type detection."""
        documents = [
            {'title': 'Agenda', 'url': 'https://example.com/agenda.pdf'},
            {'title': 'Minutes', 'url': 'https://example.com/minutes.html'},
            {'title': 'Report', 'url': 'https://example.com/report.doc'}
        ]
        
        context = self.scraper.get_document_context(documents)
        
        # Check that documents are included in the output
        assert "- Agenda: https://example.com/agenda.pdf" in context
        assert "- Minutes: https://example.com/minutes.html" in context
        assert "- Report: https://example.com/report.doc" in context
    
    def test_get_document_context_url_formatting(self):
        """Test that document URLs are properly formatted."""
        documents = [
            {'title': 'Test Document', 'url': '/relative/path/doc.pdf'},
            {'title': 'Full URL Document', 'url': 'https://example.com/doc.pdf'}
        ]
        
        context = self.scraper.get_document_context(documents)
        
        # Both relative and absolute URLs should be preserved as-is
        assert "- Test Document: /relative/path/doc.pdf" in context
        assert "- Full URL Document: https://example.com/doc.pdf" in context
    
    def test_get_document_context_empty_title(self):
        """Test document context with empty titles."""
        documents = [
            {'title': '', 'url': 'https://example.com/doc1.pdf'},
            {'title': 'Valid Title', 'url': 'https://example.com/doc2.pdf'}
        ]
        
        context = self.scraper.get_document_context(documents)
        
        # Should handle empty titles gracefully
        assert "Meeting Documents Available:" in context
        assert "https://example.com/doc1.pdf" in context
        assert "https://example.com/doc2.pdf" in context
        assert "- Valid Title: https://example.com/doc2.pdf" in context
    
    def test_get_document_context_max_docs_limit(self):
        """Test that max_docs parameter limits the number of documents."""
        documents = [
            {'title': 'Doc 1', 'url': 'https://example.com/doc1.pdf'},
            {'title': 'Doc 2', 'url': 'https://example.com/doc2.pdf'},
            {'title': 'Doc 3', 'url': 'https://example.com/doc3.pdf'},
            {'title': 'Doc 4', 'url': 'https://example.com/doc4.pdf'},
        ]
        
        context = self.scraper.get_document_context(documents, max_docs=2)
        
        # Should only include 2 documents
        assert "- Doc 1: https://example.com/doc1.pdf" in context
        assert "- Doc 2: https://example.com/doc2.pdf" in context
        assert "https://example.com/doc3.pdf" not in context
        assert "https://example.com/doc4.pdf" not in context