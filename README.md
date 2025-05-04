<p align="center">
<img src="./logo.svg" alt="Voltar Logo" width="200" height="200" />
</p>

<p align="center"  >

# Voltar 

</p>

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
pip install voltar 
```

## Quick Start

```python
import voltar as v

# Define a schema
user_schema = v.Object({
    "username": v.String().min(3).max(20).trim(),
    "email": v.String().email(),
    "age": v.Number().int().min(18).optional(),
    "tags": v.List(v.String()).min(1).max(5),
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
import voltar as v
from voltar.openapi import generate_openapi_schema

user_schema = v.Object({
    "username": v.String().min(3).max(20),
    "email": v.String().email(),
    "age": v.Number().int().min(18),
})

# Generate OpenAPI schema
openapi_schema = generate_openapi_schema(user_schema)
print(openapi_schema)
```

# Schema Modification

Voltar provides powerful schema modification capabilities through three main methods: `extend`, `exclude`, and `omit`. These methods allow you to adapt and reuse schemas flexibly while maintaining type safety and validation rules.

## Extending Schemas (`extend`)

Use `extend` to add new fields to an existing schema without modifying the original:

```python
import voltar as v

# Base user schema
user_schema = v.Object({
    "name": v.String(),
    "age": v.Number()
})

# Create employee schema by extending user schema
employee_schema = user_schema.extend({
    "department": v.String(),
    "salary": v.Number()
})

# Base schema remains unchanged
user_data = user_schema.validate({
    "name": "John",
    "age": 30
})

# Extended schema includes all fields
employee_data = employee_schema.validate({
    "name": "John",
    "age": 30,
    "department": "Engineering",
    "salary": 75000
})
```

## Excluding Fields (`exclude`)

Use `exclude` to temporarily ignore specific fields during validation. The fields remain in the schema but aren't validated:

```python
import voltar as v

# Schema with sensitive data
user_schema = v.Object({
    "name": v.String(),
    "age": v.Number(),
    "email": v.Email(),
    "ssn": v.String()
})

# Create public view that doesn't validate sensitive fields
public_schema = user_schema.exclude("email", "ssn")

# These fields are allowed but not validated
public_schema.validate({
    "name": "John",
    "age": 30,
    "email": "not-validated",  # Would normally fail Email validation
    "ssn": "any-value"        # No validation performed
})
```

## Omitting Fields (`omit`)

Use `omit` to create a new schema without specific fields. Unlike `exclude`, omitted fields are not allowed in the data:

```python
import voltar as v

# Full user schema
user_schema = v.Object({
    "name": v.String(),
    "age": v.Number(),
    "email": v.Email(),
    "password": v.String()
})

# Create public profile schema without sensitive data
profile_schema = user_schema.omit(["password", "email"])

# Valid: only includes allowed fields
profile_schema.validate({
    "name": "John",
    "age": 30
})

# Invalid: raises ValidationError for omitted fields
profile_schema.validate({
    "name": "John",
    "age": 30,
    "password": "secret"  # Error: unexpected field
})
```

## Key Differences: `exclude` vs `omit`

- `exclude`:
  - Fields remain in schema but are ignored during validation
  - Excluded fields can still be present in the data
  - Useful for temporary validation skipping or partial validation
  - Validation rules remain for non-excluded fields

- `omit`:
  - Creates new schema without specified fields
  - Omitted fields are not allowed in the data
  - Useful for creating permanent subsets of schemas
  - Validates against unexpected fields

## Combining Operations

You can chain or combine these operations for more complex schema modifications:

```python
import voltar as v

# Start with comprehensive schema
full_schema = v.Object({
    "name": v.String(),
    "age": v.Number(),
    "email": v.Email(),
    "password": v.String(),
    "preferences": v.Object({
        "theme": v.String(),
        "notifications": v.Boolean()
    })
})

# Create public profile schema:
# 1. Omit sensitive fields
# 2. Extend with additional fields
# 3. Exclude validation for specific fields
public_profile = (
    full_schema
    .omit(["password", "email"])  # Remove sensitive fields
    .extend({
        "avatar": v.String(),
        "bio": v.String()
    })  # Add public profile fields
    .exclude("preferences")  # Don't validate preferences
)

# Usage:
profile = public_profile.validate({
    "name": "John",
    "age": 30,
    "avatar": "https://example.com/avatar.jpg",
    "bio": "Software developer",
    "preferences": {"invalid": "structure"}  # Allowed but not validated
})
```

## Common Use Cases

1. **API Response Schemas**
   ```python
   import voltar as v
   
   # Internal schema with all fields
   internal = v.Object({
       "id": v.Number(),
       "name": v.String(),
       "email": v.Email(),
       "created_at": v.DateTime(),
       "internal_notes": v.String()
   })

   # Public API response schema
   api_response = internal.omit(["internal_notes"])
   ```

2. **Form Validation**
   ```python
   import voltar as v
   
   # Complete user schema
   user = v.Object({
       "username": v.String(),
       "email": v.Email(),
       "password": v.String(),
       "confirm_password": v.String()
   })

   # Schema for profile update form (no password fields)
   profile_update = user.omit(["password", "confirm_password"])
   ```

3. **Role-Based Schemas**
   ```python
   import voltar as v
   
   # Base product schema
   product = v.Object({
       "id": v.Number(),
       "name": v.String(),
       "price": v.Number(),
       "cost": v.Number(),
       "supplier_id": v.String()
   })

   # Customer view (omit internal fields)
   customer_view = product.omit(["cost", "supplier_id"])

   # Sale view (exclude validation for internal calculations)
   sale_view = product.exclude("cost")
   ```

## Tips and Best Practices

1. Use `extend` when you need to add new fields while keeping existing ones

2. Use `exclude` when:
   - Fields should remain in the data but not be validated
   - Validation skipping is temporary
   - You need to preserve the field in the output

3. Use `omit` when:
   - Fields should not be present in the data
   - You're creating a permanent subset of a schema
   - You want to enforce field absence

4. When combining operations, consider the order:
   - `extend` then `omit` to remove fields from the complete schema
   - `omit` then `extend` to add new fields to a reduced schema
   - `exclude` can be used at any point to skip validation
