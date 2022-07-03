from src.models import get_topic_model_path
from src.models.callbacks._base import Callback

__all__ = [
    'ModelCheckpoint'
]


class ModelCheckpoint(Callback):
    """Callback to save model after each epoch."""

    def __init__(self, path, version=0):
        super(ModelCheckpoint, self).__init__()
        self.path = path
        self.version = version

    def on_epoch_end(self, epoch, logs=None):
        """

        :param epoch:
        :param logs:
        :return:
        """
        num_topics = self.model.num_topics
        path = get_topic_model_path(
            self.path,
            epoch=epoch,
            num_topics=num_topics,
            version=self.version
        )
        self.model.save(path=path)
