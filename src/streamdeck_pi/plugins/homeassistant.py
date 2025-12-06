import requests
from typing import Dict, Any
from streamdeck_pi.plugins.base import ButtonPlugin

class HomeAssistantPlugin(ButtonPlugin):
    """Control Home Assistant entities."""

    id = "homeassistant.control"
    name = "Home Assistant"
    description = "Control Home Assistant entities"
    icon = "home"
    category = "iot"

    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Service domain (e.g., light, switch)"
                },
                "service": {
                    "type": "string",
                    "description": "Service name (e.g., turn_on, toggle)"
                },
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID (e.g., light.living_room)"
                }
            },
            "required": ["domain", "service", "entity_id"]
        }

    def _get_ha_config(self):
        """Get Home Assistant configuration from plugin config or global settings."""
        url = self.config.get("url")
        token = self.config.get("token")

        if not url:
            url = self.global_settings.get("homeassistant", {}).get("url")

        if not token:
            token = self.global_settings.get("homeassistant", {}).get("token")

        return url, token

    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Execute Home Assistant service."""
        url, token = self._get_ha_config()
        domain = self.config.get("domain")
        service = self.config.get("service")
        entity_id = self.config.get("entity_id")

        if not all([url, token, domain, service, entity_id]):
            raise ValueError("Missing Home Assistant configuration (url, token, domain, service, or entity_id)")

        # Remove trailing slash from URL
        if url.endswith("/"):
            url = url[:-1]

        api_url = f"{url}/api/services/{domain}/{service}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        data = {
            "entity_id": entity_id
        }

        self.logger.info(f"Calling Home Assistant: {domain}.{service} for {entity_id}")

        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=5)
            response.raise_for_status()
            self.logger.info("Home Assistant call successful")
        except Exception as e:
            self.logger.error(f"Home Assistant call failed: {e}")
            raise


class HomeAssistantSensorPlugin(HomeAssistantPlugin):
    """Display Home Assistant entity state/attribute."""

    id = "homeassistant.sensor"
    name = "Home Assistant Sensor"
    description = "Display entity state or attribute"
    icon = "eye"
    category = "iot"

    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID (e.g., sensor.temperature)"
                },
                "attribute": {
                    "type": "string",
                    "description": "Attribute to display (optional, e.g., volume_level). Leave empty for state."
                },
                "unit": {
                    "type": "string",
                    "description": "Unit suffix (e.g., %)"
                },
                "label": {
                    "type": "string",
                    "description": "Label text (e.g., Vol)"
                }
            },
            "required": ["entity_id"]
        }

    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Fetch and display state."""
        url, token = self._get_ha_config()
        entity_id = self.config.get("entity_id")
        attribute = self.config.get("attribute")
        unit = self.config.get("unit", "")
        label = self.config.get("label", "")

        if not all([url, token, entity_id]):
            raise ValueError("Missing Home Assistant configuration")

        if url.endswith("/"):
            url = url[:-1]

        api_url = f"{url}/api/states/{entity_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        self.logger.info(f"Fetching state for {entity_id}")

        try:
            response = requests.get(api_url, headers=headers, timeout=5)
            response.raise_for_status()
            state_data = response.json()

            if attribute:
                value = state_data.get("attributes", {}).get(attribute)
            else:
                value = state_data.get("state")

            # Format value (e.g. round float)
            if isinstance(value, float):
                value = round(value, 2)
                # If it's volume (0.0-1.0), maybe multiply by 100?
                # Let's keep it raw or let user handle it via unit/label,
                # but for volume specifically, it's often 0-1.
                # I won't assume volume unless attribute is volume_level
                if attribute == "volume_level":
                    value = int(value * 100)

            display_text = f"{value}{unit}"
            if label:
                display_text = f"{label}\n{display_text}"

            self.logger.info(f"State: {value}")

            if self.device_manager:
                self.device_manager.set_button_text(
                    button_id,
                    display_text,
                    font_size=context.get("font_size", 14) if context else 14,
                    bg_color=context.get("bg_color", (0, 0, 0)) if context else (0, 0, 0),
                    text_color=context.get("text_color", (255, 255, 255)) if context else (255, 255, 255)
                )

            return value

        except Exception as e:
            self.logger.error(f"Failed to fetch state: {e}")
            if self.device_manager:
                 self.device_manager.set_button_text(button_id, "Error", text_color=(255, 0, 0))
            raise

    def tick(self, button_id: int, context: Dict[str, Any] = None):
        """Update state periodically."""
        try:
            self.execute(button_id, context)
        except Exception:
            # Errors are already logged in execute
            pass
