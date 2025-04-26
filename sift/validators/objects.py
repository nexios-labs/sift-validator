"""
Object validator for class instances and typed dictionaries.
"""

from typing import Any, Dict, Type, Optional, get_type_hints
from sift.validators.base import Validator, ValidationError
from sift.validators.collections import Dict as DictValidator

class Object(Validator[Dict[str, Any], Dict[str, Any]]):
    """
    Validator for objects/dictionaries with a specific schema.
    """
    
    def __init__(self, schema: Optional[Dict[str, Validator]] = None):
        """
        Initialize object validator with a schema.
        
        Args:
            schema: Dictionary mapping property names to their validators
        """
        super().__init__()
        self._dict_validator = DictValidator(schema)
        
    def _validate(self, data: Any, path: list[str | int]) -> Dict[str, Any]:
        return self._dict_validator._validate(data, path)
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> Dict[str, Any]:
        return await self._dict_validator._validate_async(data, path)