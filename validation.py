"""
Input Validation Module for Contextual Document Router
Provides comprehensive validation for user inputs and system data
"""
import re
import os
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
import json


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class FileValidator:
    """Validate file inputs"""
    
    ALLOWED_EXTENSIONS = {
        'txt', 'eml', 'json', 'pdf', 'msg'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_exists(file_path: str) -> Tuple[bool, str]:
        """Validate that file exists"""
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        return True, "File exists"
    
    @staticmethod
    def validate_file_extension(file_path: str) -> Tuple[bool, str]:
        """Validate file extension"""
        ext = Path(file_path).suffix.lstrip('.').lower()
        if ext not in FileValidator.ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension: {ext}. Allowed: {FileValidator.ALLOWED_EXTENSIONS}"
        return True, "Valid extension"
    
    @staticmethod
    def validate_file_size(file_path: str, max_size: int = None) -> Tuple[bool, str]:
        """Validate file size"""
        max_size = max_size or FileValidator.MAX_FILE_SIZE
        file_size = os.path.getsize(file_path)
        
        if file_size > max_size:
            return False, f"File too large: {file_size} bytes (max: {max_size} bytes)"
        if file_size == 0:
            return False, "File is empty"
        return True, f"Valid size: {file_size} bytes"
    
    @staticmethod
    def validate_file_readable(file_path: str) -> Tuple[bool, str]:
        """Validate that file is readable"""
        try:
            with open(file_path, 'r') as f:
                f.read(1)
            return True, "File is readable"
        except PermissionError:
            return False, f"Permission denied: {file_path}"
        except UnicodeDecodeError:
            # Try binary read
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
                return True, "File is readable (binary)"
            except Exception as e:
                return False, f"Cannot read file: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    @classmethod
    def validate_file(cls, file_path: str) -> Tuple[bool, List[str]]:
        """
        Comprehensive file validation
        
        Returns:
            (is_valid, list_of_error_messages)
        """
        errors = []
        
        # Check existence
        is_valid, msg = cls.validate_file_exists(file_path)
        if not is_valid:
            errors.append(msg)
            return False, errors
        
        # Check extension
        is_valid, msg = cls.validate_file_extension(file_path)
        if not is_valid:
            errors.append(msg)
        
        # Check size
        is_valid, msg = cls.validate_file_size(file_path)
        if not is_valid:
            errors.append(msg)
        
        # Check readability
        is_valid, msg = cls.validate_file_readable(file_path)
        if not is_valid:
            errors.append(msg)
        
        return len(errors) == 0, errors


class EmailValidator:
    """Validate email-related inputs"""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    @staticmethod
    def validate_email_address(email: str) -> Tuple[bool, str]:
        """Validate email address format"""
        if not email:
            return False, "Email address is empty"
        
        if not re.match(EmailValidator.EMAIL_PATTERN, email):
            return False, f"Invalid email format: {email}"
        
        return True, "Valid email address"
    
    @staticmethod
    def validate_email_content(content: str) -> Tuple[bool, str]:
        """Validate email content structure"""
        if not content:
            return False, "Email content is empty"
        
        # Check for basic email headers
        has_from = 'from:' in content.lower()
        has_to = 'to:' in content.lower()
        has_subject = 'subject:' in content.lower()
        
        if not (has_from or has_to):
            return False, "Email missing basic headers (From/To)"
        
        return True, "Valid email structure"


class JSONValidator:
    """Validate JSON inputs"""
    
    @staticmethod
    def validate_json_string(json_str: str) -> Tuple[bool, str]:
        """Validate JSON string format"""
        if not json_str:
            return False, "JSON string is empty"
        
        try:
            json.loads(json_str)
            return True, "Valid JSON"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
    
    @staticmethod
    def validate_json_schema(data: Dict, required_fields: Dict[str, type]) -> Tuple[bool, List[str]]:
        """
        Validate JSON data against schema
        
        Args:
            data: JSON data as dictionary
            required_fields: Dict mapping field names to expected types
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        for field, expected_type in required_fields.items():
            if field not in data:
                errors.append(f"Missing required field: {field}")
                continue
            
            if not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' has wrong type. "
                    f"Expected {expected_type.__name__}, got {type(data[field]).__name__}"
                )
        
        return len(errors) == 0, errors


class ConfidenceValidator:
    """Validate confidence scores"""
    
    @staticmethod
    def validate_confidence(confidence: float, min_val: float = 0.0, max_val: float = 1.0) -> Tuple[bool, str]:
        """Validate confidence score range"""
        if not isinstance(confidence, (int, float)):
            return False, f"Confidence must be numeric, got {type(confidence).__name__}"
        
        if confidence < min_val or confidence > max_val:
            return False, f"Confidence {confidence} out of range [{min_val}, {max_val}]"
        
        return True, "Valid confidence score"
    
    @staticmethod
    def is_high_confidence(confidence: float, threshold: float = 0.7) -> bool:
        """Check if confidence is above threshold"""
        return confidence >= threshold
    
    @staticmethod
    def is_low_confidence(confidence: float, threshold: float = 0.5) -> bool:
        """Check if confidence is below threshold"""
        return confidence < threshold


class IntentValidator:
    """Validate intent classifications"""
    
    VALID_INTENTS = {
        'Complaint', 'Invoice', 'Regulation', 'Fraud Risk', 'RFQ', 'Unknown'
    }
    
    @staticmethod
    def validate_intent(intent: str) -> Tuple[bool, str]:
        """Validate intent value"""
        if not intent:
            return False, "Intent is empty"
        
        if intent not in IntentValidator.VALID_INTENTS:
            return False, f"Invalid intent: {intent}. Valid: {IntentValidator.VALID_INTENTS}"
        
        return True, "Valid intent"


class InputSanitizer:
    """Sanitize user inputs"""
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\0', '')
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
        
        return text.strip()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename"""
        # Remove directory traversal attempts
        filename = os.path.basename(filename)
        
        # Remove special characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]
        
        return name + ext
    
    @staticmethod
    def sanitize_path(path: str, allowed_base_paths: List[str] = None) -> Optional[str]:
        """
        Sanitize file path and ensure it's within allowed directories
        
        Args:
            path: Input path
            allowed_base_paths: List of allowed base directories
        
        Returns:
            Sanitized path or None if invalid
        """
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        
        # Check against allowed base paths
        if allowed_base_paths:
            is_allowed = False
            for base_path in allowed_base_paths:
                abs_base = os.path.abspath(base_path)
                if abs_path.startswith(abs_base):
                    is_allowed = True
                    break
            
            if not is_allowed:
                return None
        
        return abs_path


class DataValidator:
    """Main validator class combining all validators"""
    
    def __init__(self):
        self.file_validator = FileValidator()
        self.email_validator = EmailValidator()
        self.json_validator = JSONValidator()
        self.confidence_validator = ConfidenceValidator()
        self.intent_validator = IntentValidator()
        self.sanitizer = InputSanitizer()
    
    def validate_upload(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate file upload"""
        return self.file_validator.validate_file(file_path)
    
    def validate_classification_result(self, intent: str, confidence: float) -> Tuple[bool, List[str]]:
        """Validate classification result"""
        errors = []
        
        # Validate intent
        is_valid, msg = self.intent_validator.validate_intent(intent)
        if not is_valid:
            errors.append(msg)
        
        # Validate confidence
        is_valid, msg = self.confidence_validator.validate_confidence(confidence)
        if not is_valid:
            errors.append(msg)
        
        return len(errors) == 0, errors
    
    def validate_and_sanitize_input(self, text: str, max_length: int = 10000) -> str:
        """Validate and sanitize text input"""
        if not text:
            raise ValidationError("Input text is empty")
        
        if len(text) > max_length:
            raise ValidationError(f"Input too long: {len(text)} chars (max: {max_length})")
        
        return self.sanitizer.sanitize_string(text, max_length)


# Global validator instance
validator = DataValidator()


def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate request data has required fields
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Field '{field}' cannot be None")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"Field '{field}' cannot be empty")
    
    return len(errors) == 0, errors


if __name__ == "__main__":
    # Test validators
    print("=== Testing Validation System ===\n")
    
    # Test email validation
    email_valid, msg = EmailValidator.validate_email_address("test@example.com")
    print(f"Email validation: {email_valid} - {msg}")
    
    # Test JSON validation
    json_str = '{"key": "value", "number": 123}'
    json_valid, msg = JSONValidator.validate_json_string(json_str)
    print(f"JSON validation: {json_valid} - {msg}")
    
    # Test confidence validation
    conf_valid, msg = ConfidenceValidator.validate_confidence(0.85)
    print(f"Confidence validation: {conf_valid} - {msg}")
    
    # Test intent validation
    intent_valid, msg = IntentValidator.validate_intent("Complaint")
    print(f"Intent validation: {intent_valid} - {msg}")
    
    # Test sanitization
    dirty_text = "Hello<script>alert('xss')</script>World"
    clean_text = InputSanitizer.sanitize_string(dirty_text)
    print(f"\nSanitized: '{dirty_text}' -> '{clean_text}'")
    
    print("\nValidation tests completed!")
