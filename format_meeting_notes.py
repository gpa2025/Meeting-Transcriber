"""
Module for formatting meeting notes with enhanced detail.

This module provides functions to format meeting notes in a structured way,
with comprehensive summaries, key takeaways, action items with owners,
and participant information.
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def format_enhanced_meeting_notes(
    transcript: str,
    summary: str,
    key_points: List[str],
    action_items: List[str] = None,
    participants: List[Dict[str, str]] = None,
    has_speaker_segments: bool = False,
    meeting_date: Optional[datetime] = None
) -> str:
    """
    Format meeting notes in a detailed, structured format.
    
    Args:
        transcript (str): Original transcript
        summary (str): Generated summary
        key_points (list): List of key points
        action_items (list, optional): List of action items
        participants (list, optional): List of identified participants
        has_speaker_segments (bool): Whether the transcript includes speaker segments
        meeting_date (datetime, optional): Date of the meeting
        
    Returns:
        str: Formatted meeting notes in markdown format
    """
    # Get current date for the notes if not provided
    if meeting_date is None:
        meeting_date = datetime.now()
    
    date_str = meeting_date.strftime("%B %d, %Y")
    
    # Format the notes with a more professional header
    notes = f"# Meeting Notes - {date_str}\n\n"
    
    # Add summary section
    notes += "## Summary\n\n"
    notes += f"{summary}\n\n"
    
    # Process key points to identify categories
    categorized_points = {}
    uncategorized_points = []
    
    for point in key_points:
        # Check if the point has a category prefix (e.g., "**Category**:" or "Category:")
        category_match = re.match(r'\*\*([^*]+)\*\*:\s*(.*)', point) or re.match(r'([A-Za-z]+):\s*(.*)', point)
        if category_match:
            category = category_match.group(1).strip()
            content = category_match.group(2).strip()
            
            if category not in categorized_points:
                categorized_points[category] = []
            
            categorized_points[category].append(content)
        else:
            uncategorized_points.append(point)
    
    # Add key takeaways section with categories if available
    notes += "## Key Takeaways\n\n"
    
    if categorized_points:
        # Add categorized points
        for category, points in categorized_points.items():
            notes += f"### {category}\n\n"
            for point in points:
                notes += f"- {point}\n"
            notes += "\n"
        
        # Add uncategorized points if any
        if uncategorized_points:
            notes += "### Additional Points\n\n"
            for point in uncategorized_points:
                notes += f"- {point}\n"
            notes += "\n"
    else:
        # No categories, just list all points
        for point in key_points:
            notes += f"- {point}\n"
        notes += "\n"
    
    # Extract decisions from key points and summary
    decisions = extract_decisions(key_points, summary)
    if decisions:
        notes += "## Decisions Made\n\n"
        for i, decision in enumerate(decisions, 1):
            notes += f"{i}. {decision}\n"
        notes += "\n"
    
    # Add action items if available
    if action_items and len(action_items) > 0:
        notes += "## Action Items\n\n"
        
        # Process action items to extract owners and deadlines
        processed_items = []
        for i, item in enumerate(action_items, 1):
            # Check for owner and deadline information
            owner_deadline_match = re.search(r'\(Owner:\s*([^,)]+)(?:,\s*Deadline:\s*([^)]+))?\)', item)
            owner_match = re.search(r'\(Owner:\s*([^)]+)\)', item)
            
            if owner_deadline_match:
                # Item has owner and possibly deadline
                action_text = re.sub(r'\s*\(Owner:.*?\)', '', item).strip()
                owner = owner_deadline_match.group(1).strip()
                deadline = owner_deadline_match.group(2).strip() if owner_deadline_match.group(2) else None
                
                if deadline:
                    processed_items.append(f"{i}. {action_text} **[Owner: {owner}, Deadline: {deadline}]**")
                else:
                    processed_items.append(f"{i}. {action_text} **[Owner: {owner}]**")
            elif owner_match:
                # Item has just an owner
                action_text = re.sub(r'\s*\(Owner:.*?\)', '', item).strip()
                owner = owner_match.group(1).strip()
                processed_items.append(f"{i}. {action_text} **[Owner: {owner}]**")
            else:
                # Try to infer an owner from the content
                owner = infer_owner_from_text(item, participants)
                if owner:
                    processed_items.append(f"{i}. {item} **[Owner: {owner}]**")
                else:
                    processed_items.append(f"{i}. {item}")
        
        # Add processed items to notes
        for item in processed_items:
            notes += f"{item}\n"
        notes += "\n"
    
    # Add participants if identified
    if participants and len(participants) > 0:
        notes += "## Participants\n\n"
        for participant in participants:
            # Add role or organization if available
            name = participant.get('name', participant.get('id', 'Unknown'))
            role = participant.get('role', '')
            org = participant.get('organization', '')
            
            if role and org:
                notes += f"- {name} ({role}, {org})\n"
            elif role:
                notes += f"- {name} ({role})\n"
            elif org:
                notes += f"- {name} ({org})\n"
            else:
                notes += f"- {name}\n"
        notes += "\n"
    
    # Add link to full transcript
    notes += "## Full Transcript\n\n"
    
    if has_speaker_segments:
        notes += "The full transcript with speaker identification is available in the attached file.\n"
    else:
        notes += "The full transcript is available in the attached file.\n"
    
    return notes


def extract_decisions(key_points: List[str], summary: str) -> List[str]:
    """
    Extract decisions from key points and summary.
    
    Args:
        key_points (List[str]): List of key points
        summary (str): Meeting summary
        
    Returns:
        List[str]: List of extracted decisions
    """
    decisions = []
    
    # Look for decision markers in key points
    for point in key_points:
        if "decision" in point.lower() or "decided" in point.lower() or "agreed" in point.lower():
            # Check if this is already marked as a decision
            if point.lower().startswith("**decision"):
                # Extract the actual decision text
                decision_text = re.sub(r'^\*\*Decision\*\*:\s*', '', point, flags=re.IGNORECASE)
                decisions.append(decision_text)
            else:
                decisions.append(point)
    
    # If we didn't find enough decisions, look in the summary
    if len(decisions) < 2:
        # Split summary into sentences
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        
        # Look for decision indicators in sentences
        decision_indicators = ["decided", "agreed", "concluded", "determined", "resolved", "approved", "finalized"]
        
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in decision_indicators):
                if sentence not in decisions:
                    decisions.append(sentence)
    
    # Limit to top 5 decisions
    return decisions[:5]


def infer_owner_from_text(text: str, participants: List[Dict[str, str]]) -> Optional[str]:
    """
    Try to infer the owner of an action item from its text.
    
    Args:
        text (str): The action item text
        participants (list): List of participants
        
    Returns:
        str or None: The inferred owner name or None if no owner could be inferred
    """
    if not participants:
        return None
    
    # Get list of participant names
    participant_names = [p.get('name', p.get('id', '')) for p in participants if p.get('name') or p.get('id')]
    
    # Common patterns that indicate ownership
    ownership_patterns = [
        r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?) (?:will|should|needs to|is going to|has to)',  # Name will/should/needs to
        r'(?:assigned to|owned by|responsibility of) ([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)',  # assigned to Name
    ]
    
    # Check for ownership patterns
    for pattern in ownership_patterns:
        match = re.search(pattern, text)
        if match:
            potential_owner = match.group(1)
            # Check if this matches a participant
            for name in participant_names:
                if potential_owner.lower() in name.lower() or name.lower() in potential_owner.lower():
                    return name
    
    # Check if any participant name is mentioned in the text
    for name in participant_names:
        if name in text:
            return name
    
    return None