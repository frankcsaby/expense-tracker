import os

# Application configuration
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
DATABASE_PATH = 'expenses.db'

# Available currencies
CURRENCIES = {
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar'},
    'HUF': {'symbol': 'Ft', 'name': 'Hungarian Forint'}
}

# Default currency
DEFAULT_CURRENCY = 'HUF'

# Predefined categories
EXPENSE_CATEGORIES = [
    'Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment',
    'Healthcare', 'Education', 'Shopping', 'Travel', 'Miscellaneous'
]

# Date format
DATE_FORMAT = '%Y-%m-%d'

# Budget periods
BUDGET_PERIODS = ['daily', 'weekly', 'monthly', 'yearly']

# Recurring intervals
RECURRING_INTERVALS = ['weekly', 'monthly', 'yearly'] 