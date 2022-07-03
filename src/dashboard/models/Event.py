"""Event Model"""
from src.dashboard.models import db


class Event(db.Model):
    """Event Model"""
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    collections = db.relationship('Collection', back_populates='event')

    def __init__(self, id=None, datetime=None, event_type=None, subjects=None):
        super(Event, self).__init__()
        if id is not None:
            self.id = id
        self.datetime = datetime
        self.event_type = event_type
        self.subjects = subjects

    def __repr__(self):
        return '<Event {0!r}>'.format(self.id)
