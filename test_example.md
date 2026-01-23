# Testing Otto Bot Creator

## 🧪 Quick Test Guide

Follow these steps to test Otto's bot creation capabilities.

## Step 1: Start the Server

```bash
# Kill any conflicting processes
lsof -i :8800 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :8818 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Start Otto server
python server.py
```

You should see:
```
🚀 Starting Otto Bot Creator Server...
📡 Parlant API: http://localhost:8800
⏱️  API Timeout: 30s
--------------------------------------------------
✅ Created Otto agent (ID: ...)
✅ Configured Otto with guidelines and journeys
--------------------------------------------------
🌐 Server ready at http://localhost:8800
📖 Access Sandbox UI to interact with Otto
⚡ Otto will use REST API to create bots on this server

Press Ctrl+C to stop the server
--------------------------------------------------
```

## Step 2: Access the Sandbox UI

Open your browser to:
```
http://localhost:8800
```

## Step 3: Example Conversation with Otto

### Test Case 1: Simple Bot (Minimal Info)

**You**: "I need a bot called Reva for customer support"

**Otto**: *Will ask clarifying questions like:*
- "What specific functions should Reva handle?"
- "Who are the target users?"
- "What tone should Reva use?"
- etc.

**You**: Answer each question clearly until Otto has all required info.

---

### Test Case 2: Complete Bot (Reva Example)

Use this complete description to test Otto's ability to extract all fields:

**You**: 
```
I need a bot called Reva for e-commerce customer support.

Purpose: Provide customer support for order tracking, cancellations, and refunds
Scope: Handles order status, cancellations, refunds, returns, and shipping information
Target Users: Existing customers who have placed orders
Tone: Friendly, empathetic, and efficient
Personality: Like a helpful customer service representative - warm but professional

Use Cases:
- Track order status and delivery
- Cancel orders (within 30 days)
- Request refunds
- Initiate returns
- Get shipping information

Tools: None for now, we'll integrate later

Constraints:
- 30-day cancellation policy
- Cannot refund over $500 without manager approval
- Cannot modify orders that have already shipped
- Refunds take 5-7 business days to process

Guardrails:
- Always verify order number and email before proceeding
- Ask for confirmation before cancelling or processing refunds
- Never share tracking info without verifying customer identity
- Escalate to human agent if customer is upset

Guidelines:
1. When customer asks about order status: Verify order number and email, then provide current status and tracking information
2. When customer wants to cancel: Check if within 30 days and not shipped. If eligible, confirm and process. If not, explain alternatives.
3. When customer requests refund: Verify order details and eligibility, explain the 5-7 day processing time

Journeys:
1. Order Tracking - Help customer find their order status when they ask about delivery
2. Cancellation Process - Guide through cancellation with proper verification
3. Refund Request - Process refunds following business rules
4. Return Initiation - Help customer start a return for received items
```

**Otto**: *Should extract all information and ask if anything is unclear or missing*

**You**: "Yes, that's everything. Please create the bot."

**Otto**: *Will create the bot via REST API and return:*
```
Bot created successfully!
- Agent ID: [agent-id]
- Agent Name: Reva
- Guidelines created: 3
- Journeys created: 4
- API: http://localhost:8800
```

---

### Test Case 3: Incomplete Info (Gap Detection)

**You**: "Create a support bot"

**Otto**: *Should ask specific questions:*
1. "What should I name this bot?"
2. "What is the primary purpose?"
3. "Who are the target users?"
etc.

---

## Step 4: Verify Bot Creation

### Via REST API

Check if the bot was created:

```bash
# List all agents
curl http://localhost:8800/agents

# Get specific agent (replace {agent_id} with actual ID)
curl http://localhost:8800/agents/{agent_id}

# List guidelines
curl http://localhost:8800/guidelines

# List journeys
curl http://localhost:8800/journeys
```

### Via Sandbox UI

1. In the Parlant UI, navigate to the agent list
2. Find your newly created bot (e.g., "Reva")
3. Click to view its configuration
4. Verify guidelines and journeys were created

---

## Expected Results

### ✅ Success Indicators

- [ ] Otto responds to your initial message
- [ ] Otto asks clarifying questions for missing info
- [ ] Otto summarizes gathered requirements
- [ ] Otto confirms before creating bot
- [ ] Bot creation succeeds via REST API
- [ ] Response includes agent_id and status
- [ ] Agent appears in agent list
- [ ] Guidelines and journeys are created
- [ ] No error messages in server logs

### ❌ Failure Indicators

If you see these, check the troubleshooting section:

- `Argument 'spec_json' is missing` → Otto isn't constructing the spec properly
- `API connection failed` → Parlant server isn't reachable
- `invalid JSON` → Spec construction has syntax errors
- `missing required fields` → Otto didn't gather all info

---

## Troubleshooting Test Issues

### Otto Doesn't Respond

**Symptom**: No response in chat UI

**Solutions**:
1. Check server logs for errors
2. Verify OpenAI API key is set in `.env`
3. Check browser console for errors
4. Refresh the page

### Bot Creation Fails

**Symptom**: Otto says bot creation failed

**Solutions**:
1. Check server logs: `tail -f parlant-data/parlant.log`
2. Verify all required fields were provided
3. Check `PARLANT_API_BASE_URL` points to correct server
4. Test API manually with curl commands above

### Validation Errors

**Symptom**: "missing required fields" or similar

**Solutions**:
1. Provide more complete information
2. Answer all of Otto's questions
3. Be specific and clear in responses

---

## Advanced Testing

### Test REST API Directly

Create a bot using the tool manually:

```python
import asyncio
import json
from server import create_parlant_bot
import parlant.sdk as p

async def test():
    spec = {
        "name": "TestBot",
        "purpose": "Testing",
        "scope": "Test scope",
        "target_users": "Test users",
        "use_cases": ["Test case"],
        "tone": "Friendly",
        "personality": "Helpful",
        "tools": ["none"],
        "constraints": ["Test constraint"],
        "guardrails": ["Test guardrail"],
        "guidelines": [{
            "condition": "Test condition",
            "action": "Test action"
        }],
        "journeys": [{
            "title": "Test Journey",
            "description": "Test description",
            "conditions": ["Test condition"]
        }]
    }
    
    # Simulate tool context
    class MockContext:
        plugin_data = {}
    
    result = await create_parlant_bot(
        MockContext(),
        json.dumps(spec)
    )
    
    print(json.dumps(result.data, indent=2))

asyncio.run(test())
```

### Performance Testing

Time how long bot creation takes:

```bash
# Add timing to server logs
time curl -X POST http://localhost:8800/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SpeedTest",
    "description": "Performance test bot",
    "composition_mode": "fluid"
  }'
```

---

## Sample Bots for Testing

### 1. FAQ Bot
```
Name: FAQ Assistant
Purpose: Answer common questions about our product
Scope: Product features, pricing, technical support
Target Users: Website visitors and new customers
Use Cases: [list FAQs]
Tone: Professional, helpful
Personality: Patient teacher
Tools: [knowledge base]
Constraints: [limits]
Guardrails: [safety rules]
```

### 2. Appointment Scheduler
```
Name: SchedulerBot
Purpose: Book appointments and manage calendar
Scope: Scheduling, reminders, cancellations
Target Users: Customers needing appointments
Use Cases: [scheduling scenarios]
Tone: Efficient, friendly
Personality: Organized assistant
Tools: [calendar API]
```

### 3. Sales Assistant
```
Name: SalesBot
Purpose: Qualify leads and provide product info
Scope: Product demos, pricing, lead capture
Target Users: Potential customers
Use Cases: [sales scenarios]
Tone: Persuasive, professional
Personality: Knowledgeable advisor
Tools: [CRM integration]
```

---

## Test Completion Checklist

- [ ] Server starts without errors
- [ ] Can access Sandbox UI
- [ ] Otto responds to messages
- [ ] Otto asks clarifying questions
- [ ] Otto creates bot from complete spec
- [ ] Bot appears in agent list
- [ ] Guidelines are created
- [ ] Journeys are created
- [ ] REST API endpoints work
- [ ] Server logs show no errors

---

## Getting Help

If tests fail:

1. **Check Logs**: `tail -f parlant-data/parlant.log`
2. **Review CHANGES.md**: See what was fixed
3. **Read README.md**: Full documentation
4. **Check Environment**: Verify `.env` is correct
5. **Test API**: Use curl commands to test endpoints directly

---

**Happy Testing! 🎉**
