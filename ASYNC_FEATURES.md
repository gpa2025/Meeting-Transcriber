# Async Features for Meeting Transcriber

This document describes the new asynchronous features added to the Meeting Transcriber application.

## Overview

The async features transform the Meeting Transcriber from a blocking, single-task application into a responsive, multi-task processing system with real-time progress updates and cancellation support.

## Key Features

### 🚀 **Non-Blocking Processing**
- Transcription runs in background without freezing the UI
- Users can interact with the application while processing
- Multiple transcriptions can run concurrently

### 📊 **Real-Time Progress Updates**
- Live progress bars showing transcription and summarization progress
- Detailed status messages for each processing step
- Time elapsed tracking for each task

### ❌ **Task Cancellation**
- Cancel individual tasks or all active tasks
- Graceful cleanup of AWS resources when cancelled
- Immediate UI feedback when cancellation occurs

### 🔄 **Concurrent Processing**
- Process multiple audio files simultaneously
- Configurable maximum concurrent tasks (1-5)
- Intelligent resource management to avoid API throttling

### 📋 **Task Queue Management**
- Visual task list showing all active, completed, and failed tasks
- Add multiple files to processing queue
- Clear completed tasks to keep interface clean

### 💾 **Enhanced Settings Management**
- Auto-save settings between sessions
- Performance tuning options
- Notification preferences

## Architecture

### Core Components

1. **AsyncTranscriber** (`async_transcriber.py`)
   - Main async processing engine
   - Handles task lifecycle management
   - Provides progress callbacks and cancellation

2. **AsyncGUIIntegration** (`async_gui_integration.py`)
   - Bridges PyQt5 GUI with async processing
   - Manages event loops and thread safety
   - Provides progress widgets and task management

3. **EnhancedGUI** (`meeting_transcriber_gui_async.py`)
   - Complete GUI with tabbed interface
   - Real-time progress monitoring
   - Advanced settings and configuration

### Data Flow

```
User Input → Task Creation → Async Processing → Progress Updates → UI Updates
     ↓              ↓              ↓               ↓              ↓
  Validation → Task Queue → Background Thread → Callbacks → Visual Feedback
```

## Installation

### 1. Install Async Dependencies

```bash
pip install -r requirements_async.txt
```

### 2. Test Async Features

```bash
python test_async_features.py
```

### 3. Run Enhanced GUI

```bash
python meeting_transcriber_gui_async.py
```

## Usage Guide

### Basic Workflow

1. **Launch Application**
   ```bash
   python meeting_transcriber_gui_async.py
   ```

2. **Configure Settings**
   - Go to "Settings" tab
   - Set AWS credentials (for Bedrock models) or configure free models
   - Adjust performance settings as needed

3. **Start Transcription**
   - Select audio file and output directory
   - Choose AI model and transcription settings
   - Click "Start Transcription" or "Add to Queue"

4. **Monitor Progress**
   - Switch to "Progress Monitor" tab
   - Watch real-time progress updates
   - Cancel tasks if needed

5. **Review Results**
   - Completed tasks show success status
   - Output folder opens automatically (if enabled)
   - Check activity log for detailed information

### Advanced Features

#### Batch Processing
```python
# Add multiple files to queue
for audio_file in audio_files:
    # Configure settings for each file
    # Click "Add to Queue"
    pass
```

#### Custom Progress Callbacks
```python
def my_progress_callback(update: ProgressUpdate):
    print(f"Task {update.task_id}: {update.progress_percent}%")
    
transcriber = AsyncTranscriber(progress_callback=my_progress_callback)
```

#### Task Management
```python
# Start task
task_id = await transcriber.start_transcription(task)

# Check status
status = await transcriber.get_task_status(task_id)

# Cancel task
cancelled = await transcriber.cancel_task(task_id)

# Wait for completion
result = await transcriber.wait_for_task(task_id)
```

## Configuration Options

### Performance Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Max Concurrent Tasks | 2 | Maximum number of simultaneous transcriptions |
| Thread Pool Size | 3 | Number of worker threads for blocking operations |
| Progress Update Interval | 2 seconds | How often to check transcription progress |

### UI Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Auto-save Settings | Enabled | Automatically save configuration |
| Show Notifications | Enabled | Display completion notifications |
| Auto-open Folder | Enabled | Open output folder when complete |

## API Reference

### AsyncTranscriber Class

#### Methods

- `start_transcription(task: TranscriptionTask) -> str`
  - Start async transcription task
  - Returns task ID for tracking

- `cancel_task(task_id: str) -> bool`
  - Cancel running task
  - Returns True if successfully cancelled

- `get_task_status(task_id: str) -> TaskStatus`
  - Get current task status
  - Returns status enum value

- `wait_for_task(task_id: str) -> Any`
  - Wait for task completion
  - Returns task result

#### Events

- `progress_callback(update: ProgressUpdate)`
  - Called for each progress update
  - Provides real-time status information

### ProgressUpdate Structure

```python
@dataclass
class ProgressUpdate:
    task_id: str                    # Unique task identifier
    status: TaskStatus              # Current status (PENDING, RUNNING, etc.)
    progress_percent: float         # Progress percentage (0-100)
    message: str                    # Human-readable status message
    timestamp: datetime             # When update occurred
    details: Optional[Dict] = None  # Additional details
```

### TaskStatus Enum

- `PENDING` - Task queued but not started
- `RUNNING` - Task currently processing
- `COMPLETED` - Task finished successfully
- `FAILED` - Task encountered an error
- `CANCELLED` - Task was cancelled by user

## Error Handling

### Common Issues

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'aiohttp'
   ```
   **Solution:** Install async requirements
   ```bash
   pip install -r requirements_async.txt
   ```

2. **Event Loop Errors**
   ```
   RuntimeError: There is no current event loop
   ```
   **Solution:** Ensure AsyncEventLoop is properly initialized

3. **Task Cancellation Issues**
   ```
   Task was destroyed but it is pending!
   ```
   **Solution:** Always call `shutdown()` before closing application

### Best Practices

1. **Always Shutdown Properly**
   ```python
   try:
       # Use transcriber
       pass
   finally:
       await transcriber.shutdown()
   ```

2. **Handle Cancellation Gracefully**
   ```python
   try:
       result = await transcriber.wait_for_task(task_id)
   except asyncio.CancelledError:
       print("Task was cancelled")
   ```

3. **Monitor Resource Usage**
   - Limit concurrent tasks to avoid API throttling
   - Use appropriate thread pool sizes
   - Clean up completed tasks regularly

## Performance Considerations

### Memory Usage
- Each active task uses ~50-100MB of memory
- Completed task results are cached until cleanup
- Large audio files may require more memory

### API Rate Limits
- AWS Bedrock: ~20 requests/minute per model
- AWS Transcribe: ~100 concurrent jobs
- Free APIs: Varies by provider

### Optimization Tips
1. Use appropriate concurrent task limits
2. Clean up completed tasks regularly
3. Monitor system resources during batch processing
4. Use local models (Ollama) for unlimited processing

## Troubleshooting

### Debug Mode
Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Solutions

1. **GUI Not Responding**
   - Check if async event loop is running
   - Verify PyQt5 installation
   - Look for blocking operations in main thread

2. **Tasks Not Starting**
   - Verify AWS credentials (for Bedrock models)
   - Check network connectivity
   - Ensure audio file exists and is readable

3. **Progress Updates Missing**
   - Confirm progress callback is set
   - Check for exceptions in callback function
   - Verify task ID matches

## Future Enhancements

### Planned Features
- [ ] Batch file processing with drag-and-drop
- [ ] Progress persistence across application restarts
- [ ] Advanced scheduling and priority queues
- [ ] Integration with cloud storage services
- [ ] Real-time collaboration features

### Performance Improvements
- [ ] Streaming transcription for large files
- [ ] Intelligent caching of model responses
- [ ] Adaptive concurrency based on system resources
- [ ] Background processing service

## Contributing

To contribute to the async features:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/async-enhancement`
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd meeting-transcriber

# Switch to async branch
git checkout async_feature

# Install development dependencies
pip install -r requirements_async.txt
pip install pytest pytest-asyncio

# Run tests
python test_async_features.py
pytest tests/
```

## License

This async feature enhancement maintains the same license as the main Meeting Transcriber project.

---

**Note:** The async features require Python 3.7+ and are designed to be backward compatible with the existing synchronous implementation.