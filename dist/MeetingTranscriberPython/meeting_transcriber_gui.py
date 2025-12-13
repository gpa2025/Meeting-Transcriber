"""
Meeting Transcriber GUI Application

This module provides a graphical user interface for the Meeting Transcriber application.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
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
                            QSplashScreen)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QPixmap

# Import the transcription and summarization modules directly
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

class TranscriptionWorker(QThread):
    progress_update = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, audio_file, output_dir, aws_credentials, aws_settings, skip_transcription=False, transcript_file=None):
        super().__init__()
        self.audio_file = audio_file
        self.output_dir = output_dir
        self.aws_credentials = aws_credentials
        self.aws_settings = aws_settings
        self.skip_transcription = skip_transcription
        self.transcript_file = transcript_file
        
    def run(self):
        try:
            # Set environment variables for AWS credentials - strip any whitespace
            model_id = self.aws_settings["model_id"]
            is_free_model = model_id.startswith(('ollama:', 'hf:', 'openai-free:'))
            
            if is_free_model:
                # Set dummy credentials for free models to avoid import errors
                os.environ["AWS_ACCESS_KEY_ID"] = "dummy"
                os.environ["AWS_SECRET_ACCESS_KEY"] = "dummy"
                os.environ["AWS_REGION"] = "us-east-1"
                os.environ["AWS_S3_BUCKET"] = "dummy"
            else:
                os.environ["AWS_ACCESS_KEY_ID"] = self.aws_credentials["access_key"].strip()
                os.environ["AWS_SECRET_ACCESS_KEY"] = self.aws_credentials["secret_key"].strip()
                os.environ["AWS_REGION"] = self.aws_credentials["region"].strip()
                os.environ["AWS_S3_BUCKET"] = self.aws_credentials["s3_bucket"].strip()
            os.environ["BEDROCK_MODEL_ID"] = self.aws_settings["model_id"]
            os.environ["MODEL_TEMPERATURE"] = self.aws_settings["temperature"]
            os.environ["MAX_TOKENS"] = self.aws_settings["max_tokens"]
            os.environ["SYSTEM_PROMPT"] = self.aws_settings["system_prompt"]
            os.environ["TRANSCRIBE_LANGUAGE_CODE"] = self.aws_settings["language_code"]
            os.environ["ENABLE_SPEAKER_DIARIZATION"] = "true" if self.aws_settings["enable_diarization"] else "false"
            os.environ["MAX_SPEAKER_LABELS"] = self.aws_settings["max_speakers"]
            os.environ["LOCAL_STORAGE_DIR"] = self.aws_settings["local_storage_dir"]
            os.environ["TRANSCRIPTION_METHOD"] = self.aws_settings["transcription_method"]
            os.environ["OPENAI_COMPATIBLE_KEY"] = self.aws_settings.get("openai_compatible_key", "")
            
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Get base filename without extension
            base_filename = os.path.splitext(os.path.basename(self.audio_file))[0]
            
            # Get the file creation/modification date to use as meeting date
            try:
                # Get file creation/modification time (creation time on Windows, modification time on Unix)
                if os.path.exists(self.audio_file):
                    if sys.platform == 'win32':
                        file_time = os.path.getctime(self.audio_file)
                    else:
                        file_time = os.path.getmtime(self.audio_file)
                    meeting_date = datetime.fromtimestamp(file_time)
                    self.progress_update.emit(f"Using audio file date as meeting date: {meeting_date.strftime('%B %d, %Y')}")
                else:
                    meeting_date = datetime.now()
                    self.progress_update.emit(f"Audio file not found, using current date: {meeting_date.strftime('%B %d, %Y')}")
            except Exception as e:
                meeting_date = datetime.now()
                self.progress_update.emit(f"Warning: Could not get file date, using current date: {e}")
            
            # Step 1: Transcribe audio or load existing transcript
            if self.skip_transcription:
                self.progress_update.emit("Skipping transcription - loading selected transcript file...")
                
                if self.transcript_file and os.path.exists(self.transcript_file):
                    with open(self.transcript_file, 'r', encoding='utf-8') as f:
                        text_for_summary = f.read()
                    self.progress_update.emit(f"Loaded transcript from: {self.transcript_file}")
                else:
                    raise Exception(f"Selected transcript file not found: {self.transcript_file}. Please select a valid transcript file.")
            else:
                transcription_method = os.environ.get('TRANSCRIPTION_METHOD', 'AWS Transcribe (Premium)')
                
                if "Local" in transcription_method:
                    self.progress_update.emit("Transcribing audio file locally... (this may take a while)")
                    # Import local transcription function
                    from transcriber import transcribe_audio
                    transcript = transcribe_audio(self.audio_file, method="local")
                else:
                    self.progress_update.emit("Transcribing audio file with AWS... (this may take a while)")
                    transcript = aws_transcribe.transcribe_with_aws(self.audio_file)
                
                # Save transcript to file
                if isinstance(transcript, dict) and 'speaker_segments' in transcript:
                    # Handle speaker diarization format
                    transcript_file = os.path.join(self.output_dir, f"{base_filename}_transcript.txt")
                    speaker_transcript_file = os.path.join(self.output_dir, f"{base_filename}_transcript_with_speakers.txt")
                    
                    # Save plain transcript
                    self.save_to_file(transcript['full_transcript'], transcript_file)
                    
                    # Save transcript with speaker labels
                    speaker_text = ""
                    for segment in transcript['speaker_segments']:
                        speaker_text += f"{segment['speaker']}: {segment['text']}\n\n"
                    self.save_to_file(speaker_text, speaker_transcript_file)
                    
                    self.progress_update.emit(f"Transcript saved to {transcript_file}")
                    self.progress_update.emit(f"Transcript with speakers saved to {speaker_transcript_file}")
                    
                    # Use the full transcript for summarization
                    text_for_summary = transcript['full_transcript']
                else:
                    # Handle plain text transcript
                    transcript_file = os.path.join(self.output_dir, f"{base_filename}_transcript.txt")
                    self.save_to_file(transcript, transcript_file)
                    self.progress_update.emit(f"Transcript saved to {transcript_file}")
                    text_for_summary = transcript
            
            # Step 2: Generate meeting notes
            model_id = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
            
            if model_id.startswith(('ollama:', 'hf:', 'openai-free:')):
                self.progress_update.emit("Generating meeting notes with free models... (this may take a while)")
                self.progress_update.emit(f"Using free model: {model_id}")
                os.environ['FREE_MODEL_ID'] = model_id
                summary, key_points, action_items = generate_notes_with_free_models(text_for_summary)
            else:
                self.progress_update.emit("Generating meeting notes with AWS Bedrock... (this may take a while)")
                self.progress_update.emit(f"Using model: {model_id}")
                summary, key_points, action_items = generate_notes_with_bedrock(text_for_summary)
            
            # Extract participants if available
            participants = []
            if not self.skip_transcription and isinstance(transcript, dict) and 'speaker_segments' in transcript:
                # Extract unique speakers
                speakers = set()
                for segment in transcript['speaker_segments']:
                    speakers.add(segment['speaker'])
                
                # Add to participants list
                for speaker in speakers:
                    participants.append({
                        'id': speaker,
                        'name': f"Speaker {speaker.split('_')[-1]}" if speaker.startswith('spk_') else speaker
                    })
            
            # Format meeting notes with enhanced formatting
            meeting_notes = format_meeting_notes.format_enhanced_meeting_notes(
                transcript=text_for_summary,
                summary=summary,
                key_points=key_points,
                action_items=action_items,
                participants=participants,
                has_speaker_segments=not self.skip_transcription and isinstance(transcript, dict) and 'speaker_segments' in transcript,
                meeting_date=meeting_date  # Use the file date instead of current date
            )
            
            # Save meeting notes to file
            notes_file = os.path.join(self.output_dir, f"{base_filename}_meeting_notes.md")
            self.save_to_file(meeting_notes, notes_file)
            self.progress_update.emit(f"Meeting notes saved to {notes_file}")
            
            # Open output directory
            import subprocess
            import sys
            if sys.platform == 'win32':
                subprocess.Popen(['explorer', self.output_dir])
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.output_dir])
            else:
                subprocess.Popen(['xdg-open', self.output_dir])
            
            if self.skip_transcription:
                self.finished_signal.emit(True, "Summarization completed successfully!\nOutput directory opened.")
            else:
                self.finished_signal.emit(True, "Transcription and summarization completed successfully!\nOutput directory opened.")
                
        except Exception as e:
            logger.error(f"Error in transcription worker: {e}")
            self.progress_update.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, f"Error: {str(e)}")
    
    def save_to_file(self, content, file_path):
        """Save content to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

class MeetingTranscriberGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_settings()
        
    def initUI(self):
        self.setWindowTitle('Meeting Transcriber')
        self.setGeometry(100, 100, 800, 600)
        
        # Set application icon
        icon_path = self.get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # AWS Credentials Group
        aws_group = QGroupBox("AWS Credentials (for AWS models only)")
        aws_layout = QFormLayout()
        
        self.access_key_input = QLineEdit()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        self.region_input = QComboBox()
        self.region_input.addItems([
            "us-east-1", "us-east-2", "us-west-1", "us-west-2", 
            "eu-west-1", "eu-west-2", "eu-central-1", 
            "ap-northeast-1", "ap-northeast-2", "ap-southeast-1", "ap-southeast-2"
        ])
        self.s3_bucket_input = QLineEdit()
        
        aws_layout.addRow("Access Key:", self.access_key_input)
        aws_layout.addRow("Secret Key:", self.secret_key_input)
        aws_layout.addRow("Region:", self.region_input)
        aws_layout.addRow("S3 Bucket:", self.s3_bucket_input)
        aws_group.setLayout(aws_layout)
        
        # Local Storage Group for non-AWS models
        local_group = QGroupBox("Local Storage (for free models)")
        local_layout = QFormLayout()
        
        self.local_storage_input = QLineEdit()
        self.local_storage_input.setReadOnly(True)
        local_storage_button = QPushButton("Browse...")
        local_storage_button.clicked.connect(self.browse_local_storage)
        local_storage_layout = QHBoxLayout()
        local_storage_layout.addWidget(self.local_storage_input)
        local_storage_layout.addWidget(local_storage_button)
        
        local_layout.addRow("Data Folder:", local_storage_layout)
        local_group.setLayout(local_layout)
        
        # AI Model Settings Group
        bedrock_group = QGroupBox("AI Model Settings")
        bedrock_layout = QFormLayout()
        
        # Transcription Method Selection
        self.transcription_input = QComboBox()
        self.transcription_input.addItems([
            "AWS Transcribe (Premium)",
            "Local SpeechRecognition (Free)"
        ])
        
        # AI Model for Summarization with manage button
        model_layout = QHBoxLayout()
        self.model_input = QComboBox()
        self.model_input.setEditable(True)
        self.load_model_list()
        
        manage_models_button = QPushButton("Manage Models")
        manage_models_button.clicked.connect(self.manage_models)
        
        model_layout.addWidget(self.model_input)
        model_layout.addWidget(manage_models_button)
        self.temperature_input = QLineEdit("0.7")
        self.max_tokens_input = QLineEdit("4096")
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText("Enter system prompt here...")
        self.system_prompt_input.setMaximumHeight(100)
        
        # Free model API keys
        self.openai_compatible_key_input = QLineEdit()
        self.openai_compatible_key_input.setEchoMode(QLineEdit.Password)
        self.openai_compatible_key_input.setPlaceholderText("For OpenAI-compatible free APIs (Together AI, etc.)")
        
        bedrock_layout.addRow("Transcription:", self.transcription_input)
        bedrock_layout.addRow("AI Model:", model_layout)
        bedrock_layout.addRow("Temperature:", self.temperature_input)
        bedrock_layout.addRow("Max Tokens:", self.max_tokens_input)
        bedrock_layout.addRow("System Prompt:", self.system_prompt_input)
        bedrock_layout.addRow("OpenAI-Compatible Key:", self.openai_compatible_key_input)
        bedrock_group.setLayout(bedrock_layout)
        
        # Transcription Settings Group
        transcription_group = QGroupBox("Transcription Settings")
        transcription_layout = QFormLayout()
        
        self.language_input = QComboBox()
        self.language_input.addItems(["en-US", "en-GB", "es-US", "fr-FR", "de-DE", "it-IT", "pt-BR", "ja-JP", "ko-KR", "zh-CN"])
        self.diarization_input = QComboBox()
        self.diarization_input.addItems(["Enabled", "Disabled"])
        self.max_speakers_input = QLineEdit("10")
        
        transcription_layout.addRow("Language:", self.language_input)
        transcription_layout.addRow("Speaker Diarization:", self.diarization_input)
        transcription_layout.addRow("Max Speakers:", self.max_speakers_input)
        transcription_group.setLayout(transcription_layout)
        
        # File Selection Group
        file_group = QGroupBox("File Selection")
        file_layout = QFormLayout()
        
        self.audio_file_input = QLineEdit()
        self.audio_file_input.setReadOnly(True)
        audio_file_button = QPushButton("Browse...")
        audio_file_button.clicked.connect(self.browse_audio_file)
        audio_file_layout = QHBoxLayout()
        audio_file_layout.addWidget(self.audio_file_input)
        audio_file_layout.addWidget(audio_file_button)
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setReadOnly(True)
        output_dir_button = QPushButton("Browse...")
        output_dir_button.clicked.connect(self.browse_output_dir)
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(output_dir_button)
        
        # Skip transcription checkbox
        self.skip_transcription_checkbox = QComboBox()
        self.skip_transcription_checkbox.addItems(["No - Transcribe audio", "Yes - Skip to summarization only"])
        self.skip_transcription_checkbox.currentTextChanged.connect(self.on_skip_transcription_changed)
        
        # Transcript file selection (initially hidden)
        self.transcript_file_input = QLineEdit()
        self.transcript_file_input.setReadOnly(True)
        transcript_file_button = QPushButton("Browse...")
        transcript_file_button.clicked.connect(self.browse_transcript_file)
        transcript_file_layout = QHBoxLayout()
        transcript_file_layout.addWidget(self.transcript_file_input)
        transcript_file_layout.addWidget(transcript_file_button)
        
        file_layout.addRow("Audio File:", audio_file_layout)
        file_layout.addRow("Output Directory:", output_dir_layout)
        file_layout.addRow("Skip Transcription:", self.skip_transcription_checkbox)
        file_layout.addRow("Transcript File:", transcript_file_layout)
        
        # Store references for show/hide functionality
        self.transcript_file_row_widgets = [self.transcript_file_input, transcript_file_button]
        
        # Initially hide transcript file selection
        for widget in self.transcript_file_row_widgets:
            widget.hide()
        file_group.setLayout(file_layout)
        
        # Progress and Log Group
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.log_output)
        progress_group.setLayout(progress_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        self.start_button = QPushButton("Start Transcription")
        self.start_button.clicked.connect(self.start_transcription)
        self.about_button = QPushButton("About")
        self.about_button.clicked.connect(self.show_about)
        button_layout.addWidget(self.save_settings_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.about_button)
        
        # Add all groups to main layout
        main_layout.addWidget(aws_group)
        main_layout.addWidget(local_group)
        main_layout.addWidget(bedrock_group)
        main_layout.addWidget(transcription_group)
        main_layout.addWidget(file_group)
        main_layout.addWidget(progress_group)
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def get_icon_path(self):
        """Get the path to the application icon"""
        # Check for icon in the current directory
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            return icon_path
            
        # If running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "icon.ico")
            if os.path.exists(icon_path):
                return icon_path
        
        return None
    
    def browse_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg);;All Files (*)"
        )
        if file_path:
            self.audio_file_input.setText(file_path)
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def browse_local_storage(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Local Storage Directory")
        if dir_path:
            self.local_storage_input.setText(dir_path)
    
    def browse_transcript_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Transcript File", "", 
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.transcript_file_input.setText(file_path)
    
    def on_skip_transcription_changed(self):
        skip_transcription = self.skip_transcription_checkbox.currentText().startswith("Yes")
        
        # Show/hide transcript file selection based on skip transcription option
        for widget in self.transcript_file_row_widgets:
            if skip_transcription:
                widget.show()
            else:
                widget.hide()
    
    def get_default_models(self):
        """Get the default list of AI models"""
        return [
            # AWS Bedrock Models (using inference profiles)
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            "us.anthropic.claude-3-opus-20240229-v1:0",
            "us.anthropic.claude-3-sonnet-20240229-v1:0",
            "us.anthropic.claude-3-haiku-20240307-v1:0",
            "amazon.nova-pro-v1:0",
            "amazon.nova-lite-v1:0",
            "amazon.nova-micro-v1:0",
            "amazon.titan-text-premier-v1:0",
            "meta.llama3-2-90b-instruct-v1:0",
            "meta.llama3-2-11b-instruct-v1:0",
            "meta.llama3-2-3b-instruct-v1:0",
            "meta.llama3-2-1b-instruct-v1:0",
            "meta.llama3-1-405b-instruct-v1:0",
            "meta.llama3-1-70b-instruct-v1:0",
            "meta.llama3-1-8b-instruct-v1:0",
            "mistral.mistral-large-2407-v1:0",
            "mistral.mistral-small-2402-v1:0",
            # Free Models (Ollama)
            "ollama:llama3.2",
            "ollama:llama3.1",
            "ollama:mistral",
            "ollama:codellama",
            "ollama:phi3",
            # Free Models (Hugging Face)
            "hf:microsoft/DialoGPT-large",
            "hf:microsoft/DialoGPT-medium",
            "hf:google/flan-t5-large",
            # Free Models (OpenAI-compatible APIs)
            "openai-free:meta-llama/Llama-2-7b-chat-hf",
            "openai-free:mistralai/Mistral-7B-Instruct-v0.1",
            "openai-free:NousResearch/Nous-Hermes-2-Yi-34B"
        ]
    
    def get_deprecated_models(self):
        """Get list of deprecated/end-of-life models to remove"""
        return [
            # Deprecated AWS Bedrock models
            "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "amazon.titan-text-express-v1",
            "anthropic.claude-v2",
            "anthropic.claude-v2:1",
            "anthropic.claude-instant-v1",
            "anthropic.claude-instant-v1:2",
            "anthropic.claude-v1",
            "anthropic.claude-v1.3",
            "amazon.titan-tg1-large",
            "amazon.titan-text-lite-v1",
            "ai21.j2-grande-instruct",
            "ai21.j2-jumbo-instruct",
            "cohere.command-text-v14",
            "cohere.command-light-text-v14",
            # Add more deprecated models as they become end-of-life
        ]
    
    def clean_deprecated_models(self, models):
        """Remove deprecated models from the list"""
        deprecated = self.get_deprecated_models()
        cleaned_models = [model for model in models if model not in deprecated]
        
        removed_count = len(models) - len(cleaned_models)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} deprecated models from list")
        
        return cleaned_models
    
    def load_model_list(self):
        """Load model list from config or use defaults"""
        config_path = self.get_config_path()
        models = self.get_default_models()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    models = config.get("custom_models", models)
            except Exception as e:
                logger.error(f"Error loading custom models: {e}")
        
        # Clean deprecated models
        original_count = len(models)
        models = self.clean_deprecated_models(models)
        
        # If models were removed, save the cleaned list
        if len(models) < original_count:
            self.save_model_list(models)
        
        self.model_input.clear()
        self.model_input.addItems(models)
    
    def save_model_list(self, models):
        """Save custom model list to config"""
        config_path = self.get_config_path()
        config = {}
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except Exception:
                pass
        
        config["custom_models"] = models
        
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving custom models: {e}")
    
    def manage_models(self):
        """Open model management dialog"""
        from PyQt5.QtWidgets import QDialog, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QInputDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage AI Models")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Model list
        model_list = QListWidget()
        current_models = [self.model_input.itemText(i) for i in range(self.model_input.count())]
        model_list.addItems(current_models)
        layout.addWidget(model_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Model")
        add_button.clicked.connect(lambda: self.add_model(model_list))
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(lambda: self.remove_model(model_list))
        
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(lambda: self.reset_models(model_list))
        
        update_aws_button = QPushButton("Update AWS Models")
        update_aws_button.clicked.connect(lambda: self.update_aws_models(model_list))
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_models(dialog, model_list))
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(update_aws_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec_()
    
    def add_model(self, model_list):
        """Add a new model to the list"""
        from PyQt5.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, 'Add Model', 'Enter model name:')
        if ok and text.strip():
            model_list.addItem(text.strip())
    
    def remove_model(self, model_list):
        """Remove selected model from the list"""
        current_row = model_list.currentRow()
        if current_row >= 0:
            model_list.takeItem(current_row)
    
    def reset_models(self, model_list):
        """Reset model list to defaults"""
        model_list.clear()
        model_list.addItems(self.get_default_models())
    
    def update_aws_models(self, model_list):
        """Fetch latest AWS Bedrock models and add to list"""
        try:
            import boto3
            from PyQt5.QtWidgets import QMessageBox, QProgressDialog
            from PyQt5.QtCore import Qt
            
            # Show progress dialog
            progress = QProgressDialog("Fetching AWS Bedrock models...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Get AWS credentials from the form
            access_key = self.access_key_input.text().strip()
            secret_key = self.secret_key_input.text().strip()
            region = self.region_input.currentText()
            
            if not access_key or not secret_key:
                progress.close()
                QMessageBox.warning(self, "Missing Credentials", "Please enter AWS credentials first.")
                return
            
            # Create Bedrock client
            bedrock = boto3.client(
                'bedrock',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # List foundation models
            response = bedrock.list_foundation_models()
            
            # Extract model IDs for text generation
            new_models = []
            for model in response.get('modelSummaries', []):
                model_id = model.get('modelId', '')
                output_modalities = model.get('outputModalities', [])
                
                # Only include text generation models
                if 'TEXT' in output_modalities and model_id:
                    # Use inference profile format for supported models
                    if model_id.startswith('anthropic.claude'):
                        new_models.append(f"us.{model_id}")
                    else:
                        new_models.append(model_id)
            
            progress.close()
            
            if new_models:
                # Get current models to avoid duplicates
                current_models = [model_list.item(i).text() for i in range(model_list.count())]
                
                # Add new models that aren't already in the list
                added_count = 0
                for model in new_models:
                    if model not in current_models:
                        model_list.addItem(model)
                        added_count += 1
                
                QMessageBox.information(self, "Success", f"Added {added_count} new AWS Bedrock models.")
            else:
                QMessageBox.information(self, "No New Models", "No new AWS Bedrock models found.")
                
        except ImportError:
            QMessageBox.warning(self, "Missing Dependency", "boto3 is required to fetch AWS models. Please install it.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch AWS models: {str(e)}")
    
    def update_env_file(self, config):
        """Update .env file with current settings"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        
        env_mapping = {
            "AWS_ACCESS_KEY_ID": config.get("aws_access_key", ""),
            "AWS_SECRET_ACCESS_KEY": config.get("aws_secret_key", ""),
            "AWS_REGION": config.get("aws_region", "us-east-1"),
            "AWS_S3_BUCKET": config.get("aws_s3_bucket", ""),
            "BEDROCK_MODEL_ID": config.get("bedrock_model", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
            "MODEL_TEMPERATURE": config.get("temperature", "0.7"),
            "MAX_TOKENS": config.get("max_tokens", "4096"),
            "SYSTEM_PROMPT": config.get("system_prompt", "You are an AI assistant that creates detailed meeting notes from transcripts."),
            "TRANSCRIBE_LANGUAGE_CODE": config.get("language_code", "en-US"),
            "ENABLE_SPEAKER_DIARIZATION": "true" if config.get("enable_diarization", True) else "false",
            "MAX_SPEAKER_LABELS": config.get("max_speakers", "10"),
            "LOCAL_STORAGE_DIR": config.get("local_storage_dir", ""),
            "OPENAI_COMPATIBLE_KEY": config.get("openai_compatible_key", "")
        }
        
        try:
            with open(env_path, 'w') as f:
                for key, value in env_mapping.items():
                    f.write(f"{key}={value}\n")
            logger.info(f"Updated .env file: {env_path}")
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
    
    def save_models(self, dialog, model_list):
        """Save the model list and update the combo box"""
        models = [model_list.item(i).text() for i in range(model_list.count())]
        current_selection = self.model_input.currentText()
        
        self.save_model_list(models)
        self.model_input.clear()
        self.model_input.addItems(models)
        
        # Restore selection if it still exists
        index = self.model_input.findText(current_selection)
        if index >= 0:
            self.model_input.setCurrentIndex(index)
        
        dialog.accept()
    
    def get_config_path(self):
        """Get the path to the config file, handling both script and executable modes"""
        if getattr(sys, 'frozen', False):
            # Running as executable
            # Use the user's AppData directory for Windows
            if sys.platform == 'win32':
                app_data = os.environ.get('APPDATA', '')
                if app_data:
                    config_dir = os.path.join(app_data, 'MeetingTranscriber')
                    os.makedirs(config_dir, exist_ok=True)
                    return os.path.join(config_dir, "gui_config.json")
            
            # Fallback to executable directory
            return os.path.join(os.path.dirname(sys.executable), "gui_config.json")
        else:
            # Running as script
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_config.json")
    
    def load_settings(self):
        """Load settings from config file if it exists"""
        config_path = self.get_config_path()
        logger.info(f"Loading settings from: {config_path}")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Load AWS credentials
                self.access_key_input.setText(config.get("aws_access_key", ""))
                self.secret_key_input.setText(config.get("aws_secret_key", ""))
                self.region_input.setCurrentText(config.get("aws_region", "us-east-1"))
                self.s3_bucket_input.setText(config.get("aws_s3_bucket", ""))
                
                # Load Bedrock settings
                self.model_input.setCurrentText(config.get("bedrock_model", "anthropic.claude-3-5-sonnet-20241022-v2:0"))
                self.temperature_input.setText(str(config.get("temperature", "0.7")))
                self.max_tokens_input.setText(str(config.get("max_tokens", "4096")))
                self.system_prompt_input.setText(config.get("system_prompt", "You are an AI assistant that creates detailed meeting notes from transcripts."))
                
                # Load transcription settings
                self.language_input.setCurrentText(config.get("language_code", "en-US"))
                self.diarization_input.setCurrentText("Enabled" if config.get("enable_diarization", True) else "Disabled")
                self.max_speakers_input.setText(str(config.get("max_speakers", "10")))
                
                # Load file paths
                self.output_dir_input.setText(config.get("output_dir", ""))
                self.local_storage_input.setText(config.get("local_storage_dir", ""))
                self.skip_transcription_checkbox.setCurrentText(config.get("skip_transcription", "No - Transcribe audio"))
                self.transcript_file_input.setText(config.get("transcript_file", ""))
                self.openai_compatible_key_input.setText(config.get("openai_compatible_key", ""))
                
                # Update UI visibility based on loaded skip transcription setting
                self.on_skip_transcription_changed()
                
                logger.info("Settings loaded successfully")
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        else:
            logger.info(f"Config file not found at {config_path}, using defaults")
            # Set default system prompt
            self.system_prompt_input.setText("You are an AI assistant that creates detailed meeting notes from transcripts.")
            
            # Try to load from .env file if it exists
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"')
                                
                                if key == "AWS_ACCESS_KEY_ID":
                                    self.access_key_input.setText(value)
                                elif key == "AWS_SECRET_ACCESS_KEY":
                                    self.secret_key_input.setText(value)
                                elif key == "AWS_REGION":
                                    self.region_input.setCurrentText(value)
                                elif key == "AWS_S3_BUCKET":
                                    self.s3_bucket_input.setText(value)
                                elif key == "BEDROCK_MODEL_ID":
                                    self.model_input.setCurrentText(value)
                                elif key == "MODEL_TEMPERATURE":
                                    self.temperature_input.setText(value)
                                elif key == "MAX_TOKENS":
                                    self.max_tokens_input.setText(value)
                                elif key == "SYSTEM_PROMPT":
                                    self.system_prompt_input.setText(value)
                                elif key == "TRANSCRIBE_LANGUAGE_CODE":
                                    self.language_input.setCurrentText(value)
                                elif key == "ENABLE_SPEAKER_DIARIZATION":
                                    self.diarization_input.setCurrentText("Enabled" if value.lower() == "true" else "Disabled")
                                elif key == "MAX_SPEAKER_LABELS":
                                    self.max_speakers_input.setText(value)
                except Exception as e:
                    logger.error(f"Error loading settings from .env: {e}")
    
    def save_settings(self):
        """Save settings to config file"""
        config = {
            "aws_access_key": self.access_key_input.text(),
            "aws_secret_key": self.secret_key_input.text(),
            "aws_region": self.region_input.currentText(),
            "aws_s3_bucket": self.s3_bucket_input.text(),
            "bedrock_model": self.model_input.currentText(),
            "temperature": self.temperature_input.text(),
            "max_tokens": self.max_tokens_input.text(),
            "system_prompt": self.system_prompt_input.toPlainText(),
            "language_code": self.language_input.currentText(),
            "enable_diarization": self.diarization_input.currentText() == "Enabled",
            "max_speakers": self.max_speakers_input.text(),
            "output_dir": self.output_dir_input.text(),
            "local_storage_dir": self.local_storage_input.text(),
            "skip_transcription": self.skip_transcription_checkbox.currentText(),
            "transcript_file": self.transcript_file_input.text(),
            "openai_compatible_key": self.openai_compatible_key_input.text()
        }
        
        config_path = self.get_config_path()
        logger.info(f"Saving settings to: {config_path}")
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Also update .env file
            self.update_env_file(config)
            
            logger.info("Settings saved successfully")
            QMessageBox.information(self, "Settings Saved", f"Settings have been saved successfully to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def show_about(self):
        """Show the About dialog with author information"""
        about_text = """
        <h2>Meeting Transcriber</h2>
        <p><b>Version:</b> 1.1</p>
        <p><b>Date:</b> 12-10-2025</p>
        <p><b>Author:</b> Gianpaolo Albanese</p>
        <p><b>E-Mail:</b> albaneg@yahoo.com</p>
        <p><b>Work Email:</b> gianpaoa@amazon.com</p>
        <p><b>Assisted by:</b> Amazon Q for VS Code</p>
        <p>A tool for transcribing meeting audio and generating detailed meeting notes using AWS services.</p>
        
        <h3>What's New in Version 1.1:</h3>
        <ul>
        <li><b>Skip Transcription:</b> Use existing transcript files for summarization only</li>
        <li><b>30+ AI Models:</b> Support for latest AWS Bedrock models + free alternatives</li>
        <li><b>Free Models:</b> Ollama, Hugging Face, and OpenAI-compatible APIs</li>
        <li><b>Model Management:</b> Add, remove, and update AI models from the UI</li>
        <li><b>Auto-Cleanup:</b> Deprecated models automatically removed on startup</li>
        <li><b>Enhanced Settings:</b> .env file sync and improved backup options</li>
        <li><b>Better Error Handling:</b> Improved retry logic and validation</li>
        </ul>
        """
        
        QMessageBox.about(self, "About Meeting Transcriber", about_text)
    
    def start_transcription(self):
        """Start the transcription process"""
        # Check if transcription should be skipped
        skip_transcription = self.skip_transcription_checkbox.currentText().startswith("Yes")
        
        # Validate inputs
        if not skip_transcription and not self.audio_file_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select an audio file (or enable 'Skip Transcription').")
            return
        
        if skip_transcription and not self.transcript_file_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select a transcript file when skipping transcription.")
            return
        
        if not self.output_dir_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select an output directory.")
            return
        
        # Check transcription method and model for validation
        transcription_method = self.transcription_input.currentText()
        model_id = self.model_input.currentText()
        uses_aws_transcribe = "AWS Transcribe" in transcription_method
        uses_aws_model = not model_id.startswith(('ollama:', 'hf:', 'openai-free:'))
        
        # Validate AWS credentials if using AWS services
        if uses_aws_transcribe or uses_aws_model:
            if not self.access_key_input.text() or not self.secret_key_input.text():
                QMessageBox.warning(self, "Missing Credentials", "Please enter AWS access key and secret key for AWS services.")
                return
            if uses_aws_transcribe and not self.s3_bucket_input.text():
                QMessageBox.warning(self, "Missing Input", "Please enter an S3 bucket name for AWS Transcribe.")
                return
        
        # Validate local storage for free models
        if not uses_aws_model and not self.local_storage_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select a local storage directory for free models.")
            return
        
        # Collect AWS credentials
        aws_credentials = {
            "access_key": self.access_key_input.text(),
            "secret_key": self.secret_key_input.text(),
            "region": self.region_input.currentText(),
            "s3_bucket": self.s3_bucket_input.text()
        }
        
        # Collect AWS settings
        aws_settings = {
            "model_id": self.model_input.currentText(),
            "temperature": self.temperature_input.text(),
            "max_tokens": self.max_tokens_input.text(),
            "system_prompt": self.system_prompt_input.toPlainText(),
            "language_code": self.language_input.currentText(),
            "enable_diarization": self.diarization_input.currentText() == "Enabled",
            "max_speakers": self.max_speakers_input.text(),
            "local_storage_dir": self.local_storage_input.text(),
            "transcription_method": self.transcription_input.currentText(),
            "openai_compatible_key": self.openai_compatible_key_input.text()
        }
        
        # Clear log output
        self.log_output.clear()
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        
        # Disable start button
        self.start_button.setEnabled(False)
        
        # Check if transcription should be skipped
        skip_transcription = self.skip_transcription_checkbox.currentText().startswith("Yes")
        
        # Create and start worker thread
        self.worker = TranscriptionWorker(
            self.audio_file_input.text(),
            self.output_dir_input.text(),
            aws_credentials,
            aws_settings,
            skip_transcription,
            self.transcript_file_input.text() if skip_transcription else None
        )
        self.worker.progress_update.connect(self.update_log)
        self.worker.finished_signal.connect(self.transcription_finished)
        self.worker.start()
    
    def update_log(self, message):
        """Update the log output with a new message"""
        self.log_output.append(message)
        # Scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def transcription_finished(self, success, message):
        """Handle transcription completion"""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Enable start button
        self.start_button.setEnabled(True)
        
        # Show message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

def create_desktop_shortcut():
    """Create a desktop shortcut for the application with the custom icon"""
    try:
        # Only for Windows
        if sys.platform != 'win32':
            return
            
        import winshell
        from win32com.client import Dispatch
        
        # Get the path to the executable
        if getattr(sys, 'frozen', False):
            # Running as executable
            exe_path = sys.executable
        else:
            # Running as script
            exe_path = os.path.abspath(sys.argv[0])
        
        # Get the desktop path
        desktop = winshell.desktop()
        
        # Create shortcut path
        shortcut_path = os.path.join(desktop, "Meeting Transcriber.lnk")
        
        # Create the shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        
        # Set icon path
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
            
        shortcut.save()
        logger.info(f"Desktop shortcut created at: {shortcut_path}")
    except Exception as e:
        logger.error(f"Failed to create desktop shortcut: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application icon for taskbar
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create desktop shortcut if running as executable
    if getattr(sys, 'frozen', False):
        try:
            create_desktop_shortcut()
        except Exception as e:
            logger.error(f"Error creating desktop shortcut: {e}")
    
    # Show splash screen
    try:
        from splash_screen import show_splash
        splash = show_splash(app, 3000)  # Show for 3 seconds
    except Exception as e:
        logger.error(f"Error showing splash screen: {e}")
        splash = None
    
    # Create and show the main window
    window = MeetingTranscriberGUI()
    window.show()
    
    # If splash screen is shown, make sure it stays on top until closed
    if splash and splash.isVisible():
        splash.finish(window)
    
    sys.exit(app.exec_())