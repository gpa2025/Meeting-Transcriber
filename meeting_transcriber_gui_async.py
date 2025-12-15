"""
Enhanced Meeting Transcriber GUI with Async Support

This is an enhanced version of the Meeting Transcriber GUI that includes:
- Async transcription processing
- Real-time progress updates
- Task cancellation support
- Multiple concurrent transcriptions
- Responsive user interface

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 12-15-2025
Version: 1.1
Assisted by: Amazon Q for VS Code
"""

import os
import sys
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox,
                            QGroupBox, QFormLayout, QMessageBox, QTextEdit, QProgressBar,
                            QSplashScreen, QTabWidget, QSplitter, QCheckBox, QSpinBox,
                            QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor

# Import async components
from async_gui_integration import AsyncTranscriberManager, AsyncProgressWidget
from async_transcriber import ProgressUpdate, TaskStatus

# Import existing modules
import aws_transcribe
from summarizer_bedrock import generate_notes_with_bedrock
from summarizer_free import generate_notes_with_free_models
import format_meeting_notes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class EnhancedMeetingTranscriberGUI(QMainWindow):
    """
    Enhanced Meeting Transcriber GUI with async support
    """
    
    def __init__(self):
        super().__init__()
        self.async_manager = None
        self.progress_widget = None
        self.settings = QSettings('MeetingTranscriber', 'AsyncGUI')
        self.setup_ui()
        self.setup_async_components()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the enhanced user interface"""
        self.setWindowTitle("Meeting Transcriber - Enhanced Async Version")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application icon
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.setup_transcription_tab()
        self.setup_progress_tab()
        self.setup_settings_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready - Enhanced Async Version")
        
    def setup_transcription_tab(self):
        """Set up the main transcription tab"""
        transcription_widget = QWidget()
        self.tab_widget.addTab(transcription_widget, "Transcription")
        
        layout = QVBoxLayout(transcription_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Input controls
        left_panel = self.create_input_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Quick progress and log
        right_panel = self.create_quick_progress_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([600, 400])
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Transcription")
        self.start_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.start_button.clicked.connect(self.start_transcription)
        
        self.add_to_queue_button = QPushButton("Add to Queue")
        self.add_to_queue_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px; }")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        
        self.cancel_all_button = QPushButton("Cancel All")
        self.cancel_all_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        self.cancel_all_button.clicked.connect(self.cancel_all_tasks)
        self.cancel_all_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.add_to_queue_button)
        button_layout.addWidget(self.cancel_all_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def create_input_panel(self):
        """Create the input controls panel"""
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumWidth(600)
        
        layout = QVBoxLayout(scroll_widget)
        
        # File Selection Group
        file_group = QGroupBox("File Selection")
        file_layout = QFormLayout(file_group)
        
        # Audio file input
        audio_layout = QHBoxLayout()
        self.audio_file_input = QLineEdit()
        self.audio_file_input.setReadOnly(True)
        audio_button = QPushButton("Browse...")
        audio_button.clicked.connect(self.browse_audio_file)
        audio_layout.addWidget(self.audio_file_input)
        audio_layout.addWidget(audio_button)
        file_layout.addRow("Audio File:", audio_layout)
        
        # Output directory input
        output_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        output_button = QPushButton("Browse...")
        output_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(output_button)
        file_layout.addRow("Output Directory:", output_layout)
        
        layout.addWidget(file_group)
        
        # AWS Settings Group
        aws_group = QGroupBox("AWS Settings")
        aws_layout = QFormLayout(aws_group)
        
        self.aws_access_key_input = QLineEdit()
        self.aws_access_key_input.setEchoMode(QLineEdit.Password)
        aws_layout.addRow("Access Key ID:", self.aws_access_key_input)
        
        self.aws_secret_key_input = QLineEdit()
        self.aws_secret_key_input.setEchoMode(QLineEdit.Password)
        aws_layout.addRow("Secret Access Key:", self.aws_secret_key_input)
        
        self.aws_region_input = QComboBox()
        self.aws_region_input.addItems([
            "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1"
        ])
        aws_layout.addRow("Region:", self.aws_region_input)
        
        self.s3_bucket_input = QLineEdit()
        aws_layout.addRow("S3 Bucket:", self.s3_bucket_input)
        
        layout.addWidget(aws_group)
        
        # AI Model Settings Group
        model_group = QGroupBox("AI Model Settings")
        model_layout = QFormLayout(model_group)
        
        self.model_input = QComboBox()
        self.model_input.setEditable(True)
        self.populate_model_list()
        model_layout.addRow("AI Model:", self.model_input)
        
        self.temperature_input = QLineEdit("0.7")
        model_layout.addRow("Temperature:", self.temperature_input)
        
        self.max_tokens_input = QLineEdit("4096")
        model_layout.addRow("Max Tokens:", self.max_tokens_input)
        
        layout.addWidget(model_group)
        
        # Transcription Settings Group
        transcription_group = QGroupBox("Transcription Settings")
        transcription_layout = QFormLayout(transcription_group)
        
        self.language_input = QComboBox()
        self.language_input.addItems([
            "en-US", "es-US", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"
        ])
        transcription_layout.addRow("Language:", self.language_input)
        
        self.diarization_input = QComboBox()
        self.diarization_input.addItems(["Enabled", "Disabled"])
        transcription_layout.addRow("Speaker Diarization:", self.diarization_input)
        
        self.max_speakers_input = QSpinBox()
        self.max_speakers_input.setRange(2, 20)
        self.max_speakers_input.setValue(10)
        transcription_layout.addRow("Max Speakers:", self.max_speakers_input)
        
        # Skip transcription option
        self.skip_transcription_checkbox = QCheckBox("Skip transcription (use existing transcript)")
        transcription_layout.addRow("", self.skip_transcription_checkbox)
        
        # Transcript file input (for skip transcription)
        transcript_layout = QHBoxLayout()
        self.transcript_file_input = QLineEdit()
        self.transcript_file_input.setReadOnly(True)
        self.transcript_file_input.setEnabled(False)
        transcript_button = QPushButton("Browse...")
        transcript_button.clicked.connect(self.browse_transcript_file)
        transcript_button.setEnabled(False)
        transcript_layout.addWidget(self.transcript_file_input)
        transcript_layout.addWidget(transcript_button)
        transcription_layout.addRow("Transcript File:", transcript_layout)
        
        # Connect skip transcription checkbox
        self.skip_transcription_checkbox.toggled.connect(
            lambda checked: [
                self.transcript_file_input.setEnabled(checked),
                transcript_button.setEnabled(checked)
            ]
        )
        
        layout.addWidget(transcription_group)
        
        # Async Settings Group
        async_group = QGroupBox("Async Processing Settings")
        async_layout = QFormLayout(async_group)
        
        self.concurrent_tasks_input = QSpinBox()
        self.concurrent_tasks_input.setRange(1, 5)
        self.concurrent_tasks_input.setValue(2)
        async_layout.addRow("Max Concurrent Tasks:", self.concurrent_tasks_input)
        
        self.auto_open_folder_checkbox = QCheckBox("Auto-open output folder when complete")
        self.auto_open_folder_checkbox.setChecked(True)
        async_layout.addRow("", self.auto_open_folder_checkbox)
        
        layout.addWidget(async_group)
        
        return scroll_area
    
    def create_quick_progress_panel(self):
        """Create the quick progress and log panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Quick status
        status_group = QGroupBox("Quick Status")
        status_layout = QVBoxLayout(status_group)
        
        self.quick_progress_bar = QProgressBar()
        self.quick_progress_bar.setVisible(False)
        status_layout.addWidget(self.quick_progress_bar)
        
        self.quick_status_label = QLabel("Ready")
        status_layout.addWidget(self.quick_status_label)
        
        layout.addWidget(status_group)
        
        # Recent activity log
        log_group = QGroupBox("Recent Activity")
        log_layout = QVBoxLayout(log_group)
        
        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setReadOnly(True)
        log_layout.addWidget(self.activity_log)
        
        layout.addWidget(log_group)
        
        return widget
    
    def setup_progress_tab(self):
        """Set up the detailed progress monitoring tab"""
        progress_widget = QWidget()
        self.tab_widget.addTab(progress_widget, "Progress Monitor")
        
        layout = QVBoxLayout(progress_widget)
        
        # Create progress widget
        self.progress_widget = AsyncProgressWidget()
        layout.addWidget(self.progress_widget)
        
        # Connect progress widget signals
        self.progress_widget.task_completed.connect(self.on_task_completed)
        self.progress_widget.task_failed.connect(self.on_task_failed)
        self.progress_widget.task_cancelled.connect(self.on_task_cancelled)
    
    def setup_settings_tab(self):
        """Set up the settings tab"""
        settings_widget = QWidget()
        self.tab_widget.addTab(settings_widget, "Settings")
        
        layout = QVBoxLayout(settings_widget)
        
        # Settings content
        settings_scroll = QScrollArea()
        settings_content = QWidget()
        settings_scroll.setWidget(settings_content)
        settings_scroll.setWidgetResizable(True)
        
        settings_layout = QVBoxLayout(settings_content)
        
        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        self.save_settings_checkbox = QCheckBox("Auto-save settings")
        self.save_settings_checkbox.setChecked(True)
        app_layout.addRow("", self.save_settings_checkbox)
        
        self.show_notifications_checkbox = QCheckBox("Show completion notifications")
        self.show_notifications_checkbox.setChecked(True)
        app_layout.addRow("", self.show_notifications_checkbox)
        
        settings_layout.addWidget(app_group)
        
        # Performance Settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout(perf_group)
        
        self.thread_pool_size_input = QSpinBox()
        self.thread_pool_size_input.setRange(1, 8)
        self.thread_pool_size_input.setValue(3)
        perf_layout.addRow("Thread Pool Size:", self.thread_pool_size_input)
        
        self.progress_update_interval_input = QSpinBox()
        self.progress_update_interval_input.setRange(1, 10)
        self.progress_update_interval_input.setValue(2)
        self.progress_update_interval_input.setSuffix(" seconds")
        perf_layout.addRow("Progress Update Interval:", self.progress_update_interval_input)
        
        settings_layout.addWidget(perf_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_settings_button = QPushButton("Save Settings")
        save_settings_button.clicked.connect(self.save_settings)
        
        load_settings_button = QPushButton("Load Settings")
        load_settings_button.clicked.connect(self.load_settings)
        
        reset_settings_button = QPushButton("Reset to Defaults")
        reset_settings_button.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(save_settings_button)
        button_layout.addWidget(load_settings_button)
        button_layout.addWidget(reset_settings_button)
        button_layout.addStretch()
        
        settings_layout.addLayout(button_layout)
        
        layout.addWidget(settings_scroll)
    
    def setup_async_components(self):
        """Set up async transcription components"""
        try:
            self.async_manager = AsyncTranscriberManager(self)
            
            # Connect signals
            self.async_manager.progress_updated.connect(self.on_progress_updated)
            self.async_manager.task_completed.connect(self.on_async_task_completed)
            
            logger.info("Async components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize async components: {e}")
            QMessageBox.critical(self, "Initialization Error", 
                               f"Failed to initialize async components:\n{str(e)}")
    
    def populate_model_list(self):
        """Populate the AI model dropdown with available models"""
        models = [
            # AWS Bedrock Models
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "amazon.nova-pro-v1:0",
            "amazon.nova-lite-v1:0",
            "meta.llama3-2-90b-instruct-v1:0",
            "meta.llama3-2-11b-instruct-v1:0",
            "mistral.mistral-large-2407-v1:0",
            
            # Free Models
            "ollama:llama3.2",
            "ollama:mistral",
            "ollama:codellama",
            "hf:microsoft/DialoGPT-large",
            "openai-free:meta-llama/Llama-2-7b-chat-hf"
        ]
        
        self.model_input.addItems(models)
        self.model_input.setCurrentText("us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    def browse_audio_file(self):
        """Browse for audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg);;All Files (*)"
        )
        if file_path:
            self.audio_file_input.setText(file_path)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        current_dir = os.getcwd()
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", current_dir)
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def browse_transcript_file(self):
        """Browse for existing transcript file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Transcript File", "", 
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.transcript_file_input.setText(file_path)
    
    def validate_inputs(self) -> bool:
        """Validate user inputs"""
        if not self.audio_file_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select an audio file.")
            return False
        
        if not self.output_dir_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select an output directory.")
            return False
        
        # Check if using free models or AWS
        model_id = self.model_input.currentText()
        is_free_model = model_id.startswith(('ollama:', 'hf:', 'openai-free:'))
        
        if not is_free_model:
            # Validate AWS credentials
            if not all([
                self.aws_access_key_input.text(),
                self.aws_secret_key_input.text(),
                self.s3_bucket_input.text()
            ]):
                QMessageBox.warning(self, "Missing AWS Credentials", 
                                  "Please provide AWS credentials for Bedrock models.")
                return False
        
        if self.skip_transcription_checkbox.isChecked():
            if not self.transcript_file_input.text():
                QMessageBox.warning(self, "Missing Transcript", 
                                  "Please select a transcript file when skipping transcription.")
                return False
        
        return True
    
    def start_transcription(self):
        """Start a new transcription task"""
        if not self.validate_inputs():
            return
        
        if not self.async_manager:
            QMessageBox.critical(self, "Error", "Async manager not initialized.")
            return
        
        try:
            # Prepare task parameters
            aws_credentials = {
                "access_key": self.aws_access_key_input.text(),
                "secret_key": self.aws_secret_key_input.text(),
                "region": self.aws_region_input.currentText(),
                "s3_bucket": self.s3_bucket_input.text()
            }
            
            aws_settings = {
                "model_id": self.model_input.currentText(),
                "temperature": self.temperature_input.text(),
                "max_tokens": self.max_tokens_input.text(),
                "language_code": self.language_input.currentText(),
                "enable_diarization": self.diarization_input.currentText() == "Enabled",
                "max_speakers": str(self.max_speakers_input.value()),
                "local_storage_dir": self.output_dir_input.text(),
                "transcription_method": "aws",
                "openai_compatible_key": ""
            }
            
            # Start async transcription
            task_id = self.async_manager.start_transcription_async(
                audio_file=self.audio_file_input.text(),
                output_dir=self.output_dir_input.text(),
                aws_credentials=aws_credentials,
                aws_settings=aws_settings,
                skip_transcription=self.skip_transcription_checkbox.isChecked(),
                transcript_file=self.transcript_file_input.text() if self.skip_transcription_checkbox.isChecked() else None
            )
            
            # Add task to progress widget
            if self.progress_widget:
                self.progress_widget.add_task(task_id, self.audio_file_input.text())
                
                # Connect cancellation
                self.progress_widget.request_task_cancellation = self.cancel_task
            
            # Update UI
            self.cancel_all_button.setEnabled(True)
            self.log_activity(f"Started transcription: {os.path.basename(self.audio_file_input.text())}")
            
            # Switch to progress tab
            self.tab_widget.setCurrentIndex(1)
            
        except Exception as e:
            logger.error(f"Failed to start transcription: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start transcription:\n{str(e)}")
    
    def add_to_queue(self):
        """Add current settings to queue for batch processing"""
        if not self.validate_inputs():
            return
        
        # For now, just start another transcription
        # In a full implementation, you'd maintain a queue
        self.start_transcription()
    
    def cancel_task(self, task_id: str):
        """Cancel a specific task"""
        if self.async_manager:
            success = self.async_manager.cancel_task(task_id)
            if success:
                self.log_activity(f"Cancelled task: {task_id}")
            else:
                self.log_activity(f"Failed to cancel task: {task_id}")
    
    def cancel_all_tasks(self):
        """Cancel all active tasks"""
        if self.progress_widget:
            active_count = self.progress_widget.get_active_task_count()
            if active_count == 0:
                QMessageBox.information(self, "No Active Tasks", "No active tasks to cancel.")
                return
            
            reply = QMessageBox.question(self, "Cancel All Tasks", 
                                       f"Are you sure you want to cancel {active_count} active task(s)?",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Cancel all active tasks
                for task_id, task_info in self.progress_widget.active_tasks.items():
                    if task_info['status'] in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                        self.cancel_task(task_id)
                
                self.log_activity(f"Cancelled {active_count} active tasks")
    
    def on_progress_updated(self, update: ProgressUpdate):
        """Handle progress updates from async transcriber"""
        # Update progress widget
        if self.progress_widget:
            self.progress_widget.update_task_progress(update)
        
        # Update quick progress if this is the most recent task
        self.quick_status_label.setText(update.message)
        if update.status == TaskStatus.RUNNING:
            self.quick_progress_bar.setVisible(True)
            self.quick_progress_bar.setValue(int(update.progress_percent))
        elif update.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            self.quick_progress_bar.setVisible(False)
        
        # Log activity
        self.log_activity(f"{update.task_id}: {update.message}")
    
    def on_async_task_completed(self, task_id: str, result: dict):
        """Handle async task completion"""
        self.log_activity(f"Task completed: {task_id}")
        
        if self.show_notifications_checkbox.isChecked():
            QMessageBox.information(self, "Task Completed", 
                                  f"Transcription completed successfully!\nTask ID: {task_id}")
        
        # Check if no more active tasks
        if self.progress_widget and self.progress_widget.get_active_task_count() == 0:
            self.cancel_all_button.setEnabled(False)
    
    def on_task_completed(self, task_id: str, result: dict):
        """Handle task completion from progress widget"""
        self.log_activity(f"✅ Completed: {task_id}")
    
    def on_task_failed(self, task_id: str, error_message: str):
        """Handle task failure from progress widget"""
        self.log_activity(f"❌ Failed: {task_id} - {error_message}")
        
        if self.show_notifications_checkbox.isChecked():
            QMessageBox.warning(self, "Task Failed", 
                              f"Transcription failed:\n{error_message}")
    
    def on_task_cancelled(self, task_id: str):
        """Handle task cancellation from progress widget"""
        self.log_activity(f"🚫 Cancelled: {task_id}")
    
    def log_activity(self, message: str):
        """Log activity to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.activity_log.append(formatted_message)
        
        # Keep log size manageable
        if self.activity_log.document().blockCount() > 100:
            cursor = self.activity_log.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
    
    def save_settings(self):
        """Save current settings"""
        try:
            self.settings.setValue("audio_file", self.audio_file_input.text())
            self.settings.setValue("output_dir", self.output_dir_input.text())
            self.settings.setValue("aws_access_key", self.aws_access_key_input.text())
            self.settings.setValue("aws_secret_key", self.aws_secret_key_input.text())
            self.settings.setValue("aws_region", self.aws_region_input.currentText())
            self.settings.setValue("s3_bucket", self.s3_bucket_input.text())
            self.settings.setValue("model", self.model_input.currentText())
            self.settings.setValue("temperature", self.temperature_input.text())
            self.settings.setValue("max_tokens", self.max_tokens_input.text())
            self.settings.setValue("language", self.language_input.currentText())
            self.settings.setValue("diarization", self.diarization_input.currentText())
            self.settings.setValue("max_speakers", self.max_speakers_input.value())
            self.settings.setValue("auto_open_folder", self.auto_open_folder_checkbox.isChecked())
            self.settings.setValue("show_notifications", self.show_notifications_checkbox.isChecked())
            
            self.statusBar().showMessage("Settings saved", 2000)
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "Save Error", f"Failed to save settings:\n{str(e)}")
    
    def load_settings(self):
        """Load saved settings"""
        try:
            self.audio_file_input.setText(self.settings.value("audio_file", ""))
            self.output_dir_input.setText(self.settings.value("output_dir", ""))
            self.aws_access_key_input.setText(self.settings.value("aws_access_key", ""))
            self.aws_secret_key_input.setText(self.settings.value("aws_secret_key", ""))
            self.aws_region_input.setCurrentText(self.settings.value("aws_region", "us-east-1"))
            self.s3_bucket_input.setText(self.settings.value("s3_bucket", ""))
            self.model_input.setCurrentText(self.settings.value("model", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"))
            self.temperature_input.setText(self.settings.value("temperature", "0.7"))
            self.max_tokens_input.setText(self.settings.value("max_tokens", "4096"))
            self.language_input.setCurrentText(self.settings.value("language", "en-US"))
            self.diarization_input.setCurrentText(self.settings.value("diarization", "Enabled"))
            self.max_speakers_input.setValue(int(self.settings.value("max_speakers", 10)))
            self.auto_open_folder_checkbox.setChecked(self.settings.value("auto_open_folder", True, type=bool))
            self.show_notifications_checkbox.setChecked(self.settings.value("show_notifications", True, type=bool))
            
            self.statusBar().showMessage("Settings loaded", 2000)
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                   "Are you sure you want to reset all settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self.load_settings()
            self.statusBar().showMessage("Settings reset to defaults", 2000)
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Save settings if auto-save is enabled
        if self.save_settings_checkbox.isChecked():
            self.save_settings()
        
        # Shutdown async components
        if self.async_manager:
            self.async_manager.shutdown()
        
        event.accept()

def main():
    """Main function to run the enhanced GUI"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Meeting Transcriber - Async")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("Meeting Transcriber")
    
    # Create and show main window
    window = EnhancedMeetingTranscriberGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()