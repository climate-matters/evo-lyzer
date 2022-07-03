"""Document Model"""
from src.dashboard.models import db


class DocumentTopicProba(db.Model):
    """Topic distribution of document."""
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), primary_key=True)
    document = db.relationship('Document', back_populates='_topic_proba')
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), primary_key=True)
    topic = db.relationship('Topic')
    proba = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return '<DocumentTopicProba {0!r},{0!r}>'.format(self.collection_id, self.topic.index)


class Document(db.Model):
    """Document Model"""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(512), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    author = db.relationship('Subject')
    created_at = db.Column(db.DateTime, nullable=True)
    _topic_proba = db.relationship('DocumentTopicProba', lazy='dynamic', back_populates='document')

    def set_topic_proba(self, topic, proba):
        """sets topic probability of provided topic.

        :param topic: topic to set the probability.
        :param proba: probability value to set.
        :return: None.
        """
        topic_proba = DocumentTopicProba(topic=topic, proba=proba)
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
        return '<Document {0!r}>'.format(self.id)
