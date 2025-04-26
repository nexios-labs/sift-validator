# Sift

A modern Python validation library with Zod-like syntax, async support, and OpenAPI integration.

## Features

- 🔄 **Chainable API**: Intuitive, fluent interface for building validation schemas
- ⚡ **Async Support**: Fast, non-blocking validation for high-performance applications
- 📝 **Type Hints**: Comprehensive typing for excellent editor integration
- 📊 **OpenAPI**: Seamless generation of OpenAPI schemas from your validators
- 🔍 **Powerful Validation**: Built-in validators for common use cases with custom validation support
- 🔧 **Data Transformation**: Transform and normalize data during validation

## Installation

```bash
pip install sift
```

## Quick Start

```python
from sift import String, Number, Object, List

# Define a schema
user_schema = Object({
    "username": String().min(3).max(20).trim(),
    "email": String().email(),
    "age": Number().int().min(18).optional(),
    "tags": List(String()).min(1).max(5),
})

# Validate data
try:
    valid_user = user_schema.validate({
        "username": "  johndoe  ",  # Will be trimmed
        "email": "john@example.com",
        "tags": ["python", "validation"]
    })
    print(valid_user)
except ValueError as e:
    print(f"Validation error: {e}")

# Async validation
import asyncio

async def validate_user_async():
    try:
        valid_user = await user_schema.validate_async({
            "username": "johndoe",
            "email": "john@example.com",
            "tags": ["python", "validation"]
        })
        print(valid_user)
    except ValueError as e:
        print(f"Validation error: {e}")

asyncio.run(validate_user_async())
```

## OpenAPI Integration

```python
from sift import String, Number, Object
from sift.openapi import generate_openapi_schema

user_schema = Object({
    "username": String().min(3).max(20),
    "email": String().email(),
    "age": Number().int().min(18),
})

# Generate OpenAPI schema
openapi_schema = generate_openapi_schema(user_schema)
print(openapi_schema)
```

## License

MIT

