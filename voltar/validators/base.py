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

class Symbol:
    """
    A unique symbol for identifying validator attributes.
    
    Symbols can be used as unique identifiers for validation
    operations, error codes, or other metadata.
    """
    
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self) -> str:
        return f"Symbol({self.name})"
    
    def __str__(self) -> str:
        return self.name

# Define common error codes as symbols
ERROR_CODES = {
    "invalid_type": Symbol("invalid_type"),
    "invalid_value": Symbol("invalid_value"),
    "required": Symbol("required"),
    "too_small": Symbol("too_small"),
    "too_big": Symbol("too_big"),
    "invalid_format": Symbol("invalid_format"),
    "custom": Symbol("custom"),
    "invalid_enum_value": Symbol("invalid_enum_value"),
    "unrecognized_keys": Symbol("unrecognized_keys"),
    "invalid_union": Symbol("invalid_union")
}

class ValidationIssue:
    """
    Structured representation of a single validation issue.
    
    This class provides detailed information about a validation
    failure, including the path, error code, expected type,
    and custom message.
    """
    
    def __init__(
        self,
        code: str,
        path: list[str | int],
        message: str,
        expected: Optional[str] = None,
        received: Optional[str] = None,
        keys: Optional[list[str]] = None,
        **kwargs
    ):
        """
        Initialize a validation issue with detailed information.
        
        Args:
            code: Error code identifier
            path: Path to the field that failed validation
            message: Human-readable error message
            expected: Expected type or value
            received: Actual received type or value
            keys: For unrecognized_keys errors, the names of the invalid keys
            **kwargs: Additional context specific to the error
        """
        self.code = code
        self.path = path.copy() if path else []
        self.message = message
        self.expected = expected
        self.received = received
        self.keys = keys
        self.context = kwargs
    
    def to_dict(self) -> dict:
        """Convert the issue to a dictionary representation."""
        result = {
            "code": self.code,
            "path": self.path,
            "message": self.message
        }
        
        if self.expected is not None:
            result["expected"] = self.expected
        
        if self.received is not None:
            result["received"] = self.received
            
        if self.keys is not None:
            result["keys"] = self.keys
            
        if self.context:
            result.update(self.context)
            
        return result

class ValidationError(ValueError):
    """Error raised when validation fails.
    
    This class supports both simple error messages with paths and 
    dictionary-style error handling with field-error pairs.
    
    It also supports detailed error descriptions and better formatting
    for nested field validation errors.
    """
    
    def __init__(self, 
                 message: Optional[str] = None, 
                 path: Optional[list[str | int]] = None, 
                 errors: Optional[dict[str, str | dict]] = None,
                 description: Optional[str] = None,
                 code: Optional[str] = None,
                 expected: Optional[str] = None,
                 received: Optional[str] = None,
                 issues: Optional[list[ValidationIssue]] = None):
        """
        Initialize a ValidationError with detailed error information.
        
        Args:
            message: The error message
            path: The path to the field with the error
            errors: A dictionary of field-error pairs
            description: A detailed description of the error
            code: Error code identifier
            expected: Expected type or value
            received: Actual received type or value
            issues: List of structured validation issues
        """
        self.errors: dict[str, dict] = {}
        self.path = path or []
        
        # For backwards compatibility
        self.message = message or ""
        self.description = description
        self.code = code or ERROR_CODES["custom"].name
        self.expected = expected
        self.received = received
        
        # Initialize issues list
        self._issues: list[ValidationIssue] = issues or []
        
        # If errors dict is provided, use it
        if errors:
            # Handle both simple string errors and dict errors
            for field, content in errors.items():
                if isinstance(content, str):
                    self.errors[field] = {"message": content}
                    if description:
                        self.errors[field]["description"] = description
                    
                    # Create a ValidationIssue for this error
                    field_path = self._parse_field_to_path(field)
                    self._issues.append(ValidationIssue(
                        code=code or ERROR_CODES["custom"].name,
                        path=field_path,
                        message=content,
                        expected=expected,
                        received=received
                    ))
                else:
                    # Already a dictionary, use as is
                    self.errors[field] = content
                    
                    # Create a ValidationIssue if one doesn't already exist
                    if self._issues:
                        continue
                        
                    field_path = self._parse_field_to_path(field)
                    issue_code = content.get("code", code or ERROR_CODES["custom"].name)
                    issue_msg = content.get("message", "Validation failed")
                    
                    self._issues.append(ValidationIssue(
                        code=issue_code,
                        path=field_path,
                        message=issue_msg,
                        expected=content.get("expected", expected),
                        received=content.get("received", received)
                    ))
        
        # If message and path are provided but no issues, add them to the errors dict and create an issue
        if message and not self._issues:
            field = self._format_path(self.path) if self.path else "_base"
            self.errors[field] = {"message": message}
            if description:
                self.errors[field]["description"] = description
            if code:
                self.errors[field]["code"] = code
            if expected:
                self.errors[field]["expected"] = expected
            if received:
                self.errors[field]["received"] = received
                
            # Add as a validation issue
            self._issues.append(ValidationIssue(
                code=code or ERROR_CODES["custom"].name,
                path=self.path,
                message=message,
                expected=expected,
                received=received
            ))
        
        # Format the error message for the ValueError constructor
        super().__init__(self._format_error_message())
    
    def _parse_field_to_path(self, field: str) -> list[str | int]:
        """Convert a field string like 'root.nested[0]' to a path list."""
        if field == "_base":
            return []
            
        # Handle the new arrow format
        if " → " in field:
            parts = []
            for part in field.split(" → "):
                if part.startswith("[") and part.endswith("]"):
                    # Convert "[0]" to integer 0
                    parts.append(int(part[1:-1]))
                else:
                    parts.append(part)
            return parts
            
        # Legacy dot notation for backward compatibility
        result = []
        for part in field.split("."):
            if "[" in part and "]" in part:
                # Handle array indices like "items[0]"
                base = part.split("[")[0]
                if base:
                    result.append(base)
                indices = part.split("[")[1:]
                for idx in indices:
                    if "]" in idx:
                        idx_value = idx.split("]")[0]
                        try:
                            result.append(int(idx_value))
                        except ValueError:
                            result.append(idx_value)
            else:
                result.append(part)
        return result
    
    def _format_path(self, path: list[str | int]) -> str:
        """Format a path into a readable string representation.
        
        Args:
            path: The path to format
            
        Returns:
            A string representation of the path
        """
        if not path:
            return "_base"
        
        formatted_parts = []
        for part in path:
            if isinstance(part, int):
                formatted_parts.append(f"[{part}]")
            else:
                if formatted_parts:
                    formatted_parts.append(part)
                else:
                    # First element doesn't need a separator
                    formatted_parts.append(str(part))
        
        return " → ".join(formatted_parts)
    
    def _format_error_message(self) -> str:
        """Format the errors dictionary into a readable error message."""
        if not self.errors:
            return "Validation failed"
        
        formatted_errors = []
        for field, error_data in self.errors.items():
            message = error_data["message"]
            if "description" in error_data and error_data["description"]:
                formatted_errors.append(f"{field}: {message} ({error_data['description']})")
            else:
                formatted_errors.append(f"{field}: {message}")
                
        return "\n".join(formatted_errors)
    
    def add_error(self, field: str, message: str, description: Optional[str] = None,
                 code: Optional[str] = None, expected: Optional[str] = None,
                 received: Optional[str] = None) -> None:
        """Add a new field error with detailed information.
        
        Args:
            field: The field name
            message: The error message
            description: Optional detailed description
            code: Error code identifier
            expected: Expected type or value
            received: Actual received type or value
        """
        error_data = {"message": message}
        if description:
            error_data["description"] = description
        if code:
            error_data["code"] = code
        if expected:
            error_data["expected"] = expected
        if received:
            error_data["received"] = received
            
        self.errors[field] = error_data
        
        # Add a ValidationIssue for this error
        field_path = self._parse_field_to_path(field)
        self._issues.append(ValidationIssue(
            code=code or ERROR_CODES["custom"].name,
            path=field_path,
            message=message,
            expected=expected,
            received=received
        ))
        
    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a ValidationIssue directly to the error.
        
        Args:
            issue: The validation issue to add
        """
        self._issues.append(issue)
        
        # Also add to the errors dictionary for backwards compatibility
        field = self._format_path(issue.path) if issue.path else "_base"
        error_data = {
            "message": issue.message,
            "code": issue.code
        }
        
        if issue.expected:
            error_data["expected"] = issue.expected
            
        if issue.received:
            error_data["received"] = issue.received
            
        self.errors[field] = error_data
        

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
        """Set a default value to use when the input is undefined.
        
        Fields with default values are automatically made optional.
        
        Args:
            value: The default value or a callable that returns the default value
            
        Returns:
            A new validator with the default value set
        """
        validator = self._clone()
        validator._default = value
        validator._optional = True  # Fix: make the cloned validator optional, not self
        
        return validator
        
    def apply(self, func: Callable[[R], R]) -> "Validator[T, R]":
        """Apply a transformation function to the validated value.
        
        This method allows for post-validation transformations while
        maintaining the validation chain.
        
        Args:
            func: The transformation function to apply
            
        Returns:
            A new validator that applies the transformation
        """
        validator = self._clone()
        
        # Store the original validation methods
        original_validate = validator._validate
        original_validate_async = validator._validate_async
        
        # Define new validation methods that apply the transformation
        def new_validate(data: Any, path: list[str | int]) -> R:
            validated = original_validate(data, path)
            return func(validated)
            
        async def new_validate_async(data: Any, path: list[str | int]) -> R:
            validated = await original_validate_async(data, path)
            return func(validated)
        
        # Replace the validation methods
        validator._validate = new_validate
        validator._validate_async = new_validate_async
        
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
        
        Args:
            error: The original validation error
            
        Returns:
            A wrapped validation error with the custom message
        """
        if self._custom_error_message is None:
            return error
        
        # Create a new error with the custom message but preserve the path
        if error.errors and len(error.errors) > 1:
            # If there are multiple errors, wrap them all with the custom message
            all_errors = {}
            for k in error.errors.keys():
                all_errors[k] = {"message": self._custom_error_message}
                if hasattr(error, "description") and error.description:
                    all_errors[k]["description"] = error.description
            return ValidationError(errors=all_errors)
        else:
            # For single error or simple case, use the traditional approach
            return ValidationError(
                self._custom_error_message, 
                error.path, 
                description=error.description if hasattr(error, "description") else None
            )
    
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

