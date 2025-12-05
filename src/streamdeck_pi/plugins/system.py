"""
System control plugins.
"""
import subprocess
import psutil
from typing import Dict, Any
from streamdeck_pi.plugins.base import ButtonPlugin


class ShutdownPlugin(ButtonPlugin):
    """Shutdown the system."""
    
    id = "system.shutdown"
    name = "Shutdown"
    description = "Shutdown the system"
    icon = "power-off"
    category = "system"
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Execute shutdown command."""
        self.logger.info("Executing system shutdown")
        subprocess.run(["sudo", "shutdown", "-h", "now"])


class RebootPlugin(ButtonPlugin):
    """Reboot the system."""
    
    id = "system.reboot"
    name = "Reboot"
    description = "Reboot the system"
    icon = "rotate-right"
    category = "system"
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Execute reboot command."""
        self.logger.info("Executing system reboot")
        subprocess.run(["sudo", "reboot"])


class CPUInfoPlugin(ButtonPlugin):
    """Display CPU information."""
    
    id = "system.cpu_info"
    name = "CPU Info"
    description = "Display CPU usage and temperature"
    icon = "microchip"
    category = "system"
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Get CPU info."""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Try to get temperature
        try:
            temps = psutil.sensors_temperatures()
            temp = temps.get('cpu_thermal', [{}])[0].get('current', 0)
        except:
            temp = 0
        
        self.logger.info(f"CPU: {cpu_percent}% | Temp: {temp}°C")
        
        if self.device_manager:
            text = f"CPU\n{cpu_percent}%"
            if temp:
                text += f"\n{temp}°C"
                
            self.device_manager.set_button_text(
                button_id,
                text,
                font_size=context.get("font_size", 14) if context else 14,
                bg_color=context.get("bg_color", (0, 0, 0)) if context else (0, 0, 0),
                text_color=context.get("text_color", (255, 255, 255)) if context else (255, 255, 255)
            )
        
        return {
            "cpu_percent": cpu_percent,
            "temperature": temp
        }


class MemoryInfoPlugin(ButtonPlugin):
    """Display memory information."""
    
    id = "system.memory_info"
    name = "Memory Info"
    description = "Display memory usage"
    icon = "memory"
    category = "system"
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Get memory info."""
        mem = psutil.virtual_memory()
        
        self.logger.info(f"Memory: {mem.percent}% used")
        
        if self.device_manager:
            text = f"RAM\n{mem.percent}%"
            
            self.device_manager.set_button_text(
                button_id,
                text,
                font_size=context.get("font_size", 14) if context else 14,
                bg_color=context.get("bg_color", (0, 0, 0)) if context else (0, 0, 0),
                text_color=context.get("text_color", (255, 255, 255)) if context else (255, 255, 255)
            )
        
        return {
            "total": mem.total,
            "used": mem.used,
            "percent": mem.percent
        }


class ProcessControlPlugin(ButtonPlugin):
    """Control system processes."""
    
    id = "system.process_control"
    name = "Process Control"
    description = "Start/stop/restart system processes"
    icon = "gears"
    category = "system"
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "restart"],
                    "description": "Action to perform"
                },
                "service": {
                    "type": "string",
                    "description": "Systemd service name"
                }
            },
            "required": ["action", "service"]
        }
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Execute process control action."""
        action = self.config.get("action")
        service = self.config.get("service")
        
        if not action or not service:
            raise ValueError("Action and service must be configured")
        
        self.logger.info(f"Executing systemctl {action} {service}")
        subprocess.run(["sudo", "systemctl", action, service])


class DiskSpacePlugin(ButtonPlugin):
    """Display disk space information."""
    
    id = "system.disk_space"
    name = "Disk Space"
    description = "Display disk usage"
    icon = "hard-drive"
    category = "system"
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration schema."""
        return {
            "type": "object",
            "properties": {
                "mount_point": {
                    "type": "string",
                    "default": "/",
                    "description": "Mount point to check"
                }
            }
        }
    
    def execute(self, button_id: int, context: Dict[str, Any] = None):
        """Get disk space info."""
        mount_point = self.config.get("mount_point", "/")
        disk = psutil.disk_usage(mount_point)
        
        self.logger.info(f"Disk {mount_point}: {disk.percent}% used")
        
        if self.device_manager:
            text = f"Disk\n{disk.percent}%"
            
            self.device_manager.set_button_text(
                button_id,
                text,
                font_size=context.get("font_size", 14) if context else 14,
                bg_color=context.get("bg_color", (0, 0, 0)) if context else (0, 0, 0),
                text_color=context.get("text_color", (255, 255, 255)) if context else (255, 255, 255)
            )
        
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
