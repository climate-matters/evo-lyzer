"""TopicModel Model"""
import json

from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import reconstructor

from src.dashboard.models import db
from src.models import AuthorTopicModel


class TopicModelLoader(db.Model):
    """TopicModel Model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    path = db.Column(db.String(512), unique=True, nullable=False)
    topics = db.relationship('Topic', back_populates='topic_model_loader', order_by='Topic.index',
                             collection_class=ordering_list('index'))

    def __init__(self, name=None, path=None):
        super(TopicModelLoader, self).__init__()
        self.name = name
        self.path = path

    @property
    def num_topics(self):
        """Gets number of topics of model without loading whole model.

        :return: number of topics of this model.
        """
        if not hasattr(self, '_model_config_'):
            model_config_path = '{}.config.json'.format(self.path)
            with open(model_config_path, 'r', encoding='utf-8') as fp:
                _model_config_ = json.load(fp)
        return _model_config_['num_topics']

    @property
    def num_epochs(self):
        """Gets number of epochs of model without loading whole model.

        :return: number of epochs this model is trained on.
        """
        if not hasattr(self, '_model_config_'):
            model_config_path = '{}.config.json'.format(self.path)
            with open(model_config_path, 'r', encoding='utf-8') as fp:
                _model_config_ = json.load(fp)
        return _model_config_['passes']

    def __repr__(self):
        return '<TopicModelLoader {0!r}>'.format(self.id)

    @property
    def model(self):
        """Returns the loaded model that is related to this instance.

        :return: TopicModel
        """
        if (not hasattr(self, '_topic_model')) or (self._topic_model_ is None):
            self.load()
        return self._topic_model_

    def load(self):
        """Loads and returns an instance of the topic model
        described by this instance.

        Notes: No longer have to manually called to access model from loader.

        :return: `TopicModel`
        """
        if not hasattr(self, '_topic_model'):
            self._topic_model_ = None
        if self._topic_model_ is None:
            # noinspection PyAttributeOutsideInit
            self._topic_model_ = AuthorTopicModel.load(path=self.path)
        return self._topic_model_
