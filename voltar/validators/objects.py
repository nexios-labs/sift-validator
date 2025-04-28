"""
Object validator for class instances and typed dictionaries.
"""

from typing import Any, Dict, Type, Optional, get_type_hints, Self, Union, List, Set
from voltar .validators.base import Validator, ValidationError
from voltar .validators.collections import Dict as DictValidator

class Object(Validator[Dict[str, Any], Dict[str, Any]]):
    """
    Validator for objects/dictionaries with a specific schema.
    
    The Object validator provides several ways to modify schemas:
    - extend: Add new fields to an existing schema
    - exclude: Exclude fields during validation (fields remain in schema)
    - omit: Create new schema without specific fields
    
    Examples:
        >>> from voltar.validators.primitives import String, Number, Email
        >>> 
        >>> # Basic schema
        >>> user_schema = Object({
        ...     "name": String(),
        ...     "age": Number(),
        ...     "email": Email()
        ... })
        >>> 
        >>> # Extend schema with new fields
        >>> employee = user_schema.extend({
        ...     "department": String(),
        ...     "salary": Number()
        ... })
        >>> 
        >>> # Exclude fields during validation
        >>> user_schema.exclude("age", "email").validate({
        ...     "name": "John",
        ...     "age": 30,  # Will be ignored during validation
        ...     "email": "john@example.com"  # Will be ignored during validation
        ... })
        >>> 
        >>> # Create new schema without specific fields
        >>> name_only = user_schema.omit(["age", "email"])
        >>> name_only.validate({"name": "John"})  # Valid
        >>> name_only.validate({"name": "John", "age": 30})  # Invalid: unexpected field
    """
    
    def __init__(self, schema: Optional[Dict[str, Validator]] = None):
        """
        Initialize object validator with a schema.
        
        Args:
            schema: Dictionary mapping property names to their validators
        """
        super().__init__()
        self._dict_validator = DictValidator(schema)
        
    def extend(self, additional_schema: Dict[str, Validator]) -> Self:
        """
        Create a new validator by extending the current schema with additional fields.
        
        Args:
            additional_schema: Dictionary mapping new property names to their validators
            
        Returns:
            A new Object validator with the combined schema
            
        Example:
            >>> base = Object({"name": String(), "age": Number()})
            >>> extended = base.extend({"email": Email()})
        """
        # Create a new schema combining existing and additional fields
        extended_schema = self._schema.copy()
        
        # Check for conflicting field names
        conflicts = set(extended_schema.keys()) & set(additional_schema.keys())
        if conflicts:
            raise ValueError(f"Cannot extend schema: conflicting field names {conflicts}")
            
        extended_schema.update(additional_schema)
        
        # Create new validator instance with extended schema
        extended = Object(extended_schema)
        
        # Copy over configuration from base validator
        extended._dict_validator._additional_properties = self._additional_properties
        extended._dict_validator._pattern_properties = dict(self._pattern_properties)
        extended._dict_validator._min_properties = self._min_properties
        extended._dict_validator._max_properties = self._max_properties
        
        # Copy required fields set
        extended._dict_validator._required_keys = self._required_keys.copy()
        
        # Handle nullable/optional settings from base validator
        extended._nullable = self._nullable
        extended._optional = self._optional
        extended._default = self._default
        extended._custom_error_message = self._custom_error_message
        
        # Preserve excluded fields when extending
        if hasattr(self._dict_validator, '_excluded_fields'):
            extended._dict_validator._excluded_fields = self._dict_validator._excluded_fields.copy()
        
        return extended
        
    def exclude(self, *fields: str) -> Self:
        """
        Exclude specific fields from validation.
        
        Args:
            *fields: Field names to exclude from validation
            
        Returns:
            Self: The validator instance for chaining
            
        Example:
            >>> validator = Object({
            ...     "name": String(),
            ...     "age": Number(),
            ...     "email": Email()
            ... }).exclude("age", "email")
        """
        validator = self._clone()
        validator._dict_validator = self._dict_validator.exclude(*fields)
        return validator
        
    def omit(self, fields: Union[List[str], Set[str]]) -> Self:
        """
        Create a new schema that excludes the specified fields.
        
        Unlike exclude() which just ignores fields during validation,
        omit() creates a new schema without the specified fields.
        
        Args:
            fields: List or set of field names to omit from the schema
            
        Returns:
            A new Object validator without the specified fields
            
        Example:
            >>> schema = Object({
            ...     "name": String(),
            ...     "age": Number(),
            ...     "email": Email()
            ... })
            >>> # Creates new schema without 'age' and 'email'
            >>> without_contact = schema.omit(["age", "email"])
        """
        # Create new schema without omitted fields
        new_schema = {
            key: validator 
            for key, validator in self._schema.items()
            if key not in fields
        }
        
        # Create new validator instance
        new_validator = Object(new_schema)
        
        # Copy over configuration from base validator
        new_validator._dict_validator._additional_properties = self._additional_properties
        new_validator._dict_validator._pattern_properties = dict(self._pattern_properties)
        new_validator._dict_validator._min_properties = self._min_properties
        new_validator._dict_validator._max_properties = self._max_properties
        
        # Update required keys, removing omitted fields
        new_validator._dict_validator._required_keys = self._required_keys - set(fields)
        
        # Copy over base validator settings
        new_validator._nullable = self._nullable
        new_validator._optional = self._optional
        new_validator._default = self._default
        new_validator._custom_error_message = self._custom_error_message
        
        return new_validator
        
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