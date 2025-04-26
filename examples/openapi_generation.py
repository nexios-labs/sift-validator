"""
OpenAPI schema generation examples for the Sift library.

This example demonstrates how to generate OpenAPI schemas from Sift validators:
1. Basic schema generation
2. Complex schema examples
3. Custom validator schema generation
4. OpenAPI version differences
"""

import sys
import json
from pathlib import Path

# Add the parent directory to the Python path to import sift
sys.path.insert(0, str(Path(__file__).parent.parent))

from sift import String, Number, Boolean, Object, List, Dict, Union
from sift.validators.collections import Tuple
from sift.openapi.schema import (
    generate_schema, 
    generate_full_openapi_schema,
    OpenAPIVersion,
    SchemaContext
)

# Import custom validators for demonstration
from examples.async_validation import AsyncUsernameValidator, AsyncEmailValidator, PaymentValidator


def print_schema(schema, title="Schema"):
    """Helper function to print schemas in a readable format."""
    print(f"\n=== {title} ===")
    print(json.dumps(schema, indent=2))


def demonstrate_basic_schema_generation():
    """Demonstrate basic schema generation for primitive validators."""
    print("\n# Basic Schema Generation")
    
    # String schema
    string_validator = String().min(3).max(50).pattern(r"^[a-zA-Z0-9_]+$")
    string_schema = generate_schema(string_validator)
    print_schema(string_schema, "String Schema")
    # Output will include type: "string", minLength, maxLength, and pattern
    
    # Number schema
    number_validator = Number().int().min(1).max(100).multiple_of(5)
    number_schema = generate_schema(number_validator)
    print_schema(number_schema, "Number Schema")
    # Output will include type: "integer", minimum, maximum, and multipleOf
    
    # Boolean schema
    boolean_validator = Boolean()
    boolean_schema = generate_schema(boolean_validator)
    print_schema(boolean_schema, "Boolean Schema")
    # Output will include type: "boolean"
    
    # Optional field schema
    optional_validator = String().email().optional()
    optional_schema = generate_schema(optional_validator)
    print_schema(optional_schema, "Optional Field Schema")
    # In OpenAPI 3.0, this adds nullable: true
    
    # Default value schema
    default_validator = Number().default(0)
    default_schema = generate_schema(default_validator)
    print_schema(default_schema, "Default Value Schema")
    # Output will include default: 0
    
    # List schema
    list_validator = List(String().min(1)).min(1).max(10).unique()
    list_schema = generate_schema(list_validator)
    print_schema(list_schema, "List Schema")
    # Expected output:
    # {
    #   "type": "array",
    #   "items": { "type": "string", "minLength": 1 },
    #   "minItems": 1,
    #   "maxItems": 10,
    #   "uniqueItems": true
    # }
    
    # Nested array schema (matrix example)
    matrix_validator = List(List(Number().int()))
    matrix_schema = generate_schema(matrix_validator)
    print_schema(matrix_schema, "Nested Array Schema")
    # Expected output:
    # {
    #   "type": "array",
    #   "items": {
    #     "type": "array",
    #     "items": { "type": "integer" }
    #   }
    # }
    
    # Dict schema
    dict_validator = Dict({
        "name": String().min(1),
        "age": Number().int().min(0)
    })
    dict_schema = generate_schema(dict_validator)
    print_schema(dict_schema, "Dict Schema")
    # Expected output:
    # {
    #   "type": "object",
    #   "properties": {
    #     "name": { "type": "string", "minLength": 1 },
    #     "age": { "type": "integer", "minimum": 0 }
    #   },
    #   "required": ["name", "age"]
    # }

def demonstrate_complex_schema_examples():
    """Demonstrate complex schema examples."""
    print("\n# Complex Schema Examples")
    
    # Pattern properties - useful for dynamic object validation
    # Use case: Validating configuration objects with dynamic naming patterns
    config_schema = Dict().pattern_property(
        r"^db_", String()
    ).pattern_property(
        r"^api_", String()
    ).additional_properties(False)
    
    pattern_schema = generate_schema(config_schema)
    print_schema(pattern_schema, "Pattern Properties Schema")
    # Expected output:
    # {
    #   "type": "object",
    #   "patternProperties": {
    #     "^db_": { "type": "string" },
    #     "^api_": { "type": "string" }
    #   },
    #   "additionalProperties": false
    # }
    
    # Discriminated union - useful for polymorphic data
    # Use case: API endpoints that return different types based on a type field
    dog_schema = Object({
        "type": String().default("dog"),
        "name": String().min(1),
        "breed": String().min(1),
        "barksPerDay": Number().int().min(0)
    })
    
    cat_schema = Object({
        "type": String().default("cat"),
        "name": String().min(1),
        "breed": String().min(1),
        "livesLeft": Number().int().min(0).max(9)
    })
    
    bird_schema = Object({
        "type": String().default("bird"),
        "name": String().min(1),
        "species": String().min(1),
        "canFly": Boolean()
    })
    
    pet_schema = Union(
        [dog_schema, cat_schema, bird_schema],
        discriminator="type"
    ).discriminator_mapping({
        "dog": dog_schema,
        "cat": cat_schema,
        "bird": bird_schema
    })
    
    union_openapi = generate_schema(pet_schema)
    print_schema(union_openapi, "Discriminated Union Schema")
    # Expected output:
    # {
    #   "anyOf": [
    #     { /* dog schema */ },
    #     { /* cat schema */ },
    #     { /* bird schema */ }
    #   ],
    #   "discriminator": {
    #     "propertyName": "type",
    #     "mapping": {
    #       "dog": "#/components/schemas/dogSchema",
    #       "cat": "#/components/schemas/catSchema",
    #       "bird": "#/components/schemas/birdSchema"
    #     }
    #   }
    # }
    
    # Tuple schema (fixed-length array)
    # Use case: API endpoints that return or accept coordinates, date ranges, etc.
    tuple_schema = Tuple([
        String(),     # First item: string
        Number(),     # Second item: number
        Boolean()     # Third item: boolean
    ])
    
    tuple_openapi = generate_schema(tuple_schema)
    print_schema(tuple_openapi, "Tuple Schema")
    # Expected output in OpenAPI 3.0:
    # {
    #   "type": "array",
    #   "items": [
    #     { "type": "string" },
    #     { "type": "number" },
    #     { "type": "boolean" }
    #   ],
    #   "additionalItems": false
    # }


def demonstrate_custom_validator_schema_generation():
    """
    Demonstrate schema generation for custom validators.
    
    Custom validators maintain their base schema properties while adding specific
    validation rules. For example, AsyncUsernameValidator is still a string validator
    with specific pattern and min length rules.
    """
    print("\n# Custom Validator Schema Generation")
    
    # Username validator
    username_validator = AsyncUsernameValidator()
    username_schema = generate_schema(username_validator)
    print_schema(username_schema, "AsyncUsernameValidator Schema")
    # Output includes the base string schema with pattern and minLength
    
    # Email validator
    email_validator = AsyncEmailValidator()
    email_schema = generate_schema(email_validator)
    print_schema(email_schema, "AsyncEmailValidator Schema")
    # Output includes type: "string" with format: "email"
    
    # Payment validator
    payment_validator = PaymentValidator()
    payment_schema = generate_schema(payment_validator)
    print_schema(payment_schema, "PaymentValidator Schema")
    # Output includes schema derived from the payment_schema object
    
    # Complex registration schema with custom validators
    registration_schema = Object({
        "username": AsyncUsernameValidator(),
        "email": AsyncEmailValidator(),
        "password": String().min(8).pattern(r".*[A-Z].*").pattern(r".*[0-9].*")
            .error("Password must be at least 8 characters with uppercase and number"),
        "payment": PaymentValidator().optional()
    })
    
    registration_openapi = generate_schema(registration_schema)
    print_schema(registration_openapi, "Registration Schema with Custom Validators")
    # Output will show how custom validators are integrated in complex schemas


def demonstrate_openapi_versions():
    """Demonstrate differences between OpenAPI versions."""
    print("\n# OpenAPI Version Differences")
    
    # Create a complex schema that highlights version differences
    schema = Object({
        "string": String().nullable(),
        "number": Number().optional(),
        "array": List(String()).nullable(),
        "tuple": Tuple([String(), Number()]),
        "oneOf": Union([String(), Number()])
    })
    
    # Generate schema for OpenAPI 3.0
    context_3_0 = SchemaContext(openapi_version=OpenAPIVersion.V3_0)
    schema_3_0 = generate_schema(schema, context=context_3_0)
    print_schema(schema_3_0, "Schema in OpenAPI 3.0")
    # Output will use nullable: true for nullable fields
    
    # Generate schema for OpenAPI 3.1
    context_3_1 = SchemaContext(openapi_version=OpenAPIVersion.V3_1)
    schema_3_1 = generate_schema(schema, context=context_3_1)
    print_schema(schema_3_1, "Schema in OpenAPI 3.1")
    # Compare nullable handling - especially important for API design
    print("\n=== Nullable Handling ===")
    
    # OpenAPI 3.0 nullable handling
    nullable_string_v3_0 = generate_schema(
        String().nullable(),
        context=SchemaContext(openapi_version=OpenAPIVersion.V3_0)
    )
    print_schema(nullable_string_v3_0, "Nullable String in 3.0")
    # Expected output: { "type": "string", "nullable": true }
    
    # OpenAPI 3.1 nullable handling
    nullable_string_v3_1 = generate_schema(
        String().nullable(),
        context=SchemaContext(openapi_version=OpenAPIVersion.V3_1)
    )
    print_schema(nullable_string_v3_1, "Nullable String in 3.1")
    # Expected output: { "type": ["string", "null"] }
    
    # Compare tuple handling
    print("\n=== Tuple Handling ===")
    
    # OpenAPI 3.0 tuple representation
    tuple_v3_0 = generate_schema(
        Tuple([String(), Number(), Boolean()]),
        context=SchemaContext(openapi_version=OpenAPIVersion.V3_0)
    )
    print_schema(tuple_v3_0, "Tuple in 3.0")
    # Expected output: { "type": "array", "items": [...], "additionalItems": false }
    
    # OpenAPI 3.1 tuple representation with prefixItems
    tuple_v3_1 = generate_schema(
        Tuple([String(), Number(), Boolean()]),
        context=SchemaContext(openapi_version=OpenAPIVersion.V3_1)
    )
    print_schema(tuple_v3_1, "Tuple in 3.1")
    # Expected output: { "type": "array", "prefixItems": [...] }
    
    # Generate full OpenAPI document
    print("\n=== Full OpenAPI Document ===")
    full_openapi = generate_full_openapi_schema(
        schema,
        title="Example API",
        version="1.0.0",
        description="API using Sift validators",
        openapi_version=OpenAPIVersion.V3_0
    )
    
    print(f"Full OpenAPI Document structure (truncated):")
    print("  - openapi: 3.0.3")
    print("  - info: title, version, description")
    print("  - paths: {}")
    print("  - components: schemas including all referenced schemas")
    # We don't print the full document as it would be too verbose


def demonstrate_schema_references():
    """
    Demonstrate schema references and components.
    
    Schema references allow you to:
    1. Reuse schema definitions across your API
    2. Keep your OpenAPI document DRY (Don't Repeat Yourself)
    3. Make your documentation more maintainable
    4. Improve code generation when using tools like OpenAPI Generator
    """
    print("\n# Schema References and Components")
    
    # Define reusable schema components
    address_schema = Object({
        "street": String().min(1),
        "city": String().min(1),
        "zipCode": String().pattern(r"^\d{5}$"),
        "country": String().min(2).max(2)
    })
    
    error_schema = Object({
        "code": Number().int(),
        "message": String(),
        "details": List(String()).optional()
    })
    
    # Create a context to track references
    context = SchemaContext()
    
    # Generate schemas with references
    generate_schema(address_schema, "AddressSchema", context)
    generate_schema(error_schema, "ErrorSchema", context)
    
    # Create a schema that references the others
    user_schema = Object({
        "id": Number().int(),
        "name": String().min(1),
        "address": address_schema,  # References AddressSchema
        "lastError": error_schema    # References ErrorSchema
    })
    
    # Generate the user schema - references will be replaced with $ref
    user_openapi = generate_schema(user_schema, "UserSchema", context)
    print_schema(user_openapi, "User Schema with References")
    # Expected output will include $ref pointers to components schemas:
    # {
    #   "type": "object",
    #   "properties": {
    #     "id": { "type": "integer" },
    #     "name": { "type": "string", "minLength": 1 },
    #     "address": { "$ref": "#/components/schemas/AddressSchema" },
    #     "lastError": { "$ref": "#/components/schemas/ErrorSchema" }
    #   },
    #   "required": ["id", "name", "address", "lastError"]
    # }
    
    # Get all components
    components = context.referenced_schemas
    print_schema(components, "Components Schemas")
    # Shows all referenced schemas in the components dictionary
    
    # Generate full OpenAPI document with components
    full_openapi = generate_full_openapi_schema(
        user_schema,
        title="API with References",
        version="1.0.0",
        description="Example API demonstrating schema references",
        openapi_version=OpenAPIVersion.V3_0
    )
    
    # We don't print the full document as it would be too verbose
    print("\nFull OpenAPI document benefits of using references:")
    print("  1. Smaller document size through reuse")
    print("  2. Simplified maintenance - change once, update everywhere")
    print("  3. Better organization with components/schemas section")
    print("  4. Improved client generation with named types")


def demonstrate_real_world_examples():
    """
    Demonstrate real-world use cases for schema validation in production applications.
    
    These examples show how Sift can be used to validate:
    1. API endpoint schemas for REST APIs
    2. Data model schemas for application entities
    3. Configuration validation for application settings
    """
    print("\n# Real-World Examples")

    # 1. API Endpoint Schemas for a REST API
    print("\n## API Endpoint Schemas")
    
    # Common error response schema - reused across endpoints
    error_response_schema = Object({
        "status": String().pattern(r"^error$"),
        "code": Number().int(),
        "message": String(),
        "details": List(String()).optional(),
        "timestamp": String().datetime()
    })
    
    # User creation request schema
    user_creation_request = Object({
        "username": String().min(3).max(50).pattern(r"^[a-zA-Z0-9_]+$"),
        "email": String().email(),
        "password": String().min(8).pattern(r".*[A-Z].*").pattern(r".*[0-9].*").pattern(r".*[!@#$%^&*].*"),
        "profile": Object({
            "fullName": String().min(1),
            "bio": String().max(500).optional(),
            "age": Number().int().min(13).optional()
        }).optional()
    })
    
    # User creation response schema
    user_creation_response = Object({
        "status": String().pattern(r"^success$"),
        "data": Object({
            "id": String().pattern(r"^[0-9a-f]{24}$"),  # MongoDB ObjectId format
            "username": String(),
            "email": String().email(),
            "createdAt": String().datetime()
        })
    })
    
    # Generate OpenAPI schemas for these endpoints
    context = SchemaContext()
    
    # Register schemas with names for reference
    generate_schema(error_response_schema, "ErrorResponse", context)
    request_schema = generate_schema(user_creation_request, "UserCreationRequest", context)
    response_schema = generate_schema(user_creation_response, "UserCreationResponse", context)
    
    print_schema(request_schema, "User Creation Request Schema")
    print_schema(response_schema, "User Creation Response Schema")
    
    # Add practical usage comment
    print("\nAPI Endpoint Schema Usage:")
    print("  • Input validation for REST API endpoints")
    print("  • Response validation for testing API endpoints")
    print("  • Automatic documentation generation for API endpoints")
    print("  • Client SDK generation for consuming APIs")
    
    # 2. Data Model Schemas
    print("\n## Data Model Schemas")
    
    # Product schema in a catalog
    product_schema = Object({
        "id": String().pattern(r"^[A-Z0-9]{10}$"),
        "name": String().min(1).max(100),
        "description": String().max(5000).optional(),
        "price": Number().positive(),
        "currency": String().length(3),
        "categories": List(String()).min(1).max(5).unique(),
        "attributes": Dict().pattern_property(r"^attr_", String()),
        "variations": List(Object({
            "id": String().pattern(r"^[A-Z0-9]{10}-[A-Z0-9]{4}$"),
            "name": String().min(1),
            "price": Number().positive().optional(),
            "inventory": Number().int().min(0)
        })).optional()
    })
    
    # Order schema for e-commerce
    order_schema = Object({
        "id": String().pattern(r"^ORD-[0-9]{10}$"),
        "customerId": String().pattern(r"^CUST-[0-9]{10}$"),
        "items": List(Object({
            "productId": String().pattern(r"^[A-Z0-9]{10}$"),
            "variationId": String().pattern(r"^[A-Z0-9]{10}-[A-Z0-9]{4}$").optional(),
            "quantity": Number().int().min(1),
            "unitPrice": Number().positive()
        })).min(1),
        "shipping": Object({
            "address": Object({
                "street": String().min(1),
                "city": String().min(1),
                "postalCode": String().min(1),
                "country": String().min(2).max(2)
            }),
            "method": String().pattern(r"^(standard|express|overnight)$"),
            "trackingNumber": String().optional()
        }),
        "payment": Object({
            "method": String().pattern(r"^(credit|debit|paypal|gift)$"),
            "status": String().pattern(r"^(pending|authorized|captured|failed)$"),
            "transactionId": String().optional()
        }),
        "status": String().pattern(r"^(pending|processing|shipped|delivered|cancelled)$"),
        "createdAt": String().datetime(),
        "updatedAt": String().datetime()
    })
    
    # Generate schemas
    product_openapi = generate_schema(product_schema, "Product", context)
    order_openapi = generate_schema(order_schema, "Order", context)
    
    print_schema(product_openapi, "Product Schema")
    print_schema(order_openapi, "Order Schema")
    
    # Add practical usage comment
    print("\nData Model Schema Usage:")
    print("  • Database entity validation before save/update operations")
    print("  • Domain model validation in business logic")
    print("  • Data transfer object (DTO) validation")
    print("  • Consistent schema enforcement across microservices")
    
    # 3. Configuration Validation
    print("\n## Configuration Validation")
    
    # Environment configuration schema
    env_config_schema = Dict({
        "NODE_ENV": String().pattern(r"^(development|test|staging|production)$"),
        "PORT": String().pattern(r"^\d+$"),
        "DATABASE_URL": String().pattern(r"^postgresql://"),
        "REDIS_URL": String().pattern(r"^redis://").optional(),
        "LOG_LEVEL": String().pattern(r"^(debug|info|warn|error)$").default("info"),
        "API_TIMEOUT_MS": String().pattern(r"^\d+$").default("5000")
    }).pattern_property(
        r"^JWT_", String()  # All JWT-related env vars
    ).additional_properties(True)  # Allow other env vars
    
    # Feature flag schema
    feature_flags_schema = Dict().pattern_property(
        r"^FEATURE_", Object({
            "enabled": Boolean(),
            "percentage": Number().min(0).max(100).optional(),
            "allowlist": List(String()).optional(),
            "description": String().optional()
        })
    )
    
    # API key validation schema
    api_key_schema = Object({
        "key": String().pattern(r"^[A-Za-z0-9]{32}$"),
        "name": String().min(1),
        "permissions": List(String().pattern(r"^[a-z]+(:[a-z]+)*$")).min(1),
        "rate_limit": Number().int().positive(),
        "expires_at": String().datetime().optional()
    })
    
    # Generate schemas
    env_config_openapi = generate_schema(env_config_schema, "EnvConfig", context)
    feature_flags_openapi = generate_schema(feature_flags_schema, "FeatureFlags", context)
    api_key_openapi = generate_schema(api_key_schema, "ApiKey", context)
    
    print_schema(env_config_openapi, "Environment Configuration Schema")
    print_schema(feature_flags_openapi, "Feature Flags Schema")
    print_schema(api_key_openapi, "API Key Schema")
    
    # Add practical usage comment
    print("\nConfiguration Schema Usage:")
    print("  • Environment variable validation at application startup")
    print("  • Feature flag validation for feature toggles")
    print("  • API key validation for authentication")
    print("  • Configuration file validation (JSON, YAML, etc.)")


if __name__ == "__main__":
    # Run all the demonstration functions in sequence
    demonstrate_basic_schema_generation()
    demonstrate_complex_schema_examples()
    demonstrate_custom_validator_schema_generation()
    demonstrate_openapi_versions()
    demonstrate_schema_references()
    demonstrate_real_world_examples()
