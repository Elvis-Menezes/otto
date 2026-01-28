# Quick Start with MongoDB

This is the fastest way to get Otto running with persistent storage.

## TL;DR - 3 Commands

```bash
# 1. Copy your MongoDB connection string to .env
cp env.example .env
nano .env  # Add your OPENAI_API_KEY and MONGODB_URI

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python server.py
```

## What You Need

From your `env.example`, I can see you already have:

```bash
MONGODB_URI=mongodb+srv://menezeselvis1402_db_user:hqv7J6ARcLxZxTZW@ottobots.lu8dul3.mongodb.net/
```

## Setup Steps

### 1. Create .env file

```bash
cp env.example .env
```

Then edit `.env` and make sure you have:

```bash
# Required
OPENAI_API_KEY=sk-your-actual-openai-key

# Required for persistence
MONGODB_URI=mongodb+srv://menezeselvis1402_db_user:hqv7J6ARcLxZxTZW@ottobots.lu8dul3.mongodb.net/

# Optional
MONGODB_DATABASE_NAME=otto_bots
```

### 2. Install Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

This installs:
- parlant (core framework)
- pymongo (MongoDB driver)
- motor (async MongoDB)
- httpx (REST API calls)
- python-dotenv (environment variables)

### 3. Kill Conflicting Processes

```bash
lsof -i :8800 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :8818 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### 4. Start Server

```bash
python server.py
```

### 5. Expected Output

```
🚀 Starting Otto Bot Creator Server...
📡 Parlant API: http://localhost:8800
⏱️  API Timeout: 30s
💾 MongoDB: Enabled
🔗 Testing MongoDB connection...
✅ MongoDB connection successful
💾 Bots will persist across server restarts
--------------------------------------------------
✅ Created Otto agent (ID: ...)
✅ Configured Otto with guidelines and journeys
--------------------------------------------------
🌐 Server ready at http://localhost:8800
📖 Access Sandbox UI to interact with Otto
⚡ Otto will use REST API to create bots on this server
💾 All bots stored in MongoDB - data persists!

Press Ctrl+C to stop the server
--------------------------------------------------
```

### 6. Test It

1. Open browser: `http://localhost:8800`
2. Chat with Otto: "Create a bot called TestBot for customer support"
3. Follow Otto's questions
4. Bot is created → stored in MongoDB
5. Stop server (Ctrl+C)
6. Restart server: `python server.py`
7. Check UI → TestBot should still be there! ✅

## Verify MongoDB Storage

### Check in MongoDB Atlas

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Click **"Browse Collections"** on your cluster
3. Select database: `otto_bots`
4. View collections:
   - `agents` - See Otto + your created bots
   - `guidelines` - Bot behaviors
   - `journeys` - Conversation flows

### Check via API

```bash
# List all agents (should persist after restart)
curl http://localhost:8800/agents | jq

# Count agents
curl http://localhost:8800/agents | jq '. | length'
```

## Troubleshooting

### MongoDB Connection Fails

**If you see:**
```
❌ MongoDB connection failed: ...
⚠️  Falling back to in-memory storage
```

**Check:**
1. Connection string is correct in `.env`
2. Password doesn't have typos
3. IP address is whitelisted in MongoDB Atlas (Network Access)
4. Internet connection is working

**Quick test:**
```bash
python3 -c "
from pymongo import MongoClient
client = MongoClient('YOUR_URI_HERE', serverSelectionTimeoutMS=5000)
client.admin.command('ping')
print('✅ Connected!')
"
```

### Server Won't Start

**Port already in use:**
```bash
lsof -i :8800 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**Dependencies missing:**
```bash
pip install pymongo motor httpx parlant python-dotenv openai
```

### Bots Still Disappearing

**Check:**
1. `.env` file exists in `/home/elvis/request/`
2. `MONGODB_URI` is uncommented (no `#` at start)
3. Server startup shows "MongoDB: Enabled"
4. No connection errors in logs

## Performance

- **Bot creation:** ~500ms-2s (with MongoDB)
- **In-memory:** ~50-200ms
- **Trade-off:** Slightly slower but data persists!

## MongoDB Atlas Free Tier

What you get:
- ✅ 512 MB storage (thousands of bots)
- ✅ Forever free
- ✅ Automatic backups
- ✅ Built-in monitoring
- ✅ No credit card needed
- ✅ Upgrade anytime if needed

## Success Checklist

- [ ] MongoDB Atlas cluster created
- [ ] Database user created with password saved
- [ ] Network access configured (0.0.0.0/0 or your IP)
- [ ] Connection string copied
- [ ] `.env` file created with OPENAI_API_KEY and MONGODB_URI
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Server starts successfully
- [ ] Startup shows "MongoDB connection successful"
- [ ] Bot created and persists after restart

## Next: Create Your First Persistent Bot

Try the Reva example or TestBot:

```
"I need a bot called TestBot for customer support. 
It should handle product questions and basic troubleshooting.
Friendly tone, professional personality.
Target users are existing customers."
```

Otto will ask clarifying questions, then create the bot. After server restart, it'll still be there!

---

**You're all set! Your bots now persist in MongoDB Atlas. 🎉**
