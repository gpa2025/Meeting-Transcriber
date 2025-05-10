# Meeting Transcriber User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Setting Up AWS](#setting-up-aws)
4. [Using the Application](#using-the-application)
5. [Understanding the Results](#understanding-the-results)
6. [Troubleshooting](#troubleshooting)

## Introduction

Meeting Transcriber is a powerful tool that uses AWS services to transcribe audio recordings of meetings and generate detailed meeting notes. It leverages AWS Transcribe for speech-to-text conversion and AWS Bedrock for AI-powered summarization.

## Installation

1. **Run the installer**: Double-click on `MeetingTranscriberSetup.exe`
2. **Follow the wizard**: Accept the license agreement and choose installation options
3. **Complete installation**: Click "Finish" to complete the installation
4. **Launch the application**: Use the desktop shortcut or start menu entry

## Setting Up AWS

### AWS Account Requirements

To use Meeting Transcriber, you need an AWS account with access to:
- AWS Transcribe service
- AWS Bedrock service
- AWS S3 service

### Creating AWS Access Keys

1. Log in to the AWS Management Console
2. Click on your username in the top-right corner
3. Select "Security credentials"
4. Under "Access keys", click "Create access key"
5. Download or note your Access Key ID and Secret Access Key

### Setting Up an S3 Bucket

1. Go to the S3 service in the AWS Management Console
2. Click "Create bucket"
3. Enter a unique bucket name
4. Configure bucket settings (default settings are usually fine)
5. Click "Create bucket"

### Enabling AWS Bedrock Access

1. Go to the AWS Bedrock service in the AWS Management Console
2. Request access to the models you want to use (Claude, Titan, etc.)
3. Wait for approval (this may take some time)

## Using the Application

### Configuring AWS Settings

1. Enter your AWS Access Key ID and Secret Access Key
2. Select your AWS Region
3. Enter your S3 Bucket name
4. Click "Save Settings" to store your credentials

### Configuring Bedrock Settings

1. Select the Bedrock model to use (Claude v2 recommended)
2. Set the temperature (0.7 is a good default)
3. Set the maximum tokens (4096 is usually sufficient)
4. Customize the system prompt if desired

### Configuring Transcription Settings

1. Select the language of the audio recording
2. Enable or disable speaker diarization
3. Set the maximum number of speakers (if diarization is enabled)

### Transcribing a Meeting

1. Click "Browse..." next to "Audio File" to select your meeting recording
2. Click "Browse..." next to "Output Directory" to choose where to save the results
3. Click "Start Transcription" to begin the process
4. Monitor progress in the log area

## Understanding the Results

### Output Files

The application generates several files in your chosen output directory:
- `[filename]_transcript.txt`: The raw transcript text
- `[filename]_transcript_with_speakers.txt`: Transcript with speaker labels (if diarization was enabled)
- `[filename]_meeting_notes.md`: Formatted meeting notes in Markdown format

### Meeting Notes Structure

The meeting notes include:
1. **Summary**: A comprehensive overview of the meeting
2. **Key Takeaways**: Important points organized by category
3. **Decisions Made**: Key decisions from the meeting
4. **Action Items**: Tasks with assigned owners (if mentioned)
5. **Participants**: List of meeting participants
6. **Full Transcript**: Reference to the full transcript file

## Troubleshooting

### Common Issues

#### AWS Connection Errors

- **Error**: "Invalid credentials" or "Access denied"
  - **Solution**: Verify your AWS credentials are correct and have the necessary permissions

- **Error**: "Bucket not found"
  - **Solution**: Confirm your S3 bucket name is correct and the bucket exists

#### Transcription Errors

- **Error**: "Unsupported media format"
  - **Solution**: Convert your audio to a supported format (MP3, WAV, M4A, FLAC, OGG)

- **Error**: "File too large"
  - **Solution**: Split large audio files into smaller segments

#### AI Summarization Errors

- **Error**: "Model not found" or "Access denied to model"
  - **Solution**: Ensure you have requested and been granted access to the Bedrock model

- **Error**: "Token limit exceeded"
  - **Solution**: Reduce the max tokens setting or use a model with higher token limits

### Getting Help

If you encounter issues not covered here, please contact me at albaneg@yahoo.com or gianpaoa@amazon.com with:
1. A description of the issue
2. Steps to reproduce the problem
3. Any error messages displayed
4. Log files (if available)