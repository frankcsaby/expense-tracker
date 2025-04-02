# Expense Tracker (Refactored)

A simple expense tracker web application that helps you track and manage your personal expenses.

## Key Features

- Track expenses with descriptions, amounts, categories, and dates
- Tag expenses for better organization
- Set budgets by category
- View analytics and reports
- Multiple currency support
- Dark/light theme toggle

## Code Improvements

The application has been refactored to follow better software engineering practices:

1. **Modular Architecture**: Code is now organized into modules following MVC pattern:
   - Models: Database operations and business logic
   - Controllers: Request handling and routing
   - Templates: View rendering

2. **Separation of Concerns**:
   - Database operations isolated in models
   - Configuration moved to separate module
   - Utility functions extracted to utils.py

3. **Improved Error Handling**: Consistent validation and error responses

4. **Optimized Database Queries**: Reduced redundant database calls

5. **Code Reusability**: Common operations extracted to reusable functions

## Project Structure

```
expense-tracker/
├── app/
│   ├── __init__.py           # Application factory
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database connection and initialization
│   ├── utils.py              # Utility functions
│   ├── models/               # Data models
│   │   ├── expense.py        # Expense model
│   │   ├── budget.py         # Budget model
│   │   └── tag.py            # Tag model
│   ├── controllers/          # Route controllers
│   │   ├── expense_controller.py
│   │   ├── analytics_controller.py
│   │   ├── budget_controller.py
│   │   └── settings_controller.py
│   ├── templates/            # HTML templates
│   └── static/               # Static assets (CSS, JS)
├── run.py                    # Application entry point
├── requirements.txt          # Project dependencies
└── expenses.db               # SQLite database
```

## Installation

1. Ensure you have Python installed
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python run.py`
4. Access the application at http://localhost:5000

## Future Improvements

- User authentication
- Data export/import
- Mobile app support
- Receipt scanning
- Budget alerts 