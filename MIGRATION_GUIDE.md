# Migration Guide: Old MongoDB Integration → Event-Based Persistence

## What Changed?

### Old Architecture (Removed)
- ❌ MongoDB integrated into Parlant's DI container
- ❌ Replaced `TransientDocumentDatabase` with `MongoDocumentDatabase`
- ❌ `configure_container` callback to override stores
- ❌ Dependent on Parlant schema versions
- ❌ Caused `ServerOutdated` errors on version upgrades

### New Architecture (Current)
- ✅ Parlant uses `TransientDocumentDatabase` (default, in-memory)
- ✅ MongoDB operates at application layer (event-based mirroring)
- ✅ No DI container overrides
- ✅ Independent domain schema
- ✅ No `ServerOutdated` errors
- ✅ Safe Parlant version upgrades

## Files Removed

```
mongo_config.py                    # Deleted - Parlant DI integration
```

## Files Added

```
domain_persistence.py              # New - Event-based persistence layer
domain_rehydration.py              # New - Startup rehydration logic
ARCHITECTURE.md                    # New - Architecture documentation
MIGRATION_GUIDE.md                 # This file
```

## Files Modified

```
server.py                          # Updated to use event-based persistence
requirements.txt                   # No changes (motor/pymongo still needed)
env.example                        # No changes (same MongoDB URI format)
```

## Breaking Changes

### 1. MongoDB Database Name Changed

**Old:** `otto_bots` (default)  
**New:** `otto_domain` (default)

**Why?** Different schema - old data is incompatible with new architecture.

### 2. MongoDB Schema Changed

**Old schema:** Parlant internal document format with `_schema_version`  
**New schema:** Otto domain model (see below)

#### New Collections:

```javascript
// bots
{
  bot_id: string,
  name: string,
  description: string,
  composition_mode: string,
  max_engine_iterations: int,
  metadata: object,
  created_at: datetime,
  updated_at: datetime
}

// guidelines
{
  guideline_id: string,
  bot_id: string,
  condition: string,
  action: string,
  description: string,
  criticality: string,
  created_at: datetime,
  updated_at: datetime
}

// journeys
{
  journey_id: string,
  bot_id: string,
  title: string,
  description: string,
  conditions: [string],
  created_at: datetime,
  updated_at: datetime
}

// tool_mappings
{
  bot_id: string,
  guideline_id: string,
  tool_name: string,
  created_at: datetime
}
```

### 3. Startup Sequence Changed

**Old:**
```python
# Configure MongoDB stores
server_config["configure_container"] = lambda c: configure_mongodb_stores(c, uri)

async with p.Server(**server_config) as server:
    # Create Otto
    # Parlant reads from MongoDB
```

**New:**
```python
# Initialize domain persistence
await initialize_persistence(mongodb_uri)

# Create server with defaults
async with p.Server(nlp_service=p.NLPServices.openai) as server:
    # Create Otto
    # Rehydrate bots from MongoDB
    await rehydrate_bots_from_persistence(server, persistence)
```

## Migration Steps

### Option 1: Fresh Start (Recommended)

If you don't need to preserve old bots:

1. **Update code** (already done if you pulled latest)

2. **Use new database name:**
   ```bash
   # Edit .env
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
   # Default database will be "otto_domain" (not "otto_bots")
   ```

3. **Run server:**
   ```bash
   python server.py
   ```

4. **Verify:**
   ```
   ✅ MongoDB connected: otto_domain
   💾 Domain events will persist to MongoDB
   🔄 Bots will be rehydrated on startup
   ```

5. **Old data:**
   - Old `otto_bots` database can be safely deleted
   - Or keep it as backup (won't interfere)

### Option 2: Preserve Old Bots (Manual Export/Import)

If you need to keep existing bots:

1. **Export old bots from MongoDB:**
   ```bash
   mongoexport --uri="mongodb+srv://..." \
     --db=otto_bots \
     --collection=agents \
     --out=old_bots.json
   ```

2. **Update code** (already done)

3. **Start new server:**
   ```bash
   python server.py
   ```

4. **Manually recreate bots:**
   - Open Otto UI
   - For each old bot, describe it to Otto
   - Otto will create it with new architecture

5. **Verify persistence:**
   ```bash
   # Check new database
   mongo --eval 'db.bots.find()' otto_domain
   ```

### Option 3: Use Different Database Name

Keep both old and new data:

1. **Edit `.env`:**
   ```bash
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
   MONGODB_DATABASE_NAME=otto_domain_v2
   ```

2. **Run server:**
   ```bash
   python server.py
   ```

3. **Result:**
   - Old data in `otto_bots` (unused)
   - New data in `otto_domain_v2`
   - No conflicts

## Verification Checklist

After migration, verify:

- [ ] No `mongo_config.py` file exists
- [ ] Server starts without `ServerOutdated` error
- [ ] Startup shows: "Parlant: Using TransientDocumentDatabase"
- [ ] Startup shows: "Persistence: Event-based MongoDB mirroring"
- [ ] Can create new bot via Otto
- [ ] New bot appears in MongoDB `bots` collection
- [ ] Server restart preserves bots (rehydration works)
- [ ] No `_schema_version` fields in MongoDB documents

## Testing the New Architecture

### Test 1: Persistence Works

```bash
# Start server
python server.py

# Create a test bot via Otto UI
# Message: "Create a bot called TestBot for testing"

# Check MongoDB
mongo --eval 'db.bots.find({name: "TestBot"}).pretty()' otto_domain

# Should see bot document with Otto domain schema
```

### Test 2: Rehydration Works

```bash
# Start server, create bot (as above)
# Note bot ID from logs

# Stop server (Ctrl+C)

# Restart server
python server.py

# Check logs for:
# "📥 Rehydrating 1 bot(s) from MongoDB..."
# "✅ Restored bot: TestBot (ID: ...)"

# Verify bot is available in UI
```

### Test 3: Persistence Optional

```bash
# Edit .env, comment out MONGODB_URI
# MONGODB_URI=

# Start server
python server.py

# Should see:
# "⚠️  MongoDB persistence is disabled"
# "💾 Using in-memory only (no persistence)"

# Server runs normally, just no persistence
```

## Common Issues

### Issue: ServerOutdated error

**Cause:** Old code still in place  
**Fix:** 
```bash
# Ensure mongo_config.py is deleted
rm -f mongo_config.py

# Verify server.py doesn't have configure_container callback
grep -n "configure_container" server.py  # Should only be in comments
```

### Issue: Bots not persisting

**Check logs for:**
```
💾 Persisted bot 'BotName' to MongoDB (ID: agent-xxx)
```

**If missing:**
```bash
# Check MONGODB_URI is set
cat .env | grep MONGODB_URI

# Test MongoDB connection
python3 -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient('YOUR_URI')
    await client.admin.command('ping')
    print('✅ Connected')

asyncio.run(test())
"
```

### Issue: Rehydration fails

**Check:**
1. MongoDB has data: `mongo --eval 'db.bots.count()' otto_domain`
2. Logs show rehydration attempt
3. No errors in rehydration stats

**Debug:**
```python
# Add temporary debug logging in domain_rehydration.py
print(f"DEBUG: Found {len(persisted_bots)} bots to rehydrate")
```

### Issue: Old and new data conflict

**Fix:**
```bash
# Use separate database
MONGODB_DATABASE_NAME=otto_domain_new
```

## Rollback (If Needed)

If you need to rollback to old architecture:

1. **Checkout previous commit:**
   ```bash
   git log --oneline | grep -i "mongo"  # Find commit before refactor
   git checkout <commit-hash>
   ```

2. **Restore old database:**
   ```bash
   # If you kept backup
   mongorestore --uri="..." --db=otto_bots backup/
   ```

3. **Note:** Old architecture had `ServerOutdated` issues

## Benefits of New Architecture

1. ✅ **No ServerOutdated errors**
2. ✅ **Safe Parlant upgrades** - MongoDB schema independent
3. ✅ **Cleaner code** - clear separation of concerns
4. ✅ **Optional persistence** - can disable for dev
5. ✅ **Easier testing** - mock persistence layer
6. ✅ **Better maintainability** - each layer owns its schema

## Questions?

**Q: Can I use my existing MongoDB URI?**  
A: Yes! Same URI format, just uses different database/schema.

**Q: Do I need to update MongoDB Atlas settings?**  
A: No. Network access, users, etc. remain the same.

**Q: What happens to Otto agent?**  
A: Otto is recreated on each startup (not persisted). Only user-created bots are persisted.

**Q: Can I import old bots programmatically?**  
A: Yes, but you'll need to write a custom migration script that reads old format and creates bots via Otto.

**Q: Performance impact?**  
A: Similar. Bot creation slightly slower (REST API + MongoDB write), but rehydration is fast.

---

**Summary:** The new architecture is cleaner, safer, and eliminates ServerOutdated errors. Migration is straightforward - start fresh with new database name! 🚀
