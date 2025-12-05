"""
FastAPI application for Stream Deck Pi Manager.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from streamdeck_pi.web.api import router as api_router
from streamdeck_pi.core.device import StreamDeckManager
from streamdeck_pi.core.config import ConfigManager
from streamdeck_pi.plugins.base import PluginManager
from streamdeck_pi.plugins import system, network, homeassistant

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Stream Deck Pi Manager",
        description="Web-based management interface for Elgato Stream Deck",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize managers
    device_manager = StreamDeckManager()
    plugin_manager = PluginManager(device_manager=device_manager)
    
    # Determine config path
    config_path = Path("/etc/streamdeck-pi/buttons.json")
    if not config_path.parent.exists():
        # Fallback for development
        config_path = Path("buttons.json")
        
    config_manager = ConfigManager(config_path=str(config_path))
    
    # Register built-in plugins
    plugin_manager.register_plugin(system.ShutdownPlugin)
    plugin_manager.register_plugin(system.RebootPlugin)
    plugin_manager.register_plugin(system.CPUInfoPlugin)
    plugin_manager.register_plugin(system.MemoryInfoPlugin)
    plugin_manager.register_plugin(system.ProcessControlPlugin)
    plugin_manager.register_plugin(system.DiskSpacePlugin)
    plugin_manager.register_plugin(network.ShowIPPlugin)
    plugin_manager.register_plugin(network.NetworkSpeedPlugin)
    plugin_manager.register_plugin(network.ToggleWiFiPlugin)
    plugin_manager.register_plugin(network.PingHostPlugin)
    plugin_manager.register_plugin(homeassistant.HomeAssistantPlugin)
    
    # Store in app state
    app.state.device_manager = device_manager
    app.state.plugin_manager = plugin_manager
    app.state.config_manager = config_manager
    app.state.button_configs = config_manager.load_buttons()
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Static files and templates
    base_path = Path(__file__).parent
    templates = Jinja2Templates(directory=str(base_path / "templates"))
    
    # Serve static files if directory exists
    static_path = base_path / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Root route
    @app.get("/")
    async def root(request: Request):
        """Render main page."""
        return templates.TemplateResponse("index.html", {"request": request})
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Connect to device on startup."""
        logger.info("Starting Stream Deck Pi Manager...")
        try:
            if device_manager.connect():
                logger.info("Successfully connected to Stream Deck")
            else:
                logger.warning("No Stream Deck device found")
        except Exception as e:
            logger.error(f"Failed to connect to Stream Deck: {e}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Disconnect from device on shutdown."""
        logger.info("Shutting down...")
        device_manager.disconnect()
    
    return app
