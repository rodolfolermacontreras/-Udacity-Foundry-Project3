"""
Long-Term Memory System for the Travel Concierge Agent

Provides persistent memory storage with:
- Importance-based scoring
- Memory pruning strategies
- Memory reordering
- Cosmos DB integration for persistence (optional)
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """A single memory item in long-term storage"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    content: str = ""
    memory_type: str = "general"  # general, preference, fact, tool_result
    importance_score: float = 0.5
    access_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "last_accessed": self.last_accessed.isoformat() if isinstance(self.last_accessed, datetime) else self.last_accessed,
            "tags": self.tags,
            "metadata": self.metadata,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create MemoryItem from dictionary"""
        created_at = data.get("created_at", datetime.now())
        last_accessed = data.get("last_accessed", datetime.now())
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(last_accessed, str):
            last_accessed = datetime.fromisoformat(last_accessed)
            
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            content=data.get("content", ""),
            memory_type=data.get("memory_type", "general"),
            importance_score=data.get("importance_score", 0.5),
            access_count=data.get("access_count", 0),
            created_at=created_at,
            last_accessed=last_accessed,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding")
        )


class LongTermMemory:
    """
    Long-term memory system with importance scoring and pruning.
    
    Features:
    - Memory persistence (in-memory or Cosmos DB)
    - Importance-based scoring
    - Automatic pruning of low-importance memories
    - Memory consolidation
    - Tag-based organization
    """
    
    def __init__(
        self,
        max_memories: int = 1000,
        importance_threshold: float = 0.3,
        use_cosmos: bool = False
    ):
        """
        Initialize long-term memory.
        
        Args:
            max_memories: Maximum number of memories to store
            importance_threshold: Minimum importance score to keep
            use_cosmos: Whether to use Cosmos DB for persistence
        """
        self.max_memories = max_memories
        self.importance_threshold = importance_threshold
        self.use_cosmos = use_cosmos
        self.memories: List[MemoryItem] = []
        self._cosmos_client = None
        self._container = None
        
        if use_cosmos:
            self._init_cosmos()
    
    def _init_cosmos(self) -> None:
        """Initialize Cosmos DB connection"""
        try:
            from azure.cosmos import CosmosClient
            
            endpoint = os.environ.get("COSMOS_ENDPOINT")
            key = os.environ.get("COSMOS_KEY")
            db_name = os.environ.get("COSMOS_DB", "ragdb")
            container_name = os.environ.get("COSMOS_MEMORY_CONTAINER", "memories")
            
            if endpoint and key:
                self._cosmos_client = CosmosClient(url=endpoint, credential=key)
                database = self._cosmos_client.get_database_client(db_name)
                self._container = database.get_container_client(container_name)
                logger.info(f"Connected to Cosmos DB for long-term memory: {db_name}/{container_name}")
            else:
                logger.warning("Cosmos DB credentials not found, using in-memory storage")
                self.use_cosmos = False
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {e}")
            self.use_cosmos = False
    
    def add_memory(
        self,
        session_id: str,
        content: str,
        memory_type: str = "general",
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryItem:
        """
        Add a new memory.
        
        Args:
            session_id: Session identifier
            content: Memory content
            memory_type: Type of memory (general, preference, fact, tool_result)
            importance_score: Importance score (0.0 - 1.0)
            tags: List of tags for organization
            metadata: Additional metadata
            
        Returns:
            The created MemoryItem
        """
        memory = MemoryItem(
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.memories.append(memory)
        
        # Store in Cosmos DB if enabled
        if self.use_cosmos and self._container:
            try:
                doc = memory.to_dict()
                doc["pk"] = session_id  # Partition key
                self._container.upsert_item(doc)
            except Exception as e:
                logger.error(f"Failed to store memory in Cosmos DB: {e}")
        
        # Prune if necessary
        if len(self.memories) > self.max_memories:
            self._prune_memories()
        
        return memory
    
    def get_memories(
        self,
        session_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """
        Retrieve memories with optional filtering.
        
        Args:
            session_id: Filter by session ID
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            min_importance: Minimum importance score
            limit: Maximum number of results
            
        Returns:
            List of matching MemoryItems
        """
        results = self.memories.copy()
        
        if session_id:
            results = [m for m in results if m.session_id == session_id]
        
        if memory_type:
            results = [m for m in results if m.memory_type == memory_type]
        
        if tags:
            results = [m for m in results if any(t in m.tags for t in tags)]
        
        if min_importance is not None:
            results = [m for m in results if m.importance_score >= min_importance]
        
        # Sort by importance and recency
        results.sort(key=lambda m: (m.importance_score, m.last_accessed), reverse=True)
        
        # Update access counts for returned memories
        for memory in results[:limit]:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
        
        return results[:limit]
    
    def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryItem]:
        """
        Search memories by content.
        
        Args:
            query: Search query
            session_id: Optional session filter
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        query_lower = query.lower()
        results = []
        
        for memory in self.memories:
            if session_id and memory.session_id != session_id:
                continue
            
            if query_lower in memory.content.lower():
                results.append(memory)
                memory.access_count += 1
                memory.last_accessed = datetime.now()
        
        results.sort(key=lambda m: m.importance_score, reverse=True)
        return results[:limit]
    
    def update_importance(self, memory_id: str, new_score: float) -> bool:
        """
        Update the importance score of a memory.
        
        Args:
            memory_id: Memory identifier
            new_score: New importance score (0.0 - 1.0)
            
        Returns:
            True if updated, False if not found
        """
        for memory in self.memories:
            if memory.id == memory_id:
                memory.importance_score = max(0.0, min(1.0, new_score))
                return True
        return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted, False if not found
        """
        for i, memory in enumerate(self.memories):
            if memory.id == memory_id:
                del self.memories[i]
                return True
        return False
    
    def _prune_memories(self) -> int:
        """
        Remove low-importance memories to stay within limits.
        
        Returns:
            Number of memories pruned
        """
        original_count = len(self.memories)
        
        # Remove memories below importance threshold
        self.memories = [
            m for m in self.memories 
            if m.importance_score >= self.importance_threshold
        ]
        
        # If still over limit, remove oldest low-importance memories
        if len(self.memories) > self.max_memories:
            self.memories.sort(
                key=lambda m: (m.importance_score, m.access_count, m.last_accessed),
                reverse=True
            )
            self.memories = self.memories[:self.max_memories]
        
        pruned = original_count - len(self.memories)
        if pruned > 0:
            logger.info(f"Pruned {pruned} memories")
        
        return pruned
    
    def consolidate_memories(self, session_id: str) -> int:
        """
        Consolidate similar memories to reduce redundancy.
        
        Args:
            session_id: Session to consolidate
            
        Returns:
            Number of memories consolidated
        """
        # Simple consolidation: merge memories with similar content
        session_memories = [m for m in self.memories if m.session_id == session_id]
        to_remove = []
        
        for i, m1 in enumerate(session_memories):
            for j, m2 in enumerate(session_memories[i+1:], i+1):
                # Simple similarity check (could be enhanced with embeddings)
                if m1.content.lower() == m2.content.lower():
                    # Keep the one with higher importance
                    if m1.importance_score >= m2.importance_score:
                        to_remove.append(m2.id)
                    else:
                        to_remove.append(m1.id)
        
        # Remove duplicates
        for memory_id in set(to_remove):
            self.delete_memory(memory_id)
        
        return len(set(to_remove))
    
    def get_context_for_session(self, session_id: str, max_items: int = 20) -> str:
        """
        Get a context string from memories for a session.
        
        Args:
            session_id: Session identifier
            max_items: Maximum memories to include
            
        Returns:
            Formatted context string
        """
        memories = self.get_memories(session_id=session_id, limit=max_items)
        
        if not memories:
            return ""
        
        context_parts = ["Previous context:"]
        for memory in memories:
            context_parts.append(f"- [{memory.memory_type}] {memory.content}")
        
        return "\n".join(context_parts)
    
    def export_memories(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Export memories as dictionaries.
        
        Args:
            session_id: Optional filter by session
            
        Returns:
            List of memory dictionaries
        """
        memories = self.memories
        if session_id:
            memories = [m for m in memories if m.session_id == session_id]
        return [m.to_dict() for m in memories]
    
    def import_memories(self, data: List[Dict[str, Any]]) -> int:
        """
        Import memories from dictionaries.
        
        Args:
            data: List of memory dictionaries
            
        Returns:
            Number of memories imported
        """
        count = 0
        for item in data:
            try:
                memory = MemoryItem.from_dict(item)
                self.memories.append(memory)
                count += 1
            except Exception as e:
                logger.error(f"Failed to import memory: {e}")
        
        return count
    
    def clear(self, session_id: Optional[str] = None) -> int:
        """
        Clear memories.
        
        Args:
            session_id: Optional - only clear this session
            
        Returns:
            Number of memories cleared
        """
        if session_id:
            original = len(self.memories)
            self.memories = [m for m in self.memories if m.session_id != session_id]
            return original - len(self.memories)
        else:
            count = len(self.memories)
            self.memories = []
            return count
    
    def __len__(self) -> int:
        return len(self.memories)
    
    def __repr__(self) -> str:
        return f"LongTermMemory(memories={len(self.memories)}, max={self.max_memories})"

