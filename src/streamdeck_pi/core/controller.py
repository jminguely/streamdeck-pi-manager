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
            # Set brightness to max to ensure visibility
            try:
                self.device.set_brightness(100)
                logger.info("Set brightness to 100%")
            except Exception as e:
                logger.error(f"Failed to set brightness: {e}")

            self.setup_callbacks()
            self.render_current_page()

            # Debug device capabilities
            if self.device.device:
                try:
                    import StreamDeck
                    import inspect
                    logger.info(f"StreamDeck Library Version: {getattr(StreamDeck, '__version__', 'Unknown')}")
                    logger.info(f"StreamDeck Library File: {StreamDeck.__file__}")

                    # Inspect set_touchscreen_image
                    if hasattr(self.device.device, 'set_touchscreen_image'):
                        src = inspect.getsource(self.device.device.set_touchscreen_image)
                        logger.info(f"Source of set_touchscreen_image:\n{src}")

                except Exception as e:
                    logger.error(f"Failed to inspect library: {e}")

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

        # Also register for keys 8 and 9 anyway, just in case the library maps them
        # even if set_touchscreen_callback exists (some versions do both or one)
        try:
            # We need to access the underlying device's key callback mechanism if our wrapper doesn't support > key_count
            # But our wrapper uses range(key_count).
            # Neo has 8 keys (0-7). If touch is 8/9, we need to register them.

            # Let's try to register them with our wrapper
            self.device.register_button_callback(8, self.on_key_press)
            self.device.register_button_callback(9, self.on_key_press)
            logger.info("Registered potential touch keys 8 and 9")
        except Exception as e:
            logger.warning(f"Could not register keys 8/9: {e}")

    def on_touch(self, deck, event):
        """Handle touch events."""
        try:
            # event is a dict with 'x', 'y', 'interaction' (press/release/drag)
            logger.info(f"Touch event received: {event}")

            # Ensure event is a dictionary
            if not isinstance(event, dict):
                logger.warning(f"Unexpected event format: {type(event)} - {event}")
                return

            x = event.get('x')

            # Log all details
            logger.info(f"Touch X: {x}, Y: {event.get('y')}, Interaction: {event.get('interaction')}")

            # Neo Info Bar resolution is approx 248x58
            # Left button area
            if x is not None and x < 60:
                logger.info("Left touch detected")
                self.prev_page()
            # Right button area
            elif x is not None and x > 180:
                logger.info("Right touch detected")
                self.next_page()
        except Exception as e:
            logger.error(f"Error in on_touch: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
                # Use button colors if set, otherwise use page colors, otherwise default
                bg_color = button.bg_color
                if bg_color == (0, 0, 0) and page.bg_color:
                    bg_color = page.bg_color

                text_color = button.text_color
                if text_color == (255, 255, 255) and page.text_color:
                    text_color = page.text_color

                self.device.set_button_text(
                    key,
                    button.label,
                    icon=button.icon,
                    font_size=button.font_size,
                    bg_color=bg_color,
                    text_color=text_color
                )
                # TODO: Handle icons

    def update_info_screen(self):
        """Update the info screen (Neo specific)."""
        # Check if device supports touchscreen
        # This is a best-effort attempt to support Neo features
        # Even if the library method is a stub, we will try to use our manual implementation if it's a Neo
        is_neo = self.device.device and self.device.device.deck_type() == "Stream Deck Neo"

        if not is_neo and not hasattr(self.device.device, 'set_touchscreen_image'):
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

        # Determine colors
        bg_color = page.bg_color if page.bg_color else (0, 0, 0)
        text_color = page.text_color if page.text_color else (255, 255, 255)

        # Use RGBA for transparency support if needed, though RGB is usually fine
        image = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        # Draw Page Title
        try:
            # Try a few common font locations
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
            ]
            font = None
            for path in font_paths:
                try:
                    font = ImageFont.truetype(path, 20)
                    break
                except:
                    continue
            if not font:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        text = f"{page.title} ({current_idx}/{total_pages})"

        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # Draw text
        draw.text((x, y), text, font=font, fill=text_color)

        # Rotate 180 degrees
        image = image.rotate(180)

        # Convert to native format and send
        try:
            if is_neo:
                # Manual implementation for Neo
                import io
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG', quality=95)
                jpeg_bytes = img_byte_arr.getvalue()
                self._send_neo_image(jpeg_bytes)
            else:
                from StreamDeck.ImageHelpers import PILHelper
                # Neo expects a specific format for the touchscreen image
                # It seems the library handles conversion, but let's ensure we are passing the right thing.
                # Some versions of the library might need explicit format conversion or sizing.

                # Log that we are attempting to set the image
                logger.info(f"Setting info screen image: {width}x{height}")

                native_image = PILHelper.to_native_format(self.device.device, image)

                # Debug native image
                if native_image:
                    logger.info(f"Native image type: {type(native_image)}")
                    if hasattr(native_image, '__len__'):
                        logger.info(f"Native image length: {len(native_image)}")
                else:
                    logger.error("Native image is None!")

                self.device.device.set_touchscreen_image(native_image)
            logger.info("Info screen updated successfully")
        except Exception as e:
            logger.error(f"Failed to update info screen: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _send_neo_image(self, jpeg_data):
        """
        Manually send image to Stream Deck Neo Info Screen.
        Protocol: Report 0x02, Command 0x0B.
        """
        IMAGE_REPORT_LENGTH = 1024
        HEADER_LENGTH = 8
        PAYLOAD_LENGTH = IMAGE_REPORT_LENGTH - HEADER_LENGTH

        page_number = 0
        bytes_remaining = len(jpeg_data)

        logger.info(f"Sending Neo Image: {bytes_remaining} bytes")

        while bytes_remaining > 0:
            this_length = min(bytes_remaining, PAYLOAD_LENGTH)
            bytes_sent = page_number * PAYLOAD_LENGTH

            is_last = 1 if this_length == bytes_remaining else 0

            # Header: [ID, CMD, PAD, FLAGS, LEN_LSB, LEN_MSB, PAGE_LSB, PAGE_MSB]
            header = [
                0x02, 0x0B, 0x00, is_last,
                this_length & 0xFF, (this_length >> 8) & 0xFF,
                page_number & 0xFF, (page_number >> 8) & 0xFF
            ]

            payload = list(jpeg_data[bytes_sent:bytes_sent + this_length])

            # Pad to full report length
            padding = [0] * (PAYLOAD_LENGTH - len(payload))

            report = header + payload + padding

            # Send report
            # Access raw HID device
            # self.device.device is the StreamDeck wrapper
            # self.device.device.device is the Transport (HID)
            try:
                self.device.device.device.write(report)
            except Exception as e:
                logger.error(f"Failed to write HID report: {e}")
                raise

            bytes_remaining -= this_length
            page_number += 1

    def on_key_press(self, key: int):
        """Handle key press."""
        logger.info(f"Key pressed: {key}")

        # Check for Neo touch keys (if they come through as regular keys)
        if key == 8:
            logger.info("Left touch detected (via key press)")
            self.prev_page()
            return
        elif key == 9:
            logger.info("Right touch detected (via key press)")
            self.next_page()
            return

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
            # Use button colors if set, otherwise use page colors
            bg_color = button.bg_color
            if bg_color == (0, 0, 0) and page.bg_color:
                bg_color = page.bg_color

            text_color = button.text_color
            if text_color == (255, 255, 255) and page.text_color:
                text_color = page.text_color

            self.device.set_button_text(
                key,
                button.label,
                icon=button.icon,
                font_size=button.font_size,
                bg_color=bg_color,
                text_color=text_color
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
