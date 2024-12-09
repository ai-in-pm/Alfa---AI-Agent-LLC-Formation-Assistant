import os
from jinja2 import Template
import json
from datetime import datetime
from models import Document, Business

class DocumentService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.template_dir = os.path.join(os.path.dirname(__file__), '../templates')

    def generate_operating_agreement(self, business_id):
        """Generate an Operating Agreement based on business information."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        template_path = os.path.join(self.template_dir, 'operating_agreement.j2')
        with open(template_path, 'r') as f:
            template = Template(f.read())

        content = template.render(
            business_name=business.name,
            state=business.state,
            formation_date=business.created_at.strftime('%B %d, %Y'),
            owner_name=f"{business.owner.first_name} {business.owner.last_name}",
        )

        document = Document(
            name=f"{business.name} - Operating Agreement",
            type="operating_agreement",
            content=content,
            business_id=business_id,
            owner_id=business.owner_id,
            status="draft"
        )

        self.db_session.add(document)
        self.db_session.commit()
        return document

    def generate_articles_of_organization(self, business_id):
        """Generate Articles of Organization based on business information."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        template_path = os.path.join(self.template_dir, f'articles_{business.state.lower()}.j2')
        with open(template_path, 'r') as f:
            template = Template(f.read())

        content = template.render(
            business_name=business.name,
            state=business.state,
            business_address=business.business_address,
            registered_agent="",  # TODO: Add registered agent information
            owner_name=f"{business.owner.first_name} {business.owner.last_name}",
        )

        document = Document(
            name=f"{business.name} - Articles of Organization",
            type="articles_of_organization",
            content=content,
            business_id=business_id,
            owner_id=business.owner_id,
            status="draft"
        )

        self.db_session.add(document)
        self.db_session.commit()
        return document

    def generate_ein_application(self, business_id):
        """Generate EIN application (Form SS-4) based on business information."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        template_path = os.path.join(self.template_dir, 'form_ss4.j2')
        with open(template_path, 'r') as f:
            template = Template(f.read())

        content = template.render(
            business_name=business.name,
            business_address=business.business_address,
            owner_name=f"{business.owner.first_name} {business.owner.last_name}",
            owner_ssn="",  # TODO: Add secure handling of SSN
            start_date=business.created_at.strftime('%Y-%m-%d'),
        )

        document = Document(
            name=f"{business.name} - Form SS-4",
            type="ein_application",
            content=content,
            business_id=business_id,
            owner_id=business.owner_id,
            status="draft"
        )

        self.db_session.add(document)
        self.db_session.commit()
        return document

    def get_document(self, document_id, user_id):
        """Retrieve a document with permission checking."""
        document = self.db_session.query(Document).get(document_id)
        if not document:
            raise ValueError("Document not found")
        
        if document.owner_id != user_id:
            raise PermissionError("Not authorized to access this document")
            
        return document

    def update_document(self, document_id, user_id, updates):
        """Update a document with permission checking."""
        document = self.get_document(document_id, user_id)
        
        for key, value in updates.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        document.updated_at = datetime.utcnow()
        self.db_session.commit()
        return document

    def delete_document(self, document_id, user_id):
        """Delete a document with permission checking."""
        document = self.get_document(document_id, user_id)
        self.db_session.delete(document)
        self.db_session.commit()

    def list_documents(self, business_id, user_id):
        """List all documents for a business with permission checking."""
        business = self.db_session.query(Business).get(business_id)
        if not business or business.owner_id != user_id:
            raise PermissionError("Not authorized to access these documents")
            
        return self.db_session.query(Document).filter_by(business_id=business_id).all()
