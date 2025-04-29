"""
Base validator classes and interfaces.

This module defines the foundational Validator abstract base class
and related interfaces that all validators implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Optional, Type, TypeVar, cast, overload
import inspect
import asyncio
from datetime import datetime
from enum import Enum

# Type variable for generic validator
T = TypeVar("T")
R = TypeVar("R")

class ValidationError(ValueError):
    """Error raised when validation fails.
    
    This class supports both simple error messages with paths and 
    dictionary-style error handling with field-error pairs.
    """
    
    def __init__(self, message: Optional[str] = None, path: Optional[list[str | int]] = None, errors: Optional[dict[str, str]] = None):
        self.errors: dict[str, str] = errors or {}
        self.path = path or []
        
        # For backwards compatibility
        self.message = message or ""
        
        # If message and path are provided, add them to the errors dict
        if message:
            field = ".".join(str(p) for p in self.path) if self.path else "_base"
            self.errors[field] = message
        
        # Format the error message for the ValueError constructor
        super().__init__(self._format_error_message())
    
    def _format_error_message(self) -> str:
        """Format the errors dictionary into a readable error message."""
        if not self.errors:
            return "Validation failed"
            
        return "\n".join(f"{field}: {message}" for field, message in self.errors.items())
    
    def add_error(self, field: str, message: str) -> None:
        """Add a new field error."""
        self.errors[field] = message
        
    def merge(self, other: 'ValidationError') -> None:
        """Merge another ValidationError's errors into this one."""
        self.errors.update(other.errors)
        
    @property
    def error_dict(self) -> dict[str, str]:
        """Get the errors as a dictionary."""
        return self.errors.copy()

class Validator(Generic[T, R]):
    """
    Base validator class that all validators inherit from.
    
    This abstract class defines the core validation interface and
    provides common functionality for all validator types.
    """
    
    def __init__(self):
        self._optional: bool = False
        self._nullable: bool = False
        self._default: Optional[T | Callable[[], T]] = None
        self._custom_error_message: Optional[str] = None
        
    @property
    def _is_nullable(self) -> bool:
        """
        Property that can be overridden by subclasses to declare themselves as nullable.
        By default, this returns False. The Null validator can override this to return True.
        """
        return False
        
    def optional(self) -> "Validator[T, R | None]":
        """Make this field optional (undefined values pass validation)."""
        validator = self._clone()
        validator._optional = True
        return validator
        
    def nullable(self) -> "Validator[T, R | None]":
        """Make this field nullable (null values pass validation)."""
        validator = self._clone()
        validator._nullable = True
        return validator
    
    def default(self, value: T | Callable[[], T]) -> "Validator[T, R]":
        """Set a default value to use when the input is undefined."""
        validator = self._clone()
        validator._default = value
        self.optional()
        
        return validator
    
    def error(self, message: str) -> "Validator[T, R]":
        """Set a custom error message for this validator."""
        validator = self._clone()
        validator._custom_error_message = message
        return validator
        
    def _clone(self) -> "Validator[T, R]":
        """Create a copy of this validator with the same configuration."""
        validator = self.__class__.__new__(self.__class__)
        validator.__dict__ = self.__dict__.copy()
        return validator
    
    def _get_error_message(self, default_message: str) -> str:
        """Get the error message, using custom message if available."""
        return self._custom_error_message or default_message
        
    def _wrap_error(self, error: ValidationError) -> ValidationError:
        """
        Wrap a validation error with a custom error message if one is provided.
        """
        if self._custom_error_message is None:
            return error
        
        # Create a new error with the custom message but preserve the path
        if error.errors and len(error.errors) > 1:
            # If there are multiple errors, wrap them all with the custom message
            all_errors = {k: self._custom_error_message for k in error.errors.keys()}
            return ValidationError(errors=all_errors)
        else:
            # For single error or simple case, use the traditional approach
            return ValidationError(self._custom_error_message, error.path)
    
    def _resolve_default(self) -> T:
        """Resolve the default value, handling callable defaults."""
        if self._default is None:
            raise ValidationError("No default value provided for undefined input")
        
        if callable(self._default) and not isinstance(self._default, type):
            return self._default()
        return cast(T, self._default)
    
    @abstractmethod
    def _validate(self, data: Any, path: list[str | int]) -> R:
        """
        Internal validation method to be implemented by subclasses.
        
        Args:
            data: The data to validate
            path: The current path in the data structure for error reporting
            
        Returns:
            The validated (and possibly transformed) data
            
        Raises:
            ValidationError: If validation fails
        """
        pass
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> R:
        """
        Asynchronous validation method with default implementation.
        
        By default, this calls the synchronous _validate method. Subclasses
        can override this to provide custom async validation logic.
        
        Args:
            data: The data to validate
            path: The current path in the data structure for error reporting
            
        Returns:
            The validated (and possibly transformed) data
            
        Raises:
            ValidationError: If validation fails
        """
        # By default, run the synchronous validation in the event loop
        return self._validate(data, path)
    
    def validate(self, data: Any) -> R:
        """
        Validate data synchronously.
        
        Args:
            data: The data to validate
            
        Returns:
            The validated (and possibly transformed) data
            
        Raises:
            ValidationError: If validation fails
        """
        # Handle undefined/null values
        if data is None:
            # Check for default value first
            if self._default is not None:
                return cast(R, self._resolve_default())
            
            # Then check if nullable (either explicitly set or by the class)
            if self._nullable or self._is_nullable:
                return cast(R, None)
            
            # Then check if optional
            if self._optional:
                return cast(R, None)
            
            # Not default, nullable, or optional, so it's an error
            raise ValidationError(self._get_error_message("Value is required"))
            
        # Perform actual validation
        try:
            return self._validate(data, [])
        except ValidationError as e:
            # Wrap the error with custom message if provided
            raise self._wrap_error(e)
        
    async def validate_async(self, data: Any) -> R:
        """
        Validate data asynchronously.
        
        Args:
            data: The data to validate
            
        Returns:
            The validated (and possibly transformed) data
            
        Raises:
            ValidationError: If validation fails
        """
        # Handle undefined/null values
        if data is None:
            # Check for default value first
            if self._default is not None:
                default_value = self._resolve_default()
                return cast(R, default_value)
            
            # Then check if nullable (either explicitly set or by the class)
            if self._nullable or self._is_nullable:
                return cast(R, None)
            
            # Then check if optional
            if self._optional:
                return cast(R, None)
                
            # Not default, nullable, or optional, so it's an error
            raise ValidationError(self._get_error_message("Value is required"))
            
        # Perform actual validation
        try:
            return await self._validate_async(data, [])
        except ValidationError as e:
            # Wrap the error with custom message if provided
            raise self._wrap_error(e)

