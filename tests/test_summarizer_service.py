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
    
    def test_generate_summary_basic(self, summarizer_service, mock_openai_response):
        """Test basic meeting summarization."""
        summarizer_service.client.chat.completions.create.return_value = mock_openai_response
        
        result = summarizer_service.generate_summary(
            transcript="Test transcript content",
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15"
        )
        
        assert result == "This is a test summary of the meeting."
        summarizer_service.client.chat.completions.create.assert_called_once()
    
    def test_generate_summary_with_document_context(self, summarizer_service, mock_openai_response):
        """Test meeting summarization with document URLs."""
        summarizer_service.client.chat.completions.create.return_value = mock_openai_response
        
        document_context = """Meeting Documents Available:
- Agenda (HTML): https://example.com/agenda.html
- Packet (PDF): https://example.com/packet.pdf
- Minutes (HTML): https://example.com/minutes.html"""
        
        documents = [
            {'title': 'Agenda (HTML)', 'url': 'https://example.com/agenda.html'},
            {'title': 'Packet (PDF)', 'url': 'https://example.com/packet.pdf'},
            {'title': 'Minutes (HTML)', 'url': 'https://example.com/minutes.html'}
        ]
        
        result = summarizer_service.generate_summary(
            transcript="Test transcript content",
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15",
            additional_context=document_context,
            documents=documents
        )
        
        assert result == "This is a test summary of the meeting."
        
        # Verify the call was made with the right parameters
        call_args = summarizer_service.client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-4o-mini"
        assert call_args[1]['temperature'] == 0.3
        assert call_args[1]['max_tokens'] == 2000
        
        # Check that the prompt includes document context
        prompt = call_args[1]['messages'][1]['content']
        assert "Meeting Documents" in prompt
        assert "https://example.com/agenda.html" in prompt
        assert "https://example.com/packet.pdf" in prompt
        assert "https://example.com/minutes.html" in prompt
    
    def test_build_unified_prompt_with_transcript(self, summarizer_service):
        """Test unified prompt building with transcript available."""
        documents = [
            {'title': 'Agenda (HTML)', 'url': 'https://example.com/agenda.html'},
            {'title': 'Minutes (HTML)', 'url': 'https://example.com/minutes.html'}
        ]
        
        prompt = summarizer_service._build_unified_prompt(
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15",
            transcript="Test transcript content",
            additional_context="Meeting Documents Available:\n- Agenda\n- Minutes",
            has_transcript=True,
            has_documents=True,
            has_minutes=True,
            has_agenda=True,
            document_count=2
        )
        
        assert "comprehensive summary of this city council meeting based on the video transcript and supporting documents" in prompt
        assert "Meeting: City Council Meeting" in prompt
        assert "Date: 2024-01-15" in prompt
        assert "Test transcript content" in prompt
        assert "Meeting Documents (2 available)" in prompt
        assert "Video transcript and meeting documents" in prompt
    
    def test_build_unified_prompt_agenda_only(self, summarizer_service):
        """Test unified prompt building with agenda only."""
        documents = [
            {'title': 'Agenda (HTML)', 'url': 'https://example.com/agenda.html'}
        ]
        
        prompt = summarizer_service._build_unified_prompt(
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15",
            transcript="",
            additional_context="Meeting Documents Available:\n- Agenda",
            has_transcript=False,
            has_documents=True,
            has_minutes=False,
            has_agenda=True,
            document_count=1
        )
        
        assert "summary of what was planned for this city council meeting based on the available agenda" in prompt
        assert "scheduled to discuss" in prompt
        assert "planned for review" in prompt
        assert "Meeting agenda only (no video or minutes available)" in prompt
        assert "actual outcomes are unknown" in prompt
    
    def test_build_unified_prompt_minutes_only(self, summarizer_service):
        """Test unified prompt building with minutes but no video."""
        documents = [
            {'title': 'Minutes (HTML)', 'url': 'https://example.com/minutes.html'}
        ]
        
        prompt = summarizer_service._build_unified_prompt(
            meeting_title="City Council Meeting",
            meeting_date="2024-01-15",
            transcript="",
            additional_context="Meeting Documents Available:\n- Minutes",
            has_transcript=False,
            has_documents=True,
            has_minutes=True,
            has_agenda=False,
            document_count=1
        )
        
        assert "summary of this city council meeting based on the available meeting minutes and documents" in prompt
        assert "Meeting minutes and documents (no video available)" in prompt
        assert "based on meeting documents only (not video recording)" in prompt
    
    def test_generate_summary_api_error(self, summarizer_service):
        """Test handling of OpenAI API errors."""
        summarizer_service.client.chat.completions.create.side_effect = Exception("API Error")
        
        result = summarizer_service.generate_summary(
            transcript="Test transcript content",
            meeting_title="City Council Meeting"
        )
    
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
        
        # Test summarization system message with transcript
        summarizer_service.generate_summary(transcript="Test transcript")
        call_args = summarizer_service.client.chat.completions.create.call_args
        system_message = call_args[1]['messages'][0]['content']
        
        assert "video transcript to accurately and contextually summarize" in system_message
        assert "decisions, discussions, and action items" in system_message
        assert "spelling mistakes" in system_message
    
    def test_create_chat_context(self, summarizer_service):
        """Test chat context creation with full information."""
        summary = "Test meeting summary"
        transcript = "Test transcript content"
        additional_context = "Test document context"
        documents = [
            {'title': 'Agenda', 'url': 'https://example.com/agenda.html'},
            {'title': 'Minutes', 'url': 'https://example.com/minutes.html'}
        ]
        sources_used = "Video transcript, Meeting documents"
        
        context = summarizer_service.create_chat_context(
            summary=summary,
            meeting_title="Test Meeting",
            meeting_date="2024-01-15",
            transcript=transcript,
            additional_context=additional_context,
            documents=documents,
            sources_used=sources_used
        )
        
        assert "MEETING SUMMARY:" in context
        assert summary in context
        assert "FULL MEETING TRANSCRIPT:" in context
        assert transcript in context
        assert "MEETING DOCUMENTS AND CONTEXT:" in context
        assert additional_context in context
        assert "DOCUMENT REFERENCES:" in context
        assert "https://example.com/agenda.html" in context
        assert "SOURCES USED FOR THIS SUMMARY:" in context
        assert sources_used in context
        assert "MEETING TITLE: Test Meeting" in context
        assert "MEETING DATE: 2024-01-15" in context
    
    def test_create_chat_context_minimal(self, summarizer_service):
        """Test chat context creation with minimal information."""
        summary = "Test summary"
        
        context = summarizer_service.create_chat_context(
            summary=summary,
            meeting_title="",
            meeting_date="",
            transcript="",
            additional_context="",
            documents=None,
            sources_used=""
        )
        
        assert "MEETING SUMMARY:" in context
        assert summary in context
        assert "MEETING TRANSCRIPT: Not available" in context
        assert "MEETING DOCUMENTS: No additional documents were available" in context
    
    def test_chat_response_success(self, summarizer_service, mock_openai_response):
        """Test successful chat response generation."""
        summarizer_service.client.chat.completions.create.return_value = mock_openai_response
        mock_openai_response.choices[0].message.content = "Test chat response"
        
        chat_history = [
            {"role": "system", "content": "System context"},
            {"role": "assistant", "content": "Initial message"}
        ]
        
        response = summarizer_service.chat_response(
            user_message="Test question",
            chat_history=chat_history
        )
        
        assert response == "Test chat response"
        
        # Verify the API was called with correct parameters
        summarizer_service.client.chat.completions.create.assert_called_once()
        call_args = summarizer_service.client.chat.completions.create.call_args
        assert call_args[1]['model'] == summarizer_service.model
        assert call_args[1]['temperature'] == 0.3
        assert call_args[1]['max_tokens'] == 1000
        
        # Check that user message was added to conversation
        messages = call_args[1]['messages']
        assert len(messages) == 3
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Test question"
    
    def test_chat_response_api_error(self, summarizer_service):
        """Test chat response with API error."""
        summarizer_service.client.chat.completions.create.side_effect = Exception("API Error")
        
        chat_history = [{"role": "system", "content": "System context"}]
        
        response = summarizer_service.chat_response(
            user_message="Test question",
            chat_history=chat_history
        )
        
        assert response is None


if __name__ == "__main__":
    pytest.main([__file__])