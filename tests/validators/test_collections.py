"""
Tests for collection validators: List, Dict, Tuple, Union.
"""

import pytest
import asyncio
from typing import Any, Dict, List, Union as TypeUnion

from voltar .validators.base import Validator, ValidationError
from voltar .validators.primitives import String, Number, Boolean, Any, Null
from voltar .validators.collections import List as ListValidator
from voltar .validators.collections import Dict as DictValidator
from voltar .validators.collections import Tuple as TupleValidator
from voltar .validators.collections import Union


class TestListValidator:
    """Tests for the List validator."""
    
    def test_basic_validation(self, list_validator):
        """Test basic list validation."""
        # Valid lists
        assert list_validator.validate([]) == []
        assert list_validator.validate(["hello"]) == ["hello"]
        assert list_validator.validate(["hello", "world"]) == ["hello", "world"]
        
        # Lists from other sequence types
        assert list_validator.validate(("hello", "world")) == ["hello", "world"]
        
        # Invalid types
        with pytest.raises(ValidationError):
            list_validator.validate(123)
        with pytest.raises(ValidationError):
            list_validator.validate("not a list")
        with pytest.raises(ValidationError):
            list_validator.validate(None)
    
    def test_item_validation(self):
        """Test item validation in lists."""
        string_list_validator = ListValidator(String())
        number_list_validator = ListValidator(Number().int())
        
        # Valid items for string list
        assert string_list_validator.validate(["a", "b", "c"]) == ["a", "b", "c"]
        
        # Invalid items for string list
        with pytest.raises(ValidationError) as exc_info:
            string_list_validator.validate(["a", 123, "c"])
        assert "Expected string" in str(exc_info.value)
        
        # Valid items for number list
        assert number_list_validator.validate([1, 2, 3]) == [1, 2, 3]
        
        # Invalid items for number list
        with pytest.raises(ValidationError):
            number_list_validator.validate([1, "two", 3])
        with pytest.raises(ValidationError):
            number_list_validator.validate([1, 2.5, 3])  # Not an integer
    
    def test_min_length(self):
        """Test minimum length validation for lists."""
        validator = ListValidator(String()).min(2)
        
        # Valid lists
        assert validator.validate(["a", "b"]) == ["a", "b"]
        assert validator.validate(["a", "b", "c"]) == ["a", "b", "c"]
        
        # Invalid lists (too short)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([])
        assert "at least 2 items" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            validator.validate(["a"])
    
    def test_max_length(self):
        """Test maximum length validation for lists."""
        validator = ListValidator(String()).max(3)
        
        # Valid lists
        assert validator.validate([]) == []
        assert validator.validate(["a"]) == ["a"]
        assert validator.validate(["a", "b", "c"]) == ["a", "b", "c"]
        
        # Invalid lists (too long)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(["a", "b", "c", "d"])
        assert "at most 3 items" in str(exc_info.value)
    
    def test_exact_length(self):
        """Test exact length validation for lists."""
        validator = ListValidator(String()).length(3)
        
        # Valid lists
        assert validator.validate(["a", "b", "c"]) == ["a", "b", "c"]
        
        # Invalid lists (wrong length)
        with pytest.raises(ValidationError):
            validator.validate(["a", "b"])
        with pytest.raises(ValidationError):
            validator.validate(["a", "b", "c", "d"])
    
    def test_unique_items(self):
        """Test unique items constraint for lists."""
        validator = ListValidator(String()).unique()
        
        # Valid lists (unique items)
        assert validator.validate([]) == []
        assert validator.validate(["a"]) == ["a"]
        assert validator.validate(["a", "b", "c"]) == ["a", "b", "c"]
        
        # Invalid lists (duplicate items)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(["a", "b", "a"])
        assert "must be unique" in str(exc_info.value)
    
    def test_unique_unhashable_items(self):
        """Test unique items constraint with unhashable items."""
        validator = ListValidator(ListValidator(Number())).unique()
        
        # Valid lists (unique unhashable items)
        assert validator.validate([[1], [2], [3]]) == [[1], [2], [3]]
        
        # Invalid lists (duplicate unhashable items)
        with pytest.raises(ValidationError):
            validator.validate([[1], [2], [1]])
    
    def test_nonempty(self):
        """Test non-empty constraint for lists."""
        validator = ListValidator(String()).nonempty()
        
        # Valid lists (non-empty)
        assert validator.validate(["a"]) == ["a"]
        assert validator.validate(["a", "b"]) == ["a", "b"]
        
        # Invalid lists (empty)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate([])
        assert "cannot be empty" in str(exc_info.value)
    
    def test_nested_lists(self):
        """Test nested list validation."""
        # Matrix validator (list of lists of numbers)
        matrix_validator = ListValidator(ListValidator(Number().int()))
        
        # Valid matrix
        valid_matrix = [[1, 2], [3, 4], [5, 6]]
        assert matrix_validator.validate(valid_matrix) == valid_matrix
        
        # Invalid outer list items
        with pytest.raises(ValidationError):
            matrix_validator.validate([[1, 2], "not a list", [5, 6]])
        
        # Invalid inner list items
        with pytest.raises(ValidationError):
            matrix_validator.validate([[1, 2], [3, "four"], [5, 6]])
    
    def test_chained_validation(self):
        """Test chaining multiple validations for lists."""
        validator = ListValidator(String()).min(2).max(4).unique()
        
        # Valid lists
        assert validator.validate(["a", "b"]) == ["a", "b"]
        assert validator.validate(["a", "b", "c", "d"]) == ["a", "b", "c", "d"]
        
        # Invalid lists
        with pytest.raises(ValidationError):
            validator.validate(["a"])  # Too short
        with pytest.raises(ValidationError):
            validator.validate(["a", "b", "c", "d", "e"])  # Too long
        with pytest.raises(ValidationError):
            validator.validate(["a", "b", "a"])  # Not unique
    
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for lists."""
        validator = ListValidator(String().min(2))
        
        # Valid list
        result = await validator.validate_async(["hello", "world"])
        assert result == ["hello", "world"]
        
        # Invalid list (item validation fails)
        with pytest.raises(ValidationError):
            await validator.validate_async(["h", "world"])
    
    @pytest.mark.asyncio
    async def test_parallel_validation(self):
        """Test that list items are validated in parallel."""
        # Create a validator with deliberate delay
        class DelayedValidator(Validator):
            async def _validate_async(self, data, path):
                await asyncio.sleep(0.1)  # Add delay
                if not isinstance(data, str):
                    raise ValidationError("Expected string", path)
                return data
        
        validator = ListValidator(DelayedValidator())
        
        # Validate a list with 5 items
        start_time = asyncio.get_event_loop().time()
        await validator.validate_async(["a", "b", "c", "d", "e"])
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Should take ~0.1s due to parallel validation, not ~0.5s
        assert elapsed < 0.2, "List validation should be parallel"


class TestDictValidator:
    """Tests for the Dict validator."""
    
    def test_basic_validation(self, dict_validator):
        """Test basic dictionary validation."""
        # Valid dictionaries
        assert dict_validator.validate({"name": "John", "age": 30}) == {"name": "John", "age": 30}
        
        # Invalid types
        with pytest.raises(ValidationError):
            dict_validator.validate(123)
        with pytest.raises(ValidationError):
            dict_validator.validate("not a dict")
        with pytest.raises(ValidationError):
            dict_validator.validate(None)
        with pytest.raises(ValidationError):
            dict_validator.validate([])
    
    def test_schema_validation(self):
        """Test schema validation for dictionaries."""
        validator = DictValidator({
            "name": String().min(1),
            "age": Number().int().min(0),
            "email": String().email().optional()
        })
        
        # Valid dictionary
        assert validator.validate({
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }) == {
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }
        
        # Valid with optional field missing
        assert validator.validate({
            "name": "John",
            "age": 30
        }) == {
            "name": "John",
            "age": 30
        }
        
        # Invalid name
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({
                "name": "",  # Too short
                "age": 30
            })
        assert "name" in str(exc_info.value) and "at least 1" in str(exc_info.value)
        
        # Invalid age
        with pytest.raises(ValidationError):
            validator.validate({
                "name": "John",
                "age": -1  # Negative
            })
        
        # Invalid email
        with pytest.raises(ValidationError):
            validator.validate({
                "name": "John",
                "age": 30,
                "email": "not-an-email"
            })
    
    def test_required_fields(self):
        """Test required fields validation for dictionaries."""
        validator = DictValidator({
            "name": String(),
            "age": Number(),
            "email": String()
        }).required("name", "email")  # Only name and email are required
        
        # Valid with all fields
        assert validator.validate({
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }) == {
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }
        
        # Valid with only required fields
        assert validator.validate({
            "name": "John",
            "email": "john@example.com"
        }) == {
            "name": "John",
            "email": "john@example.com"
        }
        
        # Invalid (missing required field)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({
                "name": "John"
                # Missing email
            })
        assert "Missing required properties: email" in str(exc_info.value)
    
    def test_pattern_properties(self):
        """Test pattern properties validation for dictionaries."""
        validator = DictValidator().pattern_property(
            r"^meta_", String()
        ).pattern_property(
            r"^num_", Number().int()
        )
        
        # Valid with pattern properties
        assert validator.validate({
            "meta_title": "Hello",
            "meta_author": "John",
            "num_pages": 42,
            "num_chapters": 5
        }) == {
            "meta_title": "Hello",
            "meta_author": "John",
            "num_pages": 42,
            "num_chapters": 5
        }
        
        # Invalid meta property (should be string)
        with pytest.raises(ValidationError):
            validator.validate({
                "meta_title": 123  # Should be string
            })
        
        # Invalid num property (should be integer)
        with pytest.raises(ValidationError):
            validator.validate({
                "num_pages": "42"  # Should be number
            })
    
    def test_additional_properties(self):
        """Test additional properties validation for dictionaries."""
        # Disallow additional properties
        validator_strict = DictValidator({
            "name": String(),
            "age": Number()
        }).additional_properties(False)
        
        # Valid (no additional properties)
        assert validator_strict.validate({
            "name": "John",
            "age": 30
        }) == {
            "name": "John",
            "age": 30
        }
        
        # Invalid (has additional property)
        with pytest.raises(ValidationError) as exc_info:
            validator_strict.validate({
                "name": "John",
                "age": 30,
                "email": "john@example.com"  # Additional property
            })
        assert "Unexpected additional properties" in str(exc_info.value)
        
        # Allow additional properties with validation
        validator_with_validation = DictValidator({
            "name": String(),
            "age": Number()
        }).additional_properties(String().min(3))
        
        # Valid (additional property passes validation)
        assert validator_with_validation.validate({
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }) == {
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }
        
        # Invalid (additional property fails validation)
        with pytest.raises(ValidationError):
            validator_with_validation.validate({
                "name": "John",
                "age": 30,
                "x": "a"  # Too short
            })
    
    def test_min_max_properties(self):
        """Test min and max properties constraints for dictionaries."""
        validator = DictValidator().min_properties(2).max_properties(4)
        
        # Valid dictionaries
        assert validator.validate({"a": 1, "b": 2}) == {"a": 1, "b": 2}
        assert validator.validate({"a": 1, "b": 2, "c": 3}) == {"a": 1, "b": 2, "c": 3}
        assert validator.validate({"a": 1, "b": 2, "c": 3, "d": 4}) == {"a": 1, "b": 2, "c": 3, "d": 4}
        
        # Invalid dictionaries (too few properties)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({"a": 1})  # Only one property
        assert "at least 2 properties" in str(exc_info.value)
        
        # Invalid dictionaries (too many properties)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})  # Five properties
        assert "at most 4 properties" in str(exc_info.value)
    
    def test_nested_dictionaries(self):
        """Test nested dictionary validation."""
        user_schema = DictValidator({
            "name": String().min(1),
            "profile": DictValidator({
                "age": Number().int().min(0),
                "address": DictValidator({
                    "city": String().min(1),
                    "zipCode": String().pattern(r"^\d{5}$")
                })
            })
        })
        
        # Valid nested dictionary
        valid_user = {
            "name": "John",
            "profile": {
                "age": 30,
                "address": {
                    "city": "New York",
                    "zipCode": "10001"
                }
            }
        }
        assert user_schema.validate(valid_user) == valid_user
        
        # Invalid nested value (invalid zip code)
        invalid_user = {
            "name": "John",
            "profile": {
                "age": 30,
                "address": {
                    "city": "New York",
                    "zipCode": "invalid"  # Invalid zip code
                }
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            user_schema.validate(invalid_user)
        assert "profile.address.zipCode" in str(exc_info.value)
        
        # Missing nested property
        missing_property = {
            "name": "John",
            "profile": {
                "age": 30,
                "address": {
                    "city": "New York"
                    # Missing zipCode
                }
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            user_schema.validate(missing_property)
        assert "profile.address" in str(exc_info.value) and "zipCode" in str(exc_info.value)
    
    def test_chained_validation(self):
        """Test chaining multiple validations for dictionaries."""
        validator = DictValidator({
            "name": String().min(1),
            "age": Number().int()
        }).min_properties(2).max_properties(3).additional_properties(String())
        
        # Valid dictionary
        assert validator.validate({
            "name": "John",
            "age": 30,
            "note": "Extra info"
        }) == {
            "name": "John",
            "age": 30,
            "note": "Extra info"
        }
        
        # Invalid (additional property with wrong type)
        with pytest.raises(ValidationError):
            validator.validate({
                "name": "John",
                "age": 30,
                "score": 100  # Should be string
            })
        
        # Invalid (too many properties)
        with pytest.raises(ValidationError):
            validator.validate({
                "name": "John",
                "age": 30,
                "note": "Extra info",
                "more": "Too many"
            })
    
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for dictionaries."""
        validator = DictValidator({
            "name": String().min(2),
            "age": Number().int().min(18)
        })
        
        # Valid dictionary
        result = await validator.validate_async({
            "name": "John",
            "age": 30
        })
        assert result == {"name": "John", "age": 30}
        
        # Invalid dictionary (field validation fails)
        with pytest.raises(ValidationError):
            await validator.validate_async({
                "name": "J",  # Too short
                "age": 30
            })
    
    @pytest.mark.asyncio
    async def test_parallel_validation(self):
        """Test that dict properties are validated in parallel."""
        # Create a validator with deliberate delay
        class DelayedValidator(Validator):
            async def _validate_async(self, data, path):
                await asyncio.sleep(0.1)  # Add delay
                return data
        
        validator = DictValidator({
            "field1": DelayedValidator(),
            "field2": DelayedValidator(),
            "field3": DelayedValidator(),
            "field4": DelayedValidator(),
            "field5": DelayedValidator()
        })
        
        # Validate a dictionary with 5 fields
        start_time = asyncio.get_event_loop().time()
        await validator.validate_async({
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
            "field4": "value4",
            "field5": "value5"
        })
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Should take ~0.1s due to parallel validation, not ~0.5s
        assert elapsed < 0.2, "Dict validation should be parallel"


class TestTupleValidator:
    """Tests for the Tuple validator."""
    
    def test_basic_validation(self, tuple_validator):
        """Test basic tuple validation."""
        # Valid tuples
        assert tuple_validator.validate(("hello", 42, True)) == ("hello", 42, True)
        
        # Tuples from lists
        assert tuple_validator.validate(["hello", 42, True]) == ("hello", 42, True)
        
        # Invalid types
        with pytest.raises(ValidationError):
            tuple_validator.validate(123)
        with pytest.raises(ValidationError):
            tuple_validator.validate("not a tuple")
        with pytest.raises(ValidationError):
            tuple_validator.validate(None)
        
        # Invalid length
        with pytest.raises(ValidationError) as exc_info:
            tuple_validator.validate(("hello", 42))  # Too short
        assert "at least 3 items" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            tuple_validator.validate(("hello", 42, True, "extra"))  # Too long
    
    def test_item_validation(self):
        """Test item validation in tuples."""
        validator = TupleValidator([
            String().min(3),  # First item: string with min length 3
            Number().int().min(0),  # Second item: non-negative integer
            Boolean()  # Third item: boolean
        ])
        
        # Valid tuple
        assert validator.validate(("hello", 42, True)) == ("hello", 42, True)
        
        # Invalid first item
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(("hi", 42, True))  # First item too short
        assert "at least 3 characters" in str(exc_info.value)
        
        # Invalid second item
        with pytest.raises(ValidationError):
            validator.validate(("hello", -5, True))  # Second item negative
        
        with pytest.raises(ValidationError):
            validator.validate(("hello", 3.14, True))  # Second item not an integer
        
        # Invalid third item
        with pytest.raises(ValidationError):
            validator.validate(("hello", 42, "not a boolean"))  # Third item not a boolean
    
    def test_rest_validator(self):
        """Test rest validator for tuples."""
        # Tuple with fixed items and rest validator
        validator = TupleValidator(
            [String(), Number()],  # First two items: string and number
            rest_validator=String().min(3)  # Additional items: strings with min length 3
        )
        
        # Valid tuples (with and without rest items)
        assert validator.validate(("hello", 42)) == ("hello", 42)
        assert validator.validate(("hello", 42, "rest1", "rest2")) == ("hello", 42, "rest1", "rest2")
        
        # Invalid first items
        with pytest.raises(ValidationError):
            validator.validate((123, 42))  # First item wrong type
        
        # Invalid rest items
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(("hello", 42, "ok", "no"))  # Last rest item too short
        assert "at least 3 characters" in str(exc_info.value)
        
        # Invalid rest item type
        with pytest.raises(ValidationError):
            validator.validate(("hello", 42, "ok", 123))  # Last rest item wrong type
    
    def test_min_max_length(self):
        """Test min and max length constraints for tuples with rest validator."""
        # Tuple with rest validator and length constraints
        validator = TupleValidator(
            [String()],  # First item must be string
            rest_validator=Number()  # Additional items must be numbers
        ).min(2).max(4)  # Total length between 2 and 4
        
        # Valid tuples
        assert validator.validate(("hello", 1)) == ("hello", 1)
        assert validator.validate(("hello", 1, 2)) == ("hello", 1, 2)
        assert validator.validate(("hello", 1, 2, 3)) == ("hello", 1, 2, 3)
        
        # Invalid tuples (too short)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(("hello",))  # Only one item
        assert "at least 2 items" in str(exc_info.value)
        
        # Invalid tuples (too long)
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(("hello", 1, 2, 3, 4))  # Five items
        assert "at most 4 items" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation for tuples."""
        validator = TupleValidator([
            String().min(3),
            Number().int().min(0),
            Boolean()
        ])
        
        # Valid tuple
        result = await validator.validate_async(("hello", 42, True))
        assert result == ("hello", 42, True)
        
        # Invalid tuple (item validation fails)
        with pytest.raises(ValidationError):
            await validator.validate_async(("hi", 42, True))  # First item too short
    
    @pytest.mark.asyncio
    async def test_parallel_validation(self):
        """Test that tuple items are validated in parallel."""
        # Create a validator with deliberate delay
        class DelayedValidator(Validator):
            async def _validate_async(self, data, path):
                await asyncio.sleep(0.1)  # Add delay
                return data
        
        validator = TupleValidator([
            DelayedValidator(),
            DelayedValidator(),
            DelayedValidator(),
            DelayedValidator(),
            DelayedValidator()
        ])
        
        # Validate a tuple with 5 items
        start_time = asyncio.get_event_loop().time()
        await validator.validate_async((1, 2, 3, 4, 5))
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Should take ~0.1s due to parallel validation, not ~0.5s
        assert elapsed < 0.2, "Tuple validation should be parallel"


class TestUnionValidator:
    """Tests for the Union validator."""
    
    def test_basic_validation(self, union_validator):
        """Test basic union validation."""
        # Valid values (string)
        assert union_validator.validate("hello") == "hello"
        
        # Valid values (number)
        assert union_validator.validate(42) == 42
        
        # Invalid types
        with pytest.raises(ValidationError) as exc_info:
            union_validator.validate(True)  # Not string or number
        assert "does not match any of the expected types" in str(exc_info.value)
        
        with pytest.raises(ValidationError):
            union_validator.validate(None)
    
    
