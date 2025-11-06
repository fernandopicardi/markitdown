"""
AWS S3 integration for MarkItDown GUI.
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from gui.core.cloud_storage import (
    CloudStorageProvider,
    CloudProvider,
    CloudFile,
)

logger = logging.getLogger(__name__)


class AWSS3Provider(CloudStorageProvider):
    """AWS S3 storage provider."""

    def __init__(self) -> None:
        """Initialize AWS S3 provider."""
        super().__init__(CloudProvider.AWS_S3)
        self.s3_client = None
        self.current_bucket: Optional[str] = None

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with AWS S3."""
        if not HAS_BOTO3:
            logger.error("boto3 not available")
            return False

        try:
            access_key = credentials.get("access_key_id")
            secret_key = credentials.get("secret_access_key")
            region = credentials.get("region", "us-east-1")

            if not access_key or not secret_key:
                return False

            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )

            # Verify authentication
            self.s3_client.list_buckets()
            self.authenticated = True
            logger.info("AWS S3 authenticated")
            return True

        except ClientError as e:
            logger.error(f"AWS S3 authentication error: {e}")
            return False

    def list_buckets(self) -> List[str]:
        """
        List available buckets.
        
        Returns:
            List of bucket names
        """
        if not self.s3_client:
            return []

        try:
            response = self.s3_client.list_buckets()
            return [bucket['Name'] for bucket in response.get('Buckets', [])]
        except ClientError as e:
            logger.error(f"Error listing buckets: {e}")
            return []

    def set_bucket(self, bucket_name: str) -> bool:
        """
        Set current bucket.
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            True if bucket exists
        """
        if bucket_name in self.list_buckets():
            self.current_bucket = bucket_name
            return True
        return False

    def list_files(self, folder_id: Optional[str] = None) -> List[CloudFile]:
        """List files in S3 bucket."""
        if not self.s3_client or not self.current_bucket:
            return []

        try:
            prefix = folder_id if folder_id else ""
            response = self.s3_client.list_objects_v2(
                Bucket=self.current_bucket,
                Prefix=prefix
            )

            files = []
            for obj in response.get('Contents', []):
                key = obj['Key']
                # Skip if it's a folder marker
                if key.endswith('/'):
                    continue

                files.append(CloudFile(
                    file_id=key,
                    name=Path(key).name,
                    path=key,
                    size=obj['Size'],
                    modified_time=obj['LastModified'],
                    is_folder=False,
                    provider=CloudProvider.AWS_S3,
                    parent_id=Path(key).parent.as_posix() if '/' in key else None,
                ))

            return files

        except ClientError as e:
            logger.error(f"Error listing S3 files: {e}")
            return []

    def download_file(self, file_id: str, local_path: Path) -> bool:
        """Download file from S3."""
        if not self.s3_client or not self.current_bucket:
            return False

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            self.s3_client.download_file(
                self.current_bucket,
                file_id,
                str(local_path)
            )
            return True

        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            return False

    def upload_file(self, local_path: Path, cloud_path: str, folder_id: Optional[str] = None) -> Optional[str]:
        """Upload file to S3."""
        if not self.s3_client or not self.current_bucket:
            return None

        try:
            key = f"{folder_id}/{cloud_path}" if folder_id else cloud_path
            self.s3_client.upload_file(
                str(local_path),
                self.current_bucket,
                key
            )
            return key

        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """Delete file from S3."""
        if not self.s3_client or not self.current_bucket:
            return False

        try:
            self.s3_client.delete_object(
                Bucket=self.current_bucket,
                Key=file_id
            )
            return True

        except ClientError as e:
            logger.error(f"Error deleting from S3: {e}")
            return False

    def get_share_link(self, file_id: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get presigned URL for file.
        
        Args:
            file_id: File key
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL or None
        """
        if not self.s3_client or not self.current_bucket:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.current_bucket, 'Key': file_id},
                ExpiresIn=expires_in
            )
            return url

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create folder in S3 (folder marker)."""
        if not self.s3_client or not self.current_bucket:
            return None

        try:
            key = f"{parent_id}/{name}/" if parent_id else f"{name}/"
            self.s3_client.put_object(
                Bucket=self.current_bucket,
                Key=key
            )
            return key

        except ClientError as e:
            logger.error(f"Error creating folder: {e}")
            return None

