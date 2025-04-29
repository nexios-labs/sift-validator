"""
Utility for converting Voltar  schemas to Pydantic models.

This module provides functionality to convert Voltar  validator schemas 
into equivalent Pydantic model classes with appropriate type hints
and validation constraints.

## Overview

The VOLTAR  validator system provides a flexible way to validate data using
a chainable API. Pydantic is a popular data validation library in the Python
ecosystem. This module bridges the gap between VOLTAR  validators and Pydantic
models, allowing you to:

1. Define your data schemas using VOLTAR  validators
2. Convert those schemas to Pydantic models for use with other Pydantic-compatible libraries
3. Leverage both systems depending on your needs

## Basic Usage

```python
from voltar .validators.primitives import String, Number, Boolean
from voltar .validators.objects import Object
from voltar .pydantic_converter import convert_schema

# Define a VOLTAR  schema
user_schema = {
    "username": String().min(3).max(20),
    "age": Number().int().min(0),
    "is_active": Boolean().default(True)
}

# Convert to a Pydantic model
UserModel = convert_schema(user_schema, "UserModel")

# Use the Pydantic model
user = UserModel(username="john_doe", age=25)
print(user.dict())  # {"username": "john_doe", "age": 25, "is_active": True}
```

## Conversion Features

The converter supports:

- Basic validator types (String, Number, Boolean)
- Complex validators (List, Dict, Tuple, Union)
- Nested objects with complex structure
- Optional and nullable fields
- Default values (including callable defaults)
- Validation constraints (min/max length, regex patterns, etc.)

### Validator Type Mapping

| VOLTAR  Validator | Pydantic/Python Type |
|----------------|----------------------|
| String         | str                  |
| String().email() | EmailStr           |
| Number         | float                |
| Number().int() | int                  |
| Boolean        | bool                 |
| List(String()) | List[str]            |
| Object         | BaseModel subclass   |
| Dict           | Dict[str, Any] or BaseModel |
| Union          | Union[...]           |
| Null           | Optional[Any]        |
| Any            | Any                  |

For more complex examples and specific usage patterns, see the examples below.
"""

from typing import Any, Dict, List as ListType, Optional, Set, Tuple, Type, Union as UnionType, get_type_hints
import inspect
import re

# Import Pydantic
from pydantic import BaseModel, Field, EmailStr,create_model

# Import Voltar  validators
from voltar.validators.base import Validator, ValidationError
from voltar.validators.primitives import Null, String, Number, Boolean, Any as  Any, Null
from voltar.validators.collections import List, Dict as VoltarDict, Union, Tuple as VoltarTuple, Union
from voltar.validators.objects import Object

class SchemaConverter:
    """
    Converts Voltar  validator schemas to Pydantic models.
    
    This class analyzes Voltar  validators and their chain modifiers to create
    equivalent Pydantic model classes with proper type hints and validation.
    
    The converter handles:
    - Basic types (String, Number, Boolean)
    - Collection types (List, Dict, Tuple)
    - Union types for polymorphic data
    - Nested object structures
    - Optional and nullable fields
    - Default values including callable defaults
    - Validation constraints (min/max length, numeric ranges, patterns, etc.)
    
    The conversion process preserves as much type information and validation logic
    as possible while mapping to Pydantic's validation system.
    
    Example:
        ```python
        from voltar .validators.primitives import String, Number
        from voltar .validators.objects import Object
        
        # Create a converter instance
        converter = SchemaConverter()
        
        # Define a schema and convert it
        schema = {
            "name": String(),
            "age": Number().int()
        }
        
        # Convert to a Pydantic model
        UserModel = converter.convert_schema(schema, "UserModel")
        
        # Use the model
        user = UserModel(name="John", age=30)
        ```
    """
    
    def __init__(self):
        self.model_registry = {}  # Cache for created models to avoid duplicates
        
    def convert_schema(self, schema: Dict[str, Validator], model_name: str = "GeneratedModel") -> Type[BaseModel]:
        """
        Converts a Voltar  schema dictionary to a Pydantic model class.
        
        Args:
            schema: Dictionary mapping field names to Voltar  validators
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
        Converts a Voltar  Object validator to a Pydantic model class.
        
        Args:
            obj_validator: Voltar  Object validator instance
            class_name: Name for the generated Pydantic model class
            
        Returns:
            A Pydantic model class with fields derived from the Object schema
        """
        # Get the schema from the Object validator
        schema = obj_validator._schema
        return self.convert_schema(schema, class_name)
    
    def _convert_validator(self, validator: Validator, field_name: str = None) -> Tuple[Type, Any]:
        """
        Converts a Voltar  validator to a Pydantic field type and constraints.
        
        Args:
            validator: Voltar  validator instance
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
        elif isinstance(validator,  Dict):
            return self._convert_dict_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Object):
            return self._convert_object_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Union):
            return self._convert_union_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Any):
            return self._convert_any_validator(validator, field_params, is_optional, is_nullable)
        elif isinstance(validator, Null):
            return self._convert_null_validator(validator, field_params)
        elif isinstance(validator, Tuple):
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
            field_params["pattern"] = pattern
        
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
    
    def _convert_any_validator(self, validator:  Any, field_params: Dict[str, Any],
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
    
    def _convert_tuple_validator(self, validator:  Tuple, field_params: Dict[str, Any],
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



# Example demonstrating complete conversion from VOLTAR  to Pydantic
"""
The following example demonstrates a more complex conversion from VOLTAR  validators
to Pydantic models, including nested objects, lists, and various constraints.

```python
from voltar .validators.primitives import String, Number, Boolean
from voltar .validators.collections import List, Dict
from voltar .validators.objects import Object
from voltar .pydantic_converter import convert_schema

# Define a nested address schema
address_schema = {
    "street": String().max(100),
    "city": String(),
    "zip_code": String().pattern(r'^\d{5}$').error("Zip code must be 5 digits"),
    "country": String().default("USA")
}

# Define the main user schema with nested objects and lists
user_schema = {
    "username": String().min(3).max(20),
    "email": String().email().error("Invalid email format"),
    "age": Number().int().min(18).error("Must be at least 18 years old"),
    "is_active": Boolean().default(True),
    "tags": List(String()).optional(),
    "address": Object(address_schema),
    "previous_addresses": List(Object(address_schema)).optional()
}

# Convert to a Pydantic model
UserModel = convert_schema(user_schema, "UserModel")

# Create a user instance with the model
user = UserModel(
    username="john_doe",
    email="john@example.com",
    age=25,
    address={
        "street": "123 Main St",
        "city": "Anytown",
        "zip_code": "12345"
    },
    previous_addresses=[
        {
            "street": "456 Old Road",
            "city": "Oldtown",
            "zip_code": "67890"
        }
    ]
)

# Access the data in a structured way
print(user.username)  # "john_doe"
print(user.address.street)  # "123 Main St"
print(user.dict())  # Full user object as dict
```

The converter handles:
- Validation constraints (String length, Number range, etc.)
- Default values (country="USA", is_active=True)
- Optional fields (tags, previous_addresses)
- Nested object structures
- List of primitive types or complex objects
"""

def convert_object(obj_validator: Object, model_name: str = "GeneratedModel") -> Type[BaseModel]:
    """
    Convert a Voltar  Object validator to a Pydantic model class.
    
    This function takes a VOLTAR  Object validator instance and creates an equivalent
    Pydantic model class with all fields and validations properly mapped.
    
    Args:
        obj_validator: VOLTAR  Object validator instance containing a schema
        model_name: Name for the generated Pydantic model class
    
    Returns:
        Type[BaseModel]: A generated Pydantic model class that can be instantiated
            with data matching the schema defined in the Object validator
    
    Example:
        ```python
        from voltar .validators.primitives import String, Number
        from voltar .validators.objects import Object
        from voltar .pydantic_converter import convert_object
        
        # Create an Object validator
        user_validator = Object({
            "username": String().min(3),
            "age": Number().int().min(0)
        })
        
        # Convert to Pydantic model
        UserModel = convert_object(user_validator, "UserModel")
        
        # Use the model
        user = UserModel(username="john", age=25)
        ```
    """ 
    converter = SchemaConverter()
    return converter.convert_object(obj_validator, model_name)

def convert_schema(schema: Dict[str, Validator], model_name: str = "GeneratedModel") -> Type[BaseModel]:
    """
    Convert a Voltar  schema dictionary to a Pydantic model class.
    
    This function is the main entry point for converting VOLTAR  validator schemas
    directly to Pydantic models. It handles all validator types, nested structures,
    and validation constraints.
    
    Args:
        schema: Dictionary mapping field names to Voltar  validators
        model_name: Name for the generated Pydantic model class
    
    Returns:
        Type[BaseModel]: A generated Pydantic model class that can be instantiated
            with data matching the schema defined in the dictionary
    
    Example:
        ```python
        from voltar .validators.primitives import String, Number, Boolean
        from voltar .pydantic_converter import convert_schema
        
        # Define a schema dictionary
        schema = {
            "name": String().min(2),
            "age": Number().int().min(0).optional(),
            "is_active": Boolean().default(True)
        }
        
        # Convert to Pydantic model
        PersonModel = convert_schema(schema, "PersonModel")
        
        # Create instances
        person1 = PersonModel(name="Alice", age=30)
        person2 = PersonModel(name="Bob")  # age is optional
        
        # ValidationError would be raised for:
        # PersonModel(age=25)  # missing required name
        # PersonModel(name="C")  # name too short
        ```
    
    Notes:
        - Optional validators are converted to Optional[Type] in Python's typing system
        - Nullable validators also use Optional[Type] but semantically allow None values
        - Default values are preserved in the Pydantic model
        - Validator constraints are mapped to Pydantic's validation system
    """ 
    converter = SchemaConverter()
    return converter.convert_schema(schema, model_name)

