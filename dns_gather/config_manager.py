"""Configuration management for DNS-Gather"""

import configparser
from pathlib import Path
from typing import Any


class ConfigManager:
    """Manages application configuration from .ini files"""
    
    DEFAULT_CONFIG = {
        'DNS': {
            'server_address': '192.168.168.55',
            'zone_discovery_server': '',
            'port': '53',
            'timeout': '10',
            'use_tcp': 'True'
        },
        'Authentication': {
            '# tsig_keyname': '',
            '# tsig_secret': '',
            '# tsig_algorithm': 'hmac-sha256'
        },
        'Output': {
            'output_directory': './Reports',
            'filename_format': 'DNS-Gather_%Y%m%d-%H-%M.xlsx'
        },
        'Excel': {
            'header_bg_color': '4472C4',
            'header_font_color': 'FFFFFF',
            'auto_adjust_columns': 'True',
            'max_column_width': '50'
        },
        'Logging': {
            'log_level': 'INFO',
            'log_directory': './Logs',
            'log_filename_format': 'DNS-Gather_%Y%m%d-%H-%M.log'
        }
    }
    
    def __init__(self, config_path: str = 'DNS-Gather.ini'):
        """
        Initialize ConfigManager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        self.config.optionxform = str  # Preserve case
        
        # Load or create config
        if not self.config_path.exists():
            self.create_default_config()
        
        self.load_config()
    
    def create_default_config(self) -> None:
        """Create default configuration file with all options"""
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        config.optionxform = str  # Preserve case
        
        # Add sections and options
        for section, options in self.DEFAULT_CONFIG.items():
            config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)
        
        # Write to file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write('# DNS-Gather Configuration File\n')
            f.write('# All configurable options are listed below\n')
            f.write('# Options starting with # are commented out (not active)\n\n')
            config.write(f)
    
    def load_config(self) -> dict:
        """
        Load configuration from file
        
        Returns:
            Dictionary containing configuration
        """
        try:
            self.config.read(self.config_path, encoding='utf-8')
            return {section: dict(self.config.items(section)) 
                   for section in self.config.sections()}
        except Exception as e:
            # If loading fails, use defaults
            print(f"[WARN] Failed to load config: {e}. Using defaults.")
            return {}
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        try:
            value = self.config.get(section, key)
            
            # Convert boolean strings (only exact matches)
            if value.strip().lower() in ('true', 'yes', '1'):
                return True
            elif value.strip().lower() in ('false', 'no', '0'):
                return False
            
            # Try to convert to int (only if it's purely numeric)
            try:
                # Only convert if the entire string is numeric
                if value.strip().lstrip('-').isdigit():
                    return int(value)
            except (ValueError, AttributeError):
                pass
            
            return value
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def validate_config(self) -> bool:
        """
        Validate configuration values
        
        Returns:
            True if configuration is valid
        """
        valid = True
        
        # Validate DNS section
        port = self.get('DNS', 'port', 53)
        if not isinstance(port, int) or port < 1 or port > 65535:
            print(f"[WARN] Invalid DNS port: {port}. Using default: 53")
            valid = False
        
        timeout = self.get('DNS', 'timeout', 10)
        if not isinstance(timeout, int) or timeout < 1:
            print(f"[WARN] Invalid timeout: {timeout}. Using default: 10")
            valid = False
        
        # Validate Excel section
        max_width = self.get('Excel', 'max_column_width', 50)
        if not isinstance(max_width, int) or max_width < 10:
            print(f"[WARN] Invalid max_column_width: {max_width}. Using default: 50")
            valid = False
        
        # Validate paths
        output_dir = self.get('Output', 'output_directory', './output')
        log_dir = self.get('Logging', 'log_directory', './logs')
        
        # Create directories if they don't exist
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[WARN] Failed to create directories: {e}")
            valid = False
        
        return valid
