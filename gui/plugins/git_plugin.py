"""
Git Integration Plugin for MarkItDown GUI.

This plugin provides Git integration for version control of conversions.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

try:
    from git import Repo, GitCommandError
    HAS_GIT = True
except ImportError:
    HAS_GIT = False

from gui.core.plugin_system import (
    AbstractPlugin,
    PluginMetadata,
    PluginType,
    PluginStatus,
)

logger = logging.getLogger(__name__)

PLUGIN_METADATA = PluginMetadata(
    plugin_id="git_integration",
    name="Git Integration",
    version="1.0.0",
    description="Git integration for version control of converted documents",
    author="MarkItDown Team",
    plugin_type=PluginType.INTEGRATION,
    dependencies=[],
    config_schema={
        "auto_commit": {"type": "boolean", "default": False},
        "commit_message_template": {"type": "string", "default": "Convert: {file}"},
        "branch": {"type": "string", "default": "main"},
    },
    permissions=["file_write", "git_operations"],
)


class GitPlugin(AbstractPlugin):
    """Git integration plugin."""

    def __init__(self, plugin_id: str, metadata: PluginMetadata) -> None:
        """Initialize Git plugin."""
        super().__init__(plugin_id, metadata)
        self.git_available = HAS_GIT
        self.repos: Dict[str, Repo] = {}

    def init(self, context: Dict[str, Any]) -> None:
        """Initialize plugin."""
        if not self.git_available:
            self.logger.warning("GitPython not available")
        else:
            self.logger.info("Git plugin initialized")

    def activate(self) -> None:
        """Activate plugin."""
        if not self.git_available:
            raise RuntimeError("GitPython not available")

        self.status = PluginStatus.ACTIVATED
        self.logger.info("Git plugin activated")

    def deactivate(self) -> None:
        """Deactivate plugin."""
        self.repos.clear()
        self.status = PluginStatus.DEACTIVATED
        self.logger.info("Git plugin deactivated")

    def get_repo(self, path: Path) -> Optional[Repo]:
        """
        Get or initialize Git repository.
        
        Args:
            path: Path to repository
            
        Returns:
            Git repository or None
        """
        if not self.git_available:
            return None

        path_str = str(path.resolve())
        if path_str in self.repos:
            return self.repos[path_str]

        try:
            # Try to open existing repo
            repo = Repo(path)
            self.repos[path_str] = repo
            return repo
        except Exception:
            # Try to initialize new repo
            try:
                repo = Repo.init(path)
                self.repos[path_str] = repo
                self.logger.info(f"Initialized Git repo at {path}")
                return repo
            except Exception as e:
                self.logger.error(f"Failed to initialize Git repo: {e}")
                return None

    def commit_conversion(
        self,
        file_path: Path,
        markdown_path: Path,
        message: Optional[str] = None
    ) -> bool:
        """
        Commit conversion to Git.
        
        Args:
            file_path: Original file path
            markdown_path: Converted Markdown path
            message: Commit message (uses template if None)
            
        Returns:
            True if committed successfully
        """
        if not self.git_available:
            return False

        repo = self.get_repo(markdown_path.parent)
        if not repo:
            return False

        try:
            # Add files
            repo.index.add([str(markdown_path)])

            # Create commit message
            if not message:
                template = self.config.get("commit_message_template", "Convert: {file}")
                message = template.format(file=file_path.name)

            # Commit
            repo.index.commit(message)
            self.logger.info(f"Committed conversion: {message}")
            return True

        except GitCommandError as e:
            self.logger.error(f"Git error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error committing: {e}")
            return False

    def get_conversion_history(self, markdown_path: Path) -> list:
        """
        Get conversion history from Git.
        
        Args:
            markdown_path: Path to Markdown file
            
        Returns:
            List of commits
        """
        if not self.git_available:
            return []

        repo = self.get_repo(markdown_path.parent)
        if not repo:
            return []

        try:
            commits = list(repo.iter_commits(paths=str(markdown_path)))
            return [
                {
                    "hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "date": datetime.fromtimestamp(commit.committed_date).isoformat(),
                }
                for commit in commits
            ]
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return []

