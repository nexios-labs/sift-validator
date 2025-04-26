"""
Test script to identify issues with optional fields.

This script focuses specifically on testing different combinations of 
optional and nullable fields to pinpoint validation issues.
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path to import sift
sys.path.insert(0, str(Path(__file__).parent))

from sift import String, Number, Boolean, Object, List, Dict
from sift.validators.base import ValidationError

def print_separator():
    print("\n" + "="*60 + "\n")

def test_optional_field():
    """Test a field marked as optional."""
    print("Testing Optional Field (no default)")
    
    # Schema with an optional field
    schema = Object({
        "name": String(),
        "description": String().optional()  # Optional with no default
    })
    
    # Case 1: Field is present
    data1 = {"name": "Test", "description": "This is a test"}
    try:
        result = schema.validate(data1)
        print(f"✓ Field present: {result}")
    except ValidationError as e:
        print(f"✗ Field present error: {e}")
    
    # Case 2: Field is missing
    data2 = {"name": "Test"}
    try:
        result = schema.validate(data2)
        print(f"✓ Field missing: {result}")
    except ValidationError as e:
        print(f"✗ Field missing error: {e}")
    
    # Case 3: Field is explicitly None
    data3 = {"name": "Test", "description": None}
    try:
        result = schema.validate(data3)
        print(f"✓ Field is None: {result}")
    except ValidationError as e:
        print(f"✗ Field is None error: {e}")

def test_optional_field_with_default():
    """Test a field marked as optional with a default value."""
    print("Testing Optional Field with Default")
    
    # Schema with an optional field with default
    schema = Object({
        "name": String(),
        "status": String().optional().default("active")
    })
    
    # Case 1: Field is present
    data1 = {"name": "Test", "status": "pending"}
    try:
        result = schema.validate(data1)
        print(f"✓ Field present: {result}")
    except ValidationError as e:
        print(f"✗ Field present error: {e}")
    
    # Case 2: Field is missing
    data2 = {"name": "Test"}
    try:
        result = schema.validate(data2)
        print(f"✓ Field missing (should use default): {result}")
    except ValidationError as e:
        print(f"✗ Field missing error: {e}")
    
    # Case 3: Field is explicitly None
    data3 = {"name": "Test", "status": None}
    try:
        result = schema.validate(data3)
        print(f"✓ Field is None: {result}")
    except ValidationError as e:
        print(f"✗ Field is None error: {e}")

def test_nullable_field():
    """Test a field marked as nullable."""
    print("Testing Nullable Field")
    
    # Schema with a nullable field
    schema = Object({
        "name": String(),
        "parent": String().nullable()  # Can be null but not missing
    })
    
    # Case 1: Field is present
    data1 = {"name": "Test", "parent": "Parent"}
    try:
        result = schema.validate(data1)
        print(f"✓ Field present: {result}")
    except ValidationError as e:
        print(f"✗ Field present error: {e}")
    
    # Case 2: Field is missing
    data2 = {"name": "Test"}
    try:
        result = schema.validate(data2)
        print(f"✓ Field missing: {result}")
    except ValidationError as e:
        print(f"✗ Field missing error: {e}")
    
    # Case 3: Field is explicitly None
    data3 = {"name": "Test", "parent": None}
    try:
        result = schema.validate(data3)
        print(f"✓ Field is None: {result}")
    except ValidationError as e:
        print(f"✗ Field is None error: {e}")

def test_optional_and_nullable():
    """Test a field marked as both optional and nullable."""
    print("Testing Optional AND Nullable Field")
    
    # Schema with a field that's both optional and nullable
    schema = Object({
        "name": String(),
        "reference": String().optional().nullable()
    })
    
    # Case 1: Field is present
    data1 = {"name": "Test", "reference": "REF-123"}
    try:
        result = schema.validate(data1)
        print(f"✓ Field present: {result}")
    except ValidationError as e:
        print(f"✗ Field present error: {e}")
    
    # Case 2: Field is missing
    data2 = {"name": "Test"}
    try:
        result = schema.validate(data2)
        print(f"✓ Field missing: {result}")
    except ValidationError as e:
        print(f"✗ Field missing error: {e}")
    
    # Case 3: Field is explicitly None
    data3 = {"name": "Test", "reference": None}
    try:
        result = schema.validate(data3)
        print(f"✓ Field is None: {result}")
    except ValidationError as e:
        print(f"✗ Field is None error: {e}")

def test_complete_example():
    """Test a complete example with multiple optional/nullable fields."""
    print("Testing Complete Example")
    
    # Create a complex schema
    user_schema = Object({
        "username": String().min(3).max(20),
        "email": String().email().optional(),     # Optional only
        "meta": Object({                          # Nested optional object
            "verified": Boolean().default(False)
        }).optional(),
        "profile": String().nullable(),           # Nullable only
        "settings": Dict().optional().nullable(), # Both optional and nullable
        "is_active": Boolean().optional().default(True)  # Optional with default
    })
    
    # Test case 1: All fields present
    full_user = {
        "username": "johndoe",
        "email": "john@example.com",
        "meta": {"verified": True},
        "profile": "User profile",
        "settings": {"theme": "dark"},
        "is_active": True
    }
    
    try:
        result = user_schema.validate(full_user)
        print("✓ Full user validation succeeded")
        print(f"  Result: {result}")
    except ValidationError as e:
        print(f"✗ Full user validation failed: {e}")
    
    # Test case 2: Only required fields
    minimal_user = {
        "username": "johndoe"
    }
    
    try:
        result = user_schema.validate(minimal_user)
        print("\n✓ Minimal user validation succeeded")
        print(f"  Result: {result}")
    except ValidationError as e:
        print(f"✗ Minimal user validation failed: {e}")
    
    # Test case 3: Mix of missing and null fields
    mixed_user = {
        "username": "johndoe",
        "profile": None,
        "settings": None,
        "is_active": False
    }
    
    try:
        result = user_schema.validate(mixed_user)
        print("\n✓ Mixed user validation succeeded")
        print(f"  Result: {result}")
    except ValidationError as e:
        print(f"✗ Mixed user validation failed: {e}")

if __name__ == "__main__":
    test_optional_field()
    print_separator()
    test_optional_field_with_default()
    print_separator()
    test_nullable_field()
    print_separator()
    test_optional_and_nullable()
    print_separator()
    test_complete_example()

