"""Tests for document scanning utilities."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import os

from utils.document_scanner import (
    DocumentMetadata, DocumentScanner, LocalFileScanner, 
    GoogleDriveScanner, scan_documents
)


class TestDocumentMetadata:
    """Tests for DocumentMetadata class."""
    
    def test_document_metadata_creation(self):
        """Test creating DocumentMetadata instance."""
        metadata = DocumentMetadata(
            path="/path/to/file.pdf",
            name="file.pdf",
            type=".pdf",
            size=1024,
            modified_date=datetime(2024, 1, 1),
            source="local"
        )
        
        assert metadata.path == "/path/to/file.pdf"
        assert metadata.name == "file.pdf"
        assert metadata.type == ".pdf"
        assert metadata.size == 1024
        assert metadata.modified_date == datetime(2024, 1, 1)
        assert metadata.source == "local"
        assert metadata.additional_data is None
    
    def test_document_metadata_to_dict(self):
        """Test converting DocumentMetadata to dictionary."""
        modified_date = datetime(2024, 1, 1, 12, 0, 0)
        metadata = DocumentMetadata(
            path="/path/to/file.pdf",
            name="file.pdf",
            type=".pdf",
            size=1024,
            modified_date=modified_date,
            source="local",
            additional_data={"key": "value"}
        )
        
        result = metadata.to_dict()
        
        assert result["path"] == "/path/to/file.pdf"
        assert result["name"] == "file.pdf"
        assert result["type"] == ".pdf"
        assert result["size"] == 1024
        assert result["modified_date"] == modified_date.isoformat()
        assert result["source"] == "local"
        assert result["additional_data"] == {"key": "value"}


class TestLocalFileScanner:
    """Tests for LocalFileScanner class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files
        files = [
            ("doc1.md", "# Document 1", datetime.now() - timedelta(days=1)),
            ("doc2.pdf", b"PDF content", datetime.now() - timedelta(days=2)),
            ("doc3.docx", b"DOCX content", datetime.now() - timedelta(days=3)),
            ("doc4.txt", "Text content", datetime.now() - timedelta(days=4)),
            ("ignored.jpg", b"Image content", datetime.now() - timedelta(days=5)),
            ("subdir/doc5.md", "# Document 5", datetime.now() - timedelta(days=6)),
        ]
        
        for file_path, content, mod_time in files:
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(content, bytes):
                full_path.write_bytes(content)
            else:
                full_path.write_text(content)
            
            # Set modification time
            os.utime(full_path, (mod_time.timestamp(), mod_time.timestamp()))
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_scan_local_directory(self, temp_dir):
        """Test scanning a local directory."""
        scanner = LocalFileScanner()
        documents = scanner.scan(temp_dir)
        
        # Should find 5 documents (excluding .jpg)
        assert len(documents) == 5
        
        # Check document names
        names = {doc.name for doc in documents}
        assert names == {"doc1.md", "doc2.pdf", "doc3.docx", "doc4.txt", "doc5.md"}
        
        # Check sorting by modified date (newest first)
        assert documents[0].name == "doc1.md"
        assert documents[-1].name == "doc5.md"
        
        # Check metadata
        doc1 = next(doc for doc in documents if doc.name == "doc1.md")
        assert doc1.type == ".md"
        assert doc1.source == "local"
        assert doc1.size > 0
        assert "relative_path" in doc1.additional_data
    
    def test_scan_with_file_type_filter(self, temp_dir):
        """Test scanning with file type filter."""
        scanner = LocalFileScanner()
        scanner.set_file_types({".md", ".txt"})
        documents = scanner.scan(temp_dir)
        
        # Should only find .md and .txt files
        assert len(documents) == 3
        types = {doc.type for doc in documents}
        assert types == {".md", ".txt"}
    
    def test_scan_with_date_filter(self, temp_dir):
        """Test scanning with date range filter."""
        scanner = LocalFileScanner()
        
        # Only files from last 3.5 days (to ensure we catch the 3rd day file)
        min_date = datetime.now() - timedelta(days=3.5)
        scanner.set_date_filter(min_date=min_date)
        documents = scanner.scan(temp_dir)
        
        # Should find 3 most recent files
        assert len(documents) == 3
        names = {doc.name for doc in documents}
        assert names == {"doc1.md", "doc2.pdf", "doc3.docx"}
    
    def test_scan_nonexistent_path(self):
        """Test scanning a nonexistent path."""
        scanner = LocalFileScanner()
        
        with pytest.raises(ValueError, match="Path does not exist"):
            scanner.scan("/nonexistent/path")
    
    def test_scan_file_instead_of_directory(self, temp_dir):
        """Test scanning a file instead of directory."""
        scanner = LocalFileScanner()
        file_path = os.path.join(temp_dir, "doc1.md")
        
        with pytest.raises(ValueError, match="Path is not a directory"):
            scanner.scan(file_path)


class TestGoogleDriveScanner:
    """Tests for GoogleDriveScanner class."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock Google Drive service."""
        service = Mock()
        
        # Mock files().list() response
        mock_response = {
            'files': [
                {
                    'id': 'file1',
                    'name': 'document1.pdf',
                    'mimeType': 'application/pdf',
                    'size': '1024',
                    'modifiedTime': '2024-01-01T12:00:00Z',
                    'webViewLink': 'https://drive.google.com/file1'
                },
                {
                    'id': 'file2',
                    'name': 'document2.docx',
                    'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'size': '2048',
                    'modifiedTime': '2024-01-02T12:00:00Z',
                    'webViewLink': 'https://drive.google.com/file2'
                },
                {
                    'id': 'file3',
                    'name': 'notes.md',
                    'mimeType': 'text/markdown',
                    'size': '512',
                    'modifiedTime': '2024-01-03T12:00:00Z',
                    'webViewLink': 'https://drive.google.com/file3'
                }
            ]
        }
        
        service.files().list().execute.return_value = mock_response
        return service
    
    @patch('utils.document_scanner.build')
    @patch('utils.document_scanner.os.path.exists')
    def test_scan_google_drive_folder(self, mock_exists, mock_build, mock_service):
        """Test scanning a Google Drive folder."""
        # Mock authentication
        mock_exists.return_value = False  # No existing token
        mock_build.return_value = mock_service
        
        scanner = GoogleDriveScanner()
        scanner.service = mock_service  # Bypass authentication
        
        documents = scanner.scan('folder123')
        
        # Should find 3 documents
        assert len(documents) == 3
        
        # Check document details
        assert documents[0].name == "notes.md"  # Newest first
        assert documents[0].type == ".md"
        assert documents[0].source == "google_drive"
        assert documents[0].path == "file3"
        assert documents[0].additional_data["web_view_link"] == "https://drive.google.com/file3"
        
        # Verify API call was made (not checking exact call count as implementation may vary)
        mock_service.files().list.assert_called()
        # Get the last call to list()
        calls = mock_service.files().list.call_args_list
        # Find the call that has the query parameter
        for call in calls:
            if len(call) > 1 and 'q' in call[1]:
                assert "'folder123' in parents" in call[1]['q']
                break
    
    @patch('utils.document_scanner.build')
    def test_scan_with_file_type_filter(self, mock_build, mock_service):
        """Test scanning with file type filter."""
        mock_build.return_value = mock_service
        
        scanner = GoogleDriveScanner()
        scanner.service = mock_service
        scanner.set_file_types({".pdf"})
        
        documents = scanner.scan('folder123')
        
        # Should only find PDF files
        assert len(documents) == 1
        assert documents[0].type == ".pdf"
    
    def test_get_file_extension(self):
        """Test file extension detection."""
        scanner = GoogleDriveScanner()
        
        # Test known MIME type
        file_data = {'mimeType': 'application/pdf', 'name': 'document'}
        assert scanner._get_file_extension(file_data) == '.pdf'
        
        # Test file name with extension
        file_data = {'mimeType': 'unknown/type', 'name': 'document.xyz'}
        assert scanner._get_file_extension(file_data) == '.xyz'
        
        # Test no extension
        file_data = {'mimeType': 'unknown/type', 'name': 'document'}
        assert scanner._get_file_extension(file_data) is None
    
    @patch('utils.document_scanner.build')
    def test_authentication_error(self, mock_build):
        """Test handling authentication errors."""
        mock_build.side_effect = Exception("Authentication failed")
        
        scanner = GoogleDriveScanner(credentials_file='nonexistent.json')
        
        with pytest.raises(FileNotFoundError):
            scanner.scan('folder123')


class TestScanDocuments:
    """Tests for scan_documents convenience function."""
    
    @patch('utils.document_scanner.LocalFileScanner')
    @patch('utils.document_scanner.os.path.exists')
    def test_scan_documents_auto_detect_local(self, mock_exists, mock_scanner_class):
        """Test auto-detecting local paths."""
        mock_exists.return_value = True
        mock_scanner = Mock()
        mock_scanner.scan.return_value = []
        mock_scanner_class.return_value = mock_scanner
        
        scan_documents(['/local/path'], scanner_type='auto')
        
        mock_scanner_class.assert_called_once()
        mock_scanner.scan.assert_called_once_with('/local/path')
    
    @patch('utils.document_scanner.GoogleDriveScanner')
    @patch('utils.document_scanner.os.path.exists')
    def test_scan_documents_auto_detect_drive(self, mock_exists, mock_scanner_class):
        """Test auto-detecting Google Drive IDs."""
        mock_exists.return_value = False
        mock_scanner = Mock()
        mock_scanner.scan.return_value = []
        mock_scanner_class.return_value = mock_scanner
        
        scan_documents(['drive_folder_id'], scanner_type='auto')
        
        mock_scanner_class.assert_called_once()
        mock_scanner.scan.assert_called_once_with('drive_folder_id')
    
    @patch('utils.document_scanner.LocalFileScanner')
    def test_scan_documents_with_filters(self, mock_scanner_class):
        """Test scanning with filters."""
        mock_scanner = Mock()
        mock_scanner.scan.return_value = []
        mock_scanner_class.return_value = mock_scanner
        
        min_date = datetime(2024, 1, 1)
        max_date = datetime(2024, 12, 31)
        file_types = {'.pdf', '.docx'}
        
        scan_documents(['/path'], scanner_type='local', 
                      file_types=file_types, min_date=min_date, max_date=max_date)
        
        mock_scanner.set_file_types.assert_called_once_with(file_types)
        mock_scanner.set_date_filter.assert_called_once_with(min_date, max_date)
    
    @patch('utils.document_scanner.LocalFileScanner')
    def test_scan_documents_error_handling(self, mock_scanner_class):
        """Test error handling in scan_documents."""
        mock_scanner = Mock()
        mock_scanner.scan.side_effect = Exception("Scan failed")
        mock_scanner_class.return_value = mock_scanner
        
        # Should not raise, just print error and continue
        result = scan_documents(['/path1', '/path2'], scanner_type='local')
        
        assert result == []  # Empty result due to errors
        assert mock_scanner.scan.call_count == 2