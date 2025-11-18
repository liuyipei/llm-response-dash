# LLM Message Format Explorer

A comprehensive Streamlit web application to explore and understand LLM messaging formats across providers and models, with special focus on reasoning tokens and tool calling.

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google Gemini, DeepSeek, Qwen, Moonshot, OpenRouter, Fireworks, LiteLLM
- **Reasoning Token Detection**: Automatically detects and displays reasoning/thinking content
- **Tool Calling Examples**: Test tool calling with 5 example functions
- **JSON Inspection**: View complete request and response JSON
- **Parsed Field Extraction**: See how reasoning and tool calls are extracted
- **Example Prompts**: Pre-loaded prompts for reasoning and tool calling

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone the repository:**
```bash
cd llm-message-explorer
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up API keys** (optional - can enter in UI):
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
DEEPSEEK_API_KEY=your-deepseek-key
QWEN_API_KEY=your-qwen-key
MOONSHOT_API_KEY=your-moonshot-key
OPENROUTER_API_KEY=your-openrouter-key
FIREWORKS_API_KEY=your-fireworks-key
LITELLM_API_KEY=your-litellm-key
EOF
```

## Usage

### Running the App

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

### Using the Interface

1. **Select Provider**: Choose from the dropdown in the sidebar
2. **Enter API Key**: Paste your API key (or it will use environment variable)
3. **Select Model**: Choose a model from the provider
4. **Configure Parameters**:
   - Temperature: Controls randomness (0 = deterministic)
   - Max Tokens: Maximum response length
   - Enable Tool Calling: Include example tools
   - Enable Reasoning: Activate reasoning mode (if supported)
5. **Enter Prompt**: Use example prompts or write your own
6. **Send Request**: Click the button to make the API call
7. **Explore Results**:
   - **Response Tab**: User-friendly display
   - **Request JSON Tab**: Full request object
   - **Response JSON Tab**: Full response object
   - **Parsed Fields Tab**: Extracted reasoning and tool calls

### Example Workflows

#### Testing Reasoning Models

1. Select "DeepSeek" provider
2. Choose "deepseek-reasoner" model
3. Enable "Enable Reasoning" checkbox
4. Select example: "Think step by step: Why is the sky blue?"
5. Click "Send Request"
6. View reasoning tokens in "Parsed Fields" tab

#### Testing Tool Calling

1. Select "OpenAI" provider
2. Choose "gpt-4o" model
3. Enable "Enable Tool Calling" checkbox
4. Select example: "What's the weather in San Francisco and what time is it there?"
5. Click "Send Request"
6. View tool calls in "Parsed Fields" tab

#### Comparing Formats

1. Run same prompt on Anthropic Claude
2. Run same prompt on OpenAI GPT-4o
3. Compare the "Response JSON" tabs
4. Notice differences in reasoning token structure

## Understanding the Output

### Reasoning Token Formats

Different providers expose reasoning tokens differently:

**Anthropic:**
```json
{
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me analyze step by step...",
      "signature": "base64_signature"
    }
  ]
}
```

**OpenAI (o-series):**
```json
{
  "choices": [
    {
      "message": {
        "reasoning_content": "Step 1: First I need to...",
        "content": "The answer is 42."
      }
    }
  ]
}
```

**Fireworks:**
```json
{
  "choices": [
    {
      "message": {
        "content": "<think>\nAnalyzing the problem...\n</think>\nThe answer is 42."
      }
    }
  ]
}
```

### Tool Call Formats

**Anthropic:**
```json
{
  "type": "tool_use",
  "id": "toolu_01ABC",
  "name": "calculator",
  "input": {
    "expression": "2 + 2"
  }
}
```

**OpenAI:**
```json
{
  "tool_calls": [
    {
      "id": "call_ABC123",
      "type": "function",
      "function": {
        "name": "calculator",
        "arguments": "{\"expression\": \"2 + 2\"}"
      }
    }
  ]
}
```

**Google Gemini:**
```json
{
  "functionCall": {
    "name": "calculator",
    "args": {
      "expression": "2 + 2"
    }
  }
}
```

## Supported Providers

### Direct Providers

- **OpenAI**: GPT-4o, o-series reasoning models
- **Anthropic**: Claude 3.7, 4, 4.5 with extended thinking
- **Google Gemini**: Gemini 2.5 Pro with thinking config
- **DeepSeek**: DeepSeek-R1 reasoning model
- **Alibaba (Qwen)**: Qwen3 Thinking models
- **Moonshot (Kimi)**: Kimi K2 with reasoning

### Aggregators & Platforms

- **OpenRouter**: Multi-provider routing with cost tracking
- **Fireworks**: Inference platform with OpenAI compatibility
- **LiteLLM**: Unified API translation layer

## Example Tools

The app includes 5 example tools for testing:

1. **calculator**: Perform arithmetic calculations
2. **get_current_time**: Get time in specified timezone
3. **search_web**: Web search (placeholder)
4. **get_weather**: Weather information (placeholder)
5. **get_random_number**: Generate random number

These are non-functional placeholders designed to show how tools are called.

## Documentation

See [LLM_Provider_Message_Format_Analysis.md](./LLM_Provider_Message_Format_Analysis.md) for:
- Comprehensive format comparison tables
- Request/response schemas for each provider
- Reasoning token extraction code examples
- Tool calling patterns and parsing logic
- Migration guide for integrating new providers
- Real API response examples

## Troubleshooting

### API Key Errors

**Error:** "API key is required"
- **Solution**: Enter your API key in the sidebar or set environment variable

### Invalid Model

**Error:** Model not found
- **Solution**: Check that you're using the correct model name for the provider

### Reasoning Not Working

**Issue:** No reasoning tokens appear
- **Check**: Model supports reasoning (see documentation)
- **Check**: "Enable Reasoning" checkbox is checked
- **Note**: Some models require specific parameters (see documentation)

### Tool Calls Not Appearing

**Issue:** Tools not called
- **Check**: "Enable Tool Calling" is checked
- **Check**: Prompt actually requests tool usage
- **Try**: Use example prompts from "Tool Calling" category
- **Note**: Reasoning models may not support tools

### Streaming Errors

**Error:** Streaming failed
- **Solution**: The app uses non-streaming by default for simplicity
- **Note**: Streaming support can be added (see code comments)

## Technical Details

### Architecture

```
app.py
├── Provider Configuration (PROVIDERS dict)
├── Tool Definitions (EXAMPLE_TOOLS)
├── Client Initialization
│   ├── get_openai_client()
│   ├── get_anthropic_client()
│   └── get_gemini_client()
├── Request Building
│   └── make_request()
├── Response Parsing
│   ├── extract_reasoning_tokens()
│   └── extract_tool_calls()
└── Streamlit UI
    ├── Sidebar (config)
    ├── Prompt Input
    └── Results Display
```

### Adding a New Provider

1. Add to `PROVIDERS` dict:
```python
"NewProvider": {
    "base_url": "https://api.newprovider.com/v1",
    "models": ["model-1", "model-2"],
    "supports_reasoning": True,
    "supports_tools": True,
    "api_key_env": "NEWPROVIDER_API_KEY"
}
```

2. Add client initialization if needed:
```python
def get_newprovider_client(api_key: str):
    return NewProviderClient(api_key=api_key)
```

3. Add to `make_request()`:
```python
elif provider == "NewProvider":
    client = get_newprovider_client(api_key)
    # Build request and handle response
```

4. Add to `extract_reasoning_tokens()` and `extract_tool_calls()`:
```python
elif provider == "NewProvider":
    # Extract reasoning based on provider's format
```

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Add streaming support
- [ ] Add more providers
- [ ] Add model auto-detection from API
- [ ] Add conversation history
- [ ] Add export functionality
- [ ] Add side-by-side provider comparison
- [ ] Add prompt library
- [ ] Add cost estimation

## License

MIT License - feel free to use and modify

## Related Projects

- **Cline**: VSCode extension using similar provider handling
  - https://github.com/liuyipei/cline
- **LiteLLM**: Multi-provider translation layer
  - https://github.com/BerriAI/litellm
- **OpenRouter**: Multi-provider API aggregator
  - https://openrouter.ai

## Resources

- [Anthropic API Docs](https://docs.anthropic.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [DeepSeek API Docs](https://api-docs.deepseek.com/)
- [OpenRouter Docs](https://openrouter.ai/docs)
- [LiteLLM Docs](https://docs.litellm.ai/)

## Contact

For questions or issues:
- Open an issue on GitHub
- Check the documentation
- Review example code in `app.py`
