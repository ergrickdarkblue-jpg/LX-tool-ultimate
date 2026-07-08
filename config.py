"""
Config Module - LX Tool Ultimate

Quản lý toàn bộ đường dẫn, cài đặt và constants cho dự án.
Tất cả module khác sẽ import từ đây để lấy đường dẫn.

Quy tắc:
- Không hardcode đường dẫn ở bất cứ nơi nào
- Mọi module phải import config và sử dụng các hằng số từ đây
- Tự động tạo toàn bộ thư mục khi khởi động
"""

import os
import sys
from pathlib import Path
from datetime import datetime


# ====================================================================
# BASE DIRECTORIES
# ====================================================================

# Lấy thư mục gốc của dự án (nơi chứa app.py)
BASE_DIR = Path(__file__).resolve().parent

# Tất cả các đường dẫn phải là Path object, không phải string
# để tương thích với cả Windows và Unix


# ====================================================================
# PROJECT DIRECTORIES
# ====================================================================

CONFIG_DIR = BASE_DIR / "config"
DATABASE_DIR = BASE_DIR / "database"
LOG_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"
CACHE_DIR = BASE_DIR / "cache"
EXPORT_DIR = BASE_DIR / "exports"
IMPORT_DIR = BASE_DIR / "imports"
UPLOAD_DIR = BASE_DIR / "uploads"
SCREENSHOT_DIR = BASE_DIR / "screenshots"
TEMP_DIR = BASE_DIR / "temp"
PLUGIN_DIR = BASE_DIR / "plugins"
SCRCPY_DIR = BASE_DIR / "scrcpy"
ADB_DIR = BASE_DIR / "platform-tools"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"


# ====================================================================
# FILE PATHS
# ====================================================================

DATABASE_FILE = DATABASE_DIR / "lx_tool.db"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
LOG_FILE_PATTERN = LOG_DIR / "{date}.log"  # {date} sẽ được thay thế


# ====================================================================
# ADB CONFIGURATION
# ====================================================================

# Ưu tiên: platform-tools/adb.exe
# Nếu không có, tìm trong PATH
# Nếu vẫn không có, báo lỗi
ADB_EXECUTABLE = ADB_DIR / "adb.exe" if sys.platform == "win32" else ADB_DIR / "adb"

# Timeout cho ADB commands (giây)
ADB_COMMAND_TIMEOUT = 30

# Timeout cho ADB connection (giây)
ADB_CONNECTION_TIMEOUT = 10

# Retry count khi ADB command thất bại
ADB_RETRY_COUNT = 3

# Delay giữa các retry (giây)
ADB_RETRY_DELAY = 1


# ====================================================================
# SCRCPY CONFIGURATION
# ====================================================================

# Ưu tiên: scrcpy/scrcpy.exe
# Nếu không có, tìm trong PATH
# Nếu vẫn không có, hiển thị cảnh báo nhưng không crash
SCRCPY_EXECUTABLE = SCRCPY_DIR / "scrcpy.exe" if sys.platform == "win32" else SCRCPY_DIR / "scrcpy"

# Port cho scrcpy (sẽ tự increment nếu có nhiều device)
SCRCPY_PORT_BASE = 5000

# Video codec
SCRCPY_VIDEO_CODEC = "h264"

# Audio codec
SCRCPY_AUDIO_CODEC = "aac"


# ====================================================================
# DATABASE CONFIGURATION
# ====================================================================

# SQLite timeout (giây)
DB_TIMEOUT = 30

# Enable WAL mode (Write-Ahead Logging) để tăng performance
DB_ENABLE_WAL = True

# Journal mode
DB_JOURNAL_MODE = "wal"

# Synchronous mode (0=off, 1=normal, 2=full, 3=extra)
DB_SYNCHRONOUS = 1

# Cache size (pages, -1 = tính bằng KB)
DB_CACHE_SIZE = -64000


# ====================================================================
# LOGGING CONFIGURATION
# ====================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# Format của log message
LOG_FORMAT = "%(asctime)s | %(name)-15s | %(levelname)-8s | %(message)s"

# Date format trong log
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Max log file size (bytes) trước khi rotate
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB

# Số file log backup giữ lại
LOG_BACKUP_COUNT = 10

# Enable console logging
LOG_ENABLE_CONSOLE = True

# Enable file logging
LOG_ENABLE_FILE = True


# ====================================================================
# FLASK CONFIGURATION
# ====================================================================

# Flask debug mode
FLASK_DEBUG = False

# Flask host
FLASK_HOST = "0.0.0.0"

# Flask port
FLASK_PORT = 5000

# Flask secret key (PHẢI thay đổi trong production)
FLASK_SECRET_KEY = "lx-tool-ultimate-dev-key-change-in-production"

# Max upload file size (bytes)
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB


# ====================================================================
# WEBSOCKET CONFIGURATION
# ====================================================================

# WebSocket namespace
WEBSOCKET_NAMESPACE = "/ws"

# Heartbeat interval (giây)
WEBSOCKET_HEARTBEAT = 25

# Enable CORS cho WebSocket
WEBSOCKET_CORS_ALLOWED_ORIGINS = "*"


# ====================================================================
# DEVICE CONFIGURATION
# ====================================================================

# Interval để refresh device list (giây)
DEVICE_REFRESH_INTERVAL = 5

# Timeout khi lấy device properties (giây)
DEVICE_PROPERTY_TIMEOUT = 10

# Max concurrent ADB operations
MAX_CONCURRENT_OPERATIONS = 10


# ====================================================================
# TASK CONFIGURATION
# ====================================================================

# Task timeout mặc định (giây)
TASK_DEFAULT_TIMEOUT = 300

# Max task per device
MAX_TASKS_PER_DEVICE = 100

# Task cleanup interval (giây)
TASK_CLEANUP_INTERVAL = 3600

# Task history retention (ngày)
TASK_HISTORY_RETENTION_DAYS = 30


# ====================================================================
# SCREENSHOT CONFIGURATION
# ====================================================================

# Screenshot format: png, jpg
SCREENSHOT_FORMAT = "png"

# Screenshot quality (1-100, chỉ cho JPG)
SCREENSHOT_QUALITY = 90

# Max screenshots per device giữ lại
MAX_SCREENSHOTS_PER_DEVICE = 100


# ====================================================================
# PLUGIN CONFIGURATION
# ====================================================================

# Plugin enabled
PLUGIN_ENABLED = True

# Plugin auto-load
PLUGIN_AUTO_LOAD = True


# ====================================================================
# CADDY CONFIGURATION
# ====================================================================

# Caddy config file
CADDY_CONFIG_FILE = BASE_DIR / "Caddyfile"

# Caddy port (HTTP)
CADDY_HTTP_PORT = 80

# Caddy HTTPS port
CADDY_HTTPS_PORT = 443


# ====================================================================
# API CONFIGURATION
# ====================================================================

# API version
API_VERSION = "v1"

# API base URL
API_BASE_URL = f"/api/{API_VERSION}"

# API rate limit (requests per minute)
API_RATE_LIMIT = 1000


# ====================================================================
# PERFORMANCE CONFIGURATION
# ====================================================================

# Enable caching
ENABLE_CACHE = True

# Cache TTL (seconds)
CACHE_TTL = 300

# Thread pool size cho async operations
THREAD_POOL_SIZE = 10


# ====================================================================
# APPLICATION CONFIGURATION
# ====================================================================

# Application name
APP_NAME = "LX Tool Ultimate"

# Application version
APP_VERSION = "1.0.0"

# Application description
APP_DESCRIPTION = "Professional Phone Farm Management Software for Windows"

# Contact email
CONTACT_EMAIL = "support@lxtool.local"


# ====================================================================
# INITIALIZATION FUNCTION
# ====================================================================

def initialize_directories():
    """
    Tự động tạo toàn bộ thư mục và file cần thiết.
    
    Gọi hàm này khi ứng dụng khởi động để đảm bảo toàn bộ
    cấu trúc thư mục đã tồn tại.
    
    Raises:
        Exception: Nếu không thể tạo thư mục nào
    """
    
    directories_to_create = [
        CONFIG_DIR,
        DATABASE_DIR,
        LOG_DIR,
        BACKUP_DIR,
        CACHE_DIR,
        EXPORT_DIR,
        IMPORT_DIR,
        UPLOAD_DIR,
        SCREENSHOT_DIR,
        TEMP_DIR,
        PLUGIN_DIR,
        SCRCPY_DIR,
        ADB_DIR,
        STATIC_DIR,
        TEMPLATE_DIR,
    ]
    
    for directory in directories_to_create:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise Exception(f"Không thể tạo thư mục {directory}: {e}")


def get_log_file_path(date=None):
    """
    Lấy đường dẫn file log cho một ngày cụ thể.
    
    Args:
        date: datetime object hoặc None (sẽ dùng ngày hôm nay)
        
    Returns:
        Path object cho file log
        
    Example:
        >>> log_file = get_log_file_path()
        >>> log_file = get_log_file_path(datetime(2026, 7, 8))
    """
    
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    return LOG_DIR / f"{date_str}.log"


def validate_executables():
    """
    Kiểm tra xem adb.exe và scrcpy.exe có tồn tại không.
    
    Returns:
        dict: {
            'adb': (exists: bool, path: str or None),
            'scrcpy': (exists: bool, path: str or None)
        }
        
    Note:
        - Nếu không tìm thấy trong thư mục project, sẽ tìm trong PATH
        - Nếu không tìm thấy, sẽ return None
    """
    
    result = {
        "adb": (False, None),
        "scrcpy": (False, None)
    }
    
    # Kiểm tra ADB
    if ADB_EXECUTABLE.exists():
        result["adb"] = (True, str(ADB_EXECUTABLE))
    else:
        # Tìm trong PATH
        adb_in_path = _find_executable_in_path("adb")
        if adb_in_path:
            result["adb"] = (True, adb_in_path)
    
    # Kiểm tra SCRCPY
    if SCRCPY_EXECUTABLE.exists():
        result["scrcpy"] = (True, str(SCRCPY_EXECUTABLE))
    else:
        # Tìm trong PATH
        scrcpy_in_path = _find_executable_in_path("scrcpy")
        if scrcpy_in_path:
            result["scrcpy"] = (True, scrcpy_in_path)
    
    return result


def _find_executable_in_path(executable_name):
    """
    Tìm executable trong PATH.
    
    Args:
        executable_name: Tên của executable (adb, scrcpy, etc)
        
    Returns:
        str: Đường dẫn đầy đủ hoặc None nếu không tìm thấy
    """
    
    # Trên Windows, thêm .exe nếu cần
    if sys.platform == "win32" and not executable_name.endswith(".exe"):
        executable_name += ".exe"
    
    # Dùng 'where' trên Windows, 'which' trên Unix
    if sys.platform == "win32":
        try:
            result = os.popen(f"where {executable_name}").read().strip()
            if result:
                return result
        except:
            pass
    else:
        try:
            result = os.popen(f"which {executable_name}").read().strip()
            if result:
                return result
        except:
            pass
    
    return None


# ====================================================================
# AUTO-INITIALIZATION
# ====================================================================

# Khởi tạo thư mục khi module được import
try:
    initialize_directories()
except Exception as e:
    # Nếu khởi tạo thất bại, log error nhưng không crash
    # Logger chưa được init nên dùng print
    print(f"[CONFIG ERROR] Không thể khởi tạo thư mục: {e}")


if __name__ == "__main__":
    """Hiển thị thông tin config khi chạy trực tiếp."""
    
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - Configuration")
    print("="*70)
    
    print(f"\n📁 BASE DIRECTORIES:")
    print(f"  BASE_DIR:         {BASE_DIR}")
    print(f"  CONFIG_DIR:       {CONFIG_DIR}")
    print(f"  DATABASE_DIR:     {DATABASE_DIR}")
    print(f"  LOG_DIR:          {LOG_DIR}")
    print(f"  SCREENSHOT_DIR:   {SCREENSHOT_DIR}")
    print(f"  UPLOAD_DIR:       {UPLOAD_DIR}")
    
    print(f"\n📄 FILE PATHS:")
    print(f"  DATABASE_FILE:    {DATABASE_FILE}")
    print(f"  SETTINGS_FILE:    {SETTINGS_FILE}")
    print(f"  LOG_FILE_PATTERN: {LOG_FILE_PATTERN}")
    
    print(f"\n🔧 EXECUTABLES:")
    executables = validate_executables()
    adb_exists, adb_path = executables["adb"]
    scrcpy_exists, scrcpy_path = executables["scrcpy"]
    
    print(f"  ADB:              {'✓' if adb_exists else '✗'} {adb_path or 'NOT FOUND'}")
    print(f"  SCRCPY:           {'✓' if scrcpy_exists else '✗'} {scrcpy_path or 'NOT FOUND'}")
    
    print(f"\n⚙️  APPLICATION:")
    print(f"  Name:             {APP_NAME}")
    print(f"  Version:          {APP_VERSION}")
    print(f"  Flask Port:       {FLASK_PORT}")
    
    print(f"\n💾 DATABASE:")
    print(f"  Timeout:          {DB_TIMEOUT}s")
    print(f"  WAL Mode:         {DB_ENABLE_WAL}")
    print(f"  Cache Size:       {DB_CACHE_SIZE} pages")
    
    print(f"\n📊 LOGGING:")
    print(f"  Level:            {LOG_LEVEL}")
    print(f"  Max File Size:    {LOG_MAX_BYTES / (1024*1024):.1f} MB")
    print(f"  Backup Count:     {LOG_BACKUP_COUNT}")
    
    print("\n" + "="*70)
