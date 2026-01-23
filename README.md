# Otto Bot Creator Server 🤖

**Otto** is a Parlant-based orchestrator agent that converts business bot descriptions into fully configured Parlant bots via RESTful APIs.

## 🎯 Overview

Otto acts as an intelligent bot creation assistant that:
- ✅ Collects bot requirements through conversational interaction
- ✅ Detects gaps and asks clarifying questions
- ✅ Validates complete specifications
- ✅ Creates bots via Parlant REST APIs (agents, guidelines, journeys)
- ✅ Ensures production-ready bot configurations

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key
- Virtual environment (recommended)

### Installation

1. **Clone/navigate to the project directory**
   ```bash
   cd /home/elvis/request
   ```

2. **Activate virtual environment**
   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example and edit with your values
   cp env.example .env
   
   # Edit .env and add your OpenAI API key
   nano .env
   ```

5. **Kill any conflicting processes** (if ports are in use)
   ```bash
   # Kill processes on ports 8800 and 8818
   lsof -i :8800 | grep LISTEN | awk '{print $2}' | xargs kill -9
   lsof -i :8818 | grep LISTEN | awk '{print $2}' | xargs kill -9
   ```

6. **Run the server**
   ```bash
   python server.py
   ```

The server will start on `http://localhost:8800`

## 🎮 Usage

### Access the Sandbox UI

Open your browser to:
```
http://localhost:8800
```

### Interact with Otto

1. **Describe your bot**
   ```
   "I need a bot called Reva for e-commerce customer support"
   ```

2. **Answer Otto's clarification questions**
   - Otto will ask about: purpose, scope, users, use cases, tone, tools, constraints, guardrails
   - Provide clear, specific answers

3. **Review and confirm**
   - Otto will summarize your requirements
   - Confirm when ready

4. **Bot creation**
   - Otto validates the spec
   - Calls REST APIs to create: agent → guidelines → journeys
   - Returns bot details with agent ID

## 🔧 How It Works

### Architecture

```
Business User
    ↓
Otto Agent (Orchestrator)
    ↓
create_parlant_bot Tool
    ↓
Parlant REST APIs
    ├── POST /agents          (Create agent)
    ├── POST /guidelines      (Create guidelines)
    └── POST /journeys        (Create journeys)
    ↓
Configured Bot Created ✅
```

### REST API Integration

Otto uses the `create_parlant_bot` tool which makes secure REST API calls:

**1. Agent Creation**
```http
POST http://localhost:8800/agents
Content-Type: application/json

{
  "name": "Reva",
  "description": "E-commerce support bot...",
  "composition_mode": "fluid",
  "max_engine_iterations": 3
}
```

**2. Guideline Creation**
```http
POST http://localhost:8800/guidelines
Content-Type: application/json

{
  "condition": "Customer asks about order status",
  "action": "Verify order and provide tracking",
  "criticality": "high"
}
```

**3. Journey Creation**
```http
POST http://localhost:8800/journeys
Content-Type: application/json

{
  "title": "Order Tracking",
  "description": "Help customer find order status",
  "conditions": ["When customer asks about delivery"]
}
```

### Required Bot Specification Fields

Otto collects these **required** fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Bot name |
| `purpose` | string | Bot's primary purpose |
| `scope` | string | What the bot handles |
| `target_users` | string | Who will use the bot |
| `use_cases` | array | List of specific use cases |
| `tone` | string | Communication tone |
| `personality` | string | Bot personality traits |
| `tools` | array | Required integrations (use `["none"]` if none) |
| `constraints` | array | Business rules/limitations |
| `guardrails` | array | Safety measures |
| `guidelines` | array | Bot behavior rules |
| `journeys` | array | Customer interaction flows |

**Optional fields:**
- `composition_mode`: `"FLUID"` (default), `"COMPOSITED"`, `"STRICT"`
- `max_engine_iterations`: Integer (default: 3)

## 📋 Example Bot Specification

<details>
<summary>Click to see complete Reva example</summary>

```json
{
  "name": "Reva",
  "purpose": "E-commerce customer support for order tracking and returns",
  "scope": "Order status, cancellations, refunds, returns, shipping info",
  "target_users": "Existing customers with placed orders",
  "use_cases": [
    "Track order status",
    "Cancel an order",
    "Request a refund",
    "Initiate a return"
  ],
  "tone": "Friendly, empathetic, efficient",
  "personality": "Helpful customer service rep - warm and professional",
  "tools": ["none"],
  "constraints": [
    "30-day cancellation policy",
    "Cannot refund over $500 without approval",
    "Cannot modify shipped orders"
  ],
  "guardrails": [
    "Always verify order number and email",
    "Confirm before cancelling or refunding",
    "Escalate upset customers to human agents"
  ],
  "guidelines": [
    {
      "condition": "Customer asks about order status",
      "action": "Verify order number and email, then provide tracking info",
      "criticality": "HIGH"
    },
    {
      "condition": "Customer wants to cancel an order",
      "action": "Check eligibility (within 30 days, not shipped), confirm and process",
      "criticality": "HIGH"
    }
  ],
  "journeys": [
    {
      "title": "Order Tracking",
      "description": "Help customer find their order status",
      "conditions": ["When customer asks where their order is"]
    },
    {
      "title": "Cancellation Process",
      "description": "Guide customer through order cancellation",
      "conditions": ["When customer wants to cancel an order"]
    }
  ],
  "composition_mode": "FLUID",
  "max_engine_iterations": 3
}
```

</details>

## 🔒 Security Features

- ✅ **Request validation**: All specs validated before API calls
- ✅ **Timeout protection**: Configurable API timeouts (default 30s)
- ✅ **Error handling**: Graceful degradation with detailed error messages
- ✅ **Type safety**: Strict schema validation
- ✅ **Safe defaults**: Sensible fallbacks for optional parameters

## 🛠️ Configuration

### Environment Variables

Edit `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (defaults shown)
PARLANT_API_BASE_URL=http://localhost:8800
PARLANT_API_TIMEOUT=30
```

### Custom Ports

Modify `server.py` if ports conflict:

```python
async with p.Server(
    nlp_service=p.NLPServices.openai,
    port=8801,              # Change main port
    tool_service_port=8819  # Change tool service port
) as server:
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill processes on conflicting ports
lsof -i :8800 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :8818 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### OpenAI API Key Not Set
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY
```

### Module Not Found
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### API Connection Failed
- Ensure Parlant server is running on the configured URL
- Check `PARLANT_API_BASE_URL` in `.env`
- Verify firewall/network settings

## 📚 API Reference

### Otto Guidelines

Otto follows these behavioral rules:

1. **Requirement Extraction** (HIGH priority)
   - Extract all required fields from user description
   - Summarize clearly before proceeding

2. **Gap Detection** (HIGH priority)
   - Ask ONE focused question at a time
   - Explain why each detail matters

3. **Specification Building** (MEDIUM priority)
   - Construct detailed guidelines and journeys
   - Apply best practices for bot design

4. **Bot Creation** (HIGH priority)
   - Validate complete specification
   - Call REST API only when all fields confirmed
   - Return detailed creation results

### REST API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agents` | POST | Create agent |
| `/guidelines` | POST | Create guideline |
| `/journeys` | POST | Create journey |

See [Parlant API Docs](https://www.parlant.io/docs/api/) for full reference.

## 📝 Development

### Project Structure

```
/home/elvis/request/
├── server.py              # Main server with Otto orchestrator
├── requirements.txt       # Python dependencies
├── env.example           # Environment variable template
├── .env                  # Your environment config (gitignored)
├── parlant-data/         # Parlant data directory
└── README.md            # This file
```

### Key Functions

- `_validate_spec()`: Validates bot specification schema
- `_call_parlant_api()`: Makes secure REST API calls
- `create_parlant_bot()`: Tool that creates bots via API
- `main()`: Initializes Otto and keeps server running

## 🤝 Contributing

To extend Otto's capabilities:

1. Add new guidelines in `main()` function
2. Update `REQUIRED_SPEC_FIELDS` if adding fields
3. Modify `_validate_spec()` for new validation rules
4. Update this README with changes

## 📄 License

This project uses [Parlant](https://parlant.io) which is licensed under Apache 2.0.

## 🆘 Support

- **Parlant Docs**: https://parlant.io/docs
- **GitHub Issues**: Report bugs and request features
- **Discord**: Join the Parlant community

---

**Built with [Parlant](https://parlant.io) - The agent orchestration framework**
