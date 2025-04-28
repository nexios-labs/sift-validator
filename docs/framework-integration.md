# Framework Integration

This guide demonstrates how to integrate Voltar validators with popular Python web frameworks for request validation, dependency injection, and API documentation.

## Nexios Integration

Nexios is a modern Python web framework with first-class support for Voltar validators. The integration provides built-in request validation, error handling, and automatic OpenAPI documentation generation.

### Basic Request Validation

```python
from nexios import get_application
from nexios.http import Request, Response
from voltar import Object, String, Number, ValidationError

app = get_application()

# Define your validation schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

@app.post("/users")
async def create_user(request: Request, response: Response):
    try:
        # Validate request data
        data = await request.json
        validated_data = await user_schema.validate_async(data)
        
        # Process validated data
        return response.json({
            "status": "success",
            "data": validated_data
        })
    except ValidationError as e:
        # Format validation errors
        error_details = [
            {"field": ".".join(err.path), "message": err.message}
            for err in e.errors
        ]
        return response.json({
            "status": "error",
            "code": "validation_error",
            "errors": error_details
        }, status=422)
    except Exception as e:
        return response.json({
            "status": "error",
            "code": "internal_error",
            "message": str(e)
        }, status=500)
```

### Validation Middleware

Create reusable validation middleware:

```python
from nexios import get_application
from nexios.decorators import catch_exceptions
from nexios.http import Request, Response
from voltar import Validator, ValidationError
from typing import Dict, Any

async def validate_request(request: Request,response: Response, exception: Exception):
    return response.json({
        "status": "error",
        "code": "internal_error",
        "message": e.errors
    }, status=422)

# Usage in routes
app = get_application()

user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email()
})

@app.post("/users")
@catch_exceptions(ValidationError,validate_request)
async def create_user(request: Request, validated_data: Dict[str, Any]):

    user_data = await request.json
    validated_data = await user_schema.validate_async(user_data)    
    return Response.json({
        "status": "success",
        "data": validated_data
    })
```

### Error Handling

Nexios provides built-in error handling for Voltar validation errors:

```python
from nexios import get_application
from nexios.http import Request, Response
from voltar import ValidationError

app = get_application()

@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request,resonse: Response, exc: ValidationError):
    """Global validation error handler."""
    return response.json({
        "status": "error",
        "code": "validation_error",
        "errors": [
            {
                "field": ".".join(err.path) if err.path else "_",
                "message": err.message,
                "code": "invalid_field"
            }
            for err in exc.errors
        ]
    }, status=422)
```


## FastAPI Integration

[FastAPI](https://fastapi.tiangolo.com/) is a modern, high-performance web framework for building APIs with Python. It features built-in validation powered by Pydantic, but you can also use Voltar's more powerful validation capabilities alongside or in place of Pydantic.

### Basic Request Validation

#### Using Dependencies

The most straightforward approach is to use FastAPI's dependency injection system with Voltar validators:

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from voltar import Object, String, Number
from typing import Dict, Any

app = FastAPI()

# Define your Voltar schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18).optional()
})

# Create a dependency that validates request data
async def validate_user_data(request: Request) -> Dict[str, Any]:
    try:
        data = await request.json()
        validated_data = await user_schema.validate_async(data)
        return validated_data
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

# Use the dependency in your endpoint
@app.post("/users/")
async def create_user(user_data: Dict[str, Any] = Depends(validate_user_data)):
    # Data is already validated by the dependency
    return {"status": "success", "data": user_data}
```

#### Validation Middleware

For more reusable validation, you can create a validation middleware function:

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from voltar import Validator, ValidationError, List
from typing import Callable, Dict, Any

app = FastAPI()

def validate_with(schema: Validator):
    """Create a dependency that validates request JSON data against a Voltar schema."""
    async def validate(request: Request) -> Dict[str, Any]:
        try:
            data = await request.json()
            validated_data = await schema.validate_async(data)
            return validated_data
        except ValidationError as e:
            # Format errors for better display
            error_details = [
                {"field": ".".join(err.path), "message": err.message} 
                for err in e.errors
            ]
            raise HTTPException(status_code=422, detail=error_details)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return Depends(validate)

# Define schemas
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18).optional()
})

post_schema = Object({
    "title": String().min(5).max(100),
    "content": String().min(10),
    "tags": List(String()).optional()
})

# Use in endpoints
@app.post("/users/")
async def create_user(data: Dict[str, Any] = validate_with(user_schema)):
    return {"status": "success", "data": data}

@app.post("/posts/")
async def create_post(data: Dict[str, Any] = validate_with(post_schema)):
    return {"status": "success", "data": data}
```

### Form Data Validation

For validating form data, you can use FastAPI's `Form` parameters with Voltar:

```python
from fastapi import FastAPI, Form, HTTPException
from voltar import Object, String

app = FastAPI()

# Define login schema
login_schema = Object({
    "username": String().min(3),
    "password": String().min(8)
})

@app.post("/login/")
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        # Validate form data using Voltar
        validated_data = login_schema.validate({
            "username": username,
            "password": password
        })
        
        # Process login
        return {"message": "Login successful"}
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

### Query Parameter Validation

You can validate query parameters using Voltar:

```python
from fastapi import FastAPI, Query, HTTPException
from voltar import Object, String, Number

app = FastAPI()

# Define search parameters schema
search_schema = Object({
    "q": String().min(1),
    "page": Number().int().min(1).default(1),
    "limit": Number().int().min(1).max(100).default(20)
})

@app.get("/search/")
async def search(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(20, description="Results per page")
):
    try:
        # Validate query parameters
        validated_params = search_schema.validate({
            "q": q,
            "page": page,
            "limit": limit
        })
        
        # Perform search with validated parameters
        results = [
            # ... search results
        ]
        
        return {
            "results": results,
            "pagination": {
                "page": validated_params["page"],
                "limit": validated_params["limit"],
                "total": 100  # Example total
            }
        }
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

### Path Parameter Validation

For validating path parameters:

```python
from fastapi import FastAPI, Path, HTTPException
from voltar import String, ValidationError

app = FastAPI()

# Create a validator for user IDs
user_id_validator = String().uuid()

@app.get("/users/{user_id}")
async def get_user(user_id: str = Path(..., description="User ID (UUID)")):
    try:
        # Validate the user ID
        validated_id = user_id_validator.validate(user_id)
        
        # Retrieve user with validated ID
        user = {
            "id": validated_id,
            "username": "johndoe",
            "email": "john@example.com"
        }
        
        return user
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

### Response Validation

You can also validate your API responses to ensure they meet your schema requirements:

```python
from fastapi import FastAPI, HTTPException
from voltar import Object, String, Number, List, ValidationError

app = FastAPI()

# Define user response schema
user_schema = Object({
    "id": Number().int(),
    "username": String(),
    "email": String().email(),
    "posts": List(
        Object({
            "id": Number().int(),
            "title": String(),
            "content": String()
        })
    ).default([])
})

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # Simulate retrieving user data
    user_data = {
        "id": user_id,
        "username": "johndoe",
        "email": "john@example.com",
        "posts": [
            {"id": 1, "title": "Hello World", "content": "My first post"}
        ]
    }
    
    try:
        # Validate the response data
        validated_data = user_schema.validate(user_data)
        return validated_data
    except ValidationError as e:
        # Log the error (this is a server-side issue)
        print(f"Response validation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Integration with OpenAPI Documentation

Voltar can help generate OpenAPI schemas for your FastAPI documentation:

```python
from fastapi import FastAPI, Depends
from voltar import Object, String, Number, List
from voltar.openapi import generate_openapi_schema
from typing import Dict, Any

app = FastAPI()

# Define Voltar schema
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18).optional()
})

# Generate OpenAPI schema
user_openapi_schema = generate_openapi_schema(user_schema)

# Define a model for documentation
class UserModel:
    # This will be used only for documentation
    openapi_schema = user_openapi_schema
    
    @classmethod
    def __get_validators__(cls):
        # This is needed for FastAPI to recognize it as a valid type
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        return v

# Use in endpoint
@app.post("/users/", response_model=UserModel)
async def create_user(data: Dict[str, Any] = Depends(validate_with(user_schema))):
    return data
```

### Advanced Techniques

#### Combining with Pydantic

You can use both Voltar and Pydantic together:

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from voltar import Object, String, Number, ValidationError
from typing import Dict, Any, Optional

app = FastAPI()

# Define a Voltar validator for deep validation
email_validator = String().email().pattern(r".*@(gmail|outlook|yahoo)\.com$")

# Define Pydantic model with Voltar validation
class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    age: Optional[int] = Field(None, ge=18)
    
    # Add custom validator using Voltar
    @validator('email')
    def validate_email(cls, v):
        try:
            return email_validator.validate(v)
        except ValidationError as e:
            raise ValueError(str(e))

@app.post("/users/")
async def create_user(user: User):
    # Both Pydantic and Voltar validations are applied
    return user
```

#### Custom Error Handler

Create a custom exception handler for Voltar validation errors:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from voltar import ValidationError

app = FastAPI()

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "loc": err.path,
                    "msg": err.message,
                    "type": "validation_error"
                } 
                for err in exc.errors
            ]
        }
    )
```

#### Async Validators for Database Checks

You can create custom async validators that interact with your database:

```python
from fastapi import FastAPI, Depends
from voltar import Object, String, ValidationError
from voltar.validators.base import Validator
from typing import Any, List as TypedList, Dict

app = FastAPI()

# Example database dependency
async def get_db():
    # In a real app, this would be a database connection
    return {"users": {"johndoe": {"username": "johndoe", "email": "john@example.com"}}}

class UniqueUsernameValidator(String):
    """Validator that ensures a username is unique."""
    
    async def _validate_async(self, data: Any, path: TypedList[str]) -> str:
        # First validate as a string
        username = await super()._validate_async(data, path)
        
        # Check if username exists in database
        db = await get_db()
        if username in db["users"]:
            raise ValidationError(f"Username '{username}' is already taken", path)
            
        return username

# Use in schema
registration_schema = Object({
    "username": UniqueUsernameValidator().min(3).max(50),
    "password": String().min(8),
    "email": String().email()
})

@app.post("/register/")
async def register(data: Dict[str, Any] = Depends(validate_with(registration_schema))):
    # Username uniqueness already validated
    return {"status": "success", "data": {"username": data["username"]}}
```

### Best Practices

#### 1. Organize Validators in a Central Location

```python
# validators.py
from voltar import Object, String, Number, List

class Schemas:
    """Central repository for all application schemas."""
    
    # User-related schemas
    user = Object({
        "username": String().min(3).max(50),
        "email": String().email(),
        "age": Number().int().min(18).optional()
    })
    
    user_update = Object({
        "username": String().min(3).max(50).optional(),
        "email": String().email().optional(),
        "age": Number().int().min(18).optional()
    })
    
    # Post-related schemas
    post = Object({
        "title": String().min(5).max(100),
        "content": String().min(10),
        "tags": List(String()).optional()
    })

# routes.py
from .validators import Schemas

@app.post("/users/")
async def create_user(data: Dict[str, Any] = validate_with(Schemas.user)):
    return {"status": "success", "data": data}
```

#### 2. Create Reusable Validation Components

```python
# components.py
from voltar import Object, String, Number

# Basic components
address = Object({
    "street": String(),
    "city": String(),
    "country": String().length(2).uppercase()  # ISO country code
})

contact = Object({
    "email": String().email(),
    "phone": String().pattern(r"^\+[0-9]{1,3}\s[0-9]{4,14}$").optional()
})

# validators.py
from .components import address, contact
from voltar import Object, String

user_profile = Object({
    "name": String(),
    "address": address,
    "contact": contact
})
```

#### 3. Consistent Error Handling

Create unified error handling for all validation errors:

```python
# errors.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from voltar import ValidationError

async def validation_exception_handler(request: Request, exc: ValidationError):
    """Convert Voltar validation errors to a consistent API response format."""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": "validation_error",
            "message": "Input validation failed",
            "errors": [
                {
                    "field": ".".join(err.path) if err.path else "_",
                    "message": err.message,
                    "code": "invalid_field"
                } 
                for err in exc.errors
            ]
        }
    )

# main.py
from fastapi import FastAPI
from voltar import ValidationError
from .errors import validation_exception_handler

app = FastAPI()
app.add_exception_handler(ValidationError, validation_exception_handler)
```

#### 4. Schema Versioning

For API versioning, maintain separate schema versions:

```python
# schemas/v1/users.py
from voltar import Object, String, Number

user_v1 = Object({
    "username": String().min(3),
    "email": String().email()
})

# schemas/v2/users.py
from voltar import Object, String, Number
from ..v1.users import user_v1

user_v2 = user_v1.extend({
    "profile_url": String().url().optional(),
    "preferences": Object({
        "theme": String().pattern(r"^(light|dark)$").default("light"),
        "notifications": Boolean().default(True)
    }).optional()
})
```
