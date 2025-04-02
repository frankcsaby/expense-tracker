from app.database import get_db_connection

class Budget:
    """Model for handling budget-related operations."""
    
    @staticmethod
    def get_all():
        """Get all budgets."""
        with get_db_connection() as conn:
            return conn.execute('SELECT * FROM budgets ORDER BY category').fetchall()
    
    @staticmethod
    def get_by_category(category):
        """Get budget for a specific category."""
        with get_db_connection() as conn:
            return conn.execute('SELECT * FROM budgets WHERE category = ?', (category,)).fetchone()
    
    @staticmethod
    def get_by_id(budget_id):
        """Get a single budget by ID."""
        with get_db_connection() as conn:
            return conn.execute('SELECT * FROM budgets WHERE id = ?', (budget_id,)).fetchone()
    
    @staticmethod
    def create_or_update(budget_data):
        """Create a new budget or update if already exists."""
        category = budget_data['category']
        amount = budget_data['amount']
        period = budget_data['period']
        
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
                budget_id = existing['id']
                is_new = False
            else:
                # Create new budget
                cursor = conn.execute('''
                    INSERT INTO budgets (category, amount, period)
                    VALUES (?, ?, ?)
                ''', (category, amount, period))
                budget_id = cursor.lastrowid
                is_new = True
            
            conn.commit()
            return {'id': budget_id, 'is_new': is_new}
    
    @staticmethod
    def delete(budget_id):
        """Delete a budget."""
        with get_db_connection() as conn:
            conn.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
            conn.commit()
    
    @staticmethod
    def get_comparison(date_range=None):
        """Get budget comparison with actual spending."""
        with get_db_connection() as conn:
            budgets = conn.execute('SELECT * FROM budgets ORDER BY category').fetchall()
            
            result = []
            for budget in budgets:
                # Query to get spending for this category within date range
                query = '''
                    SELECT SUM(amount) as spent
                    FROM expenses
                    WHERE category = ?
                '''
                params = [budget['category']]
                
                if date_range:
                    if date_range.get('from_date'):
                        query += ' AND date >= ?'
                        params.append(date_range['from_date'])
                    
                    if date_range.get('to_date'):
                        query += ' AND date <= ?'
                        params.append(date_range['to_date'])
                
                spending = conn.execute(query, params).fetchone()
                spent = spending['spent'] if spending and spending['spent'] else 0
                
                # Calculate percentage of budget used
                percentage = round((spent / budget['amount']) * 100) if budget['amount'] > 0 else 0
                
                result.append({
                    'id': budget['id'],
                    'category': budget['category'],
                    'budget': budget['amount'],
                    'period': budget['period'],
                    'spent': spent,
                    'percentage': percentage
                })
            
            return result
    
    @staticmethod
    def validate(form_data):
        """Validate budget data."""
        errors = []
        
        # Category validation
        if not form_data.get('category'):
            errors.append('Category is required')
        
        # Amount validation
        try:
            amount = float(form_data.get('amount', 0))
            if amount <= 0:
                errors.append('Budget amount must be greater than zero')
        except ValueError:
            errors.append('Budget amount must be a valid number')
        
        # Period validation
        if not form_data.get('period') or form_data.get('period') not in ['daily', 'weekly', 'monthly', 'yearly']:
            errors.append('Valid budget period is required')
        
        return errors 