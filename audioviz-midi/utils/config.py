# utils/config.py
"""
Configuration management for AudioViz MIDI application.
Handles loading, saving, and accessing user settings.
"""

import json
import os
from typing import Any, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration with JSON persistence."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "audio": {
            "sample_rate": 22050,
            "hop_length": 512,
            "normalize": True,
            "mono_conversion": True
        },
        "pitch_detection": {
            "algorithm": "piptrack",  # Options: piptrack, pyin
            "fmin": 65.0,  # Lowest frequency (C2 for guitar/piano)
            "fmax": 2093.0,  # Highest frequency (C7)
            "threshold": 0.1,  # Confidence threshold
            "min_note_duration": 0.05  # Minimum note duration in seconds
        },
        "midi": {
            "default_velocity": 80,  # MIDI velocity (0-127)
            "quantize": True,
            "remove_short_notes": True,
            "fill_gaps": True
        },
        "visualization": {
            "color_scheme": "chromatic",  # Options: chromatic, octave, velocity, rainbow
            "fps": 60,
            "show_grid": True,
            "show_keyboard": True,
            "note_height": 10,
            "background_color": [30, 30, 40],  # RGB
            "grid_color": [60, 60, 70],  # RGB
            "playhead_color": [255, 100, 100]  # RGB
        },
        "playback": {
            "default_speed": 1.0,
            "default_volume": 0.8,
            "loop_enabled": False
        },
        "export": {
            "default_format": "midi",  # Options: midi, json
            "default_directory": "exports",
            "include_metadata": True
        },
        "ui": {
            "window_width": 1920,
            "window_height": 1080,
            "theme": "dark",
            "last_directory": ""
        }
    }
    
    def __init__(self, config_file='config.json'):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default if not exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_file}")
                
                # Merge with defaults to handle missing keys
                self.config = self._merge_configs(self.DEFAULT_CONFIG, self.config)
            except Exception as e:
                logger.error(f"Error loading config: {e}. Using defaults.")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            logger.info("Config file not found. Creating default configuration.")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key within section
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key within section
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        logger.debug(f"Config updated: {section}.{key} = {value}")
    
    def get_section(self, section: str) -> Dict:
        """
        Get entire configuration section.
        
        Args:
            section: Configuration section name
        
        Returns:
            Dictionary of section configuration
        """
        return self.config.get(section, {})
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """
        Recursively merge user config with defaults.
        
        Args:
            default: Default configuration dictionary
            user: User configuration dictionary
        
        Returns:
            Merged configuration dictionary
        """
        merged = default.copy()
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
