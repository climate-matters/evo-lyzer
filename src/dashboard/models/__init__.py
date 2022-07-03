"""Module with all Models."""
from flask_sqlalchemy import SQLAlchemy

__all__ = [
    'db',
    'Collection',
    'CollectionTopicProba',
    'Document',
    'DocumentTopicProba',
    'Event',
    'Subject',
    'Participation',
    'Topic',
    'TopicModelLoader',
    'User',
]

db = SQLAlchemy()

from src.dashboard.models.User import User
from src.dashboard.models.Event import Event
from src.dashboard.models.Subject import Subject, Participation
from src.dashboard.models.Topic import Topic
from src.dashboard.models.TopicModelLoader import TopicModelLoader
from src.dashboard.models.Collection import Collection, CollectionTopicProba
from src.dashboard.models.Document import Document, DocumentTopicProba
