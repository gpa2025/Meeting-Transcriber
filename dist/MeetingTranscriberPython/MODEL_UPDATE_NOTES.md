# Model Update Notes

## Changes Made

### Updated Model List
Replaced deprecated models with current AWS Bedrock supported models:

**Removed (End of Support):**
- `anthropic.claude-v2`
- `anthropic.claude-instant-v1`

**Added (Current Models):**
- `anthropic.claude-3-5-sonnet-20241022-v2:0` (Latest Claude 3.5 Sonnet)
- `anthropic.claude-3-5-sonnet-20240620-v1:0`
- `anthropic.claude-3-5-haiku-20241022-v1:0`
- `anthropic.claude-3-opus-20240229-v1:0`
- `anthropic.claude-3-sonnet-20240229-v1:0`
- `anthropic.claude-3-haiku-20240307-v1:0`
- `amazon.nova-pro-v1:0` (New Amazon Nova models)
- `amazon.nova-lite-v1:0`
- `amazon.nova-micro-v1:0`
- `amazon.titan-text-premier-v1:0`
- `meta.llama3-2-90b-instruct-v1:0` (Meta Llama 3.2 models)
- `meta.llama3-2-11b-instruct-v1:0`
- `meta.llama3-2-3b-instruct-v1:0`
- `meta.llama3-2-1b-instruct-v1:0`
- `meta.llama3-1-405b-instruct-v1:0` (Meta Llama 3.1 models)
- `meta.llama3-1-70b-instruct-v1:0`
- `meta.llama3-1-8b-instruct-v1:0`
- `mistral.mistral-large-2407-v1:0` (Mistral models)
- `mistral.mistral-small-2402-v1:0`

### API Format Updates

**Claude 3+ Models:**
- Updated to use Messages API format with `anthropic_version: "bedrock-2023-05-31"`
- Changed from `prompt` to `messages` array format
- Updated response parsing to handle `content[0].text` structure

**Amazon Nova Models:**
- Added support for new Nova model family
- Uses same API format as Titan models

**Meta Llama Models:**
- Added specific API format with `max_gen_len` parameter
- Uses `generation` field in response

**Mistral Models:**
- Added support with `max_tokens` parameter
- Uses `outputs[0].text` for response parsing

### Default Model Change
- Changed default model from `anthropic.claude-v2` to `anthropic.claude-3-5-sonnet-20241022-v2:0`

## Files Modified
1. `meeting_transcriber_gui.py` - Updated model dropdown list and default model
2. `summarizer_bedrock.py` - Updated API calls and response parsing for new models

## Benefits
- Access to latest and most capable models
- Better performance and accuracy
- Future-proofed against model deprecations
- Support for multiple model providers (Anthropic, Amazon, Meta, Mistral)

## Migration Notes
- Existing configurations will automatically use the new default model
- Users can select their preferred model from the expanded list
- All new API formats are backward compatible with existing functionality