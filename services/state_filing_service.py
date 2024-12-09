import requests
from typing import Dict, Any
import json
from datetime import datetime
from models import Business, Document
import os
import base64

class StateFilingService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.api_keys = {
            'DE': os.getenv('DELAWARE_API_KEY'),
            'WY': os.getenv('WYOMING_API_KEY'),
            # Add more state API keys
        }
        self.api_endpoints = {
            'DE': {
                'base_url': 'https://api.delaware.gov/business/v1',
                'formation': '/formation/llc',
                'status': '/status',
                'documents': '/documents'
            },
            'WY': {
                'base_url': 'https://api.wyo.gov/business/v1',
                'formation': '/formation/llc',
                'status': '/status',
                'documents': '/documents'
            }
            # Add more state endpoints
        }

    async def submit_llc_formation(self, business_id: int) -> Dict[str, Any]:
        """Submit LLC formation documents to the state."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        state = business.state
        if state not in self.api_endpoints:
            raise ValueError(f"State {state} not supported")

        # Prepare formation documents
        documents = self._prepare_formation_documents(business)
        
        # Submit to state API
        try:
            response = await self._submit_to_state_api(state, 'formation', {
                'business_name': business.name,
                'business_type': 'LLC',
                'documents': documents,
                'registered_agent': {
                    'name': business.registered_agent,
                    'address': business.registered_agent_address
                },
                'owners': self._format_owners(business),
                'contact': {
                    'name': f"{business.owner.first_name} {business.owner.last_name}",
                    'email': business.owner.email,
                    'phone': business.phone
                }
            })

            # Update business status
            business.formation_status = 'submitted'
            business.state_filing_number = response.get('filing_number')
            self.db_session.commit()

            return {
                'status': 'success',
                'filing_number': response.get('filing_number'),
                'estimated_completion': response.get('estimated_completion'),
                'fees': response.get('fees')
            }

        except Exception as e:
            business.formation_status = 'error'
            self.db_session.commit()
            raise Exception(f"Formation submission failed: {str(e)}")

    async def check_filing_status(self, business_id: int) -> Dict[str, Any]:
        """Check the status of a submitted LLC formation."""
        business = self.db_session.query(Business).get(business_id)
        if not business or not business.state_filing_number:
            raise ValueError("Business or filing number not found")

        try:
            response = await self._submit_to_state_api(
                business.state,
                'status',
                {'filing_number': business.state_filing_number}
            )

            # Update business status if formation is complete
            if response.get('status') == 'completed':
                business.formation_status = 'completed'
                business.formation_date = datetime.strptime(
                    response.get('completion_date'),
                    '%Y-%m-%d'
                )
                self.db_session.commit()

            return response

        except Exception as e:
            raise Exception(f"Status check failed: {str(e)}")

    async def retrieve_filed_documents(self, business_id: int) -> Dict[str, Any]:
        """Retrieve filed documents from the state."""
        business = self.db_session.query(Business).get(business_id)
        if not business or not business.state_filing_number:
            raise ValueError("Business or filing number not found")

        try:
            response = await self._submit_to_state_api(
                business.state,
                'documents',
                {'filing_number': business.state_filing_number}
            )

            # Save documents to database
            for doc in response.get('documents', []):
                document = Document(
                    name=doc['name'],
                    type=doc['type'],
                    content=doc['content'],
                    business_id=business_id,
                    owner_id=business.owner_id,
                    status='filed'
                )
                self.db_session.add(document)
            
            self.db_session.commit()
            return response

        except Exception as e:
            raise Exception(f"Document retrieval failed: {str(e)}")

    def _prepare_formation_documents(self, business: Business) -> Dict[str, str]:
        """Prepare and format documents for state filing."""
        documents = {}
        
        # Get all draft documents for the business
        business_docs = self.db_session.query(Document).filter_by(
            business_id=business.id,
            status='draft'
        ).all()

        for doc in business_docs:
            # Convert document content to base64 if needed
            content = base64.b64encode(doc.content.encode()).decode() if doc.content else ''
            documents[doc.type] = {
                'name': doc.name,
                'content': content,
                'format': 'base64'
            }

        return documents

    def _format_owners(self, business: Business) -> List[Dict[str, Any]]:
        """Format owner information for state filing."""
        # For now, just return the primary owner
        return [{
            'name': f"{business.owner.first_name} {business.owner.last_name}",
            'type': 'individual',
            'ownership_percentage': 100,
            'address': business.owner_address
        }]

    async def _submit_to_state_api(self, state: str, endpoint_type: str, payload: Dict) -> Dict:
        """Submit request to state API."""
        if state not in self.api_endpoints:
            raise ValueError(f"State {state} not supported")

        api_config = self.api_endpoints[state]
        url = f"{api_config['base_url']}{api_config[endpoint_type]}"

        headers = {
            'Authorization': f"Bearer {self.api_keys[state]}",
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    async def calculate_filing_fees(self, business_id: int) -> Dict[str, float]:
        """Calculate filing fees for LLC formation."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # State-specific fee calculations
        state_fees = {
            'DE': {
                'formation': 90.00,
                'registered_agent': 50.00,
                'expedited': 50.00,
                'certified_copy': 30.00
            },
            'WY': {
                'formation': 100.00,
                'registered_agent': 50.00,
                'expedited': 50.00,
                'certified_copy': 30.00
            }
        }

        fees = state_fees.get(business.state, {})
        total = sum(fees.values())

        return {
            'breakdown': fees,
            'total': total,
            'currency': 'USD'
        }
