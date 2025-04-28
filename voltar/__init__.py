"""
Voltar : A Python validation library with Zod-like syntax and async support.

This module provides a chainable API for data validation with both
synchronous and asynchronous support, comprehensive type hints,
and OpenAPI schema generation capabilities.
"""

__version__ = "0.1.0"

# Import commonly used validators for convenient access
from voltar .validators.base import Validator, ValidationError
from voltar .validators.primitives import String, Number, Boolean, Any, Null
from voltar .validators.collections import List, Dict, Tuple,Union
from voltar .validators.objects import Object


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
    "ValidationError"
]

