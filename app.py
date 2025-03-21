from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
import os
from contextlib import contextmanager

app = Flask(__name__)
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

# Database setup with context manager
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('expenses.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        # Create expenses table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                recurring INTEGER DEFAULT 0,
                recurring_interval TEXT
            )
        ''')
        
        # Create budgets table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE,
                amount REAL NOT NULL,
                period TEXT NOT NULL
            )
        ''')
        
        # Create tags table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Create expense_tags table (for many-to-many relationship)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expense_tags (
                expense_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (expense_id, tag_id),
                FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

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
    
    with get_db_connection() as conn:
        expenses = conn.execute(query, params).fetchall()
        # Get total expenses
        total_expenses = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
        
        # Get available categories for the filter dropdown
        categories = conn.execute('SELECT DISTINCT category FROM expenses').fetchall()
        categories = [c['category'] for c in categories] + [c for c in EXPENSE_CATEGORIES if c not in categories]
    
    # Get all available tags for the filter dropdown
    tags = []
    with get_db_connection() as conn:
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
        
        with get_db_connection() as conn:
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
    with get_db_connection() as conn:
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
    with get_db_connection() as conn:
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
    
    with get_db_connection() as conn:
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
    currency_code = session.get('currency', 'USD')
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
            with get_db_connection() as conn:
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
    with get_db_connection() as conn:
        budgets = conn.execute('SELECT * FROM budgets ORDER BY category').fetchall()
        
        # Get available categories for the dropdown
        categories = conn.execute('SELECT DISTINCT category FROM expenses').fetchall()
        categories = [c['category'] for c in categories] + [c for c in EXPENSE_CATEGORIES if c not in categories]
    
    # Get current currency (default to USD)
    currency_code = session.get('currency', 'USD')
    currency = CURRENCIES[currency_code]
    
    return render_template('budgets.html', 
                          budgets=budgets,
                          categories=sorted(set(categories)),
                          currency=currency,
                          currency_code=currency_code)

# Delete budget
@app.route('/budgets/delete/<int:id>', methods=['POST'])
def delete_budget(id):
    with get_db_connection() as conn:
        conn.execute('DELETE FROM budgets WHERE id = ?', (id,))
        conn.commit()
        flash('Budget deleted successfully!', 'success')
    
    return redirect(url_for('manage_budgets'))

# Export data
@app.route('/export', methods=['GET'])
def export_data():
    format_type = request.args.get('format', 'json')
    
    with get_db_connection() as conn:
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
    with get_db_connection() as conn:
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
    
    # If a specific theme is requested, use it; otherwise cycle through themes
    if requested_theme:
        new_theme = requested_theme
    else:
        # Toggle between themes: light -> dark -> freaky -> light
        current_theme = request.cookies.get('theme', 'light')
        if current_theme == 'light':
            new_theme = 'dark'
        elif current_theme == 'dark':
            new_theme = 'freaky'
        else:
            new_theme = 'light'
    
    # Create response with redirect
    response = make_response(redirect(redirect_url))
    
    # Set the cookie (30-day expiration)
    response.set_cookie('theme', new_theme, max_age=30*24*60*60)
    
    return response

# Settings page
@app.route('/settings', methods=['GET'])
def settings():
    # Get current currency
    current_currency = session.get('currency', 'USD')
    
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
        currency = request.form.get('currency', 'USD')
        if currency in CURRENCIES:
            session['currency'] = currency
            flash(f'Currency changed to {CURRENCIES[currency]["name"]}', 'success')
        else:
            flash('Invalid currency selected', 'danger')
        return redirect(url_for('settings'))
    
    # Default to USD if not set
    current_currency = session.get('currency', 'USD')
    
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
    
    with get_db_connection() as conn:
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
    
    # Get current currency
    currency_code = session.get('currency', 'USD')
    currency = CURRENCIES[currency_code]
    
    return render_template('reports.html',
                          report_data=report_data,
                          summary=summary,
                          report_type=report_type,
                          from_date=from_date,
                          to_date=to_date,
                          grouping=grouping,
                          currency=currency,
                          currency_code=currency_code)

# Run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
