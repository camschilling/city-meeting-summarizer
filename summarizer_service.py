from openai import OpenAI
from typing import List, Dict, Optional


class SummarizerService:
    """Service for generating meeting summaries using OpenAI's ChatGPT."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Using GPT-4 mini for cost-effectiveness
    
    def generate_summary(
        self,
        meeting_title: str = "",
        meeting_date: str = "",
        transcript: str = "",
        additional_context: str = "",
        documents: List[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Generate a comprehensive meeting summary based on available sources.
        
        Args:
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            transcript: Full transcript (if available)
            additional_context: Additional context from documents
            documents: List of document dictionaries
            
        Returns:
            Summary text or None if failed
        """
        try:
            # Determine what sources are available
            has_transcript = bool(transcript and transcript.strip())
            has_documents = bool(documents and len(documents) > 0)
            has_additional_context = bool(additional_context and additional_context.strip())
            
            # Check document types if available
            has_minutes = False
            has_agenda = False
            if has_documents:
                has_minutes = any('minutes' in doc.get('title', '').lower() for doc in documents)
                has_agenda = any('agenda' in doc.get('title', '').lower() for doc in documents)
            
            # Build the appropriate prompt based on available sources
            prompt = self._build_unified_prompt(
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                transcript=transcript,
                additional_context=additional_context,
                has_transcript=has_transcript,
                has_documents=has_documents,
                has_minutes=has_minutes,
                has_agenda=has_agenda,
                document_count=len(documents) if documents else 0
            )
            
            # Determine appropriate system message based on sources
            system_content = (
                "You are an expert at summarizing city council meetings, including their transcripts, agendas, and minutes."
                "Your are familiar with Snoqualmie, WA and its governance structure."
            )
            
            if has_agenda:
                system_content = (
                                "You shall use the meeting agenda to outline what was planned for discussion during the meeting. "
                                "If no other information is provided, then summarize only the agenda within the cotext of Snoqualmie, WA."
                                )

            if has_transcript:
                system_content = (
                                "You shall use the video transcript to accurately and contextually summarize "
                                "decisions, discussions, and action items."
                                "The transcript likely includes spelling mistakes, especially regarding proper nouns and technical terms. "
                                "Be aware of those and identify where spelling may be wrong in your summaries."
                                )
            if has_minutes:
                system_content = (
                                "You shall use the meeting minutes to delineate discussion points from recorded decisions, "
                                "clearly indicating when information comes from minutes vs. other sources."
                                )

            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None
    
    def _build_unified_prompt(
        self,
        meeting_title: str,
        meeting_date: str,
        transcript: str,
        additional_context: str,
        has_transcript: bool,
        has_documents: bool,
        has_minutes: bool,
        has_agenda: bool,
        document_count: int
    ) -> str:
        """Build a unified prompt that adapts based on available sources."""
        prompt_parts = []
        
        # Adaptive opening based on available sources
        if has_transcript and has_documents:
            prompt_parts.append("Please provide a comprehensive summary of this city council meeting based on the video transcript and supporting documents.")
            source_note = "**Summary based on:** Video transcript and meeting documents"
        elif has_transcript:
            prompt_parts.append("Please provide a comprehensive summary of this city council meeting based on the video transcript.")
            source_note = "**Summary based on:** Video transcript only"
        elif has_minutes:
            prompt_parts.append("Please provide a summary of this city council meeting based on the available meeting minutes and documents.")
            source_note = "**Summary based on:** Meeting minutes and documents (no video available)"
        elif has_agenda:
            prompt_parts.append("Please provide a summary of what was planned for this city council meeting based on the available agenda and documents.")
            source_note = "**Summary based on:** Meeting agenda only (no video or minutes available)"
        else:
            prompt_parts.append("Please provide a summary based on the available meeting information.")
            source_note = "**Summary based on:** Limited meeting information"
        
        # Common summary structure
        prompt_parts.append("\nThe summary should include (when information is available):")
        prompt_parts.append("1. Key topics and agenda items discussed")
        prompt_parts.append("2. Important decisions made")
        prompt_parts.append("3. Action items and next steps")
        prompt_parts.append("4. Public comments (if any)")
        prompt_parts.append("5. Votes taken and their outcomes")
        
        # Add specific guidance based on source type
        if has_transcript:
            prompt_parts.append("\nFocus on what actually occurred during the meeting as captured in the transcript.")
        elif has_minutes:
            prompt_parts.append("\nFocus on official decisions and actions as recorded in the meeting minutes.")
        elif has_agenda:
            prompt_parts.append("\nFocus on what was planned for discussion. Use language like 'scheduled to discuss', 'planned for review', etc. Note that without minutes or video, actual outcomes are unknown.")
        
        # Meeting metadata
        if meeting_title:
            prompt_parts.append(f"\n\nMeeting: {meeting_title}")
        
        if meeting_date:
            prompt_parts.append(f"Date: {meeting_date}")
        
        # Add documents context if available
        if has_documents and additional_context and additional_context.strip():
            prompt_parts.append(f"\n\nMeeting Documents ({document_count} available):")
            prompt_parts.append(f"{additional_context}")
            
            if has_transcript:
                prompt_parts.append("\nUse these documents to:")
                prompt_parts.append("- Provide context for discussions in the transcript")
                prompt_parts.append("- Identify which agenda items were covered")
                prompt_parts.append("- Include relevant background information")
            elif has_minutes:
                prompt_parts.append("\nUse these documents to:")
                prompt_parts.append("- Understand the full context of recorded decisions")
                prompt_parts.append("- Provide background on agenda items")
                prompt_parts.append("- Include relevant supporting information")
            else:
                prompt_parts.append("\nUse these documents to:")
                prompt_parts.append("- Understand planned discussion topics")
                prompt_parts.append("- Provide context for agenda items")
                prompt_parts.append("- Include relevant background information")
        
        # Add transcript if available
        if has_transcript and transcript:
            prompt_parts.append(f"\n\nMeeting Transcript:\n{transcript}")
        
        # Final instructions based on source type
        if has_transcript:
            prompt_parts.append(
                f"\n\n{source_note}\n\n"
                "Please ensure the summary is well-structured, professional, and captures all significant discussions and decisions. "
                "If meeting documents include agenda items that weren't discussed in the transcript, note them as 'Not discussed' or 'Deferred'."
            )
        elif has_minutes:
            prompt_parts.append(
                f"\n\n{source_note}\n\n"
                "Please clearly indicate that this summary is based on meeting documents only (not video recording). "
                "Focus on official decisions and actions as recorded in the minutes and supporting documents."
            )
        else:
            prompt_parts.append(
                f"\n\n{source_note}\n\n"
                "Please clearly state that this summary represents what was PLANNED for discussion according to the agenda, "
                "not what actually occurred. Use language like 'was scheduled to discuss', 'was planned for review', etc. "
                "Note that without minutes or video, the actual outcomes are unknown."
            )
        
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
