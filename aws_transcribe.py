"""
AWS Transcribe direct implementation without speech_recognition dependency.

This module provides a direct implementation of AWS Transcribe functionality
without relying on the speech_recognition package, which has dependencies
that may not be available in newer Python versions.
"""

import os
import time
import json
import logging
import boto3
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

def transcribe_with_aws(audio_file_path):
    """
    Transcribe audio using AWS Transcribe service directly.
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    logger.info("Using AWS Transcribe service")
    
    # Check if AWS credentials are configured
    if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
        raise EnvironmentError("AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
    
    # Create a client for the AWS Transcribe service
    transcribe = boto3.client('transcribe',
                             region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    # Upload file to S3 (required for AWS Transcribe)
    s3 = boto3.client('s3',
                     region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    bucket_name = os.environ.get('AWS_S3_BUCKET', 'meeting-transcriber-bucket')
    file_name = os.path.basename(audio_file_path)
    s3_path = f"uploads/{file_name}"
    
    logger.info(f"Uploading audio file to S3 bucket: {bucket_name}")
    try:
        s3.upload_file(audio_file_path, bucket_name, s3_path)
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise
    
    # Start transcription job
    job_name = f"transcribe_{os.path.splitext(file_name)[0]}_{int(datetime.now().timestamp())}"
    job_uri = f"s3://{bucket_name}/{s3_path}"
    
    # Determine if speaker diarization is enabled
    enable_diarization = os.environ.get('ENABLE_SPEAKER_DIARIZATION', 'false').lower() == 'true'
    max_speakers = int(os.environ.get('MAX_SPEAKER_LABELS', '10'))
    language_code = os.environ.get('TRANSCRIBE_LANGUAGE_CODE', 'en-US')
    
    # Prepare transcription job parameters
    job_params = {
        'TranscriptionJobName': job_name,
        'Media': {'MediaFileUri': job_uri},
        'MediaFormat': os.path.splitext(file_name)[1][1:],  # Remove the dot from extension
        'LanguageCode': language_code,
        'Settings': {}
    }
    
    # Add speaker diarization settings if enabled
    if enable_diarization:
        logger.info(f"Enabling speaker diarization with max {max_speakers} speakers")
        job_params['Settings']['ShowSpeakerLabels'] = True
        job_params['Settings']['MaxSpeakerLabels'] = max_speakers
    
    logger.info(f"Starting AWS Transcribe job: {job_name}")
    transcribe.start_transcription_job(**job_params)
    
    # Wait for the job to complete with progress updates
    dots = 0
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        job_status = status['TranscriptionJob']['TranscriptionJobStatus']
        
        if job_status in ['COMPLETED', 'FAILED']:
            break
            
        # Print a progress indicator with dots
        dots = (dots % 3) + 1
        progress_indicator = '.' * dots + ' ' * (3 - dots)
        logger.info(f"Waiting for transcription to complete{progress_indicator}")
        print(f"Waiting for transcription to complete{progress_indicator}")
        time.sleep(30)
    
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        # Get the transcript
        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        
        # Download and parse the transcript
        logger.info(f"Downloading transcript from {transcript_uri}")
        with urllib.request.urlopen(transcript_uri) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Basic transcript text
            transcript = data['results']['transcripts'][0]['transcript']
            
            # If speaker diarization was enabled, process the speaker segments
            if enable_diarization and 'speaker_labels' in data['results']:
                return process_speaker_segments(data, transcript)
            
            return transcript
    else:
        error = status['TranscriptionJob'].get('FailureReason', 'Unknown error')
        logger.error(f"Transcription job failed: {error}")
        raise Exception(f"AWS Transcribe job failed: {error}")


def process_speaker_segments(transcription_data, full_transcript):
    """
    Process speaker segments from AWS Transcribe results.
    
    Args:
        transcription_data (dict): The full AWS Transcribe response
        full_transcript (str): The complete transcript text
        
    Returns:
        dict: A dictionary containing the formatted transcript with speaker labels
    """
    logger.info("Processing speaker segments from transcription")
    
    # Extract speaker segments and items (words)
    speaker_labels = transcription_data['results']['speaker_labels']
    segments = speaker_labels['segments']
    items = transcription_data['results']['items']
    
    # Map each word to its speaker
    word_to_speaker = {}
    for segment in segments:
        speaker_label = segment['speaker_label']
        for item in segment['items']:
            word_to_speaker[item['start_time']] = speaker_label
    
    # Build a formatted transcript with speaker labels
    formatted_transcript = []
    current_speaker = None
    current_segment = ""
    
    for item in items:
        # Skip non-pronunciation items (like punctuation)
        if item['type'] != 'pronunciation':
            if current_segment and item.get('alternatives'):
                current_segment += item['alternatives'][0]['content']
            continue
            
        start_time = item['start_time']
        word = item['alternatives'][0]['content']
        speaker = word_to_speaker.get(start_time, "Unknown")
        
        # If speaker changes, start a new segment
        if speaker != current_speaker:
            if current_segment:
                formatted_transcript.append({
                    "speaker": current_speaker,
                    "text": current_segment.strip()
                })
            current_speaker = speaker
            current_segment = word
        else:
            current_segment += " " + word
            
        # Add punctuation if available
        next_index = items.index(item) + 1
        if next_index < len(items) and items[next_index]['type'] == 'punctuation':
            current_segment += items[next_index]['alternatives'][0]['content']
    
    # Add the last segment
    if current_segment:
        formatted_transcript.append({
            "speaker": current_speaker,
            "text": current_segment.strip()
        })
    
    return {
        "full_transcript": full_transcript,
        "speaker_segments": formatted_transcript
    }