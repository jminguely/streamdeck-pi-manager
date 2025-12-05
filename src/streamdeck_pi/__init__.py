"""
Stream Deck Pi Manager
A web-based management interface for Elgato Stream Deck devices on Raspberry Pi.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

from streamdeck_pi.core.device import StreamDeckManager
from streamdeck_pi.core.button import Button, ButtonAction
from streamdeck_pi.plugins.base import ButtonPlugin

__all__ = [
    "StreamDeckManager",
    "Button",
    "ButtonAction",
    "ButtonPlugin",
]
