import openai
from datetime import datetime
from models import BusinessInsight, Business, FinancialRecord
from sqlalchemy import func

class BusinessIntelligenceService:
    def __init__(self, db_session):
        self.db_session = db_session

    def generate_market_analysis(self, business_id):
        """Generate market analysis using OpenAI."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        prompt = f"""
        Provide a detailed market analysis for a {business.industry} business in {business.state}.
        Include:
        1. Market size and growth potential
        2. Key competitors
        3. Target customer demographics
        4. Industry trends
        5. Potential challenges and opportunities
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business analyst expert."},
                {"role": "user", "content": prompt}
            ]
        )

        analysis = response.choices[0].message.content

        insight = BusinessInsight(
            business_id=business_id,
            type="market_analysis",
            content={
                "analysis": analysis,
                "generated_date": datetime.utcnow().isoformat()
            },
            priority=1
        )

        self.db_session.add(insight)
        self.db_session.commit()
        return insight

    def generate_financial_insights(self, business_id):
        """Generate financial insights based on business records."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Calculate key financial metrics
        financial_data = self.db_session.query(
            func.sum(FinancialRecord.amount).label('total_revenue'),
            func.avg(FinancialRecord.amount).label('avg_transaction'),
            func.count(FinancialRecord.id).label('transaction_count')
        ).filter(
            FinancialRecord.business_id == business_id,
            FinancialRecord.type == 'revenue'
        ).first()

        # Generate insights using OpenAI
        prompt = f"""
        Analyze the following financial metrics and provide strategic insights:
        - Total Revenue: ${financial_data.total_revenue or 0:,.2f}
        - Average Transaction: ${financial_data.avg_transaction or 0:,.2f}
        - Transaction Count: {financial_data.transaction_count or 0}

        Provide:
        1. Performance analysis
        2. Growth opportunities
        3. Cost optimization suggestions
        4. Revenue improvement strategies
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial analyst expert."},
                {"role": "user", "content": prompt}
            ]
        )

        analysis = response.choices[0].message.content

        insight = BusinessInsight(
            business_id=business_id,
            type="financial_analysis",
            content={
                "metrics": {
                    "total_revenue": float(financial_data.total_revenue or 0),
                    "avg_transaction": float(financial_data.avg_transaction or 0),
                    "transaction_count": int(financial_data.transaction_count or 0)
                },
                "analysis": analysis,
                "generated_date": datetime.utcnow().isoformat()
            },
            priority=1
        )

        self.db_session.add(insight)
        self.db_session.commit()
        return insight

    def generate_growth_recommendations(self, business_id):
        """Generate personalized growth recommendations."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get business context
        financial_metrics = self.get_financial_metrics(business_id)
        market_position = self.analyze_market_position(business)

        prompt = f"""
        Provide strategic growth recommendations for a {business.industry} business with:
        Revenue: ${financial_metrics['total_revenue']:,.2f}
        Market Position: {market_position}
        State: {business.state}

        Include:
        1. Short-term growth tactics
        2. Long-term strategic initiatives
        3. Resource allocation suggestions
        4. Risk mitigation strategies
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business strategy expert."},
                {"role": "user", "content": prompt}
            ]
        )

        recommendations = response.choices[0].message.content

        insight = BusinessInsight(
            business_id=business_id,
            type="growth_recommendations",
            content={
                "recommendations": recommendations,
                "context": {
                    "financial_metrics": financial_metrics,
                    "market_position": market_position
                },
                "generated_date": datetime.utcnow().isoformat()
            },
            priority=2
        )

        self.db_session.add(insight)
        self.db_session.commit()
        return insight

    def get_financial_metrics(self, business_id):
        """Calculate key financial metrics for a business."""
        metrics = {}
        
        # Revenue metrics
        revenue_data = self.db_session.query(
            func.sum(FinancialRecord.amount).label('total_revenue'),
            func.avg(FinancialRecord.amount).label('avg_revenue')
        ).filter(
            FinancialRecord.business_id == business_id,
            FinancialRecord.type == 'revenue'
        ).first()
        
        metrics['total_revenue'] = float(revenue_data.total_revenue or 0)
        metrics['avg_revenue'] = float(revenue_data.avg_revenue or 0)
        
        return metrics

    def analyze_market_position(self, business):
        """Analyze the market position of a business."""
        # This would typically involve more complex analysis
        # For now, return a simplified position
        return "Growing business in competitive market"

    def get_latest_insights(self, business_id, insight_type=None, limit=5):
        """Retrieve the latest business insights."""
        query = self.db_session.query(BusinessInsight).filter(
            BusinessInsight.business_id == business_id
        )
        
        if insight_type:
            query = query.filter(BusinessInsight.type == insight_type)
            
        return query.order_by(BusinessInsight.created_at.desc()).limit(limit).all()
