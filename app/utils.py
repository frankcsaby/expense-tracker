from datetime import datetime, timedelta
from app.config import CURRENCIES, DEFAULT_CURRENCY, DATE_FORMAT

def get_date_range(period):
    """Get date range based on period."""
    today = datetime.now().date()
    
    if period == 'week':
        start_date = (today - timedelta(days=7)).strftime(DATE_FORMAT)
    elif period == 'month':
        start_date = (today - timedelta(days=30)).strftime(DATE_FORMAT)
    elif period == 'year':
        start_date = (today - timedelta(days=365)).strftime(DATE_FORMAT)
    else:  # all
        start_date = None
    
    end_date = today.strftime(DATE_FORMAT)
    
    return {
        'from_date': start_date,
        'to_date': end_date
    }

def format_currency(amount, currency_code=None):
    """Format amount with currency symbol."""
    if currency_code is None:
        currency_code = DEFAULT_CURRENCY
    
    currency = CURRENCIES.get(currency_code, CURRENCIES[DEFAULT_CURRENCY])
    return f"{currency['symbol']}{amount:.2f}"

def parse_tags(tags_str):
    """Parse tags string into list of tags."""
    if not tags_str:
        return []
    
    return [tag.strip() for tag in tags_str.split(',') if tag.strip()]

def get_chart_colors(count):
    """Get a list of chart colors."""
    base_colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#6f42c1', '#5a5c69', '#858796', '#2e59d9', '#17a673'
    ]
    
    # Repeat colors if more than 10 items
    colors = []
    for i in range(count):
        colors.append(base_colors[i % len(base_colors)])
    
    return colors

def calculate_recurring_dates(base_date, interval, count=12):
    """Calculate future recurring dates from base date."""
    try:
        base_date = datetime.strptime(base_date, DATE_FORMAT).date()
    except ValueError:
        return []
    
    dates = []
    current_date = base_date
    
    for _ in range(count):
        if interval == 'weekly':
            current_date = current_date + timedelta(days=7)
        elif interval == 'monthly':
            # Add a month (approximately handling month boundaries)
            month = current_date.month + 1
            year = current_date.year
            
            if month > 12:
                month = 1
                year += 1
            
            # Handle different month lengths
            day = min(current_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
            
            current_date = current_date.replace(year=year, month=month, day=day)
        elif interval == 'yearly':
            current_date = current_date.replace(year=current_date.year + 1)
        
        dates.append(current_date.strftime(DATE_FORMAT))
    
    return dates 