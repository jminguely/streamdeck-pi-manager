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
                "url": {
                    "type": "string",
                    "description": "Home Assistant URL (e.g., http://homeassistant.local:8123)"
                },
                "token": {
                    "type": "string",
                    "description": "Long-lived Access Token"
                },
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
            "required": ["url", "token", "domain", "service", "entity_id"]
        }

    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Execute Home Assistant service."""
        url = self.config.get("url")
        token = self.config.get("token")
        domain = self.config.get("domain")
        service = self.config.get("service")
        entity_id = self.config.get("entity_id")

        if not all([url, token, domain, service, entity_id]):
            raise ValueError("Missing Home Assistant configuration")

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
