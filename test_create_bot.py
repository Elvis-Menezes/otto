#!/usr/bin/env python3
"""
Test script to create a bot using the dummy specification.
This bypasses Otto and directly calls the create_parlant_bot tool.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from server import create_parlant_bot
import parlant.sdk as p


class MockContext:
    """Mock tool context for testing."""
    def __init__(self):
        self.plugin_data = {}


async def test_create_bot():
    """Test bot creation with dummy specification."""
    
    print("🧪 Testing Bot Creation with Dummy Specification")
    print("=" * 60)
    print()
    
    # Load the dummy spec
    with open("dummy_bot_spec.json", "r") as f:
        spec = json.load(f)
    
    print("📋 Specification loaded:")
    print(f"   Name: {spec['name']}")
    print(f"   Purpose: {spec['purpose']}")
    print(f"   Guidelines: {len(spec['guidelines'])}")
    print(f"   Journeys: {len(spec['journeys'])}")
    print()
    
    # Convert to JSON string
    spec_json = json.dumps(spec, indent=2)
    
    print("🚀 Creating bot via REST API...")
    print()
    
    # Create mock context
    context = MockContext()
    
    # Call the tool
    try:
        result = await create_parlant_bot(context, spec_json)
        
        print("✅ Bot Creation Result:")
        print("=" * 60)
        print(json.dumps(result.data, indent=2))
        print()
        
        if result.data.get("status") == "created":
            print("✅ SUCCESS! Bot created successfully!")
            print(f"   Agent ID: {result.data.get('agent_id')}")
            print(f"   Agent Name: {result.data.get('agent_name')}")
            print(f"   Guidelines Created: {result.data.get('guidelines_created')}")
            print(f"   Journeys Created: {result.data.get('journeys_created')}")
            print(f"   API Base URL: {result.data.get('api_base_url')}")
        else:
            print("❌ FAILED! Bot creation failed:")
            for error in result.data.get("errors", []):
                print(f"   - {error}")
                
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print()
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_create_bot())
    sys.exit(exit_code)
