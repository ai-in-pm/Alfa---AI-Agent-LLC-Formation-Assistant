import openai
from sqlalchemy.orm import Session
from models import Business
from typing import Dict, Any, List, Optional
import json
import os
from openai import AsyncOpenAI

class LLCBuilderService:
    def __init__(self, session: Session):
        self.session = session
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def build_llc_from_prompt(self, user_prompt: str) -> Dict:
        """Build LLC details based on user's natural language prompt."""
        # Generate LLC details using OpenAI
        llc_details = await self._generate_llc_details(user_prompt)
        
        # Create LLC record in database
        new_llc = Business(
            name=llc_details["name"],
            industry=llc_details["industry"],
            state=llc_details["state"],
            is_nonprofit=llc_details.get("is_nonprofit", False),
            tax_classification=llc_details.get("tax_classification"),
            mission_statement=llc_details.get("mission_statement")
        )
        
        self.session.add(new_llc)
        self.session.commit()
        
        return {
            "llc_details": llc_details,
            "registration_steps": await self._generate_registration_steps(llc_details),
            "required_documents": await self._generate_required_documents(llc_details),
            "estimated_costs": await self._generate_cost_estimates(llc_details),
            "timeline": await self._generate_timeline(llc_details)
        }

    async def create_llc(self, name: str, industry: str, state: str, is_nonprofit: bool = False,
                        tax_classification: str = "LLC", mission_statement: str = None) -> Business:
        """Create a new LLC with the specified details."""
        business = Business(
            name=name,
            industry=industry,
            state=state,
            is_nonprofit=is_nonprofit,
            tax_classification=tax_classification,
            mission_statement=mission_statement
        )

        self.session.add(business)
        self.session.commit()
        return business

    async def _generate_llc_details(self, user_prompt: str) -> Dict:
        """Generate LLC details using OpenAI based on user prompt."""
        prompt = f"""Based on the following user's description, generate detailed LLC information:
        User Description: {user_prompt}
        
        Generate a JSON response with the following structure:
        {{
            "name": "LLC name",
            "industry": "Industry type",
            "state": "State of registration",
            "is_nonprofit": false,
            "tax_classification": "Tax classification type",
            "mission_statement": "Mission statement if nonprofit",
            "target_market": "Target market description",
            "business_model": "Business model description",
            "revenue_streams": ["List of revenue streams"],
            "key_activities": ["List of key activities"]
        }}
        
        Ensure the response is valid JSON with proper quotes and boolean values.
        """
        
        response = await self.client.create_completion(
            model="gpt-4",
            prompt=prompt,
            temperature=0.7
        )
        
        return json.loads(response.choices[0].text)

    async def _generate_registration_steps(self, llc_details: Dict) -> List[Dict]:
        """Generate registration steps based on LLC details."""
        prompt = f"""Generate detailed registration steps for an LLC with the following details:
        Name: {llc_details['name']}
        State: {llc_details['state']}
        Industry: {llc_details['industry']}
        Is Nonprofit: {llc_details.get('is_nonprofit', False)}
        
        Return a JSON array of objects with 'step_number', 'description', and 'requirements' keys.
        Example:
        [
            {{
                "step_number": 1,
                "description": "Choose a business name",
                "requirements": ["Must be unique", "Must include LLC"]
            }}
        ]
        """
        
        response = await self.client.create_completion(
            model="gpt-4",
            prompt=prompt,
            temperature=0.7
        )
        
        return json.loads(response.choices[0].text)

    async def _generate_required_documents(self, llc_details: Dict) -> List[Dict]:
        """Generate list of required documents based on LLC details."""
        prompt = f"""List all required documents for registering an LLC with the following details:
        Name: {llc_details['name']}
        State: {llc_details['state']}
        Industry: {llc_details['industry']}
        Is Nonprofit: {llc_details.get('is_nonprofit', False)}
        
        Return a JSON array of objects with 'document_name', 'description', and 'required' (boolean) keys.
        Example:
        [
            {{
                "document_name": "Articles of Organization",
                "description": "Legal document establishing the LLC",
                "required": true
            }}
        ]
        """
        
        response = await self.client.create_completion(
            model="gpt-4",
            prompt=prompt,
            temperature=0.7
        )
        
        return json.loads(response.choices[0].text)

    async def _generate_cost_estimates(self, llc_details: Dict) -> Dict:
        """Generate cost estimates for LLC registration and setup."""
        prompt = f"""Generate detailed cost estimates for registering and setting up an LLC with the following details:
        Name: {llc_details['name']}
        State: {llc_details['state']}
        Industry: {llc_details['industry']}
        Is Nonprofit: {llc_details.get('is_nonprofit', False)}
        
        Return a JSON object with categories as keys and amounts as numeric values.
        Include filing fees, legal fees, licenses, permits, etc.
        Example:
        {{
            "filing_fee": 100,
            "legal_fees": 500,
            "licenses": 200
        }}
        """
        
        response = await self.client.create_completion(
            model="gpt-4",
            prompt=prompt,
            temperature=0.7
        )
        
        return json.loads(response.choices[0].text)

    async def _generate_timeline(self, llc_details: Dict) -> List[Dict]:
        """Generate estimated timeline for LLC setup and registration."""
        prompt = f"""Generate a detailed timeline for setting up and registering an LLC with the following details:
        Name: {llc_details['name']}
        State: {llc_details['state']}
        Industry: {llc_details['industry']}
        Is Nonprofit: {llc_details.get('is_nonprofit', False)}
        
        Return a JSON array of objects with 'phase', 'duration', and 'description' keys.
        Include all major phases from initial filing to final approval.
        Example:
        [
            {{
                "phase": "Initial Filing",
                "duration": "1-2 weeks",
                "description": "Submit Articles of Organization"
            }}
        ]
        """
        
        response = await self.client.create_completion(
            model="gpt-4",
            prompt=prompt,
            temperature=0.7
        )
        
        return json.loads(response.choices[0].text)
