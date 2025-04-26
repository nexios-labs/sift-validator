"""
Collection validators for complex data structures.

This module provides validators for collection types like lists, 
dictionaries, tuples, etc.
"""

import asyncio
from typing import Any, Callable, Dict as DictType, Generic, List as ListType, Literal, Mapping, Optional, Set
from typing import Tuple as TupleType, Type, TypeVar, Union, cast, overload, get_args, get_origin, Self, get_type_hints
import re
from collections.abc import Sequence
import inspect

from sift.validators.base import Validator, ValidationError

T = TypeVar("T")
R = TypeVar("R")
ItemType = TypeVar("ItemType")

class List(Validator[ListType[Any], ListType[ItemType]]):
    """
    Validator for list/array values.
    
    Examples:
        >>> from sift.validators.primitives import String
        >>> List(String()).validate(["hello", "world"])
        ['hello', 'world']
        >>> List(String()).min(3).validate(["a", "b"])  # Raises ValidationError
    """
    
    def __init__(self, item_validator: Optional[Validator] = None):
        """
        Initialize list validator with optional item validator.
        
        Args:
            item_validator: Validator to apply to each item in the list.
                If None, any values are accepted.
        """
        super().__init__()
        self._item_validator = item_validator
        self._min_length: Optional[int] = None
        self._max_length: Optional[int] = None
        self._unique: bool = False
        self._nonempty: bool = False
        
    def min(self, length: int) -> Self:
        """
        Set minimum list length.
        
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
        Set maximum list length.
        
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
        Set exact list length.
        
        Args:
            length: Exact required length
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._min_length = length
        validator._max_length = length
        return validator
        
    def unique(self) -> Self:
        """
        Require all items in the list to be unique.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._unique = True
        return validator
        
    def nonempty(self) -> Self:
        """
        Require the list to have at least one item.
        
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._nonempty = True
        return validator
        
    def _validate(self, data: Any, path: list[str | int]) -> ListType[ItemType]:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(ListType[ItemType], None)
            
        if not isinstance(data, (list, tuple)):
            raise ValidationError(
                self._get_error_message(f"Expected list, got {type(data).__name__}"),
                path
            )
            
        result = list(data)
            
        if self._nonempty and not result:
            raise ValidationError(
                self._get_error_message("List cannot be empty"),
                path
            )
            
        if self._min_length is not None and len(result) < self._min_length:
            raise ValidationError(
                self._get_error_message(f"List must have at least {self._min_length} items"),
                path
            )
            
        if self._max_length is not None and len(result) > self._max_length:
            raise ValidationError(
                self._get_error_message(f"List must have at most {self._max_length} items"),
                path
            )
            
        if self._unique:
            # Try to use set to check uniqueness, but handle unhashable types
            try:
                if len(set(result)) != len(result):
                    raise ValidationError(
                        self._get_error_message("List items must be unique"),
                        path
                    )
            except TypeError:
                # Fall back to manual uniqueness check for unhashable types
                seen = []
                for item in result:
                    for seen_item in seen:
                        if item == seen_item:
                            raise ValidationError(
                                self._get_error_message("List items must be unique"),
                                path
                            )
                    seen.append(item)
            
        # Validate each item if item validator is provided
        if self._item_validator:
            for i, item in enumerate(result):
                item_path = path + [i]
                result[i] = self._item_validator._validate(item, item_path)
                
        return cast(ListType[ItemType], result)
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> ListType[ItemType]:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(ListType[ItemType], None)
            
        if not isinstance(data, (list, tuple)):
            raise ValidationError(
                self._get_error_message(f"Expected list, got {type(data).__name__}"),
                path
            )
            
        result = list(data)
            
        if self._nonempty and not result:
            raise ValidationError(
                self._get_error_message("List cannot be empty"),
                path
            )
            
        if self._min_length is not None and len(result) < self._min_length:
            raise ValidationError(
                self._get_error_message(f"List must have at least {self._min_length} items"),
                path
            )
            
        if self._max_length is not None and len(result) > self._max_length:
            raise ValidationError(
                self._get_error_message(f"List must have at most {self._max_length} items"),
                path
            )
            
        if self._unique:
            # Try to use set to check uniqueness, but handle unhashable types
            try:
                if len(set(result)) != len(result):
                    raise ValidationError(
                        self._get_error_message("List items must be unique"),
                        path
                    )
            except TypeError:
                # Fall back to manual uniqueness check for unhashable types
                seen = []
                for item in result:
                    for seen_item in seen:
                        if item == seen_item:
                            raise ValidationError(
                                self._get_error_message("List items must be unique"),
                                path
                            )
                    seen.append(item)
            
        # Validate each item if item validator is provided
        if self._item_validator:
            # Validate all items in parallel for better performance
            tasks = []
            for i, item in enumerate(result):
                item_path = path + [i]
                # Create a task for each item validation
                tasks.append(
                    asyncio.create_task(
                        self._item_validator._validate_async(item, item_path)
                    )
                )
                
            # Wait for all validations to complete
            if tasks:
                validated_items = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions and raise the first one encountered
                for i, item in enumerate(validated_items):
                    if isinstance(item, Exception):
                        if isinstance(item, ValidationError):
                            raise item
                        else:
                            raise ValidationError(
                                self._get_error_message(f"Item validation failed: {str(item)}"),
                                path + [i]
                            )
                    else:
                        result[i] = item
                
        return cast(ListType[ItemType], result)


class Dict(Validator[DictType[Any, Any], DictType[Any, Any]]):
    """
    Validator for dictionary values.
    
    Examples:
        >>> from sift.validators.primitives import String, Number
        >>> Dict({"name": String(), "age": Number().int()}).validate({"name": "John", "age": 30})
        {'name': 'John', 'age': 30}
    """
    
    def __init__(self, schema: Optional[DictType[str, Validator]] = None):
        """
        Initialize dictionary validator with optional schema.
        
        Args:
            schema: A dictionary mapping keys to their validators.
                If None, any key-value pairs are accepted.
        """
        super().__init__()
        self._schema = schema or {}
        self._additional_properties: Union[bool, Validator] = True
        self._pattern_properties: DictType[str, Validator] = {}
        self._min_properties: Optional[int] = None
        self._max_properties: Optional[int] = None
        
        # Set required keys from schema by default
        # Only fields that are neither optional nor nullable are required
        self._required_keys = set()
        if schema:
            for key, validator in schema.items():
                if not validator._optional and not validator._nullable:
                    self._required_keys.add(key)
        
    def additional_properties(self, allowed: Union[bool, Validator]) -> Self:
        """
        Control whether additional properties are allowed.
        
        Args:
            allowed: True to allow any additional properties, False to disallow any,
                or a Validator to validate all additional properties.
                
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._additional_properties = allowed
        return validator
        
    def pattern_property(self, pattern: str, validator: Validator) -> Self:
        """
        Add a pattern property validator.
        
        Any property whose key matches the pattern will be validated against
        the provided validator.
        
        Args:
            pattern: Regular expression pattern for matching property keys
            validator: Validator for matching properties
            
        Returns:
            Self: The validator instance for chaining
        """
        validator_clone = self._clone()
        pattern_properties = dict(validator_clone._pattern_properties)
        pattern_properties[pattern] = validator
        validator_clone._pattern_properties = pattern_properties
        return validator_clone
        
    def required(self, *keys: str) -> Self:
        """
        Specify which keys are required.
        
        This overrides the default behavior where all schema keys are required.
        
        Args:
            *keys: Required key names
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._required_keys = set(keys)
        return validator
        
    def min_properties(self, count: int) -> Self:
        """
        Set minimum number of properties.
        
        Args:
            count: Minimum number of properties
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._min_properties = count
        return validator
        
    def max_properties(self, count: int) -> Self:
        """
        Set maximum number of properties.
        
        Args:
            count: Maximum number of properties
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._max_properties = count
        return validator
        
    def _validate(self, data: Any, path: list[str | int]) -> DictType[Any, Any]:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(DictType[Any, Any], None)
            
        if not isinstance(data, dict):
            raise ValidationError(
                self._get_error_message(f"Expected object/dict, got {type(data).__name__}"),
                path
            )
            
        result = dict(data)
            
        # Check property count constraints
        if self._min_properties is not None and len(result) < self._min_properties:
            raise ValidationError(
                self._get_error_message(f"Object must have at least {self._min_properties} properties"),
                path
            )
            
        if self._max_properties is not None and len(result) > self._max_properties:
            raise ValidationError(
                self._get_error_message(f"Object must have at most {self._max_properties} properties"),
                path
            )
            
        # Check required keys
        missing_keys = self._required_keys - set(result.keys())
        if missing_keys:
            missing_keys_str = ", ".join(missing_keys)
            raise ValidationError(
                self._get_error_message(f"Missing required properties: {missing_keys_str}"),
                path
            )
            
        # Track keys that have been validated
        validated_keys = set()
            
        # Validate schema properties
        for key, validator in self._schema.items():
            if key in result:
                item_path = path + [key]
                result[key] = validator._validate(result[key], item_path)
                validated_keys.add(key)
                
        # Validate pattern properties
        for pattern_str, validator in self._pattern_properties.items():
            pattern = re.compile(pattern_str)
            for key in result.keys():
                if isinstance(key, str) and pattern.match(key):
                    item_path = path + [key]
                    result[key] = validator._validate(result[key], item_path)
                    validated_keys.add(key)
                    
        # Handle additional properties
        unvalidated_keys = set(result.keys()) - validated_keys
        if unvalidated_keys:
            if self._additional_properties is False:
                unexpected_keys_str = ", ".join(str(k) for k in unvalidated_keys)
                raise ValidationError(
                    self._get_error_message(f"Unexpected additional properties: {unexpected_keys_str}"),
                    path
                )
                
            if isinstance(self._additional_properties, Validator):
                for key in unvalidated_keys:
                    item_path = path + [key]
                    result[key] = self._additional_properties._validate(result[key], item_path)
                    
        return result
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> DictType[Any, Any]:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(DictType[Any, Any], None)
            
        if not isinstance(data, dict):
            raise ValidationError(
                self._get_error_message(f"Expected object/dict, got {type(data).__name__}"),
                path
            )
            
        result = dict(data)
            
        # Check property count constraints
        if self._min_properties is not None and len(result) < self._min_properties:
            raise ValidationError(
                self._get_error_message(f"Object must have at least {self._min_properties} properties"),
                path
            )
            
        if self._max_properties is not None and len(result) > self._max_properties:
            raise ValidationError(
                self._get_error_message(f"Object must have at most {self._max_properties} properties"),
                path
            )
            
        # Check required keys
        missing_keys = self._required_keys - set(result.keys())
        if missing_keys:
            missing_keys_str = ", ".join(missing_keys)
            raise ValidationError(
                self._get_error_message(f"Missing required properties: {missing_keys_str}"),
                path
            )
            
        # Track keys that have been validated
        validated_keys = set()
            
        # Create tasks for all validations
        validation_tasks = []
        validation_keys = []
        
        # Schema property validations
        for key, validator in self._schema.items():
            if key in result:
                item_path = path + [key]
                validation_tasks.append(
                    asyncio.create_task(
                        validator._validate_async(result[key], item_path)
                    )
                )
                validation_keys.append(key)
                validated_keys.add(key)

        # Pattern property validations
        pattern_validations = []  # [(key, task)] pairs for pattern properties
        for pattern_str, validator in self._pattern_properties.items():
            pattern = re.compile(pattern_str)
            for key in result.keys():
                if key not in validated_keys and isinstance(key, str) and pattern.match(key):
                    item_path = path + [key]
                    task = asyncio.create_task(
                        validator._validate_async(result[key], item_path)
                    )
                    pattern_validations.append((key, task))
                    validated_keys.add(key)

        # Additional property validations
        additional_validations = []  # [(key, task)] pairs for additional properties
        if isinstance(self._additional_properties, Validator):
            unvalidated_keys = set(result.keys()) - validated_keys
            for key in unvalidated_keys:
                item_path = path + [key]
                task = asyncio.create_task(
                    self._additional_properties._validate_async(result[key], item_path)
                )
                additional_validations.append((key, task))

        # Process schema validation results
        if validation_tasks:
            validated_values = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Update result dict with validated values
            for i, (key, value) in enumerate(zip(validation_keys, validated_values)):
                if isinstance(value, Exception):
                    if isinstance(value, ValidationError):
                        raise value
                    else:
                        raise ValidationError(
                            self._get_error_message(f"Property validation failed: {str(value)}"),
                            path + [key]
                        )
                else:
                    result[key] = value

        # Process pattern validation results
        for key, task in pattern_validations:
            try:
                result[key] = await task
            except ValidationError as e:
                raise e
            except Exception as e:
                raise ValidationError(
                    self._get_error_message(f"Pattern property validation failed: {str(e)}"),
                    path + [key]
                )

        # Process additional property validation results
        for key, task in additional_validations:
            try:
                result[key] = await task
            except ValidationError as e:
                raise e
            except Exception as e:
                raise ValidationError(
                    self._get_error_message(f"Additional property validation failed: {str(e)}"),
                    path + [key]
                )

        # Check for unexpected properties
        unvalidated_keys = set(result.keys()) - validated_keys
        if unvalidated_keys and self._additional_properties is False:
            unexpected_keys_str = ", ".join(str(k) for k in unvalidated_keys)
            raise ValidationError(
                self._get_error_message(f"Unexpected additional properties: {unexpected_keys_str}"),
                path
            )
                    
        return result


class Tuple(Validator[TupleType, TupleType]):
    """
    Validator for tuple values with position-based validation.
    
    Examples:
        >>> from sift.validators.primitives import String, Number
        >>> Tuple([String(), Number().int()]).validate(("hello", 42))
        ('hello', 42)
        >>> Tuple([String(), Number().int()]).validate(("hello", "world"))  # Raises ValidationError
    """
    
    def __init__(self, item_validators: list[Validator], rest_validator: Optional[Validator] = None):
        """
        Initialize tuple validator with position-based item validators.
        
        Args:
            item_validators: List of validators, one for each position in the tuple
            rest_validator: Optional validator for additional items beyond defined positions
        """
        super().__init__()
        self._item_validators = item_validators
        self._rest_validator = rest_validator
        self._min_length: Optional[int] = len(item_validators)
        self._max_length: Optional[int] = None if rest_validator else len(item_validators)
        
    def min(self, length: int) -> Self:
        """
        Set minimum tuple length.
        
        Args:
            length: Minimum allowed length
            
        Returns:
            Self: The validator instance for chaining
        """
        validator = self._clone()
        validator._min_length = max(length, len(self._item_validators))
        return validator
        
    def max(self, length: int) -> Self:
        """
        Set maximum tuple length.
        
        This applies only when a rest_validator is provided.
        
        Args:
            length: Maximum allowed length
            
        Returns:
            Self: The validator instance for chaining
        """
        if self._rest_validator is None:
            raise ValueError("Cannot set max length without a rest validator")
        
        validator = self._clone()
        validator._max_length = length
        return validator
        
    def _validate(self, data: Any, path: list[str | int]) -> TupleType:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(TupleType, None)
            
        if not isinstance(data, (list, tuple)):
            raise ValidationError(
                self._get_error_message(f"Expected tuple, got {type(data).__name__}"),
                path
            )
            
        result = list(data)  # Convert to list for easier manipulation
        
        # Check length constraints
        if len(result) < self._min_length:
            raise ValidationError(
                self._get_error_message(f"Tuple must have at least {self._min_length} items"),
                path
            )
            
        if self._max_length is not None and len(result) > self._max_length:
            raise ValidationError(
                self._get_error_message(f"Tuple must have at most {self._max_length} items"),
                path
            )
            
        # Validate fixed position items
        for i, validator in enumerate(self._item_validators):
            if i < len(result):
                item_path = path + [i]
                result[i] = validator._validate(result[i], item_path)
            else:
                # This should not happen if min_length is enforced correctly
                raise ValidationError(
                    self._get_error_message(f"Missing item at position {i}"),
                    path
                )
                
        # Validate rest items with rest_validator if provided
        if self._rest_validator and len(result) > len(self._item_validators):
            for i in range(len(self._item_validators), len(result)):
                item_path = path + [i]
                result[i] = self._rest_validator._validate(result[i], item_path)
                
        return tuple(result)  # Convert back to tuple
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> TupleType:
        # Check for nullable fields
        if data is None and self._nullable:
            return cast(TupleType, None)
            
        if not isinstance(data, (list, tuple)):
            raise ValidationError(
                self._get_error_message(f"Expected tuple, got {type(data).__name__}"),
                path
            )
            
        result = list(data)  # Convert to list for easier manipulation
        
        # Check length constraints
        if len(result) < self._min_length:
            raise ValidationError(
                self._get_error_message(f"Tuple must have at least {self._min_length} items"),
                path
            )
            
        if self._max_length is not None and len(result) > self._max_length:
            raise ValidationError(
                self._get_error_message(f"Tuple must have at most {self._max_length} items"),
                path
            )
            
        # Prepare tasks for asynchronous validation
        validation_tasks = []
        
        # Tasks for fixed position items
        for i, validator in enumerate(self._item_validators):
            if i < len(result):
                item_path = path + [i]
                validation_tasks.append(
                    (i, asyncio.create_task(validator._validate_async(result[i], item_path)))
                )
            else:
                # This should not happen if min_length is enforced correctly
                raise ValidationError(
                    self._get_error_message(f"Missing item at position {i}"),
                    path
                )
                
        # Tasks for rest items
        if self._rest_validator and len(result) > len(self._item_validators):
            for i in range(len(self._item_validators), len(result)):
                item_path = path + [i]
                validation_tasks.append(
                    (i, asyncio.create_task(self._rest_validator._validate_async(result[i], item_path)))
                )
                
        # Process validation results
        for i, task in validation_tasks:
            try:
                result[i] = await task
            except ValidationError as e:
                raise e
            except Exception as e:
                raise ValidationError(
                    self._get_error_message(f"Item validation failed at position {i}: {str(e)}"),
                    path + [i]
                )
                
        return tuple(result)  # Convert back to tuple


class Union(Validator[Any, Any]):
    """
    Validator that accepts values matching any of the provided validators.
    
    Examples:
        >>> from sift.validators.primitives import String, Number
        >>> Union([String(), Number()]).validate("hello")
        'hello'
        >>> Union([String(), Number()]).validate(42)
        42
        >>> Union([String(), Number()]).validate(True)  # Raises ValidationError
    """
    
    def __init__(self, validators: list[Validator], discriminator: Optional[str] = None):
        """
        Initialize union validator with a list of possible validators.
        
        Args:
            validators: List of validators to try
            discriminator: Optional field name used to determine which validator to use
        """
        super().__init__()
        self._validators = validators
        self._discriminator = discriminator
        self._discriminator_map: DictType[Any, Validator] = {}
        
    def discriminator_mapping(self, mapping: DictType[Any, Validator]) -> Self:
        """
        Set a mapping from discriminator values to validators.
        
        This allows more efficient validation by checking the discriminator field
        and using the specific validator for that value.
        
        Args:
            mapping: Dictionary mapping discriminator values to validators
            
        Returns:
            Self: The validator instance for chaining
        """
        if not self._discriminator:
            raise ValueError("Cannot set discriminator mapping without a discriminator field")
            
        validator = self._clone()
        validator._discriminator_map = dict(mapping)
        return validator

    def _validate(self, data: Any, path: list[str | int]) -> Any:
        # If discriminator is provided and data is a dict with that field,
        # use the specific validator for that discriminator value
        if (
            self._discriminator and 
            isinstance(data, dict) and 
            self._discriminator in data and
            self._discriminator_map
        ):
            discriminator_value = data[self._discriminator]
            if discriminator_value in self._discriminator_map:
                return self._discriminator_map[discriminator_value]._validate(data, path)
                
        # Try each validator in turn
        errors = []
        for i, validator in enumerate(self._validators):
            try:
                return validator._validate(data, path)
            except ValidationError as e:
                errors.append(f"Option {i+1}: {str(e)}")
                
        # If all validators failed, raise an error with all validation errors
        raise ValidationError(
            self._get_error_message(f"Value does not match any of the expected types:\n" + "\n".join(errors)),
            path
        )
        
    async def _validate_async(self, data: Any, path: list[str | int]) -> Any:
        # If discriminator is provided and data is a dict with that field,
        # use the specific validator for that discriminator value
        if (
            self._discriminator and 
            isinstance(data, dict) and 
            self._discriminator in data and
            self._discriminator_map
        ):
            discriminator_value = data[self._discriminator]
            if discriminator_value in self._discriminator_map:
                return await self._discriminator_map[discriminator_value]._validate_async(data, path)
        
        # Without a matching discriminator, try all validators (potentially in parallel)
        # We'll collect all errors to provide comprehensive feedback if validation fails
        tasks = []
        for validator in self._validators:
            # Create a task for each validation attempt
            tasks.append(
                asyncio.create_task(
                    self._try_validate_async(validator, data, path)
                )
            )
        
        # Wait for all validation attempts to complete
        results = await asyncio.gather(*tasks)
        
        # Process results - look for the first success
        errors = []
        for i, (success, result) in enumerate(results):
            if success:
                return result
            errors.append(f"Option {i+1}: {result}")
            
        # If all validators failed, raise an error with all validation errors
        raise ValidationError(
            self._get_error_message(f"Value does not match any of the expected types:\n" + "\n".join(errors)),
            path
        )
    
    async def _try_validate_async(self, validator: Validator, data: Any, path: list[str | int]) -> tuple[bool, Any]:
        """
        Try to validate data with a validator, returning success status and result/error.
        
        Args:
            validator: The validator to try
            data: The data to validate
            path: The validation path
            
        Returns:
            Tuple of (success, result_or_error)
        """
        try:
            result = await validator._validate_async(data, path)
            return True, result
        except ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
