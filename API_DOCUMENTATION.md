# AI Agent API Documentation

## Overview

Enhanced AI Agent API that processes messages sequentially through DeepSeek Reasoner and Moonshot Kiwi K2 models, providing separate outputs and advanced features.

## Base URL

```
https://your-api-domain.com
```

## Authentication

Currently uses API keys configured in environment variables. No additional authentication required for endpoints.

## Endpoints

### 1. Chat Endpoint

Process a message through both AI models and return structured responses.

**Endpoint:** `POST /chat`

**Request Body:**

```json
{
  "message": "What is artificial intelligence?",
  "include_models": ["deepseek", "moonshot"],
  "stream": false
}
```

**Parameters:**

- `message` (string, required): The user's message
- `include_models` (array, optional): Models to include in response. Default: `["deepseek", "moonshot"]`
- `stream` (boolean, optional): Enable streaming response. Default: `false`

**Response (Success):**

```json
{
  "primary_response": "Moonshot's refined response...",
  "model_outputs": {
    "deepseek": {
      "content": "DeepSeek's original reasoning...",
      "processing_time": 2.1,
      "token_count": 450,
      "model_name": "deepseek-reasoner",
      "timestamp": "2024-01-01T12:00:00"
    },
    "moonshot": {
      "content": "Moonshot's refined response...",
      "processing_time": 1.8,
      "token_count": 380,
      "model_name": "moonshot-v1-8k",
      "timestamp": "2024-01-01T12:00:02"
    }
  },
  "status": "success",
  "total_processing_time": 3.9
}
```

**Response (Error):**

```json
{
  "primary_response": "Sorry, I encountered an error...",
  "model_outputs": {},
  "status": "error",
  "error": "Error message details",
  "total_processing_time": 0.0
}
```

### 2. Streaming Chat Endpoint

Real-time streaming of model responses as they're generated.

**Usage:**
Set `stream: true` in the chat request. The response will be a stream of JSON objects.

**Stream Response Format:**

```json
{"type": "status", "data": {"status": "processing", "model": "deepseek"}}
{"type": "model_output", "data": {"model": "deepseek", "content": "...", "status": "completed"}}
{"type": "status", "data": {"status": "processing", "model": "moonshot"}}
{"type": "model_output", "data": {"model": "moonshot", "content": "...", "status": "completed"}}
{"type": "complete", "data": {"status": "success"}}
```

### 3. Compare Endpoint

Compare DeepSeek and Moonshot responses with detailed differences.

**Endpoint:** `POST /compare`

**Request Body:**

```json
{
  "message": "Explain quantum computing"
}
```

**Response:**

```json
{
  "similarity_score": 0.85,
  "differences": ["+ Added by Moonshot", "- Removed by Moonshot"],
  "deepseek_content": "DeepSeek's full response...",
  "moonshot_content": "Moonshot's full response...",
  "processing_times": {
    "deepseek": 2.1,
    "moonshot": 1.8
  }
}
```

### 4. Health Check

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy",
  "service": "ai_agent"
}
```

## Frontend Integration Examples

### Next.js Example (Non-streaming)

```javascript
async function sendMessage(message) {
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        include_models: ["deepseek", "moonshot"],
        stream: false,
      }),
    });

    const data = await response.json();

    if (data.status === "success") {
      // Display primary response
      console.log("Primary:", data.primary_response);

      // Access individual model outputs
      console.log("DeepSeek:", data.model_outputs.deepseek.content);
      console.log("Moonshot:", data.model_outputs.moonshot.content);

      // Show performance metrics
      console.log(
        "DeepSeek time:",
        data.model_outputs.deepseek.processing_time
      );
      console.log("Total time:", data.total_processing_time);
    }
  } catch (error) {
    console.error("Error:", error);
  }
}
```

### Next.js Example (Streaming)

```javascript
async function streamMessage(message, onChunk, onComplete) {
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        stream: true,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            onChunk(data);
          } catch (e) {
            console.error("Parse error:", e);
          }
        }
      }
    }

    onComplete();
  } catch (error) {
    console.error("Stream error:", error);
  }
}

// Usage
streamMessage(
  "Hello, how are you?",
  (chunk) => {
    switch (chunk.type) {
      case "status":
        console.log(`${chunk.data.model} is processing...`);
        break;
      case "model_output":
        console.log(`${chunk.data.model}: ${chunk.data.content}`);
        break;
      case "complete":
        console.log("Stream completed");
        break;
      case "error":
        console.error("Error:", chunk.data.error);
        break;
    }
  },
  () => console.log("Stream finished")
);
```

### Comparison Feature Example

```javascript
async function compareResponses(message) {
  try {
    const response = await fetch("/api/compare", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();

    console.log("Similarity:", data.similarity_score);
    console.log("Differences:", data.differences);

    // Display side-by-side comparison
    displayComparison(data.deepseek_content, data.moonshot_content);
  } catch (error) {
    console.error("Comparison error:", error);
  }
}
```

## Response Structure Details

### ModelOutput Object

- `content` (string): The model's generated response
- `processing_time` (float): Time taken in seconds
- `token_count` (int): Approximate token count (words)
- `model_name` (string): Identifier of the model used
- `timestamp` (string): ISO 8601 timestamp of when response was generated

### Comparison Features

- **Similarity Score**: 0.0 to 1.0 indicating how similar the responses are
- **Differences**: List of specific changes made by Moonshot
- **Processing Times**: Individual model performance metrics

## Error Handling

### Common Error Scenarios

1. **API Timeout**: Models taking too long to respond
2. **Rate Limits**: Hitting API provider limits
3. **Invalid Message**: Empty or malformed input
4. **Service Unavailable**: AI services temporarily down

### Error Response Format

All endpoints return consistent error formatting with `status: "error"` and detailed error messages.

## Best Practices

### For Better Performance

1. Use streaming for longer conversations
2. Cache repeated queries when possible
3. Monitor response times and adjust timeouts
4. Implement client-side retry logic for transient errors

### User Experience

1. Show model processing status in real-time
2. Display performance metrics to build trust
3. Allow users to toggle between model outputs
4. Provide comparison features for power users

## Rate Limits

Current implementation has no built-in rate limiting. Consider implementing:

- Per-user request limits
- Concurrent request limits
- Daily usage quotas

## Model Information

- **DeepSeek Reasoner**: Primary reasoning model, provides detailed analysis
- **Moonshot Kiwi K2**: Refinement model, enhances clarity and structure

## Changelog

- **v2.0**: Added separate model outputs, streaming, and comparison features
- **v1.0**: Initial sequential processing with single output
