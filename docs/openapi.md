# OpenAPI Integration

This guide explains how to use Voltar  to generate [OpenAPI](https://www.openapis.org/) (formerly known as Swagger) documentation for your APIs. OpenAPI provides a standardized way to describe RESTful APIs, enabling automated generation of documentation, client libraries, and testing tools.

## OpenAPI Schema Generation

### Basic Schema Generation

Voltar  provides tools to automatically convert validators into OpenAPI schema definitions:

```python
from voltar  import String, Number, Object, List, Boolean
from voltar .openapi import generate_openapi_schema

# Define a Voltar  validator
user_schema = Object({
    "id": Number().int().positive(),
    "username": String().min(3).max(50),
    "email": String().email(),
    "is_active": Boolean().default(True),
    "profile": Object({
        "full_name": String().optional(),
        "bio": String().max(500).optional(),
        "age": Number().int().min(18).optional()
    }).optional(),
    "tags": List(String()).optional()
})

# Generate OpenAPI schema
openapi_schema = generate_openapi_schema(user_schema)

# Print the resulting schema
import json
print(json.dumps(openapi_schema, indent=2))
```

This produces an OpenAPI-compatible JSON schema:

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "format": "int64",
      "minimum": 1
    },
    "username": {
      "type": "string",
      "minLength": 3,
      "maxLength": 50
    },
    "email": {
      "type": "string",
      "format": "email"
    },
    "is_active": {
      "type": "boolean",
      "default": true
    },
    "profile": {
      "type": "object",
      "properties": {
        "full_name": {
          "type": "string"
        },
        "bio": {
          "type": "string",
          "maxLength": 500
        },
        "age": {
          "type": "integer",
          "format": "int64",
          "minimum": 18
        }
      }
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": ["id", "username", "email"]
}
```

### Schema Mapping

Voltar  has built-in mapping logic that translates validator constraints to equivalent OpenAPI properties:

| Voltar  Validator  | OpenAPI Schema |
|-----------------|----------------|
| `String()`      | `{"type": "string"}` |
| `String().email()` | `{"type": "string", "format": "email"}` |
| `String().min(3)` | `{"type": "string", "minLength": 3}` |
| `Number().int()` | `{"type": "integer", "format": "int64"}` |
| `Number().min(0)` | `{"type": "number", "minimum": 0}` |
| `Boolean()` | `{"type": "boolean"}` |
| `Object({...})` | `{"type": "object", "properties": {...}}` |
| `List(...)` | `{"type": "array", "items": {...}}` |
| `nullable()` | `{"nullable": true}` |
| `optional()` | Excluded from required array |
| `default(value)` | `{"default": value}` |

## Integration with Web Frameworks

### FastAPI Integration

FastAPI has built-in support for OpenAPI, and you can use Voltar  to generate the schemas:

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from voltar  import Object, String, Number, Boolean, List as Voltar List
from voltar .openapi import generate_openapi_schema
from voltar .validators.base import ValidationError

app = FastAPI()

# Define Voltar  validator
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_admin": Boolean().default(False)
})

# Pydantic model for documentation (can be auto-generated, shown later)
class UserModel(BaseModel):
    username: str
    email: str
    age: int
    is_admin: bool = False

# Helper to validate with Voltar 
async def validate_with_voltar (request: Request, schema):
    try:
        data = await request.json()
        return await schema.validate_async(data)
    except ValidationError as e:
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        raise HTTPException(status_code=422, detail=error_details)

# Endpoint with Voltar  validation
@app.post("/users/", response_model=UserModel)
async def create_user(user_data: Dict[str, Any] = Depends(lambda request: validate_with_voltar (request, user_schema))):
    # Process validated user data
    return user_data
```

### Flask Integration

For Flask, you can use Flask-OpenAPI or manually add the schema to your Swagger UI:

```python
from flask import Flask, request, jsonify
from voltar  import Object, String, Number
from voltar .openapi import generate_openapi_schema
from voltar .validators.base import ValidationError
import json

app = Flask(__name__)

# Define Voltar  validator
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

# Generate OpenAPI schema
user_schema_openapi = generate_openapi_schema(user_schema)

# Define OpenAPI documentation
openapi_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "User API",
        "version": "1.0.0"
    },
    "paths": {
        "/users": {
            "post": {
                "summary": "Create a new user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": user_schema_openapi
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "User created successfully",
                        "content": {
                            "application/json": {
                                "schema": user_schema_openapi
                            }
                        }
                    },
                    "422": {
                        "description": "Validation error"
                    }
                }
            }
        }
    }
}

# Serve OpenAPI specification
@app.route("/openapi.json")
def get_openapi_spec():
    return jsonify(openapi_spec)

# API endpoint with Voltar  validation
@app.route("/users", methods=["POST"])
def create_user():
    try:
        user_data = request.get_json()
        validated_data = user_schema.validate(user_data)
        # Process the validated user data
        return jsonify(validated_data)
    except ValidationError as e:
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        return jsonify({"errors": error_details}), 422
```

### Nexios Integration

If you're using the Nexios framework, Voltar  validation is built-in and OpenAPI documentation is generated automatically:

```python
from nexios import get_application
from nexios.http import Request, Response
from voltar  import Object, String, Number, Boolean

app = get_application()

# Define Voltar  validator
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_active": Boolean().default(True)
})

@app.post("/users")
async def create_user(request: Request, response: Response):
    try:
        # Validate with Voltar  schema
        data = await request.json()
        validated_data = await user_schema.validate_async(data)
        
        # Process the validated data
        return response.json({"status": "success", "data": validated_data})
    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, status=422)

# Nexios automatically generates OpenAPI docs from Voltar  schemas
app.include_openapi_documentation()
```

## Custom Schema Generation and Customization

### Adding Metadata

You can add custom metadata to the generated schema:

```python
from voltar  import Object, String, Number
from voltar .openapi import generate_openapi_schema

# Define a schema with custom metadata
product_schema = Object({
    "id": Number().int().positive(),
    "name": String().min(1).max(100),
    "price": Number().min(0)
}).metadata({
    "title": "Product",
    "description": "A product available for purchase",
    "example": {
        "id": 1,
        "name": "Laptop",
        "price": 999.99
    }
})

# Generate schema with metadata
schema = generate_openapi_schema(product_schema)

# The schema will include the metadata:
# {
#   "title": "Product",
#   "description": "A product available for purchase",
#   "type": "object",
#   "properties": {...},
#   "required": [...],
#   "example": {
#     "id": 1,
#     "name": "Laptop",
#     "price": 999.99
#   }
# }
```

### Custom Schema Transformers

You can customize how Voltar  validators are converted to OpenAPI schemas:

```python
from voltar  import String, Object
from voltar .openapi import generate_openapi_schema, OpenAPISchemaTransformer
from typing import Any, Dict

# Define a custom transformer
class CustomTransformer(OpenAPISchemaTransformer):
    def transform_string(self, validator, schema):
        # First apply the default transformations
        schema = super().transform_string(validator, schema)
        
        # Add custom format for phone numbers
        if hasattr(validator, '_is_phone') and validator._is_phone:
            schema["format"] = "phone"
            
        return schema

# Add a custom method to String validator
class PhoneString(String):
    def phone(self):
        validator = self.clone()
        validator._is_phone = True
        return validator

# Use the custom validator
contact_schema = Object({
    "name": String(),
    "phone": PhoneString().phone().pattern(r'^\+\d{1,3}\s\d{3}\s\d{3}\s\d{4}$')
})

# Generate schema with custom transformer
schema = generate_openapi_schema(contact_schema, transformer=CustomTransformer())

# The schema will include the custom format:
# {
#   "type": "object",
#   "properties": {
#     "name": {
#       "type": "string"
#     },
#     "phone": {
#       "type": "string",
#       "format": "phone",
#       "pattern": "^\\+\\d{1,3}\\s\\d{3}\\s\\d{3}\\s\\d{4}$"
#     }
#   },
#   "required": ["name", "phone"]
# }
```

### Extending the OpenAPI Schema

Sometimes you need to add OpenAPI-specific details that don't map directly to validators:

```python
from voltar  import Object, String, Number, List
from voltar .openapi import generate_openapi_schema

# Define the validator
user_schema = Object({
    "id": Number().int().positive(),
    "username": String().min(3).max(50),
    "email": String().email()
})

# Generate base schema
base_schema = generate_openapi_schema(user_schema)

# Extend with additional OpenAPI details
extended_schema = {
    **base_schema,
    "title": "User",
    "description": "A user account",
    "example": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com"
    },
    "xml": {
        "name": "User"
    }
}

# Use in your API documentation
path_item = {
    "get": {
        "summary": "Get a user by ID",
        "parameters": [
            {
                "name": "id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "integer"
                }
            }
        ],
        "responses": {
            "200": {
                "description": "A single user",
                "content": {
                    "application/json": {
                        "schema": extended_schema
                    }
                }
            }
        }
    }
}
```

## Examples of Common API Patterns

### Pagination Response

A common pattern for list endpoints is pagination:

```python
from voltar  import Object, String, Number, List, Any
from voltar .openapi import generate_openapi_schema

# Define a generic item schema
item_schema = Any()  # Replace with your actual item schema

# Define a generic paginated response schema
def paginated_response(item_schema):
    return Object({
        "items": List(item_schema),
        "pagination": Object({
            "total": Number().int().min(0),
            "page": Number().int().min(1),
            "per_page": Number().int().min(1),
            "pages": Number().int().min(0)
        })
    })

# Example for a specific entity
user_schema = Object({
    "id": Number().int().positive(),
    "username": String().min(3),
    "email": String().email()
})

# Create a paginated response schema for users
users_response_schema = paginated_response(user_schema)

# Generate OpenAPI schema
openapi_schema = generate_openapi_schema(users_response_schema)

# The schema describes a paginated list response
```

### Search/Filter Request

For search or filter endpoints:

```python
from voltar  import Object, String, Number, Boolean, List
from voltar .openapi import generate_openapi_schema

# Define a search filter schema
user_filter_schema = Object({
    "query": String().optional(),
    "email_domain": String().optional(),
    "min_age": Number().int().min(0).optional(),
    "max_age": Number().int().min(0).optional(),
    "is_active": Boolean().optional(),
    "roles": List(String()).optional(),
    "sort_by": String().pattern(r"^(username|email|created_at)$").optional(),
    "sort_dir": String().pattern(r"^(asc|desc)$").optional().default("asc"),
    "page": Number().int().min(1).optional().default(1),
    "per_page": Number().int().min(1).max(100).optional().default(20)
})

# Generate OpenAPI schema
filter_schema = generate_openapi_schema(user_filter_schema)

# Use in API documentation
```

### Error Responses

Define consistent error response schemas:

```python
from voltar  import Object, String, Number, List
from voltar .openapi import generate_openapi_schema

# Define an error schema
error_schema = Object({
    "code": String(),
    "message": String(),
    "details": List(
        Object({
            "field": String().optional(),
            "error": String(),
            "path": String().optional()
        })
    ).optional()
})

# Generate OpenAPI schema for errors
error_openapi_schema = generate_openapi_schema(error_schema)

# Example of how to use in documentation
api_spec = {
    "openapi": "3.0.0",
    "paths": {
        "/users": {
            "post": {
                "responses": {
                    "200": {
                        "description": "User created successfully",
                        "content": {
                            "application/json": {
                                "schema": generate_openapi_schema(user_schema)
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request",
                        "content": {
                            "application/json": {
                                "schema": error_openapi_schema,
                                "examples": {
                                    "validation_error": {
                                        "value": {
                                            "code": "validation_error",
                                            "message": "Validation failed",
                                            "details": [
                                                {
                                                    "field": "email",
                                                    "error": "Invalid email format",
                                                    "path": "email"
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
```

### API Response Wrapper

Many APIs use a consistent wrapper for all responses:

```python
from voltar  import Object, String, Any, Boolean
from voltar .openapi import generate_openapi_schema

# Define a generic API response wrapper
def api_response(data_schema):
    return Object({
        "success": Boolean(),
        "data": data_schema,
        "error": Object({
            "code": String(),
            "message": String()
        }).optional()
    })

# Example usage for a user object
user_schema = Object({
    "id": Number().int().positive(),
    "username": String(),
    "email": String().email()
})

# Create wrapped response schema
user_response_schema = api_response(user_schema)

# Generate OpenAPI schema
response_openapi_schema = generate_openapi_schema(user_response_schema)
```

## API Documentation Best Practices

### Consistent Schema Naming

Use a consistent naming convention for your schemas to make your API documentation more navigable:

```python
# User-related schemas
user_schema = Object({...})
user_create_schema = Object({...})  # For creation (no ID)
user_update_schema = Object({...})  # For updates (all optional)
user_list_schema = paginated_response(user_schema)

# Order-related schemas
order_schema = Object({...})
order_create_schema = Object({...})
order_status_schema = Object({...})
```

### Documenting Authentication

Include authentication requirements in your OpenAPI specification:

```python
openapi_spec = {
    "openapi": "3.0.0",
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Authorization header using the Bearer scheme"
            },
            "apiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-KEY",
                "description": "API key authentication"
            }
        }
    },
    "security": [
        {"bearerAuth": []}
    ],
    "paths": {
        # Public endpoint - override the global security
        "/auth/login": {
            "post": {
                "security": [],
                # ...
            }
        },
        # Protected endpoint - uses the global security
        "/users": {
            "get": {
                # ...
            }
        },
        # Endpoint with specific security
        "/admin/settings": {
            "put": {
                "security": [
                    {"bearerAuth": []},
                    {"apiKeyAuth": []}
                ],
                # ...
            }
        }
    }
}
```

### Grouping Endpoints with Tags

Use tags to organize your API endpoints by resource or functionality:

```python
openapi_spec = {
    "openapi": "3.0.0",
    "tags": [
        {
            "name": "users",
            "description": "User management operations"
        },
        {
            "name": "products",
            "description": "Product management operations"
        },
        {
            "name": "orders",
            "description": "Order processing operations"
        }
    ],
    "paths": {
        "/users": {
            "get": {
                "tags": ["users"],
                "summary": "List all users",
                # ...
            },
            "post": {
                "tags": ["users"],
                "summary": "Create a new user",
                # ...
            }
        },
        "/products": {
            "get": {
                "tags": ["products"],
                "summary": "List all products",
                # ...
            }
        }
    }
}
```

### Documentation Beyond Schemas

Remember to document aspects of your API that aren't captured by validation schemas:

1. **Request Headers**: Document required and optional headers
2. **Response Headers**: Document headers returned by your API
3. **Rate Limiting**: Include information about rate limits
4. **Pagination**: Explain how pagination works (page/size, cursor, etc.)
5. **Versioning**: Document your API versioning strategy
6. **Deprecation**: Mark deprecated endpoints and provide alternatives

Example of documenting these aspects:

```python
path_spec = {
    "/users": {
        "get": {
            "summary": "List users",
            "description": """
Returns a paginated list of users.

## Pagination
Results are paginated using page-based pagination. Use the `page` and 
`per_page` query parameters to control pagination.

## Rate Limiting
This endpoint is limited to 100 requests per minute per API key.

## Deprecation Notice
The `sort` parameter is deprecated and will be removed in v3.0. Use 
`sort_by` and `sort_dir` instead.
            """,
            "parameters": [
                {
                    "name": "X-API-Version",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "API version (e.g., 'v2')"
                },
                {
                    "name": "page",
                    "in": "query",
                    "schema": {"type": "integer", "minimum": 1, "default": 1},
                    "description": "Page number"
                },
                {
                    "name": "per_page",
                    "in": "query",
                    "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "description": "Items per page"
                }
            ],
            "responses": {
                "200": {
                    "description": "User list retrieved successfully",
                    "headers": {
                        "X-Rate-Limit-Remaining": {
                            "description": "Number of requests left for the time window",
                            "schema": {"type": "integer"}
                        },
                        "X-Total-Count": {
                            "description": "Total number of users matching the filter",
                            "schema": {"type": "integer"}
                        }
                    },
                    "content": {
                        "application/json": {
                            "schema": generate_openapi_schema(users_response_schema)
                        }
                    }
                }
            }
        }
    }
}
```

## Conclusion

Voltar 's integration with OpenAPI makes it easy to generate accurate API documentation that stays in sync with your validation logic. By using Voltar  validators as the source of truth for both validation and documentation, you ensure consistency between your API behavior and its documentation.

Key benefits of using Voltar  with OpenAPI include:

1. **Single Source of Truth**: Your validation logic and API documentation come from the same source
2. **Type Safety**: Voltar 's strong typing ensures your documentation accurately reflects data types
3. **Automatic Updates**: Documentation automatically stays in sync when you change your validators
4. **Consistency**: Unified approach to validation across your entire API

### Next Steps

To further enhance your API documentation:

1. **Explore API Documentation Tools**: Consider tools like [Swagger UI](https://swagger.io/tools/swagger-ui/), [ReDoc](https://github.com/Redocly/redoc), or [Stoplight](https://stoplight.io/) to display your OpenAPI documentation

2. **Implement Mock Servers**: Use your OpenAPI specification to create mock servers for testing

3. **Generate Client SDKs**: Use tools like [OpenAPI Generator](https://openapi-generator.tech/) to generate client libraries for your API

4. **Add Examples**: Enhance your documentation with realistic examples for each endpoint

5. **Implement Request/Response Validation**: Use Voltar  not only for documentation but also to validate actual API requests and responses

By combining Voltar 's powerful validation capabilities with OpenAPI's standardized documentation format, you can create API documentation that's both accurate and user-friendly.

For more information about framework-specific integration, see the [Framework Integration](../deployment/framework-integration.md) guide.
