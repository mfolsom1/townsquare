# models.py: SQLAlchemy models
# TODO: Define User, Event, RSVP classes here
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'Events'

    EventID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.String(200), nullable=False)
    Description = db.Column(db.Text)
    StartTime = db.Column(db.DateTime, nullable=False)
    EndTime = db.Column(db.DateTime, nullable=False)
    Location = db.Column(db.String(300), nullable=False)
    CreatedAt = db.Column(db.DateTime, default=datetime.now)