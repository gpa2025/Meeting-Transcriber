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
Version: 1.1
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
                                     'You are an AI assistant that creates extremely detailed and comprehensive meeting notes from transcripts.')
        
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
        
            1. A comprehensive summary of the meeting (4-6 paragraphs) that captures:
                - The main purpose and objectives of the meeting
                - Key topics discussed with ALL specific details, numbers, metrics, and technical specifications mentioned
                - Current infrastructure details with EXACT versions, configurations, costs, and technical parameters
                - Business context including company history, business type, seasonal patterns, and market position
                - Customer's current challenges, pain points, and technical constraints
                - Any decisions made or conclusions reached with their rationale
                - Future plans, timelines, and strategic directions discussed
                
            2. A list of at least 15-20 key takeaways as bullet points that highlight:
                - ALL important facts or insights with specific details and metrics
                - ALL technical details mentioned with version numbers, specifications, and configurations
                - ALL business requirements or constraints with deadlines and dependencies
                - ALL current state assessments with metrics, costs, and performance indicators
                - ALL future state recommendations with benefits and implementation considerations
                - Group these by topic with clear headings (e.g., "Infrastructure State:", "Modernization Opportunities:", 
                  "Timing Constraints:", "Cost Analysis:", "Technical Requirements:", "Business Constraints:")
                
            3. A detailed list of next steps with assigned owners where possible:
                - Be extremely specific about what needs to be done with technical details
                - Include ALL deadlines, milestones, and dependencies if mentioned
                - Assign owners based on who committed to tasks or who has the relevant expertise
                - Group these by category (e.g., "Licensing Verification:", "Technical Assessment:", 
                  "Architecture Planning:", "Partner Coordination:", "Implementation Steps:")
                - Format as "Task description (Owner: Person's name, Deadline: [date if mentioned])"
                - Include follow-up meetings and check-ins with dates if mentioned
                
            4. A separate section for decisions made during the meeting:
                - List ALL key decisions that were finalized with their complete context
                - Include the context, alternatives considered, and reasoning behind each decision
                - Note any conditions, constraints, or dependencies related to each decision
                - Indicate who approved or supported each decision if mentioned
                
            5. Technical details section:
                - Extract ALL technical specifications, versions, configurations mentioned
                - Include ALL architecture details, system components, and integration points
                - Document ALL performance metrics, capacity requirements, and scaling considerations
                - List ALL tools, platforms, and technologies discussed with version information
                
            6. Cost and resource considerations:
                - Document ALL cost figures, budget constraints, and financial considerations
                - Include ALL resource requirements (people, time, infrastructure)
                - Note ALL potential cost savings, ROI calculations, or financial benefits mentioned
                - Capture ALL licensing, subscription, or procurement requirements
                
            7. Risk and issues:
                - Identify ALL risks, challenges, or concerns raised during the meeting
                - Document ALL mitigation strategies or contingency plans discussed
                - Note ALL dependencies, blockers, or constraints that might impact progress
                - Include ALL compliance, security, or governance considerations
                
            8. List of participants in the meeting with their roles if mentioned
                
            Meeting participants appear to include: {participants_str}
                
            Format your response with clear headings for each section. Make the notes professional, actionable, and EXTREMELY DETAILED with specific information from the transcript. Extract EVERY piece of specific information including numbers, dates, technical details, costs, and business context.
            
            DO NOT OMIT ANY DETAILS from the transcript. Include ALL specific information about:
            - Current environment (all services, versions, configurations)
            - Database details (versions, editions, utilization, performance)
            - Cost information (current spend, potential savings, budget constraints)
            - Business context (company type, seasonal nature, market position)
            - Technical challenges and modernization opportunities with specific solutions
            - Timeline constraints (all deadlines and milestones)
            - Security, compliance, and governance requirements
            - Integration points and dependencies with other systems
                
            Here's the transcript:
                
            {transcript}
                
            Assistant:"""
    else:
        # Generic prompt format for other models
        prompt = f"""{system_prompt}
        
        TASK: Analyze the following meeting transcript and create EXTREMELY DETAILED and COMPREHENSIVE meeting notes that include:
        
        1. SUMMARY (4-6 paragraphs):
           - Main purpose and objectives of the meeting
           - Key topics discussed with ALL specific details
           - Business context and background with metrics
           - Technical details with exact specifications
           - Decisions or conclusions with rationale
           - Future plans and strategic directions
        
        2. KEY TAKEAWAYS (15-20 bullet points):
           - Important facts or insights with specific metrics
           - Technical details with version numbers and specifications
           - Business requirements with deadlines and dependencies
           - Current state assessments with performance indicators
           - Future state recommendations with benefits
           - Categorize by topic (e.g., "Technical:", "Business:", "Timeline:")
        
        3. ACTION ITEMS (with owners and deadlines):
           - Specific tasks with technical details
           - Include ALL deadlines and dependencies
           - Assign owners based on discussion
           - Group by category (e.g., "Technical:", "Business:")
           - Format as "Task description (Owner: Person's name, Deadline: [date])"
        
        4. DECISIONS MADE:
           - List ALL key decisions with complete context
           - Include alternatives considered and reasoning
           - Note conditions and dependencies
           - Indicate approvers if mentioned
        
        5. TECHNICAL DETAILS:
           - ALL specifications, versions, configurations
           - Architecture details and system components
           - Performance metrics and capacity requirements
           - Tools and technologies with version information
        
        6. COST AND RESOURCE CONSIDERATIONS:
           - ALL cost figures and budget constraints
           - Resource requirements (people, time, infrastructure)
           - Potential savings and financial benefits
           - Licensing and procurement requirements
        
        7. RISKS AND ISSUES:
           - ALL challenges or concerns raised
           - Mitigation strategies discussed
           - Dependencies and blockers
           - Compliance and security considerations
        
        8. PARTICIPANTS:
           - List meeting attendees with roles if mentioned
        
        Meeting participants appear to include: {participants_str}
        
        FORMAT WITH CLEAR HEADINGS FOR EACH SECTION. Make the notes professional, actionable, and EXTREMELY DETAILED. Extract EVERY piece of specific information including numbers, dates, technical details, costs, and business context.
        
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
    technical_details = []
    cost_considerations = []
    risks_issues = []
    
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
                if re.match(r'^###\s+', line):
                    # Save previous subsection if it exists
                    if current_content:
                        subsections[current_subsection] = '\n'.join(current_content).strip()
                        current_content = []
                    
                    # Extract new subsection name
                    current_subsection = re.sub(r'^###\s+', '', line).strip()
                elif re.match(r'^[A-Za-z\s]+:', line.strip()):
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
                if re.match(r'^###\s+', line):
                    # Save previous subsection if it exists
                    if current_content:
                        subsections[current_subsection] = '\n'.join(current_content).strip()
                        current_content = []
                    
                    # Extract new subsection name
                    current_subsection = re.sub(r'^###\s+', '', line).strip()
                elif re.match(r'^[A-Za-z\s]+:', line.strip()):
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
                decisions = [f"**Decision**: {item.strip()}" for item in decision_items]
                # Add decisions to key points
                key_points.extend(decisions)
                break
    
    # Extract technical details
    for key in ['technical details', 'technical specifications', 'technical information']:
        if key in sections:
            tech_items = re.findall(r'(?:[-•*]|\d+\.)\s+(.*?)(?=\n(?:[-•*]|\d+\.|\n)|$)', sections[key], re.DOTALL)
            if tech_items:
                technical_details = [f"**Technical**: {item.strip()}" for item in tech_items]
                # Add technical details to key points
                key_points.extend(technical_details)
                break
    
    # Extract cost considerations
    for key in ['cost', 'cost and resource considerations', 'financial considerations']:
        if key in sections:
            cost_items = re.findall(r'(?:[-•*]|\d+\.)\s+(.*?)(?=\n(?:[-•*]|\d+\.|\n)|$)', sections[key], re.DOTALL)
            if cost_items:
                cost_considerations = [f"**Cost**: {item.strip()}" for item in cost_items]
                # Add cost considerations to key points
                key_points.extend(cost_considerations)
                break
    
    # Extract risks and issues
    for key in ['risks', 'risks and issues', 'challenges', 'concerns']:
        if key in sections:
            risk_items = re.findall(r'(?:[-•*]|\d+\.)\s+(.*?)(?=\n(?:[-•*]|\d+\.|\n)|$)', sections[key], re.DOTALL)
            if risk_items:
                risks_issues = [f"**Risk**: {item.strip()}" for item in risk_items]
                # Add risks and issues to key points
                key_points.extend(risks_issues)
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
            split_point = min(10, len(all_bullets))
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