# City Meeting Summarizer 🏛️

An AI-powered application that automatically transcribes and summarizes city council meetings from Snoqualmie, WA.

## Features

- 📋 **Meeting Browser**: Fetch and browse available meetings from Snoqualmie's MuniCode Meetings website
- 🎬 **Video Transcription**: Automatically transcribe meeting videos using TranscriptAPI
- 🤖 **AI Summarization**: Generate comprehensive meeting summaries using OpenAI's ChatGPT
- 📄 **Document Access**: View and download meeting-related documents
- 🎯 **Action Item Extraction**: Automatically identify and list action items from meetings
- 💾 **Export Summaries**: Download generated summaries for offline use

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (for ChatGPT summarization)
- TranscriptAPI key (for video transcription)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/camschilling/city-meeting-summarizer.git
cd city-meeting-summarizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
TRANSCRIPTAPI_KEY=your_transcriptapi_key_here
```

## Usage

Run the application using Streamlit:
```bash
streamlit run app.py
```

The application will open in your web browser at `http://localhost:8501`.

## Workflow

1. **Select Meeting**: Click "Fetch Available Meetings" to load meetings from the Snoqualmie website
2. **Choose Meeting**: Select a meeting from the list to view its details
3. **Transcribe**: Navigate to the "Transcribe" tab and start video transcription
4. **Generate Summary**: Once transcription is complete, go to the "Summary" tab and generate an AI-powered summary
5. **Review & Export**: Review the summary and optionally extract action items or download the summary

## Project Structure

```
city-meeting-summarizer/
├── app.py                    # Main Streamlit application
├── meeting_scraper.py        # Web scraper for fetching meeting data
├── transcript_service.py     # TranscriptAPI integration
├── summarizer_service.py     # OpenAI/ChatGPT integration
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment configuration
└── README.md                # This file
```

## API Documentation

### MeetingScraper
Handles fetching meeting information from the Snoqualmie MuniCode Meetings website.

### TranscriptService
Manages video transcription through TranscriptAPI. Supports asynchronous job submission and status polling.

### SummarizerService
Generates meeting summaries using OpenAI's GPT-4. Includes support for context-aware summarization and action item extraction.

## Configuration

The application uses environment variables for API keys. These should be stored in a `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key for ChatGPT access
- `TRANSCRIPTAPI_KEY`: Your TranscriptAPI key for video transcription

## Notes

- Video transcription can take significant time depending on video length
- OpenAI API calls incur costs based on usage
- The scraper is designed for Snoqualmie's MuniCode Meetings website structure

## Troubleshooting

**Missing API Keys**: Ensure `.env` file exists and contains valid API keys

**Transcription Timeout**: For long videos, the transcription may take longer than expected. The service will poll for completion.

**Scraping Issues**: If meeting data isn't loading, the website structure may have changed and the scraper may need updates.

## License

This project is provided as-is for educational and civic engagement purposes.
