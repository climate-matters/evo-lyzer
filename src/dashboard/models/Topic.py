"""Topic Model"""
from src.dashboard.models import db


class Topic(db.Model):
    """Topic Model"""
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(50))
    is_relevant = db.Column(db.Boolean)
    topic_model_loader_id = db.Column(db.Integer, db.ForeignKey('topic_model_loader.id'))
    topic_model_loader = db.relationship('TopicModelLoader', back_populates='topics')

    def __init__(self, label='', is_relevant=False):
        self.label = label
        self.is_relevant = is_relevant

    def __repr__(self):
        return '<Topic {0!r}>'.format(self.id)
