```python
"""
Module for defining state schemas.
"""

from typing import Dict, Any, List, Optional

class StateSchema:
    """
    A class to define the schema of a state.
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        Initialize the StateSchema with a schema dictionary.

        Args:
            schema (Dict[str, Any]): The schema dictionary.
        """
        self.schema = schema

    def validate_state(self, state: Dict[str, Any]) -> bool:
        """
        Validate if the given state is valid according to the schema.

        Args:
            state (Dict[str, Any]): The state dictionary to validate.

        Returns:
            bool: True if the state is valid, False otherwise.
        """
        for key, expected_type in self.schema.items():
            if key not in state:
                return False
            if not isinstance(state[key], expected_type):
                return False
        return True

    def get_schema(self) -> Dict[str, Any]:
        """
        Return the schema dictionary.

        Returns:
            Dict[str, Any]: The schema dictionary.
        """
        return self.schema
```