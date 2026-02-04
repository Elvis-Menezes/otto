# Composio Integration for Parlant/Otto

This module enables Otto to interact with 500+ external services (Gmail, Slack, GitHub, etc.) through natural language.

## Quick Start

### 1. Install Dependencies

```bash
pip install composio>=0.11.0
```

### 2. Set Environment Variables

Add to your `.env` file:

```env
COMPOSIO_API_KEY=your_composio_api_key_here
```

Get your API key from: https://platform.composio.dev

### 3. Connect a Service (e.g., Gmail)

```bash
python connect_gmail.py
```

Follow the prompts to authenticate with Gmail.

### 4. Start the Server

```bash
python server.py
```

Otto can now send emails, create GitHub issues, and more!

---

## Available Tools

| Tool | Description |
|------|-------------|
| `connect_composio_account` | Authenticate user with a service |
| `check_composio_connection` | Check if user is connected |
| `list_composio_tools` | List available actions for a service |
| `execute_composio_tool` | Execute any Composio action |
| `gmail_send_email` | Send an email via Gmail |
| `github_create_issue` | Create a GitHub issue |
| `github_list_repos` | List user's GitHub repositories |
| `slack_send_message` | Send a Slack message |

---

## How It Works

```
User: "Send an email to john@example.com about the meeting"
         ↓
Otto (Parlant Agent) understands intent
         ↓
Calls gmail_send_email tool
         ↓
Composio SDK uses stored OAuth token
         ↓
Gmail API sends the email
         ↓
User: "Email sent successfully!"
```

---

## Files

| File | Purpose |
|------|---------|
| `composio_tools.py` | All Composio tool definitions |
| `connect_gmail.py` | Helper script to connect Gmail |
| `test_composio.py` | Test script to verify integration |
| `server.py` | Main server (imports Composio tools) |

---

## Adding a New Service

### Step 1: Create Auth Config

1. Go to https://platform.composio.dev/auth-configs
2. Click "Create Auth Config"
3. Select your service (e.g., Notion)
4. Configure OAuth scopes
5. Copy the Auth Config ID

### Step 2: Connect User Account

```python
from composio import Composio

client = Composio(api_key="your_api_key")

connection = client.connected_accounts.link(
    user_id="user-123",
    auth_config_id="your_auth_config_id",
)

print(f"Authenticate here: {connection.redirect_url}")
```

### Step 3: Use the Service

```python
result = client.tools.execute(
    "NOTION_CREATE_PAGE",
    user_id="user-123",
    arguments={"title": "My Page", "content": "Hello!"},
)
```

---

## Supported Services (500+)

- **Communication**: Gmail, Slack, Discord, Microsoft Teams
- **Development**: GitHub, GitLab, Jira, Linear
- **Productivity**: Notion, Asana, Trello, Monday
- **CRM**: Salesforce, HubSpot, Pipedrive
- **Storage**: Google Drive, Dropbox, OneDrive
- **Calendar**: Google Calendar, Outlook Calendar
- **And many more...**

Full list: https://composio.dev/tools

---

## Testing

Run the test suite:

```bash
python test_composio.py
```

Expected output:
```
[OK] Imports: PASS
[OK] Client Initialization: PASS
[OK] API Connectivity: PASS
[OK] Tool Decorators: PASS
[OK] Server Integration: PASS

All tests passed!
```

---

## Troubleshooting

### "COMPOSIO_API_KEY not found"
- Make sure `.env` file exists in the project root
- Check the API key is correct

### "User not connected"
- Run `python connect_gmail.py` (or relevant connect script)
- Complete OAuth in browser

### "Tool execution failed"
- Check user has correct OAuth scopes
- Verify the tool name/slug is correct
- Check Composio dashboard for errors

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COMPOSIO_API_KEY` | Yes | Your Composio API key |
| `COMPOSIO_GMAIL_AUTH_CONFIG_ID` | No | Gmail Auth Config ID |
| `COMPOSIO_GITHUB_AUTH_CONFIG_ID` | No | GitHub Auth Config ID |
| `COMPOSIO_SLACK_AUTH_CONFIG_ID` | No | Slack Auth Config ID |

---

## Links

- Composio Dashboard: https://platform.composio.dev
- Composio Docs: https://docs.composio.dev
- Parlant Docs: https://parlant.io/docs
