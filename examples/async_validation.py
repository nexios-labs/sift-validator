"""
Async validation examples for the Sift library.

This example demonstrates:
1. Basic async validation
2. Parallel validation of collections
3. Custom async validators
4. Complex nested async validation
5. Payment processing validation
6. User registration with parallel validation
"""

import sys
import time
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# Add the parent directory to the Python path to import sift
sys.path.insert(0, str(Path(__file__).parent.parent))

from sift import String, Number, Boolean, Object, List, Dict
from sift.validators.base import Validator, ValidationError


# Utility functions for simulating async operations
async def simulate_external_validation(value, delay=0.1):
    """Simulate an external async validation (e.g., database lookup)."""
    await asyncio.sleep(delay)  # Simulate network/database delay
    if isinstance(value, str) and len(value) >= 3:
        return value
    raise ValidationError(f"Value '{value}' failed external validation")


async def simulate_database_query(query, delay=0.2):
    """Simulate a database query."""
    await asyncio.sleep(delay)  # Simulate database delay
    return {"success": True, "result": query}


async def simulate_payment_gateway(card_number, amount, delay=0.5):
    """Simulate a payment gateway authorization."""
    await asyncio.sleep(delay)  # Simulate payment gateway delay
    
    # Reject specific card numbers for testing
    if card_number.startswith("4111"):
        return {"success": False, "error": "Card reported as fraudulent"}
        
    return {"success": True, "transaction_id": f"tx_{hash(card_number + str(amount))}"[-12:]}


# Custom validators
class ExternalValidator(String):
    """Custom validator that uses an external service."""
    
    def __init__(self, delay=0.1):
        super().__init__()
        self._delay = delay
        
    async def _validate_async(self, data, path):
        # First apply the regular string validation
        result = await super()._validate_async(data, path)
        
        # Then apply external validation
        return await simulate_external_validation(result, self._delay)


class AsyncUsernameValidator(String):
    """
    A custom validator that checks if a username is available.
    
    This validator simulates a database lookup with an async operation.
    """
    
    def __init__(self):
        super().__init__()
        self._min_length = 3
        self._pattern = r"^[a-zA-Z0-9_]+$"
        
        # Simulate a database of existing usernames
        self._existing_usernames = {"admin", "user", "test", "system", "moderator"}
        
    async def _validate_async(self, data, path):
        # First apply the regular string validation
        result = await super()._validate_async(data, path)
        
        # Simulate a database lookup
        await asyncio.sleep(0.3)  # Simulate database delay
        
        # Check if username exists
        if result.lower() in self._existing_usernames:
            raise ValidationError(
                self._get_error_message(f"Username '{result}' is already taken"),
                path
            )
            
        return result


class AsyncEmailValidator(String):
    """
    A custom validator that checks if an email domain has valid MX records.
    
    This validator simulates DNS lookups with async operations.
    """
    
    def __init__(self):
        super().__init__()
        self._email = True
        self._invalid_domains = {"example.com", "test.com", "invalid.com"}
        
    async def _validate_async(self, data, path):
        # First apply the regular email validation
        result = await super()._validate_async(data, path)
        
        # Extract domain from email
        domain = result.split("@")[1]
        
        # Simulate checking MX records
        await asyncio.sleep(0.2)  # Simulate DNS lookup delay
        
        # For demo purposes, reject certain domains
        if domain in self._invalid_domains:
            raise ValidationError(
                self._get_error_message(f"Domain '{domain}' has no valid MX records"),
                path
            )
            
        return result


class PaymentValidator(Validator):
    """
    Custom validator for payment information with async payment gateway checks.
    """
    
    def __init__(self):
        super().__init__()
        # Validator for the payment details
        self._payment_schema = Object({
            "cardNumber": String().pattern(r"^\d{16}$").error("Card number must be 16 digits"),
            "expiryDate": String().pattern(r"^\d{2}/\d{2}$").error("Expiry date must be in MM/YY format"),
            "cvv": String().pattern(r"^\d{3}$").error("CVV must be 3 digits"),
            "amount": Number().positive().error("Amount must be positive")
        })
        
        # List of card prefixes that require additional verification
        self._high_risk_prefixes = {"4111", "5555", "3782"}
    
    async def _validate_async(self, data, path):
        # Make sure data is a dictionary
        if not isinstance(data, dict):
            raise ValidationError("Payment data must be an object", path)
            
        # Validate structure using the standard schema
        validated_data = await self._payment_schema._validate_async(data, path)
        
        # Check if card is expired
        try:
            expiry = validated_data["expiryDate"]
            month, year = map(int, expiry.split("/"))
            exp_date = datetime(2000 + year, month, 1)  # Convert to full datetime
            now = datetime.now()
            
            if exp_date.year < now.year or (exp_date.year == now.year and exp_date.month < now.month):
                raise ValidationError("Card is expired", path + ["expiryDate"])
        except (ValueError, IndexError):
            raise ValidationError("Invalid expiry date format", path + ["expiryDate"])
        
        # For high-risk cards, perform additional verification
        card_number = validated_data["cardNumber"]
        prefix = card_number[:4]
        
        if prefix in self._high_risk_prefixes:
            # Simulate payment gateway verification
            gateway_result = await simulate_payment_gateway(
                card_number, 
                validated_data.get("amount", 0),
                delay=0.4
            )
            
            if not gateway_result["success"]:
                raise ValidationError(
                    f"Payment gateway error: {gateway_result.get('error', 'Unknown error')}",
                    path
                )
                
            # Add the transaction ID to the validated data
            validated_data["transactionId"] = gateway_result["transaction_id"]
            
        return validated_data


async def demonstrate_basic_async_validation():
    """Demonstrate basic async validation."""
    print("\n=== Basic Async Validation ===")
    
    # Create a validator with external validation
    validator = ExternalValidator()
    
    try:
        # Valid case
        start = time.time()
        result = await validator.validate_async("hello")
        duration = time.time() - start
        print(f"Valid async validation: {result} (took {duration:.3f}s)")
        
        # Invalid case
        result = await validator.validate_async("hi")
        print(f"Invalid async validation: {result}")
    except ValidationError as e:
        print(f"Async validation error: {e}")


async def demonstrate_parallel_validation():
    """Demonstrate parallel validation of collections."""
    print("\n=== Parallel Validation ===")
    
    # Create a list validator with external validators
    item_validator = ExternalValidator(delay=0.2)
    list_validator = List(item_validator)
    
    data = ["hello", "world", "async", "validation", "example"]
    
    # Measure time for sequential validation
    start = time.time()
    results = []
    for item in data:
        try:
            result = await item_validator.validate_async(item)
            results.append(result)
        except ValidationError:
            results.append(None)
    sequential_time = time.time() - start
    
    print(f"Sequential validation took {sequential_time:.3f}s")
    
    # Measure time for parallel validation
    start = time.time()
    try:
        results = await list_validator.validate_async(data)
        parallel_time = time.time() - start
        print(f"Parallel validation took {parallel_time:.3f}s")
        print(f"Speedup factor: {sequential_time / parallel_time:.2f}x")
    except ValidationError as e:
        print(f"Validation error: {e}")


async def demonstrate_complex_async_validation():
    """Demonstrate complex nested async validation."""
    print("\n=== Complex Nested Async Validation ===")
    
    # Define a complex schema with async validators
    user_schema = Object({
        "username": ExternalValidator(delay=0.1),
        "email": String().email(),
        "profile": Object({
            "bio": String().min(10).max(200),
            "interests": List(ExternalValidator(delay=0.1)).min(2)
        }),
        "posts": List(Object({
            "title": String().min(5).max(100),
            "content": ExternalValidator(delay=0.15),
            "tags": List(String().min(2).max(20))
        }))
    })
    
    # Complex valid data
    valid_data = {
        "username": "johndoe",
        "email": "john@example.com",
        "profile": {
            "bio": "Software developer with 10 years of experience",
            "interests": ["programming", "reading", "hiking"]
        },
        "posts": [
            {
                "title": "Introduction to Async Programming",
                "content": "Async programming is powerful for I/O bound operations",
                "tags": ["programming", "async", "python"]
            },
            {
                "title": "Validation in Modern Applications",
                "content": "Validating data is crucial for application security",
                "tags": ["validation", "security"]
            }
        ]
    }
    
    start = time.time()
    try:
        result = await user_schema.validate_async(valid_data)
        duration = time.time() - start
        print(f"Complex validation successful (took {duration:.3f}s)")
    except ValidationError as e:
        print(f"Validation error: {e}")
    
    # Demonstrate validation failure
    invalid_data = {
        "username": "johndoe",
        "email": "not-an-email",  # Invalid email
        "profile": {
            "bio": "Too short",    # Too short
            "interests": ["only-one"]  # Too few interests
        },
        "posts": []  # Empty posts (which is valid)
    }
    
    try:
        result = await user_schema.validate_async(invalid_data)
        print("Validation successful (unexpected)")
    except ValidationError as e:
        print(f"Expected validation error: {e}")


async def demonstrate_payment_validation():
    """Demonstrate payment validation with async gateway checks."""
    print("\n=== Payment Validation ===")
    
    # Create a payment validator
    payment_validator = PaymentValidator()
    
    # Valid payment data
    valid_payment = {
        "cardNumber": "5105105105105100",
        "expiryDate": "12/30",
        "cvv": "123",
        "amount": 99.99
    }
    
    print("Validating valid payment:")
    start = time.time()
    try:
        result = await payment_validator.validate_async(valid_payment)
        duration = time.time() - start
        print(f"  Valid payment validated (took {duration:.3f}s)")
        print(f"  Result: {result}")
    except ValidationError as e:
        print(f"  Unexpected error: {e}")
    
    # Fraudulent payment data (using a known bad card number)
    fraudulent_payment = {
        "cardNumber": "4111111111111111",
        "expiryDate": "12/30",
        "cvv": "123",
        "amount": 999.99
    }
    
    print("\nValidating fraudulent payment:")
    start = time.time()
    try:
        result = await payment_validator.validate_async(fraudulent_payment)
        duration = time.time() - start
        print(f"  Unexpected success: {result}")
    except ValidationError as e:
        duration = time.time() - start
        print(f"  Expected error: {e}")
        print(f"  Detection took: {duration:.3f}s")
    
    # Expired card
    expired_payment = {
        "cardNumber": "5555555555554444",
        "expiryDate": "01/20",  # Expired date
        "cvv": "123",
        "amount": 50.00
    }
    
    print("\nValidating expired card:")
    try:
        result = await payment_validator.validate_async(expired_payment)
        print(f"  Unexpected success: {result}")
    except ValidationError as e:
        print(f"  Expected error: {e}")


async def demonstrate_user_registration():
    """Demonstrate user registration with parallel validation of fields."""
    print("\n=== User Registration Validation ===")
    
    # Define an address schema
    address_schema = Object({
        "street": String().min(5),
        "city": String().min(2),
        "postalCode": String().pattern(r"^\d{5}(-\d{4})?$"),
        "country": String().min(2).max(2)
    })
    
    # Define a user schema with multiple async validators
    user_schema = Object({
        "username": AsyncUsernameValidator(),
        "email": AsyncEmailValidator(),
        "password": String().min(8).pattern(r".*[A-Z].*").pattern(r".*[0-9].*")
            .error("Password must be at least 8 characters with at least one uppercase letter and one number"),
        "profile": Object({
            "fullName": String().min(3),
            "birthdate": String().pattern(r"^\d{4}-\d{2}-\d{2}$"),
            "bio": String().optional()
        }),
        "address": address_schema,
        "preferences": Dict().pattern_property(r"^pref_", String()),
        "payment": PaymentValidator()
    })
    
    # Complete valid user data
    valid_user = {
        "username": "johndoe2023",
        "email": "john.doe@gmail.com",
        "password": "SecurePass123",
        "profile": {
            "fullName": "John Doe",
            "birthdate": "1990-01-01",
            "bio": "Software developer and tech enthusiast"
        },
        "address": {
            "street": "123 Main Street",
            "city": "Anytown",
            "postalCode": "12345",
            "country": "US"
        },
        "preferences": {
            "pref_theme": "dark",
            "pref_notifications": "email"
        },
        "payment": {
            "cardNumber": "5105105105105100",
            "expiryDate": "12/30",
            "cvv": "123",
            "amount": 0
        }
    }
    
    print("Validating complete user registration:")
    start = time.time()
    try:
        result = await user_schema.validate_async(valid_user)
        duration = time.time() - start
        print(f"  Valid registration processed in {duration:.3f}s")
        print(f"  Username: {result['username']}")
        print(f"  Email: {result['email']}")
    except ValidationError as e:
        print(f"  Unexpected error: {e}")
    
    # Invalid user data with multiple errors
    invalid_user = {
        "username": "admin",  # Existing username
        "email": "user@example.com",  # Invalid domain
        "password": "weak",  # Too short, missing uppercase and number
        "profile": {
            "fullName": "A",  # Too short
            "birthdate": "01/01/1990"  # Wrong format, should be YYYY-MM-DD
            # Missing bio (but it's optional)
        },
        "address": {
            "street": "St",  # Too short
            "city": "A",  # Too short
            "postalCode": "ABC",  # Not a valid postal code format
            "country": "USA"  # Should be 2 characters
        },
        "preferences": {
            "theme": "dark",  # Missing pref_ prefix
            "pref_invalid": 123  # Should be string
        },
        "payment": {
            "cardNumber": "5555555555554444",
            "expiryDate": "01/20",  # Expired
            "cvv": "12",  # Too short
            "amount": -10.00  # Negative amount
        }
    }
    
    print("\nValidating user with multiple errors:")
    start = time.time()
    
    # Collect all errors instead of stopping at the first one
    all_errors = []
    
    try:
        result = await user_schema.validate_async(invalid_user)
        print("  Unexpected success - validation should have failed")
    except ValidationError as e:
        duration = time.time() - start
        print(f"  Validation failed as expected (in {duration:.3f}s)")
        print("  Error:", e)
    
    # Now let's attempt to collect all errors by validating each field separately
    print("\nDetailed field-by-field validation errors:")
    field_errors = {}
    field_timings = {}
    
    # Validate each top-level field separately to collect all errors
    for field, field_schema in user_schema._schema.items():
        if field in invalid_user:
            field_start = time.time()
            try:
                await field_schema.validate_async(invalid_user[field])
                print(f"  {field}: Valid (unexpected)")
            except ValidationError as e:
                field_duration = time.time() - field_start
                field_errors[field] = str(e)
                field_timings[field] = field_duration
                print(f"  {field}: {e} ({field_duration:.3f}s)")
        else:
            print(f"  {field}: Missing")
            field_errors[field] = "Field is required"
    
    # Validation summary
    print("\nValidation Summary:")
    print(f"  Total fields with errors: {len(field_errors)}")
    print(f"  Fields with async validation: username, email, payment")
    
    # Calculate total sequential vs. parallel time
    sequential_time = sum(field_timings.values())
    print(f"  Sequential validation would take: {sequential_time:.3f}s")
    print(f"  Parallel validation took: {duration:.3f}s")
    print(f"  Speedup factor: {sequential_time / duration:.2f}x")
    
    # Explanation of benefits
    print("\nBenefits of parallel validation:")
    print("  1. Faster validation for complex objects with multiple async validators")
    print("  2. Better user experience by collecting all errors at once")
    print("  3. Efficient resource utilization during I/O-bound validation operations")


async def main():
    await demonstrate_basic_async_validation()
    await demonstrate_parallel_validation()
    await demonstrate_complex_async_validation()
    await demonstrate_payment_validation()
    await demonstrate_user_registration()


if __name__ == "__main__":
    asyncio.run(main())
