import json
import os
import logging
from typing import Dict
from streamdeck_pi.core.button import Button

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration persistence."""
    
    def __init__(self, config_path: str = "buttons.json"):
        self.config_path = config_path

    def load_buttons(self) -> Dict[int, Button]:
        """Load button configurations from file."""
        if not os.path.exists(self.config_path):
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                
            buttons = {}
            for key_str, button_data in data.items():
                key = int(key_str)
                buttons[key] = Button.from_dict(button_data)
            
            logger.info(f"Loaded {len(buttons)} button configurations")
            return buttons
        except Exception as e:
            logger.error(f"Failed to load button configurations: {e}")
            return {}

    def save_buttons(self, buttons: Dict[int, Button]):
        """Save button configurations to file."""
        try:
            data = {str(k): v.to_dict() for k, v in buttons.items()}
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Saved button configurations")
        except Exception as e:
            logger.error(f"Failed to save button configurations: {e}")
