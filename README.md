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

**Required:**
- Python 3.12+
- OpenAI API key

**Optional:**
- MongoDB Atlas account (for persistent storage)
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

## 💾 Data Persistence

By default, Otto uses **in-memory storage** - bots are stored in RAM and lost when the server restarts. To enable **persistent storage**, configure MongoDB.

### Option 1: In-Memory Storage (Default)

**Pros:**
- ✅ No setup required
- ✅ Fast (instant access)
- ✅ Good for development/testing

**Cons:**
- ❌ Bots lost on server restart
- ❌ No data recovery

**Usage:** Just run `python server.py` without MongoDB configuration.

### Option 2: MongoDB Persistent Storage (Recommended)

**Pros:**
- ✅ Bots survive server restarts
- ✅ Data recovery possible
- ✅ Production-ready
- ✅ Free tier available (MongoDB Atlas)

**Cons:**
- Requires MongoDB setup (~5 minutes)
- Slightly slower (~10-50ms network latency)

### MongoDB Atlas Setup (Free Tier)

1. **Create MongoDB Atlas account**
   - Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Sign up for free account
   - No credit card required

2. **Create a free cluster**
   - Click "Build a Database"
   - Select "M0 Free" tier
   - Choose a cloud provider and region (closest to you)
   - Click "Create"

3. **Create database user**
   - Go to "Database Access" in left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Create username and strong password
   - Set role to "Read and write to any database"
   - Click "Add User"

4. **Whitelist IP addresses**
   - Go to "Network Access" in left sidebar
   - Click "Add IP Address"
   - For testing: Click "Allow Access from Anywhere" (0.0.0.0/0)
   - For production: Add your server's specific IP
   - Click "Confirm"

5. **Get connection string**
   - Go to "Database" in left sidebar
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Select "Python" driver and version 3.12+
   - Copy the connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)
   - Replace `<password>` with your actual password

6. **Configure Otto**
   - Edit your `.env` file:
     ```bash
     MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
     ```
   - Restart the server:
     ```bash
     python server.py
     ```

7. **Verify connection**
   - Look for startup message: `✅ MongoDB connection successful`
   - Create a test bot via Otto
   - Restart server and verify bot still exists

### Storage Comparison

| Aspect | In-Memory | MongoDB Atlas |
|--------|-----------|---------------|
| **Setup Time** | 0 minutes | 5 minutes |
| **Cost** | Free | Free (M0 tier) |
| **Persistence** | ❌ Lost on restart | ✅ Survives restarts |
| **Speed** | Instant | ~10-50ms per operation |
| **Data Recovery** | ❌ Impossible | ✅ Backup available |
| **Use Case** | Development | Production |

### Data Stored in MongoDB

When MongoDB is enabled, these collections are created:

| Collection | Contains | Example |
|-----------|----------|---------|
| `agents` | All created bots | Otto, TestBot, Reva |
| `guidelines` | Bot behavior rules | "When user asks X, do Y" |
| `journeys` | Conversation flows | Order tracking, refunds |
| `tags` | Organization metadata | Agent tags |
| `relationships` | Entity connections | Guideline → Agent links |
| `sessions` | Chat conversations | Customer interactions |
| `customers` | User profiles | Customer data |

### Switching Storage Modes

**From In-Memory to MongoDB:**
1. Add `MONGODB_URI` to `.env`
2. Restart server
3. Previous in-memory bots are lost (create new ones)

**From MongoDB to In-Memory:**
1. Remove or comment out `MONGODB_URI` in `.env`
2. Restart server
3. MongoDB data remains intact (just not loaded)

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

### MongoDB Connection Failed

**Symptom:** `❌ MongoDB connection failed: ...`

**Solutions:**
1. **Check connection string format**
   ```bash
   # Should look like one of these:
   mongodb+srv://username:password@cluster.mongodb.net/
   mongodb://localhost:27017/
   ```

2. **Verify credentials**
   - Username and password are correct
   - Password doesn't contain special characters (or URL-encode them)
   - Database user has "Read and write" permissions

3. **Check network access**
   - IP address is whitelisted in MongoDB Atlas
   - Or "Allow Access from Anywhere" is enabled (0.0.0.0/0)

4. **Test connection manually**
   ```bash
   # Install mongosh (MongoDB shell)
   pip install pymongo
   python -c "from pymongo import MongoClient; MongoClient('YOUR_URI').admin.command('ping'); print('Connected!')"
   ```

5. **Fallback to in-memory**
   - Server automatically falls back if MongoDB fails
   - Remove `MONGODB_URI` to disable MongoDB completely

### Bots Disappeared After Restart

**Symptom:** Bots existed before restart, now gone

**Cause:** In-memory storage mode (no MongoDB configured)

**Solution:**
1. Set up MongoDB Atlas (see Data Persistence section)
2. Add `MONGODB_URI` to `.env`
3. Restart server
4. Recreate bots (they'll now persist)

### Slow Bot Creation

**Symptom:** Creating bots takes 10-20 seconds

**Cause:** Network latency to MongoDB Atlas

**Solutions:**
- Use MongoDB cluster in region closest to you
- Accept the latency (one-time cost per bot creation)
- Switch to local MongoDB for faster access:
  ```bash
  # Install MongoDB locally
  # Then use: MONGODB_URI=mongodb://localhost:27017/
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
