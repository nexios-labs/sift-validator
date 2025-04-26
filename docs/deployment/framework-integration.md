# Framework Integration

This guide provides detailed instructions for integrating Sift into popular web frameworks through middleware and framework-specific patterns.

## FastAPI Integration

FastAPI provides excellent support for validation and has multiple ways to integrate with Sift.

### Dependency Injection Approach

The recommended way to integrate Sift with FastAPI is through its dependency injection system:

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from typing import Dict, Any, Type, TypeVar
from sift import Object, String, Number, Boolean
from sift.validators.base import Validator, ValidationError

app = FastAPI()

T = TypeVar('T')

# Create a generic dependency function that validates request data against a schema
def validate_request_body(schema: Type[Validator]):
    async def _validate(request: Request) -> Dict[str, Any]:
        try:
            # Get JSON data from request
            body = await request.json()
            
            # Validate with Sift
            validated_data = await schema.validate_async(body)
            return validated_data
        except ValidationError as e:
            # Format error response
            error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
            raise HTTPException(
                status_code=422,
                detail={"errors": error_details}
            )
        except Exception as e:
            # Handle other errors
            raise HTTPException(
                status_code=400, 
                detail={"error": "Invalid request data", "message": str(e)}
            )
            
    return _validate

# Define schemas
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_active": Boolean().default(True)
})

# Use the dependency in routes
@app.post("/users/")
async def create_user(data: Dict[str, Any] = Depends(validate_request_body(user_schema))):
    # Data is already validated
    return {"status": "success", "data": data}
```

### Request Body Validation Middleware

For global validation behavior, you can implement a middleware:

```python
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from sift.validators.base import ValidationError
import inspect
from typing import Callable, Dict, Type

app = FastAPI()

# Store schema mapping
endpoint_schemas: Dict[str, Type[Validator]] = {}

# Custom route class that supports Sift schemas
class SiftValidatedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request):
            # Check if this endpoint has a registered schema
            endpoint_key = f"{request.method}:{request.url.path}"
            if endpoint_key in endpoint_schemas:
                try:
                    # Get request body for validation
                    body = await request.json()
                    
                    # Validate using the registered schema
                    schema = endpoint_schemas[endpoint_key]
                    validated_data = await schema.validate_async(body)
                    
                    # Store validated data in request state
                    request.state.validated_data = validated_data
                    
                except ValidationError as e:
                    # Return validation error response
                    error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
                    return JSONResponse(
                        status_code=422,
                        content={"errors": error_details}
                    )
                except Exception as e:
                    # Handle other errors
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid request data", "message": str(e)}
                    )
            
            # Call the original route handler
            return await original_route_handler(request)
            
        return custom_route_handler

# Configure app to use custom route class
app.router.route_class = SiftValidatedRoute

# Decorator to register a schema for an endpoint
def validate_with(schema):
    def decorator(func):
        endpoint_key = f"{func.__name__}"
        endpoint_schemas[endpoint_key] = schema
        return func
    return decorator

# Example usage
from sift import Object, String, Number

@app.post("/products/")
@validate_with(Object({
    "name": String().min(1),
    "price": Number().min(0)
}))
async def create_product(request: Request):
    # Access validated data from request state
    validated_data = request.state.validated_data
    return {"status": "success", "data": validated_data}
```

### Integration with Pydantic

FastAPI uses Pydantic models for validation by default, but you can combine them with Sift:

```python
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from sift import Object, String, Number, List as SiftList
from sift.validators.base import ValidationError

app = FastAPI()

# Define Sift schema
user_sift_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "tags": SiftList(String()).optional()
})

# Pydantic model for documentation and serialization
class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    age: int = Field(..., ge=18)
    tags: Optional[List[str]] = None
    
    # Use Sift for validation
    @validator('*', pre=True)
    def validate_with_sift(cls, value, values):
        # For a real implementation, you would validate the complete input
        # This is just a simplified example
        try:
            data = {
                "username": values.get("username", ""),
                "email": values.get("email", ""),
                "age": values.get("age", 0),
                "tags": values.get("tags", [])
            }
            if value == data["username"]:
                user_sift_schema.validate(data)
            return value
        except ValidationError as e:
            raise ValueError(str(e))

@app.post("/users/")
async def create_user(user: User):
    return {"status": "success", "data": user.dict()}
```

## Flask Integration

### Request Validation Decorator

A clean way to integrate Sift with Flask is through decorators:

```python
from flask import Flask, request, jsonify, g
from functools import wraps
from sift.validators.base import Validator, ValidationError

app = Flask(__name__)

def validate_json(schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check content type
            if not request.is_json:
                return jsonify({"error": "Content-Type must be application/json"}), 415
                
            # Get JSON data
            data = request.get_json()
            if data is None:
                return jsonify({"error": "Invalid JSON"}), 400
                
            try:
                # Validate with Sift
                validated_data = schema.validate(data)
                
                # Store validated data for the view
                g.validated_data = validated_data
                
                # Call the view function
                return f(*args, **kwargs)
            except ValidationError as e:
                # Format validation errors
                error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
                return jsonify({"errors": error_details}), 422
                
        return decorated_function
    return decorator

# Usage with route
from sift import Object, String, Number

@app.route('/users', methods=['POST'])
@validate_json(Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
}))
def create_user():
    # Access validated data
    data = g.validated_data
    
    # Process the data (e.g., save to database)
    # ...
    
    return jsonify({"status": "success", "data": data})
```

### Flask Middleware Approach

For global validation, implement a middleware that validates based on route configuration:

```python
from flask import Flask, request, jsonify, g
from sift.validators.base import ValidationError

app = Flask(__name__)

# Store route schemas
route_schemas = {}

# Register a schema for a route
def register_schema(route, methods, schema):
    for method in methods:
        route_key = f"{method}:{route}"
        route_schemas[route_key] = schema

# Validation middleware
@app.before_request
def validate_request():
    # Skip validation for non-JSON requests
    if not request.is_json:
        return
        
    # Check if route has a schema
    route_key = f"{request.method}:{request.path}"
    if route_key not in route_schemas:
        return
        
    # Get JSON data
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400
        
    try:
        # Validate with schema
        schema = route_schemas[route_key]
        validated_data = schema.validate(data)
        
        # Store for route handler
        g.validated_data = validated_data
    except ValidationError as e:
        # Format validation errors
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        return jsonify({"errors": error_details}), 422

# Example usage
from sift import Object, String, Number

# Register schema for user creation
register_schema(
    '/users', 
    ['POST'], 
    Object({
        "username": String().min(3).max(50),
        "email": String().email(),
        "age": Number().int().min(18)
    })
)

@app.route('/users', methods=['POST'])
def create_user():
    # Access validated data
    data = g.validated_data
    
    # Process the data
    return jsonify({"status": "success", "data": data})
```

### Flask Class-Based Views Integration

For more organized code, use class-based views with Sift:

```python
from flask import Flask, jsonify, request
from flask.views import MethodView
from sift.validators.base import ValidationError

app = Flask(__name__)

class ValidatedMethodView(MethodView):
    schemas = {}  # Override in subclasses to define schemas by method
    
    def dispatch_request(self, *args, **kwargs):
        # Check if schema exists for method
        method = request.method.lower()
        if method in self.schemas and request.is_json:
            # Get JSON data
            data = request.get_json()
            if data is None:
                return jsonify({"error": "Invalid JSON"}), 400
                
            try:
                # Validate with schema
                schema = self.schemas[method]
                validated_data = schema.validate(data)
                
                # Add to keyword arguments
                kwargs['validated_data'] = validated_data
            except ValidationError as e:
                # Format validation errors
                error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
                return jsonify({"errors": error_details}), 422
        
        # Call the appropriate method
        return super().dispatch_request(*args, **kwargs)

# Example usage
from sift import Object, String, Number, Boolean

class UserAPI(ValidatedMethodView):
    schemas = {
        'post': Object({
            "username": String().min(3).max(50),
            "email": String().email(),
            "age": Number().int().min(18)
        }),
        'put': Object({
            "username": String().min(3).max(50).optional(),
            "email": String().email().optional(),
            "is_active": Boolean().optional()
        })
    }
    
    def post(self, validated_data):
        # Process validated data for user creation
        return jsonify({"status": "success", "data": validated_data})
        
    def put(self, user_id, validated_data):
        # Update user with validated data
        return jsonify({"status": "success", "id": user_id, "data": validated_data})

# Register the view
app.add_url_rule('/users', view_func=UserAPI.as_view('create_user'))
app.add_url_rule('/users/<int:user_id>', view_func=UserAPI.as_view('update_user'))
```

## Django Integration

### Django REST Framework Integration

Integrate Sift with Django REST Framework for API validation:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sift.validators.base import Validator, ValidationError

class SiftValidatedView(APIView):
    schema = None  # Override in subclasses
    
    def validate_request(self, request):
        """Validate request data against the schema."""
        if self.schema is None:
            return request.data
            
        try:
            validated_data = self.schema.validate(request.data)
            return validated_data
        except ValidationError as e:
            # Format validation errors for DRF response
            error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
            self.validation_errors = error_details
            return None
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to validate before processing."""
        self.validation_errors = None
        self.validated_data = self.validate_request(request)
        
        if self.validated_data is None and self.validation_errors is not None:
            return Response(
                {"errors": self.validation_errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
            
        return super().dispatch(request, *args, **kwargs)

# Example usage
from sift import Object, String, Number

class UserView(SiftValidatedView):
    schema = Object({
        "username": String().min(3).max(50),
        "email": String().email(),
        "age": Number().int().min(18)
    })
    
    def post(self, request):
        # Access validated data
        data = self.validated_data
        
        # Process data
        # ...
        
        return Response({"status": "success", "data": data})
```

### Django Middleware

For global request validation, implement a Django middleware:

```python
from django.http import JsonResponse
import json
from sift.validators.base import ValidationError

class SiftValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Initialize route schemas
        self.route_schemas = {}  # Populate from settings or registry
        
    def __call__(self, request):
        # Only validate POST, PUT, PATCH with JSON content
        if request.method not in ('POST', 'PUT', 'PATCH'):
            return self.get_response(request)
            
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return self.get_response(request)
            
        # Check if path has registered schema
        path = request.path
        method = request.method
        route_key = f"{method}:{path}"
        
        if route_key not in self.route_schemas:
            return self.get_response(request)
            
        # Get request body
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        try:
            # Validate with schema
            schema = self.route_schemas[route_key]
            validated_data = schema.validate(body)
            
            # Attach validated data to request
            request.validated_data = validated_data
            
            # Continue processing
            return self.get_response(request)
        except ValidationError as e:
            # Format validation errors
            error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
            return JsonResponse({"errors": error_details}, status=422)

# Configure in settings.py
"""
MIDDLEWARE = [
    # ...
    'myapp.middleware.SiftValidationMiddleware',
    # ...
]
"""

# In a registry or app initialization
from django.apps import AppConfig
from sift import Object, String, Number

class MyAppConfig(AppConfig):
    name = 'myapp'
    
    def ready(self):
        from myapp.middleware import SiftValidationMiddleware
        
        # Register schemas for routes
        SiftValidationMiddleware.route_schemas = {
            "POST:/api/users": Object({
                "username": String().min(3).max(50),
                "email": String().email(),
                "age": Number().int().min(18)
            }),
            "PUT:/api/users/\d+": Object({  # Regex pattern for numeric IDs
                "username": String().min(3).max(50).optional(),
                "email": String().email().optional()
            })
        }
```

### Django Form Integration

You can also integrate Sift with Django Forms for hybrid validation:

```python
from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from sift import Object, String, Number
from sift.validators.base import ValidationError as SiftValidationError

class SiftModelForm(forms.ModelForm):
    """A ModelForm that also uses Sift for validation."""
    
    sift_schema = None  # Override in subclasses
    
    def clean(self):
        """Use Sift to validate the cleaned data."""
        cleaned_data = super().clean()
        
        if self.sift_schema is not None:
            try:
                # Validate with Sift
                self.sift_schema.validate(cleaned_data)
            except SiftValidationError as e:
                # Convert Sift errors to Django form errors
                for err in e.errors:
                    field = err.path[0] if err.path else None
                    if field and field in self.fields:
                        self.add_error(field, err.message)
                    else:
                        raise DjangoValidationError(err.message)
        
        return cleaned_data

# Example usage
from django.contrib.auth.models import User

class UserForm(SiftModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
    
    # Define Sift schema for additional validation
    sift_schema = Object({
        "username": String().min(3).pattern(r"^[a-zA-Z0-9_]+$"),
        "email": String().email(),
        "first_name": String().optional(),
        "last_name": String().optional()
    })
```

## Nexios Framework Integration

[Nexios](https://nexios.io/) is a modern ASGI framework developed by the same team behind Sift, offering first-class integration.

### Basic Integration

Sift is built into Nexios, making validation straightforward:

```python
from nexios import get_application
from nexios.http import Request, Response
from sift import Object, String, Number, Boolean

app = get_application()

# Define your validation schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_active": Boolean().default(True)
})

@app.post("/users")
async def create_user(request: Request, response: Response):
    # Validate with Sift
    try:
        data = await request.json
        validated_data = await user_schema.validate_async(data)
        
        # Process validated data
        # ...
        
        return response.json({
            "status": "success",
            "data": validated_data
        })
    except Exception as e:
        return response.json({
            "status": "error",
            "message": str(e)
        }, status=422)
```

### Built-in Request Validation

Nexios provides built-in request body validation with Sift:

```python
from nexios import get_application
from nexios.http import Request, Response, validate_json
from sift import Object, String, Number

app = get_application()

# Define schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

# Use the built-in validator decorator
@app.post("/users")
@validate_json(user_schema)
async def create_user(request: Request, response: Response):
    # Access pre-validated data
    validated_data = request.state.validated_data
    
    # Process validated data
    # ...
    
    return response.json({
        "status": "success",
        "data": validated_data
    })
```

### Nexios Form Validation

For form validation, Nexios provides form helpers built on Sift:

```python
from nexios import get_application
from nexios.http import Request, Response
from nexios.forms import Form, field
from sift import String, Number, Boolean

app = get_application()

# Define a form with Sift validators
class UserForm(Form):
    username = field(String().min(3).max(50))
    email = field(String().email())
    age = field(Number().int().min(18))
    is_active = field(Boolean().default(True))

@app.post("/users")
async def create_user(request: Request, response: Response):
    # Process form
    form = await UserForm.from_request(request)
    
    if form.is_valid:
        # Access validated data
        user_data = form.validated_data
        
        # Process user data
        # ...
        
        return response.json({
            "status": "success",
            "data": user_data
        })
    else:
        # Return validation errors
        return response.json({
            "status": "error",
            "errors": form.errors
        }, status=422)
```

### Nexios OpenAPI Integration

Nexios can generate OpenAPI documentation from Sift schemas:

```python
from nexios import get_application
from nexios.http import Request, Response, validate_json
from nexios.openapi import setup_openapi
from sift import Object, String, Number

app = get_application()

# Define schemas
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

response_schema = Object({
    "status": String(),
    "data": user_schema.optional(),
    "error": String().optional()
})

@app.post("/users")
@validate_json(user_schema)
async def create_user(request: Request, response: Response):
    """Create a new user.
    
    This endpoint creates a new user with the provided data.
    """
    validated_data = request.state.validated_data
    
    # Process data
    # ...
    
    return response.json({
        "status": "success",
        "data": validated_data
    })

# Setup OpenAPI documentation
setup_openapi(app, 
    title="User API",
    version="1.0.0",
    description="API for managing users"
)

# Serve Swagger UI
app.mount_swagger_ui("/docs")
```

## Error Handling Best Practices

### Consistent Error Format

Maintain a consistent error response format across your API:

```python
# Define a standard error response formatter
def format_validation_error(error):
    """Format validation errors into a standardized response."""
    errors = []
    for err in error.errors:
        field = ".".join(err.path) if err.path else "data"
        errors.append({
            "field": field,
            "code": "validation_error",
            "message": err.message
        })
    
    return {
        "status": "error",
        "code": "validation_failed",
        "message": "The provided data failed validation.",
        "errors": errors
    }

# Usage example (with FastAPI)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=format_validation_error(exc)
    )
```

### Field-Specific Custom Messages

Provide user-friendly error messages for specific fields:

```python
from sift import Object, String, Number

# Use custom error messages for better UX
user_schema = Object({
    "username": String().min(3).max(50),
    "email": email_schema,
    "created_at": timestamp_schema
})

# User schemas for different endpoints
user_create_schema = Object({
    **user_base_schema.schema_dict,  # Reuse the base schema
    "password": String().min(8)
})

user_update_schema = Object({
    "username": String().min(3).max(50).optional(),
    "email": email_schema.optional(),
    "is_active": Boolean().optional()
})

user_response_schema = Object({
    "id": id_schema,
    **user_base_schema.schema_dict,
    "is_active": Boolean()
})

# List response with pagination
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

# Create paginated list schemas
users_list_schema = paginated_response(user_response_schema)
```

### Lazy Schema Initialization

For complex schemas, use lazy initialization to avoid startup overhead:

```python
from functools import lru_cache
from sift import Object, String, Number, Boolean, List

# Use a function to create schemas on demand
@lru_cache(maxsize=None)  # Cache the created schema
def get_user_schema():
    """Create and return the user schema."""
    return Object({
        "username": String().min(3).max(50),
        "email": String().email(),
        "age": Number().int().min(18),
        "preferences": Object({
            "theme": String().pattern(r"^(light|dark|system)$").default("system"),
            "notifications": Boolean().default(True),
            "language": String().default("en")
        }).optional()
    })

# In your API endpoint
@app.post("/users")
async def create_user(request: Request):
    # Get the schema only when needed
    schema = get_user_schema()
    
    # Use the schema
    try:
        data = await request.json()
        validated_data = await schema.validate_async(data)
        # Process validated data...
        return JSONResponse({"status": "success", "data": validated_data})
    except ValidationError as e:
        # Handle error...
        return JSONResponse({"errors": format_errors(e)}, status_code=422)
```

### Caching Validation Results

For frequently used validators, cache validation results:

```python
import functools
from sift.validators.base import Validator, ValidationError

class CachedValidator:
    """A wrapper that caches validation results."""
    
    def __init__(self, validator, cache_size=128):
        self.validator = validator
        self.validate = functools.lru_cache(maxsize=cache_size)(self._validate)
        self.validate_async = self._validate_async  # Async wrapper
    
    def _validate(self, data_str):
        """Cached validation method.
        
        Uses a string representation of data as cache key.
        """
        # Convert string back to original format for validation
        import json
        data = json.loads(data_str)
        
        # Perform validation
        return self.validator.validate(data)
    
    async def _validate_async(self, data):
        """Async validation that uses the cached sync validation."""
        # For async validation, convert data to string for cache key
        import json
        data_str = json.dumps(data, sort_keys=True)
        
        # Use the cached validation
        return self.validate(data_str)

# Usage
from sift import Object, String, Number

# Create a schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

# Create a cached version
cached_schema = CachedValidator(user_schema)

# In your API handler
async def handle_request(data):
    # This will use the cache for repeated validations of the same data
    validated_data = await cached_schema.validate_async(data)
    return validated_data
```

### Request-level Caching

Cache validated data at the request level to avoid re-validation:

```python
from functools import wraps
from flask import g, request
from sift.validators.base import ValidationError

def validate_once(schema):
    """Validate request data only once per request, even if called multiple times."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate a cache key based on the schema and request
            cache_key = f"validation:{id(schema)}"
            
            # Check if we already validated
            if hasattr(g, cache_key):
                return f(*args, **kwargs)
            
            # Perform validation
            try:
                data = request.get_json()
                validated_data = schema.validate(data)
                
                # Store validated data
                setattr(g, cache_key, validated_data)
                g.validated_data = validated_data  # For convenience
                
                return f(*args, **kwargs)
            except ValidationError as e:
                # Handle validation error
                error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
                return {"errors": error_details}, 422
                
        return decorated_function
    return decorator
```

## Asynchronous Optimization Examples

### Parallel Field Validation

For complex objects, validate fields in parallel:

```python
import asyncio
from sift import String, Number
from sift.validators.base import ValidationError

async def validate_fields_parallel(data, field_validators):
    """Validate multiple fields in parallel."""
    tasks = []
    results = {}
    
    # Create validation tasks for each field
    for field, validator in field_validators.items():
        if field in data:
            task = asyncio.create_task(validate_field(field, data[field], validator))
            tasks.append(task)
    
    # Run all validation tasks in parallel
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect results and errors
    errors = []
    for task in tasks:
        if isinstance(task.exception(), ValidationError):
            errors.append(task.exception())
        elif task.exception() is None:
            field, value = task.result()
            results[field] = value
    
    # If there are errors, raise a combined error
    if errors:
        combined_errors = []
        for error in errors:
            combined_errors.extend(error.errors)
        raise ValidationError(combined_errors)
    
    return results

async def validate_field(field, value, validator):
    """Validate a single field."""
    result = await validator.validate_async(value)
    return (field, result)

# Example usage
user_validators = {
    "username": String().min(3).max(50),
    "email": String().email(),
    "profile": Object({
        "bio": String().max(500),
        "website": String().url().optional()
    })
}

async def validate_user(data):
    try:
        validated_data = await validate_fields_parallel(data, user_validators)
        return validated_data
    except ValidationError as e:
        # Handle validation errors
        print(f"Validation errors: {e}")
        raise
```

### FastAPI Background Validation

For non-critical validations, use background tasks:

```python
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sift import Object, String, List
from sift.validators.base import ValidationError

app = FastAPI()

# Simple schema for initial validation
quick_schema = Object({
    "title": String().min(1),
    "content": String().min(1)
})

# Comprehensive schema for background validation
comprehensive_schema = Object({
    "title": String().min(1).max(200).pattern(r"^[A-Za-z0-9\s\-_.,!?]+$"),
    "content": String().min(10).max(50000),
    "tags": List(String().pattern(r"^[a-z0-9\-]+$")).max(10),
    "metadata": Object({
        "author": String(),
        "source": String().url().optional(),
        "language": String().pattern(r"^[a-z]{2}$").default("en")
    }).optional()
})

async def validate_post_background(post_id, data):
    """Perform comprehensive validation in the background."""
    try:
        # Perform detailed validation
        await comprehensive_schema.validate_async(data)
        # Update post status to "validated"
        await update_post_status(post_id, "validated")
    except ValidationError as e:
        # Mark post as requiring review
        await update_post_status(post_id, "needs_review", errors=e.errors)
        # Notify moderators
        await notify_moderators(post_id, e.errors)

@app.post("/posts")
async def create_post(
    background_tasks: BackgroundTasks,
    data: dict
):
    # Perform quick validation
    try:
        validated_data = quick_schema.validate(data)
    except ValidationError as e:
        # Return immediate error for basic validation failures
        return JSONResponse(status_code=422, content={"errors": e.errors})
    
    # Save post with "pending" status
    post_id = await save_post(validated_data, status="pending")
    
    # Schedule comprehensive validation in the background
    background_tasks.add_task(validate_post_background, post_id, data)
    
    return {
        "id": post_id,
        "status": "pending",
        "message": "Post created and awaiting validation"
    }
```

## Conclusion and Best Practices

When integrating Sift with web frameworks, follow these best practices for optimal results:

### Architecture Recommendations

1. **Separate Validation Logic**: Keep validation schemas in dedicated modules or packages separate from your route handlers.

2. **Validation First**: Validate input data as early as possible in the request processing pipeline.

3. **Consistent Error Handling**: Implement a consistent approach to formatting and returning validation errors.

4. **Layered Validation**: Use multiple levels of validation when appropriate:
   - Fast, lightweight validation at the API boundary
   - More thorough validation for business logic
   - Domain-specific validation closer to persistence layer

5. **Reuse Common Validators**: Create and share validator components across your application.

### Performance Considerations

1. **Cache Validation Results**: For frequently used validators or static data, implement caching strategies.

2. **Lazy Initialization**: Initialize complex validators only when needed.

3. **Async When Appropriate**: Use asynchronous validation for I/O-bound operations like database checks.

4. **Parallel Validation**: For independent fields, use parallel validation to improve performance.

5. **Background Validation**: For non-critical checks, consider moving complex validation to background tasks.

### Integration Patterns

1. **Framework-Specific Approaches**:
   - FastAPI: Use dependency injection and Pydantic integration
   - Flask: Use decorators and request/response hooks
   - Django: Integrate with forms and middleware
   - Nexios: Leverage built-in validation decorators

2. **Documentation Integration**:
   - Generate OpenAPI schemas from your Sift validators
   - Keep validation and documentation in sync automatically

3. **Testing Strategy**:
   - Write tests for your
    "email": String().email().error(
        "Please provide a valid email address"
    ),
    "password": String().min(8).pattern(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).*$").error(
        "Password must be at least 8 characters and include uppercase, lowercase, and numbers"
    ),
    "age": Number().int().min(18).error(
        "You must be at least 18 years old to register"
    )
})
```

### Graceful Error Recovery

Implement graceful degradation where appropriate:

```python
from sift import Object, String, List, Any
from sift.validators.base import ValidationError

def validate_with_fallback(data, schema, fallback_schema=None):
    """Try strict validation first, then fall back to a more permissive schema if needed."""
    try:
        return schema.validate(data), None
    except ValidationError as e:
        if fallback_schema:
            try:
                return fallback_schema.validate(data), e
            except ValidationError:
                raise e
        else:
            raise e

# Example usage
strict_schema = Object({
    "name": String().min(1),
    "tags": List(String().pattern(r"^[a-z0-9-]+$"))
})

permissive_schema = Object({
    "name": String().min(1),
    "tags": List(Any())  # Accept any tags, clean them later
})

def process_item(data):
    validated, warning = validate_with_fallback(data, strict_schema, permissive_schema)
    
    if warning:
        # Log warning but continue processing with the permissive result
        print(f"Warning: Using permissive validation: {warning}")
        
        # Maybe clean up the data
        if "tags" in validated:
            validated["tags"] = [str(tag).lower().replace(" ", "-") for tag in validated["tags"]]
    
    return validated
```
## Performance Optimization Tips

### Schema Reuse

Define schemas once and reuse them to avoid overhead:

```python
# schemas.py
from sift import Object, String, Number, Boolean, List

# Base schemas
id_schema = Number().int().positive()

email_schema = String().email()

timestamp_schema = String().datetime()

# Composed schemas
user_base_schema = Object({
    "username": String().min(3).max(50),
    "email": email_schema,
    "created_at": timestamp_schema
})

# User schemas for different endpoints
user_create_schema = Object({
    **user_base_schema.schema_dict,  # Reuse the base schema
    "password": String().min(8)
})

user_update_schema = Object({
    "username": String().min(3).max(50).optional(),
    "email": email_schema.optional()
})

user_response_schema = Object({
    "id": id_schema,
    **user_base_schema.schema_dict,
    "is_active": Boolean()
})
```

### Validator Registry

Create a central registry for validators to easily manage and update them:

```python
# validators_registry.py
from sift import Object, String, Number, Boolean, List

class ValidatorRegistry:
    """Central registry for validators."""
    
    _validators = {}
    
    @classmethod
    def register(cls, name, validator):
        """Register a validator with a name."""
        cls._validators[name] = validator
        return validator
    
    @classmethod
    def get(cls, name):
        """Get a validator by name."""
        return cls._validators.get(name)

# Register common validators
registry = ValidatorRegistry()

# Define and register validators
registry.register("email", String().email())
registry.register("username", String().min(3).max(50).pattern(r"^[a-zA-Z0-9_]+$"))
registry.register("password", String().min(8).pattern(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$"))

# Create schemas from registry components
user_schema = Object({
    "username": registry.get("username"),
    "email": registry.get("email"),
    "password": registry.get("password")
})
```

### Advanced Caching Strategies

#### Global Validator Cache

Implement a global LRU cache for commonly used validators:

```python
import functools
from typing import Dict, Any, Tuple, Hashable
import hashlib
import json

class ValidationCache:
    """Global validation cache."""
    
    def __init__(self, max_size=1000):
        self.cache = functools.lru_cache(maxsize=max_size)(self._cached_validate)
        
    def _data_to_key(self, data: Any) -> Hashable:
        """Convert data to a hashable key."""
        # For simple types
        if isinstance(data, (str, int, float, bool)):
            return data
            
        # For complex types, use JSON representation with consistent key ordering
        json_str = json.dumps(data, sort_keys=True)
        # Use hash for very large data to avoid memory issues
        if len(json_str) > 1000:
            return hashlib.md5(json_str.encode()).hexdigest()
        return json_str
        
    def _cached_validate(self, validator_id: str, data_key: Hashable) -> Tuple[Dict, bool]:
        """Cache lookup function."""
        # This function doesn't actually do validation
        # It's just a placeholder for the cache
        return None
        
    def get(self, validator_id: str, data: Any) -> Tuple[Any, bool]:
        """Get validation result from cache."""
        data_key = self._data_to_key(data)
        cache_entry = self.cache(validator_id, data_key)
        if cache_entry is None:
            return None, False
        return cache_entry, True
        
    def set(self, validator_id: str, data: Any, result: Any) -> None:
        """Store validation result in cache."""
        data_key = self._data_to_key(data)
        # Hack: call the function to store in cache
        self.cache.__wrapped__.__closure__[0].cell_contents[validator_id, data_key] = result

# Global cache instance
validation_cache = ValidationCache()

# Create a cached validator
from sift.validators.base import Validator

class CachedGlobalValidator:
    """Wrapper for a validator that uses the global cache."""
    
    def __init__(self, validator: Validator, validator_id: str = None):
        self.validator = validator
        self.validator_id = validator_id or str(id(validator))
        
    def validate(self, data):
        """Validate with caching."""
        # Check cache
        cached_result, cache_hit = validation_cache.get(self.validator_id, data)
        if cache_hit:
            return cached_result
            
        # Perform validation
        result = self.validator.validate(data)
        
        # Store in cache
        validation_cache.set(self.validator_id, data, result)
        return result
```

### Efficient Validation in High-Load Scenarios

#### Adaptive Validation Level

Adjust validation depth based on system load:

```python
import os
import psutil
from enum import Enum
from sift import Object, String, Number, List

class ValidationLevel(Enum):
    MINIMAL = 1   # Basic validation only
    STANDARD = 2  # Regular validation
    STRICT = 3    # Full validation with all checks

def get_current_load():
    """Get current system load."""
    # CPU load
    cpu_percent = psutil.cpu_percent(interval=0.1)
    # Memory usage
    memory_percent = psutil.virtual_memory().percent
    return (cpu_percent + memory_percent) / 2

def determine_validation_level():
    """Determine appropriate validation level based on load."""
    load = get_current_load()
    
    if load > 80:
        return ValidationLevel.MINIMAL
    elif load > 50:
        return ValidationLevel.STANDARD
    else:
        return ValidationLevel.STRICT

# Create schemas for different validation levels
minimal_schema = Object({
    "username": String(),
    "email": String().email()
})

standard_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18).optional()
})

strict_schema = Object({
    "username": String().min(3).max(50).pattern(r"^[a-zA-Z0-9_]+$"),
    "email": String().email(),
    "age": Number().int().min(18).optional(),
    "profile": Object({
        "bio": String().max(500).optional(),
        "website": String().url().optional()
    }).optional(),
    "tags": List(String()).optional()
})

def get_validation_schema():
    """Get the appropriate validation schema for the current load."""
    level = determine_validation_level()
    
    if level == ValidationLevel.MINIMAL:
        return minimal_schema
    elif level == ValidationLevel.STANDARD:
        return standard_schema
    else:
        return strict_schema

# In your API handler
def handle_request(data):
    """Handle request with adaptive validation."""
    schema = get_validation_schema()
    validated_data = schema.validate(data)
    return validated_data
```

#### Validation Throttling

Implement rate limiting for expensive validations:

```python
import time
from functools import wraps

class ValidationThrottler:
    """Rate limiter for expensive validations."""
    
    def __init__(self, max_validations_per_second=100):
        self.max_validations = max_validations_per_second
        self.current_count = 0
        self.reset_time = time.time() + 1.0
        
    def throttle(self, validator_fn):
        """Decorator to throttle a validation function."""
        @wraps(validator_fn)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Reset counter if second has elapsed
            if current_time > self.reset_time:
                self.current_count = 0
                self.reset_time = current_time + 1.0
                
            # Check if we're over the limit
            if self.current_count >= self.max_validations:
                # Fall back to simpler validation or queue the validation
                return self.fallback_validation(*args, **kwargs)
                
            # Perform actual validation
            self.current_count += 1
            return validator_fn(*args, **kwargs)
        
        return wrapper
        
    def fallback_validation(self, *args, **kwargs):
        """Fallback validation when throttled."""
        # Implement a simpler validation or queue the validation
        # For example, accept the data and validate asynchronously
        data = args[0] if args else kwargs.get('data')
        return data  # Just accept as-is for now, validate later

# Usage example
throttler = ValidationThrottler(max_validations_per_second=50)

@throttler.throttle
def validate_user(data):
    # Expensive validation
    return user_schema.validate(data)
```

## Conclusion

Integrating Sift with web frameworks provides powerful validation capabilities that can be tailored to your specific application needs. By following the patterns and practices outlined in this guide, you can:

1. **Ensure data integrity** through consistent validation across your application
2. **Improve user experience** with clear, helpful error messages
3. **Enhance performance** through caching and optimized validation strategies
4. **Maintain clean code** by separating validation logic from business logic
5. **Scale efficiently** with async validation and load-adaptive techniques

Each web framework has its unique integration points, but Sift's flexible design allows it to work seamlessly with any of them, whether you're using FastAPI, Flask, Django, Nexios, or another framework.

Remember that validation is not just about rejecting bad data – it's about creating a robust, secure, and user-friendly application that guides users toward proper usage while maintaining data integrity.

As you implement validation in your application, consider the following key takeaways:

- **Start simple**: Begin with basic validation and add complexity as needed
- **Think holistically**: Consider validation as part of your overall error handling strategy
- **Be strategic**: Use the appropriate validation level and techniques based on context
- **Optimize intelligently**: Apply performance techniques where they make the most impact
- **Provide clarity**: Make validation errors helpful for both users and developers

By thoughtfully integrating Sift into your framework of choice, you can build applications that are both robust and user-friendly, with validation that enhances rather than hinders the user experience.
