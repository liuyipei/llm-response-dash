# LLM Provider Message Format Analysis

**Last Updated:** November 2025

## Table of Contents
1. [Overview](#overview)
2. [Provider Categories](#provider-categories)
3. [Request Schemas](#request-schemas)
4. [Response Schemas](#response-schemas)
5. [Reasoning Token Comparison](#reasoning-token-comparison)
6. [Tool Call Format Comparison](#tool-call-format-comparison)
7. [Real Examples](#real-examples)
8. [Migration Notes](#migration-notes)

---

## Overview

This document provides a comprehensive analysis of message formats across major LLM providers, with special focus on:
- **Reasoning tokens**: How models expose their thinking process
- **Tool calling**: How models request function executions
- **Format inconsistencies**: Critical differences that break integrations

### Key Findings

1. **Three main reasoning approaches:**
   - Anthropic: Structured `thinking` blocks with signatures
   - OpenAI: `reasoning_content` field in delta/message
   - Tag-based: Content wrapped in `<think>` tags (Fireworks, some models)

2. **Two main tool calling conventions:**
   - Anthropic: `tool_use` content blocks
   - OpenAI: `tool_calls` array in message

3. **Provider types:**
   - **Direct providers**: Anthropic, OpenAI, Google, DeepSeek, Alibaba, Moonshot
   - **Aggregators**: OpenRouter (normalizes or passes through)
   - **Inference platforms**: Fireworks (OpenAI-compatible)
   - **Unified APIs**: LiteLLM (translation layer)

---

## Provider Categories

### Direct Providers

**Anthropic**
- Native API with custom message format
- First-class support for thinking/reasoning mode
- Unique `tool_use` content blocks

**OpenAI**
- Industry-standard format (many providers clone this)
- Reasoning models (o1, o3, o4) use `reasoning_effort` parameter
- Tool calls in `tool_calls` array

**Google Gemini**
- Custom protobuf-based API
- Thinking support via `thinkingConfig`
- Function calling via `functionCall` parts

**DeepSeek**
- OpenAI-compatible API
- DeepSeek-R1 model uses "R1 format" (no system role, merged consecutive messages)
- Reasoning via `reasoning_content`

**Alibaba (Qwen)**
- OpenAI-compatible API
- Qwen3 Thinking models use `enable_thinking` + `thinking_budget`
- Uses R1 format when reasoning enabled

**Moonshot (Kimi)**
- OpenAI-compatible API
- Kimi K2 supports reasoning via `reasoning_content`

### Aggregators

**OpenRouter**
- Routes to multiple providers
- Normalizes some formats, passes through others
- `delta.reasoning` for reasoning tokens
- `delta.reasoning_details` for preserving traces
- Cost tracking via generation endpoint

### Inference Platforms

**Fireworks**
- OpenAI-compatible API
- Some models use `<think>` tags in content
- Also supports `reasoning_content` field

### Unified APIs

**LiteLLM**
- Translation layer for multiple providers
- Supports `thinking` config for Anthropic models
- Handles prompt caching across providers
- Reasoning via `reasoning_content`

---

## Request Schemas

### Anthropic Request

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 8192,
  "temperature": 0,
  "system": [
    {
      "type": "text",
      "text": "You are a helpful assistant.",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "Explain reasoning step by step."
    }
  ],
  "thinking": {
    "type": "enabled",
    "budget_tokens": 5000
  },
  "tools": [
    {
      "name": "calculator",
      "description": "Perform calculations",
      "input_schema": {
        "type": "object",
        "properties": {
          "expression": {"type": "string"}
        },
        "required": ["expression"]
      }
    }
  ],
  "tool_choice": {"type": "any"}
}
```

**Key Points:**
- `thinking` parameter enables reasoning mode
- `system` is array of text blocks with cache_control
- `tools` have `input_schema` instead of `parameters`
- `tool_choice` controls tool usage behavior
- Temperature not supported in thinking mode

### OpenAI Request (Standard Models)

```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Calculate 15% of 200"
    }
  ],
  "temperature": 0,
  "max_tokens": 1024,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calculator",
        "description": "Perform calculations",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {"type": "string"}
          },
          "required": ["expression"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### OpenAI Request (Reasoning Models: o1, o3, o4)

```json
{
  "model": "o3-mini",
  "messages": [
    {
      "role": "developer",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Think step by step about this problem..."
    }
  ],
  "reasoning_effort": "medium",
  "max_tokens": 2048
}
```

**Key Differences:**
- Uses `developer` role instead of `system`
- `reasoning_effort`: low, medium, or high
- No `temperature` parameter
- No `tools` parameter (reasoning models don't support tools)

### DeepSeek Request (DeepSeek-Reasoner)

```json
{
  "model": "deepseek-reasoner",
  "messages": [
    {
      "role": "user",
      "content": "You are a helpful assistant.\n\nThink through this problem step by step..."
    }
  ],
  "max_completion_tokens": 2048,
  "stream": true
}
```

**R1 Format Requirements:**
- No `system` role - merge into first `user` message
- Consecutive messages with same role are merged
- No `temperature` parameter
- No `tools` for reasoning model

### Qwen Request (Qwen3 Thinking)

```json
{
  "model": "qwen3-thinking-80b",
  "messages": [
    {
      "role": "user",
      "content": "System: You are helpful.\n\nExplain your reasoning..."
    }
  ],
  "enable_thinking": true,
  "thinking_budget": 5000,
  "max_completion_tokens": 2048
}
```

**Key Points:**
- Uses R1 format when `enable_thinking: true`
- `thinking_budget` controls reasoning token limit
- No temperature when thinking enabled

### Google Gemini Request

```json
{
  "model": "gemini-2.5-pro",
  "contents": [
    {
      "role": "user",
      "parts": [
        {"text": "Explain your reasoning step by step..."}
      ]
    }
  ],
  "systemInstruction": {
    "parts": [
      {"text": "You are a helpful assistant."}
    ]
  },
  "generationConfig": {
    "temperature": 0,
    "maxOutputTokens": 1024
  },
  "thinkingConfig": {
    "thinkingBudget": 5000,
    "includeThoughts": true
  },
  "tools": [
    {
      "functionDeclarations": [
        {
          "name": "calculator",
          "description": "Perform calculations",
          "parameters": {
            "type": "object",
            "properties": {
              "expression": {"type": "string"}
            },
            "required": ["expression"]
          }
        }
      ]
    }
  ]
}
```

**Key Points:**
- `contents` instead of `messages`
- `parts` array within each message
- `systemInstruction` separate from messages
- `thinkingConfig` for reasoning
- Tools wrapped in `functionDeclarations`

### OpenRouter Request

```json
{
  "model": "deepseek/deepseek-r1",
  "messages": [
    {
      "role": "user",
      "content": "Explain step by step..."
    }
  ],
  "temperature": 0,
  "max_tokens": 2048,
  "provider": {
    "order": ["DeepSeek", "Together"],
    "allow_fallbacks": true
  }
}
```

**Key Points:**
- OpenAI-compatible format
- `provider` object for routing control
- Automatically handles reasoning for supported models
- Preserves native format or normalizes depending on model

---

## Response Schemas

### Anthropic Response

```json
{
  "id": "msg_01XYZ",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me think through this step by step...",
      "signature": "base64_signature_string"
    },
    {
      "type": "text",
      "text": "The answer is 42."
    },
    {
      "type": "tool_use",
      "id": "toolu_01ABC",
      "name": "calculator",
      "input": {
        "expression": "15% of 200"
      }
    }
  ],
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 50
  },
  "stop_reason": "end_turn"
}
```

**Streaming Format:**
```json
// Event: message_start
{
  "type": "message_start",
  "message": {
    "usage": {
      "input_tokens": 100,
      "cache_read_input_tokens": 50
    }
  }
}

// Event: content_block_start (thinking)
{
  "type": "content_block_start",
  "index": 0,
  "content_block": {
    "type": "thinking",
    "thinking": "",
    "signature": ""
  }
}

// Event: content_block_delta (thinking)
{
  "type": "content_block_delta",
  "index": 0,
  "delta": {
    "type": "thinking_delta",
    "thinking": "Let me analyze..."
  }
}

// Event: content_block_delta (signature)
{
  "type": "content_block_delta",
  "index": 0,
  "delta": {
    "type": "signature_delta",
    "signature": "signature_chunk"
  }
}

// Event: content_block_start (text)
{
  "type": "content_block_start",
  "index": 1,
  "content_block": {
    "type": "text",
    "text": ""
  }
}

// Event: content_block_delta (text)
{
  "type": "content_block_delta",
  "index": 1,
  "delta": {
    "type": "text_delta",
    "text": "The answer"
  }
}

// Event: content_block_start (tool_use)
{
  "type": "content_block_start",
  "index": 2,
  "content_block": {
    "type": "tool_use",
    "id": "toolu_01ABC",
    "name": "calculator",
    "input": {}
  }
}

// Event: content_block_delta (tool input)
{
  "type": "content_block_delta",
  "index": 2,
  "delta": {
    "type": "input_json_delta",
    "partial_json": "{\"expression\":"
  }
}
```

### OpenAI Response (Standard Models)

```json
{
  "id": "chatcmpl-XYZ",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The answer is 30.",
        "tool_calls": [
          {
            "id": "call_ABC123",
            "type": "function",
            "function": {
              "name": "calculator",
              "arguments": "{\"expression\": \"0.15 * 200\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150,
    "prompt_tokens_details": {
      "cached_tokens": 20
    }
  }
}
```

**Streaming Format:**
```json
// Chunk 1
{
  "id": "chatcmpl-XYZ",
  "object": "chat.completion.chunk",
  "created": 1234567890,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "delta": {
        "role": "assistant",
        "content": "The"
      },
      "finish_reason": null
    }
  ]
}

// Chunk 2
{
  "choices": [
    {
      "delta": {
        "content": " answer"
      }
    }
  ]
}

// Tool call chunk
{
  "choices": [
    {
      "delta": {
        "tool_calls": [
          {
            "index": 0,
            "id": "call_ABC123",
            "type": "function",
            "function": {
              "name": "calculator",
              "arguments": ""
            }
          }
        ]
      }
    }
  ]
}

// Final chunk with usage
{
  "choices": [
    {
      "delta": {},
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50
  }
}
```

### OpenAI Response (Reasoning Models: o3, o4)

```json
{
  "id": "chatcmpl-XYZ",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "o3-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The answer is 42.",
        "reasoning_content": "Let me think through this step by step:\n1. First, I need to...\n2. Then, I should..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "reasoning_tokens": 200,
    "total_tokens": 350
  }
}
```

**Streaming Format:**
```json
// Reasoning chunk
{
  "choices": [
    {
      "index": 0,
      "delta": {
        "reasoning_content": "Let me think..."
      }
    }
  ]
}

// Content chunk
{
  "choices": [
    {
      "delta": {
        "content": "The answer is"
      }
    }
  ]
}
```

### DeepSeek Response (DeepSeek-Reasoner)

Same format as OpenAI reasoning models - uses `reasoning_content` in streaming deltas.

### Qwen Response (Qwen3 Thinking)

Same format as OpenAI reasoning models - uses `reasoning_content` when `enable_thinking: true`.

### Google Gemini Response

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "thought": true,
            "text": "Let me reason through this..."
          },
          {
            "text": "The answer is 42."
          },
          {
            "functionCall": {
              "name": "calculator",
              "args": {
                "expression": "0.15 * 200"
              }
            }
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP"
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 100,
    "candidatesTokenCount": 50,
    "thoughtsTokenCount": 30,
    "totalTokenCount": 180,
    "cachedContentTokenCount": 20
  }
}
```

**Key Points:**
- Reasoning parts have `thought: true` flag
- Function calls in `functionCall` field
- Separate `thoughtsTokenCount` in usage

### OpenRouter Response

```json
{
  "id": "gen-XYZ",
  "model": "deepseek/deepseek-r1",
  "choices": [
    {
      "index": 0,
      "delta": {
        "reasoning": "Thinking step by step...",
        "reasoning_details": {
          "type": "thinking",
          "content": "...",
          "signature": "..."
        },
        "content": "The answer is 42."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "cost": 0.001,
    "cost_details": {
      "upstream_inference_cost": 0.0008
    }
  }
}
```

**Key Points:**
- `delta.reasoning` for reasoning text
- `delta.reasoning_details` preserves native format
- `usage.cost` includes total cost
- Can query `/generation?id=` endpoint for detailed usage

### Fireworks Response

```json
{
  "id": "chatcmpl-XYZ",
  "object": "chat.completion",
  "model": "accounts/fireworks/models/deepseek-r1",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "<think>\nLet me analyze this step by step...\n</think>\nThe answer is 42."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "prompt_cache_hit_tokens": 20,
    "prompt_cache_miss_tokens": 80
  }
}
```

**OR (for models with native reasoning support):**

```json
{
  "choices": [
    {
      "delta": {
        "reasoning_content": "Step by step analysis...",
        "content": "The answer is 42."
      }
    }
  ]
}
```

---

## Reasoning Token Comparison

| Provider/Model | Reasoning Token Location | Example JSON Structure | Parsing Code Snippet | What Breaks If Parsed Wrong |
|----------------|-------------------------|------------------------|---------------------|----------------------------|
| **Anthropic (Claude 3.7+, 4+, 4.5+)** | Separate `thinking` content blocks | `{"type": "thinking", "thinking": "...", "signature": "..."}` | `for block in content: if block["type"] == "thinking": reasoning = block["thinking"]` | Signature not preserved → can't send thinking back to API in subsequent requests → model loses context of previous reasoning |
| **OpenAI (o1, o3, o4, GPT-5)** | `reasoning_content` field in message/delta | `{"message": {"reasoning_content": "...", "content": "..."}}` | `reasoning = delta.get("reasoning_content") or message.get("reasoning_content")` | Reasoning merged with content → users see thinking mixed with answer → confusing UX |
| **DeepSeek (DeepSeek-R1)** | `reasoning_content` field (OpenAI-compatible) | Same as OpenAI | Same as OpenAI | Same as OpenAI |
| **Qwen (Qwen3 Thinking)** | `reasoning_content` field when `enable_thinking: true` | Same as OpenAI | Same as OpenAI | Same as OpenAI |
| **Moonshot (Kimi K2)** | `reasoning_content` field (if supported) | Same as OpenAI | Same as OpenAI | Same as OpenAI |
| **OpenRouter** | `delta.reasoning` string | `{"delta": {"reasoning": "...", "reasoning_details": {...}}}` | `reasoning = delta.get("reasoning"); details = delta.get("reasoning_details")` | Native format lost → can't preserve reasoning for models that need it (e.g., Anthropic signatures) |
| **Fireworks** | `<think>` tags in content OR `reasoning_content` | `{"content": "<think>...</think>Answer"}` | `if "<think>" in content: start = content.find("<think>") + 7; end = content.find("</think>"); reasoning = content[start:end]` | Tags not stripped → users see `<think>` tags in UI → poor UX |
| **Google Gemini** | `thought: true` flag in parts | `{"parts": [{"thought": true, "text": "..."}]}` | `for part in parts: if part.get("thought"): reasoning = part["text"]` | Thoughts counted as regular content → token usage wrong → billing errors |
| **LiteLLM** | `reasoning_content` (normalized) | Same as OpenAI | Same as OpenAI | Provider-specific features lost → can't use Anthropic signatures → degraded functionality |

### Code Examples for Reasoning Extraction

**Anthropic (Streaming):**
```python
reasoning_parts = []
signature_parts = []

for chunk in stream:
    if chunk.type == "content_block_start":
        if chunk.content_block.type == "thinking":
            # Start collecting reasoning
            pass
    elif chunk.type == "content_block_delta":
        if chunk.delta.type == "thinking_delta":
            reasoning_parts.append(chunk.delta.thinking)
        elif chunk.delta.type == "signature_delta":
            signature_parts.append(chunk.delta.signature)

reasoning = "".join(reasoning_parts)
signature = "".join(signature_parts)

# To send back in next request:
messages.append({
    "role": "assistant",
    "content": [
        {
            "type": "thinking",
            "thinking": reasoning,
            "signature": signature
        },
        {
            "type": "text",
            "text": final_answer
        }
    ]
})
```

**OpenAI (Streaming):**
```python
reasoning_parts = []
content_parts = []

for chunk in stream:
    delta = chunk.choices[0].delta
    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
        reasoning_parts.append(delta.reasoning_content)
    if delta.content:
        content_parts.append(delta.content)

reasoning = "".join(reasoning_parts)
content = "".join(content_parts)
```

**Fireworks (Tag-based):**
```python
full_content = ""
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        full_content += delta.content

# Parse tags
if "<think>" in full_content and "</think>" in full_content:
    think_start = full_content.find("<think>") + 7
    think_end = full_content.find("</think>")
    reasoning = full_content[think_start:think_end].strip()
    answer = full_content[think_end + 8:].strip()
else:
    reasoning = None
    answer = full_content
```

**Google Gemini:**
```python
reasoning_parts = []
content_parts = []

for chunk in stream:
    for candidate in chunk.candidates:
        for part in candidate.content.parts:
            if hasattr(part, 'thought') and part.thought:
                reasoning_parts.append(part.text)
            else:
                content_parts.append(part.text)

reasoning = "\n".join(reasoning_parts)
content = "\n".join(content_parts)
```

---

## Tool Call Format Comparison

| Provider/Model | Tool Request Format | Tool Response Format | Example JSON | What Breaks If Parsed Wrong |
|----------------|--------------------|--------------------|--------------|----------------------------|
| **Anthropic** | `tools` array with `input_schema` | `tool_use` content blocks | Request: `{"name": "calc", "input_schema": {...}}` Response: `{"type": "tool_use", "id": "...", "name": "calc", "input": {...}}` | Tool results sent in wrong format → API rejects request → conversation breaks |
| **OpenAI** | `tools` array with `function` wrapper | `tool_calls` array in message | Request: `{"type": "function", "function": {"name": "calc", "parameters": {...}}}` Response: `{"tool_calls": [{"id": "...", "type": "function", "function": {"name": "calc", "arguments": "{...}"}}]}` | Arguments are JSON string, not object → need to parse → parse errors break tool execution |
| **Google Gemini** | `functionDeclarations` array | `functionCall` parts | Request: `{"functionDeclarations": [{"name": "calc", "parameters": {...}}]}` Response: `{"functionCall": {"name": "calc", "args": {...}}}` | Args are object not string → opposite of OpenAI → confusion in parsing logic |
| **DeepSeek** | OpenAI-compatible | OpenAI-compatible | Same as OpenAI | Same as OpenAI |
| **Qwen** | OpenAI-compatible | OpenAI-compatible | Same as OpenAI | Same as OpenAI |
| **Moonshot** | OpenAI-compatible | OpenAI-compatible | Same as OpenAI | Same as OpenAI |
| **OpenRouter** | OpenAI-compatible (normalized) | OpenAI-compatible (normalized) | Same as OpenAI | Same as OpenAI |
| **Fireworks** | OpenAI-compatible | OpenAI-compatible | Same as OpenAI | Same as OpenAI |
| **LiteLLM** | Accepts both, translates | Normalizes to OpenAI format | Same as OpenAI | Same as OpenAI |

### Tool Call Parsing Examples

**Anthropic (Send tool result back):**
```python
# Received tool_use block:
tool_block = {
    "type": "tool_use",
    "id": "toolu_01ABC",
    "name": "calculator",
    "input": {
        "expression": "15% of 200"
    }
}

# Execute tool
result = execute_tool(tool_block["name"], tool_block["input"])

# Send result back to API:
messages.append({
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": tool_block["id"],
            "content": str(result)
        }
    ]
})
```

**OpenAI (Send tool result back):**
```python
# Received tool call:
tool_call = {
    "id": "call_ABC123",
    "type": "function",
    "function": {
        "name": "calculator",
        "arguments": '{"expression": "15% of 200"}'  # JSON string!
    }
}

# Parse arguments
import json
args = json.loads(tool_call["function"]["arguments"])

# Execute tool
result = execute_tool(tool_call["function"]["name"], args)

# Send result back:
messages.append({
    "role": "tool",
    "tool_call_id": tool_call["id"],
    "content": str(result)
})
```

**Google Gemini (Send tool result back):**
```python
# Received function call:
function_call = {
    "name": "calculator",
    "args": {  # Already an object, not string!
        "expression": "15% of 200"
    }
}

# Execute tool (args already parsed)
result = execute_tool(function_call["name"], function_call["args"])

# Send result back:
contents.append({
    "role": "function",
    "parts": [
        {
            "functionResponse": {
                "name": function_call["name"],
                "response": {
                    "result": result
                }
            }
        }
    ]
})
```

---

## Real Examples

### Example 1: Reasoning with Anthropic

**Request:**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 2048,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 3000
  },
  "messages": [
    {
      "role": "user",
      "content": "If I have 12 apples and give away 1/3, then buy 5 more, how many do I have?"
    }
  ]
}
```

**Response:**
```json
{
  "id": "msg_01XYZ",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "thinking",
      "thinking": "Let me work through this step by step:\n1. Start with 12 apples\n2. Give away 1/3: 12 ÷ 3 = 4 apples given away\n3. Remaining: 12 - 4 = 8 apples\n4. Buy 5 more: 8 + 5 = 13 apples\n5. Final answer: 13 apples",
      "signature": "eyJhbGc..."
    },
    {
      "type": "text",
      "text": "You would have 13 apples.\n\nHere's the calculation:\n- Starting amount: 12 apples\n- Give away 1/3: 12 ÷ 3 = 4 apples\n- Remaining: 12 - 4 = 8 apples\n- Buy 5 more: 8 + 5 = 13 apples"
    }
  ],
  "usage": {
    "input_tokens": 25,
    "output_tokens": 89
  }
}
```

### Example 2: Tool Calling with OpenAI

**Request:**
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "What's 15% of 200?"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calculator",
        "description": "Perform arithmetic calculations",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {
              "type": "string",
              "description": "Mathematical expression to evaluate"
            }
          },
          "required": ["expression"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

**Response:**
```json
{
  "id": "chatcmpl-ABC",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_XYZ",
            "type": "function",
            "function": {
              "name": "calculator",
              "arguments": "{\"expression\": \"0.15 * 200\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

**Sending Tool Result:**
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "user",
      "content": "What's 15% of 200?"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_XYZ",
          "type": "function",
          "function": {
            "name": "calculator",
            "arguments": "{\"expression\": \"0.15 * 200\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_XYZ",
      "content": "30.0"
    }
  ]
}
```

**Final Response:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "15% of 200 is 30."
      }
    }
  ]
}
```

### Example 3: DeepSeek-R1 with Reasoning

**Request (R1 Format):**
```json
{
  "model": "deepseek-reasoner",
  "messages": [
    {
      "role": "user",
      "content": "A bat and ball cost $1.10 total. The bat costs $1 more than the ball. How much does the ball cost?"
    }
  ],
  "max_completion_tokens": 2048,
  "stream": true
}
```

**Streaming Response:**
```json
// Chunk 1 - Reasoning
{
  "choices": [
    {
      "index": 0,
      "delta": {
        "reasoning_content": "Let me denote the cost of the ball as x. Then the bat costs x + $1."
      }
    }
  ]
}

// Chunk 2 - More reasoning
{
  "choices": [
    {
      "delta": {
        "reasoning_content": " The total is x + (x + 1) = 1.10. So 2x + 1 = 1.10, which means 2x = 0.10, thus x = 0.05."
      }
    }
  ]
}

// Chunk 3 - Answer starts
{
  "choices": [
    {
      "delta": {
        "content": "The ball costs"
      }
    }
  ]
}

// Chunk 4 - Answer continues
{
  "choices": [
    {
      "delta": {
        "content": " $0.05 (5 cents)."
      }
    }
  ]
}
```

### Example 4: OpenRouter with Multiple Providers

**Request:**
```json
{
  "model": "anthropic/claude-sonnet-4.5",
  "messages": [
    {
      "role": "user",
      "content": "Explain quantum entanglement simply"
    }
  ],
  "provider": {
    "order": ["Anthropic", "Together"],
    "allow_fallbacks": true
  }
}
```

**Response:**
```json
{
  "id": "gen-12345",
  "model": "anthropic/claude-sonnet-4.5",
  "provider": "Anthropic",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Quantum entanglement is when two particles..."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 45,
    "total_tokens": 60,
    "cost": 0.00027,
    "cost_details": {
      "upstream_inference_cost": 0.00025
    }
  }
}
```

---

## Migration Notes

### For Cline or Similar Agent Tools

#### 1. Adding Support for New Reasoning Models

**When adding a new model with reasoning:**

1. Identify the reasoning format:
   - Check if it uses `reasoning_content` (OpenAI-style)
   - Check if it uses `thinking` blocks (Anthropic-style)
   - Check if it uses `<think>` tags (tag-based)
   - Check if it uses `thought` parts (Gemini-style)

2. Update streaming parser:
```typescript
// Example for new provider "ProviderX"
if (delta?.reasoning_content) {
    yield {
        type: "reasoning",
        reasoning: delta.reasoning_content
    }
}
```

3. Update request builder:
```typescript
// Add reasoning parameters
if (isReasoningModel) {
    requestParams.reasoning_config = {
        enabled: true,
        budget_tokens: thinkingBudgetTokens
    }
}
```

#### 2. Common Pitfalls

**Pitfall 1: Mixing system/user roles in R1 format**
```typescript
// WRONG - R1 models reject system role
const messages = [
    { role: "system", content: systemPrompt },
    { role: "user", content: userMessage }
]

// CORRECT - Merge system into first user message
const messages = [
    { role: "user", content: `${systemPrompt}\n\n${userMessage}` }
]
```

**Pitfall 2: Not handling Anthropic signatures**
```typescript
// WRONG - Lose signature, can't send thinking back
const reasoning = thinkingBlock.thinking
saveReasoning(reasoning)

// CORRECT - Preserve signature for API reuse
const reasoning = {
    thinking: thinkingBlock.thinking,
    signature: thinkingBlock.signature
}
saveReasoning(reasoning)

// When sending back:
messages.push({
    role: "assistant",
    content: [
        {
            type: "thinking",
            thinking: reasoning.thinking,
            signature: reasoning.signature
        }
    ]
})
```

**Pitfall 3: Tool call argument parsing**
```typescript
// WRONG - Assumes arguments is always object
const args = toolCall.function.arguments
executeFunction(toolCall.function.name, args)

// CORRECT - Handle string vs object
const args = typeof toolCall.function.arguments === 'string'
    ? JSON.parse(toolCall.function.arguments)
    : toolCall.function.arguments
executeFunction(toolCall.function.name, args)
```

**Pitfall 4: Not separating reasoning from content in UI**
```typescript
// WRONG - User sees both mixed together
const fullText = reasoning + content
displayToUser(fullText)

// CORRECT - Show reasoning separately
displayReasoning(reasoning)
displayContent(content)
```

#### 3. Testing Checklist

When adding a new provider:

- [ ] Test with reasoning prompt - verify reasoning tokens extracted
- [ ] Test with tool calling prompt - verify tools executed correctly
- [ ] Test tool result flow - verify model receives and processes results
- [ ] Test streaming - verify chunks processed in correct order
- [ ] Test error cases - verify graceful degradation
- [ ] Test token counting - verify usage stats accurate
- [ ] Test cost calculation - verify billing correct
- [ ] Test multi-turn conversation - verify context preserved

#### 4. Provider-Specific Quirks

**Anthropic:**
- Requires `max_tokens` (no default)
- Temperature not allowed with thinking mode
- Tool choice must be unset or `auto` with thinking
- Cache control needs minimum 1024 tokens
- Signatures must be preserved for thinking continuity

**OpenAI o-series:**
- Uses `developer` role instead of `system`
- No temperature control
- No tool calling support
- `reasoning_effort` parameter (low/medium/high)
- Higher cost per token

**DeepSeek-R1:**
- Must use R1 format (no system role)
- No temperature control
- No tool calling on reasoning model
- Very verbose reasoning output
- Lower cost than OpenAI o-series

**Qwen3 Thinking:**
- Uses `enable_thinking` + `thinking_budget`
- Switches to R1 format when thinking enabled
- Can use tools in non-thinking mode
- Both China and International APIs available

**Gemini:**
- Uses `parts` array structure
- Thinking requires `includeThoughts: true`
- Thoughts counted separately in usage
- Function args are objects not strings
- Implicit caching (no explicit control)

**OpenRouter:**
- Normalizes most formats to OpenAI-compatible
- Preserves native formats via `reasoning_details`
- Cost tracking via separate generation endpoint
- Provider fallback support
- May have delays in usage reporting

**LiteLLM:**
- Translates between formats automatically
- Supports Anthropic thinking config
- Handles prompt caching across providers
- Session tracking via `litellm_session_id`
- Model info endpoint for cost calculation

---

## Conclusion

The LLM provider ecosystem has converged on two main patterns:

1. **OpenAI-compatible** (majority): DeepSeek, Qwen, Moonshot, Fireworks, OpenRouter, LiteLLM
2. **Native formats** (minority): Anthropic, Google Gemini

**Key takeaways for integration:**

- Always check for `reasoning_content`, `thinking`, and `thought` fields
- Handle tool call arguments as both strings and objects
- Preserve provider-specific metadata (signatures, details)
- Test streaming carefully - chunk structure varies
- Implement proper error handling for format mismatches
- Consider using LiteLLM for multi-provider support
- Monitor usage carefully - reasoning tokens can be expensive

**Future trends:**

- More providers adopting reasoning capabilities
- Standardization around OpenAI format
- Better streaming support for reasoning
- Enhanced tool calling with parallel execution
- Multimodal reasoning (vision + reasoning)
