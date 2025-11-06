"""
Workspace management system for MarkItDown GUI.

This module provides workspace management with state persistence
and multiple concurrent conversions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

from gui.core.state import ConversionState, ConversionStatus

logger = logging.getLogger(__name__)


class WorkspaceStatus(Enum):
    """Status of a workspace."""

    IDLE = "idle"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class WorkspaceState:
    """
    State of a single workspace.
    
    Each workspace maintains its own state including:
    - Conversion history
    - Current conversion
    - UI state
    - Custom settings
    """

    workspace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled"
    color: str = "#1f538d"  # Default blue
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # Conversion state
    current_conversion: Optional[ConversionState] = None
    conversion_history: List[ConversionState] = field(default_factory=list)
    
    # UI state
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    result_text: Optional[str] = None
    
    # Status
    status: WorkspaceStatus = WorkspaceStatus.IDLE
    error_message: Optional[str] = None
    
    # Custom settings
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert workspace state to dictionary."""
        data = asdict(self)
        # Convert datetime to string
        data["created_at"] = self.created_at.isoformat()
        data["last_modified"] = self.last_modified.isoformat()
        # Convert ConversionState
        if self.current_conversion:
            data["current_conversion"] = self._conversion_to_dict(self.current_conversion)
        data["conversion_history"] = [
            self._conversion_to_dict(c) for c in self.conversion_history
        ]
        return data

    def _conversion_to_dict(self, conversion: ConversionState) -> Dict[str, Any]:
        """Convert ConversionState to dictionary."""
        return {
            "input_file": str(conversion.input_file) if conversion.input_file else None,
            "output_file": str(conversion.output_file) if conversion.output_file else None,
            "status": conversion.status.value,
            "progress": conversion.progress,
            "error_message": conversion.error_message,
            "result_text": conversion.result_text,
            "start_time": conversion.start_time,
            "end_time": conversion.end_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceState":
        """Create workspace state from dictionary."""
        # Convert datetime strings
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        last_modified = datetime.fromisoformat(data.get("last_modified", datetime.now().isoformat()))
        
        # Convert ConversionState
        current_conversion = None
        if data.get("current_conversion"):
            current_conversion = cls._conversion_from_dict(data["current_conversion"])
        
        conversion_history = [
            cls._conversion_from_dict(c) for c in data.get("conversion_history", [])
        ]

        return cls(
            workspace_id=data.get("workspace_id", str(uuid.uuid4())),
            name=data.get("name", "Untitled"),
            color=data.get("color", "#1f538d"),
            created_at=created_at,
            last_modified=last_modified,
            current_conversion=current_conversion,
            conversion_history=conversion_history,
            input_file=data.get("input_file"),
            output_file=data.get("output_file"),
            result_text=data.get("result_text"),
            status=WorkspaceStatus(data.get("status", "idle")),
            error_message=data.get("error_message"),
            settings=data.get("settings", {}),
        )

    @classmethod
    def _conversion_from_dict(cls, data: Dict[str, Any]) -> ConversionState:
        """Create ConversionState from dictionary."""
        return ConversionState(
            input_file=Path(data["input_file"]) if data.get("input_file") else None,
            output_file=Path(data["output_file"]) if data.get("output_file") else None,
            status=ConversionStatus(data.get("status", "idle")),
            progress=data.get("progress", 0.0),
            error_message=data.get("error_message"),
            result_text=data.get("result_text"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
        )

    def update_status(self) -> None:
        """Update workspace status based on current conversion."""
        if self.current_conversion:
            if self.current_conversion.is_active:
                self.status = WorkspaceStatus.PROCESSING
            elif self.current_conversion.is_complete:
                self.status = WorkspaceStatus.SUCCESS
            elif self.current_conversion.has_error:
                self.status = WorkspaceStatus.ERROR
            else:
                self.status = WorkspaceStatus.IDLE
        else:
            self.status = WorkspaceStatus.IDLE
        
        self.last_modified = datetime.now()


class WorkspaceManager:
    """
    Manages multiple workspaces with persistence.
    
    Provides functionality for:
    - Creating/removing workspaces
    - Saving/loading workspace states
    - Managing workspace order
    - Workspace comparison
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """
        Initialize workspace manager.
        
        Args:
            storage_path: Path to store workspace states (defaults to user config)
        """
        if storage_path is None:
            import os
            if os.name == "nt":  # Windows
                storage_path = Path.home() / "AppData" / "Local" / "MarkItDown" / "workspaces"
            else:  # Linux/Mac
                storage_path = Path.home() / ".config" / "markitdown" / "workspaces"
            storage_path.mkdir(parents=True, exist_ok=True)

        self.storage_path = storage_path
        self.workspaces: Dict[str, WorkspaceState] = {}
        self.workspace_order: List[str] = []
        self.active_workspace_id: Optional[str] = None

        # Load saved workspaces
        self.load_all()

    def create_workspace(
        self,
        name: Optional[str] = None,
        color: Optional[str] = None
    ) -> WorkspaceState:
        """
        Create a new workspace.
        
        Args:
            name: Workspace name (auto-generated if None)
            color: Workspace color (default if None)
            
        Returns:
            Created workspace state
        """
        if name is None:
            name = f"Workspace {len(self.workspaces) + 1}"

        workspace = WorkspaceState(
            name=name,
            color=color or "#1f538d"
        )

        self.workspaces[workspace.workspace_id] = workspace
        self.workspace_order.append(workspace.workspace_id)
        self.active_workspace_id = workspace.workspace_id

        logger.info(f"Created workspace: {workspace.name} ({workspace.workspace_id})")
        return workspace

    def remove_workspace(self, workspace_id: str) -> bool:
        """
        Remove a workspace.
        
        Args:
            workspace_id: ID of workspace to remove
            
        Returns:
            True if removed, False if not found
        """
        if workspace_id not in self.workspaces:
            return False

        # Remove from order
        if workspace_id in self.workspace_order:
            self.workspace_order.remove(workspace_id)

        # Delete saved state
        workspace_file = self.storage_path / f"{workspace_id}.json"
        if workspace_file.exists():
            workspace_file.unlink()

        # Remove from memory
        del self.workspaces[workspace_id]

        # Update active workspace
        if self.active_workspace_id == workspace_id:
            if self.workspace_order:
                self.active_workspace_id = self.workspace_order[0]
            else:
                self.active_workspace_id = None

        logger.info(f"Removed workspace: {workspace_id}")
        return True

    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceState]:
        """
        Get workspace by ID.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            Workspace state or None
        """
        return self.workspaces.get(workspace_id)

    def get_active_workspace(self) -> Optional[WorkspaceState]:
        """
        Get active workspace.
        
        Returns:
            Active workspace state or None
        """
        if self.active_workspace_id:
            return self.workspaces.get(self.active_workspace_id)
        return None

    def set_active_workspace(self, workspace_id: str) -> bool:
        """
        Set active workspace.
        
        Args:
            workspace_id: Workspace ID to activate
            
        Returns:
            True if set, False if not found
        """
        if workspace_id in self.workspaces:
            self.active_workspace_id = workspace_id
            return True
        return False

    def reorder_workspaces(self, new_order: List[str]) -> None:
        """
        Reorder workspaces.
        
        Args:
            new_order: List of workspace IDs in new order
        """
        # Validate all IDs exist
        valid_ids = [wid for wid in new_order if wid in self.workspaces]
        # Add any missing IDs
        for wid in self.workspace_order:
            if wid not in valid_ids:
                valid_ids.append(wid)
        
        self.workspace_order = valid_ids
        logger.info("Workspaces reordered")

    def save_workspace(self, workspace_id: str) -> bool:
        """
        Save workspace state to disk.
        
        Args:
            workspace_id: Workspace ID to save
            
        Returns:
            True if saved, False if not found
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        workspace.update_status()
        workspace_file = self.storage_path / f"{workspace_id}.json"

        try:
            with open(workspace_file, "w", encoding="utf-8") as f:
                json.dump(workspace.to_dict(), f, indent=2)
            logger.debug(f"Saved workspace: {workspace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save workspace {workspace_id}: {e}")
            return False

    def load_workspace(self, workspace_id: str) -> Optional[WorkspaceState]:
        """
        Load workspace state from disk.
        
        Args:
            workspace_id: Workspace ID to load
            
        Returns:
            Workspace state or None
        """
        workspace_file = self.storage_path / f"{workspace_id}.json"
        if not workspace_file.exists():
            return None

        try:
            with open(workspace_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            workspace = WorkspaceState.from_dict(data)
            self.workspaces[workspace_id] = workspace
            logger.debug(f"Loaded workspace: {workspace_id}")
            return workspace
        except Exception as e:
            logger.error(f"Failed to load workspace {workspace_id}: {e}")
            return None

    def save_all(self) -> None:
        """Save all workspaces to disk."""
        for workspace_id in self.workspaces:
            self.save_workspace(workspace_id)
        
        # Save order
        order_file = self.storage_path / "order.json"
        try:
            with open(order_file, "w", encoding="utf-8") as f:
                json.dump({
                    "workspace_order": self.workspace_order,
                    "active_workspace_id": self.active_workspace_id,
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workspace order: {e}")

    def load_all(self) -> None:
        """Load all workspaces from disk."""
        if not self.storage_path.exists():
            return

        # Load order
        order_file = self.storage_path / "order.json"
        if order_file.exists():
            try:
                with open(order_file, "r", encoding="utf-8") as f:
                    order_data = json.load(f)
                self.workspace_order = order_data.get("workspace_order", [])
                self.active_workspace_id = order_data.get("active_workspace_id")
            except Exception as e:
                logger.error(f"Failed to load workspace order: {e}")

        # Load all workspace files
        for workspace_file in self.storage_path.glob("*.json"):
            if workspace_file.name == "order.json":
                continue
            
            workspace_id = workspace_file.stem
            self.load_workspace(workspace_id)
            
            # Add to order if not present
            if workspace_id not in self.workspace_order:
                self.workspace_order.append(workspace_id)

        # Ensure at least one workspace exists
        if not self.workspaces:
            self.create_workspace()

    def get_workspaces_in_order(self) -> List[WorkspaceState]:
        """
        Get all workspaces in current order.
        
        Returns:
            List of workspace states in order
        """
        workspaces = []
        for workspace_id in self.workspace_order:
            if workspace_id in self.workspaces:
                workspaces.append(self.workspaces[workspace_id])
        return workspaces

    def update_workspace(
        self,
        workspace_id: str,
        **kwargs: Any
    ) -> bool:
        """
        Update workspace properties.
        
        Args:
            workspace_id: Workspace ID
            **kwargs: Properties to update (name, color, etc.)
            
        Returns:
            True if updated, False if not found
        """
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return False

        for key, value in kwargs.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)
        
        workspace.last_modified = datetime.now()
        self.save_workspace(workspace_id)
        return True

