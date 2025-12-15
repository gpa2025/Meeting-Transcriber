"""
Async GUI Integration for Meeting Transcriber

This module provides PyQt5 integration for async transcription processing,
including real-time progress updates, cancellation support, and responsive UI.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 12-15-2025
Version: 1.1
Assisted by: Amazon Q for VS Code
"""

import asyncio
import sys
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QTextEdit, QMessageBox,
                            QListWidget, QListWidgetItem, QSplitter, QGroupBox,
                            QFormLayout, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt, QObject
from PyQt5.QtGui import QFont, QColor, QPalette

from async_transcriber import (AsyncTranscriber, TranscriptionTask, ProgressUpdate, 
                             TaskStatus, create_transcription_task)

logger = logging.getLogger(__name__)

class AsyncEventLoop(QThread):
    """
    QThread that runs an asyncio event loop for async operations
    """
    
    def __init__(self):
        super().__init__()
        self.loop = None
        self._shutdown = False
        
    def run(self):
        """Run the asyncio event loop in this thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._run_loop())
        finally:
            self.loop.close()
    
    async def _run_loop(self):
        """Main event loop coroutine"""
        while not self._shutdown:
            await asyncio.sleep(0.1)  # Keep loop alive
    
    def shutdown(self):
        """Shutdown the event loop"""
        self._shutdown = True
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

class AsyncProgressWidget(QWidget):
    """
    Widget for displaying real-time progress of async transcription tasks
    """
    
    task_completed = pyqtSignal(str, dict)  # task_id, result
    task_failed = pyqtSignal(str, str)      # task_id, error_message
    task_cancelled = pyqtSignal(str)        # task_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_tasks: Dict[str, Dict] = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the progress widget UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Transcription Progress")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Task list
        self.task_list = QListWidget()
        self.task_list.setMaximumHeight(200)
        layout.addWidget(self.task_list)
        
        # Current task details
        details_group = QGroupBox("Current Task Details")
        details_layout = QFormLayout(details_group)
        
        self.current_task_label = QLabel("No active task")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("")
        self.time_label = QLabel("")
        
        details_layout.addRow("Task:", self.current_task_label)
        details_layout.addRow("Progress:", self.progress_bar)
        details_layout.addRow("Status:", self.status_label)
        details_layout.addRow("Time:", self.time_label)
        
        layout.addWidget(details_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel Current Task")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_current_task)
        
        self.clear_completed_button = QPushButton("Clear Completed")
        self.clear_completed_button.clicked.connect(self.clear_completed_tasks)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.clear_completed_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_time_labels)
        self.update_timer.start(1000)  # Update every second
    
    def add_task(self, task_id: str, audio_file: str):
        """Add a new task to the progress widget"""
        task_info = {
            'audio_file': audio_file,
            'start_time': datetime.now(),
            'status': TaskStatus.PENDING,
            'progress': 0.0,
            'message': 'Task queued',
            'list_item': None
        }
        
        # Create list item
        item = QListWidgetItem()
        item.setText(f"🔄 {os.path.basename(audio_file)} - Queued")
        item.setData(Qt.UserRole, task_id)
        
        # Set colors based on status
        self._update_item_appearance(item, TaskStatus.PENDING)
        
        self.task_list.addItem(item)
        task_info['list_item'] = item
        
        self.active_tasks[task_id] = task_info
        
        # Select this task as current
        self.task_list.setCurrentItem(item)
        self._update_current_task_display(task_id)
        
        logger.info(f"Added task {task_id} to progress widget")
    
    def update_task_progress(self, update: ProgressUpdate):
        """Update task progress from ProgressUpdate"""
        task_id = update.task_id
        
        if task_id not in self.active_tasks:
            logger.warning(f"Received update for unknown task: {task_id}")
            return
        
        task_info = self.active_tasks[task_id]
        task_info['status'] = update.status
        task_info['progress'] = update.progress_percent
        task_info['message'] = update.message
        task_info['last_update'] = update.timestamp
        
        # Update list item
        item = task_info['list_item']
        if item:
            filename = os.path.basename(task_info['audio_file'])
            
            if update.status == TaskStatus.RUNNING:
                item.setText(f"⚡ {filename} - {update.progress_percent:.1f}% - {update.message}")
            elif update.status == TaskStatus.COMPLETED:
                item.setText(f"✅ {filename} - Completed")
                self.task_completed.emit(task_id, {})  # Emit completion signal
            elif update.status == TaskStatus.FAILED:
                item.setText(f"❌ {filename} - Failed: {update.message}")
                self.task_failed.emit(task_id, update.message)
            elif update.status == TaskStatus.CANCELLED:
                item.setText(f"🚫 {filename} - Cancelled")
                self.task_cancelled.emit(task_id)
            else:
                item.setText(f"🔄 {filename} - {update.message}")
            
            self._update_item_appearance(item, update.status)
        
        # Update current task display if this is the selected task
        current_item = self.task_list.currentItem()
        if current_item and current_item.data(Qt.UserRole) == task_id:
            self._update_current_task_display(task_id)
        
        logger.debug(f"Updated task {task_id}: {update.status.value} - {update.progress_percent}%")
    
    def _update_item_appearance(self, item: QListWidgetItem, status: TaskStatus):
        """Update the visual appearance of a list item based on status"""
        if status == TaskStatus.PENDING:
            item.setBackground(QColor(240, 240, 240))  # Light gray
        elif status == TaskStatus.RUNNING:
            item.setBackground(QColor(255, 255, 200))  # Light yellow
        elif status == TaskStatus.COMPLETED:
            item.setBackground(QColor(200, 255, 200))  # Light green
        elif status == TaskStatus.FAILED:
            item.setBackground(QColor(255, 200, 200))  # Light red
        elif status == TaskStatus.CANCELLED:
            item.setBackground(QColor(220, 220, 220))  # Gray
    
    def _update_current_task_display(self, task_id: str):
        """Update the current task details display"""
        if task_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[task_id]
        filename = os.path.basename(task_info['audio_file'])
        
        self.current_task_label.setText(filename)
        self.progress_bar.setValue(int(task_info['progress']))
        self.progress_bar.setVisible(True)
        self.status_label.setText(task_info['message'])
        
        # Enable/disable cancel button
        can_cancel = task_info['status'] in [TaskStatus.PENDING, TaskStatus.RUNNING]
        self.cancel_button.setEnabled(can_cancel)
    
    def update_time_labels(self):
        """Update time labels for all tasks"""
        current_item = self.task_list.currentItem()
        if not current_item:
            return
        
        task_id = current_item.data(Qt.UserRole)
        if task_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[task_id]
        start_time = task_info['start_time']
        elapsed = datetime.now() - start_time
        
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
        self.time_label.setText(f"Elapsed: {elapsed_str}")
    
    def cancel_current_task(self):
        """Cancel the currently selected task"""
        current_item = self.task_list.currentItem()
        if not current_item:
            return
        
        task_id = current_item.data(Qt.UserRole)
        if task_id in self.active_tasks:
            # This will be connected to the actual cancellation logic
            self.request_task_cancellation(task_id)
    
    def request_task_cancellation(self, task_id: str):
        """Request cancellation of a specific task (to be connected to async transcriber)"""
        # This method should be connected to the async transcriber's cancel method
        logger.info(f"Cancellation requested for task: {task_id}")
    
    def clear_completed_tasks(self):
        """Remove completed, failed, and cancelled tasks from the list"""
        items_to_remove = []
        
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            task_id = item.data(Qt.UserRole)
            
            if task_id in self.active_tasks:
                status = self.active_tasks[task_id]['status']
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    items_to_remove.append((i, task_id))
        
        # Remove items in reverse order to maintain indices
        for i, task_id in reversed(items_to_remove):
            self.task_list.takeItem(i)
            del self.active_tasks[task_id]
        
        logger.info(f"Cleared {len(items_to_remove)} completed tasks")
    
    def get_active_task_count(self) -> int:
        """Get the number of active (running or pending) tasks"""
        active_count = 0
        for task_info in self.active_tasks.values():
            if task_info['status'] in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                active_count += 1
        return active_count

class AsyncTranscriberManager(QObject):
    """
    Manager class that bridges PyQt5 GUI with async transcription
    """
    
    progress_updated = pyqtSignal(object)  # ProgressUpdate object
    task_completed = pyqtSignal(str, dict)  # task_id, result
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transcriber = None
        self.event_loop_thread = None
        self.setup_async_environment()
    
    def setup_async_environment(self):
        """Set up the async environment"""
        # Start async event loop in separate thread
        self.event_loop_thread = AsyncEventLoop()
        self.event_loop_thread.start()
        
        # Wait a moment for the loop to start
        import time
        time.sleep(0.1)
        
        # Create async transcriber with progress callback
        self.transcriber = AsyncTranscriber(progress_callback=self._on_progress_update)
        
        logger.info("Async transcriber manager initialized")
    
    def _on_progress_update(self, update: ProgressUpdate):
        """Handle progress updates from async transcriber"""
        # Emit signal to update GUI (signals are thread-safe in PyQt5)
        self.progress_updated.emit(update)
        
        # Check if task is completed
        if update.status == TaskStatus.COMPLETED:
            # Get task result
            if update.task_id in self.transcriber.task_results:
                result = self.transcriber.task_results[update.task_id]
                self.task_completed.emit(update.task_id, result)
    
    def start_transcription_async(self, audio_file: str, output_dir: str, 
                                aws_credentials: Dict[str, str], aws_settings: Dict[str, str],
                                skip_transcription: bool = False, transcript_file: str = None) -> str:
        """Start an async transcription task"""
        if not self.transcriber or not self.event_loop_thread.loop:
            raise RuntimeError("Async environment not properly initialized")
        
        # Create transcription task
        task = create_transcription_task(
            audio_file=audio_file,
            output_dir=output_dir,
            aws_credentials=aws_credentials,
            aws_settings=aws_settings,
            skip_transcription=skip_transcription,
            transcript_file=transcript_file
        )
        
        # Schedule task in async loop
        future = asyncio.run_coroutine_threadsafe(
            self.transcriber.start_transcription(task),
            self.event_loop_thread.loop
        )
        
        # Get task ID
        task_id = future.result(timeout=1.0)  # Should return immediately
        
        logger.info(f"Started async transcription task: {task_id}")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if not self.transcriber or not self.event_loop_thread.loop:
            return False
        
        # Schedule cancellation in async loop
        future = asyncio.run_coroutine_threadsafe(
            self.transcriber.cancel_task(task_id),
            self.event_loop_thread.loop
        )
        
        try:
            return future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task"""
        if not self.transcriber or not self.event_loop_thread.loop:
            return None
        
        future = asyncio.run_coroutine_threadsafe(
            self.transcriber.get_task_status(task_id),
            self.event_loop_thread.loop
        )
        
        try:
            return future.result(timeout=1.0)
        except Exception as e:
            logger.error(f"Failed to get status for task {task_id}: {e}")
            return None
    
    def shutdown(self):
        """Shutdown the async transcriber manager"""
        logger.info("Shutting down async transcriber manager")
        
        if self.transcriber:
            # Schedule shutdown in async loop
            if self.event_loop_thread.loop:
                future = asyncio.run_coroutine_threadsafe(
                    self.transcriber.shutdown(),
                    self.event_loop_thread.loop
                )
                try:
                    future.result(timeout=10.0)
                except Exception as e:
                    logger.error(f"Error during transcriber shutdown: {e}")
        
        if self.event_loop_thread:
            self.event_loop_thread.shutdown()
            self.event_loop_thread.wait(5000)  # Wait up to 5 seconds
        
        logger.info("Async transcriber manager shutdown complete")

# Import os for path operations
import os