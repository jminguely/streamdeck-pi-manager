import logging
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from streamdeck_pi.core.device import StreamDeckManager
from streamdeck_pi.core.config import ConfigManager, Page
from streamdeck_pi.core.button import Button
from streamdeck_pi.plugins.base import PluginManager

logger = logging.getLogger(__name__)

class DeckController:
    """
    Controls the Stream Deck logic, including paging and button actions.
    """
    def __init__(self, device_manager: StreamDeckManager, config_manager: ConfigManager, plugin_manager: PluginManager):
        self.device = device_manager
        self.config_manager = config_manager
        self.plugin_manager = plugin_manager
        self.config = self.config_manager.load_config()

    def start(self):
        """Start the controller."""
        if self.device.connect():
            self.setup_callbacks()
            self.render_current_page()

            # Debug device capabilities
            if self.device.device:
                logger.info(f"Device type: {self.device.device.deck_type()}")
                logger.info(f"Has set_touchscreen_image: {hasattr(self.device.device, 'set_touchscreen_image')}")
                logger.info(f"Has set_touchscreen_callback: {hasattr(self.device.device, 'set_touchscreen_callback')}")
                logger.info(f"Key count: {self.device.device.key_count()}")

    def stop(self):
        """Stop the controller."""
        self.device.disconnect()

    def setup_callbacks(self):
        """Register callbacks for all keys."""
        key_count = self.device.get_device_info().get("key_count", 0)
        for key in range(key_count):
            self.device.register_button_callback(key, self.on_key_press)

        # Register touch callback if available (for Neo)
        if hasattr(self.device.device, 'set_touchscreen_callback'):
            self.device.device.set_touchscreen_callback(self.on_touch)
            logger.info("Registered touchscreen callback")
        else:
            logger.warning("Device does not support set_touchscreen_callback")

    def on_touch(self, deck, event):
        """Handle touch events."""
        # event is a dict with 'x', 'y', 'interaction' (press/release/drag)
        logger.info(f"Touch event: {event}")

        x = event.get('x')
        interaction = event.get('interaction') # 'short' (tap), 'long', 'drag'

        # Neo Info Bar resolution is approx 248x58
        # Left button area
        if x < 60:
            logger.info("Left touch detected")
            self.prev_page()
        # Right button area
        elif x > 180:
            logger.info("Right touch detected")
            self.next_page()
    def get_current_page(self) -> Optional[Page]:
        """Get the current page object."""
        page_id = self.config.get("current_page_id")
        return self.config.get("pages", {}).get(page_id)

    def render_current_page(self):
        """Render the current page to the device."""
        if not self.device.is_connected():
            return

        page = self.get_current_page()
        if not page:
            return

        self.device.clear_all_buttons()

        # Update Info Screen (Neo)
        self.update_info_screen()

        for key, button in page.buttons.items():
            if button.enabled:
                self.device.set_button_text(
                    key,
                    button.label,
                    font_size=button.font_size,
                    bg_color=button.bg_color,
                    text_color=button.text_color
                )
                # TODO: Handle icons

    def update_info_screen(self):
        """Update the info screen (Neo specific)."""
        # Check if device supports touchscreen
        # This is a best-effort attempt to support Neo features
        if not hasattr(self.device.device, 'set_touchscreen_image'):
            logger.warning("Device does not support set_touchscreen_image")
            return

        page = self.get_current_page()
        if not page:
            return

        pages = list(self.config["pages"].keys())
        try:
            current_idx = pages.index(page.id) + 1
        except ValueError:
            current_idx = 1
        total_pages = len(pages)

        # Create image for info screen
        # Neo info screen is 248x58 px
        width = 248
        height = 58

        image = Image.new('RGB', (width, height), 'black')
        draw = ImageDraw.Draw(image)

        # Draw Page Title
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font = ImageFont.load_default()

        text = f"{page.title} ({current_idx}/{total_pages})"

        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2

        draw.text((x, y), text, font=font, fill="white")

        # Convert to native format and set
        try:
            from StreamDeck.ImageHelpers import PILHelper
            # Neo expects a specific format for the touchscreen image
            # It seems the library handles conversion, but let's ensure we are passing the right thing.
            # Some versions of the library might need explicit format conversion or sizing.

            # Log that we are attempting to set the image
            logger.info(f"Setting info screen image: {width}x{height}")

            native_image = PILHelper.to_native_format(self.device.device, image)
            self.device.device.set_touchscreen_image(native_image)
            logger.info("Info screen updated successfully")
        except Exception as e:
            logger.error(f"Failed to update info screen: {e}")

    def on_key_press(self, key: int):
        """Handle key press."""
        logger.info(f"Key pressed: {key}")
        page = self.get_current_page()
        if not page:
            return

        # Check if this key is a "special" key for paging?
        # For Neo, if the side buttons are keys, we need to know their IDs.
        # Usually Neo has 8 keys (0-7).
        # If side buttons are keys, they might be 8 and 9?
        # Or maybe they are not keys.

        # Let's assume for now we use keys 0 and 1 for paging if configured?
        # No, the user wants to use the specific buttons.

        # If the device is Neo, we might need to handle touch events or specific keys.
        # Since we don't know the key IDs, we can't hardcode them yet.

        button = page.buttons.get(key)
        if button and button.action and button.action.plugin_id:
            self.plugin_manager.execute_plugin(
                button.action.plugin_id,
                key,
                config=button.action.config,
                context={
                    "bg_color": button.bg_color,
                    "text_color": button.text_color,
                    "font_size": button.font_size
                }
            )

    def next_page(self):
        """Switch to next page."""
        pages = list(self.config["pages"].keys())
        current_id = self.config["current_page_id"]
        try:
            idx = pages.index(current_id)
            next_idx = (idx + 1) % len(pages)
            self.switch_page(pages[next_idx])
        except ValueError:
            pass

    def prev_page(self):
        """Switch to previous page."""
        pages = list(self.config["pages"].keys())
        current_id = self.config["current_page_id"]
        try:
            idx = pages.index(current_id)
            prev_idx = (idx - 1) % len(pages)
            self.switch_page(pages[prev_idx])
        except ValueError:
            pass

    def switch_page(self, page_id: str):
        """Switch to a specific page."""
        if page_id in self.config["pages"]:
            self.config["current_page_id"] = page_id
            self.config_manager.save_config(self.config)
            self.render_current_page()

    def reload_config(self):
        """Reload configuration from disk."""
        self.config = self.config_manager.load_config()
        self.render_current_page()

    def create_page(self, title: str) -> str:
        """Create a new page."""
        import uuid
        page_id = str(uuid.uuid4())
        self.config["pages"][page_id] = Page(id=page_id, title=title, buttons={})
        self.config_manager.save_config(self.config)
        self.update_info_screen()
        return page_id

    def delete_page(self, page_id: str):
        """Delete a page."""
        if page_id in self.config["pages"] and len(self.config["pages"]) > 1:
            del self.config["pages"][page_id]
            if self.config["current_page_id"] == page_id:
                self.config["current_page_id"] = list(self.config["pages"].keys())[0]
                self.render_current_page()
            else:
                self.update_info_screen()
            self.config_manager.save_config(self.config)

    def update_page(self, page_id: str, title: str):
        """Update page details."""
        if page_id in self.config["pages"]:
            self.config["pages"][page_id].title = title
            self.config_manager.save_config(self.config)
            if self.config["current_page_id"] == page_id:
                self.update_info_screen()

    def update_button(self, key: int, button: Button):
        """Update a button on the current page."""
        page = self.get_current_page()
        if not page:
            return

        page.buttons[key] = button
        self.config_manager.save_config(self.config)

        if button.enabled:
            self.device.set_button_text(
                key,
                button.label,
                font_size=button.font_size,
                bg_color=button.bg_color,
                text_color=button.text_color
            )
        else:
            self.device.clear_button(key)

    def clear_button(self, key: int):
        """Clear a button on the current page."""
        page = self.get_current_page()
        if not page:
            return

        if key in page.buttons:
            del page.buttons[key]
            self.config_manager.save_config(self.config)
            self.device.clear_button(key)
