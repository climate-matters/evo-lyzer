"""Subject Model"""
from src.dashboard.models import db

Participation = db.Table(
    'participation',
    db.Column('subject_id', db.ForeignKey('subject.id'), primary_key=True),
    db.Column('event_id', db.ForeignKey('event.id'), primary_key=True),
)


class Subject(db.Model):
    """Subject Model"""
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    participant = db.Column(db.Boolean, nullable=False)
    twitter = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(120), nullable=False)
    events = db.relationship('Event', secondary=Participation)
    documents = db.relationship('Document', back_populates='author')
    collections = db.relationship('Collection', back_populates='subject')

    def __init__(self, id=None, first_name=None, last_name=None, email=None,
                 twitter=None, participant=None, position=None):
        super(Subject, self).__init__()
        if id is not None:
            self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.twitter = twitter
        self.participant = participant
        self.position = position

    def __repr__(self):
        return '<Subject {0!r}>'.format(self.id)
