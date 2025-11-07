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
    scraper, transcript_service, summarizer, youtube_service = init_services()
    
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
            meetings = st.session_state['meetings']
            st.success(f"Found {len(meetings)} meetings")
            
            # Add sorting options
            col1, col2 = st.columns([3, 1])
            with col2:
                sort_order = st.selectbox(
                    "Sort by:",
                    ["Newest First", "Oldest First", "A-Z", "Z-A"],
                    index=0
                )
            
            # Sort meetings based on user preference
            if sort_order == "Newest First":
                # Sort by date descending (newest first)
                meetings_sorted = sorted(meetings, key=lambda x: x.get('date', ''), reverse=True)
            elif sort_order == "Oldest First":
                # Sort by date ascending (oldest first)
                meetings_sorted = sorted(meetings, key=lambda x: x.get('date', ''))
            elif sort_order == "A-Z":
                # Sort by title A-Z
                meetings_sorted = sorted(meetings, key=lambda x: x.get('title', ''))
            else:  # Z-A
                # Sort by title Z-A
                meetings_sorted = sorted(meetings, key=lambda x: x.get('title', ''), reverse=True)
            
            # Display meetings
            for idx, meeting in enumerate(meetings_sorted):
                # Create a comprehensive title with date
                meeting_title = meeting.get('title', 'Unknown Meeting')
                meeting_date = meeting.get('date', '')
                
                # Format the display title
                if meeting_date:
                    display_title = f"📅 {meeting_title} ({meeting_date})"
                else:
                    display_title = f"📅 {meeting_title}"
                
                with st.expander(display_title):
                    st.write(f"**Meeting:** {meeting_title}")
                    if meeting_date:
                        st.write(f"**Date & Time:** {meeting_date}")
                    st.write(f"**Meeting URL:** {meeting.get('url', 'N/A')}")
                    
                    # Show available documents if any
                    documents = meeting.get('documents', [])
                    if documents:
                        st.write(f"**Available Documents:** {len(documents)}")
                        for doc in documents[:3]:  # Show first 3 documents
                            st.write(f"  • {doc.get('title', 'Document')}")
                        if len(documents) > 3:
                            st.write(f"  • ... and {len(documents) - 3} more")
                    else:
                        st.write("**Available Documents:** None")
                    
                    # Use original index for button key to maintain consistency
                    original_idx = meetings.index(meeting)
                    if st.button(f"Select Meeting", key=f"select_{original_idx}"):
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
                # Determine video platform
                platform = scraper.get_video_platform(video_url)
                st.write(f"**Video URL:** {video_url}")
                st.write(f"**Platform:** {platform}")
                
                # Show platform-specific guidance
                if platform == "YouTube":
                    st.warning("⚠️ **YouTube Video Detected**")
                    st.info("""
                    **Note:** This is a YouTube video. Most transcription services cannot directly process YouTube URLs.
                    """)
                    
                    # YouTube transcript options
                    st.markdown("### 📝 Transcript Options for YouTube Videos")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🌐 Manual Transcription (Recommended)**")
                        st.markdown(f"""
                        1. **Copy this YouTube URL:** `{video_url}`
                        2. **Visit:** [youtubetotranscript.com](https://youtubetotranscript.com/)
                        3. **Paste the URL** and click "Get Transcript"
                        4. **Copy the transcript** and paste it below
                        """)
                        
                        # Direct link to the service with the video URL
                        youtube_video_id = video_url.split('v=')[-1].split('&')[0] if 'v=' in video_url else ''
                        if youtube_video_id:
                            st.markdown(f"🔗 **Quick Link:** [Open in YouTubeToTranscript](https://youtubetotranscript.com/?url={video_url})")
                        
                        st.markdown("---")
                        
                        # Text area for manual transcript input
                        st.markdown("**Paste Transcript Here:**")
                        manual_transcript = st.text_area(
                            "Transcript", 
                            height=200, 
                            placeholder="Paste the transcript from youtubetotranscript.com here...",
                            key="manual_transcript_input"
                        )
                        
                        if manual_transcript and st.button("✅ Use Manual Transcript", type="primary"):
                            st.session_state['transcript'] = manual_transcript
                            st.success("✅ Transcript loaded successfully!")
                            st.rerun()
                        
                        # Add option to try YouTube transcript service
                        st.markdown("---")
                        st.markdown("**🤖 Try YouTube Transcript Service**")
                        if st.button("📝 Get YouTube Transcript", type="secondary"):
                            with st.spinner("Attempting to get transcript from YouTube..."):
                                youtube_transcript = youtube_service.get_transcript(video_url)
                                
                                if youtube_transcript and "MANUAL TRANSCRIPTION REQUIRED" not in youtube_transcript:
                                    st.session_state['transcript'] = youtube_transcript
                                    st.success("✅ YouTube transcript retrieved!")
                                    st.rerun()
                                else:
                                    st.warning("⚠️ Automatic YouTube transcription not available. Please use manual method above.")
                                    if youtube_transcript:
                                        st.text(youtube_transcript)
                    
                    with col2:
                        st.markdown("**🤖 Try Automatic Transcription**")
                        st.markdown("This may not work with YouTube URLs, but you can try:")
                        
                        if st.button("🎬 Try Auto Transcription", type="secondary"):
                            with st.spinner("Attempting transcription... This may fail for YouTube URLs."):
                                transcript = transcript_service.transcribe_and_wait(video_url)
                                
                                if transcript:
                                    st.session_state['transcript'] = transcript
                                    st.success("✅ Transcription complete!")
                                    st.text_area("Transcript Preview", transcript, height=200)
                                else:
                                    st.error("❌ Transcription failed. Please use the manual method above.")
                        
                        st.markdown("---")
                        st.markdown("**Alternative: Direct Video URL**")
                        manual_url = st.text_input("Direct Video URL (MP4, WebM, etc.)", key="manual_direct_url")
                        if manual_url and st.button("Use Direct URL"):
                            st.session_state['selected_meeting']['video_url'] = manual_url
                            st.success("Updated video URL!")
                            st.rerun()
                
                elif platform == "Vimeo":
                    st.info("📹 **Vimeo Video Detected** - Some transcription services support Vimeo URLs.")
                    
                    if st.button("🎬 Start Transcription", type="primary"):
                        with st.spinner("Submitting video for transcription... This may take a while."):
                            transcript = transcript_service.transcribe_and_wait(video_url)
                            
                            if transcript:
                                st.session_state['transcript'] = transcript
                                st.success("✅ Transcription complete!")
                                st.text_area("Transcript Preview", transcript, height=300)
                            else:
                                st.error("❌ Transcription failed. Check if your transcription service supports Vimeo URLs.")
                
                elif platform == "Direct Video File":
                    st.success("✅ **Direct Video File Detected** - Should work with most transcription services.")
                    
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
                    st.warning("⚠️ **Unknown Video Platform** - Transcription may not work.")
                    
                    if st.button("🎬 Try Transcription", type="secondary"):
                        with st.spinner("Attempting transcription..."):
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
