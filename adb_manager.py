"""
ADB Manager Module - LX Tool Ultimate

Quản lý ADB commands và communication với Android devices.

Tính năng:
- Execute shell commands
- Install/Uninstall APK
- Push/Pull files
- Get device properties
- Logcat streaming
- Port forwarding
"""

import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import time

import config
import logger as logger_module


# ====================================================================
# LOGGER
# ====================================================================

log = logger_module.get_logger(__name__)


# ====================================================================
# ADB MANAGER CLASS
# ====================================================================

class ADBManager:
    """Quản lý ADB operations."""
    
    def __init__(self):
        """Khởi tạo ADBManager."""
        self.adb_path = config.get_adb_path()
        if not self.adb_path:
            raise RuntimeError("ADB not found!")
    
    def _execute_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """
        Thực hiện ADB command.
        
        Args:
            command: List of command parts
            timeout: Command timeout in seconds
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        try:
            logger_module.log_adb_command(" ".join(command), __name__)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            if not success:
                logger_module.log_adb_error("unknown", " ".join(command), output, __name__)
            
            return success, output.strip()
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timeout after {timeout}s"
            logger_module.log_adb_error("unknown", " ".join(command), error_msg, __name__)
            return False, error_msg
        
        except Exception as e:
            error_msg = str(e)
            logger_module.log_adb_error("unknown", " ".join(command), error_msg, __name__)
            return False, error_msg
    
    def get_devices(self) -> List[str]:
        """
        Lấy danh sách các devices kết nối.
        
        Returns:
            List[str]: List of device serials
        """
        success, output = self._execute_command([str(self.adb_path), "devices"])
        
        if not success:
            return []
        
        # Parse output
        devices = []
        for line in output.split('\n')[1:]:  # Skip header
            if line.strip() and '\t' in line:
                serial, status = line.split('\t')
                if status.strip() == "device":
                    devices.append(serial.strip())
        
        return devices
    
    def is_device_connected(self, device_serial: str) -> bool:
        """Kiểm tra device có kết nối không."""
        devices = self.get_devices()
        return device_serial in devices
    
    def shell(self, device_serial: str, command: str, timeout: int = 30) -> Tuple[bool, str]:
        """
        Chạy shell command trên device.
        
        Args:
            device_serial: Device serial
            command: Shell command
            timeout: Command timeout
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = [str(self.adb_path), "-s", device_serial, "shell", command]
        return self._execute_command(cmd, timeout)
    
    def push(self, device_serial: str, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """
        Push file từ local sang device.
        
        Args:
            device_serial: Device serial
            local_path: Local file path
            remote_path: Remote path on device
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = [str(self.adb_path), "-s", device_serial, "push", local_path, remote_path]
        return self._execute_command(cmd, timeout=60)
    
    def pull(self, device_serial: str, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """
        Pull file từ device sang local.
        
        Args:
            device_serial: Device serial
            remote_path: Remote path on device
            local_path: Local file path
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = [str(self.adb_path), "-s", device_serial, "pull", remote_path, local_path]
        return self._execute_command(cmd, timeout=60)
    
    def install(self, device_serial: str, apk_path: str, force: bool = False) -> Tuple[bool, str]:
        """
        Cài đặt APK trên device.
        
        Args:
            device_serial: Device serial
            apk_path: Path to APK file
            force: Force install (replace existing)
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = [str(self.adb_path), "-s", device_serial, "install"]
        if force:
            cmd.append("-r")
        cmd.append(apk_path)
        
        return self._execute_command(cmd, timeout=120)
    
    def uninstall(self, device_serial: str, package_name: str) -> Tuple[bool, str]:
        """
        Gỡ cài đặt package từ device.
        
        Args:
            device_serial: Device serial
            package_name: Package name
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = [str(self.adb_path), "-s", device_serial, "uninstall", package_name]
        return self._execute_command(cmd, timeout=60)
    
    def get_property(self, device_serial: str, prop: str) -> str:
        """
        Lấy device property.
        
        Args:
            device_serial: Device serial
            prop: Property name (e.g., "ro.build.version.release")
            
        Returns:
            str: Property value
        """
        success, output = self.shell(device_serial, f"getprop {prop}")
        return output if success else ""
    
    def get_device_info(self, device_serial: str) -> Dict:
        """
        Lấy thông tin device.
        
        Args:
            device_serial: Device serial
            
        Returns:
            Dict: Device information
        """
        info = {
            "serial": device_serial,
            "model": self.get_property(device_serial, "ro.product.model"),
            "manufacturer": self.get_property(device_serial, "ro.product.manufacturer"),
            "android_version": self.get_property(device_serial, "ro.build.version.release"),
            "api_level": self.get_property(device_serial, "ro.build.version.sdk"),
            "device_name": self.get_property(device_serial, "ro.product.device"),
        }
        return info
    
    def get_installed_packages(self, device_serial: str) -> List[str]:
        """
        Lấy danh sách installed packages.
        
        Args:
            device_serial: Device serial
            
        Returns:
            List[str]: List of package names
        """
        success, output = self.shell(device_serial, "pm list packages")
        if not success:
            return []
        
        packages = []
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith("package:"):
                package_name = line.replace("package:", "")
                packages.append(package_name)
        
        return packages
    
    def is_package_installed(self, device_serial: str, package_name: str) -> bool:
        """Kiểm tra package có cài đặt không."""
        packages = self.get_installed_packages(device_serial)
        return package_name in packages
    
    def clear_app_data(self, device_serial: str, package_name: str) -> Tuple[bool, str]:
        """
        Xóa app data.
        
        Args:
            device_serial: Device serial
            package_name: Package name
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        return self.shell(device_serial, f"pm clear {package_name}")
    
    def force_stop(self, device_serial: str, package_name: str) -> Tuple[bool, str]:
        """
        Force stop app.
        
        Args:
            device_serial: Device serial
            package_name: Package name
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        return self.shell(device_serial, f"am force-stop {package_name}")
    
    def start_activity(self, device_serial: str, package_name: str, activity: str) -> Tuple[bool, str]:
        """
        Start activity.
        
        Args:
            device_serial: Device serial
            package_name: Package name
            activity: Activity name
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = f"am start -n {package_name}/{activity}"
        return self.shell(device_serial, cmd)
    
    def take_screenshot(self, device_serial: str, remote_path: str) -> Tuple[bool, str]:
        """
        Chụp screenshot trên device.
        
        Args:
            device_serial: Device serial
            remote_path: Remote path to save screenshot
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = f"screencap -p {remote_path}"
        return self.shell(device_serial, cmd)
    
    def forward_port(self, device_serial: str, local_port: int, remote_port: int) -> Tuple[bool, str]:
        """
        Forward port.
        
        Args:
            device_serial: Device serial
            local_port: Local port
            remote_port: Remote port
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        cmd = [str(self.adb_path), "-s", device_serial, "forward", f"tcp:{local_port}", f"tcp:{remote_port}"]
        return self._execute_command(cmd)
    
    def get_logcat(self, device_serial: str, lines: int = 50) -> str:
        """
        Lấy logcat output.
        
        Args:
            device_serial: Device serial
            lines: Số dòng cần lấy
            
        Returns:
            str: Logcat output
        """
        success, output = self.shell(device_serial, f"logcat -d -t {lines}")
        return output if success else ""
    
    def reboot(self, device_serial: str) -> Tuple[bool, str]:
        """
        Reboot device.
        
        Args:
            device_serial: Device serial
            
        Returns:
            Tuple[bool, str]: (success, output)
        """
        return self.shell(device_serial, "reboot", timeout=60)


# ====================================================================
# GLOBAL INSTANCE
# ====================================================================

_adb_manager = None

def get_adb_manager() -> ADBManager:
    """Lấy ADB manager instance (singleton)."""
    global _adb_manager
    if _adb_manager is None:
        _adb_manager = ADBManager()
    return _adb_manager


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - ADB Manager Test")
    print("="*70 + "\n")
    
    try:
        adb = get_adb_manager()
        
        # Get devices
        print("Getting connected devices...")
        devices = adb.get_devices()
        print(f"Connected devices: {devices}")
        
        if devices:
            device = devices[0]
            print(f"\nTesting with device: {device}")
            
            # Get device info
            print("Getting device info...")
            info = adb.get_device_info(device)
            for key, value in info.items():
                print(f"  {key}: {value}")
            
            # Get installed packages
            print("\nGetting installed packages...")
            packages = adb.get_installed_packages(device)
            print(f"  Total: {len(packages)}")
            print(f"  First 5: {packages[:5]}")
        
        print("\n" + "="*70)
        print("✓ ADB Manager tests completed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
