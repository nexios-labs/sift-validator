"""
Tests for primitive validators: String, Number, Boolean, Any, Null.
"""

import pytest
import re
from datetime import datetime, date
import email_validator

from sift.validators.base import ValidationError
from sift.validators.primitives import String, Number, Boolean, Any, Null


class TestStringValidator:
    """Tests for the String validator."""
    
    def test_basic_validation(self, string_validator):
        """Test basic string validation."""
        # Valid strings
        assert string_validator.validate("") == ""
        assert string_validator.validate("hello") == "hello"
        assert string_validator.validate("123") == "123"
        
        # Invalid types
        with pytest.raises(ValidationError):
            string_validator.validate(123)
        with pytest.raises(ValidationError):
            string_validator.validate(True)
        with pytest.raises(ValidationError):
            string_validator.validate(None)
    
    def test_min_length(self):
        """Test string minimum length validation."""
        validator = String().min(3)
        
        # Valid strings
        assert validator.validate("abc") == "abc"
        assert validator.validate("abcdef") == "abcdef"
        
        # Invalid strings
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("ab")
        assert "at least 3 characters" in str(exc_info.value)
    
    def test_max_length(self):
        """Test string maximum length validation."""
        validator = String().max(5)
        
        # Valid strings
        assert validator.validate("") == ""
        assert validator.validate("abc") == "abc"
        assert validator.validate("abcde") == "abcde"
        
        # Invalid strings
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("abcdef")
        assert "at most 5 characters" in str(exc_info.value)
    
    def test_exact_length(self):
        """Test string exact length validation."""
        validator = String().length(4)
        
        # Valid strings
        assert validator.validate("abcd") == "abcd"
        
        # Invalid strings
        with pytest.raises(ValidationError):
            validator.validate("abc")
        with pytest.raises(ValidationError):
            validator.validate("abcde")
    
    def test_pattern(self):
        """Test string pattern validation."""
        # Test with string pattern
        validator = String().pattern(r"^[a-z]+$")
        
        assert validator.validate("abc") == "abc"
        with pytest.raises(ValidationError):
            validator.validate("123")
        with pytest.raises(ValidationError):
            validator.validate("abcDEF")
        
        # Test with compiled pattern
        validator = String().pattern(re.compile(r"^[a-z]+$"))
        
        assert validator.validate("abc") == "abc"
        with pytest.raises(ValidationError):
            validator.validate("123")
    
    def test_email(self):
        """Test email validation."""
        validator = String().email()
        
        # Valid emails
        assert validator.validate("user@example.com") == "user@example.com"
        assert validator.validate("name.surname@domain.co.uk") == "name.surname@domain.co.uk"
        
        # Invalid emails
        with pytest.raises(ValidationError):
            validator.validate("not-an-email")
        with pytest.raises(ValidationError):
            validator.validate("missing@")
        with pytest.raises(ValidationError):
            validator.validate("@domain.com")
    
    def test_url(self):
        """Test URL validation."""
        validator = String().url()
        
        # Valid URLs
        assert validator.validate("https://example.com") == "https://example.com"
        assert validator.validate("http://sub.domain.co.uk/path?query=1") == "http://sub.domain.co.uk/path?query=1"
        
        # Invalid URLs
        with pytest.raises(ValidationError):
            validator.validate("not-a-url")
        with pytest.raises(ValidationError):
            validator.validate("www.example.com")  # Missing scheme
    
    def test_uuid(self):
        """Test UUID validation."""
        validator = String().uuid()
        
        # Valid UUIDs
        assert validator.validate("123e4567-e89b-12d3-a456-426614174000") == "123e4567-e89b-12d3-a456-426614174000"
        
        # Invalid UUIDs
        with pytest.raises(ValidationError):
            validator.validate("not-a-uuid")
        with pytest.raises(ValidationError):
            validator.validate("123e4567-e89b-12d3-a456")  # Too short
    
    def test_datetime(self):
        """Test datetime validation."""
        validator = String().datetime()
        
        # Valid datetime strings
        assert validator.validate("2023-01-01T12:00:00") == "2023-01-01T12:00:00"
        assert validator.validate("2023-01-01 12:00:00") == "2023-01-01 12:00:00"
        
        # Invalid datetime strings
        with pytest.raises(ValidationError):
            validator.validate("not-a-datetime")
        with pytest.raises(ValidationError):
            validator.validate("2023-01-01")  # Missing time component
    
    def test_date(self):
        """Test date validation."""
        validator = String().date()
        
        # Valid date strings
        assert validator.validate("2023-01-01") == "2023-01-01"
        
        # Invalid date strings
        with pytest.raises(ValidationError):
            validator.validate("not-a-date")
        with pytest.raises(ValidationError):
            validator.validate("01/01/2023")  # Wrong format
    
    def test_nonempty(self):
        """Test non-empty string validation."""
        validator = String().nonempty()
        
        # Valid non-empty strings
        assert validator.validate("a") == "a"
        assert validator.validate("hello") == "hello"
        
        # Invalid empty string
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("")
        assert "cannot be empty" in str(exc_info.value)
    
    def test_transformation(self):
        """Test string transformation methods."""
        # Test trim
        validator = String().trim()
        assert validator.validate("  hello  ") == "hello"
        
        # Test lowercase
        validator = String().lowercase()
        assert validator.validate("HELLO") == "hello"
        
        # Test uppercase
        validator = String().uppercase()
        assert validator.validate("hello") == "HELLO"
        
        # Test chained transformations
        validator = String().trim().lowercase()
        assert validator.validate("  HELLO  ") == "hello"
    
    def test_chained_validation(self):
        """Test chaining multiple validations."""
        validator = String().min(3).max(10).pattern(r"^[a-z]+$")
        
        # Valid strings
        assert validator.validate("hello") == "hello"
        
        # Invalid strings
        with pytest.raises(ValidationError):
            validator.validate("ab")  # Too short
        with pytest.raises(ValidationError):
            validator.validate("abcdefghijk")  # Too long
        with pytest.raises(ValidationError):
            validator.validate("abcDEF")  # Pattern mismatch
    
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for strings."""
        validator = String().min(3).email()
        
        # Valid email
        result = await validator.validate_async("user@example.com")
        assert result == "user@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            await validator.validate_async("not-an-email")


class TestNumberValidator:
    """Tests for the Number validator."""
    
    def test_basic_validation(self, number_validator):
        """Test basic number validation."""
        # Valid numbers
        assert number_validator.validate(0) == 0
        assert number_validator.validate(42) == 42
        assert number_validator.validate(-10) == -10
        assert number_validator.validate(3.14) == 3.14
        assert number_validator.validate(-0.5) == -0.5
        
        # Invalid types
        with pytest.raises(ValidationError):
            number_validator.validate("123")
        with pytest.raises(ValidationError):
            number_validator.validate(True)  # Boolean is not a valid number
        with pytest.raises(ValidationError):
            number_validator.validate(None)
            
    def test_integer_validation(self):
        """Test integer validation."""
        validator = Number().int()
        
        # Valid integers
        assert validator.validate(0) == 0
        assert validator.validate(42) == 42
        assert validator.validate(-10) == -10
        
        # Integer-like floats should be converted to integers
        assert validator.validate(42.0) == 42
        assert isinstance(validator.validate(42.0), int)
        
        # Invalid floats (non-integer)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(3.14)
        assert "must be an integer" in str(exc_info.value)
        
    def test_min_validation(self):
        """Test minimum value validation."""
        validator = Number().min(10)
        
        # Valid numbers
        assert validator.validate(10) == 10
        assert validator.validate(20) == 20
        assert validator.validate(10.5) == 10.5
        
        # Invalid numbers
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(9)
        assert "must be at least 10" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(9.99)
            
    def test_max_validation(self):
        """Test maximum value validation."""
        validator = Number().max(10)
        
        # Valid numbers
        assert validator.validate(10) == 10
        assert validator.validate(5) == 5
        assert validator.validate(-10) == -10
        assert validator.validate(9.99) == 9.99
        
        # Invalid numbers
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(10.01)
        assert "must be at most 10" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(11)
            
    def test_range_validation(self):
        """Test range validation (min and max together)."""
        validator = Number().min(0).max(100)
        
        # Valid numbers in range
        assert validator.validate(0) == 0
        assert validator.validate(50) == 50
        assert validator.validate(100) == 100
        assert validator.validate(99.99) == 99.99
        
        # Invalid numbers outside range
        with pytest.raises(ValidationError):
            validator.validate(-0.01)
        with pytest.raises(ValidationError):
            validator.validate(100.01)
            
    def test_positive_validation(self):
        """Test positive number validation."""
        validator = Number().positive()
        
        # Valid positive numbers
        assert validator.validate(1) == 1
        assert validator.validate(0.1) == 0.1
        
        # Invalid non-positive numbers
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(0)
        assert "must be positive" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(-1)
            
    def test_negative_validation(self):
        """Test negative number validation."""
        validator = Number().negative()
        
        # Valid negative numbers
        assert validator.validate(-1) == -1
        assert validator.validate(-0.1) == -0.1
        
        # Invalid non-negative numbers
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(0)
        assert "must be negative" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(1)
            
    def test_multiple_of_validation(self):
        """Test multiple of validation."""
        validator = Number().multiple_of(5)
        
        # Valid multiples of 5
        assert validator.validate(0) == 0
        assert validator.validate(5) == 5
        assert validator.validate(10) == 10
        assert validator.validate(-5) == -5
        assert validator.validate(15.0) == 15.0
        
        # Handle floating point precision issues
        assert validator.validate(5.0 - 1e-11) == 5.0 - 1e-11  # Should pass due to tolerance
        
        # Invalid numbers
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(7)
        assert "must be a multiple of 5" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(5.1)
            
    def test_chained_validation(self):
        """Test chaining multiple validations."""
        validator = Number().int().min(0).max(100).multiple_of(5)
        
        # Valid numbers
        assert validator.validate(0) == 0
        assert validator.validate(5) == 5
        assert validator.validate(50) == 50
        assert validator.validate(100) == 100
        
        # Invalid numbers
        with pytest.raises(ValidationError):
            validator.validate(-5)  # Below min
        with pytest.raises(ValidationError):
            validator.validate(105)  # Above max
        with pytest.raises(ValidationError):
            validator.validate(7)  # Not multiple of 5
        with pytest.raises(ValidationError):
            validator.validate(3.14)  # Not an integer
    
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for numbers."""
        validator = Number().int().min(0).max(100)
        
        # Valid number
        result = await validator.validate_async(42)
        assert result == 42
        
        # Invalid number
        with pytest.raises(ValidationError):
            await validator.validate_async(-1)
            
        # Float that's not an integer
        with pytest.raises(ValidationError):
            await validator.validate_async(3.14)


class TestBooleanValidator:
    """Tests for the Boolean validator."""
    
    def test_basic_validation(self, boolean_validator):
        """Test basic boolean validation."""
        # Valid booleans
        assert boolean_validator.validate(True) is True
        assert boolean_validator.validate(False) is False
        
        # Invalid types
        with pytest.raises(ValidationError):
            boolean_validator.validate(1)
        with pytest.raises(ValidationError):
            boolean_validator.validate(0)
        with pytest.raises(ValidationError):
            boolean_validator.validate("true")
        with pytest.raises(ValidationError):
            boolean_validator.validate(None)
            
    def test_truthy_validation(self):
        """Test truthy conversion."""
        validator = Boolean().truthy()
        
        # True values
        assert validator.validate(True) is True
        assert validator.validate(1) is True
        assert validator.validate("true") is True
        assert validator.validate("yes") is True
        assert validator.validate("1") is True
        assert validator.validate("y") is True
        
        # False values
        assert validator.validate(False) is False
        assert validator.validate(0) is False
        assert validator.validate("false") is False
        assert validator.validate("no") is False
        assert validator.validate("0") is False
        assert validator.validate("n") is False
        
        # Invalid values (not convertible to boolean)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("maybe")
        assert "Cannot convert" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(None)
            
    def test_default_value(self):
        """Test default value for booleans."""
        validator = Boolean().default(True)
        
        # None should be replaced with default
        assert validator.validate(None) is True
        
        # Valid values should be kept
        assert validator.validate(True) is True
        assert validator.validate(False) is False
        
        # Invalid values should still fail
        with pytest.raises(ValidationError):
            validator.validate("not a boolean")
            
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for booleans."""
        validator = Boolean().truthy()
        
        # Valid truthy values
        assert await validator.validate_async(True) is True
        assert await validator.validate_async("yes") is True
        
        # Valid falsy values
        assert await validator.validate_async(False) is False
        assert await validator.validate_async("no") is False
        
        # Invalid values
        with pytest.raises(ValidationError):
            await validator.validate_async(None)


class TestAnyValidator:
    """Tests for the Any validator."""
    
    def test_basic_validation(self, any_validator):
        """Test that Any validator accepts any value."""
        # Test with various types, all should pass
        assert any_validator.validate("string") == "string"
        assert any_validator.validate(123) == 123
        assert any_validator.validate(3.14) == 3.14
        assert any_validator.validate(True) is True
        assert any_validator.validate([1, 2, 3]) == [1, 2, 3]
        assert any_validator.validate({"key": "value"}) == {"key": "value"}
        assert any_validator.validate(None) is None
        
    def test_optional(self):
        """Test optional with Any validator."""
        validator = Any().optional()
        
        # None should pass with optional
        assert validator.validate(None) is None
        
        # Any other value should also pass
        assert validator.validate("test") == "test"
        assert validator.validate(123) == 123
        
    def test_nullable(self):
        """Test nullable with Any validator."""
        validator = Any().nullable()
        
        # None should pass with nullable
        assert validator.validate(None) is None
        
        # Any other value should also pass
        assert validator.validate("test") == "test"
        assert validator.validate(123) == 123
        
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for Any validator."""
        validator = Any()
        
        # Test with various types, all should pass
        assert await validator.validate_async("string") == "string"
        assert await validator.validate_async(123) == 123
        assert await validator.validate_async(None) is None


class TestNullValidator:
    """Tests for the Null validator."""
    
    def test_basic_validation(self, null_validator):
        """Test that Null validator only accepts None."""
        # None should pass
        assert null_validator.validate(None) is None
        
        # Any other value should fail
        with pytest.raises(ValidationError) as exc_info:
            null_validator.validate("string")
        assert "Expected null/None" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            null_validator.validate(0)
            
        with pytest.raises(ValidationError):
            null_validator.validate(False)
            
    def test_with_default(self):
        """Test default with Null validator."""
        # This is an unusual case but should still work correctly
        validator = Null().default("default")
        
        # None should pass
        assert validator.validate(None) is None
        
        # Any other value should still fail
        with pytest.raises(ValidationError):
            validator.validate("string")
            
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for Null validator."""
        validator = Null()
        
        # None should pass
        assert await validator.validate_async(None) is None
        
        # Any other value should fail
        with pytest.raises(ValidationError):
            await validator.validate_async("not null")
            
        with pytest.raises(ValidationError):
            await validator.validate_async(0)
