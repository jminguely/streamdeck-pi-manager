"""
Sonos control plugin for Stream Deck Pi Manager.
Allows toggling devices into a group with a designated source.
"""
import logging
import threading
import soco
from typing import Dict, Any, Optional, List, Tuple
from streamdeck_pi.plugins.base import ButtonPlugin

logger = logging.getLogger(__name__)

# Shared state for Sonos grouping across all plugin instances
# Maps group_id -> { 'source_name': str, 'members': set(str) }
_sonos_groups: Dict[str, Dict[str, Any]] = {}
_sonos_lock = threading.Lock()

class SonosGroupTogglePlugin(ButtonPlugin):
    """
    Toggle Sonos device in/out of a group.
    The first device toggled becomes the source.
    """

    id = "sonos.group_toggle"
    name = "Sonos Group Toggle"
    description = "Toggle Sonos device in a group (First is source)"
    icon = "speaker"
    category = "media"

    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "device_name": {
                    "type": "string",
                    "description": "Sonos device name (e.g., Living Room)"
                },
                "group_id": {
                    "type": "string",
                    "default": "default",
                    "description": "ID to separate different grouping logic"
                }
            },
            "required": ["device_name"]
        }

    def _get_device(self, name: str) -> Optional[soco.SoCo]:
        """Find Sonos device by name."""
        try:
            return soco.discovery.by_name(name)
        except Exception as e:
            logger.error(f"Error finding Sonos device {name}: {e}")
            return None

    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Toggle the device in the group."""
        device_name = self.config.get("device_name")
        group_id = self.config.get("group_id", "default")

        if not device_name:
            return

        device = self._get_device(device_name)
        if not device:
            if self.device_manager:
                self.device_manager.set_button_text(button_id, f"{device_name}\nNot Found", text_color=(255, 0, 0))
            return

        with _sonos_lock:
            group = _sonos_groups.get(group_id, {"source_name": None, "members": set()})
            
            # 1. If no source, this device becomes the source
            if not group["source_name"]:
                group["source_name"] = device_name
                group["members"].add(device_name)
                logger.info(f"Sonos: {device_name} is now the source for group {group_id}")
            
            # 2. If it is the source, we might want to disband or just stay source
            elif group["source_name"] == device_name:
                # If it's the only member, we clear the source
                if len(group["members"]) <= 1:
                    group["source_name"] = None
                    group["members"].clear()
                    logger.info(f"Sonos: Group {group_id} cleared")
                else:
                    # If there are other members, maybe we don't want to allow un-sourcing 
                    # until everyone else is gone, or we pick a new source.
                    # For simplicity: toggling source off clears the whole group's logic
                    for member_name in list(group["members"]):
                        if member_name != device_name:
                            m_dev = self._get_device(member_name)
                            if m_dev:
                                try:
                                    m_dev.unjoin()
                                except:
                                    pass
                    group["source_name"] = None
                    group["members"].clear()
                    logger.info(f"Sonos: Group {group_id} disbanded")

            # 3. If it's a member but not the source, unjoin it
            elif device_name in group["members"]:
                try:
                    device.unjoin()
                    group["members"].remove(device_name)
                    logger.info(f"Sonos: {device_name} unjoined group {group_id}")
                except Exception as e:
                    logger.error(f"Sonos: Failed to unjoin {device_name}: {e}")

            # 4. If it's not a member, join it to the source
            else:
                source_dev = self._get_device(group["source_name"])
                if source_dev:
                    try:
                        device.join(source_dev)
                        group["members"].add(device_name)
                        logger.info(f"Sonos: {device_name} joined {group['source_name']}")
                    except Exception as e:
                        logger.error(f"Sonos: Failed to join {device_name} to {group['source_name']}: {e}")
                else:
                    # Source device not found anymore, make this one the source
                    group["source_name"] = device_name
                    group["members"].clear()
                    group["members"].add(device_name)

            _sonos_groups[group_id] = group
        
        self.update_display(button_id, context)

    def tick(self, button_id: int, context: Dict[str, Any] = None):
        """Update display state."""
        self.update_display(button_id, context)

    def update_display(self, button_id: int, context: Dict[str, Any] = None):
        """Update button color and text based on group status."""
        if not self.device_manager:
            return

        device_name = self.config.get("device_name")
        group_id = self.config.get("group_id", "default")
        
        if not device_name:
            return

        with _sonos_lock:
            group = _sonos_groups.get(group_id, {"source_name": None, "members": set()})
            
            bg_color = (0, 0, 0)
            status_text = ""

            if group["source_name"] == device_name:
                bg_color = (0, 150, 0) # Green for source
                status_text = "SOURCE"
            elif device_name in group["members"]:
                bg_color = (150, 150, 0) # Yellow for joined
                status_text = "JOINED"
            
            label = self.config.get("label", device_name)
            if status_text:
                display_text = f"{label}\n{status_text}"
            else:
                display_text = label

            # We use set_button_text which internally uses the cache we built
            self.device_manager.set_button_text(
                button_id,
                display_text,
                bg_color=bg_color,
                text_color=context.get("text_color", (255, 255, 255)) if context else (255, 255, 255),
                font_size=context.get("font_size", 14) if context else 14
            )
