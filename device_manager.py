"""
Device Manager Module - LX Tool Ultimate

Quản lý lifecycle các Android devices.

Tính năng:
- Device discovery
- Device status tracking
- Device information management
- Batch operations
- Event notifications
"""

import threading
import time
from datetime import datetime
from typing import List, Dict, Optional, Callable
from enum import Enum

import config
import logger as logger_module
from adb_manager import get_adb_manager


# ====================================================================
# LOGGER
# ====================================================================

log = logger_module.get_logger(__name__)


# ====================================================================
# ENUMS
# ====================================================================

class DeviceStatus(Enum):
    """Device status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


# ====================================================================
# DEVICE CLASS
# ====================================================================

class Device:
    """Represents an Android device."""
    
    def __init__(self, serial: str):
        """
        Khởi tạo Device.
        
        Args:
            serial: Device serial number
        """
        self.serial = serial
        self.status = DeviceStatus.DISCONNECTED
        self.name = None
        self.model = None
        self.android_version = None
        self.api_level = None
        self.device_name = None
        self.manufacturer = None
        self.ip_address = None
        self.adb_port = 5037
        self.scrcpy_port = None
        
        self.connected_at = None
        self.last_seen = datetime.now()
        self.properties = {}
        
        self._lock = threading.Lock()
    
    def update(self, info: Dict):
        """Cập nhật thông tin device."""
        with self._lock:
            self.name = info.get("name", self.name)
            self.model = info.get("model", self.model)
            self.android_version = info.get("android_version", self.android_version)
            self.api_level = info.get("api_level", self.api_level)
            self.device_name = info.get("device_name", self.device_name)
            self.manufacturer = info.get("manufacturer", self.manufacturer)
            self.ip_address = info.get("ip_address", self.ip_address)
            self.scrcpy_port = info.get("scrcpy_port", self.scrcpy_port)
            self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert device to dictionary."""
        with self._lock:
            return {
                "serial": self.serial,
                "status": self.status.value,
                "name": self.name,
                "model": self.model,
                "android_version": self.android_version,
                "api_level": self.api_level,
                "device_name": self.device_name,
                "manufacturer": self.manufacturer,
                "ip_address": self.ip_address,
                "adb_port": self.adb_port,
                "scrcpy_port": self.scrcpy_port,
                "connected_at": self.connected_at.isoformat() if self.connected_at else None,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            }


# ====================================================================
# DEVICE MANAGER CLASS
# ====================================================================

class DeviceManager:
    """Quản lý devices."""
    
    def __init__(self):
        """Khởi tạo DeviceManager."""
        self.adb = get_adb_manager()
        self.devices: Dict[str, Device] = {}
        self._lock = threading.Lock()
        self._is_monitoring = False
        self._monitor_thread = None
        self._callbacks = {
            "on_device_connected": [],
            "on_device_disconnected": [],
            "on_device_updated": [],
            "on_device_error": [],
        }
    
    def register_callback(self, event: str, callback: Callable):
        """
        Đăng ký callback cho sự kiện.
        
        Args:
            event: Event name (on_device_connected, on_device_disconnected, etc.)
            callback: Callback function
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
            log.info(f"Callback registered: {event}")
    
    def _emit_event(self, event: str, data: Dict):
        """Emit event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    log.error(f"Callback error: {e}")
    
    def start_monitoring(self, interval: int = 5):
        """
        Bắt đầu monitoring devices.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._is_monitoring:
            log.warning("Monitoring already started")
            return
        
        self._is_monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        log.info("Device monitoring started")
    
    def stop_monitoring(self):
        """Dừng monitoring devices."""
        self._is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        log.info("Device monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Monitoring loop."""
        while self._is_monitoring:
            try:
                self.refresh_devices()
                time.sleep(interval)
            except Exception as e:
                log.error(f"Monitor loop error: {e}")
                time.sleep(interval)
    
    def refresh_devices(self):
        """Refresh device list từ ADB."""
        try:
            connected_serials = self.adb.get_devices()
            
            with self._lock:
                # Check for new devices
                for serial in connected_serials:
                    if serial not in self.devices:
                        self._add_device(serial)
                
                # Check for disconnected devices
                disconnected_serials = []
                for serial in self.devices:
                    if serial not in connected_serials:
                        disconnected_serials.append(serial)
                
                for serial in disconnected_serials:
                    self._remove_device(serial)
        
        except Exception as e:
            log.error(f"Failed to refresh devices: {e}")
    
    def _add_device(self, serial: str):
        """Thêm device mới."""
        device = Device(serial)
        device.status = DeviceStatus.CONNECTING
        
        # Lấy thông tin device
        try:
            info = self.adb.get_device_info(serial)
            device.update(info)
            device.status = DeviceStatus.CONNECTED
            device.connected_at = datetime.now()
            
            self.devices[serial] = device
            log.info(f"Device added: {serial} ({info.get('model', 'Unknown')})")
            
            # Emit event
            self._emit_event("on_device_connected", device.to_dict())
        
        except Exception as e:
            log.error(f"Failed to add device {serial}: {e}")
            device.status = DeviceStatus.ERROR
            self.devices[serial] = device
            self._emit_event("on_device_error", device.to_dict())
    
    def _remove_device(self, serial: str):
        """Xoá device."""
        if serial in self.devices:
            device = self.devices.pop(serial)
            device.status = DeviceStatus.DISCONNECTED
            log.info(f"Device removed: {serial}")
            self._emit_event("on_device_disconnected", device.to_dict())
    
    def get_device(self, serial: str) -> Optional[Device]:
        """Lấy device by serial."""
        with self._lock:
            return self.devices.get(serial)
    
    def get_all_devices(self) -> List[Device]:
        """Lấy tất cả devices."""
        with self._lock:
            return list(self.devices.values())
    
    def get_connected_devices(self) -> List[Device]:
        """Lấy tất cả connected devices."""
        with self._lock:
            return [d for d in self.devices.values() if d.status == DeviceStatus.CONNECTED]
    
    def get_device_count(self) -> int:
        """Lấy số lượng devices."""
        with self._lock:
            return len(self.devices)
    
    def get_connected_device_count(self) -> int:
        """Lấy số lượng connected devices."""
        with self._lock:
            return len([d for d in self.devices.values() if d.status == DeviceStatus.CONNECTED])
    
    def install_apk_on_device(self, device_serial: str, apk_path: str, force: bool = False) -> bool:
        """
        Cài đặt APK trên device.
        
        Args:
            device_serial: Device serial
            apk_path: Path to APK file
            force: Force install
            
        Returns:
            bool: Success status
        """
        try:
            success, output = self.adb.install(device_serial, apk_path, force=force)
            if success:
                log.info(f"APK installed on {device_serial}: {apk_path}")
            else:
                log.error(f"Failed to install APK: {output}")
            return success
        except Exception as e:
            log.error(f"Error installing APK: {e}")
            return False
    
    def uninstall_package_on_device(self, device_serial: str, package_name: str) -> bool:
        """
        Gỡ cài đặt package.
        
        Args:
            device_serial: Device serial
            package_name: Package name
            
        Returns:
            bool: Success status
        """
        try:
            success, output = self.adb.uninstall(device_serial, package_name)
            if success:
                log.info(f"Package uninstalled on {device_serial}: {package_name}")
            else:
                log.error(f"Failed to uninstall package: {output}")
            return success
        except Exception as e:
            log.error(f"Error uninstalling package: {e}")
            return False
    
    def push_file_to_device(self, device_serial: str, local_path: str, remote_path: str) -> bool:
        """
        Push file tới device.
        
        Args:
            device_serial: Device serial
            local_path: Local path
            remote_path: Remote path
            
        Returns:
            bool: Success status
        """
        try:
            success, output = self.adb.push(device_serial, local_path, remote_path)
            if success:
                log.info(f"File pushed to {device_serial}: {remote_path}")
            else:
                log.error(f"Failed to push file: {output}")
            return success
        except Exception as e:
            log.error(f"Error pushing file: {e}")
            return False
    
    def pull_file_from_device(self, device_serial: str, remote_path: str, local_path: str) -> bool:
        """
        Pull file từ device.
        
        Args:
            device_serial: Device serial
            remote_path: Remote path
            local_path: Local path
            
        Returns:
            bool: Success status
        """
        try:
            success, output = self.adb.pull(device_serial, remote_path, local_path)
            if success:
                log.info(f"File pulled from {device_serial}: {local_path}")
            else:
                log.error(f"Failed to pull file: {output}")
            return success
        except Exception as e:
            log.error(f"Error pulling file: {e}")
            return False
    
    def take_screenshot(self, device_serial: str, save_path: str) -> bool:
        """
        Chụp screenshot.
        
        Args:
            device_serial: Device serial
            save_path: Path to save screenshot
            
        Returns:
            bool: Success status
        """
        try:
            remote_path = "/sdcard/screenshot.png"
            
            # Take screenshot on device
            success, output = self.adb.take_screenshot(device_serial, remote_path)
            if not success:
                log.error(f"Failed to take screenshot: {output}")
                return False
            
            # Pull screenshot
            time.sleep(0.5)  # Wait for file to be written
            success = self.pull_file_from_device(device_serial, remote_path, save_path)
            
            # Delete remote screenshot
            if success:
                self.adb.shell(device_serial, f"rm {remote_path}")
            
            return success
        
        except Exception as e:
            log.error(f"Error taking screenshot: {e}")
            return False
    
    def reboot_device(self, device_serial: str) -> bool:
        """
        Reboot device.
        
        Args:
            device_serial: Device serial
            
        Returns:
            bool: Success status
        """
        try:
            success, output = self.adb.reboot(device_serial)
            if success:
                log.info(f"Device rebooted: {device_serial}")
                with self._lock:
                    if device_serial in self.devices:
                        self.devices[device_serial].status = DeviceStatus.DISCONNECTED
            else:
                log.error(f"Failed to reboot: {output}")
            return success
        except Exception as e:
            log.error(f"Error rebooting device: {e}")
            return False
    
    def batch_install_apk(self, apk_path: str, devices: Optional[List[str]] = None, force: bool = False) -> Dict[str, bool]:
        """
        Cài đặt APK trên nhiều devices.
        
        Args:
            apk_path: Path to APK file
            devices: List of device serials (None = all)
            force: Force install
            
        Returns:
            Dict[serial, success]: Installation results
        """
        if devices is None:
            devices = [d.serial for d in self.get_connected_devices()]
        
        results = {}
        for device_serial in devices:
            results[device_serial] = self.install_apk_on_device(device_serial, apk_path, force=force)
        
        return results


# ====================================================================
# GLOBAL INSTANCE
# ====================================================================

_device_manager = None

def get_device_manager() -> DeviceManager:
    """Lấy DeviceManager instance (singleton)."""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
    return _device_manager


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - Device Manager Test")
    print("="*70 + "\n")
    
    try:
        dm = get_device_manager()
        
        # Register callbacks
        def on_connected(data):
            print(f"✓ Device connected: {data['serial']} ({data['model']})")
        
        def on_disconnected(data):
            print(f"✗ Device disconnected: {data['serial']}")
        
        dm.register_callback("on_device_connected", on_connected)
        dm.register_callback("on_device_disconnected", on_disconnected)
        
        # Start monitoring
        print("Starting device monitoring...")
        dm.start_monitoring(interval=2)
        
        # Wait and check
        print("Waiting for devices...")
        time.sleep(5)
        
        # Get devices
        devices = dm.get_all_devices()
        print(f"\nTotal devices: {len(devices)}")
        print(f"Connected: {dm.get_connected_device_count()}")
        
        for device in devices:
            print(f"\n  Serial: {device.serial}")
            print(f"  Status: {device.status.value}")
            print(f"  Model: {device.model}")
            print(f"  Android: {device.android_version}")
        
        # Stop monitoring
        dm.stop_monitoring()
        
        print("\n" + "="*70)
        print("✓ Device Manager tests completed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
