# app/memory.py
"""
Short-term Memory System for Travel Concierge Agent
Implements a sliding window memory with token management.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid
import tiktoken


class ShortTermMemory:
    """
    Short-term memory system for session-based context management.
    
    Features:
    - Sliding window eviction based on max_items and max_tokens
    - Support for conversation, tool call, and system event storage
    - Memory search and filtering capabilities
    - Export/import functionality
    """
    
    def __init__(self, max_items: int = 10, max_tokens: int = 2000):
        """
        Initialize short-term memory.
        
        Args:
            max_items: Maximum number of memory items to keep
            max_tokens: Maximum total tokens across all items
        """
        self.max_items = max_items
        self.max_tokens = max_tokens
        self.memory_items: List[Dict[str, Any]] = []
        self.total_tokens: int = 0
        self.session_id: str = str(uuid.uuid4())
        self.created_at: datetime = datetime.utcnow()
        
        # Initialize tokenizer for token counting
        try:
            self._encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        except Exception:
            # Fallback to cl100k_base if model not found
            self._encoding = tiktoken.get_encoding("cl100k_base")
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        try:
            return len(self._encoding.encode(text))
        except Exception:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4 + 1
    
    def _evict_if_needed(self):
        """Evict oldest items if limits are exceeded."""
        # Evict by item count
        while len(self.memory_items) > self.max_items:
            removed = self.memory_items.pop(0)
            self.total_tokens -= removed.get('tokens', 0)
        
        # Evict by token count
        while self.total_tokens > self.max_tokens and self.memory_items:
            removed = self.memory_items.pop(0)
            self.total_tokens -= removed.get('tokens', 0)
        
        # Ensure total_tokens doesn't go negative
        self.total_tokens = max(0, self.total_tokens)
    
    def add_conversation(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a conversation message to memory.
        
        Args:
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
            metadata: Optional metadata dictionary
        """
        tokens = self._estimate_tokens(content)
        
        item = {
            'role': role,
            'content': content,
            'tokens': tokens,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self.memory_items.append(item)
        self.total_tokens += tokens
        self._evict_if_needed()
    
    def add_tool_call(self, tool_name: str, input_data: Dict[str, Any], 
                      output_data: Any, success: bool = True):
        """
        Add a tool call record to memory.
        
        Args:
            tool_name: Name of the tool called
            input_data: Input parameters to the tool
            output_data: Output from the tool
            success: Whether the tool call succeeded
        """
        content = f"Tool call: {tool_name}"
        tokens = self._estimate_tokens(content) + self._estimate_tokens(str(output_data))
        
        item = {
            'role': 'assistant',
            'content': content,
            'tokens': tokens,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {
                'type': 'tool_call',
                'tool_name': tool_name,
                'input': input_data,
                'output': output_data,
                'success': success
            }
        }
        
        self.memory_items.append(item)
        self.total_tokens += tokens
        self._evict_if_needed()
    
    def add_system_event(self, event: str, data: Dict[str, Any] = None):
        """
        Add a system event to memory.
        
        Args:
            event: Description of the event
            data: Optional event data
        """
        tokens = self._estimate_tokens(event)
        
        item = {
            'role': 'system',
            'content': event,
            'tokens': tokens,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {
                'type': 'system_event',
                'event': event,
                'data': data or {}
            }
        }
        
        self.memory_items.append(item)
        self.total_tokens += tokens
        self._evict_if_needed()
    
    def get_conversation_history(self, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Get the conversation history.
        
        Args:
            include_metadata: Whether to include metadata in the response
            
        Returns:
            List of conversation items
        """
        if include_metadata:
            return self.memory_items.copy()
        
        return [
            {
                'role': item['role'],
                'content': item['content'],
                'timestamp': item['timestamp']
            }
            for item in self.memory_items
        ]
    
    def get_recent_conversation(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent n conversation items.
        
        Args:
            n: Number of items to retrieve
            
        Returns:
            List of recent conversation items
        """
        return self.memory_items[-n:] if self.memory_items else []
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current memory state.
        
        Returns:
            Dictionary with memory statistics
        """
        memory_usage = (len(self.memory_items) / self.max_items * 100) if self.max_items > 0 else 0
        
        return {
            'session_id': self.session_id,
            'total_items': len(self.memory_items),
            'total_tokens': self.total_tokens,
            'max_items': self.max_items,
            'max_tokens': self.max_tokens,
            'memory_usage_percent': memory_usage,
            'oldest_item': self.memory_items[0]['timestamp'] if self.memory_items else None,
            'newest_item': self.memory_items[-1]['timestamp'] if self.memory_items else None
        }
    
    def search_memory(self, query: str, role_filter: str = None) -> List[Dict[str, Any]]:
        """
        Search through memory for items matching the query.
        
        Args:
            query: Search query string
            role_filter: Optional role to filter by
            
        Returns:
            List of matching memory items
        """
        query_lower = query.lower()
        results = []
        
        for item in self.memory_items:
            # Apply role filter if specified
            if role_filter and item['role'] != role_filter:
                continue
            
            # Search in content
            if query_lower in item['content'].lower():
                results.append(item)
                continue
            
            # Search in metadata (for tool calls)
            metadata = item.get('metadata', {})
            if metadata.get('tool_name', '').lower() == query_lower:
                results.append(item)
        
        return results
    
    def clear_memory(self):
        """Clear all memory items."""
        self.memory_items = []
        self.total_tokens = 0
    
    def export_memory(self, filepath: str):
        """
        Export memory to a JSON file.
        
        Args:
            filepath: Path to save the memory file
        """
        data = {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'max_items': self.max_items,
            'max_tokens': self.max_tokens,
            'total_tokens': self.total_tokens,
            'memory_items': self.memory_items
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_memory(self, filepath: str):
        """
        Import memory from a JSON file.
        
        Args:
            filepath: Path to the memory file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.session_id = data.get('session_id', str(uuid.uuid4()))
        self.created_at = datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat()))
        self.max_items = data.get('max_items', self.max_items)
        self.max_tokens = data.get('max_tokens', self.max_tokens)
        self.total_tokens = data.get('total_tokens', 0)
        self.memory_items = data.get('memory_items', [])
    
    def get_context_window(self, max_tokens: int = None) -> str:
        """
        Get a formatted context window for the conversation.
        
        Args:
            max_tokens: Optional maximum tokens for the context
            
        Returns:
            Formatted string of the conversation context
        """
        if not self.memory_items:
            return "No conversation history."
        
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        context_parts = []
        current_tokens = 0
        
        # Start from the most recent and work backwards
        for item in reversed(self.memory_items):
            item_tokens = item.get('tokens', 0)
            
            if current_tokens + item_tokens > max_tokens:
                break
            
            role = item['role'].upper()
            content = item['content']
            context_parts.insert(0, f"{role}: {content}")
            current_tokens += item_tokens
        
        return '\n'.join(context_parts)
    
    def __str__(self) -> str:
        return f"ShortTermMemory(session_id={self.session_id}, items={len(self.memory_items)})"
    
    def __repr__(self) -> str:
        return f"ShortTermMemory(session_id={self.session_id}, items={len(self.memory_items)}, tokens={self.total_tokens})"