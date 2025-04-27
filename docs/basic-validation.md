# Basic Validation

This guide covers the core validators available in Voltar  and how to use them effectively for basic validation scenarios.

## Primitive Validators

Voltar  provides a set of primitive validators for handling common data types. These serve as the building blocks for more complex validation schemas.

### String Validator

The `String` validator is used to validate and transform string values.

#### Basic Usage

```python
from voltar  import String
from voltar .validators.base import ValidationError

# Basic string validation
string_validator = String()
valid_result = string_validator.validate("hello world")  # Returns: "hello world"

# Validation rejects non-string values
try:
    string_validator.validate(123)  # Will raise ValidationError
except ValidationError as e:
    print(e)  # Expected string, got int
```

#### String Length Validation

```python
# Minimum length
min_validator = String().min(5)
min_validator.validate("hello")  # OK
min_validator.validate("hi")     # ValidationError: String must be at least 5 characters

# Maximum length
max_validator = String().max(10)
max_validator.validate("hello")  # OK
max_validator.validate("hello world is too long")  # ValidationError: String must be at most 10 characters

# Exact length
exact_validator = String().length(6)
exact_validator.validate("123456")  # OK
exact_validator.validate("12345")   # ValidationError: String must be exactly 6 characters

# Non-empty strings
nonempty = String().nonempty()
nonempty.validate("a")   # OK
nonempty.validate("")    # ValidationError: String cannot be empty
```

#### Pattern Matching

```python
# Regular expression patterns
zip_code = String().pattern(r"^\d{5}(-\d{4})?$")
zip_code.validate("12345")       # OK
zip_code.validate("12345-6789")  # OK
zip_code.validate("1234")        # ValidationError: String must match pattern ^\d{5}(-\d{4})?$

# Common format validations
email = String().email()
email.validate("user@example.com")  # OK
email.validate("invalid-email")     # ValidationError: Invalid email address format

url = String().url()
url.validate("https://example.com")  # OK
url.validate("not a url")            # ValidationError: Invalid URL format

uuid = String().uuid()
uuid.validate("123e4567-e89b-12d3-a456-426614174000")  # OK
uuid.validate("not-a-uuid")                            # ValidationError

# Date and time validation
date = String().date()
date.validate("2023-04-26")  # OK
date.validate("04/26/2023")  # ValidationError: Invalid ISO date format

datetime = String().datetime()
datetime.validate("2023-04-26T14:30:00Z")  # OK
datetime.validate("not-a-date")            # ValidationError: Invalid ISO datetime format
```

#### String Transformations

Voltar  can transform strings during validation:

```python
# Trimming whitespace
trim = String().trim()
trim.validate("  hello  ")  # Returns: "hello"

# Case conversion
lower = String().lowercase()
lower.validate("HELLO")  # Returns: "hello"

upper = String().uppercase()
upper.validate("hello")  # Returns: "HELLO"

# Chaining transformations
transform = String().trim().lowercase()
transform.validate("  HELLO  ")  # Returns: "hello"
```

### Number Validator

The `Number` validator handles numeric values (integers and floats).

#### Basic Usage

```python
from voltar  import Number

# Basic number validation
number = Number()
number.validate(42)     # Returns: 42
number.validate(3.14)   # Returns: 3.14

# Validation rejects non-numeric values
try:
    number.validate("42")  # ValidationError
except ValidationError as e:
    print(e)  # Expected number, got str
```

#### Number Type Constraints

```python
# Integer validation
integer = Number().int()
integer.validate(42)   # OK
integer.validate(3.14)  # ValidationError: Expected integer, got float

# Float validation (default behavior, accepts both ints and floats)
float_validator = Number()
float_validator.validate(3.14)  # OK
float_validator.validate(42)    # OK (integers are valid floats)
```

#### Range Validation

```python
# Minimum value
min_validator = Number().min(10)
min_validator.validate(42)  # OK
min_validator.validate(5)   # ValidationError: Value must be at least 10

# Maximum value
max_validator = Number().max(50)
max_validator.validate(42)  # OK
max_validator.validate(100) # ValidationError: Value must be at most 50

# Combined range
range_validator = Number().min(10).max(50)
range_validator.validate(42)  # OK
range_validator.validate(5)   # ValidationError
range_validator.validate(100) # ValidationError
```

#### Sign Constraints

```python
# Positive numbers (> 0)
positive = Number().positive()
positive.validate(42)   # OK
positive.validate(0)    # ValidationError: Value must be positive
positive.validate(-42)  # ValidationError: Value must be positive

# Negative numbers (< 0)
negative = Number().negative()
negative.validate(-42)  # OK
negative.validate(0)    # ValidationError: Value must be negative
negative.validate(42)   # ValidationError: Value must be negative

# Non-negative numbers (>= 0)
non_negative = Number().min(0)
non_negative.validate(0)   # OK
non_negative.validate(42)  # OK
```

#### Divisibility

```python
# Multiple of
multiple = Number().multiple_of(5)
multiple.validate(10)  # OK
multiple.validate(15)  # OK
multiple.validate(12)  # ValidationError: Value must be a multiple of 5
```

### Boolean Validator

The `Boolean` validator handles boolean values.

#### Basic Usage

```python
from voltar  import Boolean

# Basic boolean validation
boolean = Boolean()
boolean.validate(True)   # Returns: True
boolean.validate(False)  # Returns: False

# Validation rejects non-boolean values
try:
    boolean.validate("true")  # ValidationError
except ValidationError as e:
    print(e)  # Expected boolean, got str
```

#### Truthy Values

The `truthy()` method enables accepting and converting common "truthy" values:

```python
truthy = Boolean().truthy()

# True-like values
truthy.validate(True)    # Returns: True
truthy.validate(1)       # Returns: True
truthy.validate("yes")   # Returns: True
truthy.validate("true")  # Returns: True
truthy.validate("on")    # Returns: True

# False-like values
truthy.validate(False)    # Returns: False
truthy.validate(0)        # Returns: False
truthy.validate("no")     # Returns: False
truthy.validate("false")  # Returns: False
truthy.validate("off")    # Returns: False
```

### Any Validator

The `Any` validator accepts any value type:

```python
from voltar  import Any

any_validator = Any()
any_validator.validate(42)        # OK
any_validator.validate("hello")   # OK
any_validator.validate(True)      # OK
any_validator.validate(None)      # OK
any_validator.validate([1, 2, 3]) # OK
```

### Null Validator

The `Null` validator only accepts `None` values:

```python
from voltar  import Null

null_validator = Null()
null_validator.validate(None)  # OK
null_validator.validate(42)    # ValidationError: Expected None, got int
```

## Common Validation Patterns

### Optional and Nullable Fields

Voltar  makes a clear distinction between optional values (can be omitted) and nullable values (can be `None`):

```python
from voltar  import String, Object

# Optional fields (can be omitted)
schema = Object({
    "required": String(),
    "optional": String().optional()
})

schema.validate({"required": "value"})  # OK - optional field is missing
schema.validate({"required": "value", "optional": "value"})  # OK
schema.validate({"required": "value", "optional": None})  # ValidationError - not nullable

# Nullable fields (can be None)
schema = Object({
    "required": String(),
    "nullable": String().nullable()
})

schema.validate({"required": "value", "nullable": None})  # OK - nullable field is None
schema.validate({"required": "value"})  # ValidationError - still required

# Both optional and nullable
schema = Object({
    "required": String(),
    "optional_nullable": String().optional().nullable()
})

schema.validate({"required": "value"})  # OK - field is optional
schema.validate({"required": "value", "optional_nullable": None})  # OK - field accepts None
```

### Default Values

You can specify default values for optional fields:

```python
from voltar  import String, Boolean, Number, Object

schema = Object({
    "username": String(),
    "is_active": Boolean().optional().default(True),
    "score": Number().optional().default(lambda: 100)  # Dynamic default
})

# Default values are used when fields are missing
result = schema.validate({"username": "johndoe"})
print(result)  # {"username": "johndoe", "is_active": True, "score": 100}
```

## Type Coercion and Transformation

Voltar  can transform data during validation:

### String Transformations

```python
from voltar  import String

# Multiple transformations in sequence
formatted = String().trim().lowercase()
formatted.validate("  HELLO WORLD  ")  # Returns: "hello world"
```

### Number Coercion

```python
from voltar  import Number, Object

# Converting string to number (when used with .truthy())
schema = Object({
    "id": Number().int(),
    "amount": Number().min(0),
    "quantity": Number().int().optional().default(1)
})

data = {
    "id": 123,
    "amount": 99.99
}

validated = schema.validate(data)
print(validated)  # {"id": 123, "amount": 99.99, "quantity": 1}
```

### Boolean Coercion

```python
from voltar  import Boolean

# Convert various inputs to boolean
truthy = Boolean().truthy()
truthy.validate("yes")     # Returns: True
truthy.validate(1)         # Returns: True
truthy.validate("false")   # Returns: False
truthy.validate(0)         # Returns: False
```

## Validation Rules and Constraints

### Chaining Validation Rules

You can chain multiple validation rules together:

```python
from voltar  import String, Number

# Combining multiple constraints
username = String().min(3).max(20).pattern(r"^[a-zA-Z0-9_]+$")
username.validate("johndoe_123")  # OK
username.validate("jo")            # ValidationError: String must be at least 3 characters
username.validate("johndoe@123")   # ValidationError: String must match pattern ^[a-zA-Z0-9_]+$

# Number with multiple constraints
age = Number().int().min(18).max(120)
age.validate(25)  # OK
age.validate(15)  # ValidationError: Value must be at least 18
age.validate(150) # ValidationError: Value must be at most 120
```

### Customizing Validation Messages

You can provide custom error messages for any validator:

```python
from voltar  import String, Number, Object

# Custom error messages for individual validators
username = String().min(3).error("Username is too short, minimum 3 characters")
password = String().min(8).error("Password must be at least 8 characters for security")

# Custom errors for object fields
user_schema = Object({
    "username": String().min(3).error("Username must be at least 3 characters"),
    "email": String().email().error("Please provide a valid email address"),
    "age": Number().int().min(18).error("You must be 18 or older")
})
```

## Error Handling in Depth

### Simple Error Handling

```python
from voltar  import String
from voltar .validators.base import ValidationError

validator = String().email()

try:
    validator.validate("not-an-email")
except ValidationError as e:
    print(f"Validation failed: {e}")
    # Validation failed: Invalid email address format
```

### Multiple Validation Errors

When validating complex objects, Voltar  collects all validation errors:

```python
from voltar  import Object, String, Number
from voltar .validators.base import ValidationError

user_schema = Object({
    "username": String().min(3),
    "email": String().email(),
    "age": Number().int().min(18)
})

invalid_user = {
    "username": "a",          # Too short
    "email": "not-an-email",  # Invalid format
    "age": 15                 # Too young
}

try:
    user_schema.validate(invalid_user)
except ValidationError as e:
    print(f"Validation failed with {len(e.errors)} errors:")
    
    # Access structured error data
    for error in e.errors:
        path = ".".join(error.path) if error.path else "root"
        print(f"  Field: {path}, Error: {error.message}")
```

Output:

```
Validation failed with 3 errors:
  Field: username, Error: String must be at least 3 characters
  Field: email, Error: Invalid email address format
  Field: age, Error: Value must be at least 18
```

### Error Context and Path

Errors include path information to identify where in a nested structure they occurred:

```python
from voltar  import Object, String, List
from voltar .validators.base import ValidationError

schema = Object({
    "user": Object({
        "name": String().min(3),
        "contacts": List(
            Object({
                "type": String(),
                "value": String().email()
            })
        )
    })
})

invalid_data = {
    "user": {
        "name": "Jo",  # Too short
        "contacts": [
            {"type": "email", "value": "user@example.com"},  # Valid
            {"type": "email", "value": "not-an-email"}       # Invalid
        ]
    }
}

try:
    schema.validate(invalid_data)
except ValidationError as e:
    for error in e.errors:
        print(f"Error at {'.'.join(error.path)}: {error.message}")
```

Output:

```
Error at user.name: String must be at least 3 characters
Error at user.contacts.1.value: Invalid email address format
```

### Custom Error Handling

You might want to handle validation errors differently based on context:

```python
from voltar  import Object, String
from voltar .validators.base import ValidationError

# Define a schema
login_schema = Object({
    "username": String().min(3),
    "password": String().min(8)
})

# Form validation example
def validate_login_form(data):
    try:
        # Validate the data
        login_schema.validate(data)
        return {"success": True, "data": data}
    except ValidationError as e:
        # Convert validation errors to user-friendly form errors
        form_errors = {}
        for error in e.errors:
            field = error.path[0] if error.path else "form"
            form_errors[field] = error.

