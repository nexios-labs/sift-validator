"""
OpenAPI schema generation module.

This module provides functionality to convert Voltar  validators to
OpenAPI schema definitions for API documentation and client generation.
"""

from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast
import re
from enum import Enum

from voltar .validators.base import Validator
from voltar .validators.primitives import String, Number, Boolean, Null, Any as AnyValidator
from voltar .validators.collections import List as ListValidator, Dict as DictValidator
from voltar .validators.collections import Tuple as TupleValidator, Union as UnionValidator


class OpenAPIVersion(Enum):
    """OpenAPI schema version."""
    V3_0 = "3.0"
    V3_1 = "3.1"


class SchemaContext:
    """
    Context for schema generation to handle references and components.
    
    Attributes:
        openapi_version: The OpenAPI version to target
        referenced_schemas: Dictionary of referenced schemas by name
        schema_refs: Set of referenced schema names
    """
    
    def __init__(self, openapi_version: OpenAPIVersion = OpenAPIVersion.V3_0):
        self.openapi_version: OpenAPIVersion = openapi_version
        self.referenced_schemas: Dict[str, Dict[str, Any]] = {}
        self.schema_refs: Set[str] = set()
        

def generate_schema(
    validator: Validator, 
    schema_name: Optional[str] = None,
    context: Optional[SchemaContext] = None
) -> Dict[str, Any]:
    """
    Generate an OpenAPI schema from a validator.
    
    Args:
        validator: The validator to convert
        schema_name: Optional name for this schema (used for references)
        context: Optional schema context for handling references and components
        
    Returns:
        OpenAPI schema object
    """
    if context is None:
        context = SchemaContext()
        
    schema = _generate_schema_for_validator(validator, context)
    
    # If a schema name is provided, register it for reference
    if schema_name:
        context.referenced_schemas[schema_name] = schema
        context.schema_refs.add(schema_name)
        
    return schema


def get_schema_components(context: SchemaContext) -> Dict[str, Dict[str, Any]]:
    """
    Get the components/schemas section for the OpenAPI document.
    
    Args:
        context: The schema context with referenced schemas
        
    Returns:
        Dictionary of referenced schemas
    """
    return context.referenced_schemas


def _generate_schema_for_validator(validator: Validator, context: SchemaContext) -> Dict[str, Any]:
    """
    Generate an OpenAPI schema for a specific validator.
    
    Args:
        validator: The validator to convert
        context: The schema context
        
    Returns:
        OpenAPI schema object
    """
    # Initialize with empty schema
    schema = {}
    
    # Handle String validator
    if isinstance(validator, String):
        schema = _generate_string_schema(validator, context)
        
    # Handle Number validator
    elif isinstance(validator, Number):
        schema = _generate_number_schema(validator, context)
        
    # Handle Boolean validator
    elif isinstance(validator, Boolean):
        schema = _generate_boolean_schema(validator, context)
        
    # Handle List validator
    elif isinstance(validator, ListValidator):
        schema = _generate_array_schema(validator, context)
        
    # Handle Dict validator
    elif isinstance(validator, DictValidator):
        schema = _generate_object_schema(validator, context)
        
    # Handle Tuple validator
    elif isinstance(validator, TupleValidator):
        schema = _generate_tuple_schema(validator, context)
        
    # Handle Union validator
    elif isinstance(validator, UnionValidator):
        schema = _generate_union_schema(validator, context)
        
    # Handle Null validator
    elif isinstance(validator, Null):
        schema = {"type": "null"}
        
    # Handle Any validator
    elif isinstance(validator, AnyValidator):
        schema = {}  # No restrictions
        
    # Handle Object-like validators
    elif hasattr(validator, "__dict__"):
        # Check if this is a custom validator class that inherits from Object
        # or implements a similar interface
        try:
            # Try to access schema directly
            if hasattr(validator, "_schema"):
                schema = _generate_object_schema(validator, context)
            # Try to access schema as an Object validator
            elif hasattr(validator, "properties") or hasattr(validator, "validate"):
                # Simulate Dict/Object validator
                schema = {
                    "type": "object",
                    "properties": {}
                }
                # Add properties if available
                if hasattr(validator, "properties"):
                    props = {}
                    for key, val in validator.properties.items():
                        props[key] = _generate_schema_for_validator(val, context)
                    schema["properties"] = props
        except Exception:
            # Fall back to empty schema with type object
            schema = {"type": "object", "properties": {}}
            
    # Add default values if specified and not callable
    if hasattr(validator, "_default") and validator._default is not None:
        if not callable(validator._default):
            schema["default"] = validator._default
        else:
            # For callable defaults, we can't represent them in OpenAPI
            # but we can indicate that there is a default
            pass
    
    # If we still have an empty schema for an Object-like validator, 
    # provide a minimal valid schema
    if not schema and hasattr(validator, "__class__") and validator.__class__.__name__ == "Object":
        schema = {"type": "object", "properties": {}}
    
    return schema


def _generate_string_schema(validator: String, context: SchemaContext) -> Dict[str, Any]:
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
        
    # Add nullable support
    if validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            if "type" in schema:
                schema["type"] = [schema["type"], "null"]
        else:
            schema["nullable"] = True
            
    return schema


def _generate_number_schema(validator: Number, context: SchemaContext) -> Dict[str, Any]:
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
        
    # Add nullable support
    if validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            if "type" in schema:
                schema["type"] = [schema["type"], "null"]
        else:
            schema["nullable"] = True
            
    return schema


def _generate_boolean_schema(validator: Boolean, context: SchemaContext) -> Dict[str, Any]:
    """Generate OpenAPI schema for Boolean validator."""
    schema = {"type": "boolean"}
    
    # Add nullable support
    if validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            schema["type"] = ["boolean", "null"]
        else:
            schema["nullable"] = True
            
    return schema


def _generate_array_schema(validator: ListValidator, context: SchemaContext) -> Dict[str, Any]:
    """Generate OpenAPI schema for List validator."""
    schema: Dict[str, Any] = {"type": "array"}
    
    # Add item schema if provided
    if validator._item_validator:
        schema["items"] = _generate_schema_for_validator(validator._item_validator, context)
    else:
        # OpenAPI requires items to be defined for arrays
        schema["items"] = {}
            
    # Add length constraints
    if validator._min_length is not None:
        schema["minItems"] = validator._min_length
            
    if validator._max_length is not None:
        schema["maxItems"] = validator._max_length
            
    # Add uniqueness constraint
    if validator._unique:
        schema["uniqueItems"] = True
            
    # Add nullable support
    if validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            schema["type"] = ["array", "null"]
        else:
            schema["nullable"] = True
            
    return schema


def _generate_object_schema(validator: Any, context: SchemaContext) -> Dict[str, Any]:
    """Generate OpenAPI schema for Dict or Object validator."""
    schema: Dict[str, Any] = {"type": "object"}
    
    # Initialize properties to ensure they're always present
    schema["properties"] = {}
    
    # Get the schema dict - different attribute name depending on the class
    schema_dict = None
    
    # Handle Dict validators directly
    if isinstance(validator, DictValidator) and hasattr(validator, "_schema"):
        schema_dict = validator._schema
    # Handle Object validators by accessing their __dict__
    elif hasattr(validator, "__dict__"):
        # First try direct access
        if hasattr(validator, "_schema"):
            try:
                schema_dict = validator._schema
            except AttributeError:
                # Some validators might have _schema as a property
                pass
                
        # Then try to find it in the dict
        if not schema_dict:
            for attr_name in ["_schema", "schema", "properties"]:
                try:
                    if hasattr(validator, attr_name):
                        attr_value = getattr(validator, attr_name)
                        if isinstance(attr_value, dict):
                            schema_dict = attr_value
                            break
                except Exception:
                    pass
    
    # Add properties from schema
    if schema_dict:
        properties = {}
        for key, val in schema_dict.items():
            # Skip private attributes
            if isinstance(key, str) and key.startswith("_"):
                continue
            properties[key] = _generate_schema_for_validator(val, context)
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
            schema["additionalProperties"] = _generate_schema_for_validator(
                validator._additional_properties, context
            )
        
    # Add patternProperties
    if hasattr(validator, "_pattern_properties") and validator._pattern_properties:
        pattern_properties = {}
        for pattern, val in validator._pattern_properties.items():
            pattern_properties[pattern] = _generate_schema_for_validator(val, context)
        schema["patternProperties"] = pattern_properties
        
    # Add property count constraints
    if hasattr(validator, "_min_properties") and validator._min_properties is not None:
        schema["minProperties"] = validator._min_properties
        
    if hasattr(validator, "_max_properties") and validator._max_properties is not None:
        schema["maxProperties"] = validator._max_properties
    
    # Add nullable support
    if hasattr(validator, "_nullable") and validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            schema["type"] = ["object", "null"]
        else:
            schema["nullable"] = True
            
    return schema
def _generate_tuple_schema(validator: TupleValidator, context: SchemaContext) -> Dict[str, Any]:
    """Generate OpenAPI schema for Tuple validator."""
    schema: Dict[str, Any] = {"type": "array"}
    
    # Generate schema for each item validator
    item_schemas = [
        _generate_schema_for_validator(val, context) 
        for val in validator._item_validators
    ]
    
    # OpenAPI 3.1 uses prefixItems for tuple-like arrays
    if context.openapi_version == OpenAPIVersion.V3_1:
        schema["prefixItems"] = item_schemas
        
        # If rest validator is provided, use items for additional items
        if validator._rest_validator:
            schema["items"] = _generate_schema_for_validator(validator._rest_validator, context)
        else:
            # If no rest validator and in 3.1, we can use contains: false
            schema["minItems"] = validator._min_length
            schema["maxItems"] = validator._max_length if validator._max_length is not None else len(item_schemas)
    else:
        # OpenAPI 3.0 uses items with an array for tuple-like validation
        schema["items"] = item_schemas
        
        # Handle additional items
        if validator._rest_validator:
            schema["additionalItems"] = _generate_schema_for_validator(validator._rest_validator, context)
        else:
            schema["additionalItems"] = False
        
    # Add length constraints
    if validator._min_length is not None:
        schema["minItems"] = validator._min_length
            
    if validator._max_length is not None:
        schema["maxItems"] = validator._max_length
    
    # Add nullable support
    if validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            schema["type"] = ["array", "null"]
        else:
            schema["nullable"] = True
            
    return schema


def _generate_union_schema(validator: UnionValidator, context: SchemaContext) -> Dict[str, Any]:
    """Generate OpenAPI schema for Union validator."""
    # Generate schemas for each validator
    variant_schemas = [
        _generate_schema_for_validator(val, context) 
        for val in validator._validators
    ]
    
    # For OpenAPI, unions are represented as oneOf
    schema: Dict[str, Any] = {
        "oneOf": variant_schemas
    }
    
    # Add discriminator if provided
    if hasattr(validator, "_discriminator") and validator._discriminator:
        schema["discriminator"] = {
            "propertyName": validator._discriminator
        }
        
        # Add mapping if provided
        if hasattr(validator, "_discriminator_map") and validator._discriminator_map:
            mapping = {}
            for key, val in validator._discriminator_map.items():
                # Generate a schema name based on the discriminator value
                # Ensure proper capitalization for schema names (UserSchema, AdminSchema)
                schema_name = f"{key.capitalize() if isinstance(key, str) else key}Schema"
                
                # Add to components
                component_schema = _generate_schema_for_validator(val, context)
                context.referenced_schemas[schema_name] = component_schema
                context.schema_refs.add(schema_name)
                
                # Add to mapping
                mapping[str(key)] = f"#/components/schemas/{schema_name}"
            
            schema["discriminator"]["mapping"] = mapping
    
    # Add nullable support
    if validator._nullable:
        if context.openapi_version == OpenAPIVersion.V3_1:
            # In 3.1, we can add null to the oneOf array
            schema["oneOf"].append({"type": "null"})
        else:
            # In 3.0, we need nullable: true at the schema level
            schema["nullable"] = True
            
    return schema


def generate_full_openapi_schema(
    validator: Validator,
    title: str = "API Schema",
    version: str = "1.0.0",
    openapi_version: OpenAPIVersion = OpenAPIVersion.V3_0,
    description: str = "",
) -> Dict[str, Any]:
    """
    Generate a complete OpenAPI schema document.
    
    Args:
        validator: The root validator
        title: API title
        version: API version
        openapi_version: OpenAPI specification version
        description: API description
        
    Returns:
        Complete OpenAPI schema document
    """
    context = SchemaContext(openapi_version=openapi_version)
    # Generate the root schema
    root_schema = generate_schema(validator, "RootSchema", context)
    
    # Ensure the RootSchema is properly set in components
    if "RootSchema" not in context.referenced_schemas or not context.referenced_schemas["RootSchema"]:
        context.referenced_schemas["RootSchema"] = root_schema
    
    # Create the OpenAPI document
    openapi_doc = {
        "openapi": "3.0.3" if openapi_version == OpenAPIVersion.V3_0 else "3.1.0",
        "info": {
            "title": title,
            "version": version,
            "description": description
        },
        "paths": {},
        "components": {
            "schemas": get_schema_components(context)
        }
    }
    
    return openapi_doc
