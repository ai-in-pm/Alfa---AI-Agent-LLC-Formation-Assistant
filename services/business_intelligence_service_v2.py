from datetime import datetime, timedelta
import openai
import numpy as np
from typing import Dict, List, Any
from models import Business
from sqlalchemy import func
from sqlalchemy.orm import Session
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import json
import os
from openai import AsyncOpenAI

class EnhancedBusinessIntelligenceService:
    def __init__(self, session: Session):
        self.session = session
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def analyze_business(self, business_id: int) -> Dict[str, Any]:
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError(f"Business with ID {business_id} not found")

        # Generate analysis using OpenAI
        prompt = f"""
        Analyze the following business:
        Name: {business.name}
        Industry: {business.industry}
        State: {business.state}
        Type: {"Non-Profit" if business.is_nonprofit else "For-Profit"}
        Mission: {business.mission_statement}

        Provide a comprehensive analysis including:
        1. Market opportunities
        2. Potential challenges
        3. Growth strategies
        4. Key performance indicators
        """

        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a business intelligence expert."},
                {"role": "user", "content": prompt}
            ]
        )

        analysis = response.choices[0].message.content
        return json.loads(analysis) if isinstance(analysis, str) else analysis

    async def perform_customer_segmentation(self, business_id: int) -> Dict:
        """Perform customer segmentation analysis."""
        # Get customer transaction data
        transactions = self._get_customer_transactions(business_id)
        
        if not transactions:
            return {"error": "Insufficient customer data"}

        # Prepare data for clustering
        features = self._prepare_segmentation_features(transactions)
        
        # Perform clustering
        segments = self._cluster_customers(features)
        
        # Generate segment insights
        insights = self._generate_segment_insights(segments)
        
        return {
            "segments": segments,
            "insights": insights,
            "recommendations": self._generate_segment_recommendations(segments)
        }

    def _prepare_segmentation_features(self, transactions: List[Dict]) -> pd.DataFrame:
        """Prepare customer transaction data for segmentation."""
        # Convert transactions to DataFrame
        df = pd.DataFrame(transactions)
        
        # Calculate customer metrics
        customer_metrics = df.groupby('customer_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'date': ['min', 'max']
        })
        
        # Calculate recency, frequency, monetary value
        now = datetime.now()
        customer_metrics['recency'] = (now - customer_metrics['date']['max']).dt.days
        customer_metrics['frequency'] = customer_metrics['amount']['count']
        customer_metrics['monetary'] = customer_metrics['amount']['sum']
        
        # Normalize features
        scaler = MinMaxScaler()
        features = scaler.fit_transform(customer_metrics[['recency', 'frequency', 'monetary']])
        
        return pd.DataFrame(features, columns=['recency', 'frequency', 'monetary'])

    def _cluster_customers(self, features: pd.DataFrame) -> Dict:
        """Perform customer clustering."""
        # Determine optimal number of clusters
        n_clusters = min(5, len(features))
        
        # Perform k-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features)
        
        # Analyze clusters
        cluster_analysis = []
        for i in range(n_clusters):
            cluster_features = features[clusters == i]
            cluster_analysis.append({
                "segment_id": i,
                "size": len(cluster_features),
                "avg_recency": cluster_features['recency'].mean(),
                "avg_frequency": cluster_features['frequency'].mean(),
                "avg_monetary": cluster_features['monetary'].mean()
            })
        
        return cluster_analysis

    async def generate_growth_strategy(self, business_id: int) -> Dict:
        """Generate comprehensive growth strategy."""
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Analyze current performance
        performance = self._analyze_business_performance(business_id)
        
        # Generate strategy using OpenAI
        strategy = await self._generate_growth_strategy(business, performance)
        
        return {
            "current_performance": performance,
            "growth_opportunities": strategy["opportunities"],
            "action_plan": strategy["action_plan"],
            "resource_requirements": strategy["resources"],
            "timeline": strategy["timeline"]
        }

    def _analyze_business_performance(self, business_id: int) -> Dict:
        """Analyze current business performance metrics."""
        # Get financial metrics
        financials = self._get_financial_metrics(business_id)
        
        # Calculate growth rates
        growth_rates = self._calculate_growth_rates(financials)
        
        # Analyze operational efficiency
        efficiency = self._analyze_efficiency(business_id)
        
        return {
            "financials": financials,
            "growth_rates": growth_rates,
            "efficiency": efficiency
        }

    def _get_financial_metrics(self, business_id: int) -> Dict:
        """Get financial metrics for the business."""
        # In a real implementation, this would fetch actual financial data
        # For now, returning sample metrics
        return {
            "revenue": 1000000,
            "expenses": 800000,
            "profit_margin": 0.2,
            "operating_costs": 600000,
            "marketing_spend": 100000,
            "r_and_d_spend": 100000
        }

    def _get_growth_metrics(self, business_id: int) -> Dict:
        """Get growth metrics for the business."""
        # In a real implementation, this would fetch actual growth data
        # For now, returning sample metrics
        return {
            "revenue_growth": 0.15,  # 15% year-over-year
            "customer_growth": 0.25,  # 25% year-over-year
            "market_share_growth": 0.1,  # 10% year-over-year
            "employee_growth": 0.2,  # 20% year-over-year
            "product_line_expansion": 2  # Added 2 new product lines
        }

    async def generate_risk_assessment(self, business_id: int) -> Dict:
        """Generate comprehensive risk assessment."""
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Analyze different risk categories
        financial_risks = self._assess_financial_risks(business_id)
        market_risks = self._assess_market_risks(business)
        operational_risks = self._assess_operational_risks(business)
        compliance_risks = self._assess_compliance_risks(business)
        
        # Generate mitigation strategies
        strategies = await self._generate_risk_mitigation_strategies({
            "financial": financial_risks,
            "market": market_risks,
            "operational": operational_risks,
            "compliance": compliance_risks
        })
        
        return {
            "risk_assessment": {
                "financial_risks": financial_risks,
                "market_risks": market_risks,
                "operational_risks": operational_risks,
                "compliance_risks": compliance_risks
            },
            "mitigation_strategies": strategies,
            "risk_score": self._calculate_risk_score(financial_risks, market_risks, 
                                                   operational_risks, compliance_risks)
        }

    def _assess_financial_risks(self, business_id: int) -> List[Dict]:
        """Assess financial risks based on business metrics."""
        # Get financial metrics
        metrics = self._get_financial_metrics(business_id)
        
        risks = []
        
        # Assess cash flow risk
        if metrics.get('cash_flow_ratio', 0) < 1.0:
            risks.append({
                "type": "cash_flow",
                "severity": "high",
                "description": "Negative cash flow trend detected",
                "metrics": {"cash_flow_ratio": metrics['cash_flow_ratio']}
            })
        
        # Assess debt risk
        if metrics.get('debt_to_equity', 0) > 2.0:
            risks.append({
                "type": "debt",
                "severity": "medium",
                "description": "High debt-to-equity ratio",
                "metrics": {"debt_to_equity": metrics['debt_to_equity']}
            })
        
        return risks

    async def generate_industry_benchmarks(self, business_id: int) -> Dict:
        """Generate industry benchmarks and comparative analysis."""
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get business metrics
        metrics = self._get_business_metrics(business_id)
        
        # Get industry benchmarks
        benchmarks = await self._get_industry_benchmarks(business.industry, business.state)
        
        # Compare metrics with benchmarks
        comparison = self._compare_with_benchmarks(metrics, benchmarks)
        
        return {
            "business_metrics": metrics,
            "industry_benchmarks": benchmarks,
            "comparison": comparison,
            "recommendations": self._generate_benchmark_recommendations(comparison)
        }

    def _get_business_metrics(self, business_id: int) -> Dict:
        """Calculate comprehensive business metrics."""
        return {
            "financial": self._get_financial_metrics(business_id),
            "operational": self._get_operational_metrics(business_id),
            "growth": self._get_growth_metrics(business_id)
        }

    def _get_operational_metrics(self, business_id: int) -> Dict:
        """Get operational metrics for the business."""
        # In a real implementation, this would fetch actual operational data
        # For now, returning sample metrics
        return {
            "employee_count": 50,
            "customer_satisfaction": 4.5,
            "employee_satisfaction": 4.2,
            "project_completion_rate": 0.85,
            "customer_retention_rate": 0.9,
            "average_response_time": "24h"
        }

    async def _get_industry_benchmarks(self, industry: str, state: str) -> Dict:
        """Get industry benchmarks from various sources."""
        # This would typically integrate with industry databases
        # For now, using OpenAI to generate realistic benchmarks
        prompt = f"""Generate realistic industry benchmarks for {industry} businesses in {state}, including:
        1. Financial ratios
        2. Operational metrics
        3. Growth rates
        4. Market share statistics"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business analytics expert."},
                {"role": "user", "content": prompt}
            ]
        )

        return self._parse_benchmarks(response.choices[0].message.content)

    def _parse_benchmarks(self, content: str) -> Dict:
        """Parse industry benchmarks from OpenAI response."""
        # In a real implementation, this would parse numeric benchmarks
        # For now, returning example metrics
        return {
            "financial": {
                "profit_margin": 0.15,
                "revenue_growth": 0.08,
                "operating_margin": 0.12
            },
            "operational": {
                "employee_productivity": 250000,
                "inventory_turnover": 12,
                "customer_satisfaction": 4.2
            },
            "growth": {
                "market_share": 0.05,
                "year_over_year": 0.10,
                "new_customer_rate": 0.15
            }
        }

    def _compare_with_benchmarks(self, metrics: Dict, benchmarks: Dict) -> Dict:
        """Compare business metrics with industry benchmarks."""
        comparisons = {}
        
        # Compare financial metrics
        if "financial" in metrics and "financial" in benchmarks:
            financial_comparison = {}
            for key in metrics["financial"]:
                if key in benchmarks["financial"]:
                    business_value = metrics["financial"][key]
                    benchmark_value = benchmarks["financial"][key]
                    financial_comparison[key] = {
                        "business_value": business_value,
                        "benchmark_value": benchmark_value,
                        "difference": business_value - benchmark_value if isinstance(business_value, (int, float)) else "N/A",
                        "performance": "Above Average" if business_value > benchmark_value else "Below Average" if business_value < benchmark_value else "Average"
                    }
            comparisons["financial"] = financial_comparison
        
        # Compare operational metrics
        if "operational" in metrics and "operational" in benchmarks:
            operational_comparison = {}
            for key in metrics["operational"]:
                if key in benchmarks["operational"]:
                    business_value = metrics["operational"][key]
                    benchmark_value = benchmarks["operational"][key]
                    operational_comparison[key] = {
                        "business_value": business_value,
                        "benchmark_value": benchmark_value,
                        "difference": business_value - benchmark_value if isinstance(business_value, (int, float)) else "N/A",
                        "performance": "Above Average" if business_value > benchmark_value else "Below Average" if business_value < benchmark_value else "Average"
                    }
            comparisons["operational"] = operational_comparison
        
        # Compare growth metrics
        if "growth" in metrics and "growth" in benchmarks:
            growth_comparison = {}
            for key in metrics["growth"]:
                if key in benchmarks["growth"]:
                    business_value = metrics["growth"][key]
                    benchmark_value = benchmarks["growth"][key]
                    growth_comparison[key] = {
                        "business_value": business_value,
                        "benchmark_value": benchmark_value,
                        "difference": business_value - benchmark_value if isinstance(business_value, (int, float)) else "N/A",
                        "performance": "Above Average" if business_value > benchmark_value else "Below Average" if business_value < benchmark_value else "Average"
                    }
            comparisons["growth"] = growth_comparison
        
        return comparisons

    def _generate_benchmark_recommendations(self, comparisons: Dict) -> List[str]:
        """Generate recommendations based on benchmark comparisons."""
        recommendations = []
        
        # Financial recommendations
        if "financial" in comparisons:
            for metric, data in comparisons["financial"].items():
                if data["performance"] == "Below Average":
                    if metric == "revenue":
                        recommendations.append(f"Consider strategies to increase revenue streams, such as expanding product lines or entering new markets")
                    elif metric == "profit_margin":
                        recommendations.append(f"Focus on improving profit margins through cost optimization and pricing strategies")
                    elif metric == "operating_costs":
                        recommendations.append(f"Review and optimize operational costs to align with industry standards")
        
        # Operational recommendations
        if "operational" in comparisons:
            for metric, data in comparisons["operational"].items():
                if data["performance"] == "Below Average":
                    if metric == "customer_satisfaction":
                        recommendations.append(f"Implement customer feedback programs to improve satisfaction scores")
                    elif metric == "employee_satisfaction":
                        recommendations.append(f"Review employee engagement initiatives and workplace culture")
                    elif metric == "project_completion_rate":
                        recommendations.append(f"Analyze project management processes for efficiency improvements")
        
        # Growth recommendations
        if "growth" in comparisons:
            for metric, data in comparisons["growth"].items():
                if data["performance"] == "Below Average":
                    if metric == "revenue_growth":
                        recommendations.append(f"Develop strategies to accelerate revenue growth through market expansion")
                    elif metric == "customer_growth":
                        recommendations.append(f"Focus on customer acquisition and retention strategies")
                    elif metric == "market_share_growth":
                        recommendations.append(f"Consider competitive positioning and market penetration strategies")
        
        return recommendations if recommendations else ["Maintain current performance levels and monitor industry trends"]

    async def _generate_competitive_insights(self, business, competitors) -> Dict:
        """Generate AI-powered competitive insights."""
        prompt = f"""Analyze the competitive position for a {business.industry} business in {business.state}, considering:
        1. Market opportunities
        2. Competitive threats
        3. Strategic recommendations"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a business strategy expert."},
                {"role": "user", "content": prompt}
            ]
        )

        return self._parse_insights(response.choices[0].message.content)

    def _parse_insights(self, content: str) -> Dict:
        """Parse competitive insights from OpenAI response."""
        # In a real implementation, this would use NLP to extract structured insights
        # For now, returning a simplified structure
        return {
            "opportunities": [
                "Opportunity 1 from analysis",
                "Opportunity 2 from analysis"
            ],
            "threats": [
                "Threat 1 from analysis",
                "Threat 2 from analysis"
            ],
            "recommendations": [
                "Strategic recommendation 1",
                "Strategic recommendation 2"
            ]
        }

    async def generate_funding_opportunities(self, business_id: int) -> Dict:
        """Generate funding opportunities analysis based on business type."""
        business = self.session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        prompt = f"""Analyze funding opportunities for a {business.industry} {'non-profit' if business.is_nonprofit else 'for-profit'} organization in {business.state}.
        Consider:
        1. {"Grants and charitable foundations" if business.is_nonprofit else "Venture capital and angel investors"}
        2. {"Individual donor strategies" if business.is_nonprofit else "Bank loans and credit lines"}
        3. {"Corporate sponsorships" if business.is_nonprofit else "Revenue-based financing"}
        4. Crowdfunding opportunities
        5. Tax implications and benefits"""

        response = await self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial advisor specializing in organizational funding."},
                {"role": "user", "content": prompt}
            ]
        )

        return self._parse_funding_opportunities(response.choices[0].message.content)

    def _parse_funding_opportunities(self, content: str) -> Dict:
        """Parse funding opportunities from OpenAI response."""
        return {
            "primary_sources": [
                "Source 1 from analysis",
                "Source 2 from analysis"
            ],
            "requirements": {
                "documentation": ["Required document 1", "Required document 2"],
                "qualifications": ["Qualification 1", "Qualification 2"]
            },
            "estimated_amounts": {
                "minimum": "Based on analysis",
                "maximum": "Based on analysis"
            },
            "timeline": {
                "application_period": "Typical duration",
                "review_process": "Expected timeline"
            },
            "recommendations": [
                "Strategic recommendation 1",
                "Strategic recommendation 2"
            ]
        }
