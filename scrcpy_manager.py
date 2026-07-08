"""
Scrcpy Manager Module - LX Tool Ultimate

Quản lý scrcpy screen mirroring.

Tính năng:
- Scrcpy process management
- Screen streaming
- Input control
- Screen recording
- Port management
"""

import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, List
from enum import Enum

import config
import logger as logger_module


# ====================================================================
# LOGGER
# ====================================================================

log = logger_module.get_logger(__name__)


# ====================================================================
# ENUMS
# ====================================================================

class ScrcpyStatus(Enum):
    """Scrcpy process status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


# ====================================================================
# SCRCPY MANAGER CLASS
# ====================================================================

class ScrcpyManager:
    """Quản lý scrcpy processes."""
    
    def __init__(self):
        """Khởi tạo ScrcpyManager."""
        self.scrcpy_path = config.get_scrcpy_path()
        self.processes = {}  # serial -> process info
        self._lock = threading.Lock()
    
    def is_available(self) -> bool:
        """Check if scrcpy is available."""
        return self.scrcpy_path is not None and Path(self.scrcpy_path).exists()
    
    def start_mirror(self, device_serial: str, local_port: int = 0, max_size: int = 1024, 
                     max_fps: int = 60, bit_rate: str = "8M") -> Tuple[bool, str]:
        """
        Bắt đầu screen mirroring.
        
        Args:
            device_serial: Device serial
            local_port: Local port (0 = auto)
            max_size: Max screen size
            max_fps: Max FPS
            bit_rate: Video bit rate
            
        Returns:
            Tuple[bool, str]: (success, port/error)
        """
        try:
            if not self.is_available():
                return False, "Scrcpy not available"
            
            # Check if already running
            with self._lock:
                if device_serial in self.processes:
                    return False, f"Scrcpy already running for {device_serial}"
            
            # Build command
            cmd = [str(self.scrcpy_path), "-s", device_serial]
            
            if local_port > 0:
                cmd.extend(["--local-port", str(local_port)])
            
            cmd.extend([
                "--max-size", str(max_size),
                "--max-fps", str(max_fps),
                "--bit-rate", bit_rate,
                "--always-on-top"
            ])
            
            # Start process
            logger_module.log_scrcpy_command(" ".join(cmd), __name__)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process info
            with self._lock:
                self.processes[device_serial] = {
                    "process": process,
                    "status": ScrcpyStatus.RUNNING,
                    "start_time": time.time(),
                    "port": local_port,
                    "command": cmd
                }
            
            log.info(f"Scrcpy started for {device_serial}")
            return True, f"Scrcpy started on port {local_port}"
        
        except Exception as e:
            log.error(f"Failed to start scrcpy: {e}")
            return False, str(e)
    
    def stop_mirror(self, device_serial: str) -> Tuple[bool, str]:
        """
        Dừng screen mirroring.
        
        Args:
            device_serial: Device serial
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            with self._lock:
                if device_serial not in self.processes:
                    return False, f"Scrcpy not running for {device_serial}"
                
                process_info = self.processes[device_serial]
                process = process_info["process"]
                
                # Terminate process
                process.terminate()
                
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                
                del self.processes[device_serial]
            
            log.info(f"Scrcpy stopped for {device_serial}")
            return True, "Scrcpy stopped"
        
        except Exception as e:
            log.error(f"Failed to stop scrcpy: {e}")
            return False, str(e)
    
    def is_running(self, device_serial: str) -> bool:
        """Kiểm tra scrcpy có running không."""
        with self._lock:
            if device_serial not in self.processes:
                return False
            
            process_info = self.processes[device_serial]
            process = process_info["process"]
            return process.poll() is None
    
    def get_process_info(self, device_serial: str) -> Optional[dict]:
        """Lấy thông tin process."""
        with self._lock:
            return self.processes.get(device_serial)
    
    def get_all_running(self) -> List[str]:
        """Lấy danh sách tất cả running devices."""
        with self._lock:
            return list(self.processes.keys())
    
    def stop_all(self) -> int:
        """Dừng tất cả running scrcpy processes."""
        with self._lock:
            serials = list(self.processes.keys())
        
        stopped_count = 0
        for serial in serials:
            success, _ = self.stop_mirror(serial)
            if success:
                stopped_count += 1
        
        return stopped_count
    
    def start_recording(self, device_serial: str, output_path: str) -> Tuple[bool, str]:
        """
        Bắt đầu ghi màn hình.
        
        Args:
            device_serial: Device serial
            output_path: Output video path
            
        Returns:
            Tuple[bool, str]: (success, message/error)
        """
        try:
            if not self.is_available():
                return False, "Scrcpy not available"
            
            # Build command with recording
            cmd = [str(self.scrcpy_path), "-s", device_serial]
            cmd.extend(["--record", output_path])
            cmd.extend(["--always-on-top"])
            
            logger_module.log_scrcpy_command(" ".join(cmd), __name__)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            log.info(f"Recording started for {device_serial}: {output_path}")
            return True, f"Recording to {output_path}"
        
        except Exception as e:
            log.error(f"Failed to start recording: {e}")
            return False, str(e)


# ====================================================================
# GLOBAL INSTANCE
# ====================================================================

_scrcpy_manager = None

def get_scrcpy_manager() -> ScrcpyManager:
    """Lấy ScrcpyManager instance (singleton)."""
    global _scrcpy_manager
    if _scrcpy_manager is None:
        _scrcpy_manager = ScrcpyManager()
    return _scrcpy_manager


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - Scrcpy Manager Test")
    print("="*70 + "\n")
    
    try:
        scrcpy_mgr = get_scrcpy_manager()
        
        print(f"Scrcpy available: {scrcpy_mgr.is_available()}")
        if scrcpy_mgr.is_available():
            print(f"Scrcpy path: {scrcpy_mgr.scrcpy_path}")
        
        print("\n" + "="*70)
        print("✓ Scrcpy Manager tests completed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
