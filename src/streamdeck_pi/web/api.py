"""
API routes for Stream Deck Pi Manager.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from streamdeck_pi.core.button import Button, ButtonAction, ButtonActionType
from streamdeck_pi.core.device import StreamDeckManager
from streamdeck_pi.core.config import ConfigManager
from streamdeck_pi.core.controller import DeckController
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

class PageInfo(BaseModel):
    """Page information."""
    id: str
    title: str
    bg_color: Optional[List[int]] = None
    text_color: Optional[List[int]] = None


class PageUpdateRequest(BaseModel):
    """Page update request."""
    title: str
    bg_color: Optional[List[int]] = None
    text_color: Optional[List[int]] = None


class SwapButtonRequest(BaseModel):
    """Request to swap two buttons."""
    page_id: str
    key1: int
    key2: int


class MoveButtonRequest(BaseModel):
    """Request to move a button to another page."""
    source_page_id: str
    source_key: int
    target_page_id: str


# Dependency to get managers
def get_device_manager(request: Request) -> StreamDeckManager:
    """Get device manager from app state."""
    return request.app.state.device_manager


def get_plugin_manager(request: Request) -> PluginManager:
    """Get plugin manager from app state."""
    return request.app.state.plugin_manager


def get_deck_controller(request: Request) -> DeckController:
    """Get deck controller from app state."""
    return request.app.state.deck_controller


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


# Page endpoints
@router.get("/pages", response_model=List[PageInfo])
async def get_pages(controller: DeckController = Depends(get_deck_controller)):
    """List all pages."""
    return [PageInfo(id=p.id, title=p.title) for p in controller.config["pages"].values()]

@router.post("/pages")
async def create_page(title: str, controller: DeckController = Depends(get_deck_controller)):
    """Create a new page."""
    page_id = controller.create_page(title)
    return {"id": page_id, "title": title}

@router.delete("/pages/{page_id}")
async def delete_page(page_id: str, controller: DeckController = Depends(get_deck_controller)):
    """Delete a page."""
    controller.delete_page(page_id)
    return {"status": "deleted"}

@router.post("/pages/{page_id}/activate")
async def activate_page(page_id: str, controller: DeckController = Depends(get_deck_controller)):
    """Switch to a page."""
    controller.switch_page(page_id)
    return {"status": "activated"}

@router.put("/pages/{page_id}")
async def update_page(
    page_id: str,
    req: PageUpdateRequest,
    controller: DeckController = Depends(get_deck_controller)
):
    """Update page details."""
    config = controller.config
    pages = config.get("pages", {})
    page = pages.get(page_id)

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    page.title = req.title
    page.bg_color = tuple(req.bg_color) if req.bg_color else None
    page.text_color = tuple(req.text_color) if req.text_color else None

    controller.config_manager.save_config(config)
    controller.render_current_page()
    return {"status": "updated"}
# Button endpoints
@router.get("/buttons")
async def list_buttons(
    device_manager: StreamDeckManager = Depends(get_device_manager),
    controller: DeckController = Depends(get_deck_controller)
):
    """List all buttons with their configurations for the current page."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")

    key_count = device_manager.device_info["key_count"]
    page = controller.get_current_page()

    buttons = []
    for key in range(key_count):
        if page and key in page.buttons:
            buttons.append(page.buttons[key].to_dict())
        else:
            # Default empty button
            buttons.append(Button(key=key).to_dict())

    return {"buttons": buttons}


@router.get("/buttons/{key}")
async def get_button(
    key: int,
    controller: DeckController = Depends(get_deck_controller)
):
    """Get button configuration."""
    page = controller.get_current_page()
    if page and key in page.buttons:
        return page.buttons[key].to_dict()
    return Button(key=key).to_dict()


@router.put("/buttons/{key}")
async def update_button(
    key: int,
    config: ButtonConfigRequest,
    device_manager: StreamDeckManager = Depends(get_device_manager),
    controller: DeckController = Depends(get_deck_controller)
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

    controller.update_button(key, button)
    return button.to_dict()


@router.delete("/buttons/{key}")
async def clear_button(
    key: int,
    device_manager: StreamDeckManager = Depends(get_device_manager),
    controller: DeckController = Depends(get_deck_controller)
):
    """Clear button configuration."""
    if not device_manager.is_connected():
        raise HTTPException(status_code=503, detail="Device not connected")

    controller.clear_button(key)
    return {"status": "cleared"}


@router.post("/buttons/{key}/press")
async def press_button(
    key: int,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
    controller: DeckController = Depends(get_deck_controller)
):
    """Simulate button press (for testing)."""
    page = controller.get_current_page()
    if not page or key not in page.buttons:
        return {"status": "no action configured"}

    button = page.buttons[key]
    if button.action and button.action.type == "plugin" and button.action.plugin_id:
        try:
            plugin = plugin_manager.get_plugin(button.action.plugin_id)
            if plugin:
                plugin.on_key_press(
                    button.action.plugin_id,
                    key,
                    config=button.action.config
                )
                return {"status": "executed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"status": "no action configured"}


@router.post("/buttons/swap")
async def swap_buttons(
@router.post("/buttons/swap")
async def swap_buttons(
    req: SwapButtonRequest,
    deck_controller: DeckController = Depends(get_deck_controller)
):
    """Swap two buttons on the same page."""
    config = deck_controller.config
    pages = config.get("pages", {})
    page = pages.get(req.page_id)

    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    b1 = page.buttons.get(req.key1)
    b2 = page.buttons.get(req.key2)

    # If both don't exist, nothing to do
    if not b1 and not b2:
        return {"status": "ok"}

    # Remove from dict first to avoid collision
    if req.key1 in page.buttons:
        del page.buttons[req.key1]
    if req.key2 in page.buttons:
        del page.buttons[req.key2]

    # Perform swap
    if b1:
        b1.key = req.key2
        page.buttons[req.key2] = b1

    if b2:
        b2.key = req.key1
        page.buttons[req.key1] = b2

    deck_controller.config_manager.save_config(config)
    deck_controller.render_current_page()
    return {"status": "ok"}


@router.post("/buttons/move")
async def move_button(
@router.post("/buttons/move")
async def move_button(
    req: MoveButtonRequest,
    deck_controller: DeckController = Depends(get_deck_controller)
):
    """Move a button to another page."""
    config = deck_controller.config
    pages = config.get("pages", {})
    source_page = pages.get(req.source_page_id)
    target_page = pages.get(req.target_page_id)
        raise HTTPException(status_code=404, detail="Page not found")

    button = source_page.buttons.get(req.source_key)
    if not button:
        raise HTTPException(status_code=404, detail="Button not found")

    # Find first empty slot in target page
    device_info = deck_controller.device.get_device_info()
    key_count = device_info.get("key_count", 32)

    target_key = -1
    for k in range(key_count):
        if k not in target_page.buttons:
            target_key = k
            break

    if target_key == -1:
        raise HTTPException(status_code=400, detail="Target page is full")

    # Move
    del source_page.buttons[req.source_key]
    button.key = target_key
    target_page.buttons[target_key] = button

    deck_controller.config_manager.save_config(config)
    deck_controller.render_current_page()
    return {"status": "ok", "new_key": target_key}


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
