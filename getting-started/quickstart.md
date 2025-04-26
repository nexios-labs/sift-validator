# Quickstart

This guide will help you quickly get started with Sift by introducing the core concepts and providing examples of common validation patterns.

## Core Concepts

Sift is built around a few simple yet powerful concepts:

- **Validators**: Classes that validate and transform data
- **Composability**: Combine validators to create complex schemas
- **Type Safety**: Leverages Python's type hints for IDE integration
- **Chaining**: Methods can be chained for concise schemas (e.g., `String().min(3).max(20)`)
- **Error Handling**: Clear and contextual error messages

## Basic Usage

First, let's import some basic validators:

```python
from sift import String, Number, Boolean, Object, List
from sift.validators.base import ValidationError
```

### Primitive Validators

#### String Validation

```python
# Basic string validation
name_validator = String()
name_validator.validate("John Doe")  # Returns: "John Doe"

# Chain methods for more specific validation
email_validator = String().email()
email_validator.validate("user@example.com")  # OK
email_validator.validate("not-an-email")  # ValidationError

# Transformations
trimmed = String().trim().validate("  hello  ")  # Returns: "hello"
```

#### Number Validation

```python
# Basic number validation
age_validator = Number().int().min(18)
age_validator.validate(25)  # OK
age_validator.validate(15)  # ValidationError: Value must be at least 18

# Float validation
price_validator = Number().min(0).max(1000)
price_validator.validate(99.99)  # OK
```

#### Boolean Validation

```python
# Basic boolean validation
is_active = Boolean().validate(True)  # Returns: True

# Truthy conversion (accepts 0/1, true/false strings, etc.)
truthy_validator = Boolean().truthy()
truthy_validator.validate(1)  # Returns: True
truthy_validator.validate("yes")  # Returns: True
```

## Complex Object Validation

Let's validate a more complex object representing a user:

```python
# Define a user schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "profile": Object({
        "bio": String().max(500).optional(),
        "is_public": Boolean().default(True)
    }).optional()
})

# Valid data
valid_user = {
    "username": "johndoe",
    "email": "john@example.com",
    "age": 25,
    "profile": {
        "bio": "Hello, I'm John!",
        "is_public": False
    }
}

# Validate the data
validated_user = user_schema.validate(valid_user)
print(validated_user)
```

## Optional and Nullable Fields

Sift handles missing data and explicit `None` values:

```python
schema = Object({
    # Required field
    "username": String().min(3),
    
    # Optional field (can be omitted)
    "bio": String().optional(),
    
    # Nullable field (can be explicitly None)
    "email": String().email().nullable(),
    
    # Both optional and nullable
    "website": String().url().optional().nullable(),
    
    # Optional with a default value
    "is_active": Boolean().optional().default(True)
})

# All these are valid
schema.validate({"username": "johndoe"})
schema.validate({"username": "johndoe", "bio": "Hello"})
schema.validate({"username": "johndoe", "email": None})
schema.validate({"username": "johndoe", "website": None})
```

## Collection Validation

### List Validation

```python
# List of strings
tags_schema = List(String()).max(5)
tags_schema.validate(["python", "validation", "sift"])  # OK

# List with unique items
unique_ids = List(Number().int()).unique()
unique_ids.validate([1, 2, 3])  # OK
unique_ids.validate([1, 2, 2])  # ValidationError: Duplicate items found
```

### Dictionary Validation

```python
# Open dictionary with string keys and number values
scores = Dict().additional_properties(Number())
scores.validate({"math": 90, "science": 85})  # OK
```

## Error Handling

Sift provides detailed validation errors that you can catch and handle:

```python
try:
    user_schema = Object({
        "username": String().min(3),
        "email": String().email(),
        "age": Number().int().min(18)
    })
    
    invalid_user = {
        "username": "jo",  # Too short
        "email": "not-an-email",
        "age": 16  # Too young
    }
    
    user_schema.validate(invalid_user)
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Access structured error data
    for error in e.errors:
        print(f"Field: {'.'.join(error.path)}, Error: {error.message}")
```

Sample output:

```
Validation failed: Multiple validation errors occurred
Field: username, Error: String must be at least 3 characters
Field: email, Error: Invalid email address format
Field: age, Error: Value must be at least 18
```

## Custom Error Messages

You can customize error messages for better user feedback:

```python
username = String().min(3).error("Username must be at least 3 characters long")
password = String().min(8).error("Password is too weak")

# When validation fails, your custom message is used
try:
    username.validate("ab")
except ValidationError as e:
    print(e)  # "Username must be at least 3 characters long"
```

## Best Practices

Here are some recommended patterns when using Sift:

1. **Define reusable schemas**: Create common schemas that can be imported and reused across your application

    ```python
    # In schemas.py
    from sift import String, Object
    
    UserSchema = Object({
        "username": String().min(3).max(50),
        "email": String().email()
    })
    
    # In your application
    from schemas import UserSchema
    
    validated_user = UserSchema.validate(user_data)
    ```

2. **Combine validators for complex schemas**: Build complex schemas by composing simpler ones

3. **Use custom error messages for user-facing validation**: Provide clear error messages for form validation

4. **Include validation in your data access layer**: Validate data before processing or storing it

5. **Leverage type hints**: Sift's type hints help your IDE provide better code completion and type checking

## Next Steps

Now that you understand the basics of Sift, you can:

- Learn about [Basic Validation](../guides/basic-validation.md) in depth
- Explore [Advanced Validation](../guides/advanced-validation.md) techniques
- Check out [Async Validation](../guides/async-validation.md) for high-performance applications
- See how to use [OpenAPI Integration](../guides/openapi.md) to generate API documentation

