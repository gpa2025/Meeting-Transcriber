"""
Meeting summarizer module that uses AI to generate meeting notes and takeaways.
"""

import os
import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
import spacy

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

logger = logging.getLogger(__name__)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.info("Downloading spaCy model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def generate_meeting_notes(transcript):
    """
    Generate meeting notes and key takeaways from transcript using AI.
    
    Args:
        transcript (str): The meeting transcript text
        
    Returns:
        str: Formatted meeting notes with key takeaways
    """
    logger.info("Generating meeting notes from transcript")
    
    # Check if transcript is too short
    if len(transcript.split()) < 10:
        logger.warning("Transcript is too short to generate meaningful notes")
        return "The transcript is too short to generate meaningful meeting notes."
    
    # Process the transcript with spaCy for initial analysis
    doc = nlp(transcript)
    
    # Extract sentences
    sentences = list(doc.sents)
    
    # Load summarization model
    logger.info("Loading AI summarization model...")
    model_name = "facebook/bart-large-cnn"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    
    # Split transcript into chunks if it's too long
    max_token_length = 1024
    chunks = split_into_chunks(transcript, max_token_length, tokenizer)
    
    # Summarize each chunk
    summaries = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Summarizing chunk {i+1}/{len(chunks)}")
        summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    
    # Combine summaries
    combined_summary = " ".join(summaries)
    
    # Extract key points using a different model
    logger.info("Extracting key points...")
    key_points = extract_key_points(transcript)
    
    # Format the meeting notes
    meeting_notes = format_meeting_notes(transcript, combined_summary, key_points)
    
    return meeting_notes

def split_into_chunks(text, max_length, tokenizer):
    """
    Split text into chunks that fit within the model's max token length.
    
    Args:
        text (str): Text to split
        max_length (int): Maximum token length
        tokenizer: The tokenizer to use
        
    Returns:
        list: List of text chunks
    """
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_tokens = len(tokenizer.encode(sentence))
        
        if current_length + sentence_tokens > max_length:
            # This chunk is full, start a new one
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_tokens
        else:
            current_chunk.append(sentence)
            current_length += sentence_tokens
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def extract_key_points(transcript):
    """
    Extract key points from the transcript.
    
    Args:
        transcript (str): The meeting transcript
        
    Returns:
        list: List of key points
    """
    # Use a different model for key point extraction
    model_name = "facebook/bart-large-xsum"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    
    # Create a pipeline for extractive summarization
    key_point_extractor = pipeline("summarization", model=model, tokenizer=tokenizer)
    
    # Split transcript into chunks if needed
    max_token_length = 1024
    chunks = split_into_chunks(transcript, max_token_length, tokenizer)
    
    # Extract key points from each chunk
    all_key_points = []
    for chunk in chunks:
        # Generate concise bullet points
        result = key_point_extractor(
            chunk, 
            max_length=60,  # Short summaries for key points
            min_length=10,
            do_sample=True,
            num_return_sequences=3  # Get multiple key points
        )
        
        for item in result:
            point = item['summary_text'].strip()
            if point and point not in all_key_points:
                all_key_points.append(point)
    
    # Limit to top 5-7 key points
    return all_key_points[:7]

def format_meeting_notes(transcript, summary, key_points):
    """
    Format the meeting notes in a readable structure.
    
    Args:
        transcript (str): Original transcript
        summary (str): Generated summary
        key_points (list): List of key points
        
    Returns:
        str: Formatted meeting notes
    """
    # Extract meeting metadata
    doc = nlp(transcript[:min(len(transcript), 1000)])  # Process just the beginning for metadata
    
    # Try to identify participants (this is a simple approach)
    potential_participants = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            potential_participants.append(ent.text)
    
    # Format the notes
    notes = "# Meeting Notes\n\n"
    
    # Add summary section
    notes += "## Summary\n\n"
    notes += f"{summary}\n\n"
    
    # Add key takeaways section
    notes += "## Key Takeaways\n\n"
    for point in key_points:
        notes += f"- {point}\n"
    notes += "\n"
    
    # Add participants if identified
    if potential_participants:
        notes += "## Participants\n\n"
        for participant in set(potential_participants):
            notes += f"- {participant}\n"
        notes += "\n"
    
    # Add link to full transcript
    notes += "## Full Transcript\n\n"
    notes += "See the attached transcript file for the complete meeting transcript.\n"
    
    return notes