# Integration Guide

This guide covers how to integrate Voltar  into your applications, focusing on web frameworks and deployment considerations.

## Integration with Web Frameworks

Voltar  is designed to work seamlessly with all popular Python web frameworks. Here are integration examples for the most common ones.

### FastAPI

FastAPI has excellent support for validation libraries, and Voltar  integrates particularly well with it:

```python
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any

from voltar  import Object, String, Number, Boolean, List
from voltar .validators.base import ValidationError

app = FastAPI()

# Define your validation schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_active": Boolean().default(True),
    "tags": List(String()).optional()
})

# Helper function to validate request data with Voltar 
async def validate_user_data(request: Request):
    try:
        # Get JSON data from request
        json_data = await request.json()
        
        # Validate with Voltar 
        validated_data = await user_schema.validate_async(json_data)
        return validated_data
    except ValidationError as e:
        # Format validation errors
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        raise HTTPException(status_code=422, detail={"errors": error_details})
    except Exception as e:
        # Handle other errors like invalid JSON
        raise HTTPException(status_code=400, detail={"error": "Invalid request data"})

# Endpoint that uses Voltar  validation
@app.post("/users/")
async def create_user(user_data: Dict[str, Any] = Depends(validate_user_data)):
    # At this point, user_data is already validated
    # Proceed with business logic (e.g., save to database)
    return {"status": "success", "data": user_data}

# Global exception handler for Voltar  validation errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    error_details = [{"field": ".".join(err.path), "message": err.message} for err in exc.errors]
    return JSONResponse(
        status_code=422,
        content={"errors": error_details}
    )
```

### Flask

For Flask applications, you can integrate Voltar  at various levels:

```python
from flask import Flask, request, jsonify
from voltar  import Object, String, Number
from voltar .validators.base import ValidationError

app = Flask(__name__)

# Define your validation schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

# Basic route with manual validation
@app.route("/users", methods=["POST"])
def create_user():
    try:
        # Get JSON data
        data = request.get_json()
        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400
            
        # Validate with Voltar 
        validated_data = user_schema.validate(data)
        
        # Process the validated data
        # (e.g., save to database)
        
        return jsonify({"status": "success", "data": validated_data})
    except ValidationError as e:
        # Format and return validation errors
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        return jsonify({"errors": error_details}), 422
    except Exception as e:
        # Handle other errors
        return jsonify({"error": str(e)}), 500

# More advanced: Create a validator decorator
def validate_with(schema):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "Invalid JSON"}), 400
                    
                validated_data = schema.validate(data)
                return f(validated_data=validated_data, *args, **kwargs)
            except ValidationError as e:
                error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
                return jsonify({"errors": error_details}), 422
        return decorated_function
    return decorator

# Usage with decorator
@app.route("/products", methods=["POST"])
@validate_with(Object({
    "name": String().min(1),
    "price": Number().min(0),
    "in_stock": Boolean().default(True)
}))
def create_product(validated_data):
    # Process the validated data
    return jsonify({"status": "success", "data": validated_data})
```

### Django

Integrating Voltar  with Django, especially for REST APIs:

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from voltar  import Object, String, Number, Boolean
from voltar .validators.base import ValidationError

# Define your validation schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_active": Boolean().default(True)
})

# Basic view with manual validation
@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
            
        # Validate with Voltar 
        validated_data = user_schema.validate(data)
        
        # Process the validated data
        # (e.g., save to database)
        
        return JsonResponse({"status": "success", "data": validated_data})
    except ValidationError as e:
        # Format and return validation errors
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        return JsonResponse({"errors": error_details}, status=422)
    except Exception as e:
        # Handle other errors
        return JsonResponse({"error": str(e)}, status=500)

# For Django Rest Framework
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def create_user_drf(request):
    try:
        # Validate with Voltar 
        validated_data = user_schema.validate(request.data)
        
        # Process the validated data
        # (e.g., save to database)
        
        return Response({"status": "success", "data": validated_data})
    except ValidationError as e:
        # Format and return validation errors
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        return Response({"errors": error_details}, status=422)
```

### Starlette

For Starlette, which is also the foundation of FastAPI:

```python
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import json

from voltar  import Object, String, Number
from voltar .validators.base import ValidationError

# Define your validation schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

async def create_user(request):
    try:
        # Parse JSON data
        data = await request.json()
        
        # Validate with Voltar 
        validated_data = await user_schema.validate_async(data)
        
        # Process the validated data
        # (e.g., save to database)
        
        return JSONResponse({"status": "success", "data": validated_data})
    except ValidationError as e:
        # Format and return validation errors
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        return JSONResponse({"errors": error_details}, status=422)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        # Handle other errors
        return JSONResponse({"error": str(e)}, status=500)

# Define routes
routes = [
    Route('/users', create_user, methods=['POST']),
]

# Create app
app = Starlette(routes=routes)
```

### Nexios

Nexios, developed by the same team as Voltar , has first-class support for Voltar  validators:

```python
from nexios import get_application
from nexios.http import Request, Response
from voltar  import Object, String, Number, Boolean

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
    try:
        # Get JSON data
        data = await request.json
        
        # Validate with Voltar 
        validated_data = await user_schema.validate_async(data)
        
        # Process the validated data
        # (e.g., save to database)
        
        return response.json({"status": "success", "data": validated_data})
    except Exception as e:
        return response.json({"status": "error", "message": str(e)}, status=422)
```

## Best Practices for Deployment

### Separation of Concerns

Structure your validation schemas separately from your route handlers:

```python
# schemas.py
from voltar  import Object, String, Number, Boolean, List

# User-related schemas
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18),
    "is_active": Boolean().default(True)
})

user_update_schema = Object({
    "username": String().min(3).max(50).optional(),
    "email": String().email().optional(),
    "age": Number().int().min(18).optional(),
    "is_active": Boolean().optional()
})

# Product-related schemas
product_schema = Object({
    "name": String().min(1),
    "price": Number().min(0),
    "categories": List(String()).optional()
})

# routes.py
from .schemas import user_schema, user_update_schema, product_schema

# ... your route handlers
```

### Consistent Error Handling

Implement a consistent approach to handling validation errors:

```python
# utils.py
from voltar .validators.base import ValidationError

def format_validation_error(error: ValidationError):
    """Format a validation error into a standardized response format."""
    errors = []
    for err in error.errors:
        path = ".".join(err.path) if err.path else "input"
        errors.append({
            "field": path,
            "message": err.message,
            "code": "validation_error"
        })
    
    return {
        "status": "error",
        "code": "validation_failed",
        "message": "The provided data failed validation.",
        "errors": errors
    }

# In your route handlers
try:
    validated_data = schema.validate(data)
    # ...
except ValidationError as e:
    return format_validation_error(e), 422
```

### Environment-specific Validation

Adjust validation rules based on the environment:

```python
import os
from voltar  import Object, String, List

# Default strict validation for production
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "tags": List(String()).max(5)
})

# In development or testing, optionally relax some constraints
if os.environ.get("ENVIRONMENT") in ("development", "testing"):
    user_schema = Object({
        "username": String().min(1).max(50),  # More lenient
        "email": String(),  # Any string is fine
        "tags": List(String()).max(20)  # Allow more tags
    })
```

## Error Handling and Validation Strategies

### Graceful Degradation

For non-critical validations, consider using default values instead of rejecting the request:

```python
from voltar  import Object, String, Number, List

# Instead of strict validation that might fail
product_schema = Object({
    "name": String().min(1),
    "price": Number().min(0),
    "discount": Number().min(0).max(100),
    "categories": List(String()).nonempty()
})

# More forgiving version that provides defaults
forgiving_schema = Object({
    "name": String().min(1),  # Still require a name
    "price": Number().min(0).default(0),  # Default to free
    "discount": Number().min(0).max(100).default(0),  # Default to no discount
    "categories": List(String()).default(["uncategorized"])  # Default category
})
```

### Validation Tiers

Implement different levels of validation based on the use case:

```python
from voltar  import Object, String, Number

# Basic fast validation for list endpoints
user_list_schema = Object({
    "page": Number().int().min(1).default(1),
    "per_page": Number().int().min(1).max(100).default(20)
})

# More thorough validation for creation
user_create_schema = Object({
    "username": String().min(3).max(50).pattern(r"^[a-zA-Z0-9_]+$"),
    "email": String().email(),
    "password": String().min(8).pattern(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$"),
    "age": Number().int().min(18)
})

# Minimal validation for search
user_search_schema = Object({
    "q": String().optional(),
    "filter": String().optional()
})
```

### Contextual Validation

Pass additional context to validators when needed:

```python
from voltar .validators.base import Validator, ValidationError
from typing import Any, Dict, List

class ContextualValidator(Validator):
    def __init__(self, context_key=None):
        super().__init__()
        self.context_key = context_key
    
    def _validate(self, data: Any, path: List[str], context: Dict[str, Any] = None) -> Any:
        if context is None or self.context_key not in context:
            return data
            
        # Use context for validation
        context_value = context[self.context_key]
        # ... validation logic using context_value
        
        return data

# Usage
from voltar  import Object, String

user_schema = Object({
    "username": String().min(3),
    "role": ContextualValidator(context_key="allowed_roles")
})

# When validating
try:
    context = {"allowed_roles": ["admin", "editor", "viewer"]}
    validated_data = user_schema.validate(data, context=context)
except ValidationError as e:
    # Handle validation error
```

## Performance Optimization Tips

### Schema Reuse

Define schemas once and reuse them to avoid overhead:

```

