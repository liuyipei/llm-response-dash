"""
LLM Message Format Explorer - A Streamlit app to understand provider-specific messaging formats

This app helps you explore and compare how different LLM providers handle:
- Request message formats
- Response message formats
- Reasoning token formats
- Tool calling conventions
"""

import streamlit as st
import json
import asyncio
from typing import Dict, List, Any, Optional
import time

# Import provider clients
from openai import AsyncOpenAI, OpenAI
from anthropic import AsyncAnthropic, Anthropic
import google.generativeai as genai

st.set_page_config(
    page_title="LLM Message Format Explorer",
    page_icon="🔍",
    layout="wide"
)

# ==================== PROVIDER CONFIGURATIONS ====================

PROVIDERS = {
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "models": [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4",
            "o1", "o1-mini", "o3-mini", "o4-mini"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "OPENAI_API_KEY"
    },
    "Anthropic": {
        "base_url": "https://api.anthropic.com",
        "models": [
            "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001",
            "claude-opus-4-20250514", "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "ANTHROPIC_API_KEY"
    },
    "Google Gemini": {
        "base_url": "https://generativelanguage.googleapis.com",
        "models": [
            "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash",
            "gemini-1.5-pro", "gemini-1.5-flash"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "GOOGLE_API_KEY"
    },
    "OpenRouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "deepseek/deepseek-r1",
            "qwen/qwen3-thinking-80b",
            "moonshot/kimi-k2-100k",
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-5",
            "google/gemini-2.5-pro",
            "zhipuai/glm-4-plus"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "OPENROUTER_API_KEY"
    },
    "Fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "models": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",
            "accounts/fireworks/models/qwen2p5-72b-instruct",
            "accounts/fireworks/models/deepseek-r1"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "FIREWORKS_API_KEY"
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com/v1",
        "models": [
            "deepseek-reasoner", "deepseek-chat"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "DEEPSEEK_API_KEY"
    },
    "Alibaba (Qwen)": {
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "models": [
            "qwen3-thinking-80b", "qwen-plus-latest", "qwen-turbo-latest",
            "qwen-max-latest"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "QWEN_API_KEY"
    },
    "Moonshot (Kimi)": {
        "base_url": "https://api.moonshot.ai/v1",
        "models": [
            "kimi-k2-100k", "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"
        ],
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "MOONSHOT_API_KEY"
    },
    "LiteLLM": {
        "base_url": "http://localhost:4000",  # Default LiteLLM proxy
        "models": [],  # Will be auto-populated
        "supports_reasoning": True,
        "supports_tools": True,
        "api_key_env": "LITELLM_API_KEY"
    }
}

# ==================== EXAMPLE TOOLS ====================

EXAMPLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform basic arithmetic calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time in a specified timezone",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone name (e.g., 'America/New_York', 'Asia/Tokyo')"
                    }
                },
                "required": ["timezone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_random_number",
            "description": "Generate a random number within a range",
            "parameters": {
                "type": "object",
                "properties": {
                    "min": {
                        "type": "integer",
                        "description": "Minimum value (inclusive)"
                    },
                    "max": {
                        "type": "integer",
                        "description": "Maximum value (inclusive)"
                    }
                },
                "required": ["min", "max"]
            }
        }
    }
]

# ==================== EXAMPLE PROMPTS ====================

EXAMPLE_PROMPTS = {
    "Reasoning": [
        "Think step by step: Why is the sky blue?",
        "Explain your reasoning process for solving: If a train leaves Chicago at 3pm going 60mph, and another train leaves New York (800 miles away) at 4pm going 80mph, when will they meet?",
        "Reason through this puzzle: You have 12 balls, one of which is slightly heavier. You have a balance scale and can use it only 3 times. How do you find the heavier ball?",
    ],
    "Tool Calling": [
        "What's the weather in San Francisco and what time is it there?",
        "Calculate 15% tip on a $47.50 bill and tell me what time it is in Tokyo",
        "Search for the latest news about AI and give me a random number between 1 and 100",
    ],
    "Mixed": [
        "Think through the best way to spend a day in Paris, then search for current flight prices",
        "Calculate the area of a circle with radius 5, explain your reasoning, then tell me what time it is in London",
    ]
}

# ==================== HELPER FUNCTIONS ====================

def initialize_session_state():
    """Initialize session state variables"""
    if 'request_data' not in st.session_state:
        st.session_state.request_data = None
    if 'response_data' not in st.session_state:
        st.session_state.response_data = None
    if 'parsed_fields' not in st.session_state:
        st.session_state.parsed_fields = None
    if 'error' not in st.session_state:
        st.session_state.error = None

def get_openai_client(api_key: str, base_url: str) -> OpenAI:
    """Create OpenAI client"""
    return OpenAI(api_key=api_key, base_url=base_url)

def get_anthropic_client(api_key: str) -> Anthropic:
    """Create Anthropic client"""
    return Anthropic(api_key=api_key)

def extract_reasoning_tokens(response_data: Dict, provider: str) -> Optional[str]:
    """Extract reasoning tokens from response based on provider"""
    reasoning_content = []

    if provider == "Anthropic":
        # Look for thinking blocks in Anthropic response
        if "content" in response_data:
            for block in response_data.get("content", []):
                if isinstance(block, dict):
                    if block.get("type") == "thinking":
                        reasoning_content.append(block.get("thinking", ""))
                    elif block.get("type") == "redacted_thinking":
                        reasoning_content.append("[Redacted thinking block]")

    elif provider in ["OpenAI", "DeepSeek", "Moonshot (Kimi)", "Alibaba (Qwen)"]:
        # Look for reasoning_content in streaming chunks or choices
        if "choices" in response_data:
            for choice in response_data["choices"]:
                if "message" in choice:
                    msg = choice["message"]
                    if "reasoning_content" in msg:
                        reasoning_content.append(msg["reasoning_content"])
                elif "delta" in choice:
                    delta = choice["delta"]
                    if "reasoning_content" in delta:
                        reasoning_content.append(delta["reasoning_content"])

    elif provider == "OpenRouter":
        # OpenRouter uses 'reasoning' field
        if "choices" in response_data:
            for choice in response_data["choices"]:
                if "delta" in choice and "reasoning" in choice["delta"]:
                    reasoning_content.append(choice["delta"]["reasoning"])

    elif provider == "Fireworks":
        # Fireworks may use <think> tags or reasoning_content
        if "choices" in response_data:
            for choice in response_data["choices"]:
                if "message" in choice:
                    content = choice["message"].get("content", "")
                    # Extract content between <think> tags
                    if "<think>" in content and "</think>" in content:
                        start = content.find("<think>") + 7
                        end = content.find("</think>")
                        reasoning_content.append(content[start:end])

    elif provider == "Google Gemini":
        # Gemini uses thought parts
        if "candidates" in response_data:
            for candidate in response_data["candidates"]:
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "thought" in part:
                            reasoning_content.append(part.get("text", ""))

    return "\n".join(reasoning_content) if reasoning_content else None

def extract_tool_calls(response_data: Dict, provider: str) -> Optional[List[Dict]]:
    """Extract tool calls from response based on provider"""
    tool_calls = []

    if provider == "Anthropic":
        # Anthropic uses tool_use blocks
        if "content" in response_data:
            for block in response_data.get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block.get("id"),
                        "name": block.get("name"),
                        "input": block.get("input")
                    })

    elif provider in ["OpenAI", "DeepSeek", "Moonshot (Kimi)", "Alibaba (Qwen)", "OpenRouter", "Fireworks"]:
        # OpenAI-compatible tool calls
        if "choices" in response_data:
            for choice in response_data["choices"]:
                if "message" in choice and "tool_calls" in choice["message"]:
                    for tc in choice["message"]["tool_calls"]:
                        tool_calls.append({
                            "id": tc.get("id"),
                            "type": tc.get("type"),
                            "function": tc.get("function")
                        })

    elif provider == "Google Gemini":
        # Gemini uses function_call
        if "candidates" in response_data:
            for candidate in response_data["candidates"]:
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "functionCall" in part:
                            fc = part["functionCall"]
                            tool_calls.append({
                                "name": fc.get("name"),
                                "args": fc.get("args")
                            })

    return tool_calls if tool_calls else None

def make_request(provider: str, model: str, api_key: str, prompt: str,
                 enable_tools: bool = False, enable_reasoning: bool = False,
                 temperature: float = 0.0, max_tokens: int = 1024) -> tuple:
    """Make API request to the selected provider"""

    provider_config = PROVIDERS[provider]
    base_url = provider_config["base_url"]

    request_data = {}
    response_data = {}

    try:
        if provider == "Anthropic":
            client = get_anthropic_client(api_key)

            # Build request
            request_data = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature if not enable_reasoning else None,
                "messages": [{"role": "user", "content": prompt}]
            }

            if enable_tools:
                # Convert OpenAI tool format to Anthropic format
                anthropic_tools = []
                for tool in EXAMPLE_TOOLS:
                    anthropic_tools.append({
                        "name": tool["function"]["name"],
                        "description": tool["function"]["description"],
                        "input_schema": tool["function"]["parameters"]
                    })
                request_data["tools"] = anthropic_tools
                if not enable_reasoning:
                    request_data["tool_choice"] = {"type": "any"}

            if enable_reasoning:
                request_data["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": 5000
                }

            # Make request
            response = client.messages.create(**request_data)
            response_data = response.model_dump()

        elif provider == "Google Gemini":
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)

            request_data = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }

            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )

            if enable_reasoning:
                generation_config.thinking_config = {
                    "thinking_budget": 5000,
                    "include_thoughts": True
                }

            tools = None
            if enable_tools:
                # Convert to Gemini tool format
                gemini_tools = []
                for tool in EXAMPLE_TOOLS:
                    gemini_tools.append(genai.protos.FunctionDeclaration(
                        name=tool["function"]["name"],
                        description=tool["function"]["description"],
                        parameters=tool["function"]["parameters"]
                    ))
                tools = gemini_tools

            # Make request
            response = model_obj.generate_content(
                prompt,
                generation_config=generation_config,
                tools=tools
            )
            response_data = {
                "candidates": [c._pb for c in response.candidates],
                "usage_metadata": response._result.usage_metadata
            }

        else:  # OpenAI-compatible providers
            client = get_openai_client(api_key, base_url)

            # Build request
            messages = [{"role": "user", "content": prompt}]

            # For reasoning models, use developer role for system prompt
            is_reasoning_model = any(x in model.lower() for x in ["o1", "o3", "o4", "reasoning", "r1", "thinking"])

            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature if not is_reasoning_model else None,
                "max_tokens": max_tokens
            }

            if enable_tools and not is_reasoning_model:
                request_data["tools"] = EXAMPLE_TOOLS
                request_data["tool_choice"] = "auto"

            # Add reasoning parameters for specific models
            if enable_reasoning and is_reasoning_model:
                if "o1" in model or "o3" in model or "o4" in model or "gpt-5" in model:
                    request_data["reasoning_effort"] = "medium"
                elif "qwen" in model.lower() and "thinking" in model.lower():
                    request_data["enable_thinking"] = True
                    request_data["thinking_budget"] = 5000

            # Make request
            response = client.chat.completions.create(**request_data)
            response_data = response.model_dump()

        return request_data, response_data, None

    except Exception as e:
        return request_data, None, str(e)

# ==================== STREAMLIT UI ====================

def main():
    initialize_session_state()

    st.title("🔍 LLM Message Format Explorer")
    st.markdown("""
    Explore and compare how different LLM providers handle request/response formats,
    reasoning tokens, and tool calling.
    """)

    # Sidebar configuration
    st.sidebar.header("Configuration")

    # Provider selection
    provider = st.sidebar.selectbox(
        "Provider",
        options=list(PROVIDERS.keys()),
        help="Select the LLM provider to test"
    )

    # API key input
    api_key = st.sidebar.text_input(
        "API Key",
        type="password",
        help=f"Enter your {provider} API key",
        placeholder=f"{PROVIDERS[provider]['api_key_env']}"
    )

    # Model selection
    models = PROVIDERS[provider]["models"]
    if not models:
        st.sidebar.info("Enter API key to load available models")
        models = ["custom-model"]

    model = st.sidebar.selectbox(
        "Model",
        options=models,
        help="Select the model to use"
    )

    # Parameters
    st.sidebar.subheader("Parameters")

    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.0,
        step=0.1,
        help="Sampling temperature (0 = deterministic)"
    )

    max_tokens = st.sidebar.slider(
        "Max Tokens",
        min_value=256,
        max_value=4096,
        value=1024,
        step=256,
        help="Maximum tokens in response"
    )

    enable_tools = st.sidebar.checkbox(
        "Enable Tool Calling",
        value=False,
        disabled=not PROVIDERS[provider]["supports_tools"],
        help="Include example tools in the request"
    )

    enable_reasoning = st.sidebar.checkbox(
        "Enable Reasoning",
        value=False,
        disabled=not PROVIDERS[provider]["supports_reasoning"],
        help="Enable reasoning/thinking mode (if supported)"
    )

    # Main area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Prompt")

        # Example prompts
        prompt_category = st.selectbox(
            "Example Prompts",
            options=["Custom"] + list(EXAMPLE_PROMPTS.keys())
        )

        if prompt_category != "Custom":
            example_prompt = st.selectbox(
                "Select Example",
                options=EXAMPLE_PROMPTS[prompt_category]
            )
            prompt = st.text_area(
                "Edit Prompt",
                value=example_prompt,
                height=150
            )
        else:
            prompt = st.text_area(
                "Enter Your Prompt",
                height=150,
                placeholder="Enter your prompt here..."
            )

    with col2:
        st.subheader("Actions")

        if st.button("🚀 Send Request", type="primary", use_container_width=True):
            if not api_key:
                st.error("Please enter an API key")
            elif not prompt:
                st.error("Please enter a prompt")
            else:
                with st.spinner("Making request..."):
                    request_data, response_data, error = make_request(
                        provider, model, api_key, prompt,
                        enable_tools, enable_reasoning,
                        temperature, max_tokens
                    )

                    st.session_state.request_data = request_data
                    st.session_state.response_data = response_data
                    st.session_state.error = error

                    if response_data:
                        # Parse fields
                        st.session_state.parsed_fields = {
                            "reasoning": extract_reasoning_tokens(response_data, provider),
                            "tool_calls": extract_tool_calls(response_data, provider)
                        }

        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.request_data = None
            st.session_state.response_data = None
            st.session_state.parsed_fields = None
            st.session_state.error = None
            st.rerun()

    # Display results
    if st.session_state.error:
        st.error(f"Error: {st.session_state.error}")

    if st.session_state.response_data or st.session_state.request_data:
        tabs = st.tabs(["Response", "Request JSON", "Response JSON", "Parsed Fields"])

        with tabs[0]:
            st.subheader("Response")
            response_data = st.session_state.response_data

            if response_data:
                # Extract main text content
                text_content = ""

                if provider == "Anthropic":
                    for block in response_data.get("content", []):
                        if isinstance(block, dict) and block.get("type") == "text":
                            text_content += block.get("text", "")

                elif "choices" in response_data:
                    for choice in response_data["choices"]:
                        if "message" in choice:
                            text_content += choice["message"].get("content", "")
                        elif "text" in choice:
                            text_content += choice["text"]

                elif "candidates" in response_data:
                    for candidate in response_data["candidates"]:
                        if "content" in candidate:
                            text_content += str(candidate["content"])

                st.markdown(text_content if text_content else "No text content found")

                # Show usage
                if "usage" in response_data:
                    usage = response_data["usage"]
                    st.caption(f"**Tokens:** Input: {usage.get('input_tokens', usage.get('prompt_tokens', 'N/A'))}, "
                             f"Output: {usage.get('output_tokens', usage.get('completion_tokens', 'N/A'))}")

        with tabs[1]:
            st.subheader("Request JSON")
            if st.session_state.request_data:
                st.json(st.session_state.request_data)

                if st.button("📋 Copy Request JSON"):
                    st.code(json.dumps(st.session_state.request_data, indent=2), language="json")

        with tabs[2]:
            st.subheader("Response JSON")
            if st.session_state.response_data:
                st.json(st.session_state.response_data)

                if st.button("📋 Copy Response JSON"):
                    st.code(json.dumps(st.session_state.response_data, indent=2), language="json")

        with tabs[3]:
            st.subheader("Parsed Fields")

            if st.session_state.parsed_fields:
                # Reasoning tokens
                st.markdown("### Reasoning Tokens")
                reasoning = st.session_state.parsed_fields.get("reasoning")
                if reasoning:
                    st.info(reasoning)
                else:
                    st.caption("No reasoning tokens found")

                # Tool calls
                st.markdown("### Tool Calls")
                tool_calls = st.session_state.parsed_fields.get("tool_calls")
                if tool_calls:
                    for i, tc in enumerate(tool_calls):
                        with st.expander(f"Tool Call {i+1}: {tc.get('name', tc.get('function', {}).get('name', 'Unknown'))}"):
                            st.json(tc)
                else:
                    st.caption("No tool calls found")

    # Footer
    st.markdown("---")
    st.markdown("""
    **Tips:**
    - Use reasoning prompts to see how models expose their thinking process
    - Enable tools to see different tool calling formats
    - Compare the same prompt across different providers to spot format differences
    """)

if __name__ == "__main__":
    main()
