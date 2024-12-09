import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from services.document_service import DocumentService
from models import Business, User, Document

class TestDocumentService(unittest.TestCase):
    def setUp(self):
        self.db_session = Mock()
        self.document_service = DocumentService(self.db_session)

    def test_generate_operating_agreement(self):
        # Mock business and owner data
        mock_owner = Mock(
            first_name="John",
            last_name="Doe"
        )
        mock_business = Mock(
            id=1,
            name="Test LLC",
            state="DE",
            created_at=datetime.now(),
            owner=mock_owner,
            owner_id=1
        )

        # Configure mock database query
        self.db_session.query.return_value.get.return_value = mock_business

        # Call the method
        result = self.document_service.generate_operating_agreement(1)

        # Assertions
        self.assertEqual(result.name, "Test LLC - Operating Agreement")
        self.assertEqual(result.type, "operating_agreement")
        self.assertEqual(result.business_id, 1)
        self.assertEqual(result.owner_id, 1)
        self.assertEqual(result.status, "draft")

        # Verify database interactions
        self.db_session.add.assert_called_once()
        self.db_session.commit.assert_called_once()

    def test_generate_articles_of_organization(self):
        # Mock data
        mock_owner = Mock(
            first_name="John",
            last_name="Doe"
        )
        mock_business = Mock(
            id=1,
            name="Test LLC",
            state="DE",
            business_address="123 Main St",
            owner=mock_owner,
            owner_id=1
        )

        self.db_session.query.return_value.get.return_value = mock_business

        # Call the method
        result = self.document_service.generate_articles_of_organization(1)

        # Assertions
        self.assertEqual(result.name, "Test LLC - Articles of Organization")
        self.assertEqual(result.type, "articles_of_organization")
        self.assertEqual(result.business_id, 1)
        self.assertEqual(result.status, "draft")

    def test_get_document_with_permission(self):
        # Mock document
        mock_document = Mock(
            id=1,
            owner_id=1,
            name="Test Document"
        )

        self.db_session.query.return_value.get.return_value = mock_document

        # Call the method
        result = self.document_service.get_document(1, 1)

        # Assertions
        self.assertEqual(result, mock_document)

    def test_get_document_without_permission(self):
        # Mock document owned by different user
        mock_document = Mock(
            id=1,
            owner_id=2,
            name="Test Document"
        )

        self.db_session.query.return_value.get.return_value = mock_document

        # Assert that accessing document raises PermissionError
        with self.assertRaises(PermissionError):
            self.document_service.get_document(1, 1)

    def test_update_document(self):
        # Mock document
        mock_document = Mock(
            id=1,
            owner_id=1,
            name="Test Document",
            content="Original content"
        )

        self.db_session.query.return_value.get.return_value = mock_document

        # Update document
        updates = {
            "content": "Updated content",
            "status": "revised"
        }

        result = self.document_service.update_document(1, 1, updates)

        # Assertions
        self.assertEqual(result.content, "Updated content")
        self.assertEqual(result.status, "revised")
        self.db_session.commit.assert_called_once()

    def test_delete_document(self):
        # Mock document
        mock_document = Mock(
            id=1,
            owner_id=1,
            name="Test Document"
        )

        self.db_session.query.return_value.get.return_value = mock_document

        # Delete document
        self.document_service.delete_document(1, 1)

        # Verify document was deleted
        self.db_session.delete.assert_called_once_with(mock_document)
        self.db_session.commit.assert_called_once()

    def test_list_documents(self):
        # Mock business and documents
        mock_business = Mock(
            id=1,
            owner_id=1
        )
        mock_documents = [
            Mock(id=1, name="Doc 1"),
            Mock(id=2, name="Doc 2")
        ]

        self.db_session.query.return_value.get.return_value = mock_business
        self.db_session.query.return_value.filter_by.return_value.all.return_value = mock_documents

        # List documents
        result = self.document_service.list_documents(1, 1)

        # Assertions
        self.assertEqual(len(result), 2)
        self.assertEqual(result, mock_documents)

    def test_list_documents_without_permission(self):
        # Mock business owned by different user
        mock_business = Mock(
            id=1,
            owner_id=2
        )

        self.db_session.query.return_value.get.return_value = mock_business

        # Assert that listing documents raises PermissionError
        with self.assertRaises(PermissionError):
            self.document_service.list_documents(1, 1)

if __name__ == '__main__':
    unittest.main()
