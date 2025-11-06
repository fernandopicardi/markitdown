"""
GitHub Wiki exporter for MarkItDown GUI.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import uuid

try:
    from git import Repo, GitCommandError
    HAS_GIT = True
except ImportError:
    HAS_GIT = False

from gui.core.exporters import (
    AbstractExporter,
    ExportPlatform,
    ExportResult,
    ExportStatus,
)

logger = logging.getLogger(__name__)


class GitHubWikiExporter(AbstractExporter):
    """GitHub Wiki exporter."""

    def __init__(self) -> None:
        """Initialize GitHub Wiki exporter."""
        super().__init__(ExportPlatform.GITHUB_WIKI)
        self.repo: Optional[Repo] = None
        self.wiki_path: Optional[Path] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with GitHub Wiki."""
        if not HAS_GIT:
            logger.error("GitPython not available")
            return False

        try:
            wiki_path = Path(credentials.get("wiki_path", ""))
            if not wiki_path or not wiki_path.exists():
                return False

            # Clone or open wiki repository
            if not (wiki_path / ".git").exists():
                # Clone wiki
                repo_url = credentials.get("wiki_url", "")
                if repo_url:
                    Repo.clone_from(repo_url, wiki_path)
                else:
                    # Initialize new repo
                    repo = Repo.init(wiki_path)
                    # Set up remote if provided
                    remote_url = credentials.get("remote_url", "")
                    if remote_url:
                        repo.create_remote("origin", remote_url)

            self.repo = Repo(wiki_path)
            self.wiki_path = wiki_path
            self.authenticated = True
            logger.info("GitHub Wiki authenticated")
            return True

        except Exception as e:
            logger.error(f"GitHub Wiki authentication error: {e}")
            return False

    def export(
        self,
        markdown_text: str,
        metadata: Dict[str, Any],
        destination: Optional[str] = None
    ) -> ExportResult:
        """Export to GitHub Wiki."""
        if not self.repo or not self.wiki_path:
            return ExportResult(
                export_id="",
                platform=ExportPlatform.GITHUB_WIKI,
                status=ExportStatus.FAILED,
                error="Not authenticated"
            )

        try:
            mapped_meta = self._extract_metadata(metadata)
            filename = destination or mapped_meta.get("title", "Untitled").replace(" ", "-") + ".md"

            # Write file
            file_path = self.wiki_path / filename
            file_path.write_text(markdown_text, encoding="utf-8")

            # Commit
            self.repo.index.add([str(file_path)])
            commit_message = metadata.get("commit_message", f"Add/update {filename}")
            self.repo.index.commit(commit_message)

            # Push if remote exists
            try:
                origin = self.repo.remotes.origin
                origin.push()
            except Exception as e:
                logger.warning(f"Failed to push to remote: {e}")

            # Generate URL (GitHub wiki URL format)
            repo_url = metadata.get("repo_url", "")
            wiki_url = f"{repo_url}/wiki/{filename}" if repo_url else None

            return ExportResult(
                export_id=str(uuid.uuid4()),
                platform=ExportPlatform.GITHUB_WIKI,
                status=ExportStatus.COMPLETED,
                exported_id=filename,
                exported_url=wiki_url,
                metadata={"filename": filename, "file_path": str(file_path)}
            )

        except GitCommandError as e:
            logger.error(f"GitHub Wiki export error: {e}")
            return ExportResult(
                export_id="",
                platform=ExportPlatform.GITHUB_WIKI,
                status=ExportStatus.FAILED,
                error=str(e)
            )

    def get_export_url(self, export_id: str) -> Optional[str]:
        """Get URL for exported content."""
        # URL is constructed from repo URL and filename
        return None

