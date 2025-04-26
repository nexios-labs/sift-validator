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
        
    @property
    def _schema(self) -> Dict[str, Validator]:
        """Expose the schema from the internal dict validator."""
        return self._dict_validator._schema
        
    @property
    def _required_keys(self) -> set:
        """Expose required keys from the internal dict validator."""
        return self._dict_validator._required_keys
        
    @property
    def _additional_properties(self) -> Any:
        """Expose additional properties setting from the internal dict validator."""
        return getattr(self._dict_validator, "_additional_properties", True)
        
    @property
    def _pattern_properties(self) -> Dict:
        """Expose pattern properties from the internal dict validator."""
        return getattr(self._dict_validator, "_pattern_properties", {})
        
    @property
    def _min_properties(self) -> Optional[int]:
        """Expose min properties from the internal dict validator."""
        return getattr(self._dict_validator, "_min_properties", None)
        
    @property
    def _max_properties(self) -> Optional[int]:
        """Expose max properties from the internal dict validator."""
        return getattr(self._dict_validator, "_max_properties", None)
        
    def _validate(self, data: Any, path: list[str | int]) -> Dict[str, Any]:
        return self._dict_validator._validate(data, path)
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> Dict[str, Any]:
        return await self._dict_validator._validate_async(data, path)

    @property
    def field_names(self) -> set[str]:
        """
        Get the field names of the schema.
        
        Returns:
            A set of field names defined in the schema.
        """
        return set(self._schema.keys())

    @property
    def fields(self) -> Dict[str, Validator]:
        """
        Get the fields of the schema.
        
        Returns:
            A dictionary of field names and their corresponding validators.
        """
        return self._schema.copy()