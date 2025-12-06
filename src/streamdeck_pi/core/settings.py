import json
import os
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages application-wide settings (config.json)."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        if not self.config_path:
            # Default paths
            paths = [
                Path("/etc/streamdeck-pi/config.json"),
                Path("config/config.json"),
                Path("config.json")
            ]
            for p in paths:
                if p.exists():
                    self.config_path = str(p)
                    break

        if self.config_path:
            logger.info(f"Loading settings from {self.config_path}")
            self.settings = self.load_settings()
            logger.info(f"Loaded settings keys: {list(self.settings.keys())}")
        else:
            logger.warning("No configuration file found in default locations.")
            self.settings = {}

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        if not self.config_path or not os.path.exists(self.config_path):
            logger.warning(f"Settings file not found: {self.config_path}")
            return {}

        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self.settings.get(key, default)
