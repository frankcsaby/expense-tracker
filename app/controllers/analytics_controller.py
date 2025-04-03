from flask import Blueprint, render_template, request, session
from app.models.expense import Expense
from app.models.budget import Budget
from app.config import CURRENCIES, DEFAULT_CURRENCY
from app.utils import get_date_range

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics')
def index():
    """Analytics page with expense charts and statistics."""
    # Get filter parameters
    period = request.args.get('period', 'month')
    chart_type = request.args.get('chart_type', 'category')
    
    # Get date range based on period
    date_range = get_date_range(period)
    
    # Get expense statistics
    stats = Expense.get_statistics(date_range)
    
    # Get top expenses for the period
    with_filters = Expense.get_all(date_range, 'amount DESC')
    top_expenses = with_filters[:5] if with_filters else []
    
    # Get category totals for the period
    category_totals = Expense.get_category_totals(date_range)
    
    # Get budget comparison
    budget_comparison = Budget.get_comparison(date_range)
    
    # Get current currency
    currency_code = session.get('currency', DEFAULT_CURRENCY)
    currency = CURRENCIES[currency_code]
    
    # Create chart data based on chart type
    chart_data = {}
    if chart_type == 'category':
        # Category chart
        labels = [item['category'] for item in category_totals]
        data = [round(float(item['total']), 2) for item in category_totals]
        
        chart_data = {
            'labels': labels,
            'data': data
        }
    else:
        # Time chart - would need to implement time-based grouping
        # This is a placeholder and should be implemented based on requirements
        chart_data = {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'data': [100, 150, 200, 175, 225, 250]
        }
    
    return render_template('analytics.html',
                          stats=stats,
                          top_expenses=top_expenses,
                          category_totals=category_totals,
                          budget_comparison=budget_comparison,
                          chart_data=chart_data,
                          period=period,
                          chart_type=chart_type,
                          currency=currency,
                          currency_code=currency_code)

@analytics_bp.route('/reports')
def reports():
    """Reports page for generating expense reports."""
    # Get filter parameters
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    grouping = request.args.get('grouping', 'month')  # month, week, category
    
    # Create filters
    filters = {}
    if from_date:
        filters['from_date'] = from_date
    if to_date:
        filters['to_date'] = to_date
    
    # Get report data based on grouping
    # Implementation depends on requirements, this is a placeholder
    report_data = []
    report_type = 'Monthly'
    
    # Get current currency
    currency_code = session.get('currency', DEFAULT_CURRENCY)
    currency = CURRENCIES[currency_code]
    
    return render_template('reports.html',
                          report_data=report_data,
                          report_type=report_type,
                          from_date=from_date,
                          to_date=to_date,
                          grouping=grouping,
                          currency=currency,
                          currency_code=currency_code) 