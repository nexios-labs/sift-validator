"""
OpenAPI schema generator for Sift validators.

This module provides functionality to convert Sift validation schemas into
OpenAPI compatible schema definitions.
"""

from typing import Any, Dict, List, Optional, Set, Type, Union, cast
import re
from types import SimpleNamespace

from sift.validators.base import Validator
from sift.validators.primitives import String, Number, Boolean, Null, Any as AnyValidator
from sift.validators.collections import List as ListValidator, Dict as DictValidator
from sift.validators.collections import Tuple as TupleValidator, Union as UnionValidator

class OpenAPISchemaGenerator:
    """
    Generator for converting Sift validators to OpenAPI schemas.
    
    Attributes:
        referenced_schemas: A dictionary of schemas that have been referenced
        schema_refs: A set of schema names that have been referenced
    """
    
    def __init__(self):
        self.referenced_schemas: Dict[str, Dict[str, Any]] = {}
        self.schema_refs: Set[str] = set()
        
    def generate_schema(self, validator: Validator, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an OpenAPI schema from a validator.
        
        Args:
            validator: The validator to convert
            schema_name: Optional name for this schema (used for references)
            
        Returns:
            OpenAPI schema object
        """
        schema = self._generate_schema_for_validator(validator)
        
        # If a schema name is provided, register it for reference
        if schema_name:
            self.referenced_schemas[schema_name] = schema
            self.schema_refs.add(schema_name)
            
        return schema
        
    def get_components_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the components/schemas section for the OpenAPI document.
        
        Returns:
            Dictionary of referenced schemas
        """
        return self.referenced_schemas
    
    def _generate_schema_for_validator(self, validator: Validator) -> Dict[str, Any]:
        """
        Generate an OpenAPI schema for a specific validator.
        
        Args:
            validator: The validator to convert
            
        Returns:
            OpenAPI schema object
        """
        schema = {}
        
        # Handle String validator
        if isinstance(validator, String):
            schema = self._generate_string_schema(validator)
            
        # Handle Number validator
        elif isinstance(validator, Number):
            schema = self._generate_number_schema(validator)
            
        # Handle Boolean validator
        elif isinstance(validator, Boolean):
            schema = self._generate_boolean_schema(validator)
            
        # Handle List validator
        elif isinstance(validator, ListValidator):
            schema = self._generate_array_schema(validator)
            
        # Handle Dict validator
        elif isinstance(validator, DictValidator):
            schema = self._generate_object_schema(validator)
            
        # Handle Tuple validator
        elif isinstance(validator, TupleValidator):
            schema = self._generate_tuple_schema(validator)
            
        # Handle Union validator
        elif isinstance(validator, UnionValidator):
            schema = self._generate_union_schema(validator)
            
        # Handle Null validator
        elif isinstance(validator, Null):
            schema = {"type": "null"}
            
        # Handle Any validator
        elif isinstance(validator, AnyValidator):
            schema = {}  # No restrictions
            
        # Check if this is an Object validator or a custom validator that inherits from Object
        elif hasattr(validator, "_schema") and callable(getattr(validator, "_validate", None)):
            # This is likely an Object validator or a custom validator class that inherits from Object
            # Try to get its schema
            try:
                # Import here to avoid circular import issues
                from sift.validators.objects import Object
                
                # Check if it's an Object validator instance
                if isinstance(validator, Object):
                    schema = self._generate_object_schema(validator)
                else:
                    # It's a custom validator with schema attribute
                    schema = self._generate_object_schema(validator)
            except (AttributeError, ImportError):
                # Fall back to empty schema
                schema = {}
        
        # Add nullable if specified
        if schema and getattr(validator, "_nullable", False):
            schema["nullable"] = True
        
        return schema
        
    def _generate_string_schema(self, validator: String) -> Dict[str, Any]:
        """Generate OpenAPI schema for String validator."""
        schema: Dict[str, Any] = {"type": "string"}
        
        # Add format based on validations
        if validator._email:
            schema["format"] = "email"
        elif validator._url:
            schema["format"] = "uri"
        elif validator._uuid:
            schema["format"] = "uuid"
        elif validator._datetime:
            schema["format"] = "date-time"
        elif validator._date:
            schema["format"] = "date"
            
        # Add length constraints
        if validator._min_length is not None:
            schema["minLength"] = validator._min_length
            
        if validator._max_length is not None:
            schema["maxLength"] = validator._max_length
            
        # Add pattern if specified
        if validator._pattern:
            schema["pattern"] = validator._pattern.pattern
            
        return schema
        
    def _generate_number_schema(self, validator: Number) -> Dict[str, Any]:
        """Generate OpenAPI schema for Number validator."""
        # Determine the type based on integer constraint
        schema: Dict[str, Any] = {"type": "integer" if validator._integer else "number"}
        
        # Add range constraints
        if validator._min_value is not None:
            schema["minimum"] = validator._min_value
            
        if validator._max_value is not None:
            schema["maximum"] = validator._max_value
            
        # Add multipleOf constraint
        if validator._multiple_of is not None:
            schema["multipleOf"] = validator._multiple_of
            
        # Handle exclusivity
        if validator._positive and validator._min_value is None:
            schema["exclusiveMinimum"] = 0
            
        if validator._negative and validator._max_value is None:
            schema["exclusiveMaximum"] = 0
            
        return schema
        
    def _generate_boolean_schema(self, validator: Boolean) -> Dict[str, Any]:
        """Generate OpenAPI schema for Boolean validator."""
        return {"type": "boolean"}
        
    def _generate_array_schema(self, validator: ListValidator) -> Dict[str, Any]:
        """Generate OpenAPI schema for List validator."""
        schema: Dict[str, Any] = {"type": "array"}
        
        # Add item schema if provided
        if validator._item_validator:
            schema["items"] = self._generate_schema_for_validator(validator._item_validator)
            
        # Add length constraints
        if validator._min_length is not None:
            schema["minItems"] = validator._min_length
            
        if validator._max_length is not None:
            schema["maxItems"] = validator._max_length
            
        # Add uniqueness constraint
        if validator._unique:
            schema["uniqueItems"] = True
            
        return schema
        
    def _generate_object_schema(self, validator) -> Dict[str, Any]:
        """Generate OpenAPI schema for Dict or Object validator."""
        schema: Dict[str, Any] = {"type": "object"}
        
        # Get the schema dict - different attribute name depending on the class
        schema_dict = None
        if hasattr(validator, "_schema"):
            schema_dict = validator._schema
        elif hasattr(validator, "__dict__") and hasattr(validator, "__class__"):
            # Try to find it in the object's dictionary by convention
            for attr_name in ["_schema", "schema"]:
                if attr_name in validator.__dict__:
                    schema_dict = validator.__dict__[attr_name]
                    break
        
        # Add properties from schema
        if schema_dict:
            properties = {}
            for key, val in schema_dict.items():
                # Skip private attributes
                if isinstance(key, str) and key.startswith("_"):
                    continue
                properties[key] = self._generate_schema_for_validator(val)
            schema["properties"] = properties
            
            # Add required properties
            required_keys = []
            if hasattr(validator, "_required_keys"):
                required_keys = list(validator._required_keys)
            else:
                # Determine required keys based on the schema
                for key, val in schema_dict.items():
                    if isinstance(key, str) and not key.startswith("_"):
                        if not (hasattr(val, "_optional") and val._optional) and not (hasattr(val, "_nullable") and val._nullable):
                            required_keys.append(key)
            
            if required_keys:
                schema["required"] = required_keys
        else:
            # Always include an empty properties object for object type
            schema["properties"] = {}
                
        # Add additionalProperties constraint
        if hasattr(validator, "_additional_properties"):
            if isinstance(validator._additional_properties, bool):
                schema["additionalProperties"] = validator._additional_properties
            elif validator._additional_properties is not True:  # Not the default True
                schema["additionalProperties"] = self._generate_schema_for_validator(validator._additional_properties)
            
        # Add patternProperties
        if hasattr(validator, "_pattern_properties") and validator._pattern_properties:
            pattern_properties = {}
            for pattern, val in validator._pattern_properties.items():
                pattern_properties[pattern] = self._generate_schema_for_validator(val)
            schema["patternProperties"] = pattern_properties
            
        # Add property count constraints
        if hasattr(validator, "_min_properties") and validator._min_properties is not None:
            schema["minProperties"] = validator._min_properties
            
        if hasattr(validator, "_max_properties") and validator._max_properties is not None:
            schema["maxProperties"] = validator._max_properties
            
        return schema
        
    def _generate_tuple_schema(self, validator: TupleValidator) -> Dict[str, Any]:
        """Generate OpenAPI schema for Tuple validator."""
        # For OpenAPI, tuples are arrays with specific prefixItems
        schema: Dict[str, Any] = {"type": "array"}
        
        # Add prefixItems for position-based validation (OpenAPI 3.1+)
        # For OpenAPI 3.0, we'll use items with an array of schemas
        prefix_items = []
        for val in validator._item_validators:
            prefix_items.append(self._generate_schema_for_validator(val))
            
        # OpenAPI 3.1 uses prefixItems, but for 3.0 compatibility we use items
        # Check if items is an array type
        schema["items"] = prefix_items
        
        # Add additional items constraint for rest validator
        if validator._rest_validator:
            # OpenAPI 3.1 uses items for the rest elements
            # OpenAPI 3.0 uses additionalItems
            schema["additionalItems"] = self._generate_schema_for_validator(validator._rest_validator)
        else:
            # If no rest validator, additional items are not allowed
            schema["additionalItems"] = False
            
        # Add length constraints
        if validator._min_length is not None:
            schema["minItems"] = validator._min_length
            
        if validator._max_length is not None:
            schema["maxItems"] = validator._max_length
            
        return schema
        
    def _generate_union_schema(self, validator: UnionValidator) -> Dict[str, Any]:
        """Generate OpenAPI schema for Union validator."""
        # For OpenAPI, unions are represented as oneOf
        schema: Dict[str, Any] = {
            "oneOf": [
                self._generate_schema_for_validator(val) 
                for val in validator._validators
            ]
        }
        
        # Add discriminator if provided
        if hasattr(validator, "_discriminator") and validator._discriminator:
            schema["discriminator"] = {
                "propertyName": validator._discriminator
            }
            
            # Add mapping if available
            if hasattr(validator, "_discriminator_map") and validator._discriminator_map:
                schema["discriminator"]["mapping"] = {}
                
                for k, v in validator._discriminator_map.items():
                    # Generate a schema name based on discriminator value
                    schema_name = f"{k}Schema"
                    
                    # Add to referenced schemas
                    component_schema = self._generate_schema_for_validator(v)
                    self.referenced_schemas[schema_name] = component_schema
                    
                    # Add to mapping
                    schema["discriminator"]["mapping"][str(k)] = f"#/components/schemas/{schema_name}"
        
        return schema

def generate_openapi_schema(validator: Validator, schema_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an OpenAPI schema from a validator.
    
    Args:
        validator: The validator to convert
        schema_name: Optional name for this schema
        
    Returns:
        OpenAPI schema object
    """
    generator = OpenAPISchemaGenerator()
    return generator.generate_schema(validator, schema_name)

def generate_openapi_components(validator: Validator, schema_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Generate OpenAPI components/schemas section from a validator.
    
    Args:
        validator: The validator to convert
        schema_name: Name for the main schema
        
    Returns:
        Components schemas object
    """
    generator = OpenAPISchemaGenerator()
    generator.generate_schema(validator, schema_name)
    return generator.get_components_schemas()


