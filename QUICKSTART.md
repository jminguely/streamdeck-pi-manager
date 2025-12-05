# Quick Start Guide

## Installation on Raspberry Pi

### 1. Clone the Repository

```bash
cd ~
git clone https://github.com/jminguely/streamdeck-pi-manager.git
cd streamdeck-pi-manager
```

### 2. Run Installation

```bash
sudo python3 install.py
```

> **Note for Raspberry Pi OS Bookworm or newer:**
> If you encounter an `externally-managed-environment` error, run the installation with this environment variable:
>
> ```bash
> sudo PIP_BREAK_SYSTEM_PACKAGES
> ```

````

This will:

- Install all system dependencies
- Set up Python package
- Configure udev rules
- Create systemd service
- Set up sudo permissions

### 3. Start the Service

```bash
sudo systemctl start streamdeck-pi
````

### 4. Access Web Interface

Open your browser and navigate to:

```
http://your-raspberry-pi-ip:8888
```

Default login:

- Username: `admin`
- Password: `streamdeck`

**⚠️ Change the default password immediately!**

## Development Setup (on Mac/PC)

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Run in Development Mode

```bash
python3 -m streamdeck_pi.web --dev
```

The web interface will be available at `http://localhost:8888`

**Note**: You need a Stream Deck connected to your development machine.

## Basic Usage

### Configure a Button

1. Click on any button in the grid
2. Enter a label
3. Select a plugin (e.g., "Shutdown")
4. Configure plugin settings if needed
5. Click "Save"

### Built-in Plugins

**System Control:**

- Shutdown
- Reboot
- CPU Info
- Memory Info
- Process Control
- Disk Space

**Network:**

- Show IP Address
- Network Speed
- Toggle WiFi
- Ping Host

### CLI Commands

```bash
# Show device info
streamdeck-pi info

# Test connection
streamdeck-pi test

# Clear all buttons
streamdeck-pi clear
```

## Troubleshooting

### Device Not Detected

```bash
# Check if device is connected
lsusb | grep 0fd9

# Check udev rules
ls -l /etc/udev/rules.d/99-streamdeck.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Service Not Starting

```bash
# Check service status
sudo systemctl status streamdeck-pi

# View logs
sudo journalctl -u streamdeck-pi -f

# Restart service
sudo systemctl restart streamdeck-pi
```

### Web Interface Not Accessible

```bash
# Check if service is running
sudo systemctl status streamdeck-pi

# Check port is listening
sudo netstat -tlnp | grep 8888

# Check firewall
sudo ufw status
```

## Next Steps

- Read the full [README.md](README.md)
- Create custom plugins (see [Plugin Development Guide](docs/plugins.md))
- Configure HTTPS (see [Security Guide](docs/security.md))
- Set up automatic backups

## Support

- 📖 [Full Documentation](docs/)
- 🐛 [Report Issues](https://github.com/jminguely/streamdeck-pi-manager/issues)
- 💬 [Community Discussions](https://github.com/jminguely/streamdeck-pi-manager/discussions)
