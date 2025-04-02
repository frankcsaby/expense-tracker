from datetime import datetime
from app.database import get_db_connection
from app.config import DATE_FORMAT

class Expense:
    """Model for handling expense-related operations."""
    
    @staticmethod
    def get_all(filters=None, order_by='date DESC'):
        """Get all expenses with optional filtering."""
        query = 'SELECT * FROM expenses WHERE 1=1'
        params = []
        
        if filters:
            # Apply search filter
            if filters.get('search'):
                query += ' AND description LIKE ?'
                params.append(f'%{filters["search"]}%')
            
            # Apply category filter
            if filters.get('category'):
                query += ' AND category = ?'
                params.append(filters['category'])
            
            # Apply date range filters
            if filters.get('from_date'):
                query += ' AND date >= ?'
                params.append(filters['from_date'])
            
            if filters.get('to_date'):
                query += ' AND date <= ?'
                params.append(filters['to_date'])
        
        # Add ordering
        if order_by:
            query += f' ORDER BY {order_by}'
        
        with get_db_connection() as conn:
            return conn.execute(query, params).fetchall()
    
    @staticmethod
    def get_by_tag(tag_name, filters=None):
        """Get expenses with a specific tag."""
        query = '''
            SELECT e.* FROM expenses e
            JOIN expense_tags et ON e.id = et.expense_id
            JOIN tags t ON et.tag_id = t.id
            WHERE t.name = ?
        '''
        params = [tag_name]
        
        if filters:
            # Apply search filter
            if filters.get('search'):
                query += ' AND e.description LIKE ?'
                params.append(f'%{filters["search"]}%')
            
            # Apply category filter
            if filters.get('category'):
                query += ' AND e.category = ?'
                params.append(filters['category'])
            
            # Apply date range filters
            if filters.get('from_date'):
                query += ' AND e.date >= ?'
                params.append(filters['from_date'])
            
            if filters.get('to_date'):
                query += ' AND e.date <= ?'
                params.append(filters['to_date'])
        
        query += ' ORDER BY e.date DESC'
        
        with get_db_connection() as conn:
            return conn.execute(query, params).fetchall()
    
    @staticmethod
    def get_by_id(expense_id):
        """Get a single expense by ID."""
        with get_db_connection() as conn:
            return conn.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,)).fetchone()
    
    @staticmethod
    def create(expense_data):
        """Create a new expense."""
        with get_db_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO expenses (description, amount, category, date, recurring, recurring_interval)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                expense_data['description'],
                expense_data['amount'],
                expense_data['category'],
                expense_data['date'],
                expense_data.get('recurring', 0),
                expense_data.get('recurring_interval')
            ))
            expense_id = cursor.lastrowid
            
            # Handle tags if provided
            if 'tags' in expense_data and expense_data['tags']:
                Expense.set_tags(expense_id, expense_data['tags'])
            
            conn.commit()
            return expense_id
    
    @staticmethod
    def update(expense_id, expense_data):
        """Update an existing expense."""
        with get_db_connection() as conn:
            conn.execute('''
                UPDATE expenses
                SET description = ?, amount = ?, category = ?, date = ?, recurring = ?, recurring_interval = ?
                WHERE id = ?
            ''', (
                expense_data['description'],
                expense_data['amount'],
                expense_data['category'],
                expense_data['date'],
                expense_data.get('recurring', 0),
                expense_data.get('recurring_interval'),
                expense_id
            ))
            
            # Handle tags if provided
            if 'tags' in expense_data:
                # Remove existing tags
                conn.execute('DELETE FROM expense_tags WHERE expense_id = ?', (expense_id,))
                
                # Add new tags
                if expense_data['tags']:
                    Expense.set_tags(expense_id, expense_data['tags'])
            
            conn.commit()
    
    @staticmethod
    def delete(expense_id):
        """Delete an expense."""
        with get_db_connection() as conn:
            # Delete expense and related tags (cascade will handle the expense_tags)
            conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()
    
    @staticmethod
    def get_total():
        """Get the sum of all expenses."""
        with get_db_connection() as conn:
            result = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
            return result['total'] if result and result['total'] else 0
    
    @staticmethod
    def get_category_totals(filters=None):
        """Get expense totals grouped by category."""
        query = '''
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM expenses
            WHERE 1=1
        '''
        params = []
        
        if filters:
            # Apply date range filters
            if filters.get('from_date'):
                query += ' AND date >= ?'
                params.append(filters['from_date'])
            
            if filters.get('to_date'):
                query += ' AND date <= ?'
                params.append(filters['to_date'])
        
        query += ' GROUP BY category ORDER BY total DESC'
        
        with get_db_connection() as conn:
            return conn.execute(query, params).fetchall()
    
    @staticmethod
    def get_statistics(filters=None):
        """Get expense statistics (total, average, max, count)."""
        query = '''
            SELECT 
                SUM(amount) as total,
                AVG(amount) as average,
                MAX(amount) as max,
                COUNT(*) as count
            FROM expenses
            WHERE 1=1
        '''
        params = []
        
        if filters:
            # Apply date range filters
            if filters.get('from_date'):
                query += ' AND date >= ?'
                params.append(filters['from_date'])
            
            if filters.get('to_date'):
                query += ' AND date <= ?'
                params.append(filters['to_date'])
            
            # Apply category filter
            if filters.get('category'):
                query += ' AND category = ?'
                params.append(filters['category'])
        
        with get_db_connection() as conn:
            stats = conn.execute(query, params).fetchone()
            return {
                'total': stats['total'] if stats['total'] else 0,
                'average': stats['average'] if stats['average'] else 0,
                'max': stats['max'] if stats['max'] else 0,
                'count': stats['count']
            }
    
    @staticmethod
    def set_tags(expense_id, tags):
        """Associate tags with an expense."""
        if not tags:
            return
        
        with get_db_connection() as conn:
            for tag_name in tags:
                tag_name = tag_name.strip()
                if not tag_name:
                    continue
                
                # Get tag ID or create new tag
                tag = conn.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).fetchone()
                if tag:
                    tag_id = tag['id']
                else:
                    cursor = conn.execute('INSERT INTO tags (name) VALUES (?)', (tag_name,))
                    tag_id = cursor.lastrowid
                
                # Create relationship
                conn.execute('''
                    INSERT OR IGNORE INTO expense_tags (expense_id, tag_id)
                    VALUES (?, ?)
                ''', (expense_id, tag_id))
            
            conn.commit()
    
    @staticmethod
    def get_tags(expense_id):
        """Get tags for an expense."""
        with get_db_connection() as conn:
            tags = conn.execute('''
                SELECT t.name FROM tags t
                JOIN expense_tags et ON t.id = et.tag_id
                WHERE et.expense_id = ?
                ORDER BY t.name
            ''', (expense_id,)).fetchall()
            return [tag['name'] for tag in tags]
    
    @staticmethod
    def validate(form_data):
        """Validate expense data."""
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
                datetime.strptime(date_str, DATE_FORMAT)
            else:
                errors.append('Date is required')
        except ValueError:
            errors.append('Invalid date format')
        
        return errors 