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
                            QGroupBox, QFormLayout, QMessageBox, QTextEdit, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

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
    
    def __init__(self, audio_file, output_dir, aws_credentials, aws_settings):
        super().__init__()
        self.audio_file = audio_file
        self.output_dir = output_dir
        self.aws_credentials = aws_credentials
        self.aws_settings = aws_settings
        
    def run(self):
        try:
            # Create a temporary .env file with the credentials
            env_file = self._create_temp_env_file()
            
            # Run the main.py script as a subprocess
            cmd = [
                sys.executable, 
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"),
                "--audio", self.audio_file,
                "--output", self.output_dir
            ]
            
            # Set environment variables for the subprocess
            env = os.environ.copy()
            env.update({
                "AWS_ACCESS_KEY_ID": self.aws_credentials["access_key"],
                "AWS_SECRET_ACCESS_KEY": self.aws_credentials["secret_key"],
                "AWS_REGION": self.aws_credentials["region"],
                "AWS_S3_BUCKET": self.aws_credentials["s3_bucket"],
                "BEDROCK_MODEL_ID": self.aws_settings["model_id"],
                "MODEL_TEMPERATURE": self.aws_settings["temperature"],
                "MAX_TOKENS": self.aws_settings["max_tokens"],
                "SYSTEM_PROMPT": self.aws_settings["system_prompt"],
                "TRANSCRIBE_LANGUAGE_CODE": self.aws_settings["language_code"],
                "ENABLE_SPEAKER_DIARIZATION": "true" if self.aws_settings["enable_diarization"] else "false",
                "MAX_SPEAKER_LABELS": self.aws_settings["max_speakers"]
            })
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env
            )
            
            # Stream the output
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.progress_update.emit(line.strip())
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.finished_signal.emit(True, "Transcription and summarization completed successfully!")
            else:
                self.finished_signal.emit(False, f"Process failed with return code {return_code}")
                
        except Exception as e:
            logger.error(f"Error in transcription worker: {e}")
            self.finished_signal.emit(False, f"Error: {str(e)}")
    
    def _create_temp_env_file(self):
        """Create a temporary .env file with the credentials"""
        temp_env = tempfile.NamedTemporaryFile(delete=False, mode='w')
        temp_env.write(f"# AWS Credentials\n")
        temp_env.write(f"AWS_ACCESS_KEY_ID={self.aws_credentials['access_key']}\n")
        temp_env.write(f"AWS_SECRET_ACCESS_KEY={self.aws_credentials['secret_key']}\n")
        temp_env.write(f"AWS_REGION={self.aws_credentials['region']}\n")
        temp_env.write(f"AWS_S3_BUCKET={self.aws_credentials['s3_bucket']}\n\n")
        
        temp_env.write(f"# AWS Bedrock Settings\n")
        temp_env.write(f"BEDROCK_MODEL_ID={self.aws_settings['model_id']}\n\n")
        
        temp_env.write(f"# AI Model Settings\n")
        temp_env.write(f"MODEL_TEMPERATURE={self.aws_settings['temperature']}\n")
        temp_env.write(f"MAX_TOKENS={self.aws_settings['max_tokens']}\n")
        temp_env.write(f"SYSTEM_PROMPT=\"{self.aws_settings['system_prompt']}\"\n\n")
        
        temp_env.write(f"# Transcription Settings\n")
        temp_env.write(f"TRANSCRIBE_LANGUAGE_CODE={self.aws_settings['language_code']}\n")
        temp_env.write(f"ENABLE_SPEAKER_DIARIZATION={'true' if self.aws_settings['enable_diarization'] else 'false'}\n")
        temp_env.write(f"MAX_SPEAKER_LABELS={self.aws_settings['max_speakers']}\n")
        
        temp_env.close()
        return temp_env.name

class MeetingTranscriberGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_settings()
        
    def initUI(self):
        self.setWindowTitle('Meeting Transcriber')
        self.setGeometry(100, 100, 800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # AWS Credentials Group
        aws_group = QGroupBox("AWS Credentials")
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
        
        # Bedrock Settings Group
        bedrock_group = QGroupBox("Bedrock Settings")
        bedrock_layout = QFormLayout()
        
        self.model_input = QComboBox()
        self.model_input.addItems([
            "anthropic.claude-v2",
            "anthropic.claude-instant-v1",
            "amazon.titan-text-express-v1"
        ])
        self.temperature_input = QLineEdit("0.7")
        self.max_tokens_input = QLineEdit("4096")
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText("Enter system prompt here...")
        self.system_prompt_input.setMaximumHeight(100)
        
        bedrock_layout.addRow("Model:", self.model_input)
        bedrock_layout.addRow("Temperature:", self.temperature_input)
        bedrock_layout.addRow("Max Tokens:", self.max_tokens_input)
        bedrock_layout.addRow("System Prompt:", self.system_prompt_input)
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
        
        file_layout.addRow("Audio File:", audio_file_layout)
        file_layout.addRow("Output Directory:", output_dir_layout)
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
        button_layout.addWidget(self.save_settings_button)
        button_layout.addWidget(self.start_button)
        
        # Add all groups to main layout
        main_layout.addWidget(aws_group)
        main_layout.addWidget(bedrock_group)
        main_layout.addWidget(transcription_group)
        main_layout.addWidget(file_group)
        main_layout.addWidget(progress_group)
        main_layout.addLayout(button_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
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
    
    def load_settings(self):
        """Load settings from config file if it exists"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_config.json")
        
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
                self.model_input.setCurrentText(config.get("bedrock_model", "anthropic.claude-v2"))
                self.temperature_input.setText(str(config.get("temperature", "0.7")))
                self.max_tokens_input.setText(str(config.get("max_tokens", "4096")))
                self.system_prompt_input.setText(config.get("system_prompt", "You are an AI assistant that creates detailed meeting notes from transcripts."))
                
                # Load transcription settings
                self.language_input.setCurrentText(config.get("language_code", "en-US"))
                self.diarization_input.setCurrentText("Enabled" if config.get("enable_diarization", True) else "Disabled")
                self.max_speakers_input.setText(str(config.get("max_speakers", "10")))
                
                # Load file paths
                self.output_dir_input.setText(config.get("output_dir", ""))
                
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
        else:
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
            "output_dir": self.output_dir_input.text()
        }
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui_config.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
    
    def start_transcription(self):
        """Start the transcription process"""
        # Validate inputs
        if not self.audio_file_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select an audio file.")
            return
        
        if not self.output_dir_input.text():
            QMessageBox.warning(self, "Missing Input", "Please select an output directory.")
            return
        
        if not self.access_key_input.text() or not self.secret_key_input.text():
            QMessageBox.warning(self, "Missing Credentials", "Please enter AWS access key and secret key.")
            return
        
        if not self.s3_bucket_input.text():
            QMessageBox.warning(self, "Missing Input", "Please enter an S3 bucket name.")
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
            "max_speakers": self.max_speakers_input.text()
        }
        
        # Clear log output
        self.log_output.clear()
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        
        # Disable start button
        self.start_button.setEnabled(False)
        
        # Create and start worker thread
        self.worker = TranscriptionWorker(
            self.audio_file_input.text(),
            self.output_dir_input.text(),
            aws_credentials,
            aws_settings
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeetingTranscriberGUI()
    window.show()
    sys.exit(app.exec_())