# Otto Bot Creator - Event-Based Persistence Architecture

## Overview

This document describes the event-based persistence architecture that completely decouples Parlant's internal storage from Otto's domain persistence layer.

## Architecture Principles

### 1. Clean Separation of Concerns

**Parlant (Execution Engine)**
- Remains fully in-memory with `TransientDocumentDatabase`
- No MongoDB integration at Parlant SDK level
- No dependency injection overrides
- No schema migrations
- Default SDK configuration

**MongoDB (Domain Persistence)**
- Operates at application layer only
- Stores domain events, not Parlant internals
- Custom schema independent of Parlant
- No knowledge of Parlant document formats
- Optional (can be disabled for development)

### 2. Event-Based Mirroring Pattern

```
User Request → Otto → Parlant API → TransientDB (in-memory)
                                           ↓
                                    MongoDB Mirror (persistent)
```

**Flow:**
1. Bot created in Parlant via REST API
2. Parlant stores in `TransientDocumentDatabase` (in-memory)
3. Application layer mirrors event to MongoDB
4. MongoDB is the source of truth
5. On restart, events are replayed into Parlant

### 3. No Parlant Internals

- ❌ Never access Parlant's `DocumentDatabase` directly
- ❌ Never override Parlant's DI container stores
- ❌ Never depend on Parlant's document schema
- ✅ Use only public Parlant SDK APIs
- ✅ Store domain concepts, not Parlant internals
- ✅ Rehydrate via SDK calls on startup

## Components

### 1. `domain_persistence.py`

**Purpose:** Domain-level persistence layer using MongoDB

**Key Classes:**
- `DomainPersistence` - Main persistence interface

**MongoDB Collections:**

```javascript
// bots collection
{
  bot_id: string,          // Parlant agent ID
  name: string,
  description: string,
  composition_mode: string,
  max_engine_iterations: int,
  metadata: object,
  created_at: datetime,
  updated_at: datetime
}

// guidelines collection
{
  guideline_id: string,    // Parlant guideline ID
  bot_id: string,          // Reference to bot
  condition: string,
  action: string,
  description: string,
  criticality: string,     // "low", "medium", "high"
  created_at: datetime,
  updated_at: datetime
}

// journeys collection
{
  journey_id: string,      // Parlant journey ID
  bot_id: string,          // Reference to bot
  title: string,
  description: string,
  conditions: [string],
  created_at: datetime,
  updated_at: datetime
}

// tool_mappings collection
{
  bot_id: string,
  guideline_id: string,
  tool_name: string,
  created_at: datetime
}
```

**Key Methods:**
- `connect()` - Initialize MongoDB connection
- `persist_bot()` - Mirror bot creation event
- `persist_guideline()` - Mirror guideline creation
- `persist_journey()` - Mirror journey creation
- `list_bots()` - Retrieve all persisted bots
- `delete_bot()` - Remove bot and related data

### 2. `domain_rehydration.py`

**Purpose:** Restore domain state from MongoDB into Parlant on startup

**Key Functions:**

```python
async def rehydrate_bots_from_persistence(
    server: p.Server,
    persistence: DomainPersistence
) -> dict[str, Any]
```

**Rehydration Flow:**
1. Read all bots from MongoDB
2. For each bot:
   - Call `server.create_agent()` with stored params
   - Parlant creates agent in `TransientDocumentDatabase`
   - Read bot's guidelines from MongoDB
   - Call `agent.create_guideline()` for each
   - Read bot's journeys from MongoDB
   - Call `agent.create_journey()` for each
3. Parlant's transient stores now match MongoDB state

**Important:** Otto agent is NOT rehydrated (created separately in `main()`)

```python
async def persist_bot_creation(
    persistence: DomainPersistence,
    agent_id: str,
    agent_name: str,
    # ... other params
) -> bool
```

**Persistence Flow:**
1. Bot already created in Parlant (in-memory)
2. Mirror bot metadata to MongoDB
3. Mirror all guidelines to MongoDB
4. Mirror all journeys to MongoDB
5. Persistence failure does not break bot creation

### 3. `server.py` - Updated Main Server

**Startup Sequence:**

```python
async def main():
    # 1. Initialize domain persistence (separate from Parlant)
    persistence_enabled, message = await initialize_persistence(MONGODB_URI)
    
    # 2. Create Parlant server with DEFAULT config
    #    No DI overrides, uses TransientDocumentDatabase
    async with p.Server(nlp_service=p.NLPServices.openai) as server:
        
        # 3. Create Otto agent
        agent = await server.create_agent(name="Otto", ...)
        
        # 4. Configure Otto's guidelines and journeys
        await agent.create_guideline(...)
        
        # 5. Rehydrate persisted bots from MongoDB
        if persistence_enabled:
            await rehydrate_bots_from_persistence(server, persistence)
        
        # 6. Start server and keep alive
        await server.wait_until_ready()
        while True:
            await asyncio.sleep(1)
```

**Bot Creation Tool (`create_parlant_bot`):**

```python
@p.tool
async def create_parlant_bot(context, spec_json) -> p.ToolResult:
    # 1. Validate spec
    spec = json.loads(spec_json)
    errors = _validate_spec(spec)
    
    # 2. Create agent via REST API (Parlant stores in-memory)
    agent_response = await _call_parlant_api("POST", "/agents", {...})
    agent_id = agent_response["id"]
    
    # 3. Create guidelines via REST API
    for guideline in spec["guidelines"]:
        await _call_parlant_api("POST", "/guidelines", {...})
    
    # 4. Create journeys via REST API
    for journey in spec["journeys"]:
        await _call_parlant_api("POST", "/journeys", {...})
    
    # 5. Mirror to MongoDB (event-based persistence)
    persistence = get_persistence()
    if persistence.enabled:
        await persist_bot_creation(
            persistence, agent_id, agent_name, ...
        )
    
    return p.ToolResult({...})
```

## Data Flow Diagrams

### Bot Creation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ User: "Create bot Hexon for order tracking"                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Otto Agent (Parlant)                                        │
│  - Extracts requirements                                    │
│  - Validates specification                                  │
│  - Calls create_parlant_bot tool                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ create_parlant_bot Tool                                     │
│                                                             │
│  1. POST /agents → Parlant Server                          │
│     ├─> TransientDocumentDatabase (RAM)                    │
│     └─> Returns agent_id                                   │
│                                                             │
│  2. POST /guidelines (for each) → Parlant Server           │
│     └─> TransientDocumentDatabase (RAM)                    │
│                                                             │
│  3. POST /journeys (for each) → Parlant Server             │
│     └─> TransientDocumentDatabase (RAM)                    │
│                                                             │
│  4. persist_bot_creation() → MongoDB (if enabled)          │
│     ├─> bots collection                                    │
│     ├─> guidelines collection                              │
│     └─> journeys collection                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Result                                                      │
│  - Bot exists in Parlant (in-memory)                       │
│  - Bot mirrored to MongoDB (persistent)                    │
│  - User receives confirmation                              │
└─────────────────────────────────────────────────────────────┘
```

### Server Restart Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Server Restart                                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Initialize Persistence                                   │
│    - Connect to MongoDB                                     │
│    - Test connection                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Create Parlant Server                                    │
│    - Default configuration                                  │
│    - TransientDocumentDatabase (empty)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Create Otto Agent                                        │
│    - server.create_agent("Otto")                           │
│    - Configure guidelines & journeys                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Rehydrate Bots from MongoDB                             │
│                                                             │
│    for bot in persistence.list_bots():                     │
│      ├─> agent = server.create_agent(bot.name, ...)       │
│      │    └─> TransientDocumentDatabase.store(agent)      │
│      │                                                      │
│      ├─> for guideline in persistence.list_guidelines():   │
│      │    └─> agent.create_guideline(...)                 │
│      │        └─> TransientDocumentDatabase.store()       │
│      │                                                      │
│      └─> for journey in persistence.list_journeys():       │
│           └─> agent.create_journey(...)                   │
│               └─> TransientDocumentDatabase.store()       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Server Ready                                             │
│    - Parlant: In-memory state matches MongoDB              │
│    - MongoDB: Source of truth                              │
│    - All bots available for use                            │
└─────────────────────────────────────────────────────────────┘
```

## Benefits of This Architecture

### 1. No ServerOutdated Errors

- Parlant always uses default `TransientDocumentDatabase`
- No schema migrations required
- No version compatibility issues
- MongoDB schema is completely independent

### 2. Parlant Version Upgrades Safe

- Upgrade Parlant SDK → No MongoDB changes needed
- Parlant breaking changes → Only affect rehydration logic
- MongoDB schema never changes with Parlant versions
- Clear upgrade path

### 3. Optional Persistence

```bash
# Disable persistence (development mode)
# MONGODB_URI=

# Enable persistence (production mode)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

### 4. Clean Separation

- Parlant team owns execution engine
- Otto team owns domain model
- No coupling between the two
- Each can evolve independently

### 5. Testability

```python
# Test without MongoDB
persistence = DomainPersistence(mongodb_uri=None)
assert not persistence.enabled

# Test with mock MongoDB
persistence = DomainPersistence(mongodb_uri="mongodb://localhost:27017")
await persistence.connect()
```

### 6. Auditability

```javascript
// MongoDB stores complete history
db.bots.find({name: "Hexon"})
// Returns full bot metadata + timestamps

db.guidelines.find({bot_id: "agent-123"})
// Returns all guidelines for a bot

// Parlant only has current runtime state
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional - Domain persistence
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Optional - Custom database name (default: otto_domain)
# Note: This is different from previous implementation
# which used "otto_bots" - this is intentional to avoid
# conflicts with old Parlant-integrated MongoDB data
```

### MongoDB Database

Default database name: `otto_domain` (not `otto_bots`)

This prevents conflicts with the old architecture where MongoDB was integrated into Parlant's stores.

## Migration from Old Architecture

### If You Had Old MongoDB Integration:

1. **Old data is incompatible** - different schema
2. **Start fresh** - new event-based approach
3. **Old database** - can be safely deleted or renamed

### Steps:

```bash
# Option 1: Use new database name (recommended)
MONGODB_DATABASE_NAME=otto_domain_v2

# Option 2: Drop old database (if you want clean slate)
python3 -c "
from pymongo import MongoClient
client = MongoClient('YOUR_URI')
client.drop_database('otto_bots')  # Old database
print('Old database dropped')
"
```

## Troubleshooting

### Q: ServerOutdated error?

**A:** This architecture eliminates that error. If you still see it:
- Check you deleted `mongo_config.py`
- Verify no `configure_container` callback in `p.Server()`
- Confirm Parlant uses default configuration

### Q: Bots not persisting?

**A:** Check:
```python
# In server startup logs, should see:
✅ MongoDB connected: otto_domain
💾 Domain events will persist to MongoDB

# When creating bot, should see:
💾 Persisted bot 'Hexon' to MongoDB (ID: agent-xxx)
```

### Q: Rehydration not working?

**A:** Check:
```python
# On startup, should see:
📥 Rehydrating N bot(s) from MongoDB...
  ✅ Restored bot: Hexon (ID: agent-xxx)
    └─ X guidelines, Y journeys
✅ Rehydration complete: ...
```

### Q: Want to disable persistence?

**A:** Comment out in `.env`:
```bash
# MONGODB_URI=mongodb+srv://...
```

Server will run in-memory only mode.

## Summary

| Aspect | Parlant | MongoDB |
|--------|---------|---------|
| **Storage** | TransientDocumentDatabase | Custom domain collections |
| **Lifetime** | Process lifetime | Permanent |
| **Schema** | Parlant internal format | Otto domain model |
| **Migrations** | Parlant SDK handles | None needed |
| **Versioning** | Parlant versions | Independent |
| **Purpose** | Runtime execution | Source of truth |
| **Updates** | Parlant team | Otto team |
| **Testing** | Always enabled | Optional |

---

**Result:** Clean, maintainable, upgrade-safe persistence architecture! 🎉
