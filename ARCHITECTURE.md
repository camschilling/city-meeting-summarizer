# Application Workflow Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    City Meeting Summarizer                   │
│                     (Streamlit Web App)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Meeting        │  │  Transcript     │  │  Summarizer     │
│  Scraper        │  │  Service        │  │  Service        │
│                 │  │                 │  │                 │
│ - Fetch list    │  │ - Submit video  │  │ - Generate      │
│ - Get details   │  │ - Poll status   │  │   summary       │
│ - Download docs │  │ - Get transcript│  │ - Extract       │
│                 │  │                 │  │   action items  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Snoqualmie      │  │ TranscriptAPI   │  │ OpenAI GPT-4    │
│ MuniCode Site   │  │ (transcription) │  │ (summarization) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## User Interface Flow

### Tab 1: Select Meeting
```
┌────────────────────────────────────────────────────────────┐
│ 📋 Select Meeting                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [🔄 Fetch Available Meetings]                            │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 📅 City Council Meeting - January 15, 2025        │   │
│  │ URL: https://snoqualmie-wa.municodemeetings.com/...│   │
│  │                                        [Select]     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 📅 Planning Commission - January 10, 2025         │   │
│  │ URL: https://snoqualmie-wa.municodemeetings.com/...│   │
│  │                                        [Select]     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Tab 2: Transcribe
```
┌────────────────────────────────────────────────────────────┐
│ 🎬 Transcribe Meeting Video                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Meeting: City Council Meeting                            │
│  Date: January 15, 2025                                   │
│                                                            │
│  Video URL: https://video.municode.com/...                │
│                                                            │
│  [🎬 Start Transcription]                                 │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Transcript Preview:                                │   │
│  │                                                    │   │
│  │ The meeting was called to order at 7:00 PM by     │   │
│  │ Mayor Jones. All council members were present...  │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  📄 Available Documents:                                  │
│  - Agenda.pdf                                             │
│  - Previous Minutes.pdf                                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Tab 3: Summary
```
┌────────────────────────────────────────────────────────────┐
│ 📝 Meeting Summary                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  City Council Meeting                                      │
│                                                            │
│  [✨ Generate Summary]  [🎯 Extract Action Items]         │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 📋 Meeting Summary                                 │   │
│  │                                                    │   │
│  │ **Key Topics Discussed:**                          │   │
│  │ 1. Budget approval for fiscal year 2025           │   │
│  │ 2. New park development proposal                  │   │
│  │ 3. Traffic safety improvements on Main Street     │   │
│  │                                                    │   │
│  │ **Important Decisions:**                           │   │
│  │ - Budget approved unanimously (5-0 vote)          │   │
│  │ - Park development moved to planning phase        │   │
│  │                                                    │   │
│  │ **Action Items:**                                  │   │
│  │ - Staff to prepare detailed park proposal         │   │
│  │ - Traffic study to be completed by March 1        │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  [📥 Download Summary]                                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Data Flow

1. **User Action**: Click "Fetch Available Meetings"
   - App calls `MeetingScraper.get_meetings()`
   - Scraper fetches and parses HTML from Snoqualmie website
   - Returns list of meetings with titles and URLs

2. **User Action**: Select a specific meeting
   - App calls `MeetingScraper.get_meeting_details(meeting_url)`
   - Scraper extracts video URL, documents, and metadata
   - Displays meeting details in Transcribe tab

3. **User Action**: Click "Start Transcription"
   - App calls `TranscriptService.transcribe_and_wait(video_url)`
   - Service submits video to TranscriptAPI
   - Polls for completion (every 30 seconds)
   - Returns full transcript text

4. **User Action**: Click "Generate Summary"
   - App calls `SummarizerService.generate_summary(transcript, ...)`
   - Service constructs prompt with transcript and context
   - Sends to OpenAI GPT-4 API
   - Returns formatted summary

5. **User Action**: Click "Extract Action Items" (Optional)
   - App calls `SummarizerService.extract_action_items(transcript)`
   - Service uses specialized prompt to identify action items
   - Returns list of actionable items

6. **User Action**: Click "Download Summary"
   - Browser downloads the summary as a text file
   - Filename includes meeting date for easy organization

## Configuration Requirements

- **OPENAI_API_KEY**: Required for summary generation
- **TRANSCRIPTAPI_KEY**: Required for video transcription  
- **TRANSCRIPTAPI_URL**: Optional, defaults to standard endpoint

All configuration is loaded from `.env` file at application startup.
