"""Configuration management for ROM Duplicate Manager."""

import configparser
import os
from typing import Dict, Any

# Configuration file name
CONFIG_FILE = 'rom_duplicate_manager.ini'


def load_config() -> configparser.ConfigParser:
    """Load application configuration from INI file.

    Returns:
        ConfigParser object with loaded settings or empty if file doesn't exist
    """
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


def save_config(dark_mode: bool, row_colors: bool, language: str, smart_select: bool,
                scan_images: bool, match_size: bool, permanent_delete: bool,
                use_regex: bool, file_type: str, search_in_path: bool, theme: str = 'darkly') -> None:
    """Save application configuration to INI file.

    Args:
        dark_mode: Whether dark mode is enabled
        row_colors: Whether alternating row colors are enabled
        language: Preferred language setting
        smart_select: Whether smart selection is enabled
        scan_images: Whether image scanning is enabled
        match_size: Whether size-based matching is enabled
        permanent_delete: Whether permanent deletion is enabled
        use_regex: Whether regex filtering is enabled
        file_type: Current file type filter
        search_in_path: Whether to search in full file paths
        theme: Current ttkbootstrap theme name
    """
    config = configparser.ConfigParser()
    config['Settings'] = {
        'dark_mode': str(dark_mode),
        'row_colors': str(row_colors),
        'language': str(language),
        'smart_select': str(smart_select),
        'scan_images': str(scan_images),
        'match_size': str(match_size),
        'permanent_delete': str(permanent_delete),
        'use_regex': str(use_regex),
        'file_type': str(file_type),
        'search_in_path': str(search_in_path),
        'theme': str(theme)
    }
    with open(CONFIG_FILE, 'w') as f:
        config.write(f)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration values.

    Returns:
        Dictionary of default configuration values
    """
    return {
        'dark_mode': False,
        'row_colors': True,
        'language': 'English',
        'smart_select': True,
        'scan_images': True,
        'match_size': False,
        'permanent_delete': False,
        'use_regex': False,
        'file_type': 'Archives',
        'search_in_path': False
    }