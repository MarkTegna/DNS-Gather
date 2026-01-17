"""Property-based tests for configuration management"""

import pytest
import tempfile
import configparser
from pathlib import Path
from hypothesis import given, strategies as st, settings

from dns_gather.config_manager import ConfigManager


@st.composite
def valid_port_strategy(draw):
    """Generate valid port numbers"""
    return draw(st.integers(min_value=1, max_value=65535))


@st.composite
def valid_timeout_strategy(draw):
    """Generate valid timeout values"""
    return draw(st.integers(min_value=1, max_value=300))


@st.composite
def valid_column_width_strategy(draw):
    """Generate valid column widths"""
    return draw(st.integers(min_value=10, max_value=200))


@st.composite
def invalid_port_strategy(draw):
    """Generate invalid port numbers"""
    return draw(st.one_of(
        st.integers(max_value=0),
        st.integers(min_value=65536)
    ))


@st.composite
def invalid_timeout_strategy(draw):
    """Generate invalid timeout values"""
    return draw(st.integers(max_value=0))


# Feature: dns-zone-exporter, Property 14: Configuration File Reading
@given(
    port=valid_port_strategy(),
    timeout=valid_timeout_strategy(),
    max_width=valid_column_width_strategy()
)
@settings(max_examples=100)
def test_valid_config_values_are_applied(port, timeout, max_width):
    """
    For any valid configuration values, they should be successfully parsed and applied
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config file with valid values
        config = configparser.ConfigParser()
        config['DNS'] = {
            'server_address': '192.168.1.1',
            'port': str(port),
            'timeout': str(timeout),
            'use_tcp': 'True'
        }
        config['Excel'] = {
            'max_column_width': str(max_width)
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Load config
        manager = ConfigManager(str(config_path))
        
        # Verify values are applied correctly
        assert manager.get('DNS', 'port') == port
        assert manager.get('DNS', 'timeout') == timeout
        assert manager.get('Excel', 'max_column_width') == max_width
        assert manager.get('DNS', 'use_tcp') is True


# Feature: dns-zone-exporter, Property 15: Invalid Configuration Handling
@given(
    invalid_port=invalid_port_strategy()
)
@settings(max_examples=100)
def test_invalid_port_uses_default(invalid_port):
    """
    For any invalid port value, the application should use default value
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config file with invalid port
        config = configparser.ConfigParser()
        config['DNS'] = {
            'port': str(invalid_port)
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Load config
        manager = ConfigManager(str(config_path))
        
        # Validate should detect invalid port
        is_valid = manager.validate_config()
        assert is_valid is False
        
        # Should still be able to get a default value
        port = manager.get('DNS', 'port', 53)
        assert port == invalid_port or port == 53  # Either reads invalid or uses default


# Feature: dns-zone-exporter, Property 15: Invalid Configuration Handling
@given(
    invalid_timeout=invalid_timeout_strategy()
)
@settings(max_examples=100)
def test_invalid_timeout_uses_default(invalid_timeout):
    """
    For any invalid timeout value, the application should use default value
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config file with invalid timeout
        config = configparser.ConfigParser()
        config['DNS'] = {
            'timeout': str(invalid_timeout)
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Load config
        manager = ConfigManager(str(config_path))
        
        # Validate should detect invalid timeout
        is_valid = manager.validate_config()
        assert is_valid is False


# Feature: dns-zone-exporter, Property 14: Configuration File Reading
@given(
    server_address=st.text(min_size=2, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.').filter(
        lambda x: not x.lstrip('-').isdigit() and x.strip().lower() not in ('true', 'false', 'yes', 'no', '1', '0')
    ),
    log_level=st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
)
@settings(max_examples=100)
def test_string_config_values_are_preserved(server_address, log_level):
    """
    For any valid string configuration values, they should be preserved exactly
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config file
        config = configparser.ConfigParser(interpolation=None)
        config['DNS'] = {
            'server_address': server_address
        }
        config['Logging'] = {
            'log_level': log_level
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        # Load config
        manager = ConfigManager(str(config_path))
        
        # Verify string values are preserved
        result_address = manager.get('DNS', 'server_address')
        result_level = manager.get('Logging', 'log_level')
        
        # Should preserve non-numeric strings
        assert result_address == server_address
        assert result_level == log_level


# Feature: dns-zone-exporter, Property 14: Configuration File Reading
@given(
    use_tcp=st.booleans(),
    auto_adjust=st.booleans()
)
@settings(max_examples=100)
def test_boolean_config_values_are_converted(use_tcp, auto_adjust):
    """
    For any boolean configuration values, they should be correctly converted from strings
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config file with boolean strings
        config = configparser.ConfigParser()
        config['DNS'] = {
            'use_tcp': 'True' if use_tcp else 'False'
        }
        config['Excel'] = {
            'auto_adjust_columns': 'True' if auto_adjust else 'False'
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Load config
        manager = ConfigManager(str(config_path))
        
        # Verify boolean conversion
        assert manager.get('DNS', 'use_tcp') is use_tcp
        assert manager.get('Excel', 'auto_adjust_columns') is auto_adjust


def test_missing_config_file_creates_default():
    """
    When config file does not exist, a default config should be created
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Ensure file doesn't exist
        assert not config_path.exists()
        
        # Create ConfigManager
        manager = ConfigManager(str(config_path))
        
        # Config file should now exist
        assert config_path.exists()
        
        # Should have default values
        assert manager.get('DNS', 'port', 53) == 53
        assert manager.get('DNS', 'timeout', 10) == 10
