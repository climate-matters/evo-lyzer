"""Subject Model"""
from src.dashboard.models import db

DocumentCollection = db.Table(
    'document_collection',
    db.Column('collection_id', db.ForeignKey('collection.id'), primary_key=True),
    db.Column('document_id', db.ForeignKey('document.id'), primary_key=True),
)


class CollectionTopicProba(db.Model):
    """Topic distribution of collection."""
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'), primary_key=True)
    collection = db.relationship('Collection', back_populates='_topic_proba')
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), primary_key=True)
    topic = db.relationship('Topic')
    proba = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<CollectionTopicProba {0!r},{0!r}>'.format(self.collection_id, self.topic_id)


class Collection(db.Model):
    """Collection Model"""
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    group = db.Column(db.String(50))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subject = db.relationship('Subject', back_populates='collections')
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    event = db.relationship('Event', back_populates='collections')
    documents = db.relationship('Document', secondary=DocumentCollection)
    _topic_proba = db.relationship('CollectionTopicProba', lazy='dynamic', back_populates='collection')

    __table_args__ = (
        db.UniqueConstraint('type', 'subject_id', 'event_id', 'group', name='_group_type_subject_event_uc'),
    )

    def set_topic_proba(self, topic, proba):
        """sets topic probability of provided topic.

        :param topic: topic to set the probability.
        :param proba: probability value to set.
        :return: None.
        """
        topic_proba = CollectionTopicProba(topic=topic, proba=proba)
        self._topic_proba.append(topic_proba)

    def get_topic_proba(self, topic):
        """Gets topic probability of provided topic.

        :param topic: topic to get the probability.
        :return: collection topic probability.
        """
        return self._topic_proba.filter_by(topic_id=topic.id).one()

    def get_topic_dist(self, topics):
        """Returns topic probability distributions in the order of topics provided.

        :param topics: Topics to include in the output.
            If TopicModelLoader is passed it will try to load topics from there.
        :return: list of topic probabilities.
        """
        topics_iter = topics
        if (topics.__class__.__module__.split('.')[-1] == 'TopicModelLoader') and hasattr(topics, 'topics'):
            topics_iter = topics.topics
        return [self.get_topic_proba(topic) for topic in topics_iter]

    def __repr__(self):
        return '<Collection {0!r}>'.format(self.id)
