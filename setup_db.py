import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import *
import click

@click.command()
@click.option('--db-type', type=click.Choice(['sqlite', 'mysql', 'postgresql']), 
              prompt='Choose database type', help='Database type to use')
def setup_database(db_type):
    """Initialize the database with the chosen type."""
    # Set environment variable for database type
    os.environ['DATABASE_TYPE'] = db_type
    
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        if db_type in ['mysql', 'postgresql']:
            click.echo(f"Setting up {db_type} database...")
            # Create database if it doesn't exist
            try:
                db.create_all()
                click.echo(f"Database tables created successfully for {db_type}")
            except Exception as e:
                click.echo(f"Error creating database: {str(e)}")
                return
        else:
            # For SQLite, just create the tables
            db.create_all()
            click.echo("SQLite database and tables created successfully")
        
        # Set default settings
        setting = Setting(key='currency', value='HUF')
        db.session.add(setting)
        db.session.commit()
        
        click.echo("Database setup completed successfully!")

if __name__ == '__main__':
    setup_database() 