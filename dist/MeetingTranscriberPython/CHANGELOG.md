# Changelog

## [2.0.0] - 2024-12-19

### Added
- **Free Models Support**: Added support for 15+ free AI models
  - Ollama integration for local processing (Llama 3.2, Mistral, CodeLlama, Phi-3)
  - Hugging Face Inference API support (DialoGPT, Flan-T5)
  - OpenAI-compatible free APIs (Together AI, Anyscale, etc.)
- **New summarizer_free.py module** for handling free model integrations
- **Comprehensive setup guides** for all free model providers
- **Environment variable support** for free model configuration

### Updated
- **Model List**: Replaced deprecated models with 20+ current AWS Bedrock models
  - Added Claude 3.5 Sonnet (latest), Claude 3 Opus/Sonnet/Haiku
  - Added Amazon Nova Pro/Lite/Micro models
  - Added Meta Llama 3.1 and 3.2 models (multiple sizes)
  - Added Mistral Large and Small models
- **API Integration**: Updated to support Claude 3+ Messages API format
- **Default Model**: Changed from deprecated Claude v2 to Claude 3.5 Sonnet
- **Documentation**: Comprehensive updates to README.md with free model setup

### Removed
- **Deprecated Models**: Removed end-of-support models
  - anthropic.claude-v2
  - anthropic.claude-instant-v1

### Technical Improvements
- **Automatic Model Detection**: App automatically uses correct API based on model selection
- **Enhanced Error Handling**: Better error messages for different model types
- **Flexible Configuration**: Support for both premium and free model workflows

### Files Added
- `summarizer_free.py` - Free models integration
- `FREE_MODELS_SETUP.md` - Setup guide for free models
- `MODEL_UPDATE_NOTES.md` - Documentation of model changes
- `requirements_free.txt` - Additional dependencies
- `CHANGELOG.md` - This changelog

### Migration Notes
- Existing users: App will automatically use new default model
- AWS users: No action required, all existing functionality preserved
- New users: Can now choose between premium AWS models or free alternatives
- Cost-conscious users: Can run completely free with Ollama local models

## [1.1.0] - 2024-09-05

### Initial Release
- AWS Transcribe integration
- AWS Bedrock integration (Claude v2, Titan)
- Speaker diarization support
- GUI interface with PyQt5
- Meeting notes generation and formatting