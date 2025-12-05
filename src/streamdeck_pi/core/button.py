"""
Button configuration and management.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ButtonActionType(str, Enum):
    """Types of button actions."""
    PLUGIN = "plugin"
    SCRIPT = "script"
    HTTP = "http"
    NONE = "none"


@dataclass
class ButtonAction:
    """Represents an action to be executed when a button is pressed."""
    
    type: ButtonActionType
    plugin_id: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "plugin_id": self.plugin_id,
            "config": self.config,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ButtonAction":
        """Create from dictionary."""
        return cls(
            type=ButtonActionType(data.get("type", "none")),
            plugin_id=data.get("plugin_id"),
            config=data.get("config", {}),
        )


@dataclass
class Button:
    """Represents a Stream Deck button configuration."""
    
    key: int
    label: str = ""
    icon: Optional[str] = None
    action: Optional[ButtonAction] = None
    bg_color: tuple = (0, 0, 0)
    text_color: tuple = (255, 255, 255)
    font_size: int = 14
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "label": self.label,
            "icon": self.icon,
            "action": self.action.to_dict() if self.action else None,
            "bg_color": self.bg_color,
            "text_color": self.text_color,
            "font_size": self.font_size,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Button":
        """Create from dictionary."""
        action_data = data.get("action")
        action = ButtonAction.from_dict(action_data) if action_data else None
        
        return cls(
            key=data["key"],
            label=data.get("label", ""),
            icon=data.get("icon"),
            action=action,
            bg_color=tuple(data.get("bg_color", [0, 0, 0])),
            text_color=tuple(data.get("text_color", [255, 255, 255])),
            font_size=data.get("font_size", 14),
            enabled=data.get("enabled", True),
        )
