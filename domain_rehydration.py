"""
Domain Rehydration Module

This module handles restoring persisted bots from MongoDB into Parlant's in-memory stores
on server startup. It bridges the gap between persistent MongoDB storage and transient
Parlant execution.

CRITICAL: Rehydration must run AFTER Parlant server is fully ready!
Call `await server.wait_until_ready()` before calling rehydrate_bots_from_persistence().

Flow:
1. Wait for Parlant server to be fully initialized
2. Read all bots from MongoDB (source of truth)
3. Recreate each bot in Parlant using SDK calls
4. Use OLD bot_id for MongoDB reads, NEW agent object for Parlant writes
5. Parlant populates its TransientDocumentDatabase naturally

ID Mapping:
- MongoDB stores the original bot_id from when the bot was first created
- On rehydration, Parlant generates NEW IDs (this is expected)
- We use OLD IDs to query related data from MongoDB
- NEW IDs are used within Parlant's runtime
"""

from typing import Any
import parlant.sdk as p
from domain_persistence import DomainPersistence


def _normalize_composition_mode(mode: str | None) -> str:
    """
    Normalize composition mode string to lowercase.
    
    Handles variations like "FLUID", "Fluid", "fluid" → "fluid"
    """
    if mode is None:
        return "fluid"
    return mode.lower().strip()


def _normalize_criticality(criticality: str | None) -> str:
    """
    Normalize criticality string to lowercase.
    
    Handles variations like "HIGH", "High", "high" → "high"
    """
    if criticality is None:
        return "medium"
    return criticality.lower().strip()


async def rehydrate_bots_from_persistence(
    server: p.Server,
    persistence: DomainPersistence,
) -> dict[str, Any]:
    """
    Rehydrate all bots from MongoDB into Parlant's in-memory stores.
    
    IMPORTANT: This must be called AFTER `await server.wait_until_ready()`
    to ensure Parlant's engine, tool registry, and stores are fully initialized.
    
    Args:
        server: Parlant server instance (must be fully ready)
        persistence: Domain persistence layer
    
    Returns:
        dict: Statistics about rehydration including:
            - enabled: bool
            - bots_restored: int
            - guidelines_restored: int
            - journeys_restored: int
            - errors: list[str]
            - message: str
            - id_mapping: dict[str, str] (old_bot_id -> new_parlant_id)
    """
    if not persistence.enabled:
        return {
            "enabled": False,
            "bots_restored": 0,
            "guidelines_restored": 0,
            "journeys_restored": 0,
            "errors": [],
            "id_mapping": {},
            "message": "Persistence disabled - no rehydration needed"
        }
    
    stats = {
        "enabled": True,
        "bots_restored": 0,
        "guidelines_restored": 0,
        "journeys_restored": 0,
        "errors": [],
        "id_mapping": {},  # old_bot_id -> new_parlant_id
    }
    
    try:
        # Get all persisted bots from MongoDB (source of truth)
        persisted_bots = await persistence.list_bots()
        
        if not persisted_bots:
            stats["message"] = "No persisted bots found - starting fresh"
            return stats
        
        # Count non-Otto bots
        bots_to_restore = [b for b in persisted_bots if b.get("name") != "Otto"]
        print(f"📥 Rehydrating {len(bots_to_restore)} bot(s) from MongoDB...")
        
        # Composition mode mapping (normalized to lowercase)
        composition_mode_map = {
            "fluid": p.CompositionMode.FLUID,
            "canned_fluid": p.CompositionMode.FLUID,  # Fallback
            "canned_composited": p.CompositionMode.COMPOSITED,
            "composited": p.CompositionMode.COMPOSITED,  # Alternative
            "canned_strict": p.CompositionMode.STRICT,
            "strict": p.CompositionMode.STRICT,  # Alternative
        }
        
        # Criticality mapping (normalized to lowercase)
        criticality_map = {
            "low": p.Criticality.LOW,
            "medium": p.Criticality.MEDIUM,
            "high": p.Criticality.HIGH,
        }
        
        for bot_doc in persisted_bots:
            try:
                # OLD bot_id from MongoDB - used for querying related data
                old_bot_id = bot_doc["bot_id"]
                bot_name = bot_doc.get("name", "Unknown")
                
                # Skip Otto - it's created separately in main() before rehydration
                # This prevents duplicate Otto agents
                if bot_name == "Otto":
                    print(f"  ⏭️  Skipping Otto (system agent, created in main)")
                    continue
                
                # Normalize composition mode to handle case variations
                raw_composition_mode = bot_doc.get("composition_mode", "fluid")
                normalized_mode = _normalize_composition_mode(raw_composition_mode)
                composition_mode = composition_mode_map.get(
                    normalized_mode,
                    p.CompositionMode.FLUID  # Default fallback
                )
                
                # Recreate bot in Parlant (generates NEW ID)
                agent = await server.create_agent(
                    name=bot_name,
                    description=bot_doc.get("description", ""),
                    composition_mode=composition_mode,
                    max_engine_iterations=bot_doc.get("max_engine_iterations", 3),
                )
                
                # Store ID mapping for reference
                new_parlant_id = agent.id
                stats["id_mapping"][old_bot_id] = new_parlant_id
                
                # CRITICAL: Update MongoDB with the new Parlant ID so chat works!
                # The web UI uses the bot_id from MongoDB to create sessions
                if old_bot_id != new_parlant_id:
                    try:
                        await persistence.update_bot_id(old_bot_id, new_parlant_id)
                        print(f"  🔄 Updated MongoDB bot_id: {old_bot_id} → {new_parlant_id}")
                    except Exception as e:
                        print(f"  ⚠️  Failed to update bot_id in MongoDB: {e}")
                        stats["errors"].append(f"ID update failed for {bot_name}: {e}")
                
                stats["bots_restored"] += 1
                print(f"  ✅ Restored bot: {bot_name}")
                print(f"      MongoDB ID: {old_bot_id}")
                print(f"      Parlant ID: {new_parlant_id}")
                
                # Track per-bot counts
                bot_guidelines_count = 0
                bot_journeys_count = 0
                
                # Rehydrate guidelines using OLD bot_id for MongoDB query
                guidelines = await persistence.list_guidelines(old_bot_id)
                for guideline_doc in guidelines:
                    try:
                        # Normalize criticality
                        raw_criticality = guideline_doc.get("criticality", "medium")
                        normalized_criticality = _normalize_criticality(raw_criticality)
                        criticality = criticality_map.get(
                            normalized_criticality,
                            p.Criticality.MEDIUM
                        )
                        
                        # Create guideline on NEW agent object
                        await agent.create_guideline(
                            condition=guideline_doc.get("condition", ""),
                            action=guideline_doc.get("action"),
                            description=guideline_doc.get("description"),
                            criticality=criticality,
                        )
                        stats["guidelines_restored"] += 1
                        bot_guidelines_count += 1
                    except Exception as e:
                        error_msg = f"Guideline for {bot_name}: {e}"
                        stats["errors"].append(error_msg)
                        print(f"      ⚠️  Failed guideline: {e}")
                
                # Rehydrate journeys using OLD bot_id for MongoDB query
                journeys = await persistence.list_journeys(old_bot_id)
                for journey_doc in journeys:
                    try:
                        # Create journey on NEW agent object
                        await agent.create_journey(
                            title=journey_doc.get("title", ""),
                            description=journey_doc.get("description", ""),
                            conditions=journey_doc.get("conditions", []),
                        )
                        stats["journeys_restored"] += 1
                        bot_journeys_count += 1
                    except Exception as e:
                        error_msg = f"Journey for {bot_name}: {e}"
                        stats["errors"].append(error_msg)
                        print(f"      ⚠️  Failed journey: {e}")
                
                print(f"      └─ {bot_guidelines_count} guidelines, {bot_journeys_count} journeys")
                
            except Exception as e:
                bot_name = bot_doc.get("name", "unknown")
                error_msg = f"Failed to restore bot {bot_name}: {e}"
                stats["errors"].append(error_msg)
                print(f"  ❌ {error_msg}")
        
        stats["message"] = (
            f"Rehydration complete: {stats['bots_restored']} bots, "
            f"{stats['guidelines_restored']} guidelines, "
            f"{stats['journeys_restored']} journeys"
        )
        
        if stats["errors"]:
            stats["message"] += f" ({len(stats['errors'])} errors)"
        
        print(f"✅ {stats['message']}")
        
    except Exception as e:
        stats["message"] = f"Rehydration failed: {str(e)}"
        stats["errors"].append(str(e))
        print(f"❌ {stats['message']}")
    
    return stats


async def persist_bot_creation(
    persistence: DomainPersistence,
    agent_id: str,
    agent_name: str,
    agent_description: str,
    composition_mode: str,
    max_engine_iterations: int,
    guidelines: list[dict[str, Any]],
    journeys: list[dict[str, Any]],
) -> bool:
    """
    Persist a newly created bot and all its components to MongoDB.
    
    This is called after a bot is created in Parlant to mirror it to MongoDB.
    
    Args:
        persistence: Domain persistence layer
        agent_id: Parlant agent ID
        agent_name: Bot name
        agent_description: Bot description
        composition_mode: Parlant composition mode
        max_engine_iterations: Max iterations
        guidelines: List of guideline dicts with (id, condition, action, criticality)
        journeys: List of journey dicts with (id, title, description, conditions)
    
    Returns:
        bool: True if all persistence operations succeeded
    """
    if not persistence.enabled:
        return False
    
    try:
        # Persist bot
        await persistence.persist_bot(
            bot_id=agent_id,
            name=agent_name,
            description=agent_description,
            composition_mode=composition_mode,
            max_engine_iterations=max_engine_iterations,
        )
        
        # Persist guidelines
        for guideline in guidelines:
            if "id" in guideline:  # Only persist successfully created guidelines
                await persistence.persist_guideline(
                    guideline_id=guideline["id"],
                    bot_id=agent_id,
                    condition=guideline.get("condition", ""),
                    action=guideline.get("action"),
                    description=guideline.get("description"),
                    criticality=guideline.get("criticality", "medium"),
                )
        
        # Persist journeys
        for journey in journeys:
            if "id" in journey:  # Only persist successfully created journeys
                await persistence.persist_journey(
                    journey_id=journey["id"],
                    bot_id=agent_id,
                    title=journey.get("title", ""),
                    description=journey.get("description", ""),
                    conditions=journey.get("conditions", []),
                )
        
        return True
    except Exception as e:
        print(f"⚠️  Failed to persist bot creation to MongoDB: {e}")
        return False
