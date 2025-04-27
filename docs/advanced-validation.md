# Advanced Validation

This guide covers advanced validation techniques in Voltar , enabling you to handle complex validation scenarios and extend the library with custom functionality.

## Custom Validators

### Creating Custom Validators

You can extend Voltar  by creating custom validators that implement your specific validation logic:

```python
from voltar .validators.base import Validator, ValidationError
from typing import Any, List

class EvenNumberValidator(Validator[int, int]):
    """A validator that ensures a number is even."""
    
    def _validate(self, data: Any, path: List[str]) -> int:
        # First, ensure we have an integer
        if not isinstance(data, int):
            raise ValidationError(
                self._get_error_message(f"Expected integer, got {type(data).__name__}"),
                path
            )
        
        # Then check if it's even
        if data % 2 != 0:
            raise ValidationError(
                self._get_error_message("Number must be even"),
                path
            )
            
        return data

# Usage
even_validator = EvenNumberValidator()
even_validator.validate(2)  # OK
even_validator.validate(3)  # ValidationError: Number must be even
```

### Extending Built-in Validators

You can also extend Voltar 's built-in validators to add custom functionality:

```python
from voltar  import String
from voltar .validators.base import ValidationError
from typing import Any, List, Optional

class PasswordValidator(String):
    """Custom password validator with strength requirements."""
    
    def __init__(self, min_length: int = 8):
        super().__init__()
        self.min_length = min_length
    
    def _validate(self, data: Any, path: List[str]) -> str:
        # Use the parent's validation first
        data = super()._validate(data, path)
        
        # Check minimum length
        if len(data) < self.min_length:
            raise ValidationError(
                self._get_error_message(f"Password must be at least {self.min_length} characters"),
                path
            )
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in data):
            raise ValidationError(
                self._get_error_message("Password must contain at least one uppercase letter"),
                path
            )
        
        # Check for at least one digit
        if not any(c.isdigit() for c in data):
            raise ValidationError(
                self._get_error_message("Password must contain at least one digit"),
                path
            )
            
        return data

# Usage
password_validator = PasswordValidator(min_length=10)
password_validator.validate("StrongPass123")  # OK
password_validator.validate("weakpass")       # ValidationError: Password must contain at least one uppercase letter
password_validator.validate("Weakpass")       # ValidationError: Password must contain at least one digit
password_validator.validate("Short1")         # ValidationError: Password must be at least 10 characters
```

### Adding Custom Methods

You can add custom chainable methods to your validators:

```python
from voltar .validators.base import Validator
from typing import Any, List, TypeVar, Generic, Callable, cast, Optional

T = TypeVar('T')
R = TypeVar('R')

class CustomValidator(Validator[T, R], Generic[T, R]):
    def with_transformer(self, transformer: Callable[[T], R]) -> 'CustomValidator[T, R]':
        """Add a custom transformation function to the validator."""
        # Clone the validator
        validator = cast(CustomValidator[T, R], self.clone())
        
        # Store the original _validate method
        original_validate = validator._validate
        
        # Define a new _validate method that applies the transformation
        def new_validate(data: Any, path: List[str]) -> R:
            # First validate with the original method
            validated = original_validate(data, path)
            # Then apply the transformation
            return transformer(validated)
        
        # Replace the _validate method
        validator._validate = new_validate
        
        return validator

# Example usage with a String validator
from voltar  import String

class EnhancedString(String):
    def reverse(self) -> 'EnhancedString':
        """Add a method to reverse the string."""
        validator = cast(EnhancedString, self.clone())
        
        # Store the original _validate method
        original_validate = validator._validate
        
        # Define a new _validate method that reverses the string
        def new_validate(data: Any, path: List[str]) -> str:
            # First validate with the original method
            validated = original_validate(data, path)
            # Then reverse the string
            return validated[::-1]
        
        # Replace the _validate method
        validator._validate = new_validate
        
        return validator

# Usage
enhanced = EnhancedString().reverse()
result = enhanced.validate("hello")  # Returns: "olleh"
```

## Complex Object and Nested Validation

### Deep Nested Objects

Voltar  excels at validating deeply nested data structures:

```python
from voltar  import Object, String, Number, List, Boolean

# Define a complex nested schema
company_schema = Object({
    "name": String().min(1),
    "founded": Number().int(),
    "active": Boolean(),
    "address": Object({
        "street": String(),
        "city": String(),
        "state": String().length(2),
        "zip": String().pattern(r"^\d{5}(-\d{4})?$")
    }),
    "departments": List(
        Object({
            "name": String(),
            "head": Object({
                "name": String(),
                "title": String(),
                "hire_date": String().date()
            }),
            "employees": List(
                Object({
                    "id": Number().int(),
                    "name": String(),
                    "role": String(),
                    "contact": Object({
                        "email": String().email(),
                        "phone": String().optional()
                    })
                })
            )
        })
    )
})

# Example data
company_data = {
    "name": "Acme Inc.",
    "founded": 1985,
    "active": True,
    "address": {
        "street": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip": "62701"
    },
    "departments": [
        {
            "name": "Engineering",
            "head": {
                "name": "Jane Smith",
                "title": "CTO",
                "hire_date": "2010-05-12"
            },
            "employees": [
                {
                    "id": 1001,
                    "name": "John Doe",
                    "role": "Senior Developer",
                    "contact": {
                        "email": "john@acme.com",
                        "phone": "555-1234"
                    }
                },
                {
                    "id": 1002,
                    "name": "Alice Johnson",
                    "role": "Developer",
                    "contact": {
                        "email": "alice@acme.com"
                    }
                }
            ]
        }
    ]
}

# Validate the complex nested data
validated_company = company_schema.validate(company_data)
```

### Reusing Schema Components

For complex schemas, it's often beneficial to break down the schema into reusable components:

```python
from voltar  import Object, String, Number, List

# Reusable components
address_schema = Object({
    "street": String(),
    "city": String(),
    "state": String().length(2),
    "zip": String().pattern(r"^\d{5}(-\d{4})?$")
})

contact_schema = Object({
    "email": String().email(),
    "phone": String().optional(),
    "address": address_schema.optional()
})

person_schema = Object({
    "id": Number().int(),
    "name": String(),
    "contact": contact_schema
})

# Use components in a larger schema
employee_schema = Object({
    "personal_info": person_schema,
    "department": String(),
    "salary": Number().min(0),
    "start_date": String().date()
})

# Even more composition
team_schema = Object({
    "name": String(),
    "leader": person_schema,
    "members": List(employee_schema)
})
```

## Conditional Validation

### Dependent Fields

You can implement conditional validation where the validation of one field depends on another:

```python
from voltar  import Object, String, Number, Boolean
from voltar .validators.base import Validator, ValidationError
from typing import Any, Dict, List

class ConditionalObject(Object):
    """Object validator with support for conditional validation based on other fields."""
    
    def __init__(self, schema: Dict[str, Validator]):
        super().__init__(schema)
        self._conditions = []
    
    def when(self, field: str, condition_fn: callable, then_fn: callable) -> 'ConditionalObject':
        """Add a conditional validation rule."""
        validator = self.clone()
        validator._conditions.append((field, condition_fn, then_fn))
        return validator
    
    def _validate(self, data: Any, path: List[str]) -> Dict:
        # First validate with the normal Object validator
        result = super()._validate(data, path)
        
        # Then apply conditional validations
        for field, condition_fn, then_fn in self._conditions:
            # Check if the field exists and meets the condition
            if field in result and condition_fn(result[field]):
                # Apply the additional validation/transformation
                result = then_fn(result, path)
        
        return result

# Example usage
payment_schema = ConditionalObject({
    "method": String(),
    "amount": Number().min(0),
    "card_number": String().optional(),
    "expiry_date": String().optional(),
    "account_number": String().optional(),
    "routing_number": String().optional()
})

# Add conditional validation
payment_schema = payment_schema.when(
    field="method",
    condition_fn=lambda method: method == "credit_card",
    then_fn=lambda data, path: validate_credit_card(data, path)
).when(
    field="method",
    condition_fn=lambda method: method == "bank_transfer",
    then_fn=lambda data, path: validate_bank_transfer(data, path)
)

def validate_credit_card(data, path):
    """Validate credit card fields."""
    if "card_number" not in data or not data["card_number"]:
        raise ValidationError("Card number is required for credit card payments", path + ["card_number"])
    if "expiry_date" not in data or not data["expiry_date"]:
        raise ValidationError("Expiry date is required for credit card payments", path + ["expiry_date"])
    return data

def validate_bank_transfer(data, path):
    """Validate bank transfer fields."""
    if "account_number" not in data or not data["account_number"]:
        raise ValidationError("Account number is required for bank transfers", path + ["account_number"])
    if "routing_number" not in data or not data["routing_number"]:
        raise ValidationError("Routing number is required for bank transfers", path + ["routing_number"])
    return data

# Test with valid credit card payment
credit_card_payment = {
    "method": "credit_card",
    "amount": 100.00,
    "card_number": "4111111111111111",
    "expiry_date": "12/25"
}
payment_schema.validate(credit_card_payment)  # OK

# Test with invalid bank transfer (missing account_number)
invalid_bank_transfer = {
    "method": "bank_transfer",
    "amount": 500.00,
    "routing_number": "123456789"
}
# payment_schema.validate(invalid_bank_transfer)  # ValidationError: Account number is required for bank transfers
```

### Dynamic Schema Based on Data

You can also create schemas that adapt dynamically based on the data:

```python
from voltar  import Object, String, Number, List, Union, Any as AnyValidator
from voltar .validators.base import Validator, ValidationError
from typing import Dict, Any, List as ListType

class DynamicValidator(Validator):
    """A validator that dynamically determines the schema based on the data."""
    
    def __init__(self, schema_selector_fn):
        super().__init__()
        self.schema_selector_fn = schema_selector_fn
    
    def _validate(self, data: Any, path: ListType[str]):
        # Select the appropriate schema based on the data
        schema = self.schema_selector_fn(data)
        
        if not schema:
            raise ValidationError("Could not determine schema for data", path)
            
        # Validate with the selected schema
        return schema.validate(data)

# Example usage: Schema depends on "type" field
def select_schema(data):
    if not isinstance(data, dict) or "type" not in data:
        return None
        
    type_map = {
        "user": Object({
            "type": String(),
            "username": String().min(3),
            "email": String().email()
        }),
        "product": Object({
            "type": String(),
            "name": String(),
            "price": Number().min(0),
            "sku": String()
        }),
        "order": Object({
            "type": String(),
            "order_id": String(),
            "items": List(
                Object({
                    "product_id": String(),
                    "quantity": Number().int().min(1)
                })
            )
        })
    }
    
    return type_map.get(data["type"])

# Create the dynamic validator
dynamic_schema = DynamicValidator(select_schema)

# Validate different types of data
user_data = {
    "type": "user",
    "username": "johndoe",
    "email": "john@example.com"
}
dynamic_schema.validate(user_data)  # OK

product_data = {
    "type": "product",
    "name": "Laptop",
    "price": 999.99,
    "sku": "LT-12345"
}
dynamic_schema.validate(product_data)  # OK
```

## Union Types and Discriminators

### Basic Union Types

Use `Union` to validate data against multiple possible schemas:

```python
from voltar  import Union, Number, String, Boolean

# Create a union validator that accepts different types
multi_type = Union([String(), Number(), Boolean()])

multi_type.validate("hello")  # OK
multi_type.validate(42)       # OK
multi_type.validate(True)     # OK
multi_type.validate([])       # ValidationError: Value did not match any of the expected types
```

### Discriminated Unions

For more complex scenarios, you can use discriminated unions to select the appropriate schema based on a "discriminator" field:

```python
from voltar  import Union, Object, String, Number, List

# Define schemas for different shapes
circle_schema = Object({
    "type": String().exact("circle"),
    "radius": Number().positive()
})

rectangle_schema = Object({
    "type": String().exact("rectangle"),
    "width": Number().positive(),
    "height": Number().positive()
})

triangle_schema = Object({
    "type": String().exact("triangle"),
    "sides": List(Number().positive()).length(3)
})

# Create a union with a discriminator field
shape_schema = Union([
    circle_schema,
    rectangle_schema,
    triangle_schema
]).discriminator("type")

# Validate different shapes
circle = {"type": "circle", "radius": 5}
shape_schema.validate(circle)  # OK

rectangle = {"type": "

