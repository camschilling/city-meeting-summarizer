# Quick Start Guide

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/camschilling/city-meeting-summarizer.git
   cd city-meeting-summarizer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file and add your API keys:
   - `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys
   - `TRANSCRIPTAPI_KEY`: Get from https://transcriptapi.com (or your transcription service)

## Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The application will open in your web browser at http://localhost:8501

## Using the Application

### Step 1: Select Meeting
1. Click "Fetch Available Meetings" button
2. Browse the list of available meetings
3. Click "Select Meeting" on your desired meeting

### Step 2: Transcribe Video
1. The video URL will be automatically detected
2. Click "Start Transcription" to begin
3. Wait for the transcription to complete (this may take several minutes)

### Step 3: Generate Summary
1. Once transcription is complete, go to the "Summary" tab
2. Click "Generate Summary" to create an AI-powered summary
3. Review the summary
4. Optionally click "Extract Action Items" for a focused list of action items
5. Download the summary using the "Download Summary" button

## Troubleshooting

### API Keys Not Working
- Verify your API keys are correctly entered in `.env` file
- Check that `.env` is in the same directory as `app.py`
- Restart the Streamlit application after editing `.env`

### Meetings Not Loading
- The website structure may have changed
- Check your internet connection
- Verify the website is accessible: https://snoqualmie-wa.municodemeetings.com/

### Transcription Taking Too Long
- Large video files can take significant time to transcribe
- The application will poll the transcription service every 30 seconds
- Maximum wait time is 1 hour by default

### Summary Not Generating
- Verify your OpenAI API key is valid
- Check that you have sufficient credits/quota on your OpenAI account
- Ensure the transcript was successfully generated

## Features Overview

- **Automatic Meeting Discovery**: Scrapes Snoqualmie's meeting website
- **Video Transcription**: Converts meeting videos to text
- **AI Summarization**: Uses GPT-4 to create comprehensive summaries
- **Action Item Extraction**: Identifies tasks and decisions from meetings
- **Document Support**: Lists and links to meeting documents
- **Export Functionality**: Download summaries for offline use

## Notes

- The application requires active internet connection
- Transcription and summarization may incur API costs
- For best results, ensure videos have clear audio quality
