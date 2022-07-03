import os

from src.config import config

__all__ = [
    'format_topic_model_name',
    'parse_topic_model_name',
    'list_topic_models',
    'get_topic_model_path',
]


def parse_topic_model_name(name):
    """Parse path to topic models.

    :param name:
    :return:
    """
    try:
        vi, ti, ei = name.split('-')
        if not vi.upper().startswith('V'):
            raise ValueError
        if not ti.upper().startswith('T'):
            raise ValueError
        if not ei.upper().startswith('E'):
            raise ValueError
    except ValueError as ex:
        raise ValueError('invalid path to parse: {}'.format(name))
    return dict(
        version=vi[1:],
        epoch=ei[1:],
        num_topics=ti[1:],
    )


def format_topic_model_name(num_topics=None, epoch=None, version=None):
    """Parse path to topic models.

    :param num_topics:
    :param epoch:
    :param version:
    :return:
    """
    model_name = 'v{}'.format(version)
    if num_topics:
        model_name = '{}-T{}'.format(model_name, num_topics)
    if epoch:
        model_name = '{}-E{}'.format(model_name, epoch)
    return model_name


def list_topic_models(path=None):
    """List all available saved topic models fro the path provided.

    :param path:
    :return:
    """
    base_path = path
    if base_path is None:
        base_path = os.path.join(config['DEFAULT']['project_path'], 'models')
    models = []
    for file in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, file)):
            try:
                model_config = parse_topic_model_name(file)
                models.append(model_config)
            except ValueError as ex:
                pass
    return models


def get_topic_model_path(path=None, num_topics=None, epoch=None, version=0):
    """Gets the actual path to a model provided a base path to a folder that contains a topic model.

    :param path: base path to model.
    :param epoch: current epoch.
    :param num_topics: number of topics of the model.
    :param version: version information.
    :return: complete path to the model.
        path: str
    """
    base_path = path
    if base_path is None:
        base_path = os.path.join(config['DEFAULT']['project_path'], 'models')
    model_name = format_topic_model_name(num_topics=num_topics, epoch=epoch, version=version)
    output_path = os.path.join(base_path, model_name)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    return os.path.join(output_path, 'model.pt')
