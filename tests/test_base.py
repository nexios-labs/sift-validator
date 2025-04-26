"""
Tests for the base Validator class.
"""

import pytest
import asyncio
from typing import Any, Optional

from sift.validators.base import Validator, ValidationError


class TestValidator:
    """Tests for the base Validator class."""
    
    def test_validate_method(self):
        """Test the validate method."""
        # Create a simple implementation of Validator for testing
        class TestStringValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        validator = TestStringValidator()
        
        # Valid data
        assert validator.validate("hello") == "hello"
        
        # Invalid data
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(123)
        assert "Value must be a string" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_async_method(self):
        """Test the validate_async method."""
        # Create a validator with async validation
        class TestAsyncValidator(Validator):
            async def _validate_async(self, data, path):
                await asyncio.sleep(0.01)  # Add small delay
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data.upper()
            
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        validator = TestAsyncValidator()
        
        # Valid data
        result = await validator.validate_async("hello")
        assert result == "HELLO"  # Should be uppercase due to _validate_async implementation
        
        # Invalid data
        with pytest.raises(ValidationError) as exc_info:
            await validator.validate_async(123)
        assert "Value must be a string" in str(exc_info.value)
    
    def test_optional(self):
        """Test optional validation."""
        # Create a simple validator
        class TestValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        # Create optional validator
        validator = TestValidator().optional()
        
        # None should pass
        assert validator.validate(None) is None
        
        # Normal validation still applies to non-None values
        assert validator.validate("hello") == "hello"
        with pytest.raises(ValidationError):
            validator.validate(123)
    
    def test_nullable(self):
        """Test nullable validation."""
        # Create a simple validator
        class TestValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        # Create nullable validator
        validator = TestValidator().nullable()
        
        # None should pass
        assert validator.validate(None) is None
        
        # Normal validation still applies to non-None values
        assert validator.validate("hello") == "hello"
        with pytest.raises(ValidationError):
            validator.validate(123)
    
    def test_optional_and_nullable_difference(self):
        """Test the difference between optional and nullable."""
        # Create a simple validator
        class TestValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        # Optional should only allow None as input
        optional_validator = TestValidator().optional()
        assert optional_validator.validate(None) is None
        
        # Nullable should only allow None as input
        nullable_validator = TestValidator().nullable()
        assert nullable_validator.validate(None) is None
        
        # The difference would be more apparent in data structures, not at direct input level
    
    def test_default(self):
        """Test default values."""
        # Create a simple validator
        class TestValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        # Static default value
        validator_with_default = TestValidator().default("default_value")
        assert validator_with_default.validate(None) == "default_value"
        assert validator_with_default.validate("hello") == "hello"
        
        # Callable default value
        counter = 0
        def get_default():
            nonlocal counter
            counter += 1
            return f"generated_{counter}"
        
        validator_with_callable = TestValidator().default(get_default)
        assert validator_with_callable.validate(None) == "generated_1"
        assert validator_with_callable.validate(None) == "generated_2"
        assert validator_with_callable.validate("hello") == "hello"
    
    def test_error(self):
        """Test custom error messages."""
        # Create a simple validator
        class TestValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        # Create validator with custom error
        validator = TestValidator().error("Custom error message")
        
        # Error message should be replaced
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(123)
        assert "Custom error message" in str(exc_info.value)
    
    def test_clone(self):
        """Test the _clone method."""
        # Create a validator with state
        class TestValidator(Validator):
            def __init__(self):
                super().__init__()
                self._min_length = 0
                
            def min(self, length):
                validator = self._clone()
                validator._min_length = length
                return validator
                
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                if len(data) < self._min_length:
                    raise ValidationError(f"String must be at least {self._min_length} characters", path)
                return data
        
        # Create original validator
        original = TestValidator()
        
        # Create clone with different state
        clone = original.min(5)
        
        # Original should not be affected
        assert original._min_length == 0
        assert clone._min_length == 5
        
        # Behavior should be different
        assert original.validate("a") == "a"
        with pytest.raises(ValidationError):
            clone.validate("a")
    
    def test_error_path(self):
        """Test that error paths are correctly included in messages."""
        # Create a validator
        class TestValidator(Validator):
            def _validate(self, data, path):
                if not isinstance(data, str):
                    raise ValidationError("Value must be a string", path)
                return data
        
        validator = TestValidator()
        
        # Test with path
        with pytest.raises(ValidationError) as exc_info:
            validator._validate(123, ["root", "nested", 0])
        
        error_msg = str(exc_info.value)
        assert "root.nested.0" in error_msg
        assert "Value must be a string" in error_msg

"""
Tests for the base validator functionality.
"""

import pytest
import asyncio
from sift.validators.base import Validator, ValidationError


def test_validator_optional():
    """Test that optional validation works correctly."""
    # Create a simple validator that extends the base class
    class TestValidator(Validator):
        def _validate(self, data, path):
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data

    # Create a validator and mark it as optional
    validator = TestValidator().optional()
    
    # Test with None - should pass and return None
    assert validator.validate(None) is None
    
    # Test with a string - should pass and return the string
    assert validator.validate("test") == "test"
    
    # Test with a non-string - should raise ValidationError
    with pytest.raises(ValidationError):
        validator.validate(123)


def test_validator_nullable():
    """Test that nullable validation works correctly."""
    # Create a simple validator that extends the base class
    class TestValidator(Validator):
        def _validate(self, data, path):
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data

    # Create a validator and mark it as nullable
    validator = TestValidator().nullable()
    
    # Test with None - should pass and return None
    assert validator.validate(None) is None
    
    # Test with a string - should pass and return the string
    assert validator.validate("test") == "test"
    
    # Test with a non-string - should raise ValidationError
    with pytest.raises(ValidationError):
        validator.validate(123)


def test_validator_default():
    """Test that default values work correctly."""
    # Create a simple validator that extends the base class
    class TestValidator(Validator):
        def _validate(self, data, path):
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data

    # Create a validator with a default value
    validator = TestValidator().default("default")
    
    # Test with None - should use the default value
    assert validator.validate(None) == "default"
    
    # Test with a string - should use the provided value
    assert validator.validate("test") == "test"
    
    # Test with a non-string - should raise ValidationError
    with pytest.raises(ValidationError):
        validator.validate(123)
        
    # Test with a callable default
    counter = 0
    def get_default():
        nonlocal counter
        counter += 1
        return f"default-{counter}"
        
    validator = TestValidator().default(get_default)
    
    # Each call should get a fresh default value
    assert validator.validate(None) == "default-1"
    assert validator.validate(None) == "default-2"


def test_validator_error():
    """Test that custom error messages work correctly."""
    # Create a simple validator that extends the base class
    class TestValidator(Validator):
        def _validate(self, data, path):
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data

    # Create a validator with a custom error message
    validator = TestValidator().error("Custom error message")
    
    # Test with a non-string - should raise ValidationError with custom message
    with pytest.raises(ValidationError) as exc_info:
        validator.validate(123)
    assert "Custom error message" in str(exc_info.value)


def test_validation_error_path():
    """Test that validation errors include the correct path."""
    # Create a simple validator that extends the base class
    class TestValidator(Validator):
        def _validate(self, data, path):
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data

    # Create a validator
    validator = TestValidator()
    
    # Test with a path
    with pytest.raises(ValidationError) as exc_info:
        validator._validate(123, ["root", "nested", 0])
    assert "root.nested.0: Value must be a string" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_validation():
    """Test that async validation works correctly."""
    # Create a simple validator with async validation
    class AsyncValidator(Validator):
        async def _validate_async(self, data, path):
            await asyncio.sleep(0.01)  # simulate async operation
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data.upper()
            
        def _validate(self, data, path):
            if not isinstance(data, str):
                raise ValidationError("Value must be a string", path)
            return data

    # Create a validator
    validator = AsyncValidator()
    
    # Test async validation with a string
    result = await validator.validate_async("test")
    assert result == "TEST"
    
    # Test async validation with a non-string
    with pytest.raises(ValidationError):
        await validator.validate_async(123)
        
    # Test that optional and nullable work with async validation
    optional_validator = AsyncValidator().optional()
    assert await optional_validator.validate_async(None) is None
    
    nullable_validator = AsyncValidator().nullable()
    assert await nullable_validator.validate_async(None) is None

