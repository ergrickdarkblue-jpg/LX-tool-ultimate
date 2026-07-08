"""
Setup Project Script for LX Tool Ultimate

Tự động tạo toàn bộ cấu trúc thư mục và file cần thiết cho dự án.
Chạy: python setup_project.py
"""

import os
import sys
from pathlib import Path


def create_directory_structure():
    """Tạo toàn bộ cấu trúc thư mục cho dự án."""
    
    # Danh sách các thư mục cần tạo
    directories = [
        "config",
        "database",
        "logs",
        "backups",
        "cache",
        "exports",
        "imports",
        "uploads",
        "screenshots",
        "temp",
        "plugins",
        "scrcpy",
        "platform-tools",
        "templates",
        "static",
        "static/css",
        "static/js",
        "static/img",
        "static/icons",
    ]
    
    # Tạo tất cả thư mục
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Tạo thư mục: {directory}")
    
    print("\n" + "="*60)
    print("✓ Toàn bộ cấu trúc thư mục đã được tạo thành công!")
    print("="*60)


def create_placeholder_files():
    """Tạo các file placeholder để giữ thư mục trong git."""
    
    placeholder_dirs = [
        "config",
        "database",
        "logs",
        "backups",
        "cache",
        "exports",
        "imports",
        "uploads",
        "screenshots",
        "temp",
        "plugins",
        "scrcpy",
        "platform-tools",
    ]
    
    for directory in placeholder_dirs:
        gitkeep_path = Path(directory) / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        print(f"✓ Tạo placeholder: {directory}/.gitkeep")
    
    print("\n" + "="*60)
    print("✓ Toàn bộ placeholder file đã được tạo!")
    print("="*60)


def print_structure():
    """Hiển thị cấu trúc dự án đã tạo."""
    
    print("\n" + "="*60)
    print("CẤU TRÚC DỰ ÁN LX_TOOL_ULTIMATE")
    print("="*60)
    
    structure = """
LX_TOOL_ULTIMATE/
├── app.py                    (Flask app main)
├── config.py                 (Config & paths)
├── database.py               (SQLite service)
├── logger.py                 (Logging service)
├── adb_manager.py            (ADB commands)
├── device_manager.py         (Device management)
├── apk_manager.py            (APK operations)
├── scrcpy_manager.py         (scrcpy control)
├── task_manager.py           (Task scheduling)
├── websocket_manager.py      (Real-time updates)
├── settings_manager.py       (Settings management)
├── utils.py                  (Utility functions)
├── setup_project.py          (This file)
├── requirements.txt          (Python dependencies)
├── README.md                 (Documentation)
├── run.bat                   (Windows launcher)
├── install.bat               (Windows installer)
├── Caddyfile                 (Caddy configuration)
│
├── config/                   (Configuration files)
├── database/                 (SQLite database)
├── logs/                     (Application logs)
├── backups/                  (Database backups)
├── cache/                    (Cache files)
├── exports/                  (Export files)
├── imports/                  (Import files)
├── uploads/                  (Uploaded files)
├── screenshots/              (Device screenshots)
├── temp/                     (Temporary files)
├── plugins/                  (Plugin system)
├── scrcpy/                   (scrcpy binary)
├── platform-tools/           (ADB binary)
│
├── templates/                (HTML templates)
│   ├── base.html
│   ├── dashboard.html
│   ├── devices.html
│   ├── tasks.html
│   ├── settings.html
│   └── ...
│
├── static/                   (Static assets)
│   ├── css/
│   │   ├── style.css
│   │   ├── dark-mode.css
│   │   └── bootstrap.min.css
│   ├── js/
│   │   ├── app.js
│   │   ├── websocket.js
│   │   ├── device-manager.js
│   │   └── bootstrap.bundle.min.js
│   ├── img/
│   └── icons/
    """
    
    print(structure)


def main():
    """Main function."""
    
    print("\n" + "="*60)
    print("LX TOOL ULTIMATE - Project Setup Script")
    print("="*60)
    print("\nBắt đầu tạo cấu trúc dự án...")
    print()
    
    try:
        # Tạo cấu trúc thư mục
        create_directory_structure()
        
        # Tạo placeholder files
        print()
        create_placeholder_files()
        
        # Hiển thị cấu trúc
        print_structure()
        
        print("\n" + "="*60)
        print("✓ Setup hoàn tất!")
        print("="*60)
        print("\nBước tiếp theo:")
        print("1. Chạy: pip install -r requirements.txt")
        print("2. Đặt adb.exe vào: platform-tools/")
        print("3. Đặt scrcpy.exe vào: scrcpy/")
        print("4. Chạy: python app.py")
        print("\n")
        
    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
