"""
Stream Deck Device Manager
Handles connection and communication with Stream Deck devices.
"""
import logging
from typing import Optional, List, Dict, Any, Callable
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices.StreamDeck import StreamDeck
from StreamDeck.ImageHelpers import PILHelper
from PIL import Image, ImageDraw, ImageFont
import threading
import os

logger = logging.getLogger(__name__)


class StreamDeckManager:
    """Manages Stream Deck device connection and operations."""

    def __init__(self):
        self.device: Optional[StreamDeck] = None
        self.device_info: Dict[str, Any] = {}
        self.button_callbacks: Dict[int, Callable] = {}
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """
        Connect to the first available Stream Deck device.

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            streamdecks = DeviceManager().enumerate()

            if not streamdecks:
                logger.error("No Stream Deck devices found")
                return False

            # Use first device
            self.device = streamdecks[0]
            self.device.open()
            self.device.reset()

            # Store device information
            self.device_info = {
                "type": self.device.deck_type(),
                "serial": self.device.get_serial_number(),
                "firmware": self.device.get_firmware_version(),
                "key_count": self.device.key_count(),
                "key_layout": self.device.key_layout(),
            }

            logger.info(f"Connected to {self.device_info['type']} (Serial: {self.device_info['serial']})")

            # Set up button callback
            self.device.set_key_callback(self._handle_key_press)

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Stream Deck: {e}")
            return False

    def disconnect(self):
        """Disconnect from the Stream Deck device."""
        if self.device:
            try:
                self.device.reset()
                self.device.close()
                logger.info("Disconnected from Stream Deck")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self.device = None

    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self.device is not None and self.device.is_open()

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        return self.device_info

    def set_brightness(self, brightness: int):
        """
        Set device brightness.

        Args:
            brightness: Brightness level (0-100)
        """
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        brightness = max(0, min(100, brightness))
        self.device.set_brightness(brightness)
        logger.info(f"Brightness set to {brightness}%")

    def set_button_image(self, key: int, image: Image.Image):
        """
        Set image for a specific button.

        Args:
            key: Button index
            image: PIL Image object
        """
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        with self._lock:
            # Convert PIL image to Stream Deck format
            native_image = PILHelper.to_native_format(self.device, image)
            self.device.set_key_image(key, native_image)

    def set_button_text(self, key: int, text: str, icon: Optional[str] = None, font_size: int = 14,
                       bg_color: tuple = (0, 0, 0), text_color: tuple = (255, 255, 255)):
        """
        Set text and icon on a button.

        Args:
            key: Button index
            text: Text to display
            icon: Icon character (emoji or text)
            font_size: Font size for text
            bg_color: Background color (R, G, B)
            text_color: Text color (R, G, B)
        """
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        # Create image with text
        image = PILHelper.create_image(self.device)
        draw = ImageDraw.Draw(image)

        # Fill background
        draw.rectangle([(0, 0), image.size], fill=bg_color)

        # Determine project root to find assets
        # src/streamdeck_pi/core/device.py -> ../../../
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
        assets_font_dir = os.path.join(project_root, "assets", "fonts")

        # Load Fonts
        # Text Font (Noto Sans)
        text_font = None
        text_font_paths = [
            os.path.join(assets_font_dir, "Noto_Sans/static/NotoSans-Regular.ttf"),
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        for path in text_font_paths:
            try:
                text_font = ImageFont.truetype(path, font_size)
                break
            except:
                continue
        if not text_font:
            text_font = ImageFont.load_default()

        # Icon Font (Noto Emoji or Noto Sans)
        icon_font = None
        if icon:
            icon_size = int(image.height * 0.5) # Icon takes up half the height
            icon_font_paths = [
                os.path.join(assets_font_dir, "Noto_Emoji/static/NotoEmoji-Regular.ttf"),
                "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf", # Monochrome emoji
                "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Apple Color Emoji.ttc" # macOS fallback
            ]
            for path in icon_font_paths:
                try:
                    icon_font = ImageFont.truetype(path, icon_size)
                    break
                except:
                    continue
            if not icon_font:
                icon_font = ImageFont.load_default()

        # Draw Content
        if icon:
            # Draw Icon (Centered horizontally, Top half)
            bbox_icon = draw.textbbox((0, 0), icon, font=icon_font)
            icon_w = bbox_icon[2] - bbox_icon[0]
            icon_h = bbox_icon[3] - bbox_icon[1]

            # Position icon slightly above center
            # Move icon down slightly to reduce gap
            icon_x = (image.width - icon_w) / 2
            icon_y = (image.height / 2 - icon_h) / 2 + 10

            draw.text((icon_x, icon_y), icon, font=icon_font, fill=text_color)

            # Draw Text (Centered horizontally, Bottom half)
            bbox_text = draw.textbbox((0, 0), text, font=text_font)
            text_w = bbox_text[2] - bbox_text[0]
            text_h = bbox_text[3] - bbox_text[1]

            text_x = (image.width - text_w) / 2
            # Move text up slightly to reduce gap
            text_y = image.height - text_h - 10

            draw.text((text_x, text_y), text, font=text_font, fill=text_color)

        else:
            # Center text only
            bbox = draw.textbbox((0, 0), text, font=text_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (image.width - text_width) / 2
            y = (image.height - text_height) / 2

            draw.text((x, y), text, font=text_font, fill=text_color)

        self.set_button_image(key, image)

    def clear_button(self, key: int):
        """Clear a button (set to black)."""
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        with self._lock:
            self.device.set_key_image(key, None)

    def clear_all_buttons(self):
        """Clear all buttons."""
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        for key in range(self.device.key_count()):
            self.clear_button(key)

    def register_button_callback(self, key: int, callback: Callable):
        """
        Register a callback for button press.

        Args:
            key: Button index
            callback: Function to call when button is pressed
        """
        self.button_callbacks[key] = callback

    def unregister_button_callback(self, key: int):
        """Unregister button callback."""
        if key in self.button_callbacks:
            del self.button_callbacks[key]

    def _handle_key_press(self, deck, key: int, state: bool):
        """Internal handler for key press events."""
        if state:  # Only handle key press, not release
            logger.debug(f"Button {key} pressed")

            if key in self.button_callbacks:
                try:
                    self.button_callbacks[key](key)
                except Exception as e:
                    logger.error(f"Error in button callback for key {key}: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
