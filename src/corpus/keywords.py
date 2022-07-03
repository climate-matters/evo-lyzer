import os
from collections import defaultdict

import pandas as pd

from src.config import config


def load_keywords(path=None, level='phrase'):
    """Loads keywords from the path provided.

    :param path: path to the list/mapping of keywords.
    :param level: determine the level at which keywords are loaded either at 'phrase' level or 'word' level.
    :return: a mapping of topics to a list of keywords.
        keywords: dict[str, list[str]]
    """
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'external', 'keywords.v3.2.csv')
    df = pd.read_csv(path)
    output = defaultdict(set)
    for row in df.itertuples():
        phrase, topic = row.raw_keyword, row.label
        if level == 'word':
            for token in phrase.split(' '):
                if len(token) > 2:
                    output[topic].add(token)
        else:
            output[topic].add(phrase.lower())
    return {k: list(v) for k, v in output.items()}


try:
    keywords = load_keywords()
except FileNotFoundError as ex:
    keywords = None
