# Stream Deck Pi Manager

A modern web-based management interface for Elgato Stream Deck devices on Raspberry Pi (headless).

## Features

- 🎮 **Web Interface** - Manage your Stream Deck from any browser
- 🔌 **Plugin System** - Easy to extend with custom button actions
- 📦 **Easy Installation** - One-command install and update
- 🔄 **Auto-Start** - Systemd service for automatic startup
- 🎨 **Visual Editor** - Drag-and-drop button configuration
- 📊 **Real-time Preview** - See changes instantly
- 🔒 **Secure** - Built-in authentication and HTTPS support

## Supported Devices

- Elgato Stream Deck Neo
- Elgato Stream Deck Mini
- Elgato Stream Deck Original
- Elgato Stream Deck XL
- Elgato Stream Deck MK.2

## Quick Start

### Installation

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/streamdeck-pi-manager/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/yourusername/streamdeck-pi-manager.git
cd streamdeck-pi-manager
sudo python3 install.py
```

### Access Web Interface

Open your browser and navigate to:
```
http://your-raspberry-pi-ip:8888
```

Default credentials:
- Username: `admin`
- Password: `streamdeck` (change on first login)

## Built-in Plugins

### System Control
- Shutdown
- Reboot
- Sleep/Wake
- Process Management

### System Information
- CPU Usage
- Memory Usage
- Temperature
- Disk Space
- Network Stats

### Media Control
- Volume Control
- Play/Pause
- Next/Previous Track

### Network
- Toggle WiFi
- Show IP Address
- Network Speed

### Custom Scripts
- Execute bash scripts
- Python scripts
- HTTP requests

## Configuration

Configuration is stored in `/etc/streamdeck-pi/config.json`:

```json
{
  "web": {
    "host": "0.0.0.0",
    "port": 8888,
    "ssl": false
  },
  "device": {
    "brightness": 50,
    "timeout": 300
  },
  "security": {
    "enabled": true,
    "username": "admin",
    "password_hash": "..."
  }
}
```

## API Documentation

REST API available at `/api/v1/`:

- `GET /api/v1/device` - Get device information
- `GET /api/v1/buttons` - List all buttons
- `PUT /api/v1/buttons/:id` - Update button configuration
- `POST /api/v1/buttons/:id/press` - Simulate button press
- `GET /api/v1/plugins` - List available plugins

## Development

### Project Structure

```
streamdeck-pi-manager/
├── src/
│   └── streamdeck_pi/
│       ├── core/           # Core device management
│       ├── web/            # Web interface (FastAPI)
│       ├── plugins/        # Button action plugins
│       └── __init__.py
├── tests/
├── docs/
├── config/
│   ├── config.example.json
│   └── systemd/
├── install.py
├── setup.py
├── requirements.txt
└── README.md
```

### Running in Development Mode

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m streamdeck_pi.web --dev
```

### Creating Custom Plugins

```python
from streamdeck_pi.plugins import ButtonPlugin

class MyCustomPlugin(ButtonPlugin):
    name = "My Custom Action"
    description = "Does something awesome"
    icon = "custom-icon.png"
    
    def execute(self, button_id: int, context: dict):
        """Execute the plugin action"""
        # Your code here
        pass
    
    def get_config_schema(self) -> dict:
        """Return JSON schema for configuration"""
        return {
            "type": "object",
            "properties": {
                "setting1": {"type": "string"}
            }
        }
```

## Update

```bash
sudo streamdeck-pi update
```

Or:

```bash
cd /opt/streamdeck-pi-manager
git pull
sudo systemctl restart streamdeck-pi
```

## Uninstall

```bash
sudo streamdeck-pi uninstall
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

- [python-elgato-streamdeck](https://github.com/abcminiuser/python-elgato-streamdeck)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)

## Support

- 📖 [Documentation](https://streamdeck-pi-manager.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/yourusername/streamdeck-pi-manager/issues)
- 💬 [Discussions](https://github.com/yourusername/streamdeck-pi-manager/discussions)

## Roadmap

- [ ] Multi-page support
- [ ] Button macros (sequences)
- [ ] MQTT integration
- [ ] Home Assistant integration
- [ ] Mobile app
- [ ] Cloud sync
- [ ] Button templates marketplace
