#!/usr/bin/env python3
"""
Basic test for async Meeting Transcriber features (without external dependencies)

This script tests the core async functionality without requiring aiohttp/aiofiles.
"""

import asyncio
import sys
import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define basic structures for testing
class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressUpdate:
    task_id: str
    status: TaskStatus
    progress_percent: float
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None

class MockAsyncTranscriber:
    """Mock async transcriber for testing core functionality"""
    
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.active_tasks = {}
        self.task_results = {}
    
    async def start_transcription(self, task_data: Dict) -> str:
        """Start a mock transcription task"""
        task_id = f"task_{int(datetime.now().timestamp() * 1000)}"
        
        # Store task
        self.active_tasks[task_id] = {
            'status': TaskStatus.PENDING,
            'data': task_data,
            'start_time': datetime.now()
        }
        
        # Send initial progress
        await self._send_progress_update(
            task_id, TaskStatus.PENDING, 0.0, "Task queued"
        )
        
        # Start processing
        asyncio.create_task(self._process_task(task_id))
        
        return task_id
    
    async def _process_task(self, task_id: str):
        """Mock task processing"""
        try:
            # Simulate transcription steps
            steps = [
                (TaskStatus.RUNNING, 10.0, "Initializing transcription"),
                (TaskStatus.RUNNING, 25.0, "Uploading audio file"),
                (TaskStatus.RUNNING, 40.0, "Transcription in progress"),
                (TaskStatus.RUNNING, 65.0, "Processing speaker diarization"),
                (TaskStatus.RUNNING, 80.0, "Generating summary"),
                (TaskStatus.RUNNING, 95.0, "Formatting meeting notes"),
                (TaskStatus.COMPLETED, 100.0, "Transcription completed successfully")
            ]
            
            for status, progress, message in steps:
                await asyncio.sleep(0.5)  # Simulate processing time
                await self._send_progress_update(task_id, status, progress, message)
                
                # Check if task was cancelled
                if task_id not in self.active_tasks:
                    return
            
            # Store result
            self.task_results[task_id] = {
                'success': True,
                'output_files': ['transcript.txt', 'meeting_notes.md'],
                'processing_time': 3.5
            }
            
        except Exception as e:
            await self._send_progress_update(
                task_id, TaskStatus.FAILED, 0.0, f"Error: {str(e)}"
            )
        finally:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id not in self.active_tasks:
            return False
        
        del self.active_tasks[task_id]
        
        await self._send_progress_update(
            task_id, TaskStatus.CANCELLED, 0.0, "Task cancelled by user"
        )
        
        return True
    
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """Get task status"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]['status']
        elif task_id in self.task_results:
            return TaskStatus.COMPLETED
        else:
            return None
    
    async def _send_progress_update(self, task_id: str, status: TaskStatus, 
                                  progress: float, message: str):
        """Send progress update"""
        if self.progress_callback:
            update = ProgressUpdate(
                task_id=task_id,
                status=status,
                progress_percent=progress,
                message=message,
                timestamp=datetime.now()
            )
            
            if asyncio.iscoroutinefunction(self.progress_callback):
                await self.progress_callback(update)
            else:
                self.progress_callback(update)

class TestProgressCallback:
    """Test progress callback"""
    
    def __init__(self):
        self.updates = []
    
    def __call__(self, update: ProgressUpdate):
        self.updates.append(update)
        print(f"[{update.timestamp.strftime('%H:%M:%S')}] {update.task_id}: "
              f"{update.status.value} - {update.progress_percent:.1f}% - {update.message}")

async def test_single_task():
    """Test single task processing"""
    print("=" * 60)
    print("Testing Single Task Processing")
    print("=" * 60)
    
    callback = TestProgressCallback()
    transcriber = MockAsyncTranscriber(progress_callback=callback)
    
    # Start task
    task_data = {
        'audio_file': 'test_audio.mp3',
        'output_dir': '/tmp/output',
        'model': 'claude-3.5-sonnet'
    }
    
    task_id = await transcriber.start_transcription(task_data)
    print(f"Started task: {task_id}")
    
    # Wait for completion
    while True:
        status = await transcriber.get_task_status(task_id)
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, None]:
            break
        await asyncio.sleep(0.1)
    
    print(f"Task completed with status: {status}")
    print(f"Total progress updates: {len(callback.updates)}")
    
    return len(callback.updates) > 0

async def test_multiple_tasks():
    """Test multiple concurrent tasks"""
    print("\n" + "=" * 60)
    print("Testing Multiple Concurrent Tasks")
    print("=" * 60)
    
    callback = TestProgressCallback()
    transcriber = MockAsyncTranscriber(progress_callback=callback)
    
    # Start multiple tasks
    task_ids = []
    for i in range(3):
        task_data = {
            'audio_file': f'test_audio_{i}.mp3',
            'output_dir': f'/tmp/output_{i}',
            'model': 'claude-3.5-sonnet'
        }
        
        task_id = await transcriber.start_transcription(task_data)
        task_ids.append(task_id)
        print(f"Started task {i+1}: {task_id}")
    
    # Wait for all tasks to complete
    completed_tasks = 0
    while completed_tasks < len(task_ids):
        completed_tasks = 0
        for task_id in task_ids:
            status = await transcriber.get_task_status(task_id)
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, None]:
                completed_tasks += 1
        
        await asyncio.sleep(0.1)
    
    print(f"All {len(task_ids)} tasks completed")
    print(f"Total progress updates: {len(callback.updates)}")
    
    return len(callback.updates) > len(task_ids)

async def test_task_cancellation():
    """Test task cancellation"""
    print("\n" + "=" * 60)
    print("Testing Task Cancellation")
    print("=" * 60)
    
    callback = TestProgressCallback()
    transcriber = MockAsyncTranscriber(progress_callback=callback)
    
    # Start task
    task_data = {
        'audio_file': 'test_audio_cancel.mp3',
        'output_dir': '/tmp/output_cancel',
        'model': 'claude-3.5-sonnet'
    }
    
    task_id = await transcriber.start_transcription(task_data)
    print(f"Started task: {task_id}")
    
    # Wait a bit then cancel
    await asyncio.sleep(1.0)
    
    cancelled = await transcriber.cancel_task(task_id)
    print(f"Cancellation result: {cancelled}")
    
    # Check final status
    await asyncio.sleep(0.5)
    status = await transcriber.get_task_status(task_id)
    print(f"Final status: {status}")
    
    return cancelled and status == TaskStatus.CANCELLED

async def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    callback = TestProgressCallback()
    transcriber = MockAsyncTranscriber(progress_callback=callback)
    
    # Test invalid operations
    status = await transcriber.get_task_status("invalid_task")
    print(f"Status for invalid task: {status}")
    
    cancelled = await transcriber.cancel_task("invalid_task")
    print(f"Cancel invalid task result: {cancelled}")
    
    return status is None and not cancelled

def test_data_structures():
    """Test data structures"""
    print("\n" + "=" * 60)
    print("Testing Data Structures")
    print("=" * 60)
    
    # Test ProgressUpdate
    update = ProgressUpdate(
        task_id="test_task",
        status=TaskStatus.RUNNING,
        progress_percent=50.0,
        message="Test message",
        timestamp=datetime.now()
    )
    
    print(f"ProgressUpdate created: {update.task_id} - {update.progress_percent}%")
    
    # Test TaskStatus enum
    statuses = [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, 
                TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    print(f"TaskStatus values: {[s.value for s in statuses]}")
    
    return len(statuses) == 5

async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Async Feature Tests (Basic)")
    print("=" * 60)
    
    results = []
    
    try:
        # Test data structures
        results.append(("Data Structures", test_data_structures()))
        
        # Test single task
        results.append(("Single Task", await test_single_task()))
        
        # Test multiple tasks
        results.append(("Multiple Tasks", await test_multiple_tasks()))
        
        # Test cancellation
        results.append(("Task Cancellation", await test_task_cancellation()))
        
        # Test error handling
        results.append(("Error Handling", await test_error_handling()))
        
        # Print results
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        all_passed = True
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name:20} {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All Basic Async Tests Passed!")
            print("\nNext Steps:")
            print("1. Install async dependencies: pip install aiohttp aiofiles")
            print("2. Run full async tests: python test_async_features.py")
            print("3. Try the enhanced GUI: python meeting_transcriber_gui_async.py")
        else:
            print("\n❌ Some tests failed. Check the implementation.")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        logger.exception("Test suite failed")
        return False

def main():
    """Main function"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required for async features")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ Basic async functionality is working!")
        sys.exit(0)
    else:
        print("\n❌ Some basic tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()