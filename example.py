"""
Example script demonstrating how to use the meeting transcriber.
"""

import os
from transcriber import transcribe_audio
from summarizer import generate_meeting_notes
from utils import setup_logging, save_to_file, create_sample_env_file

def run_example():
    """
    Run an example transcription and summarization on a sample audio file.
    """
    # Set up logging
    logger = setup_logging()
    
    # Create sample .env file if it doesn't exist
    create_sample_env_file()
    
    # Check if sample audio file exists
    sample_audio = "sample_meeting.mp3"
    if not os.path.exists(sample_audio):
        logger.error(f"Sample audio file '{sample_audio}' not found.")
        logger.info("Please place a sample audio file named 'sample_meeting.mp3' in the project directory.")
        return
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Step 1: Transcribe audio
    logger.info(f"Transcribing sample audio file: {sample_audio}")
    transcript = transcribe_audio(sample_audio, method="local")
    
    # Save transcript to file
    transcript_file = "output/sample_transcript.txt"
    save_to_file(transcript, transcript_file)
    logger.info(f"Transcript saved to {transcript_file}")
    
    # Step 2: Generate meeting notes with AI
    logger.info("Generating meeting notes with AI...")
    meeting_notes = generate_meeting_notes(transcript)
    
    # Save meeting notes to file
    notes_file = "output/sample_meeting_notes.md"
    save_to_file(meeting_notes, notes_file)
    logger.info(f"Meeting notes saved to {notes_file}")
    
    print("\nExample completed successfully!")
    print(f"Transcript: {transcript_file}")
    print(f"Meeting Notes: {notes_file}")

if __name__ == "__main__":
    run_example()