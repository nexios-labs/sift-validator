"""
Primitive type validators for basic data types.

This module provides validators for primitive data types like strings,
numbers, booleans, etc.
"""

import re
import uuid
from typing import Any, Callable, Generic, List, Optional, Pattern, TypeVar, Union, cast, overload, Self
from datetime import date, datetime
import urllib.parse

from voltar .validators.email_validator import EmailValidator, EmailValidationError
from voltar .validators.base import Validator, ValidationError

T = TypeVar("T")

class String(Validator[str, str]):
    """
    Validator for string values with various string-specific validations.
    
    Examples:
        >>> String().validate("hello")
        'hello'
        >>> String().min(5).validate("hello")
        'hello'
        >>> String().max(3).validate("hello")  # Raises ValidationError
    """
    
    def __init__(self):
        super().__init__()
        self._min_length: Optional[int] = None
        self._max_length: Optional[int] = None
        self._pattern: Optional[Pattern] = None
        self._email: bool = False
        self._url: bool = False
        self._uuid: bool = False
        self._datetime: bool = False
        self._date: bool = False
        self._trim: bool = False
        self._lowercase: bool = False
        self._uppercase: bool = False
        self._nonempty: bool = False
        
    def min(self, length: int) -> Self:
        """
        Set minimum string length.
        
        Args:
            length: Minimum allowed length
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._min_length = length
        return validator
        
    def max(self, length: int) -> Self:
        """
        Set maximum string length.
        
        Args:
            length: Maximum allowed length
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._max_length = length
        return validator
        
    def length(self, length: int) -> Self:
        """
        Set exact string length.
        
        Args:
            length: Exact required length
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._min_length = length
        validator._max_length = length
        return validator
        
    def pattern(self, pattern: str | Pattern) -> Self:
        """
        Set regex pattern to match against.
        
        Args:
            pattern: Regular expression pattern as string or compiled Pattern
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        if isinstance(pattern, str):
            validator._pattern = re.compile(pattern)
        else:
            validator._pattern = pattern
        return validator
        
    def email(self) -> Self:
        """
        Validate that the string is a valid email address.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._email = True
        return validator
        
    def url(self) -> Self:
        """
        Validate that the string is a valid URL.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._url = True
        return validator
        
    def uuid(self) -> Self:
        """
        Validate that the string is a valid UUID.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._uuid = True
        return validator
        
    def datetime(self) -> Self:
        """
        Validate that the string is a valid ISO format datetime.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._datetime = True
        return validator
        
    def date(self) -> Self:
        """
        Validate that the string is a valid ISO format date.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._date = True
        return validator
        
    def trim(self) -> Self:
        """
        Trim whitespace from beginning and end of string.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._trim = True
        return validator
        
    def lowercase(self) -> Self:
        """
        Convert string to lowercase.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._lowercase = True
        return validator
        
    def uppercase(self) -> Self:
        """
        Convert string to uppercase.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._uppercase = True
        return validator
        
    def nonempty(self) -> Self:
        """
        Validate that the string is not empty.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._nonempty = True
        return validator
        
    def _validate(self, data: Any, path: list[str | int]) -> str:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(str, None)
            
        if not isinstance(data, str):
            raise ValidationError(
                self._get_error_message(f"Expected string, got {type(data).__name__}"),
                path
            )
            
        result = data
            
        # Apply transformations
        if self._trim:
            result = result.strip()
            
        if self._lowercase:
            result = result.lower()
            
        if self._uppercase:
            result = result.upper()
            
        # Validate constraints
        if self._nonempty and not result:
            raise ValidationError(
                self._get_error_message("String cannot be empty"),
                path
            )
            
        if self._min_length is not None and len(result) < self._min_length:
            raise ValidationError(
                self._get_error_message(f"String must be at least {self._min_length} characters long"),
                path
            )
            
        if self._max_length is not None and len(result) > self._max_length:
            raise ValidationError(
                self._get_error_message(f"String must be at most {self._max_length} characters long"),
                path
            )
            
        if self._pattern is not None and not self._pattern.match(result):
            raise ValidationError(
                self._get_error_message(f"String does not match pattern: {self._pattern.pattern}"),
                path
            )
            
        if self._email:
            try:
                # Use our EmailValidator's validate_email method
                EmailValidator().validate_email(data)
            except EmailValidationError as e:
                raise ValidationError(
                    self._get_error_message(f"Invalid email address: {str(e)}"),
                    path
                )
                
        if self._url:
            try:
                result_parsed = urllib.parse.urlparse(result)
                if not all([result_parsed.scheme, result_parsed.netloc]):
                    raise ValueError("URL must have a scheme and netloc")
            except Exception as e:
                raise ValidationError(
                    self._get_error_message(f"Invalid URL: {str(e)}"),
                    path
                )
                
        if self._uuid:
            try:
                uuid.UUID(result)
            except ValueError:
                raise ValidationError(
                    self._get_error_message("Invalid UUID format"),
                    path
                )
                
        if self._datetime:
            try:
                # Make sure it's a complete datetime (has both date and time parts)
                dt = datetime.fromisoformat(result)
                # Check if it has time components (at least hour and minute)
                if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
                    # If date object has all time components as 0, it might be just a date string
                    # Check if the original string contains time separators
                    if ":" not in result and "T" not in result:
                        raise ValueError("Missing time component")
            except ValueError:
                raise ValidationError(
                    self._get_error_message("Invalid ISO format datetime"),
                    path
                )
                
        if self._date:
            try:
                date.fromisoformat(result)
            except ValueError:
                raise ValidationError(
                    self._get_error_message("Invalid ISO format date"),
                    path
                )
                
        return result


class Number(Validator[Union[int, float], Union[int, float]]):
    """
    Validator for numeric values (integers and floats).
    
    Examples:
        >>> Number().validate(42)
        42
        >>> Number().min(10).validate(5)  # Raises ValidationError
        >>> Number().int().validate(3.14)  # Raises ValidationError
    """
    
    def __init__(self):
        super().__init__()
        self._min_value: Optional[Union[int, float]] = None
        self._max_value: Optional[Union[int, float]] = None
        self._integer: bool = False
        self._positive: bool = False
        self._negative: bool = False
        self._multiple_of: Optional[Union[int, float]] = None
        
    def min(self, value: Union[int, float]) -> Self:
        """
        Set minimum allowed value.
        
        Args:
            value: Minimum allowed value
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._min_value = value
        return validator
        
    def max(self, value: Union[int, float]) -> Self:
        """
        Set maximum allowed value.
        
        Args:
            value: Maximum allowed value
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._max_value = value
        return validator
        
    def int(self) -> Self:
        """
        Require the number to be an integer.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._integer = True
        return validator
        
    def positive(self) -> Self:
        """
        Require the number to be positive (> 0).
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._positive = True
        return validator
        
    def negative(self) -> Self:
        """
        Require the number to be negative (< 0).
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._negative = True
        return validator
        
    def multiple_of(self, value: Union[int, float]) -> Self:
        """
        Require the number to be a multiple of the specified value.
        
        Args:
            value: The number must be a multiple of this value
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._multiple_of = value
        return validator
        
    def _validate(self, data: Any, path: List[Union[str, int]]) -> Union[int, float]:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(Union[int, float], None)
        
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            raise ValidationError(
                self._get_error_message(f"Expected number, got {type(data).__name__}"),
                path
            )
            
        # Check if integer constraint is satisfied
        if self._integer and not isinstance(data, int) and not data.is_integer():
            raise ValidationError(
                self._get_error_message("Number must be an integer"),
                path
            )
            
        # Convert float to int if it's an integer value and int constraint is set
        result = int(data) if self._integer and isinstance(data, float) and data.is_integer() else data
            
        # Check positive constraint
        if self._positive and result <= 0:
            raise ValidationError(
                self._get_error_message("Number must be positive (> 0)"),
                path
            )
            
        # Check negative constraint
        if self._negative and result >= 0:
            raise ValidationError(
                self._get_error_message("Number must be negative (< 0)"),
                path
            )
            
        # Check min value constraint
        if self._min_value is not None and result < self._min_value:
            raise ValidationError(
                self._get_error_message(f"Number must be at least {self._min_value}"),
                path
            )
            
        # Check max value constraint
        if self._max_value is not None and result > self._max_value:
            raise ValidationError(
                self._get_error_message(f"Number must be at most {self._max_value}"),
                path
            )
            
        # Check multiple of constraint
        if self._multiple_of is not None:
            # Handle floating point precision issues
            remainder = result % self._multiple_of
            is_multiple = (
                remainder == 0 or 
                abs(remainder - self._multiple_of) < 1e-10
            )
            if not is_multiple:
                raise ValidationError(
                    self._get_error_message(f"Number must be a multiple of {self._multiple_of}"),
                    path
                )
                
        return result


class Boolean(Validator[bool, bool]):
    """
    Validator for boolean values.
    
    Examples:
        >>> Boolean().validate(True)
        True
        >>> Boolean().validate("true")  # Raises ValidationError
    """
    
    def __init__(self):
        super().__init__()
        self._truthy: bool = False
        
    def truthy(self) -> Self:
        """
        Allow truthy/falsy values to be converted to booleans.
        
        This will convert values like 1, "true", "yes" to True,
        and 0, "false", "no" to False.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._truthy = True
        return validator
        
    def _validate(self, data: Any, path: list[str | int]) -> bool:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(bool, None)
            
        if isinstance(data, bool):
            return data
            
        if not self._truthy:
            raise ValidationError(
                self._get_error_message(f"Expected boolean, got {type(data).__name__}"),
                path
            )
            
        # Handle truthy conversion
        if isinstance(data, (int, float)):
            return bool(data)
            
        if isinstance(data, str):
            lower_data = data.lower()
            if lower_data in ("true", "yes", "1", "y"):
                return True
            if lower_data in ("false", "no", "0", "n"):
                return False
                
        raise ValidationError(
            self._get_error_message(f"Cannot convert {type(data).__name__} to boolean"),
            path
        )


class Any(Validator[Any, Any]):
    """
    Validator that accepts any value without validation.
    
    This is useful as a placeholder or when you want to accept any type of data.
    
    Examples:
        >>> Any().validate(42)
        42
        >>> Any().validate("hello")
        'hello'
        >>> Any().validate({"key": "value"})
        {'key': 'value'}
    """
    
    def __init__(self):
        super().__init__()
        
    @property
    def _is_nullable(self) -> bool:
        """Override to make Any validator accept None values without explicit nullable()."""
        return True
        
    def _validate(self, data: Any, path: list[str | int]) -> Any:
        return data
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> Any:
        return data


class Null(Validator[None, None]):
    """
    Validator that only accepts null/None values.
    
    Examples:
        >>> Null().validate(None)
        None
        >>> Null().validate("hello")  # Raises ValidationError
    """
    
    def __init__(self):
        super().__init__()
        
    @property
    def _is_nullable(self) -> bool:
        """Override to make Null validator inherently nullable since it's designed for None values."""
        return True
    def validate(self, data: Any) -> None:
        """
        Override validate to always return None for None input regardless of default.
        
        This specialized behavior is necessary because Null validator is specifically
        designed to only accept None values, so defaults don't make sense in this context.
        """
        if data is None:
            return None
            
        # Not None, so validate normally (which will raise an error)
        return self._validate(data, [])
        
    def _validate(self, data: Any, path: list[str | int]) -> None:
        if data is not None:
            raise ValidationError(
                self._get_error_message(f"Expected null/None, got {type(data).__name__}"),
                path
            )
        return None
        return None
