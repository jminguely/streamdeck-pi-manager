"""
API routes for Stream Deck Pi Manager.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from streamdeck_pi.core.button import Button, ButtonAction, ButtonActionType
from streamdeck_pi.core.device import StreamDeckManager
from streamdeck_pi.plugins.base import PluginManager

router = APIRouter()


# Request/Response Models
class DeviceInfoResponse(BaseModel):
    """Device information response."""
    type: str
    serial: str
    firmware: str
    key_count: int
    key_layout: tuple
    connected: bool


class ButtonConfigRequest(BaseModel):
    """Button configuration request."""
    label: str = ""
    icon: Optional[str] = None
    action_type: str = "none"
    plugin_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    bg_color: List[int] = [0, 0, 0]
    text_color: List[int] = [255, 255, 255]
    font_size: int = 14
    enabled: bool = True


class PluginInfo(BaseModel):
    """Plugin information."""
    id: str
    name: str
    description: str
    category: str
    icon: Optional[str] = None
    config_schema: Dict[str, Any]


# Dependency to get managers
def get_device_manager(request: Request) -> StreamDeckManager:
    """Get device manager from app state."""
    return request.app.state.device_manager


def get_plugin_manager(request: Request) -> PluginManager:
    """Get plugin manager from app state."""
    return request.app.state.plugin_manager


def get_button_configs(request: Request) -> Dict[int, Button]:
    """Get button configurations from app state."""
    return request.app.state.button_configs


# Device endpoints
@router.get("/device", response_model=DeviceInfoResponse)
async def get_device_info(device_manager: StreamDeckManager = Depends(get_device_manager)):
    """Get Stream Deck device information."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")
    
    info = device_manager.get_device_info()
    return DeviceInfoResponse(
        type=info["type"],
        serial=info["serial"],
        firmware=info["firmware"],
        key_count=info["key_count"],
        key_layout=info["key_layout"],
        connected=True
    )


@router.post("/device/reconnect")
async def reconnect_device(device_manager: StreamDeckManager = Depends(get_device_manager)):
    """Reconnect to Stream Deck device."""
    device_manager.disconnect()
    if device_manager.connect():
        return {"status": "connected"}
    raise HTTPException(status_code=503, detail="Failed to connect to device")


@router.post("/device/brightness/{level}")
async def set_brightness(
    level: int,
    device_manager: StreamDeckManager = Depends(get_device_manager)
):
    """Set device brightness (0-100)."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")
    
    if not 0 <= level <= 100:
        raise HTTPException(status_code=400, detail="Brightness must be between 0 and 100")
    
    device_manager.set_brightness(level)
    return {"brightness": level}


# Button endpoints
@router.get("/buttons")
async def list_buttons(
    device_manager: StreamDeckManager = Depends(get_device_manager),
    button_configs: Dict[int, Button] = Depends(get_button_configs)
):
    """List all buttons with their configurations."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")
    
    key_count = device_manager.device_info["key_count"]
    
    buttons = []
    for key in range(key_count):
        if key in button_configs:
            buttons.append(button_configs[key].to_dict())
        else:
            # Default empty button
            buttons.append(Button(key=key).to_dict())
    
    return {"buttons": buttons}


@router.get("/buttons/{key}")
async def get_button(
    key: int,
    button_configs: Dict[int, Button] = Depends(get_button_configs)
):
    """Get button configuration."""
    if key in button_configs:
        return button_configs[key].to_dict()
    return Button(key=key).to_dict()


@router.put("/buttons/{key}")
async def update_button(
    key: int,
    config: ButtonConfigRequest,
    request: Request,
    device_manager: StreamDeckManager = Depends(get_device_manager),
    plugin_manager: PluginManager = Depends(get_plugin_manager)
):
    """Update button configuration."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")
    
    if key >= device_manager.device_info["key_count"]:
        raise HTTPException(status_code=404, detail="Button not found")
    
    # Create button action
    action = None
    if config.action_type != "none" and config.plugin_id:
        action = ButtonAction(
            type=ButtonActionType(config.action_type),
            plugin_id=config.plugin_id,
            config=config.config
        )
    
    # Create button config
    button = Button(
        key=key,
        label=config.label,
        icon=config.icon,
        action=action,
        bg_color=tuple(config.bg_color),
        text_color=tuple(config.text_color),
        font_size=config.font_size,
        enabled=config.enabled
    )
    
    # Store configuration
    request.app.state.button_configs[key] = button
    
    # Update button display
    if button.enabled and button.label:
        device_manager.set_button_text(
            key,
            button.label,
            font_size=button.font_size,
            bg_color=button.bg_color,
            text_color=button.text_color
        )
        
        # Register callback if action is configured
        if button.action and button.action.plugin_id:
            def button_callback(button_id: int):
                plugin_manager.execute_plugin(
                    button.action.plugin_id,
                    button_id,
                    config=button.action.config
                )
            
            device_manager.register_button_callback(key, button_callback)
    else:
        device_manager.clear_button(key)
        device_manager.unregister_button_callback(key)
    
    return button.to_dict()


@router.delete("/buttons/{key}")
async def clear_button(
    key: int,
    request: Request,
    device_manager: StreamDeckManager = Depends(get_device_manager)
):
    """Clear button configuration."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")
    
    device_manager.clear_button(key)
    device_manager.unregister_button_callback(key)
    
    if key in request.app.state.button_configs:
        del request.app.state.button_configs[key]
    
    return {"status": "cleared"}


@router.post("/buttons/{key}/press")
async def press_button(
    key: int,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    button_configs: Dict[int, Button] = Depends(get_button_configs)
):
    """Simulate button press (for testing)."""
    if key not in button_configs:
        raise HTTPException(status_code=404, detail="Button not configured")
    
    button = button_configs[key]
    if button.action and button.action.plugin_id:
        try:
            plugin_manager.execute_plugin(
                button.action.plugin_id,
                key,
                config=button.action.config
            )
            return {"status": "executed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return {"status": "no action configured"}


# Plugin endpoints
@router.get("/plugins", response_model=List[PluginInfo])
async def list_plugins(plugin_manager: PluginManager = Depends(get_plugin_manager)):
    """List all available plugins."""
    plugins_data = plugin_manager.list_plugins()
    
    return [
        PluginInfo(
            id=plugin_id,
            name=data["name"],
            description=data["description"],
            category=data["category"],
            icon=data.get("icon"),
            config_schema=data["config_schema"]
        )
        for plugin_id, data in plugins_data.items()
    ]


@router.get("/plugins/{plugin_id}")
async def get_plugin(
    plugin_id: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager)
):
    """Get plugin information."""
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return plugin.get_metadata()


# Health check
@router.get("/health")
async def health_check(device_manager: StreamDeckManager = Depends(get_device_manager)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "device_connected": device_manager.is_connected()
    }
