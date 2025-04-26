"""
OpenAPI schema generation module.

This module provides functionality to convert Sift validators to
OpenAPI schema definitions for API documentation and client generation.
"""

from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast
import re
from enum import Enum

from sift.validators.base import Validator
from sift.validators.primitives import String, Number, Boolean, Null, Any as AnyValidator
from sift.validators.collections import List as ListValidator, Dict as DictValidator
from sift.validators.collections import Tuple as TupleValidator, Union as UnionValidator


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
    # Handle String validator
    if isinstance(validator, String):
        return _generate_string_schema(validator, context)
        
    # Handle Number validator
    elif isinstance(validator, Number):
        return _generate_number_schema(validator, context)
        
    # Handle Boolean validator
    elif isinstance(validator, Boolean):
        return _generate_boolean_schema(validator, context)
        
    # Handle List validator
    elif isinstance(validator, ListValidator):
        return _generate_array_schema(validator, context)
        
    # Handle Dict validator
    elif isinstance(validator, DictValidator):
        return _generate_object_schema(validator, context)
        
    # Handle Tuple validator
    elif isinstance(validator, TupleValidator):
        return _generate_tuple_schema(validator, context)
        
    # Handle Union validator
    elif isinstance(validator, UnionValidator):
        return _generate_union_schema(validator, context)
        
    # Handle Null validator
    elif isinstance(validator, Null):
        return {"type": "null"}
        
    # Handle Any validator
    elif isinstance(validator, AnyValidator):
        return {}  # No restrictions
        
    # Default case
    return {}


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


def _generate_object_schema(validator: DictValidator, context: SchemaContext) -> Dict[str, Any]:
    """Generate OpenAPI schema for Dict validator."""
    schema: Dict[str, Any] = {"type": "object"}
    
    # Add properties from schema
    if validator._schema:
        properties = {}
        for key, val in validator._schema.items():
            properties[key] = _generate_schema_for_validator(val, context)
        schema["properties"] = properties
            
        # Add required properties
        if validator._required_keys:
            schema["required"] = list(validator._required_keys)
                
    # Add additionalProperties constraint
    if isinstance(validator._additional_properties, bool):
        schema["additionalProperties"] = validator._additional_properties
    elif validator._additional_properties is not True:  # Not the default True
        schema["additionalProperties"] = _generate_schema_for_validator(
            validator._additional_properties, context
        )
            
    # Add patternProperties
    if validator._pattern_properties:
        pattern_properties = {}
        for pattern, val in validator._pattern_properties.items():
            pattern_properties[pattern] = _generate_schema_for_validator(val, context)
        schema["patternProperties"] = pattern_properties
            
    # Add property count constraints
    if validator._min_properties is not None:
        schema["minProperties"] = validator._min_properties
            
    if validator._max_properties is not None:
        schema["maxProperties"] = validator._max_properties
            
    # Add nullable support
    if validator._nullable:
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
    
    # For OpenAPI, unions are represented as oneOf/anyOf
    # We generally use anyOf for more permissive validation
    schema: Dict[str, Any] = {
        "anyOf": variant_schemas
    }
    
    # Add discriminator if provided
    if validator._discriminator and validator._discriminator_map:
        schema["discriminator"] = {
            "propertyName": validator._discriminator,
        }
        
        # Add mapping if provided
        if validator._discriminator_map:
            mapping = {}
            for key, val in validator._discriminator_map.items():
                # Generate a schema name based on the discriminator value
                schema_name = f"{key}Schema"
                
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
            # In 3.1, we can add null to the oneOf/anyOf array
            schema["anyOf"].append({"type": "null"})
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
    schema = generate_schema(validator, "RootSchema", context)
    
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
