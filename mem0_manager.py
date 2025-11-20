# mem0_manager.py
from mem0 import MemoryClient as Memory
from typing import List, Dict, Any

import logging

# configure module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

class MemoryManager:
    def __init__(self):
        """Initialize mem0 memory client with actual API"""
        # Get API key from environment variable
        api_key = "m0-uEWorjOakaOeEuvYORRsexjlDHkDZeLI9umvmRjL"
        if not api_key:
            raise ValueError("MEM0_API_KEY environment variable is required")
        
        self.memory_client = Memory(api_key=api_key)
    
    def add_memory(self, user_id: str, memory_text: str, memory_type: str = "preference", **kwargs) -> Dict[str, Any]:
        """Add a new memory for the user"""
        try:
            message = [{"role": "user", "content": memory_text}]
            # Using the new API format with text instead of messages
            memory = self.memory_client.add(
                user_id=user_id,
                messages=message,
                memory_type=memory_type,
                **kwargs
            )
            return {"success": True, "memory": memory}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memories(self, user_id: str, limit: int = 10, offset: int = 0, memory_type: str = None) -> List[Dict[str, Any]]:
        """Retrieve memories for a user using get_all with filters"""
        try:
            # Build filters for user_id
            filters = {
                "AND": [
                    {
                        "user_id": user_id
                    }
                ]
            }
            
            # Add memory_type filter if specified
            if memory_type:
                filters["AND"].append({
                    "memory_type": memory_type
                })
            
            # Use get_all with filters
            memories = self.memory_client.get_all(
                filters=filters,
                limit=limit,
                offset=offset,
                version="v2"
            )
            return memories
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return []
    
    def search_memories(self, user_id: str, query: str, limit: int = 5, memory_type: str = None, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search memories using semantic search with filters and similarity threshold"""
        try:
            # Build filters for user_id
            filters = {
                "OR": [
                    {
                        "user_id": user_id
                    }
                ]
            }
            
            # Add memory_type filter if specified
            if memory_type:
                filters["OR"].append({
                    "memory_type": memory_type
                })
            
            # Use search with filters
            memories = self.memory_client.search(
                query=query,
                filters=filters,
                limit=limit,
                version="v2"
            )
            
            # Filter results by similarity score (threshold >= 0.5)
            filtered_memories = []
            for memory in memories['results']:
                # Check if memory has a score and it meets the threshold
                score = memory.get('score', 0)
                if score >= threshold:
                    filtered_memories.append(memory)

            logger.info(f"Search query: '{query}' returned '{filtered_memories}'")        
            
            return filtered_memories
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    def update_memory(self, memory_id: str, updated_text: str) -> Dict[str, Any]:
        """Update an existing memory"""
        try:
            updated_memory = self.memory_client.update(
                memory_id=memory_id,
                text=updated_text
            )
            return {"success": True, "memory": updated_memory}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a specific memory"""
        try:
            result = self.memory_client.delete(memory_id=memory_id)
            return {"success": True, "message": "Memory deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clear_user_memories(self, user_id: str) -> Dict[str, Any]:
        """Clear all memories for a user"""
        try:
            # Get all memories for the user and delete them one by one
            self.memory_client.delete_all(user_id=user_id)
            return {"success": True, "message": f"All memories cleared for user {user_id}"}
        except Exception as e:
            return {"success": False, "error": str(e)}