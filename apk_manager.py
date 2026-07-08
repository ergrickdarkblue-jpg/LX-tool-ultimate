"""
APK Manager Module - LX Tool Ultimate

Quản lý APK files và installations.

Tính năng:
- APK upload/download
- Package management
- Signature verification
- Installation tracking
- APK analysis
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import config
import logger as logger_module
import database as db_module


# ====================================================================
# LOGGER
# ====================================================================

log = logger_module.get_logger(__name__)


# ====================================================================
# APK MANAGER CLASS
# ====================================================================

class APKManager:
    """Quản lý APK files."""
    
    def __init__(self):
        """Khởi tạo APKManager."""
        self.apk_dir = config.APK_DIR
        self.apk_dir.mkdir(parents=True, exist_ok=True)
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Tính MD5 hash của file."""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def upload_apk(self, file_path: str, package_name: str, name: str, version: str) -> Tuple[bool, str]:
        """
        Upload APK file.
        
        Args:
            file_path: Path to APK file
            package_name: Package name
            name: App name
            version: App version
            
        Returns:
            Tuple[bool, str]: (success, message/path)
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return False, f"File not found: {file_path}"
            
            if not source_path.suffix.lower() == ".apk":
                return False, "File is not an APK"
            
            # Save APK
            filename = f"{package_name}_{version}.apk"
            dest_path = self.apk_dir / filename
            
            with open(source_path, "rb") as src:
                with open(dest_path, "wb") as dst:
                    dst.write(src.read())
            
            # Calculate MD5
            md5_hash = self._calculate_md5(dest_path)
            file_size = dest_path.stat().st_size
            
            # Save to database
            db_module.add_apk(package_name, name, version, str(dest_path), md5_hash)
            
            log.info(f"APK uploaded: {package_name} v{version}")
            return True, str(dest_path)
        
        except Exception as e:
            log.error(f"Failed to upload APK: {e}")
            return False, str(e)
    
    def get_apk(self, package_name: str) -> Optional[Dict]:
        """
        Lấy thông tin APK.
        
        Args:
            package_name: Package name
            
        Returns:
            Dict: APK information
        """
        try:
            result = db_module.get_apk(package_name)
            if result:
                return dict(result)
            return None
        except Exception as e:
            log.error(f"Failed to get APK: {e}")
            return None
    
    def get_all_apks(self) -> List[Dict]:
        """Lấy tất cả APK packages."""
        try:
            results = db_module.get_all_apks()
            return [dict(row) for row in results]
        except Exception as e:
            log.error(f"Failed to get APKs: {e}")
            return []
    
    def delete_apk(self, package_name: str) -> bool:
        """
        Xoá APK.
        
        Args:
            package_name: Package name
            
        Returns:
            bool: Success status
        """
        try:
            apk_info = self.get_apk(package_name)
            if not apk_info:
                return False
            
            # Delete file
            file_path = Path(apk_info["file_path"])
            if file_path.exists():
                file_path.unlink()
                log.info(f"APK file deleted: {file_path}")
            
            # Delete from database (implement in database module)
            # db_module.delete_apk(package_name)
            
            return True
        
        except Exception as e:
            log.error(f"Failed to delete APK: {e}")
            return False
    
    def verify_apk_integrity(self, package_name: str) -> Tuple[bool, str]:
        """
        Kiểm tra tính toàn vẹn của APK.
        
        Args:
            package_name: Package name
            
        Returns:
            Tuple[bool, str]: (valid, message)
        """
        try:
            apk_info = self.get_apk(package_name)
            if not apk_info:
                return False, "APK not found"
            
            file_path = Path(apk_info["file_path"])
            if not file_path.exists():
                return False, "APK file not found"
            
            # Verify MD5
            current_md5 = self._calculate_md5(file_path)
            stored_md5 = apk_info.get("md5_hash", "")
            
            if current_md5 == stored_md5:
                return True, "APK integrity verified"
            else:
                return False, f"MD5 mismatch: {current_md5} != {stored_md5}"
        
        except Exception as e:
            log.error(f"Failed to verify APK: {e}")
            return False, str(e)
    
    def get_apk_size(self, package_name: str) -> int:
        """
        Lấy kích thước APK.
        
        Args:
            package_name: Package name
            
        Returns:
            int: File size in bytes
        """
        try:
            apk_info = self.get_apk(package_name)
            if not apk_info:
                return 0
            
            file_path = Path(apk_info["file_path"])
            return file_path.stat().st_size if file_path.exists() else 0
        
        except Exception as e:
            log.error(f"Failed to get APK size: {e}")
            return 0
    
    def cleanup_old_apks(self, keep_latest: int = 5) -> int:
        """
        Cleanup old APK versions, keep latest.
        
        Args:
            keep_latest: Number of latest versions to keep
            
        Returns:
            int: Number of deleted APKs
        """
        try:
            # Group APKs by package
            all_apks = self.get_all_apks()
            packages = {}
            
            for apk in all_apks:
                pkg = apk["package_name"]
                if pkg not in packages:
                    packages[pkg] = []
                packages[pkg].append(apk)
            
            # Delete old versions
            deleted_count = 0
            for pkg, apk_list in packages.items():
                # Sort by uploaded_at desc
                sorted_apks = sorted(apk_list, key=lambda x: x.get("uploaded_at", ""), reverse=True)
                
                # Delete old versions
                for apk in sorted_apks[keep_latest:]:
                    if self.delete_apk(pkg):
                        deleted_count += 1
            
            log.info(f"Cleanup completed: {deleted_count} old APKs deleted")
            return deleted_count
        
        except Exception as e:
            log.error(f"Cleanup failed: {e}")
            return 0


# ====================================================================
# GLOBAL INSTANCE
# ====================================================================

_apk_manager = None

def get_apk_manager() -> APKManager:
    """Lấy APKManager instance (singleton)."""
    global _apk_manager
    if _apk_manager is None:
        _apk_manager = APKManager()
    return _apk_manager


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LX TOOL ULTIMATE - APK Manager Test")
    print("="*70 + "\n")
    
    try:
        apk_mgr = get_apk_manager()
        
        print("APK Manager initialized successfully!")
        print(f"APK Directory: {apk_mgr.apk_dir}")
        
        # Get all APKs
        apks = apk_mgr.get_all_apks()
        print(f"\nTotal APKs stored: {len(apks)}")
        
        print("\n" + "="*70)
        print("✓ APK Manager tests completed!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"✗ Error: {e}")
