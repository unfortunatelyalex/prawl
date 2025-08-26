import os
import sys
import configparser
import dearpygui.dearpygui as dpg

import os
import sys
import configparser
import dearpygui.dearpygui as dpg
from typing import Dict, Any
import logging
from scripts.constants import (
    CONFIG_FILENAME, 
    ICON_PATH, 
    MAIN_FONT_PATH, 
    ICON_FONT_PATH, 
    DEFAULT_CONFIG
)

# Set up logging
logger = logging.getLogger(__name__)

def get_platform() -> str:
    """
    Get the current platform and validate it's supported.
    
    Returns:
        Platform string if Windows, raises OSError otherwise
    """
    platform = sys.platform
    if platform.lower().startswith('win'):
        return platform
    else:
        raise OSError('Unsupported operating system - Windows required')

def script_dir() -> str:
    """
    Get the directory containing the script or executable.
    
    Returns:
        Directory path as string
    """
    if getattr(sys, 'frozen', False):
        # Running as executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(sys.argv[0]))

class Config:
    def __init__(self, filepath: str = CONFIG_FILENAME):
        self.version = '0.1.0'
        self.filepath = os.path.join(script_dir(), filepath)
        self.icon = os.path.join(script_dir(), ICON_PATH)
        self.main_font = os.path.join(script_dir(), MAIN_FONT_PATH)
        self.icon_font = os.path.join(script_dir(), ICON_FONT_PATH)
        self.defaults = DEFAULT_CONFIG.copy()
        self.config = configparser.ConfigParser()
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file, creating defaults if necessary."""
        try:
            self.config.read(self.filepath)

            if not self.config.has_section('settings'):
                self.config.add_section('settings')

            updated = False
            for key, value in self.defaults.items():
                if not self.config.has_option('settings', key):
                    self.config.set('settings', key, str(value))
                    updated = True

            if updated:
                self._write_config()

            # Load values with proper type conversion
            for key, default_value in self.defaults.items():
                try:
                    if isinstance(default_value, bool):
                        self.data[key] = self.config.getboolean('settings', key)
                    elif isinstance(default_value, int):
                        self.data[key] = self.config.getint('settings', key)
                    elif isinstance(default_value, float):
                        self.data[key] = self.config.getfloat('settings', key)
                    else:
                        self.data[key] = self.config.get('settings', key)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid config value for {key}: {e}, using default")
                    self.data[key] = default_value
                    
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Use defaults if config loading fails
            self.data = self.defaults.copy()

    def save(self) -> None:
        """Save current configuration to file."""
        config_to_save = {
            'match_time': 'match_time',
            'timer_sound': 'timer_sound',
            'always_on_top': 'always_on_top',
            'game_start_spam': 'start_spam',
            'game_restart_delay': 'wait_restart',
            'game_load_time': 'wait_gameload',
            'menu_key_presses': 'menu_key_presses',
            'menu_key_presses_delay': 'menu_key_presses_delay',
            'disconnect_delay': 'wait_disconnect',
            'reconnect_delay': 'wait_reconnect',
            'open_menu_default': 'open_menu_default',
            'open_menu_fix': 'open_menu_fix',
            'open_menu_fix2': 'open_menu_fix2',
            'open_menu_hold': 'open_menu_hold',
            'open_menu_enter': 'open_menu_enter',
            'direct_input': 'direct_input',
            'keypress_hold': 'keypress_hold',
            'keypress_delay': 'keypress_delay',
            'beep_frequency': 'beep_frequency',
            'beep_duration': 'beep_duration',
            'rate_limit_detect': 'rate_limit_detect',
            'rate_limit_wait': 'rate_limit_wait',
            'rate_limit_wait_time': 'rate_limit_wait_time',
            'max_games': 'max_games',
            'max_games_amount': 'max_games_amount',
            'auto_launch': 'auto_launch',
            'key_light': 'key_light',
            'key_heavy': 'key_heavy',
            'key_throw': 'key_throw',
            'key_left': 'key_left',
            'key_up': 'key_up',
            'key_right': 'key_right',
            'key_down': 'key_down',
        }

        try:
            if not self.config.has_section('settings'):
                self.config.add_section('settings')

            for config_key, dpg_tag in config_to_save.items():
                if dpg.does_item_exist(dpg_tag):
                    value = dpg.get_value(dpg_tag)
                    self.data[config_key] = value
                    self.config.set('settings', config_key, str(value))

            self._write_config()
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _write_config(self) -> None:
        """Write configuration to file."""
        try:
            with open(self.filepath, 'w') as f:
                self.config.write(f)
        except IOError as e:
            logger.error(f"Could not write config file: {e}")
            raise
