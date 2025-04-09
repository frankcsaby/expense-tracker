import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Default to SQLite
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')
    
    # SQLite configuration
    SQLITE_DATABASE_URI = 'sqlite:///expenses.db'
    
    # MySQL configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'expense_tracker')
    MYSQL_DATABASE_URI = f'mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    
    # PostgreSQL configuration
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'expense_tracker')
    POSTGRES_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}'
    
    # Get the appropriate database URI based on DATABASE_TYPE
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        if self.DATABASE_TYPE == 'mysql':
            return self.MYSQL_DATABASE_URI
        elif self.DATABASE_TYPE == 'postgresql':
            return self.POSTGRES_DATABASE_URI
        else:
            return self.SQLITE_DATABASE_URI
    
    # Other Flask configurations
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SQLALCHEMY_TRACK_MODIFICATIONS = False 