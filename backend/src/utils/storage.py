"""
Storage utilities for Biped Platform
Handles file operations with persistent /data volume
"""

import logging
import os
import shutil
from datetime import datetime
from typing import List, Optional

from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage operations using the /data volume"""

    def __init__(self, data_dir: str = None):
        # Use environment variable or fallback to /data, then to local directory
        if data_dir is None:
            data_dir = os.environ.get("DATA_DIR", "/data")

        # Check if we can access the data directory, fallback to local if not
        try:
            os.makedirs(data_dir, exist_ok=True)
            # Test write access
            test_file = os.path.join(data_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self.data_dir = data_dir
        except (PermissionError, OSError):
            # Fallback to local directory for development
            fallback_dir = os.path.join(os.getcwd(), "data")
            logger.warning(f"Cannot access {data_dir}, falling back to {fallback_dir}")
            self.data_dir = fallback_dir

        self.uploads_dir = os.path.join(self.data_dir, "uploads")
        self.logs_dir = os.path.join(self.data_dir, "logs")
        self.backups_dir = os.path.join(self.data_dir, "backups")

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.data_dir,
            self.uploads_dir,
            self.logs_dir,
            self.backups_dir,
            os.path.join(self.uploads_dir, "images"),
            os.path.join(self.uploads_dir, "documents"),
            os.path.join(self.uploads_dir, "portfolios"),
            os.path.join(self.uploads_dir, "profiles"),
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")

    def save_uploaded_file(self, file, category: str = "general") -> Optional[str]:
        """
        Save an uploaded file to the appropriate directory

        Args:
            file: Werkzeug FileStorage object
            category: Category for organizing files (images, documents, etc.)

        Returns:
            Relative path to saved file or None if failed
        """
        if not file or not file.filename:
            return None

        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            return None

        # Add timestamp to prevent conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"

        # Determine save directory
        category_dir = os.path.join(self.uploads_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        # Save file
        file_path = os.path.join(category_dir, filename)
        try:
            file.save(file_path)
            logger.info(f"File saved: {file_path}")

            # Return relative path from uploads directory
            return os.path.join(category, filename)
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {str(e)}")
            return None

    def get_file_path(self, relative_path: str) -> str:
        """Get absolute path for a file given its relative path"""
        return os.path.join(self.uploads_dir, relative_path)

    def delete_file(self, relative_path: str) -> bool:
        """Delete a file given its relative path"""
        try:
            file_path = self.get_file_path(relative_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {relative_path}: {str(e)}")
            return False

    def list_files(self, category: str = None) -> List[str]:
        """List files in a category or all files"""
        try:
            if category:
                category_dir = os.path.join(self.uploads_dir, category)
                if not os.path.exists(category_dir):
                    return []
                files = []
                for file in os.listdir(category_dir):
                    if os.path.isfile(os.path.join(category_dir, file)):
                        files.append(os.path.join(category, file))
                return files
            else:
                # List all files recursively
                files = []
                for root, dirs, filenames in os.walk(self.uploads_dir):
                    for filename in filenames:
                        rel_path = os.path.relpath(os.path.join(root, filename), self.uploads_dir)
                        files.append(rel_path)
                return files
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []

    def backup_database(self, db_path: str) -> Optional[str]:
        """Create a backup of the database"""
        try:
            if not os.path.exists(db_path):
                logger.warning(f"Database file not found: {db_path}")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"biped_backup_{timestamp}.db"
            backup_path = os.path.join(self.backups_dir, backup_filename)

            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup database: {str(e)}")
            return None

    def get_storage_info(self) -> dict:
        """Get storage usage information"""
        try:
            total_size = 0
            file_count = 0

            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1

            return {
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_count": file_count,
                "data_dir": self.data_dir,
                "directories": {
                    "uploads": (
                        len(os.listdir(self.uploads_dir)) if os.path.exists(self.uploads_dir) else 0
                    ),
                    "logs": len(os.listdir(self.logs_dir)) if os.path.exists(self.logs_dir) else 0,
                    "backups": (
                        len(os.listdir(self.backups_dir)) if os.path.exists(self.backups_dir) else 0
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get storage info: {str(e)}")
            return {"error": str(e)}


# Global storage manager instance
storage_manager = StorageManager()
