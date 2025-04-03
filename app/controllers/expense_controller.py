from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.expense import Expense
from app.models.tag import Tag
from app.config import EXPENSE_CATEGORIES, CURRENCIES, DEFAULT_CURRENCY, RECURRING_INTERVALS
from app.utils import parse_tags

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/')
def index():
    """Home page showing expense list with filters."""
    # Get filter parameters
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    tag_filter = request.args.get('tag', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    filters = {
        'search': search_query,
        'category': category_filter,
        'from_date': from_date,
        'to_date': to_date
    }
    
    # Get expenses based on filters
    if tag_filter:
        expenses = Expense.get_by_tag(tag_filter, filters)
    else:
        expenses = Expense.get_all(filters)
    
    # Get expense total
    total_expenses = Expense.get_total()
    
    # Get categories for the filter dropdown
    with_existing_categories = []
    existing_categories = set()
    
    for expense in expenses:
        existing_categories.add(expense['category'])
    
    # Merge existing categories with predefined ones
    with_existing_categories = list(existing_categories)
    for category in EXPENSE_CATEGORIES:
        if category not in with_existing_categories:
            with_existing_categories.append(category)
    
    # Get available tags for the filter dropdown
    tags = Tag.get_names()
    
    # Get current currency
    currency_code = session.get('currency', DEFAULT_CURRENCY)
    currency = CURRENCIES[currency_code]
    
    # Get expense tags
    for expense in expenses:
        expense_tags = Expense.get_tags(expense['id'])
        expense['tags'] = ','.join(expense_tags)
    
    return render_template('index.html', 
                          expenses=expenses, 
                          total=total_expenses,
                          categories=sorted(with_existing_categories),
                          tags=tags,
                          search_query=search_query,
                          category_filter=category_filter,
                          tag_filter=tag_filter,
                          from_date=from_date,
                          to_date=to_date,
                          currency=currency,
                          currency_code=currency_code)

@expense_bp.route('/add', methods=['GET', 'POST'])
def add_expense():
    """Add a new expense."""
    if request.method == 'POST':
        # Get form data
        form_data = {
            'description': request.form.get('description', '').strip(),
            'amount': request.form.get('amount', ''),
            'category': request.form.get('category', '').strip(),
            'date': request.form.get('date', ''),
            'recurring': 1 if request.form.get('recurring') else 0,
            'recurring_interval': request.form.get('recurring_interval')
        }
        
        # Validate form data
        errors = Expense.validate(form_data)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Try to convert amount to float
            form_data['amount'] = float(form_data['amount'])
            
            # Parse tags
            tags = parse_tags(request.form.get('tags', ''))
            form_data['tags'] = tags
            
            # Create expense
            expense_id = Expense.create(form_data)
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for('expense.index'))
    
    # Get current currency
    currency_code = session.get('currency', DEFAULT_CURRENCY)
    currency = CURRENCIES[currency_code]
    
    # Get today's date
    today = request.args.get('date', '')
    
    return render_template('add_expense.html',
                          categories=sorted(EXPENSE_CATEGORIES),
                          currency=currency,
                          currency_code=currency_code,
                          today=today,
                          tags=Tag.get_names(),
                          recurring_intervals=RECURRING_INTERVALS)

@expense_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    """Edit an existing expense."""
    # Get expense by ID
    expense = Expense.get_by_id(id)
    
    if not expense:
        flash('Expense not found', 'danger')
        return redirect(url_for('expense.index'))
    
    if request.method == 'POST':
        # Get form data
        form_data = {
            'description': request.form.get('description', '').strip(),
            'amount': request.form.get('amount', ''),
            'category': request.form.get('category', '').strip(),
            'date': request.form.get('date', ''),
            'recurring': 1 if request.form.get('recurring') else 0,
            'recurring_interval': request.form.get('recurring_interval')
        }
        
        # Validate form data
        errors = Expense.validate(form_data)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Try to convert amount to float
            form_data['amount'] = float(form_data['amount'])
            
            # Parse tags
            tags = parse_tags(request.form.get('tags', ''))
            form_data['tags'] = tags
            
            # Update expense
            Expense.update(id, form_data)
            
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('expense.index'))
    
    # Get expense tags
    expense_tags = Expense.get_tags(id)
    tags_str = ','.join(expense_tags)
    
    # Get current currency
    currency_code = session.get('currency', DEFAULT_CURRENCY)
    currency = CURRENCIES[currency_code]
    
    return render_template('edit_expense.html',
                          expense=expense,
                          tags=tags_str,
                          categories=sorted(EXPENSE_CATEGORIES),
                          currency=currency,
                          currency_code=currency_code,
                          all_tags=Tag.get_names(),
                          recurring_intervals=RECURRING_INTERVALS)

@expense_bp.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    """Delete an expense."""
    Expense.delete(id)
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expense.index'))

@expense_bp.route('/export', methods=['GET'])
def export_data():
    """Export expense data."""
    format_type = request.args.get('format', 'json')
    
    # This should return a JSON response with all expenses
    # Can be implemented later
    
    flash('Export feature coming soon!', 'info')
    return redirect(url_for('expense.index')) 