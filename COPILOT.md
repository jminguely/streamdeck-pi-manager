# Stream Deck Pi Manager - Copilot Instructions

You are an expert Python developer specializing in hardware integration (Stream Deck) and web services (FastAPI).

## Project Overview
This project is a Stream Deck manager designed to run on a Raspberry Pi. It provides a web interface for configuring buttons and integrates with Home Assistant, system monitoring, and network tools.

## Key Technologies
- **Python 3.10+**
- **FastAPI**: Web framework and API.
- **StreamDeck (python-elgato-streamdeck)**: Core hardware library.
- **Pillow (PIL)**: Image generation for buttons.
- **Jinja2**: Web templates.

## Architecture
- `src/streamdeck_pi/core`: Core logic (Controller, Device Manager, Config, Settings).
- `src/streamdeck_pi/plugins`: Plugin system for button actions (Home Assistant, System, etc.).
- `src/streamdeck_pi/web`: FastAPI application and frontend.

## Coding Standards
- Use **Type Hints** for all function signatures.
- **Async/Await**: Use async for web-related operations, but be mindful of the synchronous Stream Deck library.
- **Logging**: Use the standard `logging` module. Each module should have its own logger.
- **Thread Safety**: Access to the Stream Deck device must be thread-safe (use the lock in `StreamDeckManager`).

## Performance Guidelines
- **Font Caching**: Do not reload fonts from disk on every render. Use a cache.
- **Non-blocking Plugins**: Plugin `tick()` methods should be fast. Avoid long-running synchronous network calls in the main tick loop.
- **Image Optimization**: Pre-render or cache button images when possible.

## Home Assistant Integration
- Plugins should use the global Home Assistant configuration from `SettingsManager`.
- Prefer asynchronous HTTP clients (like `httpx`) for Home Assistant calls if possible, or ensure they don't block the controller loop.

## Stream Deck Neo Support
- Specific support for the Neo's "Info Bar" (touchscreen) is implemented via manual HID reports in `DeckController._send_neo_image`.
