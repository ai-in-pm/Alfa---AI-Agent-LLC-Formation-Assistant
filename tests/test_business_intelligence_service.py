import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from services.business_intelligence_service_v2 import EnhancedBusinessIntelligenceService
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

class TestEnhancedBusinessIntelligenceService(unittest.TestCase):
    def setUp(self):
        self.db_session = Mock()
        self.service = EnhancedBusinessIntelligenceService(self.db_session)
        # Set up mock data for reuse across tests
        self.mock_business = Mock(
            id=1,
            name="Test LLC",
            industry="Technology",
            state="DE",
            formation_date=datetime.now() - timedelta(days=365)
        )
        self.db_session.query.return_value.get.return_value = self.mock_business

    def test_prepare_segmentation_features(self):
        # Create sample transaction data
        transactions = [
            {
                "customer_id": 1,
                "amount": 100,
                "date": datetime.now() - pd.Timedelta(days=10)
            },
            {
                "customer_id": 1,
                "amount": 150,
                "date": datetime.now() - pd.Timedelta(days=5)
            },
            {
                "customer_id": 2,
                "amount": 200,
                "date": datetime.now() - pd.Timedelta(days=1)
            }
        ]

        features = self.service._prepare_segmentation_features(transactions)

        # Basic assertions for RFM features
        self.assertIsInstance(features, pd.DataFrame)
        self.assertEqual(len(features.columns), 3)  # RFM features
        self.assertIn('recency', features.columns)
        self.assertIn('frequency', features.columns)
        self.assertIn('monetary', features.columns)
        
        # Test specific values
        self.assertEqual(len(features), 2)  # Two unique customers
        # All features should be normalized between 0 and 1
        self.assertTrue((features >= 0).all().all())
        self.assertTrue((features <= 1).all().all())

    def test_cluster_customers(self):
        # Create sample features with more realistic data
        features = pd.DataFrame({
            'recency': [1, 2, 3, 10],
            'frequency': [10, 8, 6, 4],
            'monetary': [1000, 800, 600, 400]
        })

        # Perform clustering
        clusters = self.service._cluster_customers(features)

        # Enhanced assertions
        self.assertIsInstance(clusters, list)
        self.assertTrue(len(clusters) > 0)
        self.assertTrue(len(clusters) <= min(5, len(features)))  # Max 5 clusters
        
        for cluster in clusters:
            self.assertIn('segment_id', cluster)
            self.assertIn('size', cluster)
            self.assertIn('avg_recency', cluster)
            self.assertIn('avg_frequency', cluster)
            self.assertIn('avg_monetary', cluster)
            
            # Value range checks
            self.assertTrue(0 <= cluster['size'] <= len(features))
            self.assertIsInstance(cluster['avg_recency'], (float, np.floating))
            self.assertIsInstance(cluster['avg_frequency'], (float, np.floating))
            self.assertIsInstance(cluster['avg_monetary'], (float, np.floating))

    def test_analyze_business_performance(self):
        # Mock financial data
        mock_financials = {
            'revenue': 1000000,
            'expenses': 800000,
            'profit_margin': 0.2,
            'operating_costs': 600000,
            'marketing_costs': 100000,
            'admin_costs': 100000
        }
        
        mock_growth = {
            'revenue_growth': 0.15,
            'customer_growth': 0.1,
            'market_share_growth': 0.05
        }
        
        mock_efficiency = {
            'operational_efficiency': 0.85,
            'resource_utilization': 0.75,
            'employee_productivity': 0.9
        }

        self.service._get_financial_metrics = Mock(return_value=mock_financials)
        self.service._calculate_growth_rates = Mock(return_value=mock_growth)
        self.service._analyze_efficiency = Mock(return_value=mock_efficiency)

        result = self.service._analyze_business_performance(1)

        # Basic assertions
        self.assertIn('financials', result)
        self.assertIn('growth_rates', result)
        self.assertIn('efficiency', result)
        
        # Detailed financial metrics
        self.assertEqual(result['financials']['revenue'], 1000000)
        self.assertEqual(result['financials']['profit_margin'], 0.2)
        self.assertTrue(0 <= result['efficiency']['operational_efficiency'] <= 1)

    def test_assess_financial_risks(self):
        # Mock financial metrics
        mock_metrics = {
            'cash_flow_ratio': 0.8,
            'debt_to_equity': 2.5,
            'current_ratio': 1.2,
            'quick_ratio': 0.9,
            'operating_margin': 0.15,
            'debt_service_coverage': 1.5
        }

        self.service._get_financial_metrics = Mock(return_value=mock_metrics)

        risks = self.service._assess_financial_risks(1)

        # Enhanced assertions
        self.assertIsInstance(risks, list)
        self.assertTrue(len(risks) > 0)
        
        risk_types = set()
        for risk in risks:
            self.assertIn('type', risk)
            self.assertIn('severity', risk)
            self.assertIn('description', risk)
            self.assertIn('metrics', risk)
            
            # Collect risk types
            risk_types.add(risk['type'])
            
            # Verify severity is one of expected values
            self.assertIn(risk['severity'], ['low', 'medium', 'high'])
            
            # Verify metrics are present
            self.assertTrue(len(risk['metrics']) > 0)

        # Verify we're checking multiple types of risks
        self.assertTrue(len(risk_types) >= 1)

    def test_generate_competitive_analysis(self):
        async def _test():
            # Mock market data
            mock_market_data = {
                "overview": {
                    "market_size": "$500M",
                    "growth_rate": "15%",
                    "trends": ["Digital transformation", "Sustainability"]
                },
                "competitors": [
                    {
                        "name": "Company A",
                        "strengths": ["Market leader", "Strong brand"],
                        "weaknesses": ["High costs", "Legacy systems"]
                    }
                ]
            }
            
            # Create async mock for _generate_competitive_insights
            mock_insights = {
                "opportunities": ["Market expansion", "New products"],
                "threats": ["Increasing competition", "Regulatory changes"],
                "recommendations": ["Focus on innovation", "Build partnerships"]
            }
            async_mock = AsyncMock(return_value=mock_insights)
            self.service._generate_competitive_insights = async_mock

            # Mock the non-async methods
            self.service._gather_market_data = Mock(return_value=mock_market_data)
            self.service._analyze_competitors = Mock(return_value=mock_market_data["competitors"])

            result = await self.service.generate_competitive_analysis(1)
            return result

        result = run_async_test(_test())
        
        # Enhanced assertions
        self.assertIn('market_overview', result)
        self.assertIn('competitors', result)
        self.assertIn('opportunities', result)
        self.assertIn('threats', result)
        self.assertIn('recommendations', result)

    def test_generate_industry_benchmarks(self):
        async def _test():
            # Mock business metrics and benchmarks
            mock_metrics = {
                "financial": {
                    "revenue": 1000000,
                    "profit_margin": 0.15
                },
                "operational": {
                    "efficiency": 0.85,
                    "productivity": 0.9
                }
            }
            
            mock_benchmarks = {
                "financial": {
                    "avg_revenue": 900000,
                    "avg_profit_margin": 0.12
                },
                "operational": {
                    "avg_efficiency": 0.8,
                    "avg_productivity": 0.85
                }
            }

            # Create async mock for _get_industry_benchmarks
            async_mock = AsyncMock(return_value=mock_benchmarks)
            self.service._get_industry_benchmarks = async_mock

            # Mock non-async methods
            self.service._get_business_metrics = Mock(return_value=mock_metrics)
            self.service._compare_with_benchmarks = Mock(return_value={
                "financial": {"revenue": "above_average", "profit_margin": "above_average"},
                "operational": {"efficiency": "above_average", "productivity": "above_average"}
            })
            self.service._generate_benchmark_recommendations = Mock(return_value=[
                "Maintain strong financial performance",
                "Continue operational excellence"
            ])

            result = await self.service.generate_industry_benchmarks(1)
            return result

        result = run_async_test(_test())
        
        # Enhanced assertions
        self.assertIn('business_metrics', result)
        self.assertIn('industry_benchmarks', result)
        self.assertIn('comparison', result)
        self.assertIn('recommendations', result)

def run_async_test(coro):
    return asyncio.run(coro)

if __name__ == '__main__':
    unittest.main()
