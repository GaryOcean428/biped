"""
Comprehensive Route Validation System for Biped Platform
Provides input validation, sanitization, and security checks for all routes
"""

import re
from functools import wraps
from typing import Any, Dict, List, Optional, Union

from flask import jsonify, request

from src.utils.error_boundaries import ValidationError


class RouteValidator:
    """Comprehensive route validation and sanitization"""

    def __init__(self):
        self.email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        self.phone_pattern = re.compile(r"^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$")
        self.password_pattern = re.compile(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        )

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False
        return bool(self.email_pattern.match(email.strip()))

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        if not phone or not isinstance(phone, str):
            return False
        # Remove all non-digit characters except +
        cleaned = re.sub(r"[^\d+]", "", phone)
        return bool(self.phone_pattern.match(cleaned))

    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            return False
        return bool(self.password_pattern.match(password))

    def sanitize_string(self, value: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', "", value.strip())

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """Validate that all required fields are present and not empty"""
        missing_fields = []
        empty_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif not data[field] or (
                isinstance(data[field], str) and not data[field].strip()
            ):
                empty_fields.append(field)

        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        if empty_fields:
            raise ValidationError(f"Empty required fields: {', '.join(empty_fields)}")

    def validate_field_types(
        self, data: Dict[str, Any], field_types: Dict[str, type]
    ) -> None:
        """Validate field types"""
        type_errors = []

        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                type_errors.append(f"{field} must be of type {expected_type.__name__}")

        if type_errors:
            raise ValidationError(f"Type validation errors: {'; '.join(type_errors)}")

    def validate_field_lengths(
        self, data: Dict[str, Any], field_lengths: Dict[str, int]
    ) -> None:
        """Validate field lengths"""
        length_errors = []

        for field, max_length in field_lengths.items():
            if (
                field in data
                and isinstance(data[field], str)
                and len(data[field]) > max_length
            ):
                length_errors.append(
                    f"{field} must be no more than {max_length} characters"
                )

        if length_errors:
            raise ValidationError(
                f"Length validation errors: {'; '.join(length_errors)}"
            )

    def validate_numeric_ranges(
        self,
        data: Dict[str, Any],
        numeric_ranges: Dict[str, Dict[str, Union[int, float]]],
    ) -> None:
        """Validate numeric field ranges"""
        range_errors = []

        for field, range_config in numeric_ranges.items():
            if field in data:
                value = data[field]
                if isinstance(value, (int, float)):
                    min_val = range_config.get("min")
                    max_val = range_config.get("max")

                    if min_val is not None and value < min_val:
                        range_errors.append(f"{field} must be at least {min_val}")

                    if max_val is not None and value > max_val:
                        range_errors.append(f"{field} must be no more than {max_val}")

        if range_errors:
            raise ValidationError(f"Range validation errors: {'; '.join(range_errors)}")

    def validate_enum_values(
        self, data: Dict[str, Any], enum_fields: Dict[str, List[str]]
    ) -> None:
        """Validate enum/choice fields"""
        enum_errors = []

        for field, allowed_values in enum_fields.items():
            if field in data and data[field] not in allowed_values:
                enum_errors.append(
                    f"{field} must be one of: {', '.join(allowed_values)}"
                )

        if enum_errors:
            raise ValidationError(f"Enum validation errors: {'; '.join(enum_errors)}")


# Validation decorators
def validate_json_request(validation_config: Dict[str, Any]):
    """
    Decorator to validate JSON request data

    Args:
        validation_config: Dictionary containing validation rules:
            - required_fields: List of required field names
            - field_types: Dict mapping field names to expected types
            - field_lengths: Dict mapping field names to max lengths
            - numeric_ranges: Dict mapping field names to min/max values
            - enum_fields: Dict mapping field names to allowed values
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            validator = RouteValidator()

            # Check if request has JSON data
            if not request.is_json:
                raise ValidationError("Request must contain JSON data")

            data = request.get_json()
            if not data:
                raise ValidationError("Request body cannot be empty")

            # Apply validations
            if "required_fields" in validation_config:
                validator.validate_required_fields(
                    data, validation_config["required_fields"]
                )

            if "field_types" in validation_config:
                validator.validate_field_types(data, validation_config["field_types"])

            if "field_lengths" in validation_config:
                validator.validate_field_lengths(
                    data, validation_config["field_lengths"]
                )

            if "numeric_ranges" in validation_config:
                validator.validate_numeric_ranges(
                    data, validation_config["numeric_ranges"]
                )

            if "enum_fields" in validation_config:
                validator.validate_enum_values(data, validation_config["enum_fields"])

            # Sanitize string fields
            for key, value in data.items():
                if isinstance(value, str):
                    max_length = validation_config.get("field_lengths", {}).get(
                        key, 255
                    )
                    data[key] = validator.sanitize_string(value, max_length)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def _convert_param_types(params: Dict[str, str], param_types: Dict[str, type]) -> None:
    """Convert string parameters to expected types"""
    for param, expected_type in param_types.items():
        if param in params:
            try:
                if expected_type == int:
                    params[param] = int(params[param])
                elif expected_type == float:
                    params[param] = float(params[param])
                elif expected_type == bool:
                    params[param] = params[param].lower() in (
                        "true",
                        "1",
                        "yes",
                    )
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Parameter {param} must be of type {expected_type.__name__}"
                )


def validate_query_params(validation_config: Dict[str, Any]):
    """
    Decorator to validate query parameters

    Args:
        validation_config: Dictionary containing validation rules for query params
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            validator = RouteValidator()

            # Get query parameters
            params = request.args.to_dict()

            # Apply validations
            if "required_params" in validation_config:
                validator.validate_required_fields(
                    params, validation_config["required_params"]
                )

            if "param_types" in validation_config:
                _convert_param_types(params, validation_config["param_types"])

            if "enum_params" in validation_config:
                validator.validate_enum_values(params, validation_config["enum_params"])

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_user_registration():
    """Specific validation for user registration"""
    return validate_json_request(
        {
            "required_fields": [
                "email",
                "password",
                "first_name",
                "last_name",
                "user_type",
            ],
            "field_types": {
                "email": str,
                "password": str,
                "first_name": str,
                "last_name": str,
                "user_type": str,
                "phone": str,
            },
            "field_lengths": {
                "email": 255,
                "password": 128,
                "first_name": 50,
                "last_name": 50,
                "phone": 20,
            },
            "enum_fields": {"user_type": ["customer", "provider"]},
        }
    )


def validate_job_creation():
    """Specific validation for job creation"""
    return validate_json_request(
        {
            "required_fields": [
                "title",
                "description",
                "category",
                "budget_min",
                "budget_max",
            ],
            "field_types": {
                "title": str,
                "description": str,
                "category": str,
                "budget_min": (int, float),
                "budget_max": (int, float),
                "urgency": str,
            },
            "field_lengths": {
                "title": 100,
                "description": 2000,
                "category": 50,
                "location": 255,
            },
            "numeric_ranges": {
                "budget_min": {"min": 0, "max": 1000000},
                "budget_max": {"min": 0, "max": 1000000},
            },
            "enum_fields": {"urgency": ["low", "medium", "high", "urgent"]},
        }
    )


def validate_quote_submission():
    """Specific validation for quote submission"""
    return validate_json_request(
        {
            "required_fields": ["job_id", "amount", "description"],
            "field_types": {
                "job_id": int,
                "amount": (int, float),
                "description": str,
                "estimated_duration": int,
            },
            "field_lengths": {"description": 1000},
            "numeric_ranges": {
                "amount": {"min": 0, "max": 1000000},
                "estimated_duration": {"min": 1, "max": 365},
            },
        }
    )


# Global validator instance
route_validator = RouteValidator()
