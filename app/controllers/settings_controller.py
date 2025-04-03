from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from app.config import CURRENCIES, DEFAULT_CURRENCY

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET'])
def index():
    """Settings page."""
    # Get current currency
    current_currency = session.get('currency', DEFAULT_CURRENCY)
    
    # Get current theme
    current_theme = request.cookies.get('theme', 'light')
    
    return render_template('settings.html',
                          currencies=CURRENCIES,
                          current_currency=current_currency,
                          current_theme=current_theme)

@settings_bp.route('/settings/currency', methods=['GET', 'POST'])
def set_currency():
    """Set application currency."""
    if request.method == 'POST':
        currency = request.form.get('currency', DEFAULT_CURRENCY)
        if currency in CURRENCIES:
            session['currency'] = currency
            flash(f'Currency changed to {CURRENCIES[currency]["name"]}', 'success')
        else:
            flash('Invalid currency selected', 'danger')
        return redirect(url_for('settings.index'))
    
    # Default to configured default if not set
    current_currency = session.get('currency', DEFAULT_CURRENCY)
    
    return render_template('currency_settings.html', 
                          currencies=CURRENCIES,
                          current_currency=current_currency)

@settings_bp.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    """Toggle between light and dark themes."""
    # Get the redirect URL or default to index
    redirect_url = request.form.get('redirect_url', url_for('expense.index'))
    
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