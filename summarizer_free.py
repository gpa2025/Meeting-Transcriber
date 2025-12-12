"""
Free web-based AI models integration for meeting summarization.

This module provides functions to:
1. Connect to free AI services (Ollama, Hugging Face, OpenAI-compatible APIs)
2. Generate meeting summaries using free models
3. Parse and structure the AI responses

Author: Gianpaolo Albanese
Date: 2024
"""

import os
import json
import requests
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_notes_with_free_models(transcript):
    """
    Generate meeting notes using free web-based models.
    
    Args:
        transcript (str): The meeting transcript text
        
    Returns:
        tuple: (summary, key_points, action_items)
    """
    # Ensure local storage directory exists
    local_storage_dir = os.environ.get('LOCAL_STORAGE_DIR', '')
    if local_storage_dir and not os.path.exists(local_storage_dir):
        os.makedirs(local_storage_dir, exist_ok=True)
        logger.info(f"Created local storage directory: {local_storage_dir}")
    
    model_id = os.environ.get('FREE_MODEL_ID', 'ollama:llama3.2')
    
    if model_id.startswith('ollama:'):
        return generate_with_ollama(transcript, model_id.split(':', 1)[1])
    elif model_id.startswith('hf:'):
        return generate_with_huggingface(transcript, model_id.split(':', 1)[1])
    elif model_id.startswith('openai-free:'):
        return generate_with_openai_compatible(transcript, model_id.split(':', 1)[1])
    else:
        raise ValueError(f"Unsupported free model: {model_id}")

def generate_with_ollama(transcript, model_name):
    """Generate notes using local Ollama instance."""
    ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    
    prompt = create_simple_prompt(transcript)
    
    response = requests.post(f"{ollama_url}/api/generate", json={
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": float(os.environ.get('MODEL_TEMPERATURE', '0.7')),
            "num_predict": int(os.environ.get('MAX_TOKENS', '4096'))
        }
    })
    
    if response.status_code == 200:
        result = response.json()
        return parse_simple_response(result.get('response', ''))
    else:
        raise Exception(f"Ollama API error: {response.status_code}")

def generate_with_huggingface(transcript, model_name):
    """Generate notes using Hugging Face Inference API."""
    hf_token = os.environ.get('HF_TOKEN')
    if not hf_token:
        raise EnvironmentError("HF_TOKEN required for Hugging Face models")
    
    prompt = create_simple_prompt(transcript)
    
    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model_name}",
        headers={"Authorization": f"Bearer {hf_token}"},
        json={
            "inputs": prompt,
            "parameters": {
                "temperature": float(os.environ.get('MODEL_TEMPERATURE', '0.7')),
                "max_new_tokens": int(os.environ.get('MAX_TOKENS', '1024'))
            }
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        text = result[0].get('generated_text', '') if isinstance(result, list) else result.get('generated_text', '')
        return parse_simple_response(text)
    else:
        raise Exception(f"Hugging Face API error: {response.status_code}")

def generate_with_openai_compatible(transcript, model_name):
    """Generate notes using OpenAI-compatible free APIs."""
    api_url = os.environ.get('OPENAI_COMPATIBLE_URL', 'https://api.together.xyz/v1')
    api_key = os.environ.get('OPENAI_COMPATIBLE_KEY')
    
    if not api_key:
        raise EnvironmentError("OPENAI_COMPATIBLE_KEY required")
    
    prompt = create_simple_prompt(transcript)
    
    response = requests.post(f"{api_url}/chat/completions", 
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": float(os.environ.get('MODEL_TEMPERATURE', '0.7')),
            "max_tokens": int(os.environ.get('MAX_TOKENS', '4096'))
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        text = result['choices'][0]['message']['content']
        return parse_simple_response(text)
    else:
        raise Exception(f"OpenAI-compatible API error: {response.status_code}")

def create_simple_prompt(transcript):
    """Create a simplified prompt for free models."""
    return f"""Analyze this meeting transcript and create detailed meeting notes with:

1. SUMMARY (2-3 paragraphs)
2. KEY POINTS (bullet list)
3. ACTION ITEMS (with owners if mentioned)

Transcript:
{transcript[:20000]}"""  # Limit for free models

def parse_simple_response(text):
    """Parse response from free models."""
    summary = ""
    key_points = []
    action_items = []
    
    sections = text.split('\n\n')
    current_section = None
    
    for section in sections:
        if 'SUMMARY' in section.upper():
            current_section = 'summary'
            summary = section.replace('SUMMARY', '').strip()
        elif 'KEY POINTS' in section.upper() or 'TAKEAWAYS' in section.upper():
            current_section = 'points'
        elif 'ACTION' in section.upper():
            current_section = 'actions'
        elif current_section == 'summary' and not summary:
            summary = section.strip()
        elif current_section == 'points':
            points = [line.strip('- •*').strip() for line in section.split('\n') if line.strip().startswith(('- ', '• ', '* '))]
            key_points.extend(points)
        elif current_section == 'actions':
            actions = [line.strip('- •*').strip() for line in section.split('\n') if line.strip().startswith(('- ', '• ', '* '))]
            action_items.extend(actions)
    
    return summary or "Summary not available", key_points or ["No key points extracted"], action_items or ["No action items found"]