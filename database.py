"""
Database Module - LX Tool Ultimate

Quản lý SQLite database cho ứng dụng.

Tính năng:
- Connection pooling
- Query logging
- Transaction management
- Schema initialization
- Backup/Restore
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from threading import Lock
import json

import config
import logger as logger_module


# ====================================================================
# LOGGER
# ====================================================================

log = logger_module.get_logger(__name__)


# ====================================================================
# DATABASE CONNECTION
# ====================================================================

class Database:
    """Quản lý SQLite database."""
    
    def __init__(self):
        """Khởi tạo Database."""
        self.db_path = config.DATABASE_PATH
        self.lock = Lock()
        self._ensure_db_exists()
        self._initialize_schema()
    
    def _ensure_db_exists(self):
        """Đảm bảo database file tồn tại."""
        try:
            # Tạo parent directory nếu chưa tồn tại
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Nếu file không tồn tại, tạo nó
            if not self.db_path.exists():
                conn = sqlite3.connect(str(self.db_path))
                conn.close()
                log.info(f"Database created: {self.db_path}")
            
        except Exception as e:
            log.error(f"Failed to ensure database exists: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager để lấy database connection.
        
        Tự động close connection khi xong.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Trả về Row objects thay vì tuples
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            log.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _initialize_schema(self):
        """Khởi tạo schema nếu chưa tồn tại."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if tables already exist
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                
                if not tables:
                    log.info("Initializing database schema...")
                    self._create_tables(cursor)
                    conn.commit()
                    log.info("Database schema initialized")
        
        except Exception as e:
            log.error(f"Failed to initialize schema: {e}")
            raise
    
    def _create_tables(self, cursor):
        """Tạo các bảng trong database."""
        
        # Devices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial TEXT UNIQUE NOT NULL,
                name TEXT,
                model TEXT,
                android_version TEXT,
                status TEXT DEFAULT 'disconnected',
                ip_address TEXT,
                adb_port INTEGER DEFAULT 5037,
                scrcpy_port INTEGER,
                last_seen TIMESTAMP,
                connected_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                device_serial TEXT NOT NULL,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                config JSON,
                result JSON,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_serial) REFERENCES devices(serial)
            )
        """)
        
        # APK packages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apk_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_name TEXT UNIQUE NOT NULL,
                name TEXT,
                version TEXT,
                version_code INTEGER,
                file_path TEXT,
                file_size INTEGER,
                md5_hash TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Installation logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS installation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                device_serial TEXT NOT NULL,
                package_name TEXT NOT NULL,
                status TEXT,
                duration_ms INTEGER,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id),
                FOREIGN KEY (device_serial) REFERENCES devices(serial),
                FOREIGN KEY (package_name) REFERENCES apk_packages(package_name)
            )
        """)
        
        # Screenshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT UNIQUE NOT NULL,
                file_path TEXT,
                device_serial TEXT,
                task_id TEXT,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                format TEXT,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_serial) REFERENCES devices(serial),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                data_type TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Logs table (application logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT,
                module TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        log.info("All tables created successfully")
    
    def execute_query(self, query, params=None):
        """
        Thực hiện SELECT query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            list: Query results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        
        except Exception as e:
            logger_module.log_database_error(f"Query failed: {e}", __name__)
            raise
    
    def execute_update(self, query, params=None):
        """
        Thực hiện INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            int: Số rows affected
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.rowcount
        
        except Exception as e:
            logger_module.log_database_error(f"Update failed: {e}", __name__)
            raise
    
    def execute_many(self, query, params_list):
        """
        Thực hiện INSERT/UPDATE/DELETE nhiều rows.
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
            
        Returns:
            int: Số rows affected
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                return cursor.rowcount
        
        except Exception as e:
            logger_module.log_database_error(f"Batch update failed: {e}", __name__)
            raise
    
    def backup(self):
        """
        Tạo backup của database.
        
        Returns:
            Path: Đường dẫn file backup
        """
        try:
            backup_dir = config.BACKUP_DIR
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"database_backup_{timestamp}.db"
            
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(str(backup_path))
                conn.backup(backup_conn)
                backup_conn.close()
            
            log.info(f"Database backed up to: {backup_path}")
            return backup_path
        
        except Exception as e:
            log.error(f"Backup failed: {e}")
            raise


# ====================================================================
# DEVICE OPERATIONS
# ====================================================================

def add_device(serial, name=None, model=None, android_version=None):
    """Thêm device vào database."""
    query = """
        INSERT INTO devices (serial, name, model, android_version, status)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        db = Database()
        db.execute_update(query, (serial, name, model, android_version, "connected"))
        log.info(f"Device added: {serial}")
    except Exception as e:
        log.error(f"Failed to add device: {e}")
        raise


def get_device(serial):
    """Lấy thông tin device."""
    query = "SELECT * FROM devices WHERE serial = ?"
    try:
        db = Database()
        result = db.execute_query(query, (serial,))
        return result[0] if result else None
    except Exception as e:
        log.error(f"Failed to get device: {e}")
        raise


def get_all_devices():
    """Lấy tất cả devices."""
    query = "SELECT * FROM devices"
    try:
        db = Database()
        return db.execute_query(query)
    except Exception as e:
        log.error(f"Failed to get devices: {e}")
        raise


def update_device_status(serial, status):
    """Cập nhật trạng thái device."""
    query = "UPDATE devices SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE serial = ?"
    try:
        db = Database()
        db.execute_update(query, (status, serial))
        log.info(f"Device status updated: {serial} -> {status}")
    except Exception as e:
        log.error(f"Failed to update device status: {e}")
        raise


def remove_device(serial):
    """Xoá device từ database."""
    query = "DELETE FROM devices WHERE serial = ?"
    try:
        db = Database()
        db.execute_update(query, (serial,))
        log.info(f"Device removed: {serial}")
    except Exception as e:
        log.error(f"Failed to remove device: {e}")
        raise


# ====================================================================
# TASK OPERATIONS
# ====================================================================

def create_task(task_id, device_serial, task_type, config_data=None, priority=0):
    """Tạo task mới."""
    query = """
        INSERT INTO tasks (task_id, device_serial, task_type, config, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        db = Database()
        config_json = json.dumps(config_data) if config_data else None
        db.execute_update(query, (task_id, device_serial, task_type, config_json, priority, "pending"))
        log.info(f"Task created: {task_id}")
    except Exception as e:
        log.error(f"Failed to create task: {e}")
        raise


def get_task(task_id):
    """Lấy thông tin task."""
    query = "SELECT * FROM tasks WHERE task_id = ?"
    try:
        db = Database()
        result = db.execute_query(query, (task_id,))
        return result[0] if result else None
    except Exception as e:
        log.error(f"Failed to get task: {e}")
        raise


def update_task_status(task_id, status):
    """Cập nhật trạng thái task."""
    query = "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE task_id = ?"
    try:
        db = Database()
        db.execute_update(query, (status, task_id))
        log.info(f"Task status updated: {task_id} -> {status}")
    except Exception as e:
        log.error(f"Failed to update task status: {e}")
        raise


def complete_task(task_id, result_data=None, error_message=None):
    """Hoàn thành task."""
    query = """
        UPDATE tasks 
        SET status = ?, result = ?, error_message = ?, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE task_id = ?
    """
    try:
        db = Database()
        result_json = json.dumps(result_data) if result_data else None
        status = "completed" if not error_message else "failed"
        db.execute_update(query, (status, result_json, error_message, task_id))
        log.info(f"Task completed: {task_id}")
    except Exception as e:
        log.error(f"Failed to complete task: {e}")
        raise


# ====================================================================
# APK OPERATIONS
# ====================================================================

def add_apk(package_name, name, version, file_path, md5_hash=None):
    """Thêm APK package vào database."""
    query = """
        INSERT INTO apk_packages (package_name, name, version, file_path, md5_hash)
        VALUES (?, ?, ?, ?, ?)
    """
    try:
        db = Database()
        db.execute_update(query, (package_name, name, version, file_path, md5_hash))
        log.info(f"APK added: {package_name}")
    except Exception as e:
        log.error(f"Failed to add APK: {e}")
        raise


def get_apk(package_name):
    """Lấy thông tin APK."""
    query = "SELECT * FROM apk_packages WHERE package_name = ?"
    try:
        db = Database()
        result = db.execute_query(query, (package_name,))
        return result[0] if result else None
    except Exception as e:
        log.error(f"Failed to get APK: {e}")
        raise


def get_all_apks():
    """Lấy tất cả APK packages."""
    query = "SELECT * FROM apk_packages ORDER BY uploaded_at DESC"
    try:
        db = Database()
        return db.execute_query(query)
    except Exception as e:
        log.error(f"Failed to get APKs: {e}")
        raise


# ====================================================================
# SCREENSHOT OPERATIONS
# ====================================================================

def save_screenshot(file_name, file_path, device_serial, task_id=None, width=None, height=None):
    """Lưu thông tin screenshot vào database."""
    query = """
        INSERT INTO screenshots (file_name, file_path, device_serial, task_id, width, height, format)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        db = Database()
        format_type = file_path.split('.')[-1].lower() if '.' in file_path else "png"
        db.execute_update(query, (file_name, file_path, device_serial, task_id, width, height, format_type))
        log.info(f"Screenshot saved: {file_name}")
    except Exception as e:
        log.error(f"Failed to save screenshot: {e}")
        raise


def get_screenshots_by_device(device_serial, limit=50):
    """Lấy screenshots của device."""
    query = """
        SELECT * FROM screenshots 
        WHERE device_serial = ? 
        ORDER BY captured_at DESC 
        LIMIT ?
    """
    try:
        db = Database()
        return db.execute_query(query, (device_serial, limit))
    except Exception as e:
        log.error(f"Failed to get screenshots: {e}")
        raise


# ====================================================================
# SETTINGS OPERATIONS
# ====================================================================

def set_setting(key, value, data_type="string", description=None):
    """Lưu setting."""
    query = """
        INSERT OR REPLACE INTO settings (key, value, data_type, description)
        VALUES (?, ?, ?, ?)
    """
    try:
        db = Database()
        db.execute_update(query, (key, str(value), data_type, description))
    except Exception as e:
        log.error(f"Failed to set setting: {e}")
        raise


def get_setting(key):
    """Lấy setting."""
    query = "SELECT value FROM settings WHERE key = ?"
    try:
        db = Database()
        result = db.execute_query(query, (key,))
        return result[0][0] if result else None
    except Exception as e:
        log.error(f"Failed to get setting: {e}")
        raise


# ====================================================================
# INITIALIZATION
# ====================================================================

def initialize_database():
    """Khởi tạo database."""
    try:
        db = Database()
        log.info("Database initialized successfully")
        return db
    except Exception as e:
        log.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - Database Test")
    print("="*70 + "\n")
    
    try:
        db = initialize_database()
        
        # Test device operations
        print("Testing device operations...")
        add_device("emulator-5554", "Emulator", "Google Pixel 4", "12")
        device = get_device("emulator-5554")
        print(f"✓ Device added: {device}")
        
        # Test task operations
        print("\nTesting task operations...")
        create_task("task-001", "emulator-5554", "install_apk", {"package": "com.example"})
        task = get_task("task-001")
        print(f"✓ Task created: {task}")
        
        # Backup
        print("\nCreating backup...")
        backup_path = db.backup()
        print(f"✓ Backup created: {backup_path}")
        
        print("\n" + "="*70)
        print("✓ Database tests completed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
