# Expense Tracker

A comprehensive personal finance management application built with Python Flask that helps you track expenses, manage budgets, set savings goals, and analyze spending patterns.

![Expense Tracker Dashboard](screenshots/dashboard.jpg)

## Features

### Expense Management
- **Track Expenses**: Log your daily expenses with categories, descriptions, and dates
- **Filter & Search**: Easily find expenses by category, date range, or keywords
- **Mobile Responsive**: Fully optimized for desktop and mobile use
- **Expense History**: View complete spending history with detailed information

### Budget Tracking
- **Create Budgets**: Set budgets for different spending categories
- **Budget Periods**: Choose weekly, monthly, or yearly budgets
- **Visual Progress**: See your spending against budget limits with progress bars
- **Budget Alerts**: Get warnings when approaching or exceeding budget limits

### Savings Goals
- **Goal Setting**: Create savings goals with target amounts and dates
- **Progress Tracking**: Monitor your progress towards each goal
- **Status Updates**: Update your current savings amount as you progress

### Income Tracking
- **Log Income**: Record income from multiple sources
- **Income Analysis**: View breakdowns of income sources and trends
- **Recurring Income**: Track regular income payments

### Spending Predictions
- **AI-Powered Analysis**: Forecasts future spending based on historical patterns
- **Category Breakdown**: Predicts spending by category
- **Monthly Projections**: Plan ahead with monthly spending forecasts

### Analytics & Reports
- **Spending Trends**: Visualize your spending patterns over time
- **Category Analysis**: See where your money goes with category breakdowns
- **Comparison Reports**: Compare spending across different time periods
- **Data Export**: Download reports for tax or budgeting purposes

### Customization
- **Currency Settings**: Choose from multiple currency options
- **Theme Toggle**: Switch between light and dark modes
- **Personalized Dashboard**: Focus on the financial data that matters to you

## Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.jpg)
The main dashboard shows your recent expenses, spending summary, and quick access to all features.

### Expense Management
![Expense Management](screenshots/expenses.jpg)
Add, edit, and filter expenses with an intuitive interface.

### Budget Tracking
![Budget Tracking](screenshots/budgets.jpg)
Set and monitor budgets with visual indicators of your spending limits.

### Analytics
![Analytics](screenshots/analytics.jpg)
Visualize your spending patterns with interactive charts and graphs.

### Savings Goals
![Savings Goals](screenshots/savings.jpg)
Set financial goals and track your progress over time.

### Spending Predictor
![Spending Predictor](screenshots/predictor.jpg)
Get AI-powered predictions about your future spending based on historical data.

> **Note about screenshots**: The screenshots shown here are placeholders. You can capture your own screenshots of the application running on your system and place them in the `screenshots` directory to personalize this README.

## Getting Started

### Prerequisites
- Python 3.8+
- SQLite database

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/expense-tracker.git
   cd expense-tracker
   ```

2. Set up a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python app.py
   ```

5. Access the application:
   Open your browser and navigate to `http://127.0.0.1:5000`

## Usage Guide

### Adding an Expense
1. Click the "Add Expense" button in the navigation bar
2. Fill in the expense details (amount, category, description, date)
3. Click "Save" to record your expense

### Setting Up Budgets
1. Navigate to the Budgets section
2. Select a category and enter your budget amount
3. Choose the budget period (weekly, monthly, yearly)
4. Click "Save Budget" to create or update your budget

### Creating Savings Goals
1. Go to the Savings section
2. Click "Add New Goal"
3. Enter goal details (name, target amount, target date)
4. Monitor and update your progress as you save

### Using the Spending Predictor
1. Visit the Predictor section
2. The system automatically analyzes your past expenses
3. View predicted future spending by category
4. Use insights to adjust your budgets and spending habits

## Technical Details

### Technology Stack
- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Charts**: Chart.js
- **Icons**: Bootstrap Icons

### Database Schema
The application uses the following key tables:
- `expenses`: Stores all expense records
- `budgets`: Manages budget settings by category
- `savings_goals`: Tracks savings goals and progress
- `income_entries`: Records income from various sources

### Key Features Implementation
- **Theme Toggle**: Uses browser cookies to persist user preference
- **Responsive Design**: Bootstrap combined with custom CSS for all screen sizes
- **Data Visualization**: Chart.js for interactive, responsive charts
- **Spending Prediction**: Algorithm analyzes spending patterns over 6 months

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bootstrap for the responsive UI framework
- Chart.js for beautiful data visualizations
- The Flask team for the lightweight web framework
- All contributors who have helped improve the application
