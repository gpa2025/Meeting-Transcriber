"""
Utility functions for the meeting transcriber application.
"""

import os
import logging
import time
from datetime import datetime

def setup_logging():
    """
    Set up logging configuration.
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Set up logging
    log_filename = f"logs/meeting_transcriber_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def save_to_file(content, file_path):
    """
    Save content to a file.
    
    Args:
        content (str): Content to save
        file_path (str): Path to save the file
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_file_duration(audio_file_path):
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        float: Duration in seconds
    """
    from pydub import AudioSegment
    
    audio = AudioSegment.from_file(audio_file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

def format_time(seconds):
    """
    Format time in seconds to HH:MM:SS format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def create_sample_env_file():
    """
    Create a sample .env file with required environment variables.
    """
    env_content = """# AWS Credentials (required for AWS Transcribe)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# AI Model Settings
# Uncomment and set if you want to use a specific model
# AI_MODEL_PATH=path/to/local/model
"""
    
    # Don't overwrite existing .env file
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("Created sample .env file. Please update with your credentials.")
    else:
        print(".env file already exists. Skipping creation.")