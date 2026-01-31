"""
Validation Module for Backend Operations Agent
===============================================
A framework-agnostic validation module for API request payloads.
Provides structured validation results with missing field detection.
"""

from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Type Definitions
# ============================================================================

class FieldType(Enum):
    """Supported field types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    EMAIL = "email"
    URL = "url"
    ANY = "any"


@dataclass
class ValidationResult:
    """Structured validation result"""
    is_valid: bool
    missing_fields: List[str]
    message: str
    invalid_fields: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "is_valid": self.is_valid,
            "missing_fields": self.missing_fields,
            "message": self.message
        }
        if self.invalid_fields:
            result["invalid_fields"] = self.invalid_fields
        return result


@dataclass
class FieldSchema:
    """Schema definition for a field"""
    name: str
    required: bool = True
    field_type: FieldType = FieldType.ANY
    validator: Optional[Callable[[Any], bool]] = None
    default: Any = None
    description: str = ""


# ============================================================================
# Validator Class
# ============================================================================

class PayloadValidator:
    """
    Validates incoming API request payloads against defined schemas.
    
    Framework-agnostic and reusable across different backend systems.
    """
    
    def __init__(self, schema: List[FieldSchema]):
        """
        Initialize validator with a schema.
        
        Args:
            schema: List of FieldSchema objects defining expected fields
        """
        self.schema = schema
        self.required_fields = {field.name for field in schema if field.required}
        self.all_fields = {field.name: field for field in schema}
    
    def validate(self, payload: Dict[str, Any]) -> ValidationResult:
        """
        Validate a payload against the schema.
        
        Args:
            payload: Dictionary containing the request payload
            
        Returns:
            ValidationResult with validation status and details
        """
        # Check for missing required fields
        missing_fields = self._check_missing_fields(payload)
        
        # Check field types and custom validators
        invalid_fields = self._check_field_validity(payload)
        
        # Determine overall validity
        is_valid = len(missing_fields) == 0 and len(invalid_fields) == 0
        
        # Generate message
        message = self._generate_message(is_valid, missing_fields, invalid_fields)
        
        return ValidationResult(
            is_valid=is_valid,
            missing_fields=missing_fields,
            message=message,
            invalid_fields=invalid_fields if invalid_fields else None
        )
    
    def _check_missing_fields(self, payload: Dict[str, Any]) -> List[str]:
        """
        Check for missing required fields.
        
        Args:
            payload: Request payload
            
        Returns:
            List of missing required field names
        """
        payload_keys = set(payload.keys())
        missing = list(self.required_fields - payload_keys)
        return sorted(missing)
    
    def _check_field_validity(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Check validity of present fields (type and custom validation).
        
        Args:
            payload: Request payload
            
        Returns:
            Dictionary mapping invalid field names to error messages
        """
        invalid_fields = {}
        
        for field_name, field_value in payload.items():
            # Skip fields not in schema
            if field_name not in self.all_fields:
                continue
            
            field_schema = self.all_fields[field_name]
            
            # Check type
            if not self._check_type(field_value, field_schema.field_type):
                invalid_fields[field_name] = f"Invalid type: expected {field_schema.field_type.value}"
                continue
            
            # Check custom validator
            if field_schema.validator and not field_schema.validator(field_value):
                invalid_fields[field_name] = "Failed custom validation"
        
        return invalid_fields
    
    def _check_type(self, value: Any, expected_type: FieldType) -> bool:
        """
        Check if value matches expected type.
        
        Args:
            value: Value to check
            expected_type: Expected FieldType
            
        Returns:
            True if type matches, False otherwise
        """
        if expected_type == FieldType.ANY:
            return True
        
        if expected_type == FieldType.STRING:
            return isinstance(value, str)
        
        if expected_type == FieldType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        
        if expected_type == FieldType.FLOAT:
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        
        if expected_type == FieldType.BOOLEAN:
            return isinstance(value, bool)
        
        if expected_type == FieldType.LIST:
            return isinstance(value, list)
        
        if expected_type == FieldType.DICT:
            return isinstance(value, dict)
        
        if expected_type == FieldType.EMAIL:
            return isinstance(value, str) and self._is_valid_email(value)
        
        if expected_type == FieldType.URL:
            return isinstance(value, str) and self._is_valid_url(value)
        
        return False
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        return "@" in email and "." in email.split("@")[-1]
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        return url.startswith(("http://", "https://"))
    
    def _generate_message(
        self,
        is_valid: bool,
        missing_fields: List[str],
        invalid_fields: Dict[str, str]
    ) -> str:
        """
        Generate a human-readable validation message.
        
        Args:
            is_valid: Overall validation status
            missing_fields: List of missing field names
            invalid_fields: Dictionary of invalid fields
            
        Returns:
            Validation message string
        """
        if is_valid:
            return "Validation successful"
        
        messages = []
        
        if missing_fields:
            messages.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        if invalid_fields:
            invalid_list = [f"{field} ({error})" for field, error in invalid_fields.items()]
            messages.append(f"Invalid fields: {', '.join(invalid_list)}")
        
        return "; ".join(messages)


# ============================================================================
# Schema Builder Helper
# ============================================================================

class SchemaBuilder:
    """
    Helper class for building validation schemas fluently.
    """
    
    def __init__(self):
        self.fields: List[FieldSchema] = []
    
    def add_field(
        self,
        name: str,
        required: bool = True,
        field_type: FieldType = FieldType.ANY,
        validator: Optional[Callable[[Any], bool]] = None,
        default: Any = None,
        description: str = ""
    ) -> 'SchemaBuilder':
        """
        Add a field to the schema.
        
        Args:
            name: Field name
            required: Whether field is required
            field_type: Expected field type
            validator: Optional custom validation function
            default: Default value if not provided
            description: Field description
            
        Returns:
            Self for method chaining
        """
        self.fields.append(FieldSchema(
            name=name,
            required=required,
            field_type=field_type,
            validator=validator,
            default=default,
            description=description
        ))
        return self
    
    def build(self) -> List[FieldSchema]:
        """Build and return the schema"""
        return self.fields


# ============================================================================
# Quick Validation Functions
# ============================================================================

def validate_payload(
    payload: Dict[str, Any],
    required_fields: List[str]
) -> ValidationResult:
    """
    Quick validation function for simple required field checks.
    
    Args:
        payload: Request payload to validate
        required_fields: List of required field names
        
    Returns:
        ValidationResult with validation status
    """
    schema = [FieldSchema(name=field, required=True) for field in required_fields]
    validator = PayloadValidator(schema)
    return validator.validate(payload)


def validate_with_types(
    payload: Dict[str, Any],
    field_types: Dict[str, FieldType]
) -> ValidationResult:
    """
    Quick validation with type checking.
    
    Args:
        payload: Request payload to validate
        field_types: Dictionary mapping field names to expected types
        
    Returns:
        ValidationResult with validation status
    """
    schema = [
        FieldSchema(name=field, required=True, field_type=ftype)
        for field, ftype in field_types.items()
    ]
    validator = PayloadValidator(schema)
    return validator.validate(payload)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example 1: Simple required fields validation
    print("=== Example 1: Simple Required Fields ===")
    payload1 = {
        "username": "john_doe",
        "email": "john@example.com"
    }
    
    result1 = validate_payload(payload1, ["username", "email", "password"])
    print(f"Valid: {result1.is_valid}")
    print(f"Missing: {result1.missing_fields}")
    print(f"Message: {result1.message}")
    print()
    
    # Example 2: Validation with types
    print("=== Example 2: Type Validation ===")
    payload2 = {
        "user_id": 123,
        "email": "user@example.com",
        "age": 25,
        "is_active": True
    }
    
    result2 = validate_with_types(payload2, {
        "user_id": FieldType.INTEGER,
        "email": FieldType.EMAIL,
        "age": FieldType.INTEGER,
        "is_active": FieldType.BOOLEAN
    })
    print(f"Valid: {result2.is_valid}")
    print(f"Message: {result2.message}")
    print()
    
    # Example 3: Schema builder with custom validation
    print("=== Example 3: Schema Builder with Custom Validation ===")
    
    def validate_age(age: int) -> bool:
        """Custom validator: age must be between 18 and 120"""
        return 18 <= age <= 120
    
    schema = (SchemaBuilder()
        .add_field("username", required=True, field_type=FieldType.STRING)
        .add_field("email", required=True, field_type=FieldType.EMAIL)
        .add_field("age", required=True, field_type=FieldType.INTEGER, validator=validate_age)
        .add_field("website", required=False, field_type=FieldType.URL)
        .build()
    )
    
    validator = PayloadValidator(schema)
    
    # Valid payload
    payload3 = {
        "username": "jane_doe",
        "email": "jane@example.com",
        "age": 30,
        "website": "https://example.com"
    }
    
    result3 = validator.validate(payload3)
    print(f"Valid: {result3.is_valid}")
    print(f"Message: {result3.message}")
    print()
    
    # Invalid payload (age out of range)
    payload4 = {
        "username": "bob",
        "email": "bob@example.com",
        "age": 150
    }
    
    result4 = validator.validate(payload4)
    print(f"Valid: {result4.is_valid}")
    print(f"Message: {result4.message}")
    print(f"Invalid fields: {result4.invalid_fields}")
    print()
    
    # Example 4: Integration with backend operations agent
    print("=== Example 4: Backend Operations Agent Integration ===")
    
    # Define schema for error/event payloads
    agent_schema = (SchemaBuilder()
        .add_field("error_type", required=True, field_type=FieldType.STRING)
        .add_field("message", required=True, field_type=FieldType.STRING)
        .add_field("timestamp", required=True, field_type=FieldType.INTEGER)
        .add_field("context", required=False, field_type=FieldType.DICT)
        .add_field("stack_trace", required=False, field_type=FieldType.STRING)
        .build()
    )
    
    agent_validator = PayloadValidator(agent_schema)
    
    # Valid agent payload
    agent_payload = {
        "error_type": "ValidationError",
        "message": "Invalid input",
        "timestamp": 1706707025,
        "context": {"field": "email"}
    }
    
    result5 = agent_validator.validate(agent_payload)
    print(f"Agent payload valid: {result5.is_valid}")
    print(f"Result dict: {result5.to_dict()}")