# AI Agent System

A Python-based AI system that sequentially processes user prompts using DeepSeek Reasoner and Moonshot Kiwi K2 APIs.

## Architecture

The system processes user prompts through two AI APIs in sequence:

1. **DeepSeek Reasoner API** - Primary reasoning and analysis
2. **Moonshot Kiwi K2 API** - Refinement and enhancement

## Features

- 🚀 FastAPI web service for Railway deployment
- 🔄 Sequential API processing with error handling
- 📝 Modular design for easy extensibility
- 🔒 Environment-based configuration
- 📊 Basic logging and monitoring
- 🌐 CORS enabled for Firebase integration

## Project Structure

```
ai_agent/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── orchestrator.py     # Main orchestration logic
│   └── handlers/
│       ├── base.py         # Base API handler class
│       ├── deepseek.py     # DeepSeek API handler
│       └── moonshot.py     # Moonshot API handler
├── config/
│   └── settings.py         # Configuration management
├── requirements.txt        # Python dependencies
├── railway.toml           # Railway deployment config
└── .env.example           # Environment variables template
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required environment variables:

- `DEEPSEEK_API_KEY` - Your DeepSeek API key
- `MOONSHOT_API_KEY` - Your Moonshot API key

### 3. Run Locally

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST `/chat`

Process a user message through both AI APIs.

**Request:**

```json
{
  "message": "Your question or prompt here"
}
```

**Response:**

```json
{
  "response": "Processed AI response",
  "status": "success",
  "error": null
}
```

### GET `/health`

Health check endpoint.

### GET `/`

Service status endpoint.

## Deployment to Railway

1. Push your code to a Git repository
2. Connect your repository to Railway
3. Add environment variables in Railway dashboard:
   - `DEEPSEEK_API_KEY`
   - `MOONSHOT_API_KEY`
4. Deploy automatically

## Firebase Integration

Your Firebase website can call the chat endpoint:

```javascript
// Example Firebase integration
const response = await fetch("https://your-railway-app.up.railway.app/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: userInput,
  }),
});

const data = await response.json();
console.log(data.response);
```

## Error Handling

- If DeepSeek API fails, the system falls back to Moonshot-only processing
- All errors are logged to `ai_agent.log`
- Structured error responses for frontend handling

## Future Extensibility

The modular design allows easy integration of:

- Additional AI APIs
- Local models (HuggingFace, etc.)
- Authentication systems
- Rate limiting
- Advanced logging and monitoring

## Development

- Logs are written to both console and file
- Environment-based configuration
- Type hints and comprehensive error handling
