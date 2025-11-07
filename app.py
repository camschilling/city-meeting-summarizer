import streamlit as st
import os
from dotenv import load_dotenv
from meeting_scraper import MeetingScraper
from transcript_service import TranscriptService
from summarizer_service import SummarizerService

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
    
    scraper = MeetingScraper()
    transcript_service = TranscriptService(transcript_key) if transcript_key else None
    summarizer = SummarizerService(openai_key) if openai_key else None
    
    return scraper, transcript_service, summarizer


def main():
    st.title("🏛️ City Meeting Summarizer")
    st.markdown("---")
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    transcript_key = os.getenv('TRANSCRIPTAPI_KEY')
    
    if not openai_key or not transcript_key:
        st.error("⚠️ API keys not configured!")
        st.info("""
        Please configure your API keys:
        1. Copy `.env.example` to `.env`
        2. Add your OpenAI API key
        3. Add your TranscriptAPI key
        4. Restart the application
        """)
        return
    
    # Initialize services
    scraper, transcript_service, summarizer = init_services()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown("### API Status")
        st.success("✅ OpenAI API configured")
        st.success("✅ TranscriptAPI configured")
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This application:
        1. Fetches meetings from Snoqualmie's website
        2. Transcribes video recordings
        3. Generates AI-powered summaries
        """)
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📋 Select Meeting", "🎬 Transcribe", "📝 Summary"])
    
    with tab1:
        st.header("Select a Meeting")
        
        if st.button("🔄 Fetch Available Meetings", type="primary"):
            with st.spinner("Fetching meetings..."):
                meetings = scraper.get_meetings()
                st.session_state['meetings'] = meetings
        
        if 'meetings' in st.session_state and st.session_state['meetings']:
            st.success(f"Found {len(st.session_state['meetings'])} meetings")
            
            # Display meetings
            for idx, meeting in enumerate(st.session_state['meetings']):
                with st.expander(f"📅 {meeting.get('title', 'Unknown Meeting')}"):
                    st.write(f"**URL:** {meeting.get('url', 'N/A')}")
                    
                    if st.button(f"Select Meeting", key=f"select_{idx}"):
                        with st.spinner("Fetching meeting details..."):
                            details = scraper.get_meeting_details(meeting['url'])
                            st.session_state['selected_meeting'] = details
                            st.success("Meeting selected!")
                            st.rerun()
        else:
            st.info("Click 'Fetch Available Meetings' to get started")
    
    with tab2:
        st.header("Transcribe Meeting Video")
        
        if 'selected_meeting' not in st.session_state:
            st.warning("Please select a meeting first")
        else:
            meeting = st.session_state['selected_meeting']
            st.subheader(meeting.get('title', 'Meeting'))
            
            if meeting.get('date'):
                st.write(f"**Date:** {meeting['date']}")
            
            video_url = meeting.get('video_url', '')
            
            if video_url:
                st.write(f"**Video URL:** {video_url}")
                
                if st.button("🎬 Start Transcription", type="primary"):
                    with st.spinner("Submitting video for transcription... This may take a while."):
                        transcript = transcript_service.transcribe_and_wait(video_url)
                        
                        if transcript:
                            st.session_state['transcript'] = transcript
                            st.success("✅ Transcription complete!")
                            st.text_area("Transcript Preview", transcript, height=300)
                        else:
                            st.error("❌ Transcription failed. Please check the video URL and try again.")
            else:
                st.warning("No video URL found for this meeting")
                st.info("You can manually enter a video URL below:")
                manual_url = st.text_input("Video URL")
                
                if manual_url and st.button("Use Manual URL"):
                    st.session_state['selected_meeting']['video_url'] = manual_url
                    st.rerun()
            
            # Show documents if available
            if meeting.get('documents'):
                st.markdown("---")
                st.subheader("📄 Available Documents")
                for doc in meeting['documents']:
                    st.write(f"- [{doc['title']}]({doc['url']})")
    
    with tab3:
        st.header("Meeting Summary")
        
        if 'transcript' not in st.session_state:
            st.warning("Please transcribe the meeting video first")
        else:
            meeting = st.session_state.get('selected_meeting', {})
            transcript = st.session_state['transcript']
            
            st.subheader(meeting.get('title', 'Meeting Summary'))
            
            if st.button("✨ Generate Summary", type="primary"):
                with st.spinner("Generating AI summary..."):
                    summary = summarizer.summarize_meeting(
                        transcript=transcript,
                        meeting_title=meeting.get('title', ''),
                        meeting_date=meeting.get('date', ''),
                        additional_context=""
                    )
                    
                    if summary:
                        st.session_state['summary'] = summary
                        st.success("✅ Summary generated!")
                    else:
                        st.error("❌ Failed to generate summary")
            
            # Display summary if available
            if 'summary' in st.session_state:
                st.markdown("### 📋 Meeting Summary")
                st.markdown(st.session_state['summary'])
                
                # Download button
                st.download_button(
                    label="📥 Download Summary",
                    data=st.session_state['summary'],
                    file_name=f"meeting_summary_{meeting.get('date', 'unknown')}.txt",
                    mime="text/plain"
                )
                
                # Action items extraction
                st.markdown("---")
                if st.button("🎯 Extract Action Items"):
                    with st.spinner("Extracting action items..."):
                        action_items = summarizer.extract_action_items(transcript)
                        if action_items:
                            st.session_state['action_items'] = action_items
                
                if 'action_items' in st.session_state:
                    st.markdown("### 🎯 Action Items")
                    for item in st.session_state['action_items']:
                        st.write(f"- {item}")


if __name__ == "__main__":
    main()
