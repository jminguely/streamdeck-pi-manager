"""
Base plugin class and plugin system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ButtonPlugin(ABC):
    """Base class for button plugins."""
    
    # Plugin metadata (override in subclass)
    id: str = ""
    name: str = ""
    description: str = ""
    icon: Optional[str] = None
    category: str = "general"
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.device_manager = None

    def set_device_manager(self, device_manager):
        """Set the device manager instance."""
        self.device_manager = device_manager
    
    @abstractmethod
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """
        Execute the plugin action.
        
        Args:
            button_id: The button that was pressed
            context: Additional context information
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for plugin configuration.
        
        Returns:
            JSON schema dictionary
        """
        return {
            "type": "object",
            "properties": {}
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Override in subclass for custom validation
        return True, None
    
    def on_load(self):
        """Called when plugin is loaded."""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "config_schema": self.get_config_schema(),
        }


class PluginManager:
    """Manages plugin loading and execution."""
    
    def __init__(self, device_manager=None):
        self.plugins: Dict[str, ButtonPlugin] = {}
        self.device_manager = device_manager
    
    def register_plugin(self, plugin_class: type[ButtonPlugin]):
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
        """
        plugin = plugin_class()
        if self.device_manager:
            plugin.set_device_manager(self.device_manager)
        
        if not plugin.id:
            raise ValueError(f"Plugin {plugin_class.__name__} must have an 'id'")
        
        if plugin.id in self.plugins:
            raise ValueError(f"Plugin '{plugin.id}' already registered")
        
        self.plugins[plugin.id] = plugin
        plugin.on_load()
        
        logger.info(f"Registered plugin: {plugin.id} ({plugin.name})")
    
    def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin."""
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            plugin.on_unload()
            del self.plugins[plugin_id]
            logger.info(f"Unregistered plugin: {plugin_id}")
    
    def get_plugin(self, plugin_id: str) -> Optional[ButtonPlugin]:
        """Get a plugin by ID."""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all registered plugins with metadata."""
        return {
            plugin_id: plugin.get_metadata()
            for plugin_id, plugin in self.plugins.items()
        }
    
    def execute_plugin(self, plugin_id: str, button_id: int, 
                       config: Dict[str, Any] = None, context: Dict[str, Any] = None):
        """
        Execute a plugin action.
        
        Args:
            plugin_id: ID of plugin to execute
            button_id: Button that was pressed
            config: Plugin configuration
            context: Additional context
        """
        plugin = self.get_plugin(plugin_id)
        
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found")
        
        # Update plugin config if provided
        if config:
            plugin.config = config
        
        try:
            plugin.execute(button_id, context or {})
        except Exception as e:
            logger.error(f"Error executing plugin '{plugin_id}': {e}", exc_info=True)
            raise
