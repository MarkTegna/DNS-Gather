"""ASCII-compatible logging for DNS-Gather"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class ASCIILogger:
    """Logger that uses ASCII-only characters for Windows compatibility"""
    
    # ASCII character mappings for Unicode replacements
    ASCII_REPLACEMENTS = {
        # Box drawing characters
        '║': '|',
        '╔': '+',
        '╚': '+',
        '╠': '+',
        '═': '=',
        '─': '-',
        '│': '|',
        '┌': '+',
        '└': '+',
        '├': '+',
        '┤': '+',
        '┬': '+',
        '┴': '+',
        '┼': '+',
        # Status symbols
        '✓': '[OK]',
        '✗': '[FAIL]',
        '⚠': '[WARN]',
        '●': '*',
        '○': 'o',
        '►': '>',
        '◄': '<',
        # Progress indicators
        '█': '#',
        '▓': '#',
        '▒': '+',
        '░': '.',
    }
    
    def __init__(self, log_file: str, log_level: str = 'INFO'):
        """
        Initialize ASCII logger
        
        Args:
            log_file: Path to log file
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_file = Path(log_file)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create log directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Set up logger
        self.logger = logging.getLogger('DNS-Gather')
        self.logger.setLevel(self.log_level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create file handler with ASCII encoding
        self.file_handler = logging.FileHandler(
            self.log_file,
            mode='w',
            encoding='ascii',
            errors='replace'  # Replace non-ASCII with ?
        )
        self.file_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(self.file_handler)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
    
    def close(self) -> None:
        """Close the logger and release file handles"""
        if hasattr(self, 'file_handler'):
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)
    
    def _sanitize_message(self, message: str) -> str:
        """
        Replace Unicode characters with ASCII equivalents
        
        Args:
            message: Message to sanitize
        
        Returns:
            ASCII-compatible message
        """
        for unicode_char, ascii_char in self.ASCII_REPLACEMENTS.items():
            message = message.replace(unicode_char, ascii_char)
        
        # Replace any remaining non-ASCII characters
        return message.encode('ascii', errors='replace').decode('ascii')
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(self._sanitize_message(message))
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(self._sanitize_message(message))
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(self._sanitize_message(message))
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(self._sanitize_message(message))
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(self._sanitize_message(message))
    
    def log_operation(self, operation: str, status: str, details: str = '') -> None:
        """
        Log an operation with status
        
        Args:
            operation: Operation name
            status: Status (OK, FAIL, WARN)
            details: Additional details
        """
        status_symbol = {
            'OK': '[OK]',
            'FAIL': '[FAIL]',
            'WARN': '[WARN]'
        }.get(status, status)
        
        message = f"{operation} {status_symbol}"
        if details:
            message += f" - {details}"
        
        if status == 'FAIL':
            self.error(message)
        elif status == 'WARN':
            self.warning(message)
        else:
            self.info(message)


def create_logger(log_directory: str, log_filename_format: str, log_level: str = 'INFO') -> ASCIILogger:
    """
    Create a logger with timestamped filename
    
    Args:
        log_directory: Directory for log files
        log_filename_format: Filename format (strftime format)
        log_level: Logging level
    
    Returns:
        Configured ASCIILogger instance
    """
    # Create timestamped filename
    timestamp = datetime.now()
    log_filename = timestamp.strftime(log_filename_format)
    log_path = Path(log_directory) / log_filename
    
    return ASCIILogger(str(log_path), log_level)
