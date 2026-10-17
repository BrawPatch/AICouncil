```python
"""
Module for managing memory.
"""

from typing import Dict, Any, Optional

class MemoryManager:
    """
    A class to manage memory storage and retrieval.
    """

    def __init__(self):
        """
        Initialize the MemoryManager.
        """
        self.memory = {}

    def set_value(self, key: str, value: Any):
        """
        Set a value in memory.

        Args:
            key (str): The key to store the value under.
            value (Any): The value to store.
        """
        self.memory[key] = value

    def get_value(self, key: str) -> Optional[Any]:
        """
        Get a value from memory.

        Args:
            key (str): The key to retrieve the value from.

        Returns:
            Optional[Any]: The value associated with the key, or None if not found.
        """
        return self.memory.get(key)

    def delete_value(self, key: str):
        """
        Delete a value from memory.

        Args:
            key (str): The key to delete.
        """
        if key in self.memory:
            del self.memory[key]

    def list_all_keys(self) -> List[str]:
        """
        List all keys in memory.

        Returns:
            List[str]: A list of all keys in memory.
        """
        return list(self.memory.keys())
```
