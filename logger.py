"""
Advanced Logging System for Contextual Document Router
Provides comprehensive logging with multiple handlers and formatters
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional
from pathlib import Path
import json
import traceback


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        result = super().format(record)
        return result


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data)


class Logger:
    """Enhanced Logger class with multiple handlers"""
    
    _loggers = {}
    
    @staticmethod
    def get_logger(
        name: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        console: bool = True,
        json_format: bool = False
    ) -> logging.Logger:
        """
        Get or create a logger instance
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            console: Enable console logging
            json_format: Use JSON format for file logging
            
        Returns:
            Configured logger instance
        """
        
        # Return existing logger if already created
        if name in Logger._loggers:
            return Logger._loggers[name]
        
        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.propagate = False
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # Use colored formatter for console
            console_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
            console_formatter = ColoredFormatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Use rotating file handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Choose formatter based on json_format parameter
            if json_format:
                file_formatter = JSONFormatter()
            else:
                file_format = '%(asctime)s - %(levelname)s - %(name)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
                file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Store logger
        Logger._loggers[name] = logger
        return logger
    
    @staticmethod
    def log_with_context(logger: logging.Logger, level: str, message: str, **context):
        """Log message with additional context"""
        extra = {'extra_data': context}
        log_func = getattr(logger, level.lower())
        log_func(message, extra=extra)


class AuditLogger:
    """Specialized logger for audit trails"""
    
    def __init__(self, log_file: str = "logs/audit.log"):
        self.logger = Logger.get_logger(
            'audit',
            log_level='INFO',
            log_file=log_file,
            console=False,
            json_format=True
        )
    
    def log_action(self, action: str, user: str = "system", **details):
        """Log an audit action"""
        audit_data = {
            'action': action,
            'user': user,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.logger.info(f"AUDIT: {action}", extra={'extra_data': audit_data})
    
    def log_file_upload(self, filename: str, size: int, format: str, user: str = "system"):
        """Log file upload event"""
        self.log_action(
            'file_upload',
            user=user,
            filename=filename,
            size=size,
            format=format
        )
    
    def log_classification(self, filename: str, intent: str, confidence: float, user: str = "system"):
        """Log classification event"""
        self.log_action(
            'classification',
            user=user,
            filename=filename,
            intent=intent,
            confidence=confidence
        )
    
    def log_action_triggered(self, action_type: str, details: dict, user: str = "system"):
        """Log action trigger event"""
        self.log_action(
            'action_triggered',
            user=user,
            action_type=action_type,
            **details
        )
    
    def log_error(self, error_type: str, message: str, **details):
        """Log error event"""
        self.log_action(
            'error',
            user='system',
            error_type=error_type,
            message=message,
            **details
        )


class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, log_file: str = "logs/performance.log"):
        self.logger = Logger.get_logger(
            'performance',
            log_level='INFO',
            log_file=log_file,
            console=False,
            json_format=True
        )
    
    def log_processing_time(self, operation: str, duration: float, **metadata):
        """Log processing time for an operation"""
        perf_data = {
            'operation': operation,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata
        }
        self.logger.info(f"PERFORMANCE: {operation} took {duration:.3f}s", extra={'extra_data': perf_data})
    
    def log_api_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Log API request metrics"""
        self.log_processing_time(
            'api_request',
            duration,
            endpoint=endpoint,
            method=method,
            status_code=status_code
        )


class ErrorLogger:
    """Specialized logger for error tracking"""
    
    def __init__(self, log_file: str = "logs/errors.log"):
        self.logger = Logger.get_logger(
            'errors',
            log_level='ERROR',
            log_file=log_file,
            console=True,
            json_format=True
        )
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log an exception with full traceback"""
        self.logger.error(
            f"Exception in {context}: {str(exception)}",
            exc_info=True,
            extra={'extra_data': {'context': context}}
        )
    
    def log_validation_error(self, field: str, value: any, reason: str):
        """Log validation error"""
        error_data = {
            'type': 'validation_error',
            'field': field,
            'value': str(value),
            'reason': reason
        }
        self.logger.error(f"Validation error: {field} - {reason}", extra={'extra_data': error_data})
    
    def log_processing_error(self, file_path: str, stage: str, error: str):
        """Log processing error"""
        error_data = {
            'type': 'processing_error',
            'file': file_path,
            'stage': stage,
            'error': error
        }
        self.logger.error(f"Processing error at {stage}: {error}", extra={'extra_data': error_data})


# Global logger instances
app_logger = Logger.get_logger('app', log_file='logs/app.log', console=True)
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
error_logger = ErrorLogger()


def setup_logging(config_dict: dict = None):
    """
    Setup logging based on configuration
    
    Args:
        config_dict: Configuration dictionary with logging settings
    """
    if config_dict is None:
        config_dict = {
            'log_level': 'INFO',
            'log_file': 'logs/app.log',
            'enable_console_logging': True,
            'json_format': False
        }
    
    # Setup main application logger
    global app_logger
    app_logger = Logger.get_logger(
        'app',
        log_level=config_dict.get('log_level', 'INFO'),
        log_file=config_dict.get('log_file', 'logs/app.log'),
        console=config_dict.get('enable_console_logging', True),
        json_format=config_dict.get('json_format', False)
    )
    
    app_logger.info("Logging system initialized")
    return app_logger


if __name__ == "__main__":
    # Test logging system
    print("=== Testing Logging System ===\n")
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Test basic logging
    test_logger = Logger.get_logger('test', log_level='DEBUG', log_file='logs/test.log')
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    # Test audit logging
    audit = AuditLogger()
    audit.log_file_upload('test.pdf', 1024, 'PDF')
    audit.log_classification('test.pdf', 'Invoice', 0.95)
    
    # Test performance logging
    perf = PerformanceLogger()
    perf.log_processing_time('test_operation', 1.234, input_size=1000)
    
    # Test error logging
    error = ErrorLogger()
    try:
        raise ValueError("Test exception")
    except Exception as e:
        error.log_exception(e, context="test_context")
    
    print("\nLogging tests completed. Check logs/ directory for output files.")
