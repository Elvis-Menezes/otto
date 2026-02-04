# Otto Bot Creator - Production Ready

A production-ready web application for creating and managing AI chatbots using the Parlant SDK with MongoDB persistence.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Web Frontend  │ ──► │  API Server     │ ──► │   Parlant    │
│   (port 3000)   │     │  (port 8801)    │     │  (port 8800) │
└─────────────────┘     └─────────────────┘     └──────────────┘
                                                       │
                                                       ▼
                                               ┌──────────────┐
                                               │   MongoDB    │
                                               │ (persistent) │
                                               └──────────────┘
```

### Key Features

- **Persistent Storage**: All agents, guidelines, journeys, and sessions persist in MongoDB
- **No Rehydration Needed**: Data survives server restarts automatically
- **Production Ready**: Single source of truth in MongoDB
- **Web Dashboard**: Modern UI for creating and managing bots
- **Chat Interface**: Built-in chat to test bots
- **REST API**: Full API for programmatic access

## Quick Start

### Prerequisites

- Python 3.10+
- MongoDB (local or Atlas)
- OpenAI API key

### Installation

```bash
# Clone and enter directory
cd request

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Configuration

Edit `.env` with your credentials:

```env
# Required
OPENAI_API_KEY=sk-your-key-here
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=parlant

# Optional
API_PORT=8801
WEB_PORT=3000
```

### Start Services

```bash
# Start all services
./start_otto.sh

# Or start individually
python server.py          # Parlant server (port 8800)
python api_server.py      # API server (port 8801)
python -m http.server 3000 --directory web  # Web UI (port 3000)
```

### Access

- **Web Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8801/docs
- **Parlant Sandbox**: http://localhost:8800

## API Endpoints

### Bots

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/bots` | List all bots |
| GET | `/bots/{id}` | Get bot details |
| POST | `/bots` | Create a new bot |
| DELETE | `/bots/{id}` | Delete a bot |

### Guidelines

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bots/{id}/guidelines` | Add guideline |
| DELETE | `/bots/{id}/guidelines/{gid}` | Delete guideline |

### Journeys

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bots/{id}/journeys` | Add journey |
| DELETE | `/bots/{id}/journeys/{jid}` | Delete journey |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bots/{id}/sessions` | Create chat session |
| POST | `/sessions/{id}/messages` | Send message |
| GET | `/sessions/{id}/messages` | Get messages |

## Creating a Bot

### Via Web UI

1. Open http://localhost:3000
2. Click "Create"
3. Fill in bot details across 3 steps:
   - Basic Info (name, purpose, tone, etc.)
   - Guidelines (behavior rules)
   - Journeys (conversation flows)
4. Click "Create Bot"

### Via API

```bash
curl -X POST http://localhost:8801/bots \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Bot",
    "purpose": "Customer support",
    "scope": "Order inquiries",
    "target_users": "Customers",
    "use_cases": ["Track order", "Get help"],
    "tone": "Friendly",
    "personality": "Helpful assistant",
    "tools": ["none"],
    "constraints": ["Be polite"],
    "guardrails": ["Verify identity"],
    "guidelines": [{
      "condition": "Customer asks about order",
      "action": "Provide tracking info",
      "criticality": "HIGH"
    }],
    "journeys": [{
      "title": "Order Help",
      "description": "Help with orders",
      "conditions": ["Order question"]
    }]
  }'
```

### Via Otto (Conversational)

1. Open Parlant Sandbox at http://localhost:8800
2. Chat with Otto to describe your bot
3. Otto will guide you through requirements
4. Otto creates the bot for you

## File Structure

```
request/
├── server.py           # Parlant server with MongoDB backing
├── api_server.py       # FastAPI REST API
├── start_otto.sh       # Startup script
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── web/
│   ├── index.html      # Web dashboard
│   ├── app.js          # Frontend logic
│   └── styles.css      # Styling
└── README.md           # This file
```

## MongoDB Collections

When using MongoDB, Parlant creates these collections:

- `agents` - Bot definitions
- `guidelines` - Behavior rules
- `journeys` - Conversation flows
- `sessions` - Chat sessions
- `events` - Session events/messages
- `customers` - User profiles

## Production Deployment

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8800 8801
CMD ["python", "server.py"]
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `MONGODB_URI` | MongoDB connection string | Required |
| `MONGODB_DATABASE` | Database name | `parlant` |
| `API_PORT` | API server port | `8801` |
| `PARLANT_API_BASE_URL` | Parlant URL | `http://localhost:8800` |

### MongoDB Atlas Setup

1. Create cluster at mongodb.com/atlas
2. Create database user
3. Whitelist your IP
4. Get connection string
5. Update `.env`:

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=parlant
```

## Troubleshooting

### Bots not persisting?

Ensure MongoDB is running and `MONGODB_URI` is correct:

```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; c=MongoClient('mongodb://localhost:27017'); print(c.server_info())"
```

### Chat not working?

1. Ensure Parlant server is running on port 8800
2. Check that the bot exists (created after server restart)
3. Verify API server is connected to Parlant

### 404 errors after restart?

This is fixed! With MongoDB backing store, bots persist automatically.

## License

MIT
