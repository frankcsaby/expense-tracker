from app.database import get_db_connection

class Tag:
    """Model for handling tag-related operations."""
    
    @staticmethod
    def get_all():
        """Get all tags."""
        with get_db_connection() as conn:
            tags = conn.execute('SELECT * FROM tags ORDER BY name').fetchall()
            return [dict(tag) for tag in tags]
    
    @staticmethod
    def get_names():
        """Get all tag names as a list."""
        with get_db_connection() as conn:
            tags = conn.execute('SELECT name FROM tags ORDER BY name').fetchall()
            return [tag['name'] for tag in tags]
    
    @staticmethod
    def get_by_id(tag_id):
        """Get a single tag by ID."""
        with get_db_connection() as conn:
            return conn.execute('SELECT * FROM tags WHERE id = ?', (tag_id,)).fetchone()
    
    @staticmethod
    def get_by_name(name):
        """Get a tag by name."""
        with get_db_connection() as conn:
            return conn.execute('SELECT * FROM tags WHERE name = ?', (name,)).fetchone()
    
    @staticmethod
    def create(name):
        """Create a new tag."""
        with get_db_connection() as conn:
            # Check if tag already exists
            existing = conn.execute('SELECT id FROM tags WHERE name = ?', (name,)).fetchone()
            if existing:
                return existing['id']
            
            cursor = conn.execute('INSERT INTO tags (name) VALUES (?)', (name,))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def delete(tag_id):
        """Delete a tag."""
        with get_db_connection() as conn:
            conn.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
            # This will cascade and delete entries in expense_tags
            conn.commit()
    
    @staticmethod
    def get_usage_counts():
        """Get tag usage counts."""
        with get_db_connection() as conn:
            counts = conn.execute('''
                SELECT t.id, t.name, COUNT(et.expense_id) as count
                FROM tags t
                LEFT JOIN expense_tags et ON t.id = et.tag_id
                GROUP BY t.id
                ORDER BY count DESC, t.name
            ''').fetchall()
            return [dict(count) for count in counts] 