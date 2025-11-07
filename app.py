import streamlit as st
import os
from dotenv import load_dotenv
from meeting_scraper import MeetingScraper
from transcript_service import TranscriptService
from summarizer_service import SummarizerService
from youtube_transcript_service import YouTubeTranscriptService

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="City Meeting Summarizer",
    page_icon="📋",
    layout="wide"
)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize all services with API keys."""
    openai_key = os.getenv('OPENAI_API_KEY')
    transcript_key = os.getenv('TRANSCRIPTAPI_KEY')
    transcript_url = os.getenv('TRANSCRIPTAPI_URL', 'https://api.transcriptapi.com/v1')
    
    scraper = MeetingScraper()
    transcript_service = TranscriptService(transcript_key, transcript_url) if transcript_key else None
    summarizer = SummarizerService(openai_key) if openai_key else None
    youtube_service = YouTubeTranscriptService()
    
    return scraper, transcript_service, summarizer, youtube_service

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_meetings():
    """Load meetings and cache them for better UX."""
    scraper = MeetingScraper()
    return scraper.get_meetings()

def chat_with_ai(summarizer, summary, meeting_title, transcript=None, additional_context=None):
    """Handle the chat interface with OpenAI with full context."""
    
    # Build comprehensive system context
    system_context = f"""You are an AI assistant with complete access to a city meeting's information. You have:

1. MEETING SUMMARY: {summary}

2. FULL TRANSCRIPT: {transcript if transcript else "Not available"}

3. DOCUMENT CONTEXT: {additional_context if additional_context else "No additional documents were available"}

You can answer detailed questions about:
- Specific quotes and statements from the transcript
- Context around decisions and discussions
- Background information from meeting documents
- Detailed analysis of topics discussed
- Action items and their context
- Public comments and concerns raised
- Voting records and rationale

Provide comprehensive, accurate responses based on this complete information."""
    
    # Initialize chat history in session state with unique key
    chat_key = f"chat_messages_{meeting_title}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "system", "content": system_context},
            {"role": "assistant", "content": f"# 📋 {meeting_title} Summary\n\n{summary}\n\n---\n\n💬 **I've analyzed this meeting in detail and have access to the complete transcript and all supporting documents. Feel free to ask me any follow-up questions about specific discussions, decisions, quotes, or background context!**"}
        ]
    
    # Display chat messages (skip system message)
    chat_messages = st.session_state[chat_key]
    for message in chat_messages[1:]:  # Skip system message
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about this meeting...", key=f"chat_input_{meeting_title}"):
        # Add user message
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = summarizer.client.chat.completions.create(
                        model=summarizer.model,
                        messages=st.session_state[chat_key],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    ai_response = response.choices[0].message.content
                    st.write(ai_response)
                    
                    # Add AI response to chat history
                    st.session_state[chat_key].append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state[chat_key].append({"role": "assistant", "content": error_msg})
    
        # Add a clear chat button
        if len(chat_messages) > 2:  # More than just system and initial assistant messages
            if st.button("🗑️ Clear Chat History", key=f"clear_chat_{meeting_title}"):
                # Build comprehensive system context
                system_context = f"""You are an AI assistant with complete access to a city meeting's information. You have:

1. MEETING SUMMARY: {summary}

2. FULL TRANSCRIPT: {transcript if 'transcript' in locals() else st.session_state.get('current_transcript', 'Not available')}

3. DOCUMENT CONTEXT: {additional_context if 'additional_context' in locals() else "No additional documents were available"}

You can answer detailed questions about:
- Specific quotes and statements from the transcript
- Context around decisions and discussions
- Background information from meeting documents
- Detailed analysis of topics discussed
- Action items and their context
- Public comments and concerns raised
- Voting records and rationale

Provide comprehensive, accurate responses based on this complete information."""

                # Reset to initial state with full context
                st.session_state[chat_key] = [
                    {"role": "system", "content": system_context},
                    {"role": "assistant", "content": f"# 📋 {meeting_title} Summary\n\n{summary}\n\n---\n\n💬 **I've analyzed this meeting in detail and have access to the complete transcript and all supporting documents. Feel free to ask me any follow-up questions about specific discussions, decisions, quotes, or background context!**"}
                ]
                st.rerun()

def main():
    st.title("Snoqualmie City Meeting Summarizer")
    st.markdown("""
                Select a meeting below to have AI generate city meeting summary and start a chat!
                *This application uses available YouTube video recordings, 
                meeting minutes, agendas, and packets to produce comprehensive meeting summaries.
                You are then able to ask follow up questions and save the chat.*
                """
    )
    st.markdown("---")
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    transcript_key = os.getenv('TRANSCRIPTAPI_KEY')
    
    if not openai_key:
        st.error("⚠️ OpenAI API key not configured!")
        st.info("""
        Please configure your OpenAI API key:
        1. Copy `.env.example` to `.env`
        2. Add your OpenAI API key
        3. Restart the application
        """)
        return
    
    # Initialize services
    scraper, transcript_service, summarizer, youtube_service = init_services()
    
    # Load meetings automatically on app start
    if 'meetings_loaded' not in st.session_state:
        with st.spinner("Loading available meetings..."):
            meetings = load_meetings()
            st.session_state['meetings'] = meetings
            st.session_state['meetings_loaded'] = True
    
    meetings = st.session_state.get('meetings', [])
    
    if not meetings:
        st.error("❌ No meetings found. Please check the website connection.")
        if st.button("🔄 Retry Loading Meetings"):
            st.cache_data.clear()
            st.session_state['meetings_loaded'] = False
            st.rerun()
        return
    
    # Main content - Single unified panel
    if 'current_summary' in st.session_state and 'processing_meeting' in st.session_state:
        # Show completed summary and chat interface
        meeting = st.session_state['processing_meeting']
        summary = st.session_state['current_summary']
        
        st.header("✅ Summary Complete")
        st.subheader(f"{meeting.get('title', 'Unknown Meeting')}")
        
        # Start new summary button at the top
        if st.button("🔄 Summarize Different Meeting", type="secondary"):
            # Clear processing state to allow new selection
            for key in ['processing_meeting', 'current_summary', 'current_transcript']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # AI Chat Interface with Summary as First Message
        st.header("Meeting Analysis & Discussion")
        
        # Get the full context for richer chat experience
        current_transcript = st.session_state.get('current_transcript', '')
        
        # Get the document context that was used for this meeting
        meeting_documents = meeting.get('documents', [])
        document_context = ""
        if meeting_documents:
            # Try to get the same document context that was used in summarization
            document_context = scraper.get_document_context(meeting_documents, max_docs=3)
        
        chat_with_ai(summarizer, summary, meeting.get('title', 'Meeting'), 
                    transcript=current_transcript, additional_context=document_context)
        
        # Show documents that were included (compact view)
        documents = meeting.get('documents', [])
        valid_docs = [doc for doc in documents if doc.get('title') and doc.get('url')]
        if valid_docs:
            st.markdown("---")
            with st.expander(f"📄 Documents Referenced ({len(valid_docs)} available)"):
                for doc in valid_docs[:3]:  # Show first 3 docs that were included
                    st.write(f"• [{doc['title']}]({doc['url']})")
                if len(valid_docs) > 3:
                    st.write(f"• ... and {len(valid_docs) - 3} more documents")
        
        # Download button
        st.markdown("---")
        st.download_button(
            label="📥 Download Summary",
            data=summary,
            file_name=f"meeting_summary_{meeting.get('date', 'unknown').replace('/', '_')}.txt",
            mime="text/plain",
            help="Download the meeting summary as a text file"
        )
        
        # Add button to start new summary
        if st.button("� Summarize Different Meeting", type="secondary"):
            # Clear processing state to allow new selection
            for key in ['processing_meeting', 'current_summary', 'current_transcript']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
            
    elif 'processing_meeting' in st.session_state:
        # Show processing for the selected meeting
        selected_meeting = st.session_state['processing_meeting']
        
        st.header("🔄 Processing Meeting")
        st.subheader(f"📋 {selected_meeting.get('title', 'Unknown Meeting')}")
        
        # Allow cancellation
        if st.button("❌ Cancel and Select Different Meeting"):
            for key in ['processing_meeting', 'current_summary', 'current_transcript']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # Process the meeting with simple status updates
        with st.status("Processing meeting...", expanded=True) as status:
            st.write("🔍 Fetching meeting details...")
            
            details = scraper.get_meeting_details(selected_meeting['url'])
            
            if not details:
                st.error("❌ Failed to get meeting details")
                if 'processing_meeting' in st.session_state:
                    del st.session_state['processing_meeting']
                st.stop()
            
            # Update processing meeting with full details
            st.session_state['processing_meeting'] = details
            
            video_url = details.get('video_url', '')
            if not video_url:
                st.error("❌ No video URL found for this meeting")
                if 'processing_meeting' in st.session_state:
                    del st.session_state['processing_meeting']
                st.stop()
            
            st.write("📝 Getting transcript...")
            
            transcript = None
            
            # Try YouTube transcript service first
            platform = scraper.get_video_platform(video_url)
            if platform == "YouTube":
                youtube_transcript = youtube_service.get_transcript(video_url)
                
                if youtube_transcript and "MANUAL TRANSCRIPTION REQUIRED" not in youtube_transcript:
                    transcript = youtube_transcript
                    st.write("✅ YouTube transcript retrieved automatically!")
                else:
                    st.write("⚠️ Automatic YouTube transcription failed")
            
            # Fallback to TranscriptAPI for non-YouTube or if YouTube failed
            if not transcript and transcript_service and platform != "YouTube":
                transcript = transcript_service.transcribe_and_wait(video_url)
                if transcript:
                    st.write("✅ Transcript retrieved via TranscriptAPI!")
            
            # Manual transcription fallback
            if not transcript:
                st.error("❌ Automatic transcription failed")
                status.update(label="Manual transcription required", state="error")
                
                st.markdown("### 📝 Manual Transcription Required")
                
                if platform == "YouTube":
                    st.info(f"""
                    **YouTube URL:** `{video_url}`
                    
                    Please get the transcript manually:
                    1. Visit [youtubetotranscript.com](https://youtubetotranscript.com/)
                    2. Paste the URL above
                    3. Copy the transcript and paste it below
                    """)
                
                manual_transcript = st.text_area(
                    "Paste transcript here:",
                    height=200,
                    placeholder="Paste the meeting transcript here...",
                    key="manual_transcript_processing"
                )
                
                if manual_transcript and st.button("✅ Use Manual Transcript", key="use_manual_processing"):
                    transcript = manual_transcript
                    st.rerun()
                
                st.stop()
            
            # Store transcript
            st.session_state['current_transcript'] = transcript
            
            st.write("🤖 Generating AI summary...")
            
            # Include document context
            additional_context = ""
            documents = details.get('documents', [])
            if documents:
                additional_context = scraper.get_document_context(documents, max_docs=3)
                if additional_context:
                    st.write(f"📄 Including {min(len(documents), 3)} document(s) for context")
                else:
                    st.write("📄 Documents found but couldn't be processed for context")
            else:
                st.write("📄 No documents found - generating summary from transcript only")
            
            # Generate summary
            summary = summarizer.summarize_meeting(
                transcript=transcript,
                meeting_title=details.get('title', ''),
                meeting_date=details.get('date', ''),
                additional_context=additional_context
            )
            
            if not summary:
                st.error("❌ Failed to generate summary")
                if 'processing_meeting' in st.session_state:
                    del st.session_state['processing_meeting']
                st.stop()
            
            # Store the completed summary
            st.session_state['current_summary'] = summary
            
            status.update(label="Summary completed!", state="complete")
            st.write("✅ Summary generated successfully!")
        
        # Automatically transition to summary view
        st.rerun()
        
    else:
        # Show meeting selection interface
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.header("Available Meetings")
        
        with col2:
            if st.button("🔄 Reload Meetings"):
                st.cache_data.clear()
                st.session_state['meetings_loaded'] = False
                st.rerun()
        
        # Sort meetings by date (newest first)
        meetings_sorted = sorted(meetings, key=lambda x: x.get('date', ''), reverse=True)
        
        # Meeting selection interface
        for idx, meeting in enumerate(meetings_sorted):
            meeting_title = meeting.get('title', 'Unknown Meeting')
            meeting_date = meeting.get('date', 'Unknown Date')
            
            # Create a clean display title
            display_title = f"{meeting_title}"
            if meeting_date and meeting_date != 'Unknown Date':
                display_title = f"{meeting_title} - {meeting_date}"
            
            # Create an expandable section for each meeting
            with st.expander(f"📅 {display_title}"):
                st.write(f"**Meeting:** {meeting_title}")
                if meeting_date and meeting_date != 'Unknown Date':
                    st.write(f"**Date:** {meeting_date}")
                
                # Show document count
                documents = meeting.get('documents', [])
                # Only count documents that have both title and URL
                valid_docs = [doc for doc in documents if doc.get('title') and doc.get('url')]
                doc_count = len(valid_docs)
                
                if doc_count > 0:
                    st.write(f"**Documents:** {doc_count} available")
                    # Show document types
                    doc_types = []
                    for doc in valid_docs[:3]:  # Show first 3
                        doc_title = doc.get('title', 'Document')
                        doc_types.append(doc_title)
                    if doc_types:
                        st.write(f"  📄 {', '.join(doc_types)}")
                        if len(valid_docs) > 3:
                            st.write(f"  📄 ... and {len(valid_docs) - 3} more")
                else:
                    # Don't show document count if none are available
                    pass
                
                # Selection button
                if st.button(f"📝 Generate Meeting Summary", key=f"select_{idx}", type="primary"):
                    # Store selected meeting and rerun to start processing
                    st.session_state['processing_meeting'] = meeting
                    st.rerun()
        
        # Show meeting count and status at the bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"📊 **{len(meetings)} meetings** loaded")
        
        with col2:
            st.success("✅ **OpenAI** configured")
        
        with col3:
            if transcript_key:
                st.success("✅ **TranscriptAPI** configured")
            else:
                st.warning("⚠️ **TranscriptAPI** not configured")


if __name__ == "__main__":
    main()
