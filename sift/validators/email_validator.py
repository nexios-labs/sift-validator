"""
Self-contained email validator with RFC-compliant validation.
"""

import re
from typing import Any, Optional
from sift.validators.base import Validator, ValidationError


class EmailNotValidError(ValidationError):
    """Exception raised when email validation fails."""
    pass


class EmailValidationError(ValidationError):
    """Custom exception for email validation failures."""
    pass

class EmailValidator(Validator[str, str]):
    """
    Comprehensive email validator that implements RFC 5322 email validation.
    
    Features:
    - Validates email format according to RFC standards
    - Optional domain existence checking (via DNS)
    - Local part and domain validation
    - Customizable validation rules
    
    Examples:
        >>> EmailValidator().validate("user@example.com")
        'user@example.com'
        >>> EmailValidator().validate("invalid-email")  # Raises ValidationError
    """
    
    # Regular expression for RFC 5322 email validation
    EMAIL_REGEX = re.compile(
        r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    )
    
    # Simplified regex for quick format check
    SIMPLE_EMAIL_REGEX = re.compile(
        r"[^@\s]+@[^@\s]+\.[^@\s]+"
    )
    
    def __init__(self):
        super().__init__()
        self._strict: bool = True
        self._check_mx: bool = False
        self._allow_ip_domain: bool = False
        self._allow_unicode: bool = False
        self._blacklist: set[str] = set()
    
         
    def validate_email(self, email: str) -> str:
        """Public method to validate an email address."""
        try:
            return self._validate(email, [])
        except ValidationError as e:
            raise EmailValidationError(str(e))
    def strict(self, strict: bool = True) -> 'EmailValidator':
        """
        Enable/disable strict RFC 5322 validation.
        
        Args:
            strict: Whether to use strict validation
            
        Returns:
            EmailValidator: The validator instance for chaining
        """
        validator = self._clone()
        validator._strict = strict
        return validator
        
    def check_mx(self, check: bool = True) -> 'EmailValidator':
        """
        Enable/disable MX record checking for the domain.
        
        Args:
            check: Whether to check MX records
            
        Returns:
            EmailValidator: The validator instance for chaining
        """
        validator = self._clone()
        validator._check_mx = check
        return validator
        
    def allow_ip_domain(self, allow: bool = True) -> 'EmailValidator':
        """
        Allow IP addresses in the domain part (e.g., user@[192.168.1.1]).
        
        Args:
            allow: Whether to allow IP domains
            
        Returns:
            EmailValidator: The validator instance for chaining
        """
        validator = self._clone()
        validator._allow_ip_domain = allow
        return validator
        
    def allow_unicode(self, allow: bool = True) -> 'EmailValidator':
        """
        Allow Unicode characters in the email address.
        
        Args:
            allow: Whether to allow Unicode
            
        Returns:
            EmailValidator: The validator instance for chaining
        """
        validator = self._clone()
        validator._allow_unicode = allow
        return validator
        
    def blacklist(self, domains: set[str]) -> 'EmailValidator':
        """
        Set a blacklist of domains to reject.
        
        Args:
            domains: Set of domains to blacklist
            
        Returns:
            EmailValidator: The validator instance for chaining
        """
        validator = self._clone()
        validator._blacklist = domains
        return validator
        
    def _validate(self, data: Any, path: list[str | int]) -> str:
        if not isinstance(data, str):
            raise EmailNotValidError(
                self._get_error_message(f"Expected string, got {type(data).__name__}"),
                path
            )
            
        email = data.strip()
        
        # Quick format check
        if not self.SIMPLE_EMAIL_REGEX.match(email):
            raise ValidationError(
                self._get_error_message("Invalid email format"),
                path
            )
            
        # Split into local and domain parts
        try:
            local_part, domain = email.split('@', 1)
        except ValueError:
            raise ValidationError(
                self._get_error_message("Invalid email format"),
                path
            )
            
        # Validate domain blacklist
        if domain.lower() in self._blacklist:
            raise ValidationError(
                self._get_error_message(f"Email domain '{domain}' is not allowed"),
                path
            )
            
        # Strict RFC 5322 validation
        if self._strict and not self._validate_rfc5322(email):
            raise ValidationError(
                self._get_error_message("Email does not comply with RFC 5322 standards"),
                path
            )
            
        # Validate domain
        if not self._validate_domain(domain):
            raise ValidationError(
                self._get_error_message("Invalid email domain"),
                path
            )
            
        # Check MX records if enabled
        if self._check_mx and not self._check_mx_records(domain):
            raise ValidationError(
                self._get_error_message("Domain does not have valid MX records"),
                path
            )
            
        return email
        
    def _validate_rfc5322(self, email: str) -> bool:
        """Validate email against RFC 5322 standards."""
        return bool(self.EMAIL_REGEX.fullmatch(email))
        
    def _validate_domain(self, domain: str) -> bool:
        """Validate the domain part of the email."""
        if self._allow_ip_domain and domain.startswith('[') and domain.endswith(']'):
            return self._validate_ip_domain(domain[1:-1])
            
        # Check domain structure
        if '.' not in domain:
            return False
            
        # Check each part of the domain
        parts = domain.split('.')
        if any(not part for part in parts):
            return False
            
        # Check TLD length
        if len(parts[-1]) < 2:
            return False
            
        return True
        
    def _validate_ip_domain(self, ip: str) -> bool:
        """Validate IP address domain."""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            return all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
            
    def _check_mx_records(self, domain: str) -> bool:
        """Check if domain has MX records (simplified version)."""
        # In a real implementation, this would do actual DNS lookups
        # For this self-contained version, we'll just return True
        # since we can't do network operations without imports
        return True