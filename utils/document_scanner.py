"""Document scanning utilities for discovering work experience documents.

This module provides scanners for both local directories and Google Drive,
returning standardized metadata for document processing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import os
import mimetypes
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle


@dataclass
class DocumentMetadata:
    """Standardized metadata for discovered documents."""
    
    path: str  # Full path or Google Drive ID
    name: str  # File name
    type: str  # File extension or MIME type
    size: int  # Size in bytes
    modified_date: datetime
    source: str  # 'local' or 'google_drive'
    additional_data: Dict[str, Any] = None  # Extra metadata specific to source
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'path': self.path,
            'name': self.name,
            'type': self.type,
            'size': self.size,
            'modified_date': self.modified_date.isoformat(),
            'source': self.source,
            'additional_data': self.additional_data or {}
        }


class DocumentScanner(ABC):
    """Abstract base class for document scanners."""
    
    def __init__(self):
        self.supported_extensions: Set[str] = {'.md', '.pdf', '.docx', '.doc', '.txt'}
        self.min_date: Optional[datetime] = None
        self.max_date: Optional[datetime] = None
    
    def set_date_filter(self, min_date: Optional[datetime] = None, 
                       max_date: Optional[datetime] = None) -> None:
        """Set date range filter for scanning."""
        self.min_date = min_date
        self.max_date = max_date
    
    def set_file_types(self, extensions: Set[str]) -> None:
        """Set supported file extensions."""
        self.supported_extensions = {ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                                   for ext in extensions}
    
    def _is_date_in_range(self, date: datetime) -> bool:
        """Check if date is within filter range."""
        if self.min_date and date < self.min_date:
            return False
        if self.max_date and date > self.max_date:
            return False
        return True
    
    @abstractmethod
    def scan(self, path: str) -> List[DocumentMetadata]:
        """Scan for documents and return metadata."""
        pass


class LocalFileScanner(DocumentScanner):
    """Scanner for local file system directories."""
    
    def scan(self, path: str) -> List[DocumentMetadata]:
        """Recursively scan directory for supported documents.
        
        Args:
            path: Directory path to scan
            
        Returns:
            List of DocumentMetadata objects
        """
        documents = []
        root_path = Path(path)
        
        if not root_path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {path}")
        
        # Walk through directory tree
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                # Check if file extension is supported
                if file_path.suffix.lower() in self.supported_extensions:
                    try:
                        stat = file_path.stat()
                        modified_date = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Check date filter
                        if not self._is_date_in_range(modified_date):
                            continue
                        
                        # Create metadata
                        metadata = DocumentMetadata(
                            path=str(file_path.absolute()),
                            name=file_path.name,
                            type=file_path.suffix.lower(),
                            size=stat.st_size,
                            modified_date=modified_date,
                            source='local',
                            additional_data={
                                'relative_path': str(file_path.relative_to(root_path)),
                                'mime_type': mimetypes.guess_type(str(file_path))[0]
                            }
                        )
                        documents.append(metadata)
                        
                    except (OSError, IOError) as e:
                        # Skip files we can't access
                        print(f"Warning: Could not access file {file_path}: {e}")
                        continue
        
        return sorted(documents, key=lambda d: d.modified_date, reverse=True)


class GoogleDriveScanner(DocumentScanner):
    """Scanner for Google Drive folders."""
    
    # If modifying these scopes, delete the token file.
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, credentials_file: str = 'credentials.json',
                 token_file: str = 'token.pickle'):
        """Initialize Google Drive scanner.
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store authentication token
        """
        super().__init__()
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        
        # Map MIME types to extensions
        self.mime_to_ext = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'text/markdown': '.md',
            'application/vnd.google-apps.document': '.gdoc',  # Google Docs
        }
    
    def _authenticate(self) -> None:
        """Authenticate with Google Drive API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}. "
                        "Please download OAuth2 credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def _get_file_extension(self, file_data: Dict[str, Any]) -> Optional[str]:
        """Get file extension from Google Drive file data."""
        mime_type = file_data.get('mimeType', '')
        
        # Check if it's a known MIME type
        if mime_type in self.mime_to_ext:
            return self.mime_to_ext[mime_type]
        
        # Try to get from file name
        name = file_data.get('name', '')
        if '.' in name:
            return '.' + name.split('.')[-1].lower()
        
        return None
    
    def scan(self, path: str) -> List[DocumentMetadata]:
        """Scan Google Drive folder for supported documents.
        
        Args:
            path: Google Drive folder ID or path
            
        Returns:
            List of DocumentMetadata objects
        """
        if not self.service:
            self._authenticate()
        
        documents = []
        
        try:
            # Build query
            query_parts = [f"'{path}' in parents", "trashed = false"]
            
            # Add MIME type filters for supported types
            mime_filters = []
            for mime_type, ext in self.mime_to_ext.items():
                if ext in self.supported_extensions:
                    mime_filters.append(f"mimeType = '{mime_type}'")
            
            if mime_filters:
                query_parts.append(f"({' or '.join(mime_filters)})")
            
            query = ' and '.join(query_parts)
            
            # List all files in the folder
            page_token = None
            while True:
                response = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink)',
                    pageToken=page_token
                ).execute()
                
                files = response.get('files', [])
                
                for file_data in files:
                    # Get file extension
                    ext = self._get_file_extension(file_data)
                    if not ext or ext not in self.supported_extensions:
                        continue
                    
                    # Parse modified time
                    modified_str = file_data.get('modifiedTime', '')
                    modified_date = datetime.fromisoformat(modified_str.replace('Z', '+00:00'))
                    
                    # Check date filter
                    if not self._is_date_in_range(modified_date):
                        continue
                    
                    # Create metadata
                    metadata = DocumentMetadata(
                        path=file_data['id'],
                        name=file_data['name'],
                        type=ext,
                        size=int(file_data.get('size', 0)),
                        modified_date=modified_date,
                        source='google_drive',
                        additional_data={
                            'mime_type': file_data.get('mimeType'),
                            'web_view_link': file_data.get('webViewLink'),
                            'folder_id': path
                        }
                    )
                    documents.append(metadata)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as error:
            raise RuntimeError(f"An error occurred accessing Google Drive: {error}")
        
        return sorted(documents, key=lambda d: d.modified_date, reverse=True)


def scan_documents(paths: List[str], 
                  scanner_type: str = 'auto',
                  file_types: Optional[Set[str]] = None,
                  min_date: Optional[datetime] = None,
                  max_date: Optional[datetime] = None) -> List[DocumentMetadata]:
    """Convenience function to scan multiple paths with appropriate scanners.
    
    Args:
        paths: List of paths to scan (local directories or Google Drive IDs)
        scanner_type: 'local', 'google_drive', or 'auto' (detect based on path)
        file_types: Set of file extensions to include (e.g., {'.md', '.pdf'})
        min_date: Minimum file modification date
        max_date: Maximum file modification date
        
    Returns:
        Combined list of DocumentMetadata from all paths
    """
    all_documents = []
    
    for path in paths:
        # Determine scanner type
        if scanner_type == 'auto':
            # Simple heuristic: if path exists locally, use local scanner
            if os.path.exists(path):
                scanner = LocalFileScanner()
            else:
                # Assume it's a Google Drive ID
                scanner = GoogleDriveScanner()
        elif scanner_type == 'local':
            scanner = LocalFileScanner()
        elif scanner_type == 'google_drive':
            scanner = GoogleDriveScanner()
        else:
            raise ValueError(f"Unknown scanner type: {scanner_type}")
        
        # Configure scanner
        if file_types:
            scanner.set_file_types(file_types)
        scanner.set_date_filter(min_date, max_date)
        
        # Scan and collect documents
        try:
            documents = scanner.scan(path)
            all_documents.extend(documents)
        except Exception as e:
            print(f"Error scanning {path}: {e}")
            continue
    
    # Remove duplicates based on path
    seen_paths = set()
    unique_documents = []
    for doc in all_documents:
        if doc.path not in seen_paths:
            seen_paths.add(doc.path)
            unique_documents.append(doc)
    
    return sorted(unique_documents, key=lambda d: d.modified_date, reverse=True)