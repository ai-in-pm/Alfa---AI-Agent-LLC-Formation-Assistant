import openai
from typing import List, Dict, Optional
from datetime import datetime
from models import Business, User
import json

class ChatService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.context_window = 10  # Number of previous messages to include for context

    async def get_response(self, 
                          user_id: int, 
                          message: str, 
                          business_id: Optional[int] = None,
                          context: Optional[List[Dict]] = None) -> Dict:
        """Get a response from Adam based on user input and context."""
        
        # Get user and business information
        user = self.db_session.query(User).get(user_id)
        business = None
        if business_id:
            business = self.db_session.query(Business).get(business_id)

        # Build the conversation context
        conversation = self._build_conversation_context(user, business, context)
        conversation.append({
            "role": "user",
            "content": message
        })

        try:
            # Get response from OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=conversation,
                temperature=0.7,
                max_tokens=500
            )

            # Extract and process the response
            ai_message = response.choices[0].message.content
            
            # Check for any actions or recommendations
            actions = self._extract_actions(ai_message)
            
            return {
                "message": ai_message,
                "actions": actions,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "message": "I apologize, but I'm having trouble processing your request at the moment. Please try again.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _build_conversation_context(self, 
                                  user: User, 
                                  business: Optional[Business] = None,
                                  context: Optional[List[Dict]] = None) -> List[Dict]:
        """Build the conversation context for the AI."""
        
        # Start with system message defining Adam's role
        conversation = [{
            "role": "system",
            "content": self._get_system_prompt(user, business)
        }]

        # Add previous context if provided
        if context:
            # Only include the last N messages to maintain context window
            for msg in context[-self.context_window:]:
                conversation.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        return conversation

    def _get_system_prompt(self, user: User, business: Optional[Business] = None) -> str:
        """Generate the system prompt for Adam."""
        
        prompt = f"""You are Adam, an AI business formation assistant and virtual CEO. You help entrepreneurs form and manage their LLCs while providing strategic business guidance.

Current User: {user.first_name} {user.last_name}
"""

        if business:
            prompt += f"""
Active Business: {business.name}
Formation Status: {business.formation_status}
State: {business.state}
Industry: {business.industry}

Your role is to provide specific guidance for this business, including:
1. LLC formation and compliance requirements
2. Industry-specific insights and recommendations
3. Strategic business planning and growth opportunities
"""
        else:
            prompt += """
Your role is to:
1. Guide users through the LLC formation process
2. Provide general business advice and best practices
3. Help users make informed decisions about their business structure
"""

        prompt += """
Please maintain a professional yet friendly tone, and always provide actionable insights and clear next steps.
"""

        return prompt

    def _extract_actions(self, message: str) -> List[Dict]:
        """Extract any recommended actions from the AI's response."""
        actions = []
        
        # Look for common action patterns in the message
        if "next steps" in message.lower():
            actions.append({
                "type": "task_list",
                "description": "Review recommended next steps"
            })
            
        if "document" in message.lower():
            actions.append({
                "type": "document_review",
                "description": "Review or prepare documents"
            })
            
        if "file" in message.lower():
            actions.append({
                "type": "state_filing",
                "description": "Process state filing"
            })

        return actions

    async def analyze_business_query(self, 
                                   query: str, 
                                   business_id: int,
                                   category: Optional[str] = None) -> Dict:
        """Analyze a specific business query and provide detailed insights."""
        
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Prepare the analysis prompt based on category
        if category == "market":
            prompt = f"""Analyze the following market-related query for {business.name} in the {business.industry} industry:
{query}

Consider:
1. Market trends and opportunities
2. Competitive landscape
3. Customer demographics
4. Growth potential
"""
        elif category == "financial":
            prompt = f"""Analyze the following financial query for {business.name}:
{query}

Consider:
1. Revenue optimization
2. Cost management
3. Cash flow implications
4. Financial risks and opportunities
"""
        elif category == "operations":
            prompt = f"""Analyze the following operational query for {business.name}:
{query}

Consider:
1. Operational efficiency
2. Resource allocation
3. Process optimization
4. Risk management
"""
        else:
            prompt = f"""Analyze the following business query for {business.name}:
{query}

Provide comprehensive insights and actionable recommendations.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a business analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            analysis = response.choices[0].message.content

            return {
                "query": query,
                "category": category,
                "analysis": analysis,
                "recommendations": self._extract_recommendations(analysis),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _extract_recommendations(self, analysis: str) -> List[Dict]:
        """Extract structured recommendations from the analysis text."""
        recommendations = []
        
        # Split analysis into lines and look for numbered items or bullet points
        lines = analysis.split('\n')
        current_rec = None
        
        for line in lines:
            line = line.strip()
            
            # Look for numbered recommendations or bullet points
            if line.startswith(('1.', '2.', '3.', '•', '-')):
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {
                    "description": line.lstrip('123456789.- '),
                    "priority": "high" if "immediate" in line.lower() or "critical" in line.lower() else "medium"
                }
            elif current_rec and line:
                # Add details to current recommendation
                current_rec["description"] += " " + line

        # Add the last recommendation if exists
        if current_rec:
            recommendations.append(current_rec)

        return recommendations
