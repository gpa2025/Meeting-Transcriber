#!/usr/bin/env python
"""
Meeting Transcriber and Summarizer with AWS Bedrock

This script processes audio recordings of meetings, transcribes them using AWS Transcribe,
and generates detailed meeting notes with AWS Bedrock. It produces structured notes with
key takeaways, action items with owners, and decisions made during the meeting.

Features:
- AWS Transcribe for high-quality transcription with speaker diarization
- AWS Bedrock for AI-powered meeting summarization
- Categorized key takeaways by topic
- Action items with owners and deadlines
- Decisions made during the meeting
- Fallback to simple summarization if AWS Bedrock is unavailable

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.1
Assisted by: Amazon Q for VS Code
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
import nltk
from dotenv import load_dotenv

# Ensure NLTK punkt is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Import AWS direct implementation
from aws_transcribe import transcribe_with_aws
from summarizer_bedrock import generate_notes_with_bedrock
import format_meeting_notes

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def save_to_file(content, file_path):
    """Save content to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def simple_summarize(transcript):
    """
    Simple extractive summarization without external dependencies.
    
    Args:
        transcript (str): The meeting transcript text
        
    Returns:
        tuple: (summary, key_points, action_items)
    """
    logger.info("Generating simple meeting notes")
    
    # Simple extractive summarization
    sentences = nltk.sent_tokenize(transcript)
    
    # Get a simple summary (first few sentences)
    summary_length = min(5, len(sentences))
    summary = " ".join(sentences[:summary_length])
    
    # Extract some key sentences from different parts of the transcript
    key_points = []
    if len(sentences) <= 10:
        key_points = sentences
    else:
        # Take sentences from beginning, middle and end
        key_points = [
            sentences[0],
            sentences[len(sentences)//4],
            sentences[len(sentences)//2],
            sentences[3*len(sentences)//4],
            sentences[-1]
        ]
    
    # Look for potential action items
    action_items = []
    action_indicators = ["need to", "should", "will", "going to", "have to", "must", "action item"]
    
    for sentence in sentences:
        if any(indicator in sentence.lower() for indicator in action_indicators):
            action_items.append(sentence)
            if len(action_items) >= 5:  # Limit to 5 action items
                break
    
    return summary, key_points, action_items

def format_simple_notes(summary, key_points, action_items, meeting_date=None):
    """
    Format simple meeting notes.
    
    Args:
        summary (str): Meeting summary
        key_points (list): List of key points
        action_items (list): List of action items
        meeting_date (datetime): Meeting date
        
    Returns:
        str: Formatted meeting notes
    """
    # Get current date for the notes if not provided
    if meeting_date is None:
        meeting_date = datetime.now()
    
    date_str = meeting_date.strftime("%B %d, %Y")
    
    # Format the notes
    notes = f"# Meeting Notes - {date_str}\n\n"
    
    # Add summary section
    notes += "## Summary\n\n"
    notes += f"{summary}\n\n"
    
    # Add key takeaways section
    notes += "## Key Takeaways\n\n"
    for point in key_points:
        notes += f"- {point}\n"
    notes += "\n"
    
    # Add action items if available
    if action_items:
        notes += "## Action Items\n\n"
        for i, item in enumerate(action_items, 1):
            notes += f"{i}. {item}\n"
        notes += "\n"
    
    # Add link to full transcript
    notes += "## Full Transcript\n\n"
    notes += "The full transcript is available in the attached file.\n"
    
    # Add a timestamp for when the notes were generated
    notes += f"\n---\n*Notes generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*\n"
    
    return notes

def check_aws_credentials():
    """Check if AWS credentials are properly configured."""
    missing_vars = []
    for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"ERROR: Missing required AWS environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all AWS credentials are set.")
        sys.exit(1)
    
    # Check if the Bedrock model is specified
    if not os.environ.get('BEDROCK_MODEL_ID'):
        print("WARNING: BEDROCK_MODEL_ID not specified in .env file. Using default: anthropic.claude-v2")

def get_file_modified_date(file_path):
    """
    Get the modified date of a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        datetime: The file's modification date
    """
    try:
        # Get file modification time (consistent across platforms)
        if os.path.exists(file_path):
            file_time = os.path.getmtime(file_path)
            return datetime.fromtimestamp(file_time)
        else:
            logger.warning(f"File not found: {file_path}")
            return datetime.now()
    except Exception as e:
        logger.warning(f"Could not get file date: {e}")
        return datetime.now()

def main():
    """Main function to process audio and generate meeting notes."""
    # Load environment variables
    load_dotenv()
    
    # Check AWS credentials
    check_aws_credentials()
    
    parser = argparse.ArgumentParser(description="Direct Meeting Transcriber")
    parser.add_argument("audio_file", help="Path to the audio file to transcribe")
    parser.add_argument("--output_dir", default="output", help="Directory to save output files")
    parser.add_argument("--meeting_date", help="Meeting date in YYYY-MM-DD format (defaults to audio file's modified date)")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get base filename without extension
    base_filename = os.path.splitext(os.path.basename(args.audio_file))[0]
    
    # Get the file's modified date to use as meeting date
    file_modified_date = get_file_modified_date(args.audio_file)
    
    # Parse meeting date if provided, otherwise use file's modified date
    meeting_date = None
    if args.meeting_date:
        try:
            meeting_date = datetime.strptime(args.meeting_date, "%Y-%m-%d")
            logger.info(f"Using provided meeting date: {meeting_date.strftime('%B %d, %Y')}")
        except ValueError:
            logger.warning(f"Invalid date format: {args.meeting_date}. Using file's modified date.")
            meeting_date = file_modified_date
    else:
        meeting_date = file_modified_date
        logger.info(f"Using audio file's modified date as meeting date: {meeting_date.strftime('%B %d, %Y')}")
    
    try:
        # Step 1: Transcribe audio using AWS directly
        logger.info(f"Transcribing audio file: {args.audio_file}")
        print(f"Transcribing audio file... (this may take a while)")
        transcript = transcribe_with_aws(args.audio_file)
        
        # Save transcript to file
        if isinstance(transcript, dict) and 'speaker_segments' in transcript:
            # Handle speaker diarization format
            transcript_file = os.path.join(args.output_dir, f"{base_filename}_transcript.txt")
            speaker_transcript_file = os.path.join(args.output_dir, f"{base_filename}_transcript_with_speakers.txt")
            
            # Save plain transcript
            save_to_file(transcript['full_transcript'], transcript_file)
            
            # Save transcript with speaker labels
            speaker_text = ""
            for segment in transcript['speaker_segments']:
                speaker_text += f"{segment['speaker']}: {segment['text']}\n\n"
            save_to_file(speaker_text, speaker_transcript_file)
            
            logger.info(f"Transcript saved to {transcript_file}")
            logger.info(f"Transcript with speakers saved to {speaker_transcript_file}")
            print(f"Transcript saved to {transcript_file}")
            print(f"Transcript with speakers saved to {speaker_transcript_file}")
            
            # Use the full transcript for summarization
            text_for_summary = transcript['full_transcript']
        else:
            # Handle plain text transcript
            transcript_file = os.path.join(args.output_dir, f"{base_filename}_transcript.txt")
            save_to_file(transcript, transcript_file)
            logger.info(f"Transcript saved to {transcript_file}")
            print(f"Transcript saved to {transcript_file}")
            text_for_summary = transcript
        
        # Step 2: Generate meeting notes with AWS Bedrock
        logger.info("Generating meeting notes with AWS Bedrock...")
        print(f"Generating meeting notes with AWS Bedrock... (this may take a while)")
        print(f"Using model: {os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-v2')}")
        
        try:
            # Use AWS Bedrock for advanced summarization
            summary, key_points, action_items = generate_notes_with_bedrock(text_for_summary)
            
            # Extract participants if available
            participants = []
            if isinstance(transcript, dict) and 'speaker_segments' in transcript:
                # Extract unique speakers
                speakers = set()
                for segment in transcript['speaker_segments']:
                    speakers.add(segment['speaker'])
                
                # Add to participants list
                for speaker in speakers:
                    participants.append({
                        'id': speaker,
                        'name': f"Speaker {speaker.split('_')[-1]}" if speaker.startswith('spk_') else speaker
                    })
            
            # Format meeting notes with enhanced formatting
            meeting_notes = format_meeting_notes.format_enhanced_meeting_notes(
                transcript=text_for_summary,
                summary=summary,
                key_points=key_points,
                action_items=action_items,
                participants=participants,
                has_speaker_segments=isinstance(transcript, dict) and 'speaker_segments' in transcript,
                meeting_date=meeting_date  # Use the file's modified date
            )
        except Exception as e:
            error_message = f"Error using AWS Bedrock: {e}"
            logger.error(error_message)
            print(f"\nERROR: {error_message}")
            print("\nDetailed troubleshooting information:")
            
            # Provide detailed troubleshooting information
            if "No module named" in str(e):
                print("- Module import error: A required Python module is missing")
                print("- Solution: Run 'pip install boto3 nltk python-dotenv regex'")
            elif "AccessDeniedException" in str(e):
                print("- AWS Access Denied: Your AWS credentials don't have permission to use this Bedrock model")
                print("- Solution: Check your AWS credentials and ensure you have access to the Bedrock model")
                print("- Note: You may need to request access to the model in the AWS Bedrock console")
            elif "ValidationException" in str(e) and "inference profile" in str(e):
                print("- Inference Profile Required: The selected model requires an inference profile")
                print("- Solution: Use a different model like 'anthropic.claude-v2' or create an inference profile")
                print("- Note: Claude 3 models require inference profiles, Claude 2 models don't")
            elif "ResourceNotFoundException" in str(e):
                print("- Resource Not Found: The specified Bedrock model was not found")
                print("- Solution: Check the model ID in your .env file and ensure it's available in your AWS region")
            elif "ThrottlingException" in str(e):
                print("- Throttling Exception: Too many requests to AWS Bedrock")
                print("- Solution: Wait a few minutes and try again")
            else:
                print(f"- Detailed error: {str(e)}")
                print("- Check your AWS credentials, network connection, and Bedrock model configuration")
            
            # Fallback to simple summarization
            print("\nFalling back to simple summarization...")
            summary, key_points, action_items = simple_summarize(text_for_summary)
            meeting_notes = format_simple_notes(summary, key_points, action_items, meeting_date)
        
        # Save meeting notes to file
        notes_file = os.path.join(args.output_dir, f"{base_filename}_meeting_notes.md")
        save_to_file(meeting_notes, notes_file)
        logger.info(f"Meeting notes saved to {notes_file}")
        
        print(f"\nProcess completed successfully!")
        print(f"Meeting Notes: {notes_file}")
        
    except Exception as e:
        logger.error(f"Error processing audio file: {e}", exc_info=True)
        print(f"\nError: {e}")
        
        # Provide more detailed error information for common issues
        if "No such file or directory" in str(e):
            print("\nThe audio file could not be found. Please check the file path.")
        elif "AccessDenied" in str(e) and "S3" in str(e):
            print("\nAWS S3 access denied. Check your AWS credentials and S3 bucket permissions.")
        elif "TranscribeService" in str(e):
            print("\nAWS Transcribe service error. Check your AWS credentials and region settings.")
        
        sys.exit(1)

if __name__ == "__main__":
    main()