Here's the documentation for the Pydantic converter in Markdown format:

```markdown
# Voltar  to Pydantic Converter

Utility for converting Voltar  validator schemas to Pydantic models.

## Overview

The converter bridges the gap between Voltar  validators and Pydantic models, allowing you to:

1. Define data schemas using Voltar  validators
2. Convert those schemas to Pydantic models
3. Use the models with Pydantic-compatible libraries

## Basic Usage

```python
from voltar .validators.primitives import String, Number, Boolean
from voltar .validators.objects import Object
from voltar .pydantic_converter import convert_schema

# Define a Voltar  schema
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

## Main Functions

### `convert_schema(schema: Dict[str, Validator], model_name: str = "GeneratedModel") -> Type[BaseModel]`

Converts a Voltar  schema dictionary to a Pydantic model class.

**Parameters:**
- `schema`: Dictionary mapping field names to Voltar  validators
- `model_name`: Name for the generated Pydantic model class

**Returns:**
A Pydantic model class that can be instantiated with data matching the schema

**Example:**
```python
from voltar .validators.primitives import String, Number, Boolean

schema = {
    "name": String().min(2),
    "age": Number().int().min(0).optional(),
    "is_active": Boolean().default(True)
}

PersonModel = convert_schema(schema, "PersonModel")
person = PersonModel(name="Alice", age=30)
```

### `convert_object(obj_validator: Object, model_name: str = "GeneratedModel") -> Type[BaseModel]`

Converts a Voltar  Object validator to a Pydantic model class.

**Parameters:**
- `obj_validator`: Voltar  Object validator instance containing a schema
- `model_name`: Name for the generated Pydantic model class

**Returns:**
A Pydantic model class derived from the Object validator

**Example:**
```python
from voltar .validators.primitives import String, Number
from voltar .validators.objects import Object

user_validator = Object({
    "username": String().min(3),
    "age": Number().int().min(0)
})

UserModel = convert_object(user_validator, "UserModel")
user = UserModel(username="john", age=25)
```

## Type Conversion Reference

| Voltar  Validator | Pydantic/Python Type |
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

## Features

- Supports all basic validator types (String, Number, Boolean)
- Handles complex validators (List, Dict, Tuple, Union)
- Converts nested object structures to nested Pydantic models
- Preserves optional and nullable fields
- Maintains default values (including callable defaults)
- Maps validation constraints (min/max length, regex patterns, etc.)

## Advanced Example

```python
from voltar .validators.primitives import String, Number, Boolean
from voltar .validators.collections import List
from voltar .validators.objects import Object

# Nested address schema
address_schema = {
    "street": String().max(100),
    "city": String(),
    "zip_code": String().pattern(r'^\d{5}$').error("Zip code must be 5 digits"),
    "country": String().default("USA")
}

# Main user schema with nested objects and lists
user_schema = {
    "username": String().min(3).max(20),
    "email": String().email().error("Invalid email format"),
    "age": Number().int().min(18).error("Must be at least 18 years old"),
    "is_active": Boolean().default(True),
    "tags": List(String()).optional(),
    "address": Object(address_schema),
    "previous_addresses": List(Object(address_schema)).optional()
}

# Convert to Pydantic model
UserModel = convert_schema(user_schema, "UserModel")
```

## Notes

- Optional validators are converted to `Optional[Type]` in Python's typing system
- Nullable validators also use `Optional[Type]` but semantically allow None values
- Default values are preserved in the Pydantic model
- Validator constraints are mapped to Pydantic's validation system
- The converter handles nested structures recursively
