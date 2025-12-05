"""
Built-in plugins for Stream Deck Pi Manager.
"""
from streamdeck_pi.plugins.base import ButtonPlugin, PluginManager
from streamdeck_pi.plugins import system, network

__all__ = [
    "ButtonPlugin",
    "PluginManager",
    "system",
    "network",
]
