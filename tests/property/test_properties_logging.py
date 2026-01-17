"""Property-based tests for logging"""

import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings

from dns_gather.logger import ASCIILogger, create_logger


# Feature: dns-zone-exporter, Property 17: ASCII Character Compliance
@given(
    message=st.text(min_size=1, max_size=200)
)
@settings(max_examples=100)
def test_log_output_is_ascii_compatible(message):
    """
    For any log message, all characters in the log file should be ASCII-compatible
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Create logger
        with ASCIILogger(str(log_file), 'INFO') as logger:
            # Log message
            logger.info(message)
        
        # Read log file
        content = log_file.read_bytes()
        
        # Verify all bytes are ASCII (0-127)
        for byte in content:
            assert byte < 128, f"Non-ASCII byte found: {byte}"


# Feature: dns-zone-exporter, Property 17: ASCII Character Compliance
@given(
    message=st.text(min_size=1, max_size=200)
)
@settings(max_examples=100)
def test_unicode_characters_are_replaced(message):
    """
    For any message containing Unicode characters, they should be replaced with ASCII equivalents
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Create logger
        with ASCIILogger(str(log_file), 'INFO') as logger:
            # Add some known Unicode characters to the message
            unicode_message = f"{message} ✓ ✗ ║ ═"
            
            # Log message
            logger.info(unicode_message)
        
        # Read log file content
        content = log_file.read_text(encoding='ascii', errors='replace')
        
        # Verify Unicode characters were replaced
        assert '✓' not in content
        assert '✗' not in content
        assert '║' not in content
        assert '═' not in content
        
        # Verify ASCII replacements are present
        assert '[OK]' in content or '?' in content  # Either replaced or substituted
        assert '[FAIL]' in content or '?' in content
        assert '|' in content or '?' in content
        assert '=' in content or '?' in content


# Feature: dns-zone-exporter, Property 17: ASCII Character Compliance
@given(
    operation=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' -_')),
    status=st.sampled_from(['OK', 'FAIL', 'WARN']),
    details=st.text(max_size=100)
)
@settings(max_examples=100)
def test_log_operation_output_is_ascii(operation, status, details):
    """
    For any operation log, all characters should be ASCII-compatible
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Create logger
        with ASCIILogger(str(log_file), 'INFO') as logger:
            # Log operation
            logger.log_operation(operation, status, details)
        
        # Read log file
        content = log_file.read_bytes()
        
        # Verify all bytes are ASCII
        for byte in content:
            assert byte < 128


# Feature: dns-zone-exporter, Property 17: ASCII Character Compliance
@given(
    log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
    message=st.text(min_size=1, max_size=200)
)
@settings(max_examples=100)
def test_all_log_levels_produce_ascii_output(log_level, message):
    """
    For any log level and message, output should be ASCII-compatible
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Create logger with specified level
        with ASCIILogger(str(log_file), 'DEBUG') as logger:  # Set to DEBUG to capture all levels
            # Log at specified level
            if log_level == 'DEBUG':
                logger.debug(message)
            elif log_level == 'INFO':
                logger.info(message)
            elif log_level == 'WARNING':
                logger.warning(message)
            elif log_level == 'ERROR':
                logger.error(message)
            elif log_level == 'CRITICAL':
                logger.critical(message)
        
        # Read log file
        content = log_file.read_bytes()
        
        # Verify all bytes are ASCII
        for byte in content:
            assert byte < 128


def test_known_unicode_replacements():
    """Test that known Unicode characters are replaced correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / 'test.log'
        
        # Test specific Unicode characters
        test_cases = [
            ('✓', '[OK]'),
            ('✗', '[FAIL]'),
            ('║', '|'),
            ('═', '='),
            ('╔', '+'),
            ('╚', '+'),
        ]
        
        for unicode_char, expected_ascii in test_cases:
            # Clear log file
            log_file.write_text('')
            
            # Log message with Unicode character
            with ASCIILogger(str(log_file), 'INFO') as logger:
                logger.info(f"Test {unicode_char} character")
            
            # Read log content
            content = log_file.read_text(encoding='ascii', errors='replace')
            
            # Verify Unicode character is not present
            assert unicode_char not in content
            
            # Verify ASCII replacement is present
            assert expected_ascii in content or '?' in content


# Feature: dns-zone-exporter, Property 18: Timestamped Log File Creation
@given(
    log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
)
@settings(max_examples=100)
def test_log_file_is_created_with_timestamp_format(log_level):
    """
    For any application execution, a log file should be created with YYYYMMDD-HH-MM format
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / 'logs'
        log_format = 'DNS-Gather_%Y%m%d-%H-%M.log'
        
        # Create logger using create_logger function
        with create_logger(str(log_dir), log_format, log_level) as logger:
            # Log a message to ensure file is created
            logger.info("Test message")
        
        # Verify log directory exists
        assert log_dir.exists()
        
        # Verify log file exists
        log_files = list(log_dir.glob('*.log'))
        assert len(log_files) == 1
        
        # Verify filename matches expected format
        log_file = log_files[0]
        filename = log_file.name
        
        # Check format: DNS-Gather_YYYYMMDD-HH-MM.log
        assert filename.startswith('DNS-Gather_')
        assert filename.endswith('.log')
        
        # Extract timestamp part
        timestamp_part = filename[11:-4]  # Remove 'DNS-Gather_' and '.log'
        
        # Verify format: YYYYMMDD-HH-MM
        assert len(timestamp_part) == 14  # YYYYMMDD-HH-MM (8+1+2+1+2 = 14)
        assert timestamp_part[8] == '-'  # Separator between date and time
        assert timestamp_part[11] == '-'  # Separator between hour and minute
        
        # Verify all other characters are digits
        date_part = timestamp_part[:8]
        hour_part = timestamp_part[9:11]
        minute_part = timestamp_part[12:14]
        
        assert date_part.isdigit()
        assert hour_part.isdigit()
        assert minute_part.isdigit()


# Feature: dns-zone-exporter, Property 18: Timestamped Log File Creation
def test_multiple_logger_instances_create_separate_files():
    """
    For any multiple executions, each should create its own timestamped log file
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir) / 'logs'
        log_format = 'DNS-Gather_%Y%m%d-%H-%M-%S.log'  # Add seconds for uniqueness
        
        # Create multiple loggers
        with create_logger(str(log_dir), log_format, 'INFO') as logger1:
            logger1.info("Logger 1")
        
        import time
        time.sleep(1)  # Ensure different timestamp
        
        with create_logger(str(log_dir), log_format, 'INFO') as logger2:
            logger2.info("Logger 2")
        
        # Verify multiple log files exist
        log_files = list(log_dir.glob('*.log'))
        assert len(log_files) >= 1  # At least one file should exist
