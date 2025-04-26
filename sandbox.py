"""
Basic validation examples for the Sift library.

This example demonstrates:
1. Simple string/number/boolean validation
2. Validation chains
3. Error messages
4. Default values
5. Optional fields
6. Basic transformations
7. Collection validation
8. Nested object validation
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path to import sift
sys.path.insert(0, str(Path(__file__).parent.parent))

from sift import String, Number, Boolean, Object, List, Dict
from sift.validators.collections import Tuple
from sift.validators.base import ValidationError


def demonstrate_string_validation():
    """Demonstrate basic string validation."""
    print("\n=== String Validation ===")
    
    # Basic string validation
    validator = String()
    result = validator.validate("hello world")
    print(f"Basic validation: {result}")  # Output: Basic validation: hello world
    
    # Chain validation methods
    validator = String().min(5).max(20).pattern(r"^[a-zA-Z\s]+$")
    result = validator.validate("hello world")
    print(f"Chain validation: {result}")  # Output: Chain validation: hello world
    
    # String transformations
    validator = String().trim().lowercase()
    result = validator.validate("  HELLO WORLD  ")
    print(f"Transformation: {result}")  # Output: Transformation: hello world
    
    # Email validation with custom error message
    validator = String().email().error("Invalid email address")
    try:
        result = validator.validate("not-an-email")
        print(f"Email validation: {result}")
    except ValidationError as e:
        print(f"Custom error message: {e}")  # Output: Custom error message: Invalid email address


def demonstrate_number_validation():
    """Demonstrate basic number validation."""
    print("\n=== Number Validation ===")
    
    # Basic number validation
    validator = Number()
    result = validator.validate(42)
    print(f"Basic validation: {result}")  # Output: Basic validation: 42
    
    # Integer validation
    validator = Number().int()
    try:
        result = validator.validate(3.14)
        print(f"Integer validation: {result}")
    except ValidationError as e:
        print(f"Integer validation error: {e}")  # Output: Number must be an integer
    
    # Range validation
    validator = Number().min(0).max(100)
    result = validator.validate(42)
    print(f"Range validation: {result}")  # Output: Range validation: 42
    
    try:
        result = validator.validate(101)
        print(f"Range validation (should fail): {result}")
    except ValidationError as e:
        print(f"Range validation error: {e}")  # Output: Number must be at most 100
    
    # Positive/negative validation
    validator = Number().positive()
    try:
        result = validator.validate(-5)
        print(f"Positive validation: {result}")
    except ValidationError as e:
        print(f"Positive validation error: {e}")  # Output: Number must be positive (> 0)
    
    # Multiple of validation
    validator = Number().multiple_of(5)
    try:
        result = validator.validate(15)
        print(f"Multiple of validation: {result}")  # Output: Multiple of validation: 15
        
        result = validator.validate(7)
        print(f"Multiple of validation (should fail): {result}")
    except ValidationError as e:
        print(f"Multiple of validation error: {e}")  # Output: Number must be a multiple of 5


def demonstrate_boolean_validation():
    """Demonstrate basic boolean validation."""
    print("\n=== Boolean Validation ===")
    
    # Basic boolean validation
    validator = Boolean()
    result = validator.validate(True)
    print(f"Basic validation: {result}")  # Output: Basic validation: True
    
    # Truthy conversion
    validator = Boolean().truthy()
    result = validator.validate("yes")
    print(f"Truthy conversion from 'yes': {result}")  # Output: Truthy conversion from 'yes': True
    
    result = validator.validate(0)
    print(f"Truthy conversion from 0: {result}")  # Output: Truthy conversion from 0: False
    
    # Default value
    validator = Boolean().default(True)
    result = validator.validate(True)
    print(f"Default value: {result}")  # Output: Default value: True


def demonstrate_collection_validation():
    """Demonstrate collection validation features."""
    print("\n=== Collection Validation ===")
    
    # List validation
    list_validator = List(String())
    result = list_validator.validate(["hello", "world"])
    print(f"List validation: {result}")  # Output: List validation: ['hello', 'world']
    
    # List with constraints
    list_validator = List(Number().int()).min(2).max(4)
    try:
        result = list_validator.validate([1])
        print(f"List constraint validation: {result}")
    except ValidationError as e:
        print(f"List constraint error: {e}")  # Output: List must have at least 2 items
    
    # Unique items
    list_validator = List(String()).unique()
    try:
        result = list_validator.validate(["a", "b", "a"])
        print(f"Unique validation: {result}")
    except ValidationError as e:
        print(f"Unique validation error: {e}")  # Output: List items must be unique
        
    # Dictionary validation
    dict_validator = Dict({
        "name": String().min(1),
        "age": Number().int().min(0)
    })
    result = dict_validator.validate({"name": "John", "age": 30})
    print(f"Dict validation: {result}")  # Output: Dict validation: {'name': 'John', 'age': 30}
    
    # Object validation with nesting
    address_schema = Object({
        "street": String().min(1),
        "city": String().min(1),
        "zipcode": String().pattern(r"^\d{5}$")
    })
    
    user_schema = Object({
        "name": String().min(1),
        "age": Number().int().min(18),
        "address": address_schema,
        "tags": List(String()).optional()
    })
    
    valid_user = {
        "name": "John Doe",
        "age": 30,
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zipcode": "12345"
        },
        "tags": ["friend", "colleague"]
    }
    
    result = user_schema.validate(valid_user)
    print(f"Nested object validation: Valid")
    print(f"  Name: {result['name']}")
    print(f"  Age: {result['age']}")
    print(f"  Address: {result['address']['street']}, {result['address']['city']}, {result['address']['zipcode']}")
    
    # Invalid nested object
    invalid_user = {
        "name": "John Doe",
        "age": 30,
        "address": {
            "street": "123 Main St",
            "city": "Anytown",
            "zipcode": "invalid"  # Not matching pattern
        }
    }
    
    try:
        result = user_schema.validate(invalid_user)
        print(f"Nested validation (should fail): {result}")
    except ValidationError as e:
        print(f"Nested validation error: {e}")  # Output: address.zipcode: String does not match pattern: ^\d{5}$
    
    # Tuple validation
    point_validator = Tuple([Number(), Number(), String()])
    result = point_validator.validate((10.5, 20.3, "Point A"))
    print(f"Tuple validation: {result}")  # Output: Tuple validation: (10.5, 20.3, 'Point A')


def demonstrate_object_validation():
    """Demonstrate object/dictionary validation."""
    print("\n=== Object Validation ===")
    
    # Define an object schema
    user_schema = Object({
        "username": String().min(3).max(20),
        "age": Number().int().min(18),
        "email": String().email().optional(),
        "is_active": Boolean().optional().default(True)
    })

    
    # Validate a valid object
    valid_user = {
        "username": "johndoe",
        "age": 25,
        "email": "john@example.com",
    }
    
    result = user_schema.validate(valid_user)
    print(f"Valid object: {result}")
    # Output: Valid object: {'username': 'johndoe', 'age': 25, 'email': 'john@example.com', 'is_active': True}
    
    # Validate an invalid object
    invalid_user = {
        "username": "jo",  # Too short
        "age": 16,  # Too young
    }
    
    try:
        result = user_schema.validate(invalid_user)
        print(f"Invalid object: {result}")
    except ValidationError as e:
        print(f"Object validation error: {e}")  # Expected to show error


def demonstrate_error_handling():
    """Demonstrate error handling with nested structures."""
    print("\n=== Error Handling ===")
    
    # Define a complex schema with nested objects
    address_schema = Object({
        "street": String().min(1),
        "city": String().min(1),
        "postal_code": String().pattern(r"^\d{5}$").error("Postal code must be 5 digits"),
        "country": String().min(2).max(2).error("Country must be a 2-letter code")
    })
    
    user_schema = Object({
        "name": String().min(1),
        "addresses": List(address_schema).min(1)
    })
    
    # Invalid data with nested errors
    invalid_data = {
        "name": "John Doe",
        "addresses": [
            {
                "street": "123 Main St",
                "city": "Anytown",
                "postal_code": "12345",
                "country": "USA"  # Should be 2 letters
            },
            {
                "street": "456 Oak Ave",
                "city": "Othertown",
                "postal_code": "invalid",  # Invalid format
                "country": "CA"
            }
        ]
    }
    
    try:
        result = user_schema.validate(invalid_data)
        print(f"Result: {result}")
    except ValidationError as e:
        print(f"Nested validation error: {e}")
        # Expected to show errors about country and postal code


if __name__ == "__main__":
    demonstrate_string_validation()
    demonstrate_number_validation()
    demonstrate_boolean_validation()
    demonstrate_collection_validation()
    demonstrate_object_validation()
    demonstrate_error_handling()
