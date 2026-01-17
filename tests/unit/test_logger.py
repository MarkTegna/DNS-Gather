"""Unit tests for ASCIILogger"""

import pytest
import tempfile
import re
from pathlib import Path
from datetime import datetime

from dns_gather.logger import ASCIILogger, create_logger


def test_logger_creates_log_file():
    """Test that logger creates log file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.info("Test message")
        
        assert log_file.exists()


def test_logger_creates_log_directory():
    """Test that logger creates log directory if it doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'logs' / 'test.log'
        
        # Directory doesn't exist yet
        assert not log_file.parent.exists()
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.info("Test message")
        
        # Directory should now exist
        assert log_file.parent.exists()
        assert log_file.exists()


def test_log_file_has_timestamp_format():
    """Test that log filename uses YYYYMMDD-HH-MM format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / 'logs'
        log_format = 'DNS-Gather_%Y%m%d-%H-%M.log'
        
        with create_logger(str(log_dir), log_format, 'INFO') as logger:
            logger.info("Test")
        
        # Find log file
        log_files = list(log_dir.glob('*.log'))
        assert len(log_files) == 1
        
        # Verify filename format
        filename = log_files[0].name
        pattern = r'DNS-Gather_\d{8}-\d{2}-\d{2}\.log'
        assert re.match(pattern, filename)


def test_ascii_character_replacement():
    """Test that Unicode characters are replaced with ASCII"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            # Log message with Unicode characters
            logger.info("Status: ✓ Success")
            logger.info("Error: ✗ Failed")
            logger.info("Box: ║ ═ ╔ ╚")
        
        # Read log content
        content = log_file.read_text(encoding='ascii', errors='replace')
        
        # Verify Unicode characters are not present
        assert '✓' not in content
        assert '✗' not in content
        assert '║' not in content
        assert '═' not in content
        
        # Verify ASCII replacements are present
        assert '[OK]' in content or '?' in content
        assert '[FAIL]' in content or '?' in content
        assert '|' in content or '?' in content
        assert '=' in content or '?' in content


def test_log_levels():
    """Test different log levels"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'DEBUG') as logger:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
        
        content = log_file.read_text()
        
        assert 'DEBUG' in content
        assert 'INFO' in content
        assert 'WARNING' in content
        assert 'ERROR' in content
        assert 'CRITICAL' in content


def test_log_level_filtering():
    """Test that log level filtering works"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Set log level to WARNING
        with ASCIILogger(str(log_file), 'WARNING') as logger:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
        
        content = log_file.read_text()
        
        # DEBUG and INFO should not be logged
        assert 'Debug message' not in content
        assert 'Info message' not in content
        
        # WARNING and ERROR should be logged
        assert 'Warning message' in content
        assert 'Error message' in content


def test_log_operation_with_ok_status():
    """Test log_operation with OK status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.log_operation("Connect to DNS", "OK", "Connected successfully")
        
        content = log_file.read_text()
        
        assert 'Connect to DNS' in content
        assert '[OK]' in content
        assert 'Connected successfully' in content
        assert 'INFO' in content


def test_log_operation_with_fail_status():
    """Test log_operation with FAIL status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.log_operation("Zone transfer", "FAIL", "Connection timeout")
        
        content = log_file.read_text()
        
        assert 'Zone transfer' in content
        assert '[FAIL]' in content
        assert 'Connection timeout' in content
        assert 'ERROR' in content


def test_log_operation_with_warn_status():
    """Test log_operation with WARN status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.log_operation("Config validation", "WARN", "Using default value")
        
        content = log_file.read_text()
        
        assert 'Config validation' in content
        assert '[WARN]' in content
        assert 'Using default value' in content
        assert 'WARNING' in content


def test_log_operation_without_details():
    """Test log_operation without details"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.log_operation("Initialize", "OK")
        
        content = log_file.read_text()
        
        assert 'Initialize' in content
        assert '[OK]' in content


def test_log_message_format():
    """Test that log messages have correct format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            logger.info("Test message")
        
        content = log_file.read_text()
        
        # Verify format: YYYY-MM-DD HH:MM:SS | LEVEL | MESSAGE
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \| INFO\s+\| Test message'
        assert re.search(pattern, content)


def test_sanitize_message_preserves_ascii():
    """Test that ASCII characters are preserved"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        with ASCIILogger(str(log_file), 'INFO') as logger:
            ascii_message = "Test 123 ABC xyz !@#$%"
            logger.info(ascii_message)
        
        content = log_file.read_text()
        
        # All ASCII characters should be preserved
        assert 'Test 123 ABC xyz !@#$%' in content
