import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from summarizer_service import SummarizerService


class TestSummarizerService:
    """Test cases for SummarizerService."""
    
    @pytest.fixture
    def summarizer_service(self):
        """Create a SummarizerService instance for testing."""
        with patch('summarizer_service.OpenAI'):
            return SummarizerService("test_api_key")
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI response structure."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "This is a test summary of the meeting."
        mock_response.choices = [mock_choice]
        return mock_response
    
    def test_initialization(self):
        """Test that SummarizerService initializes correctly."""
        with patch('summarizer_service.OpenAI') as mock_openai:
            service = SummarizerService("test_api_key")
            mock_openai.assert_called_once_with(api_key="test_api_key")
            assert service.model == "gpt-4o-mini"
    
    def test_summarize_meeting_basic(self, summarizer_service, mock_openai_response):
        """Test basic meeting summarization."""
        summarizer_service.client.chat.completions.create.return_value = mock_openai_response
        
        result = summarizer_service.summarize_meeting(
            transcript="Test transcript content",
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15"
        )
        
        assert result == "This is a test summary of the meeting."
        summarizer_service.client.chat.completions.create.assert_called_once()
    
    def test_summarize_meeting_with_document_context(self, summarizer_service, mock_openai_response):
        """Test meeting summarization with document URLs."""
        summarizer_service.client.chat.completions.create.return_value = mock_openai_response
        
        document_context = """Meeting Documents Available:
- Agenda (HTML): https://example.com/agenda.html
- Packet (PDF): https://example.com/packet.pdf
- Minutes (HTML): https://example.com/minutes.html"""
        
        result = summarizer_service.summarize_meeting(
            transcript="Test transcript content",
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15",
            additional_context=document_context
        )
        
        assert result == "This is a test summary of the meeting."
        
        # Verify the call was made with the right parameters
        call_args = summarizer_service.client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4o-mini"
        assert call_args[1]['temperature'] == 0.3
        assert call_args[1]['max_tokens'] == 2000
        
        # Check that the prompt includes document context
        prompt = call_args[1]['messages'][1]['content']
        assert "Meeting Documents:" in prompt
        assert "Please access and review the following meeting documents" in prompt
        assert "https://example.com/agenda.html" in prompt
        assert "https://example.com/packet.pdf" in prompt
        assert "https://example.com/minutes.html" in prompt
    
    def test_build_summary_prompt_minimal(self, summarizer_service):
        """Test prompt building with minimal information."""
        prompt = summarizer_service._build_summary_prompt(
            transcript="Test transcript",
            meeting_title="",
            meeting_date="",
            additional_context=""
        )
        
        assert "Please provide a comprehensive summary" in prompt
        assert "Key topics and agenda items discussed" in prompt
        assert "Important decisions made" in prompt
        assert "Action items and next steps" in prompt
        assert "Public comments (if any)" in prompt
        assert "Votes taken and their outcomes" in prompt
        assert "Test transcript" in prompt
    
    def test_build_summary_prompt_complete(self, summarizer_service):
        """Test prompt building with all information."""
        document_context = """Meeting Documents Available:
- Agenda (HTML): https://example.com/agenda.html
- Packet (PDF): https://example.com/packet.pdf"""
        
        prompt = summarizer_service._build_summary_prompt(
            transcript="Test transcript content",
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15",
            additional_context=document_context
        )
        
        assert "Meeting: City Council Meeting" in prompt
        assert "Date: 2024-01-15" in prompt
        assert "Meeting Documents:" in prompt
        assert "Please access and review the following meeting documents" in prompt
        assert "https://example.com/agenda.html" in prompt
        assert "https://example.com/packet.pdf" in prompt
        assert "Understand the meeting agenda and planned discussion items" in prompt
        assert "Identify which agenda items were discussed vs. deferred" in prompt
        assert "Provide context for decisions and votes" in prompt
        assert "Include relevant background information from meeting packets" in prompt
        assert "Test transcript content" in prompt
        assert "If the meeting documents include agenda items that weren't discussed" in prompt
    
    def test_build_summary_prompt_empty_context(self, summarizer_service):
        """Test prompt building with empty additional context."""
        prompt = summarizer_service._build_summary_prompt(
            transcript="Test transcript",
            meeting_title="Test Meeting",
            meeting_date="2024-01-15",
            additional_context="   "  # Whitespace only
        )
        
        assert "Meeting Documents:" not in prompt
        assert "Please access and review" not in prompt
        assert "Meeting: Test Meeting" in prompt
        assert "Date: 2024-01-15" in prompt
    
    def test_summarize_meeting_api_error(self, summarizer_service):
        """Test handling of API errors during summarization."""
        summarizer_service.client.chat.completions.create.side_effect = Exception("API Error")
        
        result = summarizer_service.summarize_meeting(
            transcript="Test transcript",
            meeting_title="Test Meeting"
        )
        
        assert result is None
    
    def test_extract_action_items_success(self, summarizer_service):
        """Test successful action item extraction."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "1. Review budget proposal\n2. Schedule public hearing\n3. Update website content"
        mock_response.choices = [mock_choice]
        
        summarizer_service.client.chat.completions.create.return_value = mock_response
        
        result = summarizer_service.extract_action_items("Test transcript with action items")
        
        expected_items = [
            "1. Review budget proposal",
            "2. Schedule public hearing", 
            "3. Update website content"
        ]
        assert result == expected_items
        
        # Verify the API call
        call_args = summarizer_service.client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4o-mini"
        assert call_args[1]['temperature'] == 0.2
        assert call_args[1]['max_tokens'] == 1000
        
        # Check system message for action items
        system_message = call_args[1]['messages'][0]['content']
        assert "expert at identifying action items" in system_message
        assert "Extract clear, actionable items" in system_message
    
    def test_extract_action_items_api_error(self, summarizer_service):
        """Test handling of API errors during action item extraction."""
        summarizer_service.client.chat.completions.create.side_effect = Exception("API Error")
        
        result = summarizer_service.extract_action_items("Test transcript")
        
        assert result is None
    
    def test_extract_action_items_empty_response(self, summarizer_service):
        """Test handling of empty action items response."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "\n\n\n"  # Only whitespace
        mock_response.choices = [mock_choice]
        
        summarizer_service.client.chat.completions.create.return_value = mock_response
        
        result = summarizer_service.extract_action_items("Test transcript")
        
        assert result == []
    
    def test_system_messages_content(self, summarizer_service, mock_openai_response):
        """Test that system messages contain appropriate instructions."""
        summarizer_service.client.chat.completions.create.return_value = mock_openai_response
        
        # Test summarization system message
        summarizer_service.summarize_meeting("Test transcript")
        call_args = summarizer_service.client.chat.completions.create.call_args
        system_message = call_args[1]['messages'][0]['content']
        
        assert "expert at summarizing city council meetings" in system_message
        assert "clear, concise, and capture all important" in system_message
        assert "decisions, discussions, and action items" in system_message
    
    def test_document_context_instructions(self, summarizer_service):
        """Test that document context includes proper instructions for OpenAI."""
        document_context = """Meeting Documents Available:
- Agenda (HTML): https://example.com/agenda.html
- Packet (PDF): https://example.com/packet.pdf"""
        
        prompt = summarizer_service._build_summary_prompt(
            transcript="Test transcript",
            meeting_title="Test Meeting",
            meeting_date="2024-01-15",
            additional_context=document_context
        )
        
        # Verify all the document usage instructions are present
        expected_instructions = [
            "Please access and review the following meeting documents",
            "Use these documents to:",
            "Understand the meeting agenda and planned discussion items",
            "Identify which agenda items were discussed vs. deferred",
            "Provide context for decisions and votes", 
            "Include relevant background information from meeting packets"
        ]
        
        for instruction in expected_instructions:
            assert instruction in prompt
    
    def test_prompt_structure_order(self, summarizer_service):
        """Test that the prompt components are in the correct order."""
        document_context = "Meeting Documents Available:\n- Agenda: https://example.com/agenda.html"
        
        prompt = summarizer_service._build_summary_prompt(
            transcript="Test transcript content",
            meeting_title="Test Meeting",
            meeting_date="2024-01-15",
            additional_context=document_context
        )
        
        # Check order of major sections
        summary_intro_pos = prompt.find("Please provide a comprehensive summary")
        meeting_info_pos = prompt.find("Meeting: Test Meeting")
        document_section_pos = prompt.find("Meeting Documents:")
        transcript_pos = prompt.find("Meeting Transcript:\nTest transcript content")
        final_instructions_pos = prompt.find("Please ensure the summary is well-structured")
        
        # Verify order is correct
        assert summary_intro_pos < meeting_info_pos
        assert meeting_info_pos < document_section_pos
        assert document_section_pos < transcript_pos
        assert transcript_pos < final_instructions_pos


if __name__ == "__main__":
    pytest.main([__file__])