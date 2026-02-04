"""
Domain Persistence Layer for Otto Bot Creator

This module provides event-based persistence for Otto's domain model using MongoDB.
It operates completely independently of Parlant's internal storage (TransientDocumentDatabase).

Architecture:
- Parlant remains fully in-memory with TransientDocumentDatabase
- MongoDB stores only domain events and business state
- On startup, domain state is rehydrated from MongoDB into Parlant's transient stores
- No Parlant schema migrations or internal format dependencies

Persistence is optional and can be disabled for development.
"""

import os
import ssl
from datetime import datetime
from typing import Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Try to use certifi for CA certificates (recommended for MongoDB Atlas)
try:
    import certifi
    CA_FILE = certifi.where()
except ImportError:
    CA_FILE = None


class DomainPersistence:
    """
    Event-based persistence layer for Otto domain model.
    
    This class mirrors domain events to MongoDB without touching Parlant internals.
    """
    
    def __init__(self, mongodb_uri: Optional[str] = None, database_name: str = "otto_domain"):
        """
        Initialize domain persistence layer.
        
        Args:
            mongodb_uri: MongoDB connection string (None to disable persistence)
            database_name: Name of the MongoDB database for domain data
        """
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.enabled = mongodb_uri is not None and mongodb_uri.strip() != ""
    
    async def connect(self) -> tuple[bool, str]:
        """
        Connect to MongoDB and verify connection.
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.enabled:
            return False, "MongoDB persistence is disabled (no MONGODB_URI configured)"
        
        try:
            # Configure TLS for MongoDB Atlas connections
            # Increased timeout for Atlas connectivity (was 5000ms)
            connection_kwargs = {
                "serverSelectionTimeoutMS": 30000,  # 30 seconds
                "connectTimeoutMS": 30000,
                "socketTimeoutMS": 30000,
            }
            
            # Add TLS configuration if connecting to Atlas (mongodb+srv or contains mongodb.net)
            if self.mongodb_uri and ("mongodb+srv" in self.mongodb_uri or "mongodb.net" in self.mongodb_uri):
                connection_kwargs["tls"] = True
                # Use certifi CA bundle if available, otherwise allow system default
                if CA_FILE:
                    connection_kwargs["tlsCAFile"] = CA_FILE
                # Workaround for SSL handshake issues - try allowing invalid certificates
                # Note: Remove this in production after fixing the root cause
                connection_kwargs["tlsAllowInvalidCertificates"] = True
            
            self.client = AsyncIOMotorClient(self.mongodb_uri, **connection_kwargs)
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            return True, f"MongoDB connected: {self.database_name}"
        except Exception as e:
            self.enabled = False
            self.client = None
            self.db = None
            return False, f"MongoDB connection failed: {str(e)}"
    
    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    # ============================================================================
    # Bot (Agent) Persistence
    # ============================================================================
    
    async def persist_bot(
        self,
        bot_id: str,
        name: str,
        description: str,
        composition_mode: str = "fluid",
        max_engine_iterations: int = 3,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Persist a bot (agent) to MongoDB.
        
        Args:
            bot_id: Unique bot identifier from Parlant
            name: Bot name
            description: Bot description
            composition_mode: Parlant composition mode (fluid, canned_composited, canned_strict)
            max_engine_iterations: Max iterations for bot execution
            metadata: Additional bot metadata
        
        Returns:
            bool: True if persisted successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            bot_doc = {
                "bot_id": bot_id,
                "name": name,
                "description": description,
                "composition_mode": composition_mode,
                "max_engine_iterations": max_engine_iterations,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            result = await self.db.bots.update_one(
                {"bot_id": bot_id},
                {"$set": bot_doc},
                upsert=True
            )
            if result.upserted_id:
                print(f"📥 [MongoDB CREATE] Bot '{name}' (ID: {bot_id})")
            else:
                print(f"📥 [MongoDB UPSERT] Bot '{name}' (ID: {bot_id})")
            return True
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to persist bot {bot_id}: {e}")
            return False
    
    async def get_bot(self, bot_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a bot by ID."""
        if not self.enabled or self.db is None:
            return None
        
        try:
            return await self.db.bots.find_one({"bot_id": bot_id})
        except Exception:
            return None
    
    async def list_bots(self) -> list[dict[str, Any]]:
        """List all persisted bots."""
        if not self.enabled or self.db is None:
            return []
        
        try:
            cursor = self.db.bots.find({})
            return await cursor.to_list(length=None)
        except Exception:
            return []
    
    async def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot from persistence."""
        if not self.enabled or self.db is None:
            return False
        
        try:
            # Delete bot and all related data
            bot_result = await self.db.bots.delete_one({"bot_id": bot_id})
            gl_result = await self.db.guidelines.delete_many({"bot_id": bot_id})
            jr_result = await self.db.journeys.delete_many({"bot_id": bot_id})
            await self.db.tool_mappings.delete_many({"bot_id": bot_id})
            print(f"🗑️  [MongoDB DELETE] Bot (ID: {bot_id}) - removed {bot_result.deleted_count} bot, {gl_result.deleted_count} guidelines, {jr_result.deleted_count} journeys")
            return True
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to delete bot {bot_id}: {e}")
            return False
    
    async def update_bot_id(self, old_bot_id: str, new_bot_id: str) -> bool:
        """
        Update a bot's ID in MongoDB after Parlant rehydration.
        
        When Parlant restarts and rehydrates bots, it assigns new IDs.
        This method updates MongoDB to use the new ID so the web UI
        can correctly create chat sessions.
        
        Args:
            old_bot_id: The original bot ID stored in MongoDB
            new_bot_id: The new bot ID assigned by Parlant after rehydration
        
        Returns:
            bool: True if update succeeded
        """
        if not self.enabled or self.db is None:
            return False
        
        if old_bot_id == new_bot_id:
            return True  # No change needed
        
        try:
            # Update the bot document
            await self.db.bots.update_one(
                {"bot_id": old_bot_id},
                {
                    "$set": {
                        "bot_id": new_bot_id,
                        "metadata.previous_bot_id": old_bot_id,
                        "updated_at": datetime.utcnow(),
                    }
                }
            )
            
            # Update all related guidelines
            await self.db.guidelines.update_many(
                {"bot_id": old_bot_id},
                {"$set": {"bot_id": new_bot_id, "updated_at": datetime.utcnow()}}
            )
            
            # Update all related journeys
            await self.db.journeys.update_many(
                {"bot_id": old_bot_id},
                {"$set": {"bot_id": new_bot_id, "updated_at": datetime.utcnow()}}
            )
            
            # Update all related tool mappings
            await self.db.tool_mappings.update_many(
                {"bot_id": old_bot_id},
                {"$set": {"bot_id": new_bot_id}}
            )
            
            return True
        except Exception as e:
            print(f"⚠️  Failed to update bot_id {old_bot_id} → {new_bot_id}: {e}")
            return False
    
    # ============================================================================
    # Guideline Persistence
    # ============================================================================
    
    async def persist_guideline(
        self,
        guideline_id: str,
        bot_id: str,
        condition: str,
        action: Optional[str] = None,
        description: Optional[str] = None,
        criticality: str = "medium",
    ) -> bool:
        """
        Persist a guideline to MongoDB.
        
        Args:
            guideline_id: Unique guideline identifier from Parlant
            bot_id: Bot this guideline belongs to
            condition: Guideline condition/trigger
            action: Guideline action
            description: Guideline description
            criticality: Priority level (low, medium, high)
        
        Returns:
            bool: True if persisted successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            guideline_doc = {
                "guideline_id": guideline_id,
                "bot_id": bot_id,
                "condition": condition,
                "action": action,
                "description": description,
                "criticality": criticality,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            result = await self.db.guidelines.update_one(
                {"guideline_id": guideline_id},
                {"$set": guideline_doc},
                upsert=True
            )
            if result.upserted_id:
                print(f"📥 [MongoDB CREATE] Guideline (ID: {guideline_id}) for bot {bot_id} - condition: '{condition[:50]}...'")
            else:
                print(f"📥 [MongoDB UPSERT] Guideline (ID: {guideline_id}) for bot {bot_id}")
            return True
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to persist guideline {guideline_id}: {e}")
            return False
    
    async def list_guidelines(self, bot_id: str) -> list[dict[str, Any]]:
        """List all guidelines for a bot."""
        if not self.enabled or self.db is None:
            return []
        
        try:
            cursor = self.db.guidelines.find({"bot_id": bot_id})
            return await cursor.to_list(length=None)
        except Exception:
            return []

    async def update_guideline(
        self,
        guideline_id: str,
        condition: Optional[str] = None,
        action: Optional[str] = None,
        description: Optional[str] = None,
        criticality: Optional[str] = None,
    ) -> bool:
        """
        Update a guideline in MongoDB.
        
        Args:
            guideline_id: Guideline ID to update
            condition: New condition (optional)
            action: New action (optional)
            description: New description (optional)
            criticality: New criticality (optional)
        
        Returns:
            bool: True if updated successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            update_fields = {"updated_at": datetime.utcnow()}
            if condition is not None:
                update_fields["condition"] = condition
            if action is not None:
                update_fields["action"] = action
            if description is not None:
                update_fields["description"] = description
            if criticality is not None:
                update_fields["criticality"] = criticality
            
            result = await self.db.guidelines.update_one(
                {"guideline_id": guideline_id},
                {"$set": update_fields}
            )
            fields_updated = [k for k in update_fields.keys() if k != "updated_at"]
            print(f"📝 [MongoDB UPDATE] Guideline (ID: {guideline_id}) - fields: {fields_updated}, matched: {result.matched_count}, modified: {result.modified_count}")
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to update guideline {guideline_id}: {e}")
            return False

    async def delete_guideline(self, guideline_id: str) -> bool:
        """
        Delete a guideline from MongoDB.
        
        Args:
            guideline_id: Guideline ID to delete
        
        Returns:
            bool: True if deleted successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            result = await self.db.guidelines.delete_one({"guideline_id": guideline_id})
            print(f"🗑️  [MongoDB DELETE] Guideline (ID: {guideline_id}) - deleted: {result.deleted_count}")
            return result.deleted_count > 0
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to delete guideline {guideline_id}: {e}")
            return False
    
    # ============================================================================
    # Journey Persistence
    # ============================================================================
    
    async def persist_journey(
        self,
        journey_id: str,
        bot_id: str,
        title: str,
        description: str,
        conditions: list[str],
    ) -> bool:
        """
        Persist a journey to MongoDB.
        
        Args:
            journey_id: Unique journey identifier from Parlant
            bot_id: Bot this journey belongs to
            title: Journey title
            description: Journey description
            conditions: List of journey trigger conditions
        
        Returns:
            bool: True if persisted successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            journey_doc = {
                "journey_id": journey_id,
                "bot_id": bot_id,
                "title": title,
                "description": description,
                "conditions": conditions,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            result = await self.db.journeys.update_one(
                {"journey_id": journey_id},
                {"$set": journey_doc},
                upsert=True
            )
            if result.upserted_id:
                print(f"📥 [MongoDB CREATE] Journey '{title}' (ID: {journey_id}) for bot {bot_id}")
            else:
                print(f"📥 [MongoDB UPSERT] Journey '{title}' (ID: {journey_id}) for bot {bot_id}")
            return True
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to persist journey {journey_id}: {e}")
            return False
    
    async def list_journeys(self, bot_id: str) -> list[dict[str, Any]]:
        """List all journeys for a bot."""
        if not self.enabled or self.db is None:
            return []
        
        try:
            cursor = self.db.journeys.find({"bot_id": bot_id})
            return await cursor.to_list(length=None)
        except Exception:
            return []

    async def update_journey(
        self,
        journey_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[list[str]] = None,
    ) -> bool:
        """
        Update a journey in MongoDB.
        
        Args:
            journey_id: Journey ID to update
            title: New title (optional)
            description: New description (optional)
            conditions: New conditions list (optional)
        
        Returns:
            bool: True if updated successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            update_fields = {"updated_at": datetime.utcnow()}
            if title is not None:
                update_fields["title"] = title
            if description is not None:
                update_fields["description"] = description
            if conditions is not None:
                update_fields["conditions"] = conditions
            
            result = await self.db.journeys.update_one(
                {"journey_id": journey_id},
                {"$set": update_fields}
            )
            fields_updated = [k for k in update_fields.keys() if k != "updated_at"]
            print(f"📝 [MongoDB UPDATE] Journey (ID: {journey_id}) - fields: {fields_updated}, matched: {result.matched_count}, modified: {result.modified_count}")
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to update journey {journey_id}: {e}")
            return False

    async def delete_journey(self, journey_id: str) -> bool:
        """
        Delete a journey from MongoDB.
        
        Args:
            journey_id: Journey ID to delete
        
        Returns:
            bool: True if deleted successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            result = await self.db.journeys.delete_one({"journey_id": journey_id})
            print(f"🗑️  [MongoDB DELETE] Journey (ID: {journey_id}) - deleted: {result.deleted_count}")
            return result.deleted_count > 0
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to delete journey {journey_id}: {e}")
            return False

    # ============================================================================
    # Bot Update (for mirroring)
    # ============================================================================

    async def update_bot(
        self,
        bot_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        composition_mode: Optional[str] = None,
        max_engine_iterations: Optional[int] = None,
    ) -> bool:
        """
        Update a bot in MongoDB.
        
        Args:
            bot_id: Bot ID to update
            name: New name (optional)
            description: New description (optional)
            composition_mode: New composition mode (optional)
            max_engine_iterations: New max iterations (optional)
        
        Returns:
            bool: True if updated successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            update_fields = {"updated_at": datetime.utcnow()}
            if name is not None:
                update_fields["name"] = name
            if description is not None:
                update_fields["description"] = description
            if composition_mode is not None:
                update_fields["composition_mode"] = composition_mode
            if max_engine_iterations is not None:
                update_fields["max_engine_iterations"] = max_engine_iterations
            
            result = await self.db.bots.update_one(
                {"bot_id": bot_id},
                {"$set": update_fields}
            )
            fields_updated = [k for k in update_fields.keys() if k != "updated_at"]
            print(f"📝 [MongoDB UPDATE] Bot (ID: {bot_id}) - fields: {fields_updated}, matched: {result.matched_count}, modified: {result.modified_count}")
            return result.modified_count > 0 or result.matched_count > 0
        except Exception as e:
            print(f"⚠️  [MongoDB ERROR] Failed to update bot {bot_id}: {e}")
            return False
    
    # ============================================================================
    # Tool Mapping Persistence
    # ============================================================================
    
    async def persist_tool_mapping(
        self,
        bot_id: str,
        guideline_id: str,
        tool_name: str,
    ) -> bool:
        """
        Persist a tool-to-guideline mapping.
        
        Args:
            bot_id: Bot identifier
            guideline_id: Guideline identifier
            tool_name: Name of the tool
        
        Returns:
            bool: True if persisted successfully
        """
        if not self.enabled or self.db is None:
            return False
        
        try:
            mapping_doc = {
                "bot_id": bot_id,
                "guideline_id": guideline_id,
                "tool_name": tool_name,
                "created_at": datetime.utcnow(),
            }
            
            await self.db.tool_mappings.update_one(
                {"bot_id": bot_id, "guideline_id": guideline_id, "tool_name": tool_name},
                {"$set": mapping_doc},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"⚠️  Failed to persist tool mapping: {e}")
            return False
    
    async def list_tool_mappings(self, bot_id: str) -> list[dict[str, Any]]:
        """List all tool mappings for a bot."""
        if not self.enabled or self.db is None:
            return []
        
        try:
            cursor = self.db.tool_mappings.find({"bot_id": bot_id})
            return await cursor.to_list(length=None)
        except Exception:
            return []


# Global persistence instance (initialized in main)
_persistence: Optional[DomainPersistence] = None


def get_persistence() -> DomainPersistence:
    """Get the global persistence instance."""
    global _persistence
    if _persistence is None:
        raise RuntimeError("Persistence not initialized. Call initialize_persistence() first.")
    return _persistence


async def initialize_persistence(mongodb_uri: Optional[str] = None) -> tuple[bool, str]:
    """
    Initialize the global persistence layer.
    
    Args:
        mongodb_uri: MongoDB connection string (None to disable)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    global _persistence
    _persistence = DomainPersistence(mongodb_uri)
    return await _persistence.connect()


async def shutdown_persistence():
    """Shutdown the global persistence layer."""
    global _persistence
    if _persistence:
        await _persistence.close()
        _persistence = None
