"""
Utility for converting Sift schemas to Pydantic models.

This module provides functionality to convert Sift validator schemas 
into equivalent Pydantic model classes with appropriate type hints
and validation constraints.
"""

from typing import Any, Dict, List as ListType, Optional, Set, Tuple, Type, Union as UnionType, get_type_hints
import inspect
import re

# Import Pydantic
from pydantic import BaseModel, Field, EmailStr, validator, constr, conint, confloat, create_model

# Import Sift validators
from sift.validators.base import Validator, ValidationError
from sift.validators.primitives import String, Number, Boolean, Any as SiftAny, Null
from sift.validators.collections import List, Dict as SiftDict, Tuple as SiftTuple, Union
from sift.validators.objects import Object

class SchemaConverter:
    """
    Converts Sift validator schemas to Pydantic models.
    
    This class analyzes Sift validators and their chain modifiers to create
    equivalent Pydantic model classes with proper type hints and validation.
    """
    
    def __init__(self):
        self.model_registry = {}  # Cache for created models to avoid duplicates
        
    def convert_schema(self, schema: Dict[str, Validator], model_name: str = "GeneratedModel") -> Type[BaseModel]:
        """
        Converts a Sift schema dictionary to a Pydantic model class.
        
        Args:
            schema: Dictionary mapping field names to Sift validators
            model_name: Name for the generated Pydantic model class
            
        Returns:
            A Pydantic model class with fields derived from the schema
        """
        field_definitions = {}
        
        for field_name, validator in schema.items():
            field_type, field_info = self._convert_validator(validator, field_name)
            field_definitions[field_name] = (field_type, field_info)
        
        # Create and return the Pydantic model
        model = create_model(model_name, **field_definitions)
        return model
    
    def convert_object(self, obj_validator: Object, class_name: str = "GeneratedModel") -> Type[BaseModel]:
        """
        Converts a Sift Object validator to a Pydantic model class.
        
        Args:
            obj_validator: Sift Object validator instance
            class_name: Name for the generated Pydantic model class
            
        Returns:
            A Pydantic model class with fields derived from the Object schema
        """
        # Get the schema from the Object validator
        schema = obj_validator._schema
        return self.convert_schema(schema, class_name)
    
    def _convert_validator(self, validator: Validator, field_name: str = None) -> Tuple[Type, Any]:
        """
        Converts a Sift validator to a Pydantic field type and constraints.
        
        Args:
            validator: Sift validator instance
            field_name: Optional name of the field (for error messages)
            
        Returns:
            Tuple containing (Python type, Field object or None)
        """
        # Extract common validator attributes
        is_optional = getattr(validator, "_optional", False)
        is_nullable = getattr(validator, "_nullable", False)
        default_value = getattr(validator, "_default", None)
        custom_error = getattr(validator, "_custom_error_message", None)
        
        # Base field parameters
        field_params = {}
        
        # Handle default value
        if default_value is not None:
            if callable(default_value) and not isinstance(default_value, type):
                # For callable defaults, use ... and add a validator later
                field_params["default_factory"] = default_value
            else:
                field_params["default"] = default_value
        
        # Process validator based on its type
        if isinstance(validator, String):
            return self._convert_string_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Number):
            return self._convert_number_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Boolean):
            return self._convert_boolean_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, List):
            return self._convert_list_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, SiftDict):
            return self._convert_dict_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Object):
            return self._convert_object_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Union):
            return self._convert_union_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, SiftAny):
            return self._convert_any_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Null):
            return self._convert_null_validator(validator, field_params)
        elif isinstance(validator, SiftTuple):
            return self._convert_tuple_validator(validator, field_params, is_optional, is_nullable)
        else:
            # Default to Any for unknown validators
            py_type = Any
            
            if is_optional or is_nullable:
                py_type = Optional[py_type]
                
            return py_type, Field(**field_params) if field_params else None
    
    def _convert_string_validator(self, validator: String, field_params: Dict[str, Any], 
                               is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert String validator to Pydantic field."""
        # Start with basic string type
        py_type = str
        
        # Extract constraints
        min_length = getattr(validator, "_min_length", None)
        max_length = getattr(validator, "_max_length", None)
        pattern = getattr(validator, "_pattern", None)
        is_email = getattr(validator, "_is_email", False)
        
        # Apply constraints
        if min_length is not None:
            field_params["min_length"] = min_length
        
        if max_length is not None:
            field_params["max_length"] = max_length
            
        if pattern is not None:
            field_params["regex"] = pattern
        
        # Handle special types
        if is_email:
            py_type = EmailStr
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_number_validator(self, validator: Number, field_params: Dict[str, Any],
                               is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Number validator to Pydantic field."""
        # Check if integer-specific
        is_int = getattr(validator, "_integer", False)
        py_type = int if is_int else float
        
        # Extract constraints
        min_value = getattr(validator, "_min_value", None)
        max_value = getattr(validator, "_max_value", None)
        multiple_of = getattr(validator, "_multiple_of", None)
        
        # Apply constraints
        if min_value is not None:
            field_params["ge"] = min_value
        
        if max_value is not None:
            field_params["le"] = max_value
            
        if multiple_of is not None:
            field_params["multiple_of"] = multiple_of
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_boolean_validator(self, validator: Boolean, field_params: Dict[str, Any],
                                is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Boolean validator to Pydantic field."""
        py_type = bool
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_list_validator(self, validator: List, field_params: Dict[str, Any],
                             is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert List validator to Pydantic field."""
        # Handle item type
        item_validator = getattr(validator, "_item_validator", None)
        if item_validator:
            item_type, _ = self._convert_validator(item_validator)
        else:
            item_type = Any
            
        py_type = ListType[item_type]
        
        # Extract constraints
        min_items = getattr(validator, "_min_items", None)
        max_items = getattr(validator, "_max_items", None)
        
        # Apply constraints
        if min_items is not None:
            field_params["min_items"] = min_items
        
        if max_items is not None:
            field_params["max_items"] = max_items
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_dict_validator(self, validator: Dict, field_params: Dict[str, Any],
                             is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Dict validator to Pydantic field."""
        # For simple Dict without schema, use Dict[str, Any]
        if not hasattr(validator, "_schema") or not validator._schema:
            py_type = Dict[str, Any]
        else:
            # For Dict with typed schema, this will be handled by Object conversion
            model = self.convert_schema(validator._schema)
            py_type = model
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_object_validator(self, validator: Object, field_params: Dict[str, Any],
                              is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Object validator to Pydantic field."""
        # Generate model class for this object
        schema = validator._schema
        model_name = f"NestedModel_{len(self.model_registry)}"
        model = self.convert_schema(schema, model_name)
        
        # Add to registry
        self.model_registry[model_name] = model
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[model]
        else:
            py_type = model
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_union_validator(self, validator: Union, field_params: Dict[str, Any],
                             is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Union validator to Pydantic field."""
        # Get the union types
        union_validators = getattr(validator, "_validators", [])
        union_types = []
        
        for v in union_validators:
            type_, _ = self._convert_validator(v)
            union_types.append(type_)
        
        # Create Union type
        if union_types:
            py_type = UnionType[tuple(union_types)]
        else:
            py_type = Any
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_any_validator(self, validator: SiftAny, field_params: Dict[str, Any],
                           is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Any validator to Pydantic field."""
        py_type = Any
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None
    
    def _convert_null_validator(self, validator: Null, field_params: Dict[str, Any]) -> Tuple[Type, Any]:
        """Convert Null validator to Pydantic field."""
        py_type = Optional[Any]
        return py_type, Field(default=None, **field_params)
    
    def _convert_tuple_validator(self, validator: SiftTuple, field_params: Dict[str, Any],
                             is_optional: bool, is_nullable: bool) -> Tuple[Type, Any]:
        """Convert Tuple validator to Pydantic field."""
        # Get the tuple item validators
        item_validators = getattr(validator, "_item_validators", [])
        item_types = []
        
        for v in item_validators:
            type_, _ = self._convert_validator(v)
            item_types.append(type_)
        
        # Create Tuple type
        if item_types:
            py_type = Tuple[tuple(item_types)]
        else:
            py_type = Tuple[Any, ...]
        
        # Apply optional/nullable
        if is_optional or is_nullable:
            py_type = Optional[py_type]
            
        return py_type, Field(**field_params) if field_params else None



def convert_object(schema: Dict[str, Validator], model_name: str = "GeneratedModel") -> Type[BaseModel]:
    """
    Convert a Sift schema to a Pydantic model class.
    
    Args:
        schema: Dictionary mapping field names to Sift validators
        model_name: Name for the generated Pydantic model class
    
    Returns:
        Type[BaseModel]: Generated Pydantic model class
    """ 
    converter = SchemaConverter()
    return converter.convert_object(schema, model_name)

def convert_schema(schema: Dict[str, Validator], model_name: str = "GeneratedModel") -> Type[BaseModel]:
    """
    Convert a Sift schema to a Pydantic model class.
    
    Args:
        schema: Dictionary mapping field names to Sift validators
        model_name: Name for the generated Pydantic model class
    
    Returns:
        Type[BaseModel]: Generated Pydantic model class
    """ 
    converter = SchemaConverter()
    return converter.convert_schema(schema, model_name)

