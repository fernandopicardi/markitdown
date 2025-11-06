# Cloud Storage Integration System

## Overview

The MarkItDown GUI features comprehensive cloud storage integration with Google Drive, Dropbox, OneDrive, and AWS S3. The system provides unified interface, offline mode, conflict resolution, and bidirectional synchronization.

## Features

### ✅ Google Drive
- **OAuth2 Authentication**: Secure OAuth2 flow
- **List Files/Folders**: Browse cloud storage
- **Download**: Download files for conversion
- **Upload**: Upload converted Markdown
- **Bidirectional Sync**: Two-way synchronization
- **Share Links**: Generate shareable links

### ✅ Dropbox
- **API Integration**: Dropbox API v2
- **File Operations**: List, download, upload, delete
- **Folder Navigation**: Browse folder structure
- **Share Links**: Create shareable links

### ✅ OneDrive
- **Microsoft Graph API**: OneDrive integration
- **MSAL Authentication**: Microsoft Authentication Library
- **File Management**: Full file operations
- **Share Links**: Generate sharing links

### ✅ AWS S3
- **Bucket Management**: List and select buckets
- **Upload/Download**: File transfer operations
- **Presigned URLs**: Generate temporary access URLs
- **Region Support**: Multiple AWS regions

### ✅ Unified Interface
- **Cloud Explorer**: Unified file browser
- **Drag & Drop**: Between local and cloud
- **Sync Status**: Real-time sync status
- **Credential Management**: Secure credential storage
- **Local Cache**: Cached file metadata

### ✅ Offline Mode
- **Operation Queue**: Queue operations when offline
- **Auto-Sync**: Automatic sync when online
- **Queue Management**: View and manage queued operations
- **Status Tracking**: Track sync status

### ✅ Conflict Resolution
- **Conflict Detection**: Detect sync conflicts
- **Resolution Strategies**: Local, cloud, or merge
- **Conflict UI**: Visual conflict resolution
- **Auto-Resolution**: Configurable auto-resolution

### ✅ Share Links
- **Link Generation**: Generate shareable links
- **Copy to Clipboard**: Easy link sharing
- **Link Types**: View, edit, download links
- **Expiration**: Configurable link expiration (S3)

## Usage

### Basic Setup

```python
from gui.core.cloud_storage import CloudStorageManager, CloudProvider
from gui.integrations.google_drive import GoogleDriveProvider
from gui.views.cloud_window import show_cloud_storage

# Create manager
manager = CloudStorageManager()

# Register providers
manager.register_provider(GoogleDriveProvider())

# Show cloud window
show_cloud_storage()
```

### Google Drive

```python
from gui.integrations.google_drive import GoogleDriveProvider

# Create provider
provider = GoogleDriveProvider()

# Authenticate (OAuth2 flow)
credentials = {
    "client_config": {...}  # OAuth2 client config JSON
}
provider.authenticate(credentials)

# List files
files = provider.list_files()

# Download file
provider.download_file(file_id, Path("local_file.pdf"))

# Upload file
file_id = provider.upload_file(Path("local.md"), "cloud_file.md")
```

### Dropbox

```python
from gui.integrations.dropbox_provider import DropboxProvider

# Create provider
provider = DropboxProvider()

# Authenticate
credentials = {"access_token": "your_token"}
provider.authenticate(credentials)

# Use provider
files = provider.list_files()
```

### OneDrive

```python
from gui.integrations.onedrive_provider import OneDriveProvider

# Create provider
provider = OneDriveProvider()

# Authenticate (MSAL)
credentials = {"client_id": "your_client_id"}
provider.authenticate(credentials)

# Use provider
files = provider.list_files()
```

### AWS S3

```python
from gui.integrations.aws_s3_provider import AWSS3Provider

# Create provider
provider = AWSS3Provider()

# Authenticate
credentials = {
    "access_key_id": "your_key",
    "secret_access_key": "your_secret",
    "region": "us-east-1"
}
provider.authenticate(credentials)

# List buckets
buckets = provider.list_buckets()

# Set bucket
provider.set_bucket("my-bucket")

# Use provider
files = provider.list_files()
```

## Cloud Storage Manager

### Managing Providers

```python
from gui.core.cloud_storage import CloudStorageManager

manager = CloudStorageManager()

# Register provider
manager.register_provider(GoogleDriveProvider())

# Authenticate
manager.authenticate_provider(
    CloudProvider.GOOGLE_DRIVE,
    {"client_config": {...}}
)

# List files
files = manager.list_files(CloudProvider.GOOGLE_DRIVE)

# Download
manager.download_file(
    CloudProvider.GOOGLE_DRIVE,
    file_id,
    Path("local_file.pdf")
)

# Upload
file_id = manager.upload_file(
    CloudProvider.GOOGLE_DRIVE,
    Path("local.md"),
    "cloud_file.md"
)
```

## Offline Mode

### Queue Operations

```python
from gui.core.cloud_storage import SyncTask, SyncStatus

# Enable offline mode
manager.offline_mode = True
manager.start_sync_worker()

# Queue operation
task = SyncTask(
    task_id="task_1",
    file_id="file_123",
    operation="upload",
    local_path=Path("file.md"),
    cloud_path="file.md"
)
manager.queue_sync_task(task)

# Operations will execute when online
```

### Sync Status

```python
# Get sync status
status = manager.get_sync_status("file_123")

# Check sync tasks
tasks = manager.sync_tasks
for task in tasks.values():
    print(f"{task.operation}: {task.status.value}")
```

## Conflict Resolution

### Resolving Conflicts

```python
# Resolve conflict
manager.resolve_conflict(
    file_id="file_123",
    resolution="local",  # or "cloud", "merge"
    local_path=Path("local_file.md")
)
```

### Resolution Strategies

1. **Local**: Use local version, upload to cloud
2. **Cloud**: Use cloud version, download to local
3. **Merge**: Merge both versions (requires implementation)

## Share Links

### Generating Share Links

```python
# Get share link
provider = manager.get_provider(CloudProvider.GOOGLE_DRIVE)
link = provider.get_share_link(file_id)

# For S3 (presigned URL with expiration)
s3_provider = manager.get_provider(CloudProvider.AWS_S3)
link = s3_provider.get_share_link(file_id, expires_in=3600)  # 1 hour
```

## Integration

### With Conversion System

```python
from gui.models.conversion_model import ConversionModel
from gui.core.cloud_storage import CloudStorageManager

# Download from cloud
manager = CloudStorageManager()
manager.download_file(
    CloudProvider.GOOGLE_DRIVE,
    cloud_file_id,
    Path("temp_file.pdf")
)

# Convert
model = ConversionModel(event_bus)
result = model.convert(Path("temp_file.pdf"))

# Upload result
manager.upload_file(
    CloudProvider.GOOGLE_DRIVE,
    Path("result.md"),
    "converted_file.md"
)
```

### With Batch Processing

```python
# Process files from cloud
files = manager.list_files(CloudProvider.GOOGLE_DRIVE)
for file in files:
    if not file.is_folder:
        # Download
        local_path = Path(f"temp_{file.name}")
        manager.download_file(CloudProvider.GOOGLE_DRIVE, file.file_id, local_path)
        
        # Convert
        result = convert_file(local_path)
        
        # Upload
        manager.upload_file(
            CloudProvider.GOOGLE_DRIVE,
            result_path,
            f"{file.name}.md"
        )
```

## Authentication

### Google Drive OAuth2

1. Create OAuth2 credentials in Google Cloud Console
2. Download client configuration JSON
3. Provide in credentials dialog
4. Complete OAuth2 flow in browser

### Dropbox

1. Create Dropbox app
2. Generate access token
3. Provide token in credentials dialog

### OneDrive

1. Register app in Azure Portal
2. Get client ID
3. Complete MSAL authentication flow

### AWS S3

1. Create IAM user
2. Generate access key and secret
3. Provide credentials in dialog
4. Select region

## Best Practices

1. **Secure Credentials**: Store credentials securely
2. **Use Offline Mode**: Queue operations when offline
3. **Resolve Conflicts**: Handle conflicts promptly
4. **Cache Metadata**: Use local cache for performance
5. **Error Handling**: Handle network errors gracefully
6. **Rate Limiting**: Respect API rate limits
7. **Sync Strategy**: Choose appropriate sync strategy

## Troubleshooting

### Authentication Fails
- Check credentials
- Verify API permissions
- Check network connectivity
- Review OAuth2 flow

### Upload/Download Fails
- Check file permissions
- Verify storage quota
- Check network connection
- Review API errors

### Sync Conflicts
- Review conflict resolution
- Check file timestamps
- Verify sync status
- Resolve manually if needed

## Dependencies

- `google-api-python-client`: Google Drive
- `dropbox`: Dropbox API
- `msal`: OneDrive authentication
- `boto3`: AWS S3

## See Also

- [Cloud Storage API](../core/cloud_storage.py)
- [Google Drive Integration](../integrations/google_drive.py)
- [Dropbox Integration](../integrations/dropbox_provider.py)
- [OneDrive Integration](../integrations/onedrive_provider.py)
- [AWS S3 Integration](../integrations/aws_s3_provider.py)
- [Cloud Explorer](../components/cloud_explorer.py)
- [Cloud Window](../views/cloud_window.py)

