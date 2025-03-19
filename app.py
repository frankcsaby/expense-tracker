from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Database setup
def get_db_connection():
    conn = sqlite3.connect('expenses.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Home page
@app.route('/')
def index():
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses)

# Add expense
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']

        conn = get_db_connection()
        conn.execute('INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)',
                     (description, amount, category, date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_expense.html')

# Analytics page
@app.route('/analytics')
def analytics():
    conn = get_db_connection()

    # Get current date and calculate time ranges
    today = datetime.today()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    last_year = today - timedelta(days=365)

    # Weekly totals
    weekly_totals = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date >= ?
        GROUP BY category
    ''', (last_week.strftime('%Y-%m-%d'),)).fetchall()

    # Monthly totals
    monthly_totals = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date >= ?
        GROUP BY category
    ''', (last_month.strftime('%Y-%m-%d'),)).fetchall()

    # Yearly totals
    yearly_totals = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE date >= ?
        GROUP BY category
    ''', (last_year.strftime('%Y-%m-%d'),)).fetchall()

    conn.close()

    return render_template('analytics.html',
                           weekly_totals=weekly_totals,
                           monthly_totals=monthly_totals,
                           yearly_totals=yearly_totals)

# Edit expense
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    conn = get_db_connection()
    expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        category = request.form['category']
        date = request.form['date']

        conn.execute('''
            UPDATE expenses
            SET description = ?, amount = ?, category = ?, date = ?
            WHERE id = ?
        ''', (description, amount, category, date, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_expense.html', expense=expense)

# Delete expense
@app.route('/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


# Run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
