from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, g
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import sqlite3
from functools import wraps
import os
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import Babel
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
babel = Babel(app)

# Import models after db initialization
from app.models import Expense, Budget, SavingsGoal, IncomeEntry

app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

# Available currencies
CURRENCIES = {
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar'},
    'HUF': {'symbol': 'Ft', 'name': 'Hungarian Forint'}
}

# Predefined categories
EXPENSE_CATEGORIES = [
    'Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment',
    'Healthcare', 'Education', 'Shopping', 'Travel', 'Miscellaneous'
]

# Before request handler to setup currency
@app.before_request
def before_request():
    # Set default currency if not already set
    if 'currency' not in session:
        session['currency'] = 'HUF'
    
    # Ensure currency exists in our CURRENCIES dict
    if session.get('currency') not in CURRENCIES:
        session['currency'] = 'HUF'
    
    # Make currency info available globally
    g.currency_code = session.get('currency')
    g.currency = CURRENCIES[g.currency_code]

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")

# Validation
def validate_expense(form_data):
    errors = []
    
    # Description validation
    if not form_data.get('description') or len(form_data.get('description', '').strip()) < 2:
        errors.append('Description must be at least 2 characters long')
    
    # Amount validation
    try:
        amount = float(form_data.get('amount', 0))
        if amount <= 0:
            errors.append('Amount must be greater than zero')
    except ValueError:
        errors.append('Amount must be a valid number')
    
    # Category validation
    if not form_data.get('category'):
        errors.append('Category is required')
    
    # Date validation
    try:
        date_str = form_data.get('date', '')
        if date_str:
            datetime.strptime(date_str, '%Y-%m-%d')
        else:
            errors.append('Date is required')
    except ValueError:
        errors.append('Invalid date format')
    
    return errors

# Home page
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    tag_filter = request.args.get('tag', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Construct base query
    if tag_filter:
        # If tag filter is active, we need to join with tags
        query = '''
            SELECT e.* FROM expenses e
            JOIN expense_tags et ON e.id = et.expense_id
            JOIN tags t ON et.tag_id = t.id
            WHERE t.name = ?
        '''
        params = [tag_filter]
    else:
        query = 'SELECT * FROM expenses WHERE 1=1'
        params = []
    
    # Add search filter
    if search_query:
        query += ' AND description LIKE ?'
        params.append(f'%{search_query}%')
    
    # Add category filter
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    
    # Add date range filters
    if from_date:
        query += ' AND date >= ?'
        params.append(from_date)
    
    if to_date:
        query += ' AND date <= ?'
        params.append(to_date)
    
    query += ' ORDER BY date DESC'
    
    with get_db() as conn:
        expenses = conn.execute(query, params).fetchall()
        # Get total expenses
        total_expenses = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
        
        # Get available categories for the filter dropdown
        categories = conn.execute('SELECT DISTINCT category FROM expenses').fetchall()
        categories = [c['category'] for c in categories] + [c for c in EXPENSE_CATEGORIES if c not in categories]
    
    # Get all available tags for the filter dropdown
    tags = []
    with get_db() as conn:
        tag_rows = conn.execute('SELECT name FROM tags ORDER BY name').fetchall()
        tags = [t['name'] for t in tag_rows]
    
    # Get current currency (default to USD)
        currency_code = session.get('currency', 'HUF')
    currency = CURRENCIES[currency_code]
    
    return render_template('index.html', 
                          expenses=expenses, 
                          total=total_expenses['total'] if total_expenses['total'] else 0,
                          categories=sorted(set(categories)),
                          tags=tags,
                          search_query=search_query,
                          category_filter=category_filter,
                          tag_filter=tag_filter,
                          from_date=from_date,
                          to_date=to_date,
                          currency=currency,
                          currency_code=currency_code)

# Add expense
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        # Validate form data
        errors = validate_expense(request.form)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('add_expense.html', 
                                  form_data=request.form, 
                                  categories=EXPENSE_CATEGORIES)
        
        # Get form data
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        
        # Handle recurring expenses
        recurring = 1 if request.form.get('recurring') else 0
        recurring_interval = request.form.get('recurring_interval') if recurring else None
        
        # Handle tags
        tags = request.form.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        with get_db() as conn:
            # Insert expense
            cursor = conn.execute(
                'INSERT INTO expenses (description, amount, category, date, recurring, recurring_interval) VALUES (?, ?, ?, ?, ?, ?)',
                (description, amount, category, date, recurring, recurring_interval)
            )
            
            # Handle tags if provided
            if tags:
                expense_id = cursor.lastrowid
                
                for tag_name in tags:
                    # Check if tag exists
                    tag = conn.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                    
                    if tag:
                        tag_id = tag['id']
                    else:
                        # Create new tag
                        cursor = conn.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                        tag_id = cursor.lastrowid
                    
                    # Create relationship
                    conn.execute('INSERT INTO expense_tags (expense_id, tag_id) VALUES (?, ?)', 
                               (expense_id, tag_id))
            
            conn.commit()
            flash('Expense added successfully!', 'success')
            
        return redirect(url_for('index'))

    return render_template('add_expense.html', categories=EXPENSE_CATEGORIES)

# Edit expense
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    with get_db() as conn:
        expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
        
        if not expense:
            flash('Expense not found!', 'danger')
            return redirect(url_for('index'))
        
        # Get tags for this expense
        tag_rows = conn.execute('''
            SELECT t.name 
            FROM tags t 
            JOIN expense_tags et ON t.id = et.tag_id 
            WHERE et.expense_id = ?
        ''', (id,)).fetchall()
        
        tags = [tag['name'] for tag in tag_rows]
        
        if request.method == 'POST':
            # Validate form data
            errors = validate_expense(request.form)
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template('edit_expense.html', 
                                      expense=expense, 
                                      tags=','.join(tags),
                                      categories=EXPENSE_CATEGORIES)
            
            # Get form data
            description = request.form['description']
            amount = float(request.form['amount'])
            category = request.form['category']
            date = request.form['date']
            
            # Handle recurring expenses
            recurring = 1 if request.form.get('recurring') else 0
            recurring_interval = request.form.get('recurring_interval') if recurring else None
            
            # Update expense
            conn.execute('''
                UPDATE expenses
                SET description = ?, amount = ?, category = ?, date = ?, recurring = ?, recurring_interval = ?
                WHERE id = ?
            ''', (description, amount, category, date, recurring, recurring_interval, id))
            
            # Handle tags
            new_tags = request.form.get('tags', '').split(',')
            new_tags = [tag.strip() for tag in new_tags if tag.strip()]
            
            # Remove existing tags
            conn.execute('DELETE FROM expense_tags WHERE expense_id = ?', (id,))
            
            # Add new tags
            for tag_name in new_tags:
                # Check if tag exists
                tag = conn.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                
                if tag:
                    tag_id = tag['id']
                else:
                    # Create new tag
                    cursor = conn.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                    tag_id = cursor.lastrowid
                
                # Create relationship
                conn.execute('INSERT INTO expense_tags (expense_id, tag_id) VALUES (?, ?)', 
                           (id, tag_id))
            
            conn.commit()
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('index'))
        
        return render_template('edit_expense.html', 
                               expense=expense, 
                               tags=','.join(tags),
                               categories=EXPENSE_CATEGORIES)

# Delete expense
@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    with get_db() as conn:
        # Delete expense (foreign key constraints will handle expense_tags)
        conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
        conn.commit()
        flash('Expense deleted successfully!', 'success')
    
    return redirect(url_for('index'))

# Analytics page
@app.route('/analytics')
def analytics():
    period = request.args.get('period', 'all')
    chart_type = request.args.get('chart_type', 'category')
    
    with get_db() as conn:
        # Get current date and calculate time ranges
        today = datetime.today()
        
        # Prepare date filters based on period
        date_filters = {
            'week': today - timedelta(days=7),
            'month': today - timedelta(days=30),
            'year': today - timedelta(days=365),
            'all': None
        }
        
        selected_date = date_filters.get(period)
        date_clause = ''
        params = []
        
        if selected_date:
            date_clause = 'WHERE date >= ?'
            params.append(selected_date.strftime('%Y-%m-%d'))
        
        # Category breakdown
        category_totals = conn.execute(f'''
            SELECT category, SUM(amount) as total
            FROM expenses
            {date_clause}
            GROUP BY category
            ORDER BY total DESC
        ''', params).fetchall()
        
        # Monthly spending over time (for time-based charts)
        monthly_spending = conn.execute(f'''
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as total
            FROM expenses
            {date_clause}
            GROUP BY month
            ORDER BY month
        ''', params).fetchall()
        
        # Get top expenses
        top_expenses = conn.execute(f'''
            SELECT *
            FROM expenses
            {date_clause}
            ORDER BY amount DESC
            LIMIT 5
        ''', params).fetchall()
        
        # Get overall statistics
        stats = {}
        
        # Total expenses
        total_result = conn.execute(f'SELECT SUM(amount) as total FROM expenses {date_clause}', params).fetchone()
        stats['total'] = total_result['total'] if total_result['total'] else 0
        
        # Average expense
        avg_result = conn.execute(f'SELECT AVG(amount) as avg FROM expenses {date_clause}', params).fetchone()
        stats['average'] = avg_result['avg'] if avg_result['avg'] else 0
        
        # Highest expense
        max_result = conn.execute(f'SELECT MAX(amount) as max FROM expenses {date_clause}', params).fetchone()
        stats['max'] = max_result['max'] if max_result['max'] else 0
        
        # Count of expenses
        count_result = conn.execute(f'SELECT COUNT(*) as count FROM expenses {date_clause}', params).fetchone()
        stats['count'] = count_result['count'] if count_result['count'] else 0
        
        # Get budget comparison
        budgets = conn.execute('SELECT * FROM budgets').fetchall()
        budget_comparison = []
        
        for budget in budgets:
            category = budget['category']
            budget_amount = budget['amount']
            period = budget['period']
            
            # Calculate date range for budget period
            if period == 'monthly':
                start_date = today.replace(day=1).strftime('%Y-%m-%d')
            elif period == 'weekly':
                start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            elif period == 'yearly':
                start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')
            else:
                start_date = None
            
            # Get actual spending
            if start_date:
                spent_result = conn.execute('''
                    SELECT SUM(amount) as spent
                    FROM expenses
                    WHERE category = ? AND date >= ?
                ''', (category, start_date)).fetchone()
            else:
                spent_result = conn.execute('''
                    SELECT SUM(amount) as spent
                    FROM expenses
                    WHERE category = ?
                ''', (category,)).fetchone()
            
            spent = spent_result['spent'] if spent_result['spent'] else 0
            
            # Calculate percentage without limiting to 100%
            percentage = round((spent / budget_amount) * 100) if budget_amount > 0 else 0
            
            budget_comparison.append({
                'category': category,
                'budget': budget_amount,
                'spent': spent,
                'percentage': percentage,
                'period': period
            })
    
    # Get current currency (default to USD)
    currency_code = session.get('currency', 'HUF')
    currency = CURRENCIES[currency_code]
    
    return render_template('analytics.html',
                          category_totals=category_totals,
                          monthly_spending=monthly_spending,
                          top_expenses=top_expenses,
                          stats=stats,
                          period=period,
                          chart_type=chart_type,
                          budget_comparison=budget_comparison,
                          currency=currency,
                          currency_code=currency_code)

# Manage budgets
@app.route('/budgets', methods=['GET', 'POST'])
def manage_budgets():
    if request.method == 'POST':
        category = request.form.get('category')
        amount = request.form.get('amount')
        period = request.form.get('period', 'monthly')
        
        # Validate inputs
        errors = []
        
        if not category:
            errors.append('Category is required')
        
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append('Budget amount must be greater than zero')
        except (ValueError, TypeError):
            errors.append('Budget amount must be a valid number')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            with get_db() as conn:
                # Check if budget for this category already exists
                existing = conn.execute('SELECT id FROM budgets WHERE category = ?', (category,)).fetchone()
                
                if existing:
                    # Update existing budget
                    conn.execute('''
                        UPDATE budgets
                        SET amount = ?, period = ?
                        WHERE category = ?
                    ''', (amount, period, category))
                    flash(f'Budget for {category} updated successfully!', 'success')
                else:
                    # Create new budget
                    conn.execute('''
                        INSERT INTO budgets (category, amount, period)
                        VALUES (?, ?, ?)
                    ''', (category, amount, period))
                    flash(f'Budget for {category} created successfully!', 'success')
                
                conn.commit()
    
    # Get all budgets
    with get_db() as conn:
        budgets = conn.execute('SELECT * FROM budgets ORDER BY category').fetchall()
        
        # Get available categories for the dropdown
        categories = conn.execute('SELECT DISTINCT category FROM expenses').fetchall()
        categories = [c['category'] for c in categories] + [c for c in EXPENSE_CATEGORIES if c not in categories]
    
    # Get current currency (default to USD)
    currency_code = session.get('currency', 'HUF')
    currency = CURRENCIES[currency_code]
    
    return render_template('budgets.html', 
                          budgets=budgets,
                          categories=sorted(set(categories)),
                          currency=currency,
                          currency_code=currency_code)

# Delete budget
@app.route('/budgets/delete/<int:id>', methods=['POST'])
def delete_budget(id):
    with get_db() as conn:
        conn.execute('DELETE FROM budgets WHERE id = ?', (id,))
        conn.commit()
        flash('Budget deleted successfully!', 'success')
    
    return redirect(url_for('manage_budgets'))

# Export data
@app.route('/export', methods=['GET'])
def export_data():
    format_type = request.args.get('format', 'json')
    
    with get_db() as conn:
        # Get all expenses with their tags
        expenses = conn.execute('''
            SELECT e.*, GROUP_CONCAT(t.name) as tags
            FROM expenses e
            LEFT JOIN expense_tags et ON e.id = et.expense_id
            LEFT JOIN tags t ON et.tag_id = t.id
            GROUP BY e.id
            ORDER BY e.date DESC
        ''').fetchall()
        
        # Convert to list of dicts
        result = []
        for expense in expenses:
            expense_dict = dict(expense)
            # Split tags string into list
            tags_str = expense_dict.pop('tags', None)
            expense_dict['tags'] = tags_str.split(',') if tags_str else []
            result.append(expense_dict)
    
    if format_type == 'json':
        return jsonify(result)
    else:
        # Can implement CSV export here
        return jsonify({"error": "Format not supported"}), 400

# Tags API
@app.route('/api/tags', methods=['GET'])
def get_tags():
    with get_db() as conn:
        tags = conn.execute('SELECT name FROM tags ORDER BY name').fetchall()
        tags = [tag['name'] for tag in tags]
    
    return jsonify(tags)

# Theme toggle
@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    # Get the redirect URL or default to index
    redirect_url = request.form.get('redirect_url', url_for('index'))
    
    # Get the requested theme
    requested_theme = request.form.get('theme')
    
    # If a specific theme is requested, use it; otherwise toggle between light and dark
    if requested_theme:
        new_theme = requested_theme
    else:
        # Toggle between themes: light -> dark -> light
        current_theme = request.cookies.get('theme', 'light')
        new_theme = 'dark' if current_theme == 'light' else 'light'
    
    # Create response with redirect
    response = make_response(redirect(redirect_url))
    
    # Set the cookie (30-day expiration)
    response.set_cookie('theme', new_theme, max_age=30*24*60*60)
    
    return response

# Settings page
@app.route('/settings', methods=['GET'])
def settings():
    # Get current currency
    current_currency = session.get('currency', 'HUF')
    
    # Get current theme
    current_theme = request.cookies.get('theme', 'light')
    
    return render_template('settings.html',
                          currencies=CURRENCIES,
                          current_currency=current_currency,
                          current_theme=current_theme)

# Currency selection
@app.route('/settings/currency', methods=['GET', 'POST'])
def set_currency():
    if request.method == 'POST':
        currency = request.form.get('currency', 'HUF')
        if currency in CURRENCIES:
            session['currency'] = currency
            flash(f'Currency changed to {CURRENCIES[currency]["name"]}', 'success')
        else:
            flash('Invalid currency selected', 'danger')
        return redirect(url_for('settings'))
    
    # Default to USD if not set
    current_currency = session.get('currency', 'HUF')
    
    return render_template('currency_settings.html', 
                          currencies=CURRENCIES,
                          current_currency=current_currency)

# Expense reports
@app.route('/reports', methods=['GET'])
def reports():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    grouping = request.args.get('grouping', 'month')  # month, week, category
    
    query_params = []
    date_filter = ''
    
    # Apply date filters if provided
    if from_date:
        date_filter += ' AND date >= ?'
        query_params.append(from_date)
    
    if to_date:
        date_filter += ' AND date <= ?'
        query_params.append(to_date)
    
    with get_db() as conn:
        if grouping == 'category':
            # Group by category
            report_data = conn.execute(f'''
                SELECT category, SUM(amount) as total, COUNT(*) as count
                FROM expenses
                WHERE 1=1 {date_filter}
                GROUP BY category
                ORDER BY total DESC
            ''', query_params).fetchall()
            
            report_type = 'Category'
            
        elif grouping == 'week':
            # Group by week (using SQLite's strftime)
            report_data = conn.execute(f'''
                SELECT 
                    strftime('%Y-W%W', date) as period,
                    SUM(amount) as total,
                    COUNT(*) as count
                FROM expenses
                WHERE 1=1 {date_filter}
                GROUP BY period
                ORDER BY period
            ''', query_params).fetchall()
            
            report_type = 'Weekly'
            
        else:  # Default to month
            # Group by month
            report_data = conn.execute(f'''
                SELECT 
                    strftime('%Y-%m', date) as period,
                    SUM(amount) as total,
                    COUNT(*) as count
                FROM expenses
                WHERE 1=1 {date_filter}
                GROUP BY period
                ORDER BY period
            ''', query_params).fetchall()
            
            report_type = 'Monthly'
        
        # Get overall summary
        summary = conn.execute(f'''
            SELECT 
                SUM(amount) as grand_total,
                COUNT(*) as total_count,
                AVG(amount) as average
            FROM expenses
            WHERE 1=1 {date_filter}
        ''', query_params).fetchone()
    
    return render_template('reports.html',
                          report_data=report_data,
                          summary=summary,
                          report_type=report_type,
                          from_date=from_date,
                          to_date=to_date,
                          grouping=grouping)

# Savings Goals
@app.route('/savings-goals', methods=['GET'])
def savings_goals():
    with get_db() as conn:
        goals = conn.execute('''
            SELECT * FROM savings_goals
            ORDER BY status, target_date
        ''').fetchall()
    
    return render_template('savings_goals.html',
                          goals=goals)

@app.route('/savings-goals/add', methods=['POST'])
def add_savings_goal():
    name = request.form.get('name')
    target_amount = float(request.form.get('target_amount', 0))
    current_amount = float(request.form.get('current_amount', 0))
    start_date = request.form.get('start_date', datetime.today().strftime('%Y-%m-%d'))
    target_date = request.form.get('target_date')
    description = request.form.get('description', '')
    
    # Validate inputs
    if not name or target_amount <= 0:
        flash('Please provide a name and a valid target amount', 'danger')
        return redirect(url_for('savings_goals'))
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO savings_goals 
            (name, target_amount, current_amount, start_date, target_date, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, target_amount, current_amount, start_date, target_date, description))
        conn.commit()
    
    flash('Savings goal added successfully!', 'success')
    return redirect(url_for('savings_goals'))

@app.route('/savings-goals/update/<int:id>', methods=['POST'])
def update_savings_goal(id):
    current_amount = float(request.form.get('current_amount', 0))
    status = request.form.get('status')
    
    with get_db() as conn:
        goal = conn.execute('SELECT * FROM savings_goals WHERE id = ?', (id,)).fetchone()
        
        if not goal:
            flash('Savings goal not found!', 'danger')
            return redirect(url_for('savings_goals'))
        
        conn.execute('''
            UPDATE savings_goals
            SET current_amount = ?, status = ?
            WHERE id = ?
        ''', (current_amount, status, id))
        conn.commit()
    
    flash('Savings goal updated successfully!', 'success')
    return redirect(url_for('savings_goals'))

@app.route('/savings-goals/edit/<int:id>', methods=['POST'])
def edit_savings_goal(id):
    name = request.form.get('name')
    target_amount = float(request.form.get('target_amount', 0))
    current_amount = float(request.form.get('current_amount', 0))
    target_date = request.form.get('target_date')
    description = request.form.get('description', '')
    status = request.form.get('status')
    
    # Validate inputs
    if not name or target_amount <= 0:
        flash('Please provide a name and a valid target amount', 'danger')
        return redirect(url_for('savings_goals'))
    
    with get_db() as conn:
        conn.execute('''
            UPDATE savings_goals
            SET name = ?, target_amount = ?, current_amount = ?, 
                target_date = ?, description = ?, status = ?
            WHERE id = ?
        ''', (name, target_amount, current_amount, target_date, description, status, id))
        conn.commit()
    
    flash('Savings goal updated successfully!', 'success')
    return redirect(url_for('savings_goals'))

@app.route('/savings-goals/delete/<int:id>', methods=['POST'])
def delete_savings_goal(id):
    with get_db() as conn:
        conn.execute('DELETE FROM savings_goals WHERE id = ?', (id,))
        conn.commit()
    
    flash('Savings goal deleted successfully!', 'success')
    return redirect(url_for('savings_goals'))

# Spending Prediction
@app.route('/forecasts', methods=['GET'])
def forecasts():
    # Get month filter from request, default to current month
    current_date = datetime.today()
    default_month = current_date.strftime('%Y-%m')
    month_filter = request.args.get('month', default_month)
    category_filter = request.args.get('category', '')
    
    try:
        # Parse year and month from filter
        year, month = map(int, month_filter.split('-'))
        # Get the current year-month
        current_year = current_date.year
        current_month = current_date.month
        
        # Calculate the previous 6 months for historical data analysis
        months_data = []
        for i in range(6):
            prev_month = month - i - 1
            prev_year = year
            
            if prev_month <= 0:
                prev_month += 12
                prev_year -= 1
                
            # Skip future months
            if (prev_year > current_year) or (prev_year == current_year and prev_month > current_month):
                continue
                
            months_data.append({'year': prev_year, 'month': prev_month})
    except ValueError:
        # If invalid month format, default to current month
        year, month = current_date.year, current_date.month
        month_filter = default_month
        months_data = []
        for i in range(6):
            prev_month = current_month - i - 1
            prev_year = current_year
            
            if prev_month <= 0:
                prev_month += 12
                prev_year -= 1
                
            months_data.append({'year': prev_year, 'month': prev_month})
    
    with get_db() as conn:
        # Get categories for filter
        categories = conn.execute('SELECT DISTINCT category FROM expenses WHERE category IS NOT NULL').fetchall()
        categories = [c['category'] for c in categories if c['category']] + [c for c in EXPENSE_CATEGORIES if c not in [c['category'] for c in categories if c['category']]]
        
        # Historical data analysis
        historical_data = []
        month_totals = []
        
        base_query = '''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        '''
        
        if category_filter:
            base_query += ' AND category = ?'
        
        base_query += ' GROUP BY category ORDER BY total DESC'
        
        for month_data in months_data:
            year_str = str(month_data['year'])
            # Format month with leading zero
            month_str = f"{month_data['month']:02d}"
            
            params = [year_str, month_str]
            
            if category_filter:
                params.append(category_filter)
            
            month_expenses = conn.execute(base_query, params).fetchall()
            
            # Calculate month total - handle empty data
            month_total = sum(expense['total'] for expense in month_expenses) if month_expenses else 0
            
            if month_total > 0:  # Only add months with actual expenses
                month_totals.append(month_total)
                
                # Store data for analysis
                historical_data.append({
                    'year_month': f"{year_str}-{month_str}",
                    'expenses': month_expenses,
                    'total': month_total
                })
        
        # Skip prediction if not enough data
        prediction = None
        predicted_categories = []
        
        if month_totals and len(month_totals) > 0:
            # Simple prediction based on average of previous months
            avg_total = sum(month_totals) / len(month_totals)
            
            # Get category breakdown from historical data
            category_totals = {}
            category_counts = {}
            
            for month in historical_data:
                for expense in month['expenses']:
                    cat = expense['category']
                    if cat not in category_totals:
                        category_totals[cat] = 0
                        category_counts[cat] = 0
                    
                    category_totals[cat] += expense['total']
                    category_counts[cat] += 1
            
            # Calculate predicted amounts per category
            for cat in category_totals:
                if category_counts[cat] > 0:
                    avg_amount = category_totals[cat] / category_counts[cat]
                    predicted_categories.append({
                        'category': cat,
                        'amount': avg_amount,
                        'frequency': category_counts[cat] / len(historical_data) * 100
                    })
            
            # Sort by frequency (most common first)
            predicted_categories.sort(key=lambda x: x['frequency'], reverse=True)
            
            # Final prediction
            prediction = {
                'total': avg_total,
                'categories': predicted_categories
            }
    
    # Get next month for prediction
    next_month = month + 1
    next_year = year
    
    if next_month > 12:
        next_month = 1
        next_year += 1
        
    next_month_str = f"{next_year}-{next_month:02d}"
    
    return render_template('forecasts.html',
                          historical_data=historical_data,
                          prediction=prediction,
                          month_filter=month_filter,
                          next_month=next_month_str,
                          category_filter=category_filter,
                          categories=sorted(set(categories)) if categories else [])

# Income Tracking
@app.route('/income', methods=['GET'])
def income():
    # Default to all time if no date filters provided
    from_date = ''
    to_date = ''
    source_filter = request.args.get('source', '')
    
    query = 'SELECT * FROM income_entries WHERE 1=1'
    params = []
    
    if from_date:
        query += ' AND date >= ?'
        params.append(from_date)
    
    if to_date:
        query += ' AND date <= ?'
        params.append(to_date)
    
    if source_filter:
        query += ' AND source = ?'
        params.append(source_filter)
    
    query += ' ORDER BY date DESC'
    
    with get_db() as conn:
        income_entries = conn.execute(query, params).fetchall()
        
        # Get total income
        total_query = 'SELECT SUM(amount) as total FROM income_entries WHERE 1=1'
        total_params = []
        
        if from_date:
            total_query += ' AND date >= ?'
            total_params.append(from_date)
        
        if to_date:
            total_query += ' AND date <= ?'
            total_params.append(to_date)
        
        if source_filter:
            total_query += ' AND source = ?'
            total_params.append(source_filter)
        
        total_income = conn.execute(total_query, total_params).fetchone()
        
        # Get recurring income
        recurring_query = 'SELECT SUM(amount) as total FROM income_entries WHERE recurring = 1'
        recurring_total = conn.execute(recurring_query).fetchone()
        
        # Get monthly average (for the selected period)
        if from_date and to_date:
            start = datetime.strptime(from_date, '%Y-%m-%d')
            end = datetime.strptime(to_date, '%Y-%m-%d')
            months = (end.year - start.year) * 12 + end.month - start.month + 1
            monthly_avg = total_income['total'] / months if total_income['total'] and months > 0 else 0
        else:
            monthly_avg = 0
        
        # Get available sources for filter
        sources = conn.execute('SELECT DISTINCT source FROM income_entries ORDER BY source').fetchall()
        sources = [s['source'] for s in sources]
    
    return render_template('income.html',
                          income_entries=income_entries,
                          total=total_income['total'] if total_income['total'] else 0,
                          recurring_total=recurring_total['total'] if recurring_total['total'] else 0,
                          monthly_avg=monthly_avg,
                          sources=sources,
                          from_date=from_date,
                          to_date=to_date,
                          source_filter=source_filter)

@app.route('/income/add', methods=['POST'])
def add_income():
    source = request.form.get('source')
    amount = float(request.form.get('amount', 0))
    date = request.form.get('date')
    description = request.form.get('description', '')
    recurring = 1 if request.form.get('recurring') else 0
    recurring_interval = request.form.get('recurring_interval') if recurring else None
    
    # Validate inputs
    if not source or amount <= 0 or not date:
        flash('Please provide a source, valid amount, and date', 'danger')
        return redirect(url_for('income'))
    
    with get_db() as conn:
        conn.execute('''
            INSERT INTO income_entries 
            (source, amount, date, description, recurring, recurring_interval)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (source, amount, date, description, recurring, recurring_interval))
        conn.commit()
    
    flash('Income entry added successfully!', 'success')
    return redirect(url_for('income'))

@app.route('/income/edit/<int:id>', methods=['POST'])
def edit_income(id):
    source = request.form.get('source')
    amount = float(request.form.get('amount', 0))
    date = request.form.get('date')
    description = request.form.get('description', '')
    recurring = 1 if request.form.get('recurring') else 0
    recurring_interval = request.form.get('recurring_interval') if recurring else None
    
    # Validate inputs
    if not source or amount <= 0 or not date:
        flash('Please provide a source, valid amount, and date', 'danger')
        return redirect(url_for('income'))
    
    with get_db() as conn:
        conn.execute('''
            UPDATE income_entries
            SET source = ?, amount = ?, date = ?, description = ?, 
                recurring = ?, recurring_interval = ?
            WHERE id = ?
        ''', (source, amount, date, description, recurring, recurring_interval, id))
        conn.commit()
    
    flash('Income entry updated successfully!', 'success')
    return redirect(url_for('income'))

@app.route('/income/delete/<int:id>', methods=['POST'])
def delete_income(id):
    with get_db() as conn:
        conn.execute('DELETE FROM income_entries WHERE id = ?', (id,))
        conn.commit()
    
    flash('Income entry deleted successfully!', 'success')
    return redirect(url_for('income'))

# Run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
