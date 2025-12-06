import json
import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from streamdeck_pi.core.button import Button

logger = logging.getLogger(__name__)

@dataclass
class Page:
    """Represents a page of buttons."""
    id: str
    title: str
    buttons: Dict[int, Button] = field(default_factory=dict)
    bg_color: Optional[tuple] = None
    text_color: Optional[tuple] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "buttons": {str(k): v.to_dict() for k, v in self.buttons.items()},
            "bg_color": self.bg_color,
            "text_color": self.text_color
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Page":
        buttons = {}
        for k, v in data.get("buttons", {}).items():
            buttons[int(k)] = Button.from_dict(v)

        bg_color = data.get("bg_color")
        if bg_color:
            bg_color = tuple(bg_color)

        text_color = data.get("text_color")
        if text_color:
            text_color = tuple(text_color)

        return cls(
            id=data.get("id", "default"),
            title=data.get("title", "Default"),
            buttons=buttons,
            bg_color=bg_color,
            text_color=text_color
        )

class ConfigManager:
    """Manages configuration persistence."""

    def __init__(self, config_path: str = "buttons.json"):
        self.config_path = config_path

    def load_config(self) -> Dict[str, Any]:
        """Load configuration (pages) from file."""
        default_config = {
            "pages": {"default": Page(id="default", title="Home", buttons={})},
            "current_page_id": "default"
        }

        if not os.path.exists(self.config_path):
            return default_config

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            # Check if it's the old format (keys are numbers)
            # If data is empty, treat as old format (empty dict)
            is_old_format = not data or any(k.isdigit() for k in data.keys())

            if is_old_format:
                buttons = {}
                for k, v in data.items():
                    if k.isdigit():
                        buttons[int(k)] = Button.from_dict(v)
                page = Page(id="default", title="Home", buttons=buttons)
                return {"pages": {"default": page}, "current_page_id": "default"}

            # New format
            pages = {}
            for p_id, p_data in data.get("pages", {}).items():
                pages[p_id] = Page.from_dict(p_data)

            if not pages:
                 return default_config

            return {
                "pages": pages,
                "current_page_id": data.get("current_page_id", list(pages.keys())[0])
            }
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return default_config

    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            data = {
                "pages": {p_id: p.to_dict() for p_id, p in config["pages"].items()},
                "current_page_id": config["current_page_id"]
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info("Saved configuration")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def load_buttons(self) -> Dict[int, Button]:
        """Deprecated: Load button configurations from file (returns current page buttons)."""
        config = self.load_config()
        current_page_id = config["current_page_id"]
        return config["pages"][current_page_id].buttons

    def save_buttons(self, buttons: Dict[int, Button]):
        """Deprecated: Save button configurations to file (saves to current page)."""
        # This is tricky because we need the full config to save.
        # We'll load, update current page, and save.
        config = self.load_config()
        current_page_id = config["current_page_id"]
        config["pages"][current_page_id].buttons = buttons
        self.save_config(config)
