import unittest
from unittest.mock import Mock, patch, MagicMock
from meeting_scraper import MeetingScraper
from transcript_service import TranscriptService
from summarizer_service import SummarizerService


class TestMeetingScraper(unittest.TestCase):
    """Test cases for MeetingScraper class."""
    
    def setUp(self):
        self.scraper = MeetingScraper()
    
    def test_init(self):
        """Test MeetingScraper initialization."""
        self.assertEqual(self.scraper.base_url, "https://snoqualmie-wa.municodemeetings.com")
        self.assertIsNotNone(self.scraper.session)
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meetings_success(self, mock_get):
        """Test successful meeting fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body><a href="/meetings/1">Test Meeting</a></body></html>'
        mock_get.return_value = mock_response
        
        meetings = self.scraper.get_meetings()
        self.assertIsInstance(meetings, list)
    
    @patch('meeting_scraper.requests.Session.get')
    def test_get_meetings_error(self, mock_get):
        """Test meeting fetch with network error."""
        mock_get.side_effect = Exception("Network error")
        
        meetings = self.scraper.get_meetings()
        self.assertEqual(meetings, [])
    
    def test_parse_meeting_item(self):
        """Test parsing of meeting item."""
        mock_item = Mock()
        mock_item.get_text.return_value = "Test Meeting"
        mock_item.get.return_value = "/meetings/1"
        
        meeting = self.scraper._parse_meeting_item(mock_item)
        self.assertIsNotNone(meeting)
        self.assertEqual(meeting['title'], "Test Meeting")


class TestTranscriptService(unittest.TestCase):
    """Test cases for TranscriptService class."""
    
    def setUp(self):
        self.service = TranscriptService("test_api_key")
    
    def test_init(self):
        """Test TranscriptService initialization."""
        self.assertEqual(self.service.api_key, "test_api_key")
        self.assertIn('Authorization', self.service.headers)
    
    @patch('transcript_service.requests.post')
    def test_transcribe_video_success(self, mock_post):
        """Test successful video transcription submission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'job_id': '123', 'status': 'processing'}
        mock_post.return_value = mock_response
        
        result = self.service.transcribe_video("http://example.com/video.mp4")
        self.assertIsNotNone(result)
        self.assertEqual(result['job_id'], '123')
    
    @patch('transcript_service.requests.post')
    def test_transcribe_video_error(self, mock_post):
        """Test video transcription with error."""
        mock_post.side_effect = Exception("API error")
        
        result = self.service.transcribe_video("http://example.com/video.mp4")
        self.assertIsNone(result)


class TestSummarizerService(unittest.TestCase):
    """Test cases for SummarizerService class."""
    
    def setUp(self):
        self.service = SummarizerService("test_api_key")
    
    def test_init(self):
        """Test SummarizerService initialization."""
        self.assertIsNotNone(self.service.client)
        self.assertEqual(self.service.model, "gpt-4o-mini")
    
    def test_build_summary_prompt(self):
        """Test prompt building."""
        prompt = self.service._build_summary_prompt(
            transcript="Test transcript",
            meeting_title="Test Meeting",
            meeting_date="2025-01-01",
            additional_context=""
        )
        self.assertIn("Test transcript", prompt)
        self.assertIn("Test Meeting", prompt)
        self.assertIn("2025-01-01", prompt)
    
    @patch('summarizer_service.OpenAI')
    def test_summarize_meeting_success(self, mock_openai):
        """Test successful meeting summarization."""
        # Create mock response
        mock_completion = Mock()
        mock_completion.choices = [Mock(message=Mock(content="Test summary"))]
        
        # Setup the mock chain
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Replace the client
        self.service.client = mock_client
        
        result = self.service.summarize_meeting(
            transcript="Test transcript",
            meeting_title="Test Meeting"
        )
        self.assertEqual(result, "Test summary")


if __name__ == '__main__':
    unittest.main()
