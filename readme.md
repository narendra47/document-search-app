**Document Search Application**

A Python-based document search application that indexes PDF files from Google Drive and provides full-text search capabilities using Elasticsearch.

# Features
Google Drive Integration: Automatically fetches PDF files from Google Drive
Full-Text Search: Powerful search across document content and metadata
RESTful API: Easy-to-use HTTP API endpoints
Command Line Interface: CLI tool for easy interaction
Real-time Indexing: Keeps search index synchronized with Google Drive
Modular Architecture: Clean, maintainable OOP design

# Prerequisites
**System Requirements**

Windows 10/11
Python 3.8 or higher
Java JDK 11 or higher (for Elasticsearch)
Internet connection (for Google Drive access)

Software Dependencies

Elasticsearch 8.x
Google Drive API credentials

🛠️ Installation Guide
Step 1: Install Python Dependencies

Create project directory and navigate to it:
bashmkdir document_search
cd document_search

Create and activate virtual environment:
bashpython -m venv document_search_env
document_search_env\Scripts\activate

Install required packages:
bashpip install -r requirements.txt


Step 2: Install and Setup Elasticsearch

Download Elasticsearch 8.x:

Go to Elasticsearch Downloads
Download the Windows ZIP file


Extract and setup:
bash# Extract to C:\elasticsearch

Add C:\elasticsearch\bin to your PATH environment variable

Start Elasticsearch:
bash# Open new Command Prompt
cd C:\elasticsearch\bin
elasticsearch.bat

Verify installation:

Open browser and go to http://localhost:9200
You should see Elasticsearch cluster information



Step 3: Setup Google Drive API

Enable Google Drive API:

Go to Google Cloud Console
Create a new project or select existing one
Navigate to "APIs & Services" > "Library"
Search and enable "Google Drive API"


Create OAuth 2.0 Credentials:

Go to "APIs & Services" > "Credentials"
Click "Create Credentials" > "OAuth client ID"
Choose "Desktop application"
Download the credentials file as credentials.json


Setup OAuth Consent Screen:

Configure the OAuth consent screen
Add required scopes: https://www.googleapis.com/auth/drive.readonly
Add your email as test user


Place credentials file:
bash# Copy credentials.json to your project root directory
copy /path/to/downloaded/credentials.json ./credentials.json