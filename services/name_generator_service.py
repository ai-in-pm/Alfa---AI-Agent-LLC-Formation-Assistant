import openai
import requests
from typing import List, Dict
import json
import re

class NameGeneratorService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.state_api_endpoints = {
            'DE': 'https://icis.corp.delaware.gov/api/name-availability',
            'WY': 'https://wyobiz.wyo.gov/api/name-availability',
            # Add more state APIs as needed
        }

    def generate_business_names(self, industry: str, keywords: List[str], state: str) -> List[Dict]:
        """Generate business name suggestions using OpenAI and check availability."""
        
        # Create a detailed prompt for OpenAI
        prompt = f"""
        Generate 10 unique and creative business names for a {industry} company.
        Keywords to consider: {', '.join(keywords)}
        
        Requirements:
        1. Names should be memorable and professional
        2. Avoid common or generic terms
        3. Consider brand potential
        4. Must work as an LLC name
        5. Maximum 30 characters
        
        Format each name with a brief explanation of its meaning.
        """

        # Generate names using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business naming expert."},
                {"role": "user", "content": prompt}
            ]
        )

        # Parse the response and extract names
        generated_names = self._parse_generated_names(response.choices[0].message.content)
        
        # Check availability for each name
        available_names = []
        for name in generated_names:
            availability = self.check_name_availability(f"{name['name']}, LLC", state)
            name['available'] = availability['available']
            name['conflicts'] = availability.get('conflicts', [])
            if availability['available']:
                available_names.append(name)

        return available_names

    def _parse_generated_names(self, content: str) -> List[Dict]:
        """Parse the OpenAI response and extract names with explanations."""
        names = []
        lines = content.split('\n')
        current_name = None
        current_explanation = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for patterns like "1. Name:" or "Name:"
            name_match = re.match(r'^(?:\d+\.)?\s*([^:]+):', line)
            if name_match:
                if current_name:
                    names.append({
                        'name': current_name,
                        'explanation': ' '.join(current_explanation)
                    })
                current_name = name_match.group(1).strip()
                current_explanation = []
            elif current_name:
                current_explanation.append(line)

        # Add the last name if exists
        if current_name:
            names.append({
                'name': current_name,
                'explanation': ' '.join(current_explanation)
            })

        return names

    def check_name_availability(self, name: str, state: str) -> Dict:
        """Check if a business name is available in the specified state."""
        # Remove common business identifiers for checking
        check_name = self._normalize_business_name(name)
        
        try:
            # First check common patterns that would make the name invalid
            validation_result = self._validate_name_format(check_name)
            if not validation_result['valid']:
                return {
                    'available': False,
                    'conflicts': [validation_result['reason']]
                }

            # Mock API call for now - in production, would call actual state APIs
            # return self._call_state_api(name, state)
            
            # For demonstration, return mock response
            return {
                'available': True,
                'conflicts': []
            }

        except Exception as e:
            return {
                'available': False,
                'conflicts': [f"Error checking availability: {str(e)}"]
            }

    def _normalize_business_name(self, name: str) -> str:
        """Remove common business identifiers and normalize the name."""
        # Remove LLC, Inc, Corp, etc.
        identifiers = [
            r'\bL\.?L\.?C\.?\b',
            r'\bINC\.?\b',
            r'\bCORP\.?\b',
            r'\bINCORPORATED\b',
            r'\bCORPORATION\b',
            r'\bCOMPANY\b',
            r'\bLIMITED\b',
            r'\bLTD\.?\b'
        ]
        
        name = name.upper()
        for identifier in identifiers:
            name = re.sub(identifier, '', name, flags=re.IGNORECASE)
        
        return name.strip().strip(',').strip()

    def _validate_name_format(self, name: str) -> Dict:
        """Validate the format of a business name."""
        # Check length
        if len(name) > 30:
            return {
                'valid': False,
                'reason': 'Name exceeds maximum length of 30 characters'
            }

        # Check for restricted words
        restricted_words = ['BANK', 'INSURANCE', 'FEDERAL', 'NATIONAL', 'UNITED STATES', 'RESERVE']
        for word in restricted_words:
            if word in name.upper():
                return {
                    'valid': False,
                    'reason': f'Name contains restricted word: {word}'
                }

        # Check for special characters
        if re.search(r'[^a-zA-Z0-9\s&\'-]', name):
            return {
                'valid': False,
                'reason': 'Name contains invalid special characters'
            }

        return {'valid': True}

    def _call_state_api(self, name: str, state: str) -> Dict:
        """Call the state's business entity API to check name availability."""
        if state not in self.state_api_endpoints:
            raise ValueError(f"No API endpoint configured for state: {state}")

        try:
            response = requests.get(
                self.state_api_endpoints[state],
                params={'name': name},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling state API: {str(e)}")

    def generate_domain_suggestions(self, business_name: str) -> List[Dict]:
        """Generate domain name suggestions for the business."""
        # Remove LLC and other business identifiers
        base_name = self._normalize_business_name(business_name)
        base_name = base_name.lower().replace(' ', '')

        # Generate variations
        domains = [
            {'domain': f"{base_name}.com", 'type': 'Primary'},
            {'domain': f"{base_name}.io", 'type': 'Tech-friendly'},
            {'domain': f"{base_name}.co", 'type': 'Modern'},
            {'domain': f"get{base_name}.com", 'type': 'Action-oriented'},
            {'domain': f"{base_name}llc.com", 'type': 'Business-specific'},
        ]

        # In production, would check domain availability using a domain API
        return domains
