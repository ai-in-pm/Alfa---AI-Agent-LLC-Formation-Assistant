from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List
from models import Business, FinancialRecord
from sqlalchemy import func

class FinancialForecastingService:
    def __init__(self, db_session):
        self.db_session = db_session

    def generate_financial_forecast(self, business_id: int, months: int = 12) -> Dict:
        """Generate financial forecasts for the specified number of months."""
        business = self.db_session.query(Business).get(business_id)
        if not business:
            raise ValueError("Business not found")

        # Get historical data
        historical_data = self._get_historical_data(business_id)
        
        # Generate forecasts
        revenue_forecast = self._forecast_revenue(historical_data, months)
        expense_forecast = self._forecast_expenses(historical_data, months)
        cash_flow_forecast = self._forecast_cash_flow(revenue_forecast, expense_forecast)
        
        return {
            'revenue_forecast': revenue_forecast,
            'expense_forecast': expense_forecast,
            'cash_flow_forecast': cash_flow_forecast,
            'metrics': self._calculate_financial_metrics(revenue_forecast, expense_forecast)
        }

    def _get_historical_data(self, business_id: int) -> Dict:
        """Retrieve and organize historical financial data."""
        # Get the last 12 months of data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)

        records = self.db_session.query(
            FinancialRecord
        ).filter(
            FinancialRecord.business_id == business_id,
            FinancialRecord.date >= start_date
        ).all()

        # Organize data by type and month
        data = {
            'revenue': self._organize_monthly_data(
                [r for r in records if r.type == 'revenue']
            ),
            'expenses': self._organize_monthly_data(
                [r for r in records if r.type == 'expense']
            ),
            'cash_flow': self._organize_monthly_data(
                [r for r in records if r.type in ['revenue', 'expense']]
            )
        }

        return data

    def _organize_monthly_data(self, records: List[FinancialRecord]) -> Dict:
        """Organize financial records by month."""
        monthly_data = {}
        for record in records:
            month_key = record.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            # Add revenue, subtract expenses
            modifier = 1 if record.type == 'revenue' else -1
            monthly_data[month_key] += record.amount * modifier
        return monthly_data

    def _forecast_revenue(self, historical_data: Dict, months: int) -> List[Dict]:
        """Generate revenue forecasts using time series analysis."""
        revenue_data = list(historical_data['revenue'].values())
        
        # Calculate trend and seasonality
        if len(revenue_data) >= 12:
            trend = np.polyfit(range(len(revenue_data)), revenue_data, 1)
            seasonal_factors = self._calculate_seasonal_factors(revenue_data)
        else:
            # If less than 12 months of data, use simpler projection
            trend = [np.mean(revenue_data), 0] if revenue_data else [0, 0]
            seasonal_factors = [1.0] * 12

        # Generate forecasts
        forecasts = []
        last_month = datetime.utcnow()
        
        for i in range(months):
            forecast_month = last_month + timedelta(days=30 * (i + 1))
            month_index = forecast_month.month - 1
            
            # Calculate forecasted value
            trend_value = trend[0] * (len(revenue_data) + i) + trend[1]
            seasonal_value = trend_value * seasonal_factors[month_index]
            
            forecasts.append({
                'date': forecast_month.strftime('%Y-%m'),
                'amount': max(0, seasonal_value),  # Ensure non-negative
                'growth_rate': self._calculate_growth_rate(
                    revenue_data[-1] if revenue_data else 0,
                    seasonal_value
                )
            })

        return forecasts

    def _forecast_expenses(self, historical_data: Dict, months: int) -> List[Dict]:
        """Generate expense forecasts."""
        expense_data = list(historical_data['expenses'].values())
        
        # Calculate fixed and variable expenses
        if expense_data:
            fixed_expenses = min(expense_data)  # Assume minimum is fixed
            variable_ratio = np.mean([
                (total - fixed_expenses) / total 
                for total in expense_data if total > fixed_expenses
            ]) if any(e > fixed_expenses for e in expense_data) else 0
        else:
            fixed_expenses = 0
            variable_ratio = 0

        # Generate forecasts
        forecasts = []
        last_month = datetime.utcnow()

        for i in range(months):
            forecast_month = last_month + timedelta(days=30 * (i + 1))
            
            # Estimate expenses based on revenue forecast
            revenue_forecast = self._forecast_revenue(historical_data, i + 1)[-1]['amount']
            variable_expenses = revenue_forecast * variable_ratio
            total_expenses = fixed_expenses + variable_expenses

            forecasts.append({
                'date': forecast_month.strftime('%Y-%m'),
                'amount': total_expenses,
                'breakdown': {
                    'fixed': fixed_expenses,
                    'variable': variable_expenses
                }
            })

        return forecasts

    def _forecast_cash_flow(self, revenue_forecast: List[Dict], expense_forecast: List[Dict]) -> List[Dict]:
        """Generate cash flow forecasts."""
        cash_flow = []
        
        for i in range(len(revenue_forecast)):
            month_revenue = revenue_forecast[i]['amount']
            month_expenses = expense_forecast[i]['amount']
            
            cash_flow.append({
                'date': revenue_forecast[i]['date'],
                'net_cash_flow': month_revenue - month_expenses,
                'revenue': month_revenue,
                'expenses': month_expenses
            })

        return cash_flow

    def _calculate_seasonal_factors(self, data: List[float]) -> List[float]:
        """Calculate seasonal factors from historical data."""
        if len(data) < 12:
            return [1.0] * 12

        # Calculate average value for each month
        monthly_avgs = []
        for i in range(12):
            month_values = data[i::12]
            monthly_avgs.append(np.mean(month_values) if month_values else 1.0)

        # Normalize factors
        overall_avg = np.mean(monthly_avgs)
        seasonal_factors = [m / overall_avg for m in monthly_avgs]

        return seasonal_factors

    def _calculate_growth_rate(self, previous: float, current: float) -> float:
        """Calculate growth rate between two values."""
        if previous == 0:
            return 0
        return (current - previous) / previous

    def _calculate_financial_metrics(self, revenue_forecast: List[Dict], expense_forecast: List[Dict]) -> Dict:
        """Calculate key financial metrics from forecasts."""
        total_revenue = sum(f['amount'] for f in revenue_forecast)
        total_expenses = sum(f['amount'] for f in expense_forecast)
        
        return {
            'projected_profit_margin': (total_revenue - total_expenses) / total_revenue if total_revenue > 0 else 0,
            'average_monthly_revenue': total_revenue / len(revenue_forecast),
            'average_monthly_expenses': total_expenses / len(expense_forecast),
            'breakeven_months': next(
                (i for i, (r, e) in enumerate(zip(revenue_forecast, expense_forecast))
                 if r['amount'] > e['amount']),
                None
            )
        }

    def generate_financial_scenarios(self, business_id: int, months: int = 12) -> Dict:
        """Generate optimistic, pessimistic, and realistic financial scenarios."""
        base_forecast = self.generate_financial_forecast(business_id, months)
        
        scenarios = {
            'optimistic': self._adjust_forecast(base_forecast, 1.2, 0.9),
            'realistic': base_forecast,
            'pessimistic': self._adjust_forecast(base_forecast, 0.8, 1.1)
        }
        
        return scenarios

    def _adjust_forecast(self, forecast: Dict, revenue_multiplier: float, expense_multiplier: float) -> Dict:
        """Adjust forecasts for different scenarios."""
        adjusted = {
            'revenue_forecast': [
                {**f, 'amount': f['amount'] * revenue_multiplier}
                for f in forecast['revenue_forecast']
            ],
            'expense_forecast': [
                {**f, 'amount': f['amount'] * expense_multiplier}
                for f in forecast['expense_forecast']
            ]
        }
        
        # Recalculate cash flow and metrics
        adjusted['cash_flow_forecast'] = self._forecast_cash_flow(
            adjusted['revenue_forecast'],
            adjusted['expense_forecast']
        )
        adjusted['metrics'] = self._calculate_financial_metrics(
            adjusted['revenue_forecast'],
            adjusted['expense_forecast']
        )
        
        return adjusted
