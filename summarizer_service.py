from openai import OpenAI
from typing import List, Dict, Optional


class SummarizerService:
    """Service for generating meeting summaries using OpenAI's ChatGPT."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Using GPT-4 mini for cost-effectiveness
    
    def summarize_meeting(
        self,
        transcript: str,
        meeting_title: str = "",
        meeting_date: str = "",
        additional_context: str = ""
    ) -> Optional[str]:
        """
        Generate a summary of a meeting based on transcript and context.
        
        Args:
            transcript: Full transcript of the meeting
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            additional_context: Additional context from documents or other sources
            
        Returns:
            Summary text or None if failed
        """
        try:
            # Construct the prompt
            prompt = self._build_summary_prompt(
                transcript, meeting_title, meeting_date, additional_context
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at summarizing city council meetings. "
                                   "Your summaries are clear, concise, and capture all important "
                                   "decisions, discussions, and action items."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more focused summaries
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None
    
    def _build_summary_prompt(
        self,
        transcript: str,
        meeting_title: str,
        meeting_date: str,
        additional_context: str
    ) -> str:
        """Build the prompt for the summarization request."""
        prompt_parts = []
        
        prompt_parts.append("Please provide a comprehensive summary of this city council meeting.")
        prompt_parts.append("\nThe summary should include:")
        prompt_parts.append("1. Key topics and agenda items discussed")
        prompt_parts.append("2. Important decisions made")
        prompt_parts.append("3. Action items and next steps")
        prompt_parts.append("4. Public comments (if any)")
        prompt_parts.append("5. Votes taken and their outcomes")
        
        if meeting_title:
            prompt_parts.append(f"\n\nMeeting: {meeting_title}")
        
        if meeting_date:
            prompt_parts.append(f"Date: {meeting_date}")
        
        if additional_context and additional_context.strip():
            prompt_parts.append(f"\n\nMeeting Documents:")
            prompt_parts.append("Please access and review the following meeting documents to provide additional context:")
            prompt_parts.append(f"\n{additional_context}")
            prompt_parts.append("\nUse these documents to:")
            prompt_parts.append("- Understand the meeting agenda and planned discussion items")
            prompt_parts.append("- Identify which agenda items were discussed vs. deferred")
            prompt_parts.append("- Provide context for decisions and votes")
            prompt_parts.append("- Include relevant background information from meeting packets")
        
        prompt_parts.append(f"\n\nMeeting Transcript:\n{transcript}")
        
        prompt_parts.append("\n\nPlease ensure the summary is well-structured, professional, and captures all significant discussions and decisions. If the meeting documents include agenda items that weren't discussed in the transcript, please note them as 'Not discussed in this meeting' or 'Deferred to future meeting'.")
        
        return "\n".join(prompt_parts)
    
    def extract_action_items(self, transcript: str) -> Optional[List[str]]:
        """
        Extract action items from a meeting transcript.
        
        Args:
            transcript: Full transcript of the meeting
            
        Returns:
            List of action items or None if failed
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at identifying action items from meeting transcripts. "
                                   "Extract clear, actionable items with responsible parties if mentioned."
                    },
                    {
                        "role": "user",
                        "content": f"Please extract all action items from this meeting transcript:\n\n{transcript}"
                    }
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Parse response into list
            action_items_text = response.choices[0].message.content
            action_items = [item.strip() for item in action_items_text.split('\n') if item.strip()]
            
            return action_items
        except Exception as e:
            print(f"Error extracting action items: {e}")
            return None
