# MongoDB Atlas Setup Guide for Otto Bot Creator

This guide will help you set up MongoDB Atlas for persistent bot storage in 5-10 minutes.

## Why MongoDB?

Without MongoDB, bots created by Otto are stored **in-memory only** and disappear when the server restarts. With MongoDB, all bots, guidelines, and journeys persist across restarts.

## Step-by-Step Setup

### Step 1: Create MongoDB Atlas Account (2 minutes)

1. Go to [https://www.mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register)
2. Sign up with:
   - Email address
   - Or sign in with Google/GitHub
3. No credit card required for free tier
4. Complete the registration

### Step 2: Create a Free Cluster (3 minutes)

1. After login, click **"Build a Database"** (or **"Create"** if you see that)

2. **Choose deployment type:**
   - Select **"M0"** (Free tier)
   - Should show: "$0.00/month forever"

3. **Choose cloud provider & region:**
   - Provider: AWS, Google Cloud, or Azure (any works)
   - Region: Choose closest to your location for best performance
   - Example: `us-east-1` (Virginia) or `eu-west-1` (Ireland)

4. **Cluster name:**
   - Use default or enter custom name (e.g., "OttoBots")

5. Click **"Create Deployment"**
   - Takes 1-3 minutes to provision
   - You'll see a progress indicator

### Step 3: Create Database User (1 minute)

While the cluster is being created:

1. Click **"Database Access"** in the left sidebar (under Security)

2. Click **"Add New Database User"**

3. **Authentication Method:** Choose "Password"

4. **Username:** Enter a username (e.g., `otto_user`)

5. **Password:** 
   - Click "Autogenerate Secure Password" (recommended)
   - **SAVE THIS PASSWORD** - you'll need it in your .env file
   - Or create your own strong password

6. **Database User Privileges:**
   - Select **"Built-in Role"**
   - Choose **"Read and write to any database"**

7. Click **"Add User"**

### Step 4: Configure Network Access (1 minute)

1. Click **"Network Access"** in the left sidebar (under Security)

2. Click **"Add IP Address"**

3. **For development/testing:**
   - Click **"Allow Access from Anywhere"**
   - This adds `0.0.0.0/0`
   - Click **"Confirm"**

4. **For production:**
   - Click **"Add Current IP Address"** (adds your IP)
   - Or manually enter your server's IP address
   - Click **"Confirm"**

### Step 5: Get Connection String (2 minutes)

1. Click **"Database"** in the left sidebar

2. Your cluster should now show "Active" status

3. Click **"Connect"** button on your cluster

4. Choose **"Drivers"** (or "Connect your application")

5. **Select driver:**
   - Driver: Python
   - Version: 3.12 or later

6. **Copy connection string:**
   - You'll see something like:
     ```
     mongodb+srv://otto_user:<password>@cluster0.xxxxx.mongodb.net/
     ```

7. **Replace `<password>`:**
   - Replace `<password>` with the actual password you saved in Step 3
   - Example result:
     ```
     mongodb+srv://otto_user:MySecurePass123@cluster0.xxxxx.mongodb.net/
     ```

### Step 6: Configure Otto (1 minute)

1. **Copy to .env file:**
   ```bash
   cp env.example .env
   ```

2. **Edit .env:**
   ```bash
   nano .env
   # or use any text editor
   ```

3. **Add your configuration:**
   ```bash
   # Required: OpenAI API key
   OPENAI_API_KEY=sk-your-openai-key-here
   
   # Required: MongoDB connection string (the one you just got)
   MONGODB_URI=mongodb+srv://otto_user:MySecurePass123@cluster0.xxxxx.mongodb.net/
   
   # Optional: Custom database name (default: otto_bots)
   MONGODB_DATABASE_NAME=otto_bots
   ```

4. **Save the file**

### Step 7: Test Connection (1 minute)

Test that your MongoDB connection works:

```bash
python3 -c "
from pymongo import MongoClient
uri = 'YOUR_CONNECTION_STRING_HERE'
client = MongoClient(uri, serverSelectionTimeoutMS=5000)
client.admin.command('ping')
print('✅ MongoDB connection successful!')
client.close()
"
```

Replace `YOUR_CONNECTION_STRING_HERE` with your actual connection string.

### Step 8: Run Otto Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the server
python server.py
```

You should see:

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

### Step 9: Verify Persistence

1. Open `http://localhost:8800` in browser
2. Create a test bot via Otto
3. Stop the server (Ctrl+C)
4. Restart the server: `python server.py`
5. Check the UI - your test bot should still be there!

## MongoDB Atlas Dashboard

### View Your Data

1. Go to MongoDB Atlas dashboard
2. Click **"Browse Collections"** on your cluster
3. Select database: `otto_bots` (or your custom name)
4. You'll see collections:
   - `agents` - All your bots
   - `guidelines` - Bot behaviors
   - `journeys` - Conversation flows
   - `tags`, `relationships`, `evaluations`, etc.

### Monitor Usage

Free tier includes:
- 512 MB storage
- Shared RAM
- Suitable for thousands of bots
- No time limit

Check usage: Database → Metrics tab

## Troubleshooting

### Connection String Issues

**Error: Authentication failed**
- Double-check username and password
- Make sure you replaced `<password>` in connection string
- Password might need URL encoding if it has special characters:
  ```python
  from urllib.parse import quote_plus
  password = quote_plus("p@ssw0rd!")  # Becomes: p%40ssw0rd%21
  ```

**Error: Network timeout**
- Check if your IP is whitelisted in Network Access
- Or enable "Allow Access from Anywhere" (0.0.0.0/0)

**Error: Server selection timeout**
- Cluster might still be provisioning (wait a few minutes)
- Check your internet connection
- Verify connection string format

### Special Characters in Password

If your password has special characters, URL-encode them:

| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `:` | `%3A` |
| `/` | `%2F` |
| `?` | `%3F` |
| `#` | `%23` |
| `[` | `%5B` |
| `]` | `%5D` |
| `%` | `%25` |

Or use Python:
```python
from urllib.parse import quote_plus
encoded = quote_plus("your-password")
```

### Testing Locally Without MongoDB

To test without MongoDB (in-memory mode):

1. Comment out or remove `MONGODB_URI` from `.env`:
   ```bash
   # MONGODB_URI=mongodb+srv://...
   ```

2. Restart server:
   ```bash
   python server.py
   ```

3. You'll see:
   ```
   💾 MongoDB: Disabled (using in-memory storage)
   ⚠️  Bots will be lost when server restarts
   ```

## Connection String Examples

### MongoDB Atlas (Cloud)
```bash
# Standard format
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# With specific cluster name
MONGODB_URI=mongodb+srv://otto_user:pass123@ottobots.xxxxx.mongodb.net/

# Your actual connection (from env.example)
MONGODB_URI=mongodb+srv://menezeselvis1402_db_user:hqv7J6ARcLxZxTZW@ottobots.lu8dul3.mongodb.net/
```

### Local MongoDB
```bash
# Default local MongoDB
MONGODB_URI=mongodb://localhost:27017/

# With authentication
MONGODB_URI=mongodb://username:password@localhost:27017/

# With specific database
MONGODB_URI=mongodb://localhost:27017/otto_bots
```

## Security Best Practices

### For Production:

1. **Whitelist specific IPs** instead of 0.0.0.0/0
2. **Use environment variables** (don't commit .env to git)
3. **Rotate passwords** regularly
4. **Enable audit logs** in MongoDB Atlas
5. **Set up alerts** for unusual activity
6. **Use read-only users** where appropriate

### .gitignore Entry:

Make sure `.env` is in your `.gitignore`:
```bash
echo ".env" >> .gitignore
```

## Next Steps

Once MongoDB is configured:

1. ✅ All bots persist across restarts
2. ✅ Can deploy to Railway/Heroku/etc with confidence
3. ✅ Data is backed up by MongoDB Atlas
4. ✅ Can access data via MongoDB Compass or CLI
5. ✅ Production-ready storage

## MongoDB Atlas Free Tier Limits

- **Storage:** 512 MB (enough for thousands of bots)
- **RAM:** Shared (M0 instance)
- **Connections:** Up to 500 concurrent
- **Backup:** Available (manual)
- **Duration:** Forever free
- **Upgrade:** Easy upgrade to paid tier if needed

Perfect for Otto Bot Creator! 🎉

## Support

- **MongoDB Atlas Docs:** https://docs.atlas.mongodb.com/
- **Connection Issues:** https://docs.atlas.mongodb.com/troubleshoot-connection/
- **Python Driver:** https://pymongo.readthedocs.io/

---

**Your MongoDB is now configured! Bots will persist forever. 🎊**
