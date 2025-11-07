# Streamlit Cloud Deployment Guide

## 🚀 Deploy to Streamlit Cloud

### Prerequisites
1. **OpenAI API Key** (required)
2. **TranscriptAPI Key** (optional - for non-YouTube videos)

### Deployment Steps

#### 1. **Fork/Push to GitHub**
Make sure your repository is available on GitHub.

#### 2. **Go to Streamlit Cloud**
Visit [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.

#### 3. **Create New App**
- Click "New app"
- Select your repository: `camschilling/city-meeting-summarizer`
- Set branch: `deploy` (or `main`)
- Set main file path: `app.py`
- Click "Deploy"

#### 4. **Configure Secrets**
Once your app is deploying, go to the app dashboard and:

1. Click the **⚙️ Settings** button
2. Go to the **🔐 Secrets** tab
3. Add your API keys in TOML format:

```toml
# Required - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY = "sk-your-openai-api-key-here"

# Optional - For non-YouTube video transcription
TRANSCRIPTAPI_KEY = "your-transcriptapi-key-here"

# Optional - Custom transcription API URL (if needed)
# TRANSCRIPTAPI_URL = "https://api.transcriptapi.com/v1"
```

#### 5. **Save and Redeploy**
Click "Save" and your app will automatically redeploy with the new secrets.

### 🔑 **Getting API Keys**

#### OpenAI API Key (Required)
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

#### TranscriptAPI Key (Optional)
Only needed if you want to transcribe non-YouTube videos automatically.
1. Sign up at your transcription service provider
2. Get your API key from the dashboard
3. Add to Streamlit secrets

### 🏠 **Local Development**
For local development, you can either:
1. Use `.env` file (as before)
2. Use `.streamlit/secrets.toml` (new way)

The app will automatically detect which method to use.

### 🛠 **Troubleshooting**

#### App won't start?
- Check that all required dependencies are in `requirements.txt`
- Verify your `OPENAI_API_KEY` is correctly set in secrets

#### API errors?
- Ensure your OpenAI API key has sufficient credits
- Check that the key has the correct permissions

#### Need help?
Check the [Streamlit Community Forum](https://discuss.streamlit.io) or [Streamlit Documentation](https://docs.streamlit.io).