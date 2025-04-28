"""
Tests for Object validator and its schema modification features.
"""

import pytest
from voltar.validators import Object, String, Number, ValidationError
from voltar.validators.primitives import Boolean

class TestObjectExtend:
    def test_basic_extension(self):
        base = Object({
            "name": String(),
            "age": Number()
        })
        
        
        extended = base.extend({
            "email": String().email()
        })
        # Original schema should be unchanged
        assert set(base.field_names) == {"name", "age"}
        assert set(extended.field_names) == {"name", "age", "email"}
        
        # Test validation with extended schema
        data = {
            "name": "John",
            "age": 30,
            "email": "john@example.com"
        }
        assert extended.validate(data) == data

    def test_extend_preserves_validation_rules(self):
        base = Object({
            "name": String().min(3),
            "age": Number().min(18)
        })
        
        
        extended = base.extend({
            "email": String().email()
        })
        # Should fail due to name length
        with pytest.raises(ValidationError) as exc_info:
            extended.validate({
                "name": "Jo",  # Too short
                "age": 20,
                "email": "john@example.com"
            })
        assert "name" in str(exc_info.value)
        
        # Should fail due to age minimum
        with pytest.raises(ValidationError) as exc_info:
            extended.validate({
                "name": "John",
                "age": 17,  # Too young
                "email": "john@example.com"
            })
        assert "age" in str(exc_info.value)

    def test_extend_with_conflicts(self):
        base = Object({
            "name": String(),
            "age": Number()
        })
        
        # Should raise error when extending with existing field
        with pytest.raises(ValueError) as exc_info:
            base.extend({"age": Number()})
        assert "conflicting field names" in str(exc_info.value)

class TestObjectExclude:
    def test_basic_exclusion(self):
        schema = Object({
            "name": String(),
            "age": Number(),
            "email": String().email()
        })
        
        excluded = schema.exclude("age", "email")
        
        # Original schema should be unchanged
        assert set(schema.field_names) == {"name", "age", "email"}
        
        # Excluded fields should still be allowed but not validated
        data = {
            "name": "John",
            "age": "invalid",  # Would normally fail Number validation
            "email": "invalid"  # Would normally fail Email validation
        }
        assert excluded.validate(data) == data

    def test_exclude_required_fields(self):
        schema = Object({
            "name": String(),
            "age": Number(),
            "email": String().email()
        })
        
        excluded = schema.exclude("age", "email")
        
        # Should validate with only required non-excluded field
        assert excluded.validate({"name": "John"}) == {"name": "John"}
        
        # Should still validate with excluded fields present
        assert excluded.validate({
            "name": "John",
            "age": "invalid",
            "email": "invalid"
        }) == {
            "name": "John",
            "age": "invalid",
            "email": "invalid"
        }

class TestObjectOmit:
    def test_basic_omission(self):
        schema = Object({
            "name": String(),
            "name": String(),
            "age": Number(),
            "email": String().email()
        })
        without_contact = schema.omit(["age", "email"])
        
        # Original schema should be unchanged
        assert set(schema.field_names) == {"name", "age", "email"}
        # New schema should only have non-omitted fields
        assert set(without_contact.field_names) == {"name"}
        
        # Should validate with only remaining fields
        assert without_contact.validate({"name": "John"}) == {"name": "John"}
        
        
    def test_omit_required_fields(self):
        schema = Object({
            "name": String(),
            "age": Number().optional(),
            "email": String().email()
        })
        
        without_age = schema.omit(["age"])
        
        # Should still require non-omitted required fields
        with pytest.raises(ValidationError) as exc_info:
            without_age.validate({"name": "John"})
        assert "Missing required properties" in str(exc_info.value)
        assert "email" in str(exc_info.value)
        
        # Should validate with all required non-omitted fields
        assert without_age.validate({
            "name": "John",
            "email": "john@example.com"
        }) == {
            "name": "John",
            "email": "john@example.com"
        }

class TestCombinedOperations:
    def test_extend_then_omit(self):
        base = Object({
            "name": String(),
            "age": Number()
        })
        
        
        extended = base.extend({
            "email": String().email(),
            "active": Boolean()
        })
        final = extended.omit(["age", "email"])
        
        # Should have only remaining fields
        assert set(final.field_names) == {"name", "active"}
        
        # Should validate with remaining fields
        assert final.validate({
            "name": "John",
            "active": True
        }) == {
            "name": "John",
            "active": True
        }
        
      

    def test_extend_then_exclude(self):
        base = Object({
            "name": String(),
            "age": Number()
        })
        
        extended = base.extend({
            "email": String().email(),
            "active": Boolean()
        })
        
        final = extended.exclude("age", "email")
        
        # Should validate required fields and ignore excluded ones
        data = {
            "name": "John",
            "active": True,
            "age": "invalid",
            "email": "invalid"
        }
        assert final.validate(data) == data

    def test_exclude_then_extend(self):
        base = Object({
            "name": String(),
            "age": Number()
        }).exclude("age")
        
        extended = base.extend({
            "email": String().email()
        })
        
        # Should preserve excluded fields after extension
        data = {
            "name": "John",
            "age": "invalid",
            "email": "john@example.com"
        }
        assert extended.validate(data) == data

class TestEdgeCases:
    def test_empty_schema(self):
        schema = Object()
        
        # Empty schema should accept any object
        assert schema.validate({"any": "value"}) == {"any": "value"}
        
        # Can still extend empty schema
        extended = schema.extend({"name": String()})
        assert set(extended.field_names) == {"name"}

    def test_omit_nonexistent_fields(self):
        schema = Object({
            "name": String()
        })
        
        # Omitting non-existent fields should not error
        result = schema.omit(["age", "email"])
        assert set(result.field_names) == {"name"}

    def test_exclude_nonexistent_fields(self):
        schema = Object({
            "name": String()
        })
        
        # Excluding non-existent fields should not error
        result = schema.exclude("age", "email")
        assert set(result.field_names) == {"name"}

    def test_nested_objects(self):
        address = Object({
            "street": String(),
            "city": String(),
            "country": String()
        })
        
        user = Object({
            "name": String(),
            "address": address
        })
        
        # Test omitting nested fields
        without_address = user.omit(["address"])
        assert set(without_address.field_names) == {"name"}
        
        # Test excluding nested fields
        excluded_address = user.exclude("address")
        data = {
            "name": "John",
            "address": "invalid"
        }
        assert excluded_address.validate(data) == data

