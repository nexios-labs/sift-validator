"""
Complex schema validation examples for the Sift library.

This example demonstrates:
1. Nested object validation
2. Pattern properties
3. Tuple validation
4. Union type validation with discriminators
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path to import sift
sys.path.insert(0, str(Path(__file__).parent.parent))

from sift import String, Number, Boolean, Object, List, Dict, Union
from sift.validators.collections import Tuple
from sift.validators.base import ValidationError


def demonstrate_nested_objects():
    """Demonstrate nested object validation."""
    print("\n=== Nested Object Validation ===")
    
    # Define a complex nested schema
    address_schema = Object({
        "street": String().min(1),
        "city": String().min(1),
        "state": String().length(2).uppercase(),
        "zip": String().pattern(r"^\d{5}(-\d{4})?$"),
        "country": String().default("US")
    })
    
    contact_schema = Object({
        "email": String().email(),
        "phone": String().pattern(r"^\+?[0-9]{10,15}$").optional(),
        "address": address_schema
    })
    
    user_schema = Object({
        "id": Number().int(),
        "firstName": String().min(1),
        "lastName": String().min(1),
        "contact": contact_schema,
        "active": Boolean().default(True)
    })
    
    # Valid nested data
    valid_data = {
        "id": 12345,
        "firstName": "John",
        "lastName": "Doe",
        "contact": {
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
            }
        }
    }
    
    try:
        result = user_schema.validate(valid_data)
        print("Valid nested object:")
        for key, value in result.items():
            if key == "contact":
                print(f"  contact:")
                for contact_key, contact_value in value.items():
                    if contact_key == "address":
                        print(f"    address:")
                        for addr_key, addr_value in contact_value.items():
                            print(f"      {addr_key}: {addr_value}")
                    else:
                        print(f"    {contact_key}: {contact_value}")
            else:
                print(f"  {key}: {value}")
    except ValidationError as e:
        print(f"Unexpected validation error: {e}")
    
    # Invalid nested data
    invalid_data = {
        "id": 12345,
        "firstName": "John",
        "lastName": "Doe",
        "contact": {
            "email": "not-an-email",  # Invalid email
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "California",  # Too long, should be 2 letters
                "zip": "invalid-zip",   # Invalid format
            }
        }
    }
    
    try:
        result = user_schema.validate(invalid_data)
        print("Unexpected success with invalid data")
    except ValidationError as e:
        print(f"Expected validation error: {e}")


def demonstrate_pattern_properties():
    """Demonstrate pattern property validation."""
    print("\n=== Pattern Property Validation ===")
    
    # Define a schema with pattern properties
    headers_schema = Dict({
        "Content-Type": String(),
        "Authorization": String().optional()
    }).pattern_property(
        r"^X-", String()  # All headers starting with X- are allowed and validated as strings
    ).additional_properties(False)  # No other headers allowed
    
    # Valid data
    valid_headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "abc123",
        "X-Api-Version": "v1.0"
    }
    
    try:
        result = headers_schema.validate(valid_headers)
        print(f"Valid pattern properties: {result}")
    except ValidationError as e:
        print(f"Unexpected validation error: {e}")
    
    # Invalid data with disallowed property
    invalid_headers = {
        "Content-Type": "application/json",
        "X-Request-ID": "abc123",
        "Custom-Header": "value"  # Not allowed by pattern or schema
    }
    
    try:
        result = headers_schema.validate(invalid_headers)
        print(f"Unexpected success: {result}")
    except ValidationError as e:
        print(f"Expected validation error: {e}")
    
    # Dynamic property validators
    metadata_schema = Dict().pattern_property(
        r"^meta_", String()
    ).pattern_property(
        r"^num_", Number().int()
    )
    
    mixed_data = {
        "meta_title": "Sample Document",
        "meta_author": "John Doe",
        "num_pages": 42,
        "num_chapters": 5
    }
    
    try:
        result = metadata_schema.validate(mixed_data)
        print(f"Mixed pattern validation: {result}")
    except ValidationError as e:
        print(f"Unexpected validation error: {e}")
    
    # Invalid pattern data
    invalid_data = {
        "meta_title": "Sample Document",
        "meta_author": "John Doe",
        "num_pages": "42",  # Should be an integer
        "other_field": "value"  # Not matching any pattern but allowed by default
    }
    
    try:
        result = metadata_schema.validate(invalid_data)
        print(f"Warning: Expected validation to fail but got: {result}")
    except ValidationError as e:
        print(f"Expected pattern validation error: {e}")


def demonstrate_tuple_validation():
    """Demonstrate tuple validation (fixed-length arrays)."""
    print("\n=== Tuple Validation ===")
    
    # Fixed-length tuple with mixed types
    # (x, y, label) point tuple
    point_schema = Tuple([
        Number().min(0),  # x coordinate
        Number().min(0),  # y coordinate
        String().min(1)   # label
    ])
    
    valid_point = (10.5, 20.3, "Point A")
    
    try:
        result = point_schema.validate(valid_point)
        print(f"Valid tuple: {result}")
    except ValidationError as e:
        print(f"Unexpected validation error: {e}")
    
    # Invalid tuple - wrong length
    invalid_point = (10.5, 20.3)  # Missing label
    
    try:
        result = point_schema.validate(invalid_point)
        print(f"Unexpected success with invalid tuple: {result}")
    except ValidationError as e:
        print(f"Expected validation error (wrong length): {e}")
    
    # Invalid tuple - wrong types
    invalid_types = (10.5, "not-a-number", "Point A")
    
    try:
        result = point_schema.validate(invalid_types)
        print(f"Unexpected success with invalid types: {result}")
    except ValidationError as e:
        print(f"Expected validation error (wrong types): {e}")
    
    # Tuple with rest elements
    # (name, age, ...tags)
    person_schema = Tuple(
        [String().min(1), Number().int().min(0)],  # Fixed: name and age
        rest_validator=String().min(1)             # Variable: tags
    )
    
    valid_person = ("John Doe", 30, "developer", "python", "validation")
    
    try:
        result = person_schema.validate(valid_person)
        print(f"Valid tuple with rest elements: {result}")
    except ValidationError as e:
        print(f"Unexpected validation error: {e}")
    
    # Invalid rest elements
    invalid_rest = ("John Doe", 30, "developer", "", 123)  # Empty string and number
    
    try:
        result = person_schema.validate(invalid_rest)
        print(f"Unexpected success with invalid rest elements: {result}")
    except ValidationError as e:
        print(f"Expected validation error (invalid rest elements): {e}")


def demonstrate_union_validation():
    """Demonstrate union type validation with discriminators."""
    print("\n=== Union Type Validation ===")
    
    # Define schemas for different shapes
    circle_schema = Object({
        "type": String().default("circle"),
        "radius": Number().positive(),
        "color": String().optional()
    })
    
    rectangle_schema = Object({
        "type": String().default("rectangle"),
        "width": Number().positive(),
        "height": Number().positive(),
        "color": String().optional()
    })
    
    triangle_schema = Object({
        "type": String().default("triangle"),
        "base": Number().positive(),
        "height": Number().positive(),
        "color": String().optional()
    })
    
    # Create a union with discriminator
    shape_schema = Union(
        [circle_schema, rectangle_schema, triangle_schema],
        discriminator="type"
    ).discriminator_mapping({
        "circle": circle_schema,
        "rectangle": rectangle_schema,
        "triangle": triangle_schema
    })
    
    # Valid shapes of different types
    shapes = [
        {"type": "circle", "radius": 5, "color": "red"},
        {"type": "rectangle", "width": 10, "height": 20, "color": "blue"},
        {"type": "triangle", "base": 15, "height": 10}
    ]
    
    print("Validating different shapes:")
    for i, shape in enumerate(shapes):
        try:
            result = shape_schema.validate(shape)
            print(f"Shape {i+1} valid: {result}")
        except ValidationError as e:
            print(f"Unexpected validation error: {e}")
    
    # Invalid discriminator
    invalid_shape = {"type": "pentagon", "sides": 5}
    
    try:
        result = shape_schema.validate(invalid_shape)
        print(f"Unexpected success with invalid shape type: {result}")
    except ValidationError as e:
        print(f"Expected validation error (invalid shape type): {e}")
    
    # Valid type but invalid properties
    invalid_properties = {"type": "circle", "radius": -5}  # Negative radius
    
    try:
        result = shape_schema.validate(invalid_properties)
        print(f"Unexpected success with invalid properties: {result}")
    except ValidationError as e:
        print(f"Expected validation error (invalid properties): {e}")
    
    # Union without discriminator (tries each schema)
    flexible_schema = Union([
        Number().int(),
        String().email(),
        List(String()).min(1)
    ])
    
    valid_values = [42, "user@example.com", ["a", "b", "c"]]
    
    print("\nValidating union without discriminator:")
    for val in valid_values:
        try:
            result = flexible_schema.validate(val)
            print(f"Valid union value: {result}")
        except ValidationError as e:
            print(f"Unexpected validation error: {e}")
    
    # Value that doesn't match any schema
    invalid_union = {"key": "value"}  # Object, not in union
    
    try:
        result = flexible_schema.validate(invalid_union)
        print(f"Unexpected success with invalid union value: {result}")
    except ValidationError as e:
        print(f"Expected validation error (no matching schema): {e}")


if __name__ == "__main__":
    demonstrate_nested_objects()
    demonstrate_pattern_properties()
    demonstrate_tuple_validation()
    demonstrate_union_validation()
