# Meeting Transcriber

A tool for transcribing meeting audio and generating detailed meeting notes using AWS services.

## Installation Instructions

1. Extract all files from this ZIP archive to a folder
2. Run Setup.bat to install required Python packages and create shortcuts

## Requirements

- Python 3.7 or higher
- Internet connection for AWS services
- AWS credentials with appropriate permissions

## First-time Setup

1. Run Setup.bat to:
   - Install required Python packages
   - Download NLTK data
   - Create desktop and Start menu shortcuts
   - Create a .env file from .env.example
2. Edit the .env file to add your AWS credentials:
   - AWS_ACCESS_KEY_ID=your_access_key
   - AWS_SECRET_ACCESS_KEY=your_secret_key
   - AWS_REGION=your_region (e.g., us-east-1)
   - S3_BUCKET=your_bucket_name
3. Run LaunchApp.bat to start the application

## Launching the Application

You can launch Meeting Transcriber in several ways:
- Run LaunchApp.bat directly
- Use the desktop shortcut (created by Setup.bat)
- Use the Start menu shortcut (created by Setup.bat)

## Troubleshooting

If you encounter issues with the Setup.bat script:
- Make sure Python is installed and added to your PATH
- Try running the commands manually:
  `
  cd /path/to/extracted/folder
  python -m pip install -r requirements.txt
  python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
  `
- If you see errors related to NLTK, try running:
  `
  python -m nltk.downloader punkt stopwords
  `

## Support

For support, please contact: albaneg@yahoo.com
