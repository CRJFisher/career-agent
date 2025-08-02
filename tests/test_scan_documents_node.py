"""Unit tests for ScanDocumentsNode."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os

from nodes import ScanDocumentsNode
from utils.document_scanner import DocumentMetadata


class TestScanDocumentsNode:
    """Test suite for ScanDocumentsNode."""
    
    def test_prep_with_full_config(self):
        """Test prep method with complete configuration."""
        node = ScanDocumentsNode()
        
        shared = {
            "scan_config": {
                "google_drive_folders": [
                    {"folder_id": "123", "name": "Work Docs"},
                    {"folder_id": "456", "name": "Projects"}
                ],
                "local_directories": [
                    {"path": "~/Documents/Career"},
                    {"path": "/absolute/path"}
                ],
                "file_types": [".pdf", ".docx", ".md", ".txt"],
                "date_filter": {
                    "min_date": "2023-01-01",
                    "max_date": "2024-12-31"
                }
            }
        }
        
        result = node.prep(shared)
        
        assert result["google_drive_folders"] == shared["scan_config"]["google_drive_folders"]
        assert result["local_directories"] == shared["scan_config"]["local_directories"]
        assert result["file_types"] == [".pdf", ".docx", ".md", ".txt"]
        assert result["date_filter"]["min_date"] == "2023-01-01"
        assert result["date_filter"]["max_date"] == "2024-12-31"
    
    def test_prep_with_minimal_config(self):
        """Test prep method with minimal/missing configuration."""
        node = ScanDocumentsNode()
        
        shared = {}  # No scan_config
        
        result = node.prep(shared)
        
        assert result["google_drive_folders"] == []
        assert result["local_directories"] == []
        assert result["file_types"] == [".pdf", ".docx", ".md"]  # Default
        assert result["date_filter"] == {}
    
    def test_prep_with_partial_config(self):
        """Test prep method with partial configuration."""
        node = ScanDocumentsNode()
        
        shared = {
            "scan_config": {
                "local_directories": ["~/Documents"],
                # Missing other fields
            }
        }
        
        result = node.prep(shared)
        
        assert result["google_drive_folders"] == []
        assert result["local_directories"] == ["~/Documents"]
        assert result["file_types"] == [".pdf", ".docx", ".md"]  # Default
        assert result["date_filter"] == {}
    
    @patch('utils.document_scanner.scan_documents')
    def test_exec_with_local_directories(self, mock_scan):
        """Test exec method scanning local directories."""
        node = ScanDocumentsNode()
        
        # Mock document results
        mock_docs = [
            DocumentMetadata(
                path="/home/user/doc1.pdf",
                name="doc1.pdf",
                type=".pdf",
                size=1000,
                modified_date=datetime(2024, 1, 1),
                source="local",
                additional_data={}
            ),
            DocumentMetadata(
                path="/home/user/doc2.md",
                name="doc2.md",
                type=".md",
                size=500,
                modified_date=datetime(2024, 2, 1),
                source="local",
                additional_data={}
            )
        ]
        mock_scan.return_value = mock_docs
        
        prep_res = {
            "google_drive_folders": [],
            "local_directories": ["/home/user/docs"],
            "file_types": [".pdf", ".md"],
            "date_filter": {}
        }
        
        result = node.exec(prep_res)
        
        # Verify scan was called correctly
        mock_scan.assert_called_once()
        call_args = mock_scan.call_args
        assert call_args[1]["paths"] == ["/home/user/docs"]
        assert call_args[1]["scanner_type"] == "local"
        assert call_args[1]["file_types"] == {".pdf", ".md"}
        
        # Verify results
        assert len(result["documents"]) == 2
        assert result["documents"][0]["name"] == "doc1.pdf"
        assert result["documents"][1]["name"] == "doc2.md"
        assert result["total_found"] == 2
        assert result["scan_errors"] == []
    
    @patch('utils.document_scanner.scan_documents')
    def test_exec_with_google_drive(self, mock_scan):
        """Test exec method scanning Google Drive folders."""
        node = ScanDocumentsNode()
        
        # Mock document results
        mock_docs = [
            DocumentMetadata(
                path="gdrive_file_123",
                name="project.docx",
                type=".docx",
                size=2000,
                modified_date=datetime(2024, 3, 1),
                source="google_drive",
                additional_data={"folder_id": "folder123"}
            )
        ]
        mock_scan.return_value = mock_docs
        
        prep_res = {
            "google_drive_folders": [{"folder_id": "folder123", "name": "Work"}],
            "local_directories": [],
            "file_types": [".docx"],
            "date_filter": {}
        }
        
        result = node.exec(prep_res)
        
        # Verify scan was called correctly
        mock_scan.assert_called_once()
        call_args = mock_scan.call_args
        assert call_args[1]["paths"] == ["folder123"]
        assert call_args[1]["scanner_type"] == "google_drive"
        
        # Verify results
        assert len(result["documents"]) == 1
        assert result["documents"][0]["name"] == "project.docx"
        assert result["documents"][0]["source"] == "google_drive"
    
    @patch('utils.document_scanner.scan_documents')
    def test_exec_with_date_filter(self, mock_scan):
        """Test exec method with date filtering."""
        node = ScanDocumentsNode()
        
        mock_scan.return_value = []
        
        prep_res = {
            "google_drive_folders": [],
            "local_directories": ["/path"],
            "file_types": [".pdf"],
            "date_filter": {
                "min_date": "2023-01-01",
                "max_date": "2023-12-31"
            }
        }
        
        result = node.exec(prep_res)
        
        # Verify date parsing was attempted
        call_args = mock_scan.call_args
        assert call_args[1]["min_date"] == datetime(2023, 1, 1)
        assert call_args[1]["max_date"] == datetime(2023, 12, 31)
    
    @patch('utils.document_scanner.scan_documents')
    def test_exec_with_scan_errors(self, mock_scan):
        """Test exec method handling scan errors gracefully."""
        node = ScanDocumentsNode()
        
        # Mock scan to raise an exception
        mock_scan.side_effect = Exception("Access denied")
        
        prep_res = {
            "google_drive_folders": [],
            "local_directories": ["/restricted/path"],
            "file_types": [".pdf"],
            "date_filter": {}
        }
        
        result = node.exec(prep_res)
        
        # Should handle error gracefully
        assert result["documents"] == []
        assert result["total_found"] == 0
        assert len(result["scan_errors"]) == 1
        assert result["scan_errors"][0]["path"] == "/restricted/path"
        assert "Access denied" in result["scan_errors"][0]["error"]
    
    @patch('utils.document_scanner.scan_documents')
    def test_exec_with_home_directory_expansion(self, mock_scan):
        """Test exec method expands home directory paths."""
        node = ScanDocumentsNode()
        
        mock_scan.return_value = []
        
        prep_res = {
            "google_drive_folders": [],
            "local_directories": ["~/Documents"],
            "file_types": [".pdf"],
            "date_filter": {}
        }
        
        with patch('os.path.expanduser') as mock_expand:
            mock_expand.return_value = "/home/user/Documents"
            result = node.exec(prep_res)
            
            # Verify home expansion was called
            mock_expand.assert_called_with("~/Documents")
            
            # Verify expanded path was used
            call_args = mock_scan.call_args
            assert call_args[1]["paths"] == ["/home/user/Documents"]
    
    def test_post_stores_documents(self):
        """Test post method stores documents in shared store."""
        node = ScanDocumentsNode()
        
        shared = {}
        prep_res = {}
        exec_res = {
            "documents": [
                {"name": "doc1.pdf", "path": "/path/doc1.pdf"},
                {"name": "doc2.md", "path": "/path/doc2.md"}
            ],
            "scan_errors": [],
            "total_found": 2
        }
        
        action = node.post(shared, prep_res, exec_res)
        
        assert action == "continue"
        assert "document_sources" in shared
        assert len(shared["document_sources"]) == 2
        assert shared["document_sources"][0]["name"] == "doc1.pdf"
        assert "scan_errors" not in shared  # No errors to store
    
    def test_post_stores_errors(self):
        """Test post method stores scan errors when present."""
        node = ScanDocumentsNode()
        
        shared = {}
        prep_res = {}
        exec_res = {
            "documents": [],
            "scan_errors": [
                {"path": "/restricted", "error": "Access denied", "type": "PermissionError"}
            ],
            "total_found": 0
        }
        
        action = node.post(shared, prep_res, exec_res)
        
        assert action == "continue"
        assert "document_sources" in shared
        assert shared["document_sources"] == []
        assert "scan_errors" in shared
        assert len(shared["scan_errors"]) == 1
        assert shared["scan_errors"][0]["error"] == "Access denied"
    
    @patch('utils.document_scanner.scan_documents')
    def test_exec_with_mixed_sources(self, mock_scan):
        """Test exec method with both Google Drive and local sources."""
        node = ScanDocumentsNode()
        
        # Mock different results for each call
        mock_scan.side_effect = [
            [DocumentMetadata(
                path="gdrive_123",
                name="gdrive_doc.pdf",
                type=".pdf",
                size=1000,
                modified_date=datetime(2024, 1, 1),
                source="google_drive",
                additional_data={}
            )],
            [DocumentMetadata(
                path="/local/doc.md",
                name="local_doc.md",
                type=".md",
                size=500,
                modified_date=datetime(2024, 2, 1),
                source="local",
                additional_data={}
            )]
        ]
        
        prep_res = {
            "google_drive_folders": [{"folder_id": "folder123"}],
            "local_directories": ["/local/path"],
            "file_types": [".pdf", ".md"],
            "date_filter": {}
        }
        
        result = node.exec(prep_res)
        
        # Should have called scan twice
        assert mock_scan.call_count == 2
        
        # Verify results from both sources
        assert result["total_found"] == 2
        assert len(result["documents"]) == 2
        assert any(d["source"] == "google_drive" for d in result["documents"])
        assert any(d["source"] == "local" for d in result["documents"])