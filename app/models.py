from app import db
from datetime import datetime

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tags = db.Column(db.String(255))
    recurring = db.Column(db.Boolean, default=False)
    recurring_interval = db.Column(db.String(50))

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    period = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    notification_threshold = db.Column(db.Float)

class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_date = db.Column(db.DateTime)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')

class IncomeEntry(db.Model):
    __tablename__ = 'income_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text)
    recurring = db.Column(db.Boolean, default=False)
    recurring_interval = db.Column(db.String(50))

class Setting(db.Model):
    __tablename__ = 'settings'
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255), nullable=False)

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    target_month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    predicted_amount = db.Column(db.Float, nullable=False)
    actual_amount = db.Column(db.Float)
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy = db.Column(db.Float)
    notes = db.Column(db.Text)

class PredictionCategory(db.Model):
    __tablename__ = 'prediction_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'))
    category = db.Column(db.String(100), nullable=False)
    predicted_amount = db.Column(db.Float, nullable=False)
    actual_amount = db.Column(db.Float)
    
    prediction = db.relationship('Prediction', backref=db.backref('categories', lazy=True)) 