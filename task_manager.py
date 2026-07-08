"""
Task Manager Module - LX Tool Ultimate

Quản lý tasks và job scheduling.

Tính năng:
- Task creation and management
- Job scheduling
- Task status tracking
- Batch task execution
- Result aggregation
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from enum import Enum
from queue import Queue

import config
import logger as logger_module
import database as db_module


# ====================================================================
# LOGGER
# ====================================================================

log = logger_module.get_logger(__name__)


# ====================================================================
# ENUMS
# ====================================================================

class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Task types."""
    INSTALL_APK = "install_apk"
    UNINSTALL_APK = "uninstall_apk"
    TAKE_SCREENSHOT = "take_screenshot"
    RUN_TEST = "run_test"
    CUSTOM = "custom"


# ====================================================================
# TASK CLASS
# ====================================================================

class Task:
    """Represents a task."""
    
    def __init__(self, task_type: str, device_serial: str, config: Dict = None):
        """
        Khởi tạo Task.
        
        Args:
            task_type: Task type
            device_serial: Device serial
            config: Task configuration
        """
        self.id = str(uuid.uuid4())
        self.type = task_type
        self.device_serial = device_serial
        self.config = config or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.progress = 0
        self._lock = threading.Lock()
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        with self._lock:
            return {
                "id": self.id,
                "type": self.type,
                "device_serial": self.device_serial,
                "status": self.status.value,
                "config": self.config,
                "result": self.result,
                "error": self.error,
                "progress": self.progress,
                "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            }


# ====================================================================
# TASK MANAGER CLASS
# ====================================================================

class TaskManager:
    """Quản lý tasks."""
    
    def __init__(self, max_workers: int = 5):
        """
        Khởi tạo TaskManager.
        
        Args:
            max_workers: Maximum concurrent workers
        """
        self.tasks: Dict[str, Task] = {}
        self.max_workers = max_workers
        self._lock = threading.Lock()
        self._queue = Queue()
        self._workers = []
        self._is_running = False
        self._callbacks = {
            "on_task_started": [],
            "on_task_completed": [],
            "on_task_failed": [],
            "on_task_progress": [],
        }
    
    def register_callback(self, event: str, callback: Callable):
        """Đăng ký callback cho sự kiện."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
            log.info(f"Task callback registered: {event}")
    
    def _emit_event(self, event: str, data: Dict):
        """Emit event."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    log.error(f"Callback error: {e}")
    
    def start(self):
        """Bắt đầu task manager."""
        if self._is_running:
            log.warning("TaskManager already running")
            return
        
        self._is_running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)
        
        log.info(f"TaskManager started with {self.max_workers} workers")
    
    def stop(self):
        """Dừng task manager."""
        self._is_running = False
        for worker in self._workers:
            worker.join(timeout=5)
        log.info("TaskManager stopped")
    
    def _worker_loop(self):
        """Worker loop."""
        while self._is_running:
            try:
                # Get task from queue
                task = self._queue.get(timeout=1)
                if task is None:
                    break
                
                self._execute_task(task)
            except:
                pass
    
    def create_task(self, task_type: str, device_serial: str, config: Dict = None) -> Task:
        """
        Tạo task mới.
        
        Args:
            task_type: Task type
            device_serial: Device serial
            config: Task configuration
            
        Returns:
            Task: Created task
        """
        task = Task(task_type, device_serial, config)
        
        with self._lock:
            self.tasks[task.id] = task
        
        # Save to database
        try:
            db_module.create_task(task.id, device_serial, task_type, config)
        except Exception as e:
            log.error(f"Failed to save task to database: {e}")
        
        log.info(f"Task created: {task.id}")
        return task
    
    def queue_task(self, task: Task):
        """Thêm task vào queue."""
        self._queue.put(task)
        log.info(f"Task queued: {task.id}")
    
    def _execute_task(self, task: Task):
        """Thực hiện task."""
        try:
            with task._lock:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
            
            # Update database
            db_module.update_task_status(task.id, TaskStatus.RUNNING.value)
            
            # Emit event
            self._emit_event("on_task_started", task.to_dict())
            
            # Execute based on type
            if task.type == TaskType.INSTALL_APK.value:
                self._execute_install_apk(task)
            elif task.type == TaskType.UNINSTALL_APK.value:
                self._execute_uninstall_apk(task)
            elif task.type == TaskType.TAKE_SCREENSHOT.value:
                self._execute_take_screenshot(task)
            else:
                raise ValueError(f"Unknown task type: {task.type}")
            
            # Mark as completed
            with task._lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
            
            db_module.complete_task(task.id, task.result)
            self._emit_event("on_task_completed", task.to_dict())
            log.info(f"Task completed: {task.id}")
        
        except Exception as e:
            with task._lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
            
            db_module.complete_task(task.id, error_message=str(e))
            self._emit_event("on_task_failed", task.to_dict())
            log.error(f"Task failed: {task.id} - {e}")
    
    def _execute_install_apk(self, task: Task):
        """Thực hiện install APK task."""
        from device_manager import get_device_manager
        
        dm = get_device_manager()
        apk_path = task.config.get("apk_path")
        force = task.config.get("force", False)
        
        success = dm.install_apk_on_device(task.device_serial, apk_path, force=force)
        task.result = {"success": success}
    
    def _execute_uninstall_apk(self, task: Task):
        """Thực hiện uninstall APK task."""
        from device_manager import get_device_manager
        
        dm = get_device_manager()
        package_name = task.config.get("package_name")
        
        success = dm.uninstall_package_on_device(task.device_serial, package_name)
        task.result = {"success": success}
    
    def _execute_take_screenshot(self, task: Task):
        """Thực hiện take screenshot task."""
        from device_manager import get_device_manager
        
        dm = get_device_manager()
        save_path = task.config.get("save_path")
        
        success = dm.take_screenshot(task.device_serial, save_path)
        task.result = {"success": success, "path": save_path if success else None}
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Lấy task by ID."""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Lấy tất cả tasks."""
        with self._lock:
            return list(self.tasks.values())
    
    def get_tasks_by_device(self, device_serial: str) -> List[Task]:
        """Lấy tasks của device."""
        with self._lock:
            return [t for t in self.tasks.values() if t.device_serial == device_serial]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Lấy tasks by status."""
        with self._lock:
            return [t for t in self.tasks.values() if t.status == status]
    
    def cancel_task(self, task_id: str) -> bool:
        """Hủy task."""
        task = self.get_task(task_id)
        if not task:
            return False
        
        with task._lock:
            if task.status == TaskStatus.PENDING or task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                return True
        
        return False


# ====================================================================
# GLOBAL INSTANCE
# ====================================================================

_task_manager = None

def get_task_manager() -> TaskManager:
    """Lấy TaskManager instance (singleton)."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - Task Manager Test")
    print("="*70 + "\n")
    
    try:
        tm = get_task_manager()
        tm.start()
        
        # Create test task
        print("Creating test task...")
        task = tm.create_task(
            TaskType.INSTALL_APK.value,
            "emulator-5554",
            {"apk_path": "/path/to/app.apk"}
        )
        print(f"✓ Task created: {task.id}")
        
        # Queue task
        tm.queue_task(task)
        print(f"✓ Task queued")
        
        # Wait a bit
        import time
        time.sleep(2)
        
        # Get task
        retrieved = tm.get_task(task.id)
        print(f"✓ Task retrieved: {retrieved.status.value}")
        
        tm.stop()
        
        print("\n" + "="*70)
        print("✓ Task Manager tests completed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
