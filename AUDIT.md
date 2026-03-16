# Code Audit: Stream Deck Pi Manager

## Issues & Findings

### 1. Performance: Font Loading in `StreamDeckManager`
- **Location:** `src/streamdeck_pi/core/device.py`
- **Issue:** `ImageFont.truetype()` is called twice (for text and icon) every time `set_button_text` is invoked. This reloads font files from disk, causing significant overhead.
- **Impact:** High. Frequent button updates (e.g., sensors) will be slow and resource-heavy.
- **Fix:** Implement a simple LRU cache or a dictionary to cache loaded fonts by (path, size).

### 2. Stability: Synchronous `requests` in Plugin Ticks
- **Location:** `src/streamdeck_pi/plugins/homeassistant.py`
- **Issue:** `HomeAssistantSensorPlugin.tick` calls `execute`, which uses `requests.get()` synchronously with a 5s timeout.
- **Impact:** Medium-High. If Home Assistant is slow, the entire `_tick_loop` in `DeckController` hangs, preventing other buttons from updating.
- **Fix:** Use `httpx` for async calls or run plugin execution in a `ThreadPoolExecutor`.

### 3. Architecture: Direct HID access for Neo
- **Location:** `src/streamdeck_pi/core/controller.py`
- **Issue:** `_send_neo_image` directly writes to the underlying HID device using `self.device.device.device.write(report)`.
- **Impact:** Low-Medium. This is brittle and might break if the `StreamDeck` library structure changes.
- **Fix:** Ideally, use library methods if available, but since it's a manual workaround for Neo, it should be better encapsulated.

### 4. Configuration: Lack of per-plugin validation
- **Location:** `src/streamdeck_pi/plugins/base.py`
- **Issue:** `validate_config` is a stub and not consistently used across the API.
- **Impact:** Low. Invalid config might cause runtime crashes.
- **Fix:** Implement robust schema validation (e.g., using `jsonschema`).

### 5. Home Assistant Integration: Redundant Calls
- **Location:** `src/streamdeck_pi/plugins/homeassistant.py`
- **Issue:** Multiple sensor buttons for the same HA instance will each make individual network calls.
- **Impact:** Low. Can be optimized by caching HA states globally for a short period.

### 6. Installation: Incompatible font package names on Debian Trixie
- **Location:** `install.py`
- **Issue:** The package `fonts-noto-emoji` is not available in newer Debian versions (like Trixie), causing the installation script to fail.
- **Impact:** Critical for new installations.
- **Fix:** Removed redundant heavy system font dependencies since they are bundled in the project assets.

### 7. Installation: Externally Managed Environment (PEP 668)
- **Location:** `install.py`
- **Issue:** Modern Debian versions prevent `pip` from installing into the system Python, causing the installer to fail.
- **Impact:** Critical for new installations.
- **Fix:** Redesigned `install.py` to create a dedicated virtual environment in `/opt/streamdeck-pi/venv` and updated the systemd service to use it. This isolates the application dependencies from the system Python.
