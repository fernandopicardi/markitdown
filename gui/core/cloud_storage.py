"""
Cloud storage integration system for MarkItDown GUI.

This module provides unified interface for cloud storage services:
Google Drive, Dropbox, OneDrive, and AWS S3.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import threading
import queue

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Cloud storage providers."""

    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    ONEDRIVE = "onedrive"
    AWS_S3 = "aws_s3"


class SyncStatus(Enum):
    """Synchronization status."""

    SYNCED = "synced"
    PENDING = "pending"
    SYNCING = "syncing"
    ERROR = "error"
    CONFLICT = "conflict"


@dataclass
class CloudFile:
    """Represents a file in cloud storage."""

    file_id: str
    name: str
    path: str
    size: int
    modified_time: datetime
    is_folder: bool = False
    mime_type: Optional[str] = None
    provider: CloudProvider = CloudProvider.GOOGLE_DRIVE
    parent_id: Optional[str] = None
    download_url: Optional[str] = None
    share_url: Optional[str] = None


@dataclass
class SyncTask:
    """Synchronization task."""

    task_id: str
    file_id: str
    operation: str  # upload, download, delete
    provider: CloudProvider = CloudProvider.GOOGLE_DRIVE
    local_path: Optional[Path] = None
    cloud_path: Optional[str] = None
    status: SyncStatus = SyncStatus.PENDING
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers."""

    def __init__(self, provider: CloudProvider) -> None:
        """
        Initialize cloud storage provider.
        
        Args:
            provider: Cloud provider type
        """
        self.provider = provider
        self.authenticated = False
        self.credentials: Dict[str, Any] = {}
        self.cache_dir: Optional[Path] = None

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with cloud service.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authenticated successfully
        """
        pass

    @abstractmethod
    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """
        List files in folder.
        
        Args:
            folder_id: Folder ID (None for root)
            
        Returns:
            List of cloud files
        """
        pass

    @abstractmethod
    def download_file(self, file_id: str, local_path: Path) -> bool:
        """
        Download file from cloud.
        
        Args:
            file_id: File ID in cloud
            local_path: Local path to save
            
        Returns:
            True if downloaded successfully
        """
        pass

    @abstractmethod
    def upload_file(self, local_path: Path, cloud_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Upload file to cloud.
        
        Args:
            local_path: Local file path
            cloud_path: Cloud file path/name
            folder_id: Target folder ID (None for root)
            
        Returns:
            Cloud file ID or None
        """
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from cloud.
        
        Args:
            file_id: File ID to delete
            
        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def get_share_link(self, file_id: str) -> Optional[str]:
        """
        Get shareable link for file.
        
        Args:
            file_id: File ID
            
        Returns:
            Shareable URL or None
        """
        pass

    @abstractmethod
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Create folder in cloud.
        
        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            
        Returns:
            Created folder ID or None
        """
        pass


class CloudStorageManager:
    """Manages multiple cloud storage providers."""

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize cloud storage manager.
        
        Args:
            cache_dir: Directory for local cache
        """
        if cache_dir is None:
            import os
            if os.name == "nt":  # Windows
                cache_dir = Path.home() / "AppData" / "Local" / "MarkItDown" / "cloud_cache"
            else:  # Linux/Mac
                cache_dir = Path.home() / ".cache" / "markitdown" / "cloud"
            cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_dir = cache_dir
        self.providers: Dict[CloudProvider, CloudStorageProvider] = {}
        self.sync_queue: queue.Queue = queue.Queue()
        self.sync_tasks: Dict[str, SyncTask] = {}
        self.offline_mode = False
        self.sync_thread: Optional[threading.Thread] = None
        self.running = False

    def register_provider(self, provider: CloudStorageProvider) -> None:
        """
        Register a cloud storage provider.
        
        Args:
            provider: Provider instance
        """
        provider.cache_dir = self.cache_dir
        self.providers[provider.provider] = provider
        logger.info(f"Registered cloud provider: {provider.provider.value}")

    def get_provider(self, provider: CloudProvider) -> Optional[CloudStorageProvider]:
        """
        Get provider by type.
        
        Args:
            provider: Provider type
            
        Returns:
            Provider instance or None
        """
        return self.providers.get(provider)

    def authenticate_provider(self, provider: CloudProvider, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with provider.
        
        Args:
            provider: Provider type
            credentials: Authentication credentials
            
        Returns:
            True if authenticated successfully
        """
        prov = self.get_provider(provider)
        if not prov:
            return False

        return prov.authenticate(credentials)

    def list_files(self, provider: CloudProvider, folder_id: Optional[str] = None) -> List[CloudFile]:
        """
        List files from provider.
        
        Args:
            provider: Provider type
            folder_id: Folder ID (None for root)
            
        Returns:
            List of cloud files
        """
        prov = self.get_provider(provider)
        if not prov:
            return []

        return prov.list_files(folder_id)

    def download_file(self, provider: CloudProvider, file_id: str, local_path: Path) -> bool:
        """
        Download file from provider.
        
        Args:
            provider: Provider type
            file_id: File ID
            local_path: Local save path
            
        Returns:
            True if downloaded successfully
        """
        prov = self.get_provider(provider)
        if not prov:
            return False

        return prov.download_file(file_id, local_path)

    def upload_file(
        self,
        provider: CloudProvider,
        local_path: Path,
        cloud_path: str,
        folder_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload file to provider.
        
        Args:
            provider: Provider type
            local_path: Local file path
            cloud_path: Cloud file path
            folder_id: Target folder ID
            
        Returns:
            Cloud file ID or None
        """
        prov = self.get_provider(provider)
        if not prov:
            return None

        return prov.upload_file(local_path, cloud_path, folder_id)

    def queue_sync_task(self, task: SyncTask) -> None:
        """
        Queue synchronization task.
        
        Args:
            task: Sync task to queue
        """
        self.sync_tasks[task.task_id] = task
        if self.offline_mode:
            self.sync_queue.put(task)
        else:
            # Execute immediately
            self._execute_sync_task(task)

    def _execute_sync_task(self, task: SyncTask) -> None:
        """Execute synchronization task."""
        task.status = SyncStatus.SYNCING
        try:
            provider = task.provider
            
            if task.operation == "download":
                if task.local_path:
                    success = self.download_file(provider, task.file_id, task.local_path)
                    task.status = SyncStatus.SYNCED if success else SyncStatus.ERROR
            elif task.operation == "upload":
                if task.local_path:
                    file_id = self.upload_file(provider, task.local_path, task.cloud_path or task.local_path.name)
                    task.status = SyncStatus.SYNCED if file_id else SyncStatus.ERROR
            elif task.operation == "delete":
                prov = self.get_provider(provider)
                if prov:
                    success = prov.delete_file(task.file_id)
                    task.status = SyncStatus.SYNCED if success else SyncStatus.ERROR

        except Exception as e:
            task.status = SyncStatus.ERROR
            task.error = str(e)
            logger.error(f"Error executing sync task: {e}")

    def start_sync_worker(self) -> None:
        """Start background sync worker."""
        if self.running:
            return

        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()

    def _sync_worker(self) -> None:
        """Background sync worker."""
        while self.running:
            try:
                task = self.sync_queue.get(timeout=1.0)
                self._execute_sync_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")

    def stop_sync_worker(self) -> None:
        """Stop background sync worker."""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)

    def get_sync_status(self, file_id: str) -> Optional[SyncStatus]:
        """
        Get sync status for file.
        
        Args:
            file_id: File ID
            
        Returns:
            Sync status or None
        """
        for task in self.sync_tasks.values():
            if task.file_id == file_id:
                return task.status
        return None

    def resolve_conflict(
        self,
        file_id: str,
        resolution: str,  # "local", "cloud", "merge"
        local_path: Optional[Path] = None
    ) -> bool:
        """
        Resolve sync conflict.
        
        Args:
            file_id: File ID with conflict
            resolution: Resolution strategy
            local_path: Local file path (if needed)
            
        Returns:
            True if resolved successfully
        """
        task = self.sync_tasks.get(file_id)
        if not task or task.status != SyncStatus.CONFLICT:
            return False

        try:
            provider = task.provider
            
            if resolution == "local":
                # Use local version, upload to cloud
                if local_path:
                    self.upload_file(provider, local_path, task.cloud_path or local_path.name)
            elif resolution == "cloud":
                # Use cloud version, download to local
                if local_path:
                    self.download_file(provider, file_id, local_path)
            # merge would require more complex logic

            task.status = SyncStatus.SYNCED
            return True
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return False

