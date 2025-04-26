"""
Sift: A Python validation library with Zod-like syntax and async support.

This module provides a chainable API for data validation with both
synchronous and asynchronous support, comprehensive type hints,
and OpenAPI schema generation capabilities.
"""

__version__ = "0.1.0"

# Import commonly used validators for convenient access
from sift.validators.base import Validator
from sift.validators.primitives import String, Number, Boolean, Any, Null
from sift.validators.collections import List, Dict, Tuple,Union
from sift.validators.objects import Object


__all__ = [
    "Validator",
    "String",
    "Number",
    "Boolean",
    "Any", 
    "Null",
    "List",
    "Dict", 
    "Tuple",
    "Object",
    "Union",
]

