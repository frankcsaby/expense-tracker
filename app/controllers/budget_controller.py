from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.budget import Budget
from app.config import EXPENSE_CATEGORIES, CURRENCIES, DEFAULT_CURRENCY, BUDGET_PERIODS

budget_bp = Blueprint('budget', __name__)

@budget_bp.route('/budgets', methods=['GET', 'POST'])
def manage_budgets():
    """Manage budgets page for setting and updating budgets."""
    if request.method == 'POST':
        # Get form data
        category = request.form.get('category', '').strip()
        amount = request.form.get('amount', '')
        period = request.form.get('period', '')
        
        # Validate budget data
        errors = Budget.validate({
            'category': category,
            'amount': amount,
            'period': period
        })
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Create or update budget
            try:
                amount = float(amount)
                result = Budget.create_or_update({
                    'category': category,
                    'amount': amount,
                    'period': period
                })
                
                if result['is_new']:
                    flash(f'Budget for {category} created successfully!', 'success')
                else:
                    flash(f'Budget for {category} updated successfully!', 'success')
                    
            except ValueError:
                flash('Invalid amount provided', 'danger')
    
    # Get all budgets
    budgets = Budget.get_all()
    
    # Get all categories
    categories = list(EXPENSE_CATEGORIES)
    
    # Get current currency
    currency_code = session.get('currency', DEFAULT_CURRENCY)
    currency = CURRENCIES[currency_code]
    
    return render_template('budgets.html', 
                          budgets=budgets,
                          categories=sorted(categories),
                          periods=BUDGET_PERIODS,
                          currency=currency,
                          currency_code=currency_code)

@budget_bp.route('/budgets/delete/<int:id>', methods=['POST'])
def delete_budget(id):
    """Delete a budget."""
    Budget.delete(id)
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('budget.manage_budgets')) 