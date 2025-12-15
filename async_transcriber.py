"""
Async Meeting Transcriber Core Module

This module provides asynchronous processing capabilities for the Meeting Transcriber,
including non-blocking transcription, real-time progress updates, and cancellation support.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 12-15-2025
Version: 1.1
Assisted by: Amazon Q for VS Code
"""

import asyncio
import aiohttp
import aiofiles
import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status enumeration for async tasks"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    task_id: str
    status: TaskStatus
    progress_percent: float
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

@dataclass
class TranscriptionTask:
    """Transcription task data structure"""
    task_id: str
    audio_file: str
    output_dir: str
    aws_credentials: Dict[str, str]
    aws_settings: Dict[str, str]
    skip_transcription: bool = False
    transcript_file: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class AsyncTranscriber:
    """
    Async transcription manager with progress tracking and cancellation support
    """
    
    def __init__(self, progress_callback: Optional[Callable[[ProgressUpdate], None]] = None):
        self.progress_callback = progress_callback
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._shutdown = False
        
    async def start_transcription(self, task: TranscriptionTask) -> str:
        """
        Start an async transcription task
        
        Args:
            task: TranscriptionTask object with all necessary parameters
            
        Returns:
            str: Task ID for tracking
        """
        logger.info(f"Starting async transcription task: {task.task_id}")
        
        # Create async task
        async_task = asyncio.create_task(
            self._process_transcription_async(task)
        )
        
        # Store task reference
        self.active_tasks[task.task_id] = async_task
        
        # Send initial progress update
        await self._send_progress_update(
            task.task_id,
            TaskStatus.PENDING,
            0.0,
            "Transcription task queued"
        )
        
        return task.task_id
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running transcription task
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            bool: True if task was cancelled, False if not found or already completed
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found for cancellation")
            return False
            
        task = self.active_tasks[task_id]
        if task.done():
            logger.info(f"Task {task_id} already completed, cannot cancel")
            return False
            
        logger.info(f"Cancelling task: {task_id}")
        task.cancel()
        
        await self._send_progress_update(
            task_id,
            TaskStatus.CANCELLED,
            0.0,
            "Task cancelled by user"
        )
        
        return True
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the current status of a task"""
        if task_id not in self.active_tasks:
            return None
            
        task = self.active_tasks[task_id]
        if task.cancelled():
            return TaskStatus.CANCELLED
        elif task.done():
            if task.exception():
                return TaskStatus.FAILED
            else:
                return TaskStatus.COMPLETED
        else:
            return TaskStatus.RUNNING
    
    async def wait_for_task(self, task_id: str) -> Any:
        """Wait for a specific task to complete and return its result"""
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")
            
        task = self.active_tasks[task_id]
        try:
            result = await task
            return result
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            raise
    
    async def _process_transcription_async(self, task: TranscriptionTask) -> Dict[str, Any]:
        """
        Main async transcription processing method
        """
        try:
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                5.0,
                "Initializing transcription process"
            )
            
            # Set up environment variables
            await self._setup_environment(task)
            
            # Create output directory
            os.makedirs(task.output_dir, exist_ok=True)
            output_dir = os.path.abspath(task.output_dir)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                10.0,
                f"Using output directory: {output_dir}"
            )
            
            # Get base filename
            base_filename = os.path.splitext(os.path.basename(task.audio_file))[0]
            
            # Get meeting date from file
            meeting_date = await self._get_file_date_async(task.audio_file)
            
            # Step 1: Transcription
            transcript = None
            if task.skip_transcription and task.transcript_file:
                await self._send_progress_update(
                    task.task_id,
                    TaskStatus.RUNNING,
                    30.0,
                    "Loading existing transcript"
                )
                transcript = await self._load_transcript_async(task.transcript_file)
            else:
                await self._send_progress_update(
                    task.task_id,
                    TaskStatus.RUNNING,
                    15.0,
                    "Starting audio transcription"
                )
                transcript = await self._transcribe_audio_async(task)
                
                # Save transcript files
                await self._save_transcript_files(task, transcript, base_filename)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                60.0,
                "Transcription completed, starting summarization"
            )
            
            # Step 2: Summarization
            summary_result = await self._generate_summary_async(task, transcript)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                85.0,
                "Generating meeting notes"
            )
            
            # Step 3: Format and save meeting notes
            meeting_notes = await self._format_meeting_notes_async(
                task, transcript, summary_result, meeting_date
            )
            
            notes_file = os.path.join(output_dir, f"{base_filename}_meeting_notes.md")
            await self._save_file_async(meeting_notes, notes_file)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                95.0,
                f"Meeting notes saved to {notes_file}"
            )
            
            # Step 4: Open output directory
            await self._open_output_directory_async(output_dir)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.COMPLETED,
                100.0,
                "Transcription and summarization completed successfully!"
            )
            
            # Prepare result
            result = {
                'success': True,
                'output_dir': output_dir,
                'notes_file': notes_file,
                'transcript': transcript,
                'summary': summary_result,
                'meeting_date': meeting_date
            }
            
            # Store result
            self.task_results[task.task_id] = result
            
            return result
            
        except asyncio.CancelledError:
            await self._send_progress_update(
                task.task_id,
                TaskStatus.CANCELLED,
                0.0,
                "Task was cancelled"
            )
            raise
        except Exception as e:
            logger.error(f"Transcription task {task.task_id} failed: {e}")
            await self._send_progress_update(
                task.task_id,
                TaskStatus.FAILED,
                0.0,
                f"Error: {str(e)}"
            )
            raise
        finally:
            # Clean up task reference
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def _setup_environment(self, task: TranscriptionTask):
        """Set up environment variables for the task"""
        model_id = task.aws_settings["model_id"]
        is_free_model = model_id.startswith(('ollama:', 'hf:', 'openai-free:'))
        
        if is_free_model:
            os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
            os.environ["AWS_REGION"] = "us-east-1"
            os.environ["AWS_S3_BUCKET"] = "dummy"
        else:
            os.environ["AWS_ACCESS_KEY_ID"] = task.aws_credentials["access_key"].strip()
            os.environ["AWS_SECRET_ACCESS_KEY"] = task.aws_credentials["secret_key"].strip()
            os.environ["AWS_REGION"] = task.aws_credentials["region"].strip()
            os.environ["AWS_S3_BUCKET"] = task.aws_credentials["s3_bucket"].strip()
        
        # Set other environment variables
        for key, value in task.aws_settings.items():
            env_key = key.upper()
            if env_key == "MODEL_ID":
                os.environ["BEDROCK_MODEL_ID"] = value
            else:
                os.environ[env_key] = str(value)
    
    async def _get_file_date_async(self, audio_file: str) -> datetime:
        """Get file modification date asynchronously"""
        loop = asyncio.get_event_loop()
        
        def get_file_date():
            try:
                if os.path.exists(audio_file):
                    import sys
                    if sys.platform == 'win32':
                        file_time = os.path.getctime(audio_file)
                    else:
                        file_time = os.path.getmtime(audio_file)
                    return datetime.fromtimestamp(file_time)
                else:
                    return datetime.now()
            except Exception:
                return datetime.now()
        
        return await loop.run_in_executor(self.executor, get_file_date)
    
    async def _transcribe_audio_async(self, task: TranscriptionTask) -> Any:
        """Transcribe audio asynchronously with progress updates"""
        # Import transcription module
        import aws_transcribe
        
        # Run transcription in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Create a wrapper that provides progress updates
        async def transcribe_with_progress():
            # Start transcription in thread pool
            transcription_future = loop.run_in_executor(
                self.executor,
                aws_transcribe.transcribe_with_aws,
                task.audio_file
            )
            
            # Simulate progress updates while waiting
            progress = 15.0
            while not transcription_future.done():
                await asyncio.sleep(5)  # Check every 5 seconds
                progress = min(progress + 5, 55)  # Increment progress up to 55%
                await self._send_progress_update(
                    task.task_id,
                    TaskStatus.RUNNING,
                    progress,
                    "Transcription in progress..."
                )
            
            return await transcription_future
        
        return await transcribe_with_progress()
    
    async def _generate_summary_async(self, task: TranscriptionTask, transcript: Any) -> Tuple[str, List[str], List[str]]:
        """Generate summary asynchronously"""
        model_id = task.aws_settings["model_id"]
        is_free_model = model_id.startswith(('ollama:', 'hf:', 'openai-free:'))
        
        loop = asyncio.get_event_loop()
        
        if is_free_model:
            from summarizer_free import generate_notes_with_free_models
            return await loop.run_in_executor(
                self.executor,
                generate_notes_with_free_models,
                transcript['full_transcript'] if isinstance(transcript, dict) else transcript
            )
        else:
            from summarizer_bedrock import generate_notes_with_bedrock
            return await loop.run_in_executor(
                self.executor,
                generate_notes_with_bedrock,
                transcript['full_transcript'] if isinstance(transcript, dict) else transcript
            )
    
    async def _load_transcript_async(self, transcript_file: str) -> str:
        """Load existing transcript file asynchronously"""
        async with aiofiles.open(transcript_file, 'r', encoding='utf-8') as f:
            return await f.read()
    
    async def _save_file_async(self, content: str, file_path: str):
        """Save file asynchronously"""
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
    
    async def _save_transcript_files(self, task: TranscriptionTask, transcript: Any, base_filename: str):
        """Save transcript files asynchronously"""
        if isinstance(transcript, dict) and 'speaker_segments' in transcript:
            # Handle speaker diarization format
            transcript_file = os.path.join(task.output_dir, f"{base_filename}_transcript.txt")
            speaker_transcript_file = os.path.join(task.output_dir, f"{base_filename}_transcript_with_speakers.txt")
            
            # Save plain transcript
            await self._save_file_async(transcript['full_transcript'], transcript_file)
            
            # Save transcript with speaker labels
            speaker_text = ""
            for segment in transcript['speaker_segments']:
                speaker_text += f"{segment['speaker']}: {segment['text']}\n\n"
            await self._save_file_async(speaker_text, speaker_transcript_file)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                50.0,
                f"Transcript saved to {transcript_file}"
            )
        else:
            # Handle plain text transcript
            transcript_file = os.path.join(task.output_dir, f"{base_filename}_transcript.txt")
            await self._save_file_async(transcript, transcript_file)
            
            await self._send_progress_update(
                task.task_id,
                TaskStatus.RUNNING,
                50.0,
                f"Transcript saved to {transcript_file}"
            )
    
    async def _format_meeting_notes_async(self, task: TranscriptionTask, transcript: Any, 
                                        summary_result: Tuple[str, List[str], List[str]], 
                                        meeting_date: datetime) -> str:
        """Format meeting notes asynchronously"""
        import format_meeting_notes
        
        summary, key_points, action_items = summary_result
        
        # Extract participants if available
        participants = []
        if isinstance(transcript, dict) and 'speaker_segments' in transcript:
            speakers = set()
            for segment in transcript['speaker_segments']:
                speakers.add(segment['speaker'])
            
            for speaker in speakers:
                participants.append({
                    'id': speaker,
                    'name': f"Speaker {speaker.split('_')[-1]}" if speaker.startswith('spk_') else speaker
                })
        
        # Run formatting in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            format_meeting_notes.format_enhanced_meeting_notes,
            transcript['full_transcript'] if isinstance(transcript, dict) else transcript,
            summary,
            key_points,
            action_items,
            participants,
            isinstance(transcript, dict) and 'speaker_segments' in transcript,
            meeting_date
        )
    
    async def _open_output_directory_async(self, output_dir: str):
        """Open output directory asynchronously"""
        import subprocess
        import sys
        
        loop = asyncio.get_event_loop()
        
        def open_directory():
            try:
                normalized_output_dir = os.path.abspath(output_dir)
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', normalized_output_dir])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', normalized_output_dir])
                else:
                    subprocess.Popen(['xdg-open', normalized_output_dir])
            except Exception as e:
                logger.warning(f"Failed to open output directory: {e}")
        
        await loop.run_in_executor(self.executor, open_directory)
    
    async def _send_progress_update(self, task_id: str, status: TaskStatus, 
                                  progress: float, message: str, details: Optional[Dict] = None):
        """Send progress update to callback"""
        if self.progress_callback:
            update = ProgressUpdate(
                task_id=task_id,
                status=status,
                progress_percent=progress,
                message=message,
                timestamp=datetime.now(),
                details=details
            )
            
            # Call progress callback (handle both sync and async callbacks)
            if asyncio.iscoroutinefunction(self.progress_callback):
                await self.progress_callback(update)
            else:
                self.progress_callback(update)
    
    async def shutdown(self):
        """Shutdown the async transcriber and clean up resources"""
        logger.info("Shutting down async transcriber")
        self._shutdown = True
        
        # Cancel all active tasks
        for task_id, task in self.active_tasks.items():
            if not task.done():
                logger.info(f"Cancelling task {task_id} during shutdown")
                task.cancel()
        
        # Wait for all tasks to complete or be cancelled
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        logger.info("Async transcriber shutdown complete")

# Utility functions for creating tasks
def create_transcription_task(audio_file: str, output_dir: str, aws_credentials: Dict[str, str], 
                            aws_settings: Dict[str, str], skip_transcription: bool = False,
                            transcript_file: Optional[str] = None) -> TranscriptionTask:
    """Create a new transcription task with a unique ID"""
    task_id = f"transcribe_{int(time.time() * 1000)}"
    
    return TranscriptionTask(
        task_id=task_id,
        audio_file=audio_file,
        output_dir=output_dir,
        aws_credentials=aws_credentials,
        aws_settings=aws_settings,
        skip_transcription=skip_transcription,
        transcript_file=transcript_file
    )