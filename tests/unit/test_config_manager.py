"""Unit tests for ConfigManager"""

import pytest
import tempfile
import configparser
from pathlib import Path

from dns_gather.config_manager import ConfigManager


def test_create_default_config():
    """Test that default config file is created when it doesn't exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Ensure file doesn't exist
        assert not config_path.exists()
        
        # Create ConfigManager
        manager = ConfigManager(str(config_path))
        
        # Config file should now exist
        assert config_path.exists()
        
        # Verify it has all sections
        config = configparser.ConfigParser()
        config.read(config_path)
        
        assert 'DNS' in config.sections()
        assert 'Authentication' in config.sections()
        assert 'Output' in config.sections()
        assert 'Excel' in config.sections()
        assert 'Logging' in config.sections()


def test_default_config_has_commented_options():
    """Test that default config has commented out optional settings"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create default config
        manager = ConfigManager(str(config_path))
        
        # Read file content
        content = config_path.read_text()
        
        # Verify commented options exist
        assert '# tsig_keyname' in content
        assert '# tsig_secret' in content
        assert '# tsig_algorithm' in content


def test_load_existing_config():
    """Test loading an existing configuration file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create a config file
        config = configparser.ConfigParser()
        config['DNS'] = {
            'server_address': '10.0.0.1',
            'port': '5353',
            'timeout': '30'
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        # Load config
        manager = ConfigManager(str(config_path))
        
        # Verify values
        assert manager.get('DNS', 'server_address') == '10.0.0.1'
        assert manager.get('DNS', 'port') == 5353
        assert manager.get('DNS', 'timeout') == 30


def test_get_with_default():
    """Test getting config value with default fallback"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        manager = ConfigManager(str(config_path))
        
        # Get non-existent value with default
        value = manager.get('NonExistent', 'key', 'default_value')
        assert value == 'default_value'


def test_boolean_conversion():
    """Test that boolean strings are converted correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config with boolean values
        config = configparser.ConfigParser()
        config['Test'] = {
            'true_value': 'True',
            'false_value': 'False',
            'yes_value': 'yes',
            'no_value': 'no',
            '1_value': '1',
            '0_value': '0'
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        manager = ConfigManager(str(config_path))
        
        # Verify boolean conversion
        assert manager.get('Test', 'true_value') is True
        assert manager.get('Test', 'false_value') is False
        assert manager.get('Test', 'yes_value') is True
        assert manager.get('Test', 'no_value') is False
        assert manager.get('Test', '1_value') is True
        assert manager.get('Test', '0_value') is False


def test_integer_conversion():
    """Test that integer strings are converted correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config with integer values
        config = configparser.ConfigParser()
        config['Test'] = {
            'port': '8080',
            'timeout': '60',
            'count': '100'
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        manager = ConfigManager(str(config_path))
        
        # Verify integer conversion
        assert manager.get('Test', 'port') == 8080
        assert manager.get('Test', 'timeout') == 60
        assert manager.get('Test', 'count') == 100


def test_validate_config_with_invalid_port():
    """Test validation detects invalid port"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config with invalid port
        config = configparser.ConfigParser()
        config['DNS'] = {
            'port': '99999'  # Invalid port
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        manager = ConfigManager(str(config_path))
        
        # Validation should fail
        assert manager.validate_config() is False


def test_validate_config_with_invalid_timeout():
    """Test validation detects invalid timeout"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config with invalid timeout
        config = configparser.ConfigParser()
        config['DNS'] = {
            'timeout': '-5'  # Invalid timeout
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        manager = ConfigManager(str(config_path))
        
        # Validation should fail
        assert manager.validate_config() is False


def test_validate_config_creates_directories():
    """Test that validation creates output and log directories"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        output_dir = Path(tmpdir) / 'output'
        log_dir = Path(tmpdir) / 'logs'
        
        # Create config with custom directories
        config = configparser.ConfigParser()
        config['Output'] = {
            'output_directory': str(output_dir)
        }
        config['Logging'] = {
            'log_directory': str(log_dir)
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        manager = ConfigManager(str(config_path))
        
        # Directories should not exist yet
        assert not output_dir.exists()
        assert not log_dir.exists()
        
        # Validate config
        manager.validate_config()
        
        # Directories should now exist
        assert output_dir.exists()
        assert log_dir.exists()


def test_validate_config_with_valid_values():
    """Test validation passes with all valid values"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'test.ini'
        
        # Create config with valid values
        config = configparser.ConfigParser()
        config['DNS'] = {
            'port': '53',
            'timeout': '10'
        }
        config['Excel'] = {
            'max_column_width': '50'
        }
        config['Output'] = {
            'output_directory': str(Path(tmpdir) / 'output')
        }
        config['Logging'] = {
            'log_directory': str(Path(tmpdir) / 'logs')
        }
        
        with open(config_path, 'w') as f:
            config.write(f)
        
        manager = ConfigManager(str(config_path))
        
        # Validation should pass
        assert manager.validate_config() is True
