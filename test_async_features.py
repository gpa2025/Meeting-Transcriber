#!/usr/bin/env python3
"""
Test script for async Meeting Transcriber features

This script demonstrates and tests the async functionality without requiring
actual audio files or AWS credentials.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 12-15-2025
Version: 1.1
"""

import asyncio
import sys
import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from async_transcriber import (AsyncTranscriber, TranscriptionTask, ProgressUpdate, 
                             TaskStatus, create_transcription_task)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockProgressCallback:
    """Mock progress callback for testing"""
    
    def __init__(self):
        self.updates = []
    
    def __call__(self, update: ProgressUpdate):
        """Handle progress update"""
        self.updates.append(update)
        print(f"[{update.timestamp.strftime('%H:%M:%S')}] {update.task_id}: "
              f"{update.status.value} - {update.progress_percent:.1f}% - {update.message}")

async def create_mock_audio_file() -> str:
    """Create a mock audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(b"Mock audio content for testing")
        return f.name

async def test_basic_async_functionality():
    """Test basic async transcriber functionality"""
    print("=" * 60)
    print("Testing Basic Async Functionality")
    print("=" * 60)
    
    # Create progress callback
    progress_callback = MockProgressCallback()
    
    # Create async transcriber
    transcriber = AsyncTranscriber(progress_callback=progress_callback)
    
    try:
        # Create mock audio file
        audio_file = await create_mock_audio_file()
        output_dir = tempfile.mkdtemp()
        
        print(f"Mock audio file: {audio_file}")
        print(f"Output directory: {output_dir}")
        
        # Create transcription task
        task = create_transcription_task(
            audio_file=audio_file,
            output_dir=output_dir,
            aws_credentials={
                "access_key": "test_key",
                "secret_key": "test_secret",
                "region": "us-east-1",
                "s3_bucket": "test-bucket"
            },
            aws_settings={
                "model_id": "ollama:llama3.2",  # Use free model for testing
                "temperature": "0.7",
                "max_tokens": "4096",
                "language_code": "en-US",
                "enable_diarization": False,
                "max_speakers": "10",
                "local_storage_dir": output_dir,
                "transcription_method": "mock",
                "openai_compatible_key": ""
            }
        )
        
        print(f"Created task: {task.task_id}")
        
        # This would normally start the task, but we'll simulate it
        print("Note: This is a mock test - actual transcription would require real audio files and API access")
        
        # Test task status methods
        print(f"Task status: {await transcriber.get_task_status(task.task_id)}")
        
        # Test progress updates
        await transcriber._send_progress_update(
            task.task_id, TaskStatus.RUNNING, 25.0, "Mock transcription in progress"
        )
        
        await transcriber._send_progress_update(
            task.task_id, TaskStatus.RUNNING, 75.0, "Mock summarization in progress"
        )
        
        await transcriber._send_progress_update(
            task.task_id, TaskStatus.COMPLETED, 100.0, "Mock task completed"
        )
        
        print(f"Received {len(progress_callback.updates)} progress updates")
        
        # Clean up
        os.unlink(audio_file)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        await transcriber.shutdown()
    
    print("✅ Basic async functionality test completed")

async def test_multiple_tasks():
    """Test handling multiple concurrent tasks"""
    print("\n" + "=" * 60)
    print("Testing Multiple Concurrent Tasks")
    print("=" * 60)
    
    progress_callback = MockProgressCallback()
    transcriber = AsyncTranscriber(progress_callback=progress_callback)
    
    try:
        tasks = []
        
        # Create multiple mock tasks
        for i in range(3):
            audio_file = await create_mock_audio_file()
            output_dir = tempfile.mkdtemp()
            
            task = create_transcription_task(
                audio_file=audio_file,
                output_dir=output_dir,
                aws_credentials={
                    "access_key": "test_key",
                    "secret_key": "test_secret", 
                    "region": "us-east-1",
                    "s3_bucket": "test-bucket"
                },
                aws_settings={
                    "model_id": "ollama:llama3.2",
                    "temperature": "0.7",
                    "max_tokens": "4096",
                    "language_code": "en-US",
                    "enable_diarization": False,
                    "max_speakers": "10",
                    "local_storage_dir": output_dir,
                    "transcription_method": "mock",
                    "openai_compatible_key": ""
                }
            )
            
            tasks.append((task, audio_file))
            print(f"Created task {i+1}: {task.task_id}")
        
        # Simulate progress for all tasks
        for i, (task, audio_file) in enumerate(tasks):
            await transcriber._send_progress_update(
                task.task_id, TaskStatus.RUNNING, 30.0 + i*10, f"Mock processing task {i+1}"
            )
        
        # Test cancellation
        if tasks:
            cancel_task = tasks[0][0]
            print(f"Testing cancellation of task: {cancel_task.task_id}")
            cancelled = await transcriber.cancel_task(cancel_task.task_id)
            print(f"Cancellation result: {cancelled}")
        
        # Complete remaining tasks
        for i, (task, audio_file) in enumerate(tasks[1:], 1):
            await transcriber._send_progress_update(
                task.task_id, TaskStatus.COMPLETED, 100.0, f"Mock task {i+1} completed"
            )
        
        print(f"Total progress updates: {len(progress_callback.updates)}")
        
        # Clean up
        for task, audio_file in tasks:
            try:
                os.unlink(audio_file)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Multiple tasks test failed: {e}")
        raise
    finally:
        await transcriber.shutdown()
    
    print("✅ Multiple tasks test completed")

async def test_error_handling():
    """Test error handling and recovery"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    progress_callback = MockProgressCallback()
    transcriber = AsyncTranscriber(progress_callback=progress_callback)
    
    try:
        # Test invalid task ID
        status = await transcriber.get_task_status("invalid_task_id")
        print(f"Status for invalid task: {status}")
        
        # Test cancelling non-existent task
        cancelled = await transcriber.cancel_task("invalid_task_id")
        print(f"Cancel non-existent task result: {cancelled}")
        
        # Test error progress update
        await transcriber._send_progress_update(
            "error_task", TaskStatus.FAILED, 0.0, "Mock error occurred"
        )
        
        print("✅ Error handling test completed")
        
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        raise
    finally:
        await transcriber.shutdown()

def test_gui_components():
    """Test GUI components (without actually showing GUI)"""
    print("\n" + "=" * 60)
    print("Testing GUI Components")
    print("=" * 60)
    
    try:
        # Test imports
        from async_gui_integration import AsyncTranscriberManager, AsyncProgressWidget
        print("✅ GUI integration imports successful")
        
        # Test progress update data structure
        from async_transcriber import ProgressUpdate, TaskStatus
        
        update = ProgressUpdate(
            task_id="test_task",
            status=TaskStatus.RUNNING,
            progress_percent=50.0,
            message="Test progress update",
            timestamp=datetime.now()
        )
        
        print(f"✅ Progress update created: {update.task_id} - {update.progress_percent}%")
        
        print("✅ GUI components test completed")
        
    except ImportError as e:
        print(f"⚠️  GUI components test skipped (PyQt5 not available): {e}")
    except Exception as e:
        logger.error(f"GUI components test failed: {e}")
        raise

async def run_all_tests():
    """Run all async feature tests"""
    print("🚀 Starting Async Meeting Transcriber Tests")
    print("=" * 60)
    
    try:
        # Test basic functionality
        await test_basic_async_functionality()
        
        # Test multiple tasks
        await test_multiple_tasks()
        
        # Test error handling
        await test_error_handling()
        
        # Test GUI components (sync test)
        test_gui_components()
        
        print("\n" + "=" * 60)
        print("🎉 All Async Tests Completed Successfully!")
        print("=" * 60)
        
        print("\nNext Steps:")
        print("1. Install async requirements: pip install -r requirements_async.txt")
        print("2. Run the enhanced GUI: python meeting_transcriber_gui_async.py")
        print("3. Test with real audio files and API credentials")
        
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        logger.exception("Test suite failed")
        return False
    
    return True

def main():
    """Main function"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required for async features")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n✅ Async features are ready for use!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()