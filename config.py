"""
Configuration Management System for Contextual Document Router
Centralized configuration for all system components
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class SystemConfig:
    """Main system configuration"""
    # Application Settings
    app_name: str = "Contextual Document Router"
    version: str = "2.0.0"
    environment: str = "development"  # development, staging, production
    debug: bool = True
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    max_workers: int = 4
    
    # File Upload Settings
    upload_dir: str = "uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: tuple = (".txt", ".json", ".pdf", ".eml", ".msg")
    
    # Processing Settings
    max_retry_attempts: int = 3
    retry_delay: int = 2
    request_timeout: int = 30
    batch_processing: bool = False
    batch_size: int = 10
    
    # Classification Settings
    confidence_threshold: float = 0.7
    min_confidence: float = 0.5
    max_confidence: float = 1.0
    
    # Database/Memory Settings
    shared_memory_file: str = "shared_memory.json"
    enable_persistence: bool = True
    max_memory_entries: int = 1000
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_rotation: str = "daily"
    log_retention_days: int = 30
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    
    # Security Settings
    enable_auth: bool = False
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Email Processing Settings
    email_tone_analysis: bool = True
    email_entity_extraction: bool = True
    email_sentiment_scoring: bool = True
    
    # PDF Processing Settings
    pdf_ocr_enabled: bool = True
    pdf_extract_images: bool = False
    pdf_max_pages: int = 100
    
    # JSON Processing Settings
    json_schema_validation: bool = True
    json_max_depth: int = 10
    json_anomaly_detection: bool = True
    
    # Alert Configuration
    alert_email_enabled: bool = False
    alert_email_recipients: list = None
    alert_webhook_url: Optional[str] = None
    alert_threshold_fraud: float = 0.8
    
    # Monitoring & Metrics
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 60
    
    # Frontend Settings
    frontend_host: str = "localhost"
    frontend_port: int = 3000
    enable_cors: bool = True
    cors_origins: list = None
    
    def __post_init__(self):
        """Initialize default values for mutable types"""
        if self.alert_email_recipients is None:
            self.alert_email_recipients = []
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """Export config to JSON"""
        json_str = json.dumps(self.to_dict(), indent=4)
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        return json_str
    
    @classmethod
    def from_json(cls, filepath: str) -> 'SystemConfig':
        """Load config from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """Load config from environment variables"""
        config = cls()
        
        # Override with environment variables if present
        config.environment = os.getenv('APP_ENV', config.environment)
        config.debug = os.getenv('DEBUG', str(config.debug)).lower() == 'true'
        config.api_host = os.getenv('API_HOST', config.api_host)
        config.api_port = int(os.getenv('API_PORT', str(config.api_port)))
        config.log_level = os.getenv('LOG_LEVEL', config.log_level)
        
        return config
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration settings"""
        errors = []
        
        # Validate ports
        if not (1024 <= self.api_port <= 65535):
            errors.append(f"Invalid API port: {self.api_port}. Must be between 1024 and 65535.")
        
        # Validate confidence thresholds
        if not (0.0 <= self.confidence_threshold <= 1.0):
            errors.append(f"Invalid confidence threshold: {self.confidence_threshold}. Must be between 0.0 and 1.0.")
        
        # Validate retry settings
        if self.max_retry_attempts < 0:
            errors.append(f"Invalid max_retry_attempts: {self.max_retry_attempts}. Must be non-negative.")
        
        # Validate upload size
        if self.max_upload_size <= 0:
            errors.append(f"Invalid max_upload_size: {self.max_upload_size}. Must be positive.")
        
        # Validate paths
        if self.enable_file_logging:
            log_dir = Path(self.log_file).parent
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory: {e}")
        
        return len(errors) == 0, errors


class ConfigManager:
    """Manages system configuration with hot reload support"""
    
    _instance = None
    _config: SystemConfig = None
    _config_file: str = "config.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_file: Optional[str] = None):
        """Load configuration from file or create default"""
        if config_file:
            self._config_file = config_file
        
        if os.path.exists(self._config_file):
            try:
                self._config = SystemConfig.from_json(self._config_file)
                print(f"Configuration loaded from {self._config_file}")
            except Exception as e:
                print(f"Error loading config file: {e}. Using default configuration.")
                self._config = SystemConfig()
        else:
            # Try loading from environment
            self._config = SystemConfig.from_env()
            # Save default config
            self.save_config()
    
    def save_config(self, config_file: Optional[str] = None):
        """Save current configuration to file"""
        if config_file:
            self._config_file = config_file
        
        try:
            self._config.to_json(self._config_file)
            print(f"Configuration saved to {self._config_file}")
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get_config(self) -> SystemConfig:
        """Get current configuration"""
        return self._config
    
    def update_config(self, **kwargs):
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                print(f"Warning: Unknown config parameter: {key}")
    
    def reload_config(self):
        """Reload configuration from file"""
        self.load_config()
    
    def validate_config(self) -> bool:
        """Validate current configuration"""
        is_valid, errors = self._config.validate()
        if not is_valid:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
        return is_valid


# Global configuration instance
config_manager = ConfigManager()

def get_config() -> SystemConfig:
    """Get the global configuration instance"""
    return config_manager.get_config()


# Predefined configuration profiles
class ConfigProfiles:
    """Predefined configuration profiles for different environments"""
    
    @staticmethod
    def development() -> SystemConfig:
        """Development environment configuration"""
        config = SystemConfig()
        config.environment = "development"
        config.debug = True
        config.api_reload = True
        config.log_level = "DEBUG"
        config.enable_console_logging = True
        return config
    
    @staticmethod
    def production() -> SystemConfig:
        """Production environment configuration"""
        config = SystemConfig()
        config.environment = "production"
        config.debug = False
        config.api_reload = False
        config.log_level = "WARNING"
        config.enable_console_logging = False
        config.max_workers = 8
        config.enable_auth = True
        config.rate_limit_requests = 100
        return config
    
    @staticmethod
    def testing() -> SystemConfig:
        """Testing environment configuration"""
        config = SystemConfig()
        config.environment = "testing"
        config.debug = True
        config.log_level = "DEBUG"
        config.enable_persistence = False
        config.max_retry_attempts = 1
        return config


if __name__ == "__main__":
    # Example usage and testing
    print("=== Configuration Management System ===\n")
    
    # Get default config
    config = get_config()
    print("Default Configuration:")
    print(json.dumps(config.to_dict(), indent=2))
    
    # Validate config
    is_valid, errors = config.validate()
    print(f"\nConfiguration Valid: {is_valid}")
    if errors:
        print("Errors:", errors)
    
    # Save config
    config_manager.save_config()
    print(f"\nConfiguration saved to {config_manager._config_file}")
