#!/usr/bin/env python3
"""
Installation script for Stream Deck Pi Manager.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
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

    # Install required packages
    packages = [
        "python3-pip",
        "python3-venv",
        "libhidapi-libusb0",
        "libjpeg-dev",
        "zlib1g-dev",
        "libopenjp2-7",
    ]

    run_command(["apt", "install", "-y"] + packages)


def install_python_package():
    """Install the Python package."""
    print("Installing Stream Deck Pi Manager...")

    # Install package
    run_command([sys.executable, "-m", "pip", "install", "-e", "."])


def create_config_directory(username):
    """Create configuration directory."""
    config_dir = Path("/etc/streamdeck-pi")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Copy example config
    example_config = Path("config/config.example.json")
    if example_config.exists():
        shutil.copy(example_config, config_dir / "config.json")

    # Set ownership to the user
    shutil.chown(config_dir, user=username, group=username)
    for item in config_dir.glob("*"):
        shutil.chown(item, user=username, group=username)

    print(f"Configuration directory created at {config_dir}")


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
    """Create systemd service."""
    print("Creating systemd service...")

    service_content = f"""[Unit]
Description=Stream Deck Pi Manager
After=multi-user.target network.target

[Service]
Type=simple
User={username}
WorkingDirectory=/home/{username}
ExecStart=/usr/local/bin/streamdeck-pi-web
Restart=always
RestartSec=5
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
"""

    service_file = Path("/etc/systemd/system/streamdeck-pi.service")
    service_file.write_text(service_content)

    # Reload systemd
    run_command(["systemctl", "daemon-reload"])
    run_command(["systemctl", "enable", "streamdeck-pi.service"])

    print("Systemd service created and enabled")


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
    print()

    # Installation steps
    install_dependencies()
    install_python_package()
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
    print("Default credentials:")
    print("  Username: admin")
    print("  Password: streamdeck")
    print()
    print("Note: Please change the default password on first login!")
    print()


if __name__ == "__main__":
    main()
