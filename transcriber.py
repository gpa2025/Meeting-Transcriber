"""
Audio transcription module for meeting recordings.
Supports both local transcription using SpeechRecognition and AWS Transcribe.
"""

import os
import speech_recognition as sr
from pydub import AudioSegment
import boto3
import tempfile
import logging

logger = logging.getLogger(__name__)

def transcribe_audio(audio_file_path, method="local"):
    """
    Transcribe audio file to text.
    
    Args:
        audio_file_path (str): Path to the audio file
        method (str): Transcription method - 'local' or 'aws'
        
    Returns:
        str: Transcribed text
    """
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    if method == "local":
        return transcribe_local(audio_file_path)
    elif method == "aws":
        return transcribe_aws(audio_file_path)
    else:
        raise ValueError(f"Unsupported transcription method: {method}")

def transcribe_local(audio_file_path):
    """
    Transcribe audio using local SpeechRecognition library.
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    logger.info("Using local transcription with SpeechRecognition")
    
    # Convert audio to WAV format if needed
    file_ext = os.path.splitext(audio_file_path)[1].lower()
    
    recognizer = sr.Recognizer()
    
    # Process audio in chunks if it's large
    if file_ext != ".wav":
        logger.info(f"Converting {file_ext} to WAV format")
        audio = AudioSegment.from_file(audio_file_path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
            audio.export(temp_wav_path, format="wav")
            audio_file_path = temp_wav_path
    
    # Transcribe audio
    with sr.AudioFile(audio_file_path) as source:
        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)
        
        logger.info("Processing audio file...")
        full_transcript = ""
        
        # Process audio in chunks of 30 seconds
        chunk_duration = 30000  # 30 seconds in milliseconds
        audio_segment = AudioSegment.from_file(audio_file_path)
        
        for i, chunk in enumerate(audio_segment[::chunk_duration]):
            logger.info(f"Processing chunk {i+1}...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_chunk:
                chunk_path = temp_chunk.name
                chunk.export(chunk_path, format="wav")
            
            with sr.AudioFile(chunk_path) as chunk_source:
                audio_data = recognizer.record(chunk_source)
                try:
                    chunk_text = recognizer.recognize_google(audio_data)
                    full_transcript += chunk_text + " "
                except sr.UnknownValueError:
                    logger.warning(f"Could not understand audio in chunk {i+1}")
                except sr.RequestError as e:
                    logger.error(f"Error with speech recognition service: {e}")
            
            # Clean up temp file
            os.unlink(chunk_path)
    
    # Clean up temp WAV file if we created one
    if file_ext != ".wav" and 'temp_wav_path' in locals():
        os.unlink(temp_wav_path)
        
    return full_transcript.strip()

def transcribe_aws(audio_file_path):
    """
    Transcribe audio using AWS Transcribe service.
    
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
    transcribe = boto3.client('transcribe')
    
    # Upload file to S3 (required for AWS Transcribe)
    s3 = boto3.client('s3')
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
    job_name = f"transcribe_{os.path.splitext(file_name)[0]}_{int(time.time())}"
    job_uri = f"s3://{bucket_name}/{s3_path}"
    
    logger.info(f"Starting AWS Transcribe job: {job_name}")
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat=os.path.splitext(file_name)[1][1:],  # Remove the dot from extension
        LanguageCode='en-US'
    )
    
    # Wait for the job to complete
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        logger.info("Waiting for transcription to complete...")
        time.sleep(30)
    
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        # Get the transcript
        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        
        # Download and parse the transcript
        import urllib.request
        import json
        
        with urllib.request.urlopen(transcript_uri) as response:
            data = json.loads(response.read().decode('utf-8'))
            transcript = data['results']['transcripts'][0]['transcript']
        
        return transcript
    else:
        error = status['TranscriptionJob'].get('FailureReason', 'Unknown error')
        logger.error(f"Transcription job failed: {error}")
        raise Exception(f"AWS Transcribe job failed: {error}")