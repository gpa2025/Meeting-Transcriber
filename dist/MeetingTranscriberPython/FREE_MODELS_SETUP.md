# Free Models Setup Guide

## Available Free Models

### 1. Ollama (Local Models)
**Setup:**
1. Install Ollama: https://ollama.ai/
2. Pull models: `ollama pull llama3.2`
3. Start Ollama service
4. Set environment variable: `OLLAMA_URL=http://localhost:11434`

**Available Models:**
- `ollama:llama3.2` - Latest Llama model
- `ollama:llama3.1` - Previous Llama version
- `ollama:mistral` - Mistral 7B
- `ollama:codellama` - Code-focused model
- `ollama:phi3` - Microsoft Phi-3

### 2. Hugging Face Inference API
**Setup:**
1. Create account at https://huggingface.co/
2. Get free API token from settings
3. Set environment variable: `HF_TOKEN=your_token_here`

**Available Models:**
- `hf:microsoft/DialoGPT-large` - Conversational AI
- `hf:microsoft/DialoGPT-medium` - Smaller conversational model
- `hf:google/flan-t5-large` - Google's instruction-tuned model

### 3. OpenAI-Compatible Free APIs
**Setup:**
1. Sign up for free tier at providers like:
   - Together AI (https://together.ai/)
   - Anyscale (https://anyscale.com/)
   - Fireworks AI (https://fireworks.ai/)
2. Get API key
3. Set environment variables:
   - `OPENAI_COMPATIBLE_URL=https://api.together.xyz/v1`
   - `OPENAI_COMPATIBLE_KEY=your_api_key`

**Available Models:**
- `openai-free:meta-llama/Llama-2-7b-chat-hf`
- `openai-free:mistralai/Mistral-7B-Instruct-v0.1`
- `openai-free:NousResearch/Nous-Hermes-2-Yi-34B`

## Environment Variables

Add these to your `.env` file for free models:

```env
# For Ollama
OLLAMA_URL=http://localhost:11434

# For Hugging Face
HF_TOKEN=your_huggingface_token

# For OpenAI-compatible APIs
OPENAI_COMPATIBLE_URL=https://api.together.xyz/v1
OPENAI_COMPATIBLE_KEY=your_api_key

# Model selection (choose one)
BEDROCK_MODEL_ID=ollama:llama3.2
# or
BEDROCK_MODEL_ID=hf:microsoft/DialoGPT-large
# or
BEDROCK_MODEL_ID=openai-free:meta-llama/Llama-2-7b-chat-hf
```

## Benefits of Free Models

- **No AWS costs** - Use local or free tier APIs
- **Privacy** - Ollama runs completely locally
- **Experimentation** - Try different models without cost
- **Offline capability** - Ollama works without internet

## Limitations

- **Quality** - May not match premium models like Claude 3.5
- **Context length** - Shorter than premium models
- **Rate limits** - Free APIs have usage restrictions
- **Setup complexity** - Requires additional configuration

## Recommended Setup

1. **Start with Ollama** for privacy and offline use
2. **Use Hugging Face** for cloud-based free option
3. **Try OpenAI-compatible** for access to larger models

## Troubleshooting

**Ollama not responding:**
- Check if Ollama service is running
- Verify model is downloaded: `ollama list`
- Check URL in environment variable

**Hugging Face errors:**
- Verify token is valid
- Check model availability
- Some models may be loading (try again in a few minutes)

**OpenAI-compatible API errors:**
- Verify API key and URL
- Check rate limits
- Ensure model name is correct for the provider