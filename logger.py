"""
Logger Module - LX Tool Ultimate

Quản lý logging cho toàn bộ ứng dụng.
Tất cả module khác sẽ import từ đây để ghi log.

Tính năng:
- Log theo ngày (2026-07-08.log)
- Console output + File output
- Log rotation (max 10MB, giữ 10 file backup)
- Format chuẩn: timestamp | module | level | message
- Thread-safe
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys

import config


# ====================================================================
# LOGGER INSTANCES
# ====================================================================

# Dictionary để lưu các logger instance
_loggers = {}


# ====================================================================
# INITIALIZE LOGGER
# ====================================================================

def get_logger(name):
    """
    Lấy hoặc tạo logger cho một module cụ thể.
    
    Args:
        name: Tên của logger (thường là __name__)
        
    Returns:
        logging.Logger: Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello world")
    """
    
    # Nếu logger đã tồn tại, trả về nó
    if name in _loggers:
        return _loggers[name]
    
    # Tạo logger mới
    logger = logging.getLogger(name)
    logger.setLevel(config.LOG_LEVEL)
    
    # Nếu logger đã có handlers, không thêm nữa
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Tạo formatter
    formatter = logging.Formatter(
        fmt=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )
    
    # ====================================================
    # Console Handler
    # ====================================================
    
    if config.LOG_ENABLE_CONSOLE:
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(config.LOG_LEVEL)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        except Exception as e:
            print(f"[LOGGER ERROR] Không thể tạo console handler: {e}")
    
    # ====================================================
    # File Handler (Rotation)
    # ====================================================
    
    if config.LOG_ENABLE_FILE:
        try:
            # Đảm bảo log directory tồn tại
            config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            
            # Lấy đường dẫn file log cho hôm nay
            log_file = config.get_log_file_path()
            
            # Sử dụng RotatingFileHandler để tự động rotate
            # khi file vượt quá max_bytes
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=config.LOG_MAX_BYTES,
                backupCount=config.LOG_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setLevel(config.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"[LOGGER ERROR] Không thể tạo file handler: {e}")
    
    # Lưu vào dictionary
    _loggers[name] = logger
    
    return logger


# ====================================================================
# INITIALIZE LOGGING SYSTEM
# ====================================================================

def initialize_logging():
    """
    Khởi tạo toàn bộ logging system.
    
    Gọi hàm này ở đầu ứng dụng (trong app.py)
    
    Returns:
        logging.Logger: Root logger
    """
    
    try:
        # Tạo log directory nếu chưa tồn tại
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Tạo root logger
        root_logger = get_logger("root")
        
        # Log thông báo khởi tạo
        root_logger.info("="*70)
        root_logger.info(f"LX TOOL ULTIMATE - Logging System Initialized")
        root_logger.info(f"Log Level: {config.LOG_LEVEL}")
        root_logger.info(f"Log Directory: {config.LOG_DIR}")
        root_logger.info(f"Log File: {config.get_log_file_path()}")
        root_logger.info("="*70)
        
        return root_logger
        
    except Exception as e:
        print(f"[LOGGER ERROR] Không thể khởi tạo logging system: {e}")
        return None


# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def log_info(message, logger_name="root"):
    """Ghi log INFO."""
    logger = get_logger(logger_name)
    logger.info(message)


def log_warning(message, logger_name="root"):
    """Ghi log WARNING."""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_error(message, logger_name="root", exc_info=False):
    """Ghi log ERROR."""
    logger = get_logger(logger_name)
    logger.error(message, exc_info=exc_info)


def log_critical(message, logger_name="root", exc_info=False):
    """Ghi log CRITICAL."""
    logger = get_logger(logger_name)
    logger.critical(message, exc_info=exc_info)


def log_debug(message, logger_name="root"):
    """Ghi log DEBUG."""
    logger = get_logger(logger_name)
    logger.debug(message)


# ====================================================================
# EXCEPTION LOGGING
# ====================================================================

def log_exception(exception, logger_name="root", message=None):
    """
    Ghi log Exception chi tiết.
    
    Args:
        exception: Exception object
        logger_name: Tên logger
        message: Message tuỳ chọn
    """
    
    logger = get_logger(logger_name)
    
    if message:
        logger.error(message, exc_info=True)
    else:
        logger.error(f"Exception occurred: {type(exception).__name__}", exc_info=True)


# ====================================================================
# PERFORMANCE LOGGING
# ====================================================================

def log_performance(operation_name, duration_ms, logger_name="root"):
    """
    Ghi log performance của một operation.
    
    Args:
        operation_name: Tên operation
        duration_ms: Thời gian thực hiện (milliseconds)
        logger_name: Tên logger
    """
    
    logger = get_logger(logger_name)
    logger.info(f"[PERFORMANCE] {operation_name} took {duration_ms:.2f}ms")


# ====================================================================
# OPERATION LOGGING
# ====================================================================

class OperationLogger:
    """
    Context manager để log toàn bộ một operation.
    
    Tự động log start, success/error, duration.
    
    Example:
        >>> with OperationLogger("Install APK", logger) as op:
        ...     result = install_apk()
        ...     op.set_result(result)
    """
    
    def __init__(self, operation_name, logger_instance=None):
        """
        Khởi tạo OperationLogger.
        
        Args:
            operation_name: Tên operation
            logger_instance: Logger instance (nếu None sẽ dùng root)
        """
        self.operation_name = operation_name
        self.logger = logger_instance or get_logger("root")
        self.start_time = None
        self.result = None
        self.error = None
    
    def __enter__(self):
        """Ghi log start operation."""
        self.start_time = datetime.now()
        self.logger.info(f"[START] {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ghi log end operation."""
        
        duration = (datetime.now() - self.start_time).total_seconds() * 1000
        
        if exc_type is not None:
            self.logger.error(
                f"[FAILED] {self.operation_name} - {exc_type.__name__}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
        else:
            self.logger.info(
                f"[SUCCESS] {self.operation_name} - Duration: {duration:.2f}ms"
            )
        
        return False  # Không suppress exception
    
    def set_result(self, result):
        """Lưu result của operation."""
        self.result = result
    
    def set_error(self, error):
        """Lưu error của operation."""
        self.error = error


# ====================================================================
# DEVICE LOGGING
# ====================================================================

def log_device_connected(device_serial, logger_name="root"):
    """Ghi log device kết nối."""
    logger = get_logger(logger_name)
    logger.info(f"[DEVICE] Connected: {device_serial}")


def log_device_disconnected(device_serial, logger_name="root"):
    """Ghi log device ngắt kết nối."""
    logger = get_logger(logger_name)
    logger.warning(f"[DEVICE] Disconnected: {device_serial}")


def log_device_error(device_serial, error_message, logger_name="root"):
    """Ghi log device error."""
    logger = get_logger(logger_name)
    logger.error(f"[DEVICE ERROR] {device_serial}: {error_message}")


# ====================================================================
# ADB LOGGING
# ====================================================================

def log_adb_command(command, device_serial=None, logger_name="root"):
    """Ghi log ADB command."""
    logger = get_logger(logger_name)
    device_info = f"[{device_serial}] " if device_serial else ""
    logger.debug(f"[ADB COMMAND] {device_info}{command}")


def log_adb_result(device_serial, command, result, logger_name="root"):
    """Ghi log ADB result."""
    logger = get_logger(logger_name)
    logger.debug(f"[ADB RESULT] [{device_serial}] {command}: {result[:100]}")


def log_adb_error(device_serial, command, error, logger_name="root"):
    """Ghi log ADB error."""
    logger = get_logger(logger_name)
    logger.error(f"[ADB ERROR] [{device_serial}] {command}: {error}")


# ====================================================================
# TASK LOGGING
# ====================================================================

def log_task_created(task_id, task_type, device_serial, logger_name="root"):
    """Ghi log task được tạo."""
    logger = get_logger(logger_name)
    logger.info(f"[TASK] Created: {task_id} - Type: {task_type} - Device: {device_serial}")


def log_task_started(task_id, logger_name="root"):
    """Ghi log task bắt đầu."""
    logger = get_logger(logger_name)
    logger.info(f"[TASK] Started: {task_id}")


def log_task_completed(task_id, logger_name="root"):
    """Ghi log task hoàn thành."""
    logger = get_logger(logger_name)
    logger.info(f"[TASK] Completed: {task_id}")


def log_task_failed(task_id, error, logger_name="root"):
    """Ghi log task thất bại."""
    logger = get_logger(logger_name)
    logger.error(f"[TASK] Failed: {task_id} - Error: {error}")


# ====================================================================
# DATABASE LOGGING
# ====================================================================

def log_database_query(query, logger_name="root"):
    """Ghi log database query."""
    logger = get_logger(logger_name)
    logger.debug(f"[DATABASE QUERY] {query[:100]}")


def log_database_error(error, logger_name="root"):
    """Ghi log database error."""
    logger = get_logger(logger_name)
    logger.error(f"[DATABASE ERROR] {error}")


# ====================================================================
# WEBSOCKET LOGGING
# ====================================================================

def log_websocket_connection(client_id, logger_name="root"):
    """Ghi log WebSocket connection."""
    logger = get_logger(logger_name)
    logger.info(f"[WEBSOCKET] Client connected: {client_id}")


def log_websocket_disconnection(client_id, logger_name="root"):
    """Ghi log WebSocket disconnection."""
    logger = get_logger(logger_name)
    logger.info(f"[WEBSOCKET] Client disconnected: {client_id}")


def log_websocket_message(client_id, message_type, logger_name="root"):
    """Ghi log WebSocket message."""
    logger = get_logger(logger_name)
    logger.debug(f"[WEBSOCKET] [{client_id}] Message: {message_type}")


# ====================================================================
# CLEAR OLD LOGS
# ====================================================================

def cleanup_old_logs(days=30):
    """
    Xoá log files cũ hơn N ngày.
    
    Args:
        days: Số ngày (mặc định 30)
    """
    
    logger = get_logger("root")
    
    try:
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        log_files = list(config.LOG_DIR.glob("*.log*"))
        deleted_count = 0
        
        for log_file in log_files:
            # Lấy modification time
            mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            # Nếu file cũ hơn cutoff date, xoá nó
            if mod_time < cutoff_date:
                log_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"[CLEANUP] Deleted {deleted_count} old log files")
        
    except Exception as e:
        logger.error(f"[CLEANUP ERROR] Không thể xoá log files: {e}")


if __name__ == "__main__":
    """Test logger khi chạy trực tiếp."""
    
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - Logger Test")
    print("="*70 + "\n")
    
    # Khởi tạo logging
    root_logger = initialize_logging()
    
    # Test các level log
    root_logger.debug("Đây là DEBUG message")
    root_logger.info("Đây là INFO message")
    root_logger.warning("Đây là WARNING message")
    root_logger.error("Đây là ERROR message")
    
    # Test device logging
    log_device_connected("emulator-5554")
    log_device_disconnected("emulator-5554")
    
    # Test task logging
    log_task_created("task-001", "install_apk", "emulator-5554")
    log_task_started("task-001")
    log_task_completed("task-001")
    
    # Test ADB logging
    log_adb_command("shell getprop ro.build.version.release", "emulator-5554")
    
    # Test OperationLogger
    logger = get_logger(__name__)
    with OperationLogger("Test Operation", logger):
        import time
        time.sleep(0.5)
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception as e:
        log_exception(e, __name__, "Lỗi test")
    
    print("\n" + "="*70)
    print("✓ Logger test hoàn tất!")
    print("="*70 + "\n")
