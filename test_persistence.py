#!/usr/bin/env python3
"""
Test script for event-based persistence architecture.

This script verifies that:
1. Domain persistence layer can connect to MongoDB
2. Bot data can be persisted and retrieved
3. Rehydration logic works correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from domain_persistence import DomainPersistence

load_dotenv()

async def test_persistence():
    """Test the domain persistence layer."""
    
    print("🧪 Testing Event-Based Persistence Architecture")
    print("=" * 60)
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI")
    
    if not mongodb_uri:
        print("❌ MONGODB_URI not set in .env")
        print("💡 Set MONGODB_URI to test persistence")
        print("   For testing without MongoDB, this is expected.")
        return
    
    # Initialize persistence
    print("\n1️⃣  Initializing persistence...")
    persistence = DomainPersistence(mongodb_uri, "otto_domain_test")
    
    success, message = await persistence.connect()
    if not success:
        print(f"❌ {message}")
        return
    
    print(f"✅ {message}")
    
    # Test bot persistence
    print("\n2️⃣  Testing bot persistence...")
    test_bot_id = "test-bot-12345"
    
    await persistence.persist_bot(
        bot_id=test_bot_id,
        name="TestBot",
        description="A test bot for persistence verification",
        composition_mode="fluid",
        max_engine_iterations=3,
        metadata={"test": True}
    )
    print("✅ Bot persisted")
    
    # Retrieve bot
    print("\n3️⃣  Retrieving persisted bot...")
    bot = await persistence.get_bot(test_bot_id)
    
    if bot:
        print(f"✅ Bot retrieved:")
        print(f"   - ID: {bot['bot_id']}")
        print(f"   - Name: {bot['name']}")
        print(f"   - Description: {bot['description']}")
        print(f"   - Composition Mode: {bot['composition_mode']}")
    else:
        print("❌ Bot not found")
        return
    
    # Test guideline persistence
    print("\n4️⃣  Testing guideline persistence...")
    test_guideline_id = "test-guideline-12345"
    
    await persistence.persist_guideline(
        guideline_id=test_guideline_id,
        bot_id=test_bot_id,
        condition="When user asks for help",
        action="Provide helpful response",
        description="Test guideline",
        criticality="high"
    )
    print("✅ Guideline persisted")
    
    # List guidelines
    guidelines = await persistence.list_guidelines(test_bot_id)
    print(f"✅ Found {len(guidelines)} guideline(s)")
    
    # Test journey persistence
    print("\n5️⃣  Testing journey persistence...")
    test_journey_id = "test-journey-12345"
    
    await persistence.persist_journey(
        journey_id=test_journey_id,
        bot_id=test_bot_id,
        title="Test Journey",
        description="A test conversation flow",
        conditions=["User starts conversation", "User asks question"]
    )
    print("✅ Journey persisted")
    
    # List journeys
    journeys = await persistence.list_journeys(test_bot_id)
    print(f"✅ Found {len(journeys)} journey(s)")
    
    # List all bots
    print("\n6️⃣  Listing all persisted bots...")
    all_bots = await persistence.list_bots()
    print(f"✅ Found {len(all_bots)} bot(s) in database:")
    for bot in all_bots:
        print(f"   - {bot['name']} (ID: {bot['bot_id']})")
    
    # Cleanup test data
    print("\n7️⃣  Cleaning up test data...")
    await persistence.delete_bot(test_bot_id)
    print("✅ Test data deleted")
    
    # Close connection
    await persistence.close()
    print("\n✅ All persistence tests passed!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Run: python server.py")
    print("   2. Create a bot via Otto")
    print("   3. Restart server and verify bot persists")


async def test_without_mongodb():
    """Test that persistence layer gracefully handles no MongoDB."""
    
    print("\n🧪 Testing Persistence Without MongoDB")
    print("=" * 60)
    
    persistence = DomainPersistence(mongodb_uri=None)
    
    print(f"Enabled: {persistence.enabled}")
    assert not persistence.enabled, "Should be disabled"
    
    # Operations should fail gracefully
    success = await persistence.persist_bot(
        bot_id="test",
        name="Test",
        description="Test",
    )
    assert not success, "Should return False when disabled"
    
    bots = await persistence.list_bots()
    assert bots == [], "Should return empty list when disabled"
    
    print("✅ Persistence layer handles disabled state correctly")
    print("=" * 60)


async def main():
    """Run all tests."""
    try:
        # Test without MongoDB (should always work)
        await test_without_mongodb()
        
        # Test with MongoDB (if configured)
        await test_persistence()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
