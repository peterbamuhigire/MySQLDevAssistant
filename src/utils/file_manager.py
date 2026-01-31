"""
File manager for backup and file operations
"""

import shutil
from pathlib import Path
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations including backups."""

    @staticmethod
    def create_backup(source_path: str, backup_dir: str = 'backups',
                     compression: bool = True) -> str:
        """
        Create backup of a file.

        Args:
            source_path: Path to source file
            backup_dir: Backup directory
            compression: Whether to compress backup

        Returns:
            Path to backup file
        """
        source = Path(source_path)

        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"

        if compression:
            backup_name += '.gz'

        backup_file = backup_path / backup_name

        # Copy file
        if compression:
            import gzip
            with open(source, 'rb') as f_in:
                with gzip.open(backup_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(source, backup_file)

        logger.info(f"Created backup: {backup_file}")
        return str(backup_file)

    @staticmethod
    def cleanup_old_backups(backup_dir: str = 'backups', keep_last: int = 5):
        """
        Clean up old backup files, keeping only the most recent ones.

        Args:
            backup_dir: Backup directory
            keep_last: Number of backups to keep
        """
        backup_path = Path(backup_dir)

        if not backup_path.exists():
            return

        # Get all backup files sorted by modification time
        backups = sorted(
            backup_path.glob('*'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove old backups
        for old_backup in backups[keep_last:]:
            old_backup.unlink()
            logger.info(f"Removed old backup: {old_backup}")

    @staticmethod
    def get_backup_list(backup_dir: str = 'backups') -> list:
        """
        Get list of backup files.

        Args:
            backup_dir: Backup directory

        Returns:
            List of backup file paths
        """
        backup_path = Path(backup_dir)

        if not backup_path.exists():
            return []

        return sorted(
            [str(p) for p in backup_path.glob('*')],
            key=lambda p: Path(p).stat().st_mtime,
            reverse=True
        )
