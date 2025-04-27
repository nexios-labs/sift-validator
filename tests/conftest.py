"""
Pytest configuration and fixtures for testing the Voltar  library.
"""

import sys
import os
import pytest
import asyncio
from pathlib import Path

# Add the parent directory to the Python path to import voltar 
sys.path.insert(0, str(Path(__file__).parent.parent))

from voltar  import String, Number, Boolean, Object, List, Dict, Union, Any, Null
from voltar .validators.base import Validator, ValidationError
from voltar .validators.collections import Tuple


#
# Basic Validator Fixtures
#

@pytest.fixture
def string_validator():
    """Return a basic string validator."""
    return String()


@pytest.fixture
def number_validator():
    """Return a basic number validator."""
    return Number()


@pytest.fixture
def boolean_validator():
    """Return a basic boolean validator."""
    return Boolean()


@pytest.fixture
def any_validator():
    """Return a basic any validator."""
    return Any()


@pytest.fixture
def null_validator():
    """Return a basic null validator."""
    return Null()


@pytest.fixture
def list_validator():
    """Return a basic list validator for strings."""
    return List(String())


@pytest.fixture
def dict_validator():
    """Return a basic dict validator."""
    return Dict({
        "name": String(),
        "age": Number().int()
    })


@pytest.fixture
def tuple_validator():
    """Return a basic tuple validator."""
    return Tuple([String(), Number(), Boolean()])


@pytest.fixture
def union_validator():
    """Return a basic union validator."""
    return Union([String(), Number()])


#
# Complex Schema Fixtures
#

@pytest.fixture
def user_schema():
    """Return a complex user schema."""
    return Object({
        "id": Number().int(),
        "username": String().min(3).max(20).pattern(r"^[a-zA-Z0-9_]+$"),
        "email": String().email(),
        "profile": Object({
            "fullName": String().min(1),
            "age": Number().int().min(18).optional(),
            "bio": String().max(500).optional()
        }).optional(),
        "tags": List(String()).optional(),
        "settings": Dict().pattern_property(r"^setting_", Any()).optional()
    })


@pytest.fixture
def product_schema():
    """Return a complex product schema with variants."""
    return Object({
        "id": String().pattern(r"^[A-Z0-9]{10}$"),
        "name": String().min(1).max(100),
        "price": Number().positive(),
        "category": Union([
            String(),
            List(String())
        ]),
        "variants": List(Object({
            "id": String(),
            "name": String().min(1),
            "price": Number().positive().optional()
        })).optional()
    })


@pytest.fixture
def pet_schema():
    """Return a schema with discriminator."""
    dog_schema = Object({
        "type": String().default("dog"),
        "name": String().min(1),
        "breed": String().min(1)
    })
    
    cat_schema = Object({
        "type": String().default("cat"),
        "name": String().min(1),
        "lives": Number().int().min(1).max(9)
    })
    
    return Union(
        [dog_schema, cat_schema],
        discriminator="type"
    ).discriminator_mapping({
        "dog": dog_schema,
        "cat": cat_schema
    })


#
# Test Data Fixtures
#

@pytest.fixture
def valid_user_data():
    """Return valid user data."""
    return {
        "id": 123,
        "username": "testuser",
        "email": "user@example.com",
        "profile": {
            "fullName": "Test User",
            "age": 25,
            "bio": "A test user for validation"
        },
        "tags": ["test", "user", "validation"],
        "settings": {
            "setting_theme": "dark",
            "setting_notifications": True
        }
    }


@pytest.fixture
def valid_product_data():
    """Return valid product data."""
    return {
        "id": "PROD1234567",
        "name": "Test Product",
        "price": 99.99,
        "category": ["electronics", "gadgets"],
        "variants": [
            {
                "id": "V1",
                "name": "Standard",
                "price": 99.99
            },
            {
                "id": "V2",
                "name": "Premium",
                "price": 149.99
            }
        ]
    }


@pytest.fixture
def valid_pet_data():
    """Return valid pet data for both types."""
    return {
        "dog": {
            "type": "dog",
            "name": "Buddy",
            "breed": "Golden Retriever"
        },
        "cat": {
            "type": "cat",
            "name": "Whiskers",
            "lives": 9
        }
    }


#
# Async Testing Utilities
#

@pytest.fixture
def delayed_validator():
    """Return a validator with deliberate delay for testing async."""
    class DelayedValidator(Validator):
        def __init__(self, delay=0.1):
            super().__init__()
            self._delay = delay
            
        async def _validate_async(self, data, path):
            await asyncio.sleep(self._delay)
            return data
            
    return DelayedValidator


@pytest.fixture
def async_error_validator():
    """Return a validator that always raises an error asynchronously."""
    class AsyncErrorValidator(Validator):
        async def _validate_async(self, data, path):
            await asyncio.sleep(0.1)
            raise ValidationError("Async validation failed", path)
            
    return AsyncErrorValidator

    """Return a basic boolean validator."""
    return Boolean()


@pytest.fixture
def any_validator():
    """Return a basic any validator."""
    return Any()


@pytest.fixture
def null_validator():
    """Return a basic null validator."""
    return Null()


@pytest.fixture
def list_validator():
    """Return a basic list validator."""
    return List(String())


@pytest.fixture
def dict_validator():
    """Return a basic dict validator."""
    return Dict({
        "name": String(),
        "age": Number().int()
    })


@pytest.fixture
def tuple_validator():
    """Return a basic tuple validator."""
    return Tuple([String(), Number(), Boolean()])


@pytest.fixture
def union_validator():
    """Return a basic union validator."""
    return Union([String(), Number()])


@pytest.fixture
def complex_object_validator():
    """Return a complex object validator for testing nested validation."""
    return Object({
        "id": Number().int(),
        "name": String().min(1),
        "tags": List(String()).optional(),
        "metadata": Dict().optional()
    })

