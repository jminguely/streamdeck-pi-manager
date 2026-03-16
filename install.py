#!/usr/bin/env python3
"""
Installation script for Stream Deck Pi Manager.
Updated to use a dedicated virtual environment for better stability.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Constants
INSTALL_DIR = Path("/opt/streamdeck-pi")
VENV_DIR = INSTALL_DIR / "venv"
CONFIG_DIR = Path("/etc/streamdeck-pi")
PROJECT_ROOT = Path(__file__).parent.absolute()

def run_command(cmd, check=True, cwd=None):
    """Run a shell command."""
    print(f"Running: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, check=False, cwd=cwd)
    if check and result.returncode != 0:
        print(f"Error: Command failed with return code {result.returncode}")
        sys.exit(1)
    return result.returncode == 0


def check_root():
    """Check if running as root."""
    if os.geteuid() != 0:
        print("This script must be run as root (use sudo)")
        sys.exit(1)


def install_dependencies():
    """Install system dependencies."""
    print("Installing system dependencies...")

    # Update package list
    run_command(["apt", "update"])

    # Base packages
    base_packages = [
        "python3-pip",
        "python3-venv",
        "libhidapi-libusb0",
        "libjpeg-dev",
        "zlib1g-dev",
        "libopenjp2-7",
    ]
    
    # Try to install base packages
    run_command(["apt", "install", "-y"] + base_packages)

    print("System dependencies installed successfully.")


def setup_virtual_environment():
    """Set up a dedicated virtual environment in /opt."""
    print(f"Setting up virtual environment in {VENV_DIR}...")
    
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create venv if it doesn't exist
    if not VENV_DIR.exists():
        run_command(["python3", "-m", "venv", str(VENV_DIR)])
    
    # Upgrade pip in venv
    pip_path = VENV_DIR / "bin" / "pip"
    run_command([str(pip_path), "install", "--upgrade", "pip"])
    
    # Install the package in editable mode into the venv
    print("Installing Stream Deck Pi Manager into virtual environment...")
    run_command([str(pip_path), "install", "-e", str(PROJECT_ROOT)])


def create_config_directory(username):
    """Create configuration directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Copy example config if target doesn't exist
    example_config = PROJECT_ROOT / "config" / "config.example.json"
    target_config = CONFIG_DIR / "config.json"
    
    if example_config.exists() and not target_config.exists():
        shutil.copy(example_config, target_config)
        print(f"Created default config at {target_config}")

    # Set ownership to the user
    shutil.chown(CONFIG_DIR, user=username, group=username)
    for item in CONFIG_DIR.glob("*"):
        shutil.chown(item, user=username, group=username)

    print(f"Configuration directory at {CONFIG_DIR} is ready.")


def setup_udev_rules():
    """Set up udev rules for Stream Deck."""
    print("Setting up udev rules...")

    udev_rule = """# Stream Deck devices
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fd9", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0fd9", MODE="0666", TAG+="uaccess"
"""

    rules_file = Path("/etc/udev/rules.d/99-streamdeck.rules")
    rules_file.write_text(udev_rule)

    # Reload udev rules
    run_command(["udevadm", "control", "--reload-rules"])
    run_command(["udevadm", "trigger"])


def setup_sudo_permissions(username):
    """Set up sudo permissions for shutdown/reboot."""
    print("Setting up sudo permissions...")

    sudoers_content = f"""{username} ALL=(ALL) NOPASSWD: /usr/sbin/shutdown
{username} ALL=(ALL) NOPASSWD: /usr/sbin/reboot
{username} ALL=(ALL) NOPASSWD: /usr/bin/systemctl
"""

    sudoers_file = Path("/etc/sudoers.d/streamdeck-pi")
    sudoers_file.write_text(sudoers_content)
    sudoers_file.chmod(0o440)


def create_systemd_service(username):
    """Create systemd service using the virtual environment."""
    print("Creating systemd service...")

    # Path to the executable in our venv
    executable_path = VENV_DIR / "bin" / "streamdeck-pi-web"

    service_content = f"""[Unit]
Description=Stream Deck Pi Manager
After=multi-user.target network.target

[Service]
Type=simple
User={username}
WorkingDirectory={PROJECT_ROOT}
ExecStart={executable_path}
Restart=always
RestartSec=5
Environment="PATH={VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
"""

    service_file = Path("/etc/systemd/system/streamdeck-pi.service")
    service_file.write_text(service_content)

    # Reload systemd
    run_command(["systemctl", "daemon-reload"])
    run_command(["systemctl", "enable", "streamdeck-pi.service"])

    print("Systemd service created and enabled using virtual environment.")


def main():
    """Main installation function."""
    print("=" * 60)
    print("Stream Deck Pi Manager Installation")
    print("=" * 60)
    print()

    check_root()

    # Get the user who invoked sudo
    username = os.environ.get("SUDO_USER", "pi")

    print(f"Installing for user: {username}")
    print(f"Project path: {PROJECT_ROOT}")
    print()

    # Installation steps
    install_dependencies()
    setup_virtual_environment()
    create_config_directory(username)
    setup_udev_rules()
    setup_sudo_permissions(username)
    create_systemd_service(username)

    print()
    print("=" * 60)
    print("Installation complete!")
    print("=" * 60)
    print()
    print("To start the service:")
    print("  sudo systemctl start streamdeck-pi")
    print()
    print("To check status:")
    print("  sudo systemctl status streamdeck-pi")
    print()
    print("Web interface will be available at:")
    print("  http://your-raspberry-pi-ip:8888")
    print()


if __name__ == "__main__":
    main()
