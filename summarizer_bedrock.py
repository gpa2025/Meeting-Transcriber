"""
AWS Bedrock integration for meeting summarization.

This module provides functions to:
1. Connect to AWS Bedrock service
2. Generate detailed meeting summaries using large language models
3. Parse and structure the AI responses

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
Assisted by: Amazon Q for VS Code
"""

import os
import json
import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def generate_notes_with_bedrock(transcript):
    """
    Generate detailed meeting notes using AWS Bedrock models.
    
    This function:
    1. Connects to AWS Bedrock service
    2. Sends the transcript to a large language model (Claude, Titan, etc.)
    3. Parses the response to extract summary, key points, action items with owners
    
    Args:
        transcript (str): The meeting transcript text
        
    Returns:
        tuple: (summary, key_points, action_items)
        
    Raises:
        EnvironmentError: If AWS credentials are not configured
        Exception: If the Bedrock API call fails
    """
    logger.info("Using AWS Bedrock for meeting notes generation")
    
    try:
        import boto3
        
        # Check if AWS credentials are configured
        if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
            raise EnvironmentError("AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
        
        # Create a client for the AWS Bedrock service
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Get model parameters from environment variables
        model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-v2')
        # Force model to Claude v2 if using Claude 3 (which requires inference profiles)
        if 'claude-3' in model_id:
            logger.warning(f"Claude 3 model detected ({model_id}). Falling back to Claude v2 which doesn't require inference profiles.")
            model_id = 'anthropic.claude-v2'
        temperature = float(os.environ.get('MODEL_TEMPERATURE', '0.7'))
        max_tokens = int(os.environ.get('MAX_TOKENS', '4096'))
        system_prompt = os.environ.get('SYSTEM_PROMPT', 
                                     'You are an AI assistant that creates detailed and coherent meeting notes from transcripts.')
        
        # Prepare the prompt for the model
        prompt = create_bedrock_prompt(transcript, system_prompt, model_id)
        
        # Call Bedrock based on model type
        logger.info(f"Calling AWS Bedrock with model: {model_id}")
        
        if 'anthropic.claude' in model_id:
            # Claude models
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                })
            )
            response_body = json.loads(response['body'].read())
            result_text = response_body.get('completion', '')
            
        elif 'amazon.titan' in model_id:
            # Amazon Titan models
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": 0.9
                    }
                })
            )
            response_body = json.loads(response['body'].read())
            result_text = response_body.get('results', [{}])[0].get('outputText', '')
            
        else:
            # Generic approach for other models
            logger.warning(f"Using generic request format for model: {model_id}")
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                })
            )
            response_body = json.loads(response['body'].read())
            result_text = response_body.get('generation', '')
        
        # Parse the response to extract summary, key points, and action items
        summary, key_points, action_items = parse_bedrock_response(result_text)
        
        return summary, key_points, action_items
        
    except ImportError:
        logger.error("boto3 package not installed. Install with: pip install boto3")
        # No fallback available in the module, will be handled by the caller
        raise
        
    except Exception as e:
        logger.error(f"Error using AWS Bedrock: {e}")
        # No fallback available in the module, will be handled by the caller
        raise


def create_bedrock_prompt(transcript, system_prompt, model_id):
    """
    Create a detailed prompt for AWS Bedrock models.
    
    Args:
        transcript (str): The meeting transcript
        system_prompt (str): The system prompt to use
        model_id (str): The Bedrock model ID
        
    Returns:
        str: Formatted prompt for the model
    """
    # Truncate transcript if it's too long
    max_transcript_length = 40000  # Adjust based on model context limits
    if len(transcript) > max_transcript_length:
        logger.warning(f"Transcript too long ({len(transcript)} chars), truncating to {max_transcript_length}")
        half_length = max_transcript_length // 2
        transcript = transcript[:half_length] + "\n\n[...transcript truncated...]\n\n" + transcript[-half_length:]
    
    # Extract participant names from the transcript
    participants = extract_participant_names(transcript)
    participants_str = ", ".join(participants) if participants else "Unknown participants"
    
    # Format prompt based on model type
    if 'anthropic.claude' in model_id:
        # Claude requires a specific format with "Human:" at the beginning
        prompt = f"""Human: I need you to analyze this meeting transcript and create EXTREMELY DETAILED and COMPREHENSIVE meeting notes that include:
        
            1. A comprehensive summary of the meeting (3-4 paragraphs) that captures:
                - The main purpose of the meeting (discussing Cloud Raise assessment results)
                - Key topics discussed with ALL specific details, numbers, and metrics mentioned
                - Current infrastructure details with EXACT versions, configurations, and costs
                - Business context including company history, business type, and seasonal patterns
                - Customer's current challenges and pain points
                - Any decisions made or conclusions reached
                
            2. A list of at least 10-15 key takeaways as bullet points that highlight:
                - ALL important facts or insights with specific details
                - ALL technical details mentioned with version numbers and specifications
                - ALL business requirements or constraints with deadlines
                - ALL current state assessments with metrics
                - Group these by topic with clear headings (e.g., "Infrastructure State:", "Modernization Opportunities:", "Timing Constraints:", "Cost Analysis:")
                
            3. A detailed list of next steps with assigned owners where possible:
                - Be extremely specific about what needs to be done
                - Include ALL deadlines if mentioned
                - Assign owners based on who committed to tasks
                - Group these by category (e.g., "Licensing Verification:", "Technical Assessment:", "Architecture Planning:", "Partner Coordination:")
                - Format as "Task description (Owner: Person's name, Deadline: [date if mentioned])"
                
            4. A separate section for decisions made during the meeting:
                - List ALL key decisions that were finalized
                - Include the context or reasoning behind each decision
                
            5. List of participants in the meeting with their roles if mentioned
                
            Meeting participants appear to include: {participants_str}
                
            Format your response with clear headings for each section. Make the notes professional, actionable, and EXTREMELY DETAILED with specific information from the transcript. Extract EVERY piece of specific information including numbers, dates, technical details, costs, and business context.
            
            DO NOT OMIT ANY DETAILS from the transcript. Include ALL specific information about:
            - Current Azure environment (all services, versions, configurations)
            - SQL Server details (versions, editions, utilization)
            - Cost information (current spend, potential savings)
            - Business context (ticket reselling business, seasonal nature, NFL season)
            - Technical challenges and modernization opportunities
            - Timeline constraints (September 1st deadline)
                
            Here's the transcript:
                
            {transcript}
                
            Assistant:"""
    else:
        # Generic prompt format for other models
        prompt = f"""{system_prompt}
        
        TASK: Analyze the following meeting transcript and create detailed meeting notes that include:
        
        1. SUMMARY (2-3 paragraphs):
           - Main purpose of the meeting
           - Key topics discussed
           - Business context and background
           - Decisions or conclusions
        
        2. KEY TAKEAWAYS (6-10 bullet points):
           - Important facts or insights
           - Technical details mentioned
           - Business requirements or constraints
           - Current state assessments
           - Categorize by topic where possible (e.g., "Technical: [point]", "Business: [point]")
        
        3. ACTION ITEMS (with owners and deadlines):
           - Specific tasks to be completed
           - Include deadlines if mentioned
           - Assign owners based on who committed to tasks
           - Format as "Task description (Owner: Person's name, Deadline: [date if mentioned])"
        
        4. DECISIONS MADE:
           - List 3-5 key decisions that were finalized
           - Include context or reasoning for each decision
        
        5. PARTICIPANTS:
           - List meeting attendees with roles if mentioned
        
        Meeting participants appear to include: {participants_str}
        
        FORMAT:
        # Meeting Notes - [Date]
        
        ## Summary
        [Your detailed summary here]
        
        ## Key Takeaways
        - **[Category]**: [Takeaway 1]
        - [Takeaway 2]
        - **[Another Category]**: [Takeaway 3]
        ...
        
        ## Action Items
        1. [Action item 1] (Owner: [Name], Deadline: [Date])
        2. [Action item 2] (Owner: [Name])
        ...
        
        ## Decisions Made
        1. [Decision 1] - [Context/reasoning]
        2. [Decision 2] - [Context/reasoning]
        ...
        
        ## Participants
        - [Participant 1] ([Role if known])
        - [Participant 2]
        ...
        
        TRANSCRIPT:
        {transcript}
        """
    
    return prompt


def extract_participant_names(transcript):
    """
    Extract potential participant names from the transcript.
    
    Args:
        transcript (str): The meeting transcript
        
    Returns:
        list: List of potential participant names
    """
    # Simple pattern to find names at the beginning of lines (common in transcripts)
    name_pattern = r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?):' 
    
    # Find all matches
    matches = re.findall(name_pattern, transcript, re.MULTILINE)
    
    # Return unique names
    return list(set(matches))


def parse_bedrock_response(response_text):
    """
    Parse the response from AWS Bedrock to extract summary, key points, action items, and decisions.
    
    Args:
        response_text (str): The raw response from the Bedrock model
        
    Returns:
        tuple: (summary, key_points, action_items)
    """
    # Default values
    summary = ""
    key_points = []
    action_items = []
    decisions = []
    
    # Try to extract sections based on markdown headings
    sections = {}
    current_section = None
    current_content = []
    
    for line in response_text.split('\n'):
        # Check if this is a heading
        if re.match(r'^#+\s+', line):
            # Save previous section if it exists
            if current_section and current_content:
                sections[current_section.lower()] = '\n'.join(current_content).strip()
                current_content = []
            
            # Extract new section name
            current_section = re.sub(r'^#+\s+', '', line).strip()
        elif current_section:
            # Add content to current section
            current_content.append(line)
    
    # Save the last section
    if current_section and current_content:
        sections[current_section.lower()] = '\n'.join(current_content).strip()
    
    # Extract summary
    for key in ['summary', 'meeting summary']:
        if key in sections:
            summary = sections[key]
            break
    
    # Extract key points
    for key in ['key takeaways', 'takeaways', 'key points']:
        if key in sections:
            # First check for subsections (categories)
            subsections = {}
            current_subsection = "General"
            current_content = []
            
            # Split the section by lines
            for line in sections[key].split('\n'):
                # Check if this is a subheading (e.g., "Infrastructure State:")
                if re.match(r'^[A-Za-z\s]+:', line.strip()):
                    # Save previous subsection if it exists
                    if current_content:
                        subsections[current_subsection] = '\n'.join(current_content).strip()
                        current_content = []
                    
                    # Extract new subsection name
                    current_subsection = line.strip()
                else:
                    # Add content to current subsection
                    current_content.append(line)
            
            # Save the last subsection
            if current_content:
                subsections[current_subsection] = '\n'.join(current_content).strip()
            
            # Process each subsection
            for subsection, content in subsections.items():
                # Extract bullet points
                points = re.findall(r'[-•*]\s+(.*?)(?=\n[-•*]|\n\n|$)', content, re.DOTALL)
                if points:
                    # If it's not the general section, prefix with the category
                    if subsection != "General":
                        key_points.extend([f"**{subsection.rstrip(':')}**: {p.strip()}" for p in points])
                    else:
                        key_points.extend([p.strip() for p in points])
            
            # If no subsections were found, fall back to the original method
            if not key_points:
                points = re.findall(r'[-•*]\s+(.*?)(?=\n[-•*]|\n\n|$)', sections[key], re.DOTALL)
                if points:
                    key_points = [p.strip() for p in points]
            
            break
    
    # Extract action items
    for key in ['action items', 'next steps', 'actions', 'tasks']:
        if key in sections:
            # First check for subsections (categories)
            subsections = {}
            current_subsection = "General"
            current_content = []
            
            # Split the section by lines
            for line in sections[key].split('\n'):
                # Check if this is a subheading (e.g., "Technical Assessment:")
                if re.match(r'^[A-Za-z\s]+:', line.strip()):
                    # Save previous subsection if it exists
                    if current_content:
                        subsections[current_subsection] = '\n'.join(current_content).strip()
                        current_content = []
                    
                    # Extract new subsection name
                    current_subsection = line.strip()
                else:
                    # Add content to current subsection
                    current_content.append(line)
            
            # Save the last subsection
            if current_content:
                subsections[current_subsection] = '\n'.join(current_content).strip()
            
            # Process each subsection
            for subsection, content in subsections.items():
                # Extract bullet or numbered points with owners
                items = re.findall(r'(?:[-•*]|\d+\.)\s+(.*?)(?=\n(?:[-•*]|\d+\.|\n)|$)', content, re.DOTALL)
                if items:
                    # If it's not the general section, prefix with the category
                    if subsection != "General":
                        action_items.extend([f"**{subsection.rstrip(':')}**: {item.strip()}" for item in items])
                    else:
                        action_items.extend([item.strip() for item in items])
            
            # If no subsections were found, fall back to the original method
            if not action_items:
                items = re.findall(r'(?:[-•*]|\d+\.)\s+(.*?)(?=\n(?:[-•*]|\d+\.|\n)|$)', sections[key], re.DOTALL)
                if items:
                    action_items = [item.strip() for item in items]
            
            break
    
    # Extract decisions
    for key in ['decisions', 'decisions made', 'key decisions']:
        if key in sections:
            # Extract bullet or numbered points for decisions
            decision_items = re.findall(r'(?:[-•*]|\d+\.)\s+(.*?)(?=\n(?:[-•*]|\d+\.|\n)|$)', sections[key], re.DOTALL)
            if decision_items:
                decisions = [item.strip() for item in decision_items]
                # Add decisions to key points with a special prefix
                for decision in decisions:
                    key_points.append(f"**Decision**: {decision}")
                break
    
    # If we couldn't extract structured data, use heuristics
    if not summary and not key_points and not action_items:
        # Just use the first paragraph as summary
        paragraphs = [p for p in response_text.split('\n\n') if p.strip()]
        if paragraphs:
            summary = paragraphs[0]
        
        # Look for bullet points anywhere in the text
        all_bullets = re.findall(r'[-•*]\s+(.*?)(?=\n[-•*]|\n\n|$)', response_text, re.DOTALL)
        if all_bullets:
            # Assign first bullets to key points, rest to action items
            split_point = min(7, len(all_bullets))
            key_points = [b.strip() for b in all_bullets[:split_point]]
            action_items = [b.strip() for b in all_bullets[split_point:split_point+5]]
    
    # Process action items to ensure owner information is properly formatted
    processed_action_items = []
    for item in action_items:
        # Check if the item has owner information in parentheses
        owner_match = re.search(r'\(Owner:\s*([^,)]+)(?:,\s*Deadline:\s*([^)]+))?\)', item)
        if owner_match:
            # Extract the action text without the owner info
            action_text = re.sub(r'\s*\(Owner:.*?\)', '', item).strip()
            owner = owner_match.group(1).strip()
            deadline = owner_match.group(2).strip() if owner_match.group(2) else None
            
            # Format with owner and optional deadline
            if deadline:
                processed_action_items.append(f"{action_text} (Owner: {owner}, Deadline: {deadline})")
            else:
                processed_action_items.append(f"{action_text} (Owner: {owner})")
        else:
            processed_action_items.append(item)
    
    # Replace the original action items with processed ones
    if processed_action_items:
        action_items = processed_action_items
    
    return summary, key_points, action_items