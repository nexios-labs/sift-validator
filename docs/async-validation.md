# Async Validation

This guide covers Voltar 's asynchronous validation capabilities, which are essential for high-performance applications and systems that need to validate data from asynchronous sources such as databases or external APIs.

## Asynchronous Validation Basics

### Why Use Async Validation?

Asynchronous validation is useful when:

- You need to validate against data from external sources (databases, APIs)
- You're working within an async framework (like FastAPI, asyncio, etc.)
- You want to leverage parallelism for better performance
- Your validation includes operations that are inherently asynchronous

### Basic Usage

All Voltar  validators support async validation through the `validate_async` method:

```python
import asyncio
from voltar  import Object, String, Number

# Define a schema
user_schema = Object({
    "username": String().min(3),
    "email": String().email(),
    "age": Number().int().min(18)
})

# Data to validate
user = {
    "username": "johndoe",
    "email": "john@example.com",
    "age": 25
}

# Async validation function
async def validate_user():
    validated_user = await user_schema.validate_async(user)
    print(validated_user)
    return validated_user

# Run the async validation
asyncio.run(validate_user())
```

### Converting Sync Validators to Async

By default, `validate_async` will call the synchronous `validate` method within an async context. However, you can implement custom async validation by overriding the `_validate_async` method:

```python
import asyncio
from voltar .validators.base import Validator, ValidationError
from typing import Any, List

class ExternalApiValidator(Validator[str, bool]):
    """A validator that checks data against an external API asynchronously."""
    
    async def _validate_async(self, data: Any, path: List[str]) -> bool:
        # First validate it's a string
        if not isinstance(data, str):
            raise ValidationError(
                self._get_error_message(f"Expected string, got {type(data).__name__}"),
                path
            )
        
        # Simulate an async API call
        await asyncio.sleep(0.1)  # In real code, this would be an API call
        
        # Simulate validation logic
        is_valid = len(data) >= 3  # Simple example
        
        if not is_valid:
            raise ValidationError(
                self._get_error_message("Invalid value"),
                path
            )
            
        return True

# Usage
async def validate_with_api():
    validator = ExternalApiValidator()
    result = await validator.validate_async("valid-value")
    print(result)  # True

asyncio.run(validate_with_api())
```

## Creating Custom Async Validators

### Basic Async Validator

Here's how to create a custom validator with async capabilities:

```python
import asyncio
from voltar .validators.base import Validator, ValidationError
from typing import Any, List

class AsyncEmailValidator(Validator[str, str]):
    """A validator that checks if an email exists by simulating an async API call."""
    
    def __init__(self):
        super().__init__()
        self._real_time_check = False
        self._validated_domains = set()  # For demonstration purposes
    
    def real_time_check(self) -> 'AsyncEmailValidator':
        """Enable real-time email verification via API."""
        validator = self.clone()
        validator._real_time_check = True
        return validator
    
    def _validate(self, data: Any, path: List[str]) -> str:
        """Regular synchronous validation."""
        if not isinstance(data, str):
            raise ValidationError(
                self._get_error_message(f"Expected string, got {type(data).__name__}"),
                path
            )
            
        # Basic email format check
        if "@" not in data or "." not in data.split("@")[1]:
            raise ValidationError(
                self._get_error_message("Invalid email format"),
                path
            )
            
        return data
    
    async def _validate_async(self, data: Any, path: List[str]) -> str:
        """Asynchronous validation with optional real-time checking."""
        # First do the regular validation
        data = self._validate(data, path)
        
        # If real-time checking is enabled, perform the async check
        if self._real_time_check:
            domain = data.split("@")[1]
            
            # Simulate async domain validation
            if domain not in self._validated_domains:
                # In a real implementation, this would check if the domain exists
                await asyncio.sleep(0.2)  # Simulate API call
                
                # Simulate validation result (reject example.invalid domain)
                if domain == "example.invalid":
                    raise ValidationError(
                        self._get_error_message("Email domain does not exist"),
                        path
                    )
                
                # Cache the validated domain
                self._validated_domains.add(domain)
        
        return data

# Usage
async def validate_emails():
    # Create the validator with real-time checking enabled
    email_validator = AsyncEmailValidator().real_time_check()
    
    # Valid email
    valid_email = await email_validator.validate_async("user@example.com")
    print(f"Valid email: {valid_email}")
    
    # Invalid format
    try:
        await email_validator.validate_async("not-an-email")
    except ValidationError as e:
        print(f"Invalid format error: {e}")
    
    # Invalid domain
    try:
        await email_validator.validate_async("user@example.invalid")
    except ValidationError as e:
        print(f"Invalid domain error: {e}")

asyncio.run(validate_emails())
```

### Async Database Validation

A common use case is validating data against a database:

```python
import asyncio
import aiomysql  # Example async database driver
from voltar .validators.base import Validator, ValidationError
from typing import Any, List

class UniqueUsernameValidator(Validator[str, str]):
    """Validates that a username is unique by checking an async database."""
    
    def __init__(self, pool):
        super().__init__()
        self.pool = pool  # Database connection pool
    
    def _validate(self, data: Any, path: List[str]) -> str:
        """Synchronous validation - only checks format."""
        if not isinstance(data, str):
            raise ValidationError(
                self._get_error_message(f"Expected string, got {type(data).__name__}"),
                path
            )
            
        if len(data) < 3:
            raise ValidationError(
                self._get_error_message("Username must be at least 3 characters"),
                path
            )
            
        return data
    
    async def _validate_async(self, data: Any, path: List[str]) -> str:
        """Asynchronous validation - checks database for uniqueness."""
        # First do the regular validation
        data = self._validate(data, path)
        
        # Check database for existing username
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE username = %s",
                    (data,)
                )
                result = await cursor.fetchone()
                count = result[0]
                
                if count > 0:
                    raise ValidationError(
                        self._get_error_message("Username already exists"),
                        path
                    )
        
        return data

# Example setup and usage (in a real app)
async def setup_and_validate():
    # Create a connection pool
    pool = await aiomysql.create_pool(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='password',
        db='testdb'
    )
    
    try:
        # Create the validator with the pool
        username_validator = UniqueUsernameValidator(pool)
        
        # Validate a username
        try:
            username = await username_validator.validate_async("johndoe")
            print(f"Username '{username}' is valid and unique")
        except ValidationError as e:
            print(f"Validation error: {e}")
    finally:
        # Close the pool
        pool.close()
        await pool.wait_closed()

# In a real application, you would call this from your async framework
# asyncio.run(setup_and_validate())
```

## Performance Optimization Techniques

### Parallel Validation

For independent fields, you can validate them in parallel:

```python
import asyncio
from voltar  import String, Number
from voltar .validators.base import ValidationError
from typing import Dict, Any

async def validate_fields_parallel(data: Dict[str, Any], validators: Dict[str, Any]):
    """Validate multiple fields in parallel."""
    tasks = []
    results = {}
    errors = []
    
    # Create a task for each field
    for field, validator in validators.items():
        if field in data:
            task = asyncio.create_task(
                validate_field(field, data[field], validator)
            )
            tasks.append(task)
    
    # Gather all tasks
    if tasks:
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for task_result in completed_tasks:
            if isinstance(task_result, tuple):
                field, value = task_result
                results[field] = value
            elif isinstance(task_result, Exception):
                errors.append(task_result)
    
    # If there were errors, raise the first one
    if errors:
        raise errors[0]
    
    return results

async def validate_field(field: str, value: Any, validator: Any):
    """Validate a single field and return the field name with validated value."""
    result = await validator.validate_async(value)
    return (field, result)

# Example usage
async def validate_user_parallel():
    user_data = {
        "username": "johndoe",
        "email": "john@example.com",
        "age": 25
    }
    
    validators = {
        "username": String().min(3),
        "email": String().email(),
        "age": Number().int().min(18)
    }
    
    try:
        results = await validate_fields_parallel(user_data, validators)
        print("Validation successful:", results)
    except ValidationError as e:
        print("Validation failed:", e)

asyncio.run(validate_user_parallel())
```

### Caching Validation Results

For expensive validations, consider caching results:

```python
import asyncio
import functools
from voltar .validators.base import Validator, ValidationError
from typing import Any, List, Dict, Optional

class CachedAsyncValidator(Validator):
    """A validator that caches async validation results."""
    
    def __init__(self, base_validator):
        super().__init__()
        self.base_validator = base_validator
        self._cache: Dict[Any, Any] = {}
    
    def _validate(self, data: Any, path: List[str]) -> Any:
        """Use the base validator for synchronous validation."""
        return self.base_validator.validate(data)
    
    async def _validate_async(self, data: Any, path: List[str]) -> Any:
        """Cached async validation."""
        # For simple types that can be hashed
        if isinstance(data, (str, int, float, bool, tuple)):
            # Check if result is in cache
            if data in self._cache:
                return self._cache[data]
            
            # Not in cache, validate and store result
            result = await self.base_validator.validate_async(data)
            self._cache[data] = result
            return result
        
        # For data that can't be cached (e.g., mutable types)
        return await self.base_validator.validate_async(data)

# Example usage
async def demonstrate_caching():
    from voltar  import String
    
    # Create an expensive validator (simulated)
    class ExpensiveValidator(String):
        async def _validate_async(self, data, path):
            # Simulate expensive validation
            print(f"Validating {data}...")
            await asyncio.sleep(1)  # Expensive operation
            return super()._validate(data, path)
    
    # Wrap it with caching
    expensive = ExpensiveValidator()
    cached = CachedAsyncValidator(expensive)
    
    # First validation - will be slow
    start = asyncio.get_event_loop().time()
    result1 = await cached.validate_async("test")
    duration1 = asyncio.get_event_loop().time() - start
    
    # Second validation with same input - should be fast (cached)
    start = asyncio.get_event_loop().time()
    result2 = await cached.validate_async("test")
    duration2 = asyncio.get_event_loop().time() - start
    
    print(f"First validation: {duration1:.3f}s")
    print(f"Second validation: {duration2:.3f}s")

asyncio.run(demonstrate_caching())
```

## Integration with Async Frameworks

### Integration with FastAPI

FastAPI is a popular async web framework that works well with Voltar 's async validation:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from voltar  import Object, String, Number
from voltar .validators.base import ValidationError

app = FastAPI()

# Define Voltar  validator
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

# FastAPI model for documentation
class UserModel(BaseModel):
    username: str
    email: str
    age: int

@app.post("/users/")
async def create_user(user: UserModel):
    try:
        # Convert Pydantic model to dict
        user_data = user.dict()
        
        # Validate with Voltar 
        validated_user = await user_schema.validate_async(user_data)
        
        # Process the validated user...
        # (e.g., save to database)
        
        return {"status": "success", "user": validated_user}
    except ValidationError as e:
        # Convert Voltar  validation error to FastAPI HTTP exception
        error_details = [{"field": ".".join(err.path), "message": err.message} for err in e.errors]
        raise HTTPException(status_code=422, detail=error_details)

# To run this:
# uvicorn app:app --reload
```

### Integration with Async Database (SQLAlchemy)

Using Voltar  with SQLAlchemy's async capabilities:

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String
from voltar  import Object, String, Number
from voltar .validators.base import ValidationError

# Define SQLAlchemy models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    age = Column(Integer)

# Define Voltar  validator
user_schema = Object({
    "username": String().min(3).max(50),
    "email": String().email(),
    "age": Number().int().min(18)
})

# Example function that validates and saves to database
async def create

