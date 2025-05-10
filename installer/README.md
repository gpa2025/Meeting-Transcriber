# Meeting Transcriber

## Overview

Meeting Transcriber is a tool for transcribing meeting audio and generating detailed meeting notes using AWS services. It uses AWS Transcribe for speech-to-text conversion and AWS Bedrock for AI-powered meeting summarization.

**Author:** Gianpaolo Albanese  
**Version:** 1.0  
**Date:** 05-09-2024  

## Features

- Transcribe audio recordings of meetings using AWS Transcribe
- Generate detailed meeting notes with AWS Bedrock AI
- Speaker diarization (identify different speakers)
- Customizable AI settings
- Save and load settings
- User-friendly GUI interface

## Requirements

1. **AWS Account** with access to:
   - AWS Transcribe service
   - AWS Bedrock service (with access to Claude or Titan models)
   - AWS S3 bucket

2. **AWS Credentials**:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region
   - S3 Bucket name

## Installation

1. Run the installer (`MeetingTranscriberSetup.exe`)
2. Follow the installation wizard instructions
3. Launch the application from the desktop shortcut or start menu

## Getting Started

1. **Configure AWS Settings**:
   - Enter your AWS Access Key and Secret Key
   - Select your AWS Region
   - Enter your S3 Bucket name
   - Configure Bedrock model settings

2. **Select Audio File**:
   - Click "Browse..." to select an audio file (supported formats: MP3, WAV, M4A, FLAC, OGG)

3. **Select Output Directory**:
   - Choose where to save the transcription and meeting notes

4. **Start Transcription**:
   - Click "Start Transcription" to begin the process
   - The progress will be shown in the log area

5. **View Results**:
   - When complete, the transcript and meeting notes will be saved to the output directory
   - Meeting notes are saved in Markdown format

## Troubleshooting

### Common Issues

1. **AWS Connection Errors**:
   - Verify your AWS credentials are correct
   - Ensure your AWS account has access to the required services
   - Check that your S3 bucket exists and is accessible

2. **Transcription Errors**:
   - Ensure the audio file is in a supported format
   - Check that the audio quality is good enough for transcription
   - Verify the selected language matches the audio content

3. **AI Summarization Errors**:
   - Ensure your AWS account has access to the selected Bedrock model
   - Try using a different model if you encounter errors
   - Reduce the max tokens if you're hitting token limits

### Support

For support, please contact:
- Email: albaneg@yahoo.com

## License

This software is proprietary and confidential.
Copyright © 2024 Gianpaolo Albanese. All rights reserved.