from app import create_app, db
from app.models import Expense, Budget, SavingsGoal, IncomeEntry
from config import Config
import os

def init_database():
    app = create_app()
    
    with app.app_context():
        # Create database if it doesn't exist (for MySQL and PostgreSQL)
        if Config.DATABASE_TYPE in ['mysql', 'postgresql']:
            try:
                # Create all tables
                db.create_all()
                print(f"Database tables created successfully for {Config.DATABASE_TYPE}")
            except Exception as e:
                print(f"Error creating database: {str(e)}")
                return False
        else:
            # For SQLite, just create the tables
            db.create_all()
            print("SQLite database and tables created successfully")
        
        return True

if __name__ == '__main__':
    init_database() 