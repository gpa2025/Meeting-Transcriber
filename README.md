# Meeting Transcriber

A tool for transcribing meeting audio and generating detailed meeting notes using AWS services.

## Features

- Transcribe audio files using AWS Transcribe
- Generate detailed meeting notes using AWS Bedrock
- Speaker diarization (identify different speakers)
- GUI interface for easy use
- Save and load settings

## Requirements

- Python 3.7+
- AWS Account with access to:
  - AWS Transcribe
  - AWS S3
  - AWS Bedrock
- AWS credentials with appropriate permissions

## Installation

### Option 1: Using the Executable (Windows)

1. Download the latest release from the releases page
2. Run `MeetingTranscriber.exe`

### Option 2: From Source

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the GUI:
   ```
   python meeting_transcriber_gui.py
   ```

## Building the Executable

To build the executable yourself:

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   pip install pyinstaller pillow
   ```

2. Run the build script:
   ```
   python build_exe.py
   ```

3. The executable will be created in the `dist` folder

## Usage

1. Enter your AWS credentials (Access Key, Secret Key)
2. Specify the AWS region and S3 bucket
3. Configure Bedrock settings (model, temperature, etc.)
4. Select the audio file to transcribe
5. Choose an output directory
6. Click "Start Transcription"

## Configuration

You can save your settings (except AWS credentials) for future use by clicking the "Save Settings" button.

## Output Files

The tool generates the following files in the output directory:

- `{filename}_transcript.txt`: Raw transcript
- `{filename}_transcript_with_speakers.txt`: Transcript with speaker labels
- `{filename}_meeting_notes.md`: Formatted meeting notes

## License

MIT