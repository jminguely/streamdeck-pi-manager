"""
Network-related plugins.
"""
import subprocess
import socket
from typing import Dict, Any
import psutil
from streamdeck_pi.plugins.base import ButtonPlugin


class ShowIPPlugin(ButtonPlugin):
    """Display IP address."""
    
    id = "network.show_ip"
    name = "Show IP Address"
    description = "Display the current IP address"
    icon = "network-wired"
    category = "network"
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "interface": {
                    "type": "string",
                    "default": "eth0",
                    "description": "Network interface"
                }
            }
        }
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Get IP address."""
        interface = self.config.get("interface", "eth0")
        
        try:
            addrs = psutil.net_if_addrs().get(interface, [])
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    self.logger.info(f"IP Address ({interface}): {addr.address}")
                    return {"ip": addr.address, "interface": interface}
        except Exception as e:
            self.logger.error(f"Failed to get IP: {e}")
            return {"error": str(e)}


class NetworkSpeedPlugin(ButtonPlugin):
    """Display network speed."""
    
    id = "network.speed"
    name = "Network Speed"
    description = "Display network upload/download speed"
    icon = "gauge"
    category = "network"
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Get network speed."""
        # Get network IO counters
        net_io_1 = psutil.net_io_counters()
        
        # Wait a bit
        import time
        time.sleep(1)
        
        net_io_2 = psutil.net_io_counters()
        
        # Calculate speeds (bytes per second)
        download_speed = net_io_2.bytes_recv - net_io_1.bytes_recv
        upload_speed = net_io_2.bytes_sent - net_io_1.bytes_sent
        
        self.logger.info(f"Network: ↓{download_speed/1024:.1f} KB/s | ↑{upload_speed/1024:.1f} KB/s")
        
        return {
            "download": download_speed,
            "upload": upload_speed
        }


class ToggleWiFiPlugin(ButtonPlugin):
    """Toggle WiFi on/off."""
    
    id = "network.toggle_wifi"
    name = "Toggle WiFi"
    description = "Turn WiFi on or off"
    icon = "wifi"
    category = "network"
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "interface": {
                    "type": "string",
                    "default": "wlan0",
                    "description": "WiFi interface name"
                }
            }
        }
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Toggle WiFi."""
        interface = self.config.get("interface", "wlan0")
        
        # Check current state
        try:
            result = subprocess.run(
                ["ip", "link", "show", interface],
                capture_output=True,
                text=True
            )
            
            is_up = "UP" in result.stdout
            
            # Toggle state
            if is_up:
                self.logger.info(f"Disabling WiFi ({interface})")
                subprocess.run(["sudo", "ip", "link", "set", interface, "down"])
            else:
                self.logger.info(f"Enabling WiFi ({interface})")
                subprocess.run(["sudo", "ip", "link", "set", interface, "up"])
                
        except Exception as e:
            self.logger.error(f"Failed to toggle WiFi: {e}")


class PingHostPlugin(ButtonPlugin):
    """Ping a host to check connectivity."""
    
    id = "network.ping"
    name = "Ping Host"
    description = "Ping a host and display result"
    icon = "paper-plane"
    category = "network"
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "default": "8.8.8.8",
                    "description": "Host to ping"
                },
                "count": {
                    "type": "integer",
                    "default": 3,
                    "description": "Number of pings"
                }
            },
            "required": ["host"]
        }
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Ping host."""
        host = self.config.get("host", "8.8.8.8")
        count = self.config.get("count", 3)
        
        self.logger.info(f"Pinging {host}...")
        
        try:
            result = subprocess.run(
                ["ping", "-c", str(count), host],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            success = result.returncode == 0
            
            # Parse output for average time
            if success:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'avg' in line:
                        # Extract average time
                        parts = line.split('/')
                        if len(parts) >= 5:
                            avg_time = parts[4]
                            self.logger.info(f"Ping {host}: {avg_time}ms")
                            return {"success": True, "avg_time": avg_time}
            
            return {"success": success}
            
        except Exception as e:
            self.logger.error(f"Ping failed: {e}")
            return {"success": False, "error": str(e)}
