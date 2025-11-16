"""
Utility Functions for Contextual Document Router
Common helper functions used throughout the application
"""
import hashlib
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from pathlib import Path


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of a file
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256)
    
    Returns:
        Hexadecimal hash string
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(file_path)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove potentially dangerous characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Remove path separators and special characters
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return name + ext


def ensure_directory(directory: str) -> str:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    
    Returns:
        Absolute path to directory
    """
    Path(directory).mkdir(parents=True, exist_ok=True)
    return os.path.abspath(directory)


def timestamp_to_datetime(timestamp: str) -> Optional[datetime]:
    """
    Convert ISO format timestamp to datetime object
    
    Args:
        timestamp: ISO format timestamp string
    
    Returns:
        datetime object or None if invalid
    """
    try:
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def datetime_to_timestamp(dt: datetime) -> str:
    """
    Convert datetime object to ISO format timestamp
    
    Args:
        dt: datetime object
    
    Returns:
        ISO format timestamp string
    """
    return dt.isoformat()


def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries
    
    Args:
        *dicts: Variable number of dictionaries
    
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string, return default on error
    
    Args:
        json_str: JSON string
        default: Default value if parsing fails
    
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: Any = "{}") -> str:
    """
    Safely dump object to JSON string
    
    Args:
        obj: Object to serialize
        default: Default value if serialization fails
    
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to max length
    
    Args:
        text: Input string
        max_length: Maximum length
        suffix: Suffix to append when truncated
    
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_email_address(text: str) -> Optional[str]:
    """
    Extract first email address from text
    
    Args:
        text: Input text
    
    Returns:
        Email address or None
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_all_emails(text: str) -> List[str]:
    """
    Extract all email addresses from text
    
    Args:
        text: Input text
    
    Returns:
        List of email addresses
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text
    
    Args:
        text: Input text
    
    Returns:
        List of URLs
    """
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text
    
    Args:
        text: Input text
    
    Returns:
        List of phone numbers
    """
    patterns = [
        r'\+?1?\d{9,15}',  # International format
        r'\(\d{3}\)\s*\d{3}-\d{4}',  # (123) 456-7890
        r'\d{3}-\d{3}-\d{4}',  # 123-456-7890
    ]
    
    numbers = []
    for pattern in patterns:
        numbers.extend(re.findall(pattern, text))
    
    return list(set(numbers))  # Remove duplicates


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters
    
    Args:
        text: Input text
    
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters
    text = ''.join(char for char in text if char.isprintable())
    
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text
        chunk_size: Size of each chunk
        overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks


def calculate_confidence_score(matches: List[bool]) -> float:
    """
    Calculate confidence score from list of boolean matches
    
    Args:
        matches: List of boolean values
    
    Returns:
        Confidence score between 0 and 1
    """
    if not matches:
        return 0.0
    return sum(matches) / len(matches)


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Normalize score to range [0, 1]
    
    Args:
        score: Input score
        min_val: Minimum value in original range
        max_val: Maximum value in original range
    
    Returns:
        Normalized score
    """
    if max_val == min_val:
        return 0.5
    return (score - min_val) / (max_val - min_val)


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


def create_unique_filename(base_name: str, extension: str = "", directory: str = ".") -> str:
    """
    Create a unique filename by appending a number if file exists
    
    Args:
        base_name: Base filename
        extension: File extension (with or without dot)
        directory: Directory to check for existing files
    
    Returns:
        Unique filename
    """
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    
    counter = 0
    filename = f"{base_name}{extension}"
    filepath = os.path.join(directory, filename)
    
    while os.path.exists(filepath):
        counter += 1
        filename = f"{base_name}_{counter}{extension}"
        filepath = os.path.join(directory, filename)
    
    return filename


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Batch items into groups of specified size
    
    Args:
        items: List of items
        batch_size: Size of each batch
    
    Returns:
        List of batches
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename
    
    Returns:
        File extension (without dot)
    """
    _, ext = os.path.splitext(filename)
    return ext.lstrip('.')


def is_valid_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Check if file type is in allowed list
    
    Args:
        filename: Filename
        allowed_extensions: List of allowed extensions
    
    Returns:
        True if valid, False otherwise
    """
    ext = get_file_extension(filename).lower()
    return ext in [e.lower().lstrip('.') for e in allowed_extensions]


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Flatten nested dictionary
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_get(d: Dict, keys: str, default: Any = None) -> Any:
    """
    Get value from nested dictionary using dot notation
    
    Args:
        d: Dictionary
        keys: Dot-separated keys (e.g., 'user.profile.name')
        default: Default value if key not found
    
    Returns:
        Value or default
    """
    keys_list = keys.split('.')
    for key in keys_list:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


if __name__ == "__main__":
    # Test utility functions
    print("=== Testing Utility Functions ===\n")
    
    # Test file operations
    test_file = "test.txt"
    with open(test_file, 'w') as f:
        f.write("Test content")
    
    print(f"File hash: {calculate_file_hash(test_file)}")
    print(f"File size: {format_file_size(get_file_size(test_file))}")
    
    # Test text operations
    text = "Contact us at support@example.com or call (123) 456-7890"
    print(f"\nExtracted emails: {extract_all_emails(text)}")
    print(f"Extracted phones: {extract_phone_numbers(text)}")
    
    # Test string operations
    long_text = "This is a very long text that needs to be truncated"
    print(f"\nTruncated: {truncate_string(long_text, 20)}")
    
    # Cleanup
    os.remove(test_file)
    
    print("\nUtility tests completed!")
