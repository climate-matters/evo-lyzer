"""Functions for filtering and loading twitter data.

There are three major functions.
1. Data collection with TwitterAPI.
2. Loading from local file system.
"""
import os

import tqdm

from src.config import config
from src.utils import jsonline

__all__ = [
    'load_availability',
    'load_tweets',
]


def load_availability(path=None):
    """Returns a generator for loading tweets from filesystem.

    Note: depending on the size of the dataset it might not be a good idea to load full dataset to the memory.

    :param path: path to the root directory containing tweets.
    """
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'raw', 'tweets')
    values = set()
    usernames = os.listdir(path)
    for username in tqdm.tqdm(usernames, desc='Loading Availability'):
        timeline_fp = os.path.join(path, username)
        if os.path.isdir(timeline_fp):
            for fn in os.listdir(timeline_fp):
                fn = str(fn)
                if not fn.endswith('.jsonl'):
                    continue
                year, month = fn[:-6].split('-')
                assert len(year) == 4, 'Year must be represented with four digits.'
                assert len(month) == 2, 'Month must be represented with two digits with leading zeros if required.'
                values.add((username, int(year), int(month)))
    keys = ('twitter', 'year', 'month')
    result = [dict(zip(keys, value)) for value in values]
    return result


def load_tweets(path=None, filters=None, verbose=1):
    """Returns a generator for loading tweets from filesystem.

    Note: depending on the size of the dataset it might not be a good idea to load full dataset to the memory.

    :param path: path to the root directory containing tweets.
    :param filters: list of files metadata for loading. Should be a dict with keys ['twitter', 'year', 'month'].
    :param verbose: whether to show progress bar.
    """
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'raw', 'tweets')
    if filters is None:
        filters = load_availability(path=path)
    if verbose:
        filters = tqdm.tqdm(filters, desc='Loading Documents')
    for item in filters:
        year, month = item['year'], item['month']
        lang = item.get('lang', None)
        fn = '{}-{:02}.{}'.format(year, month, 'jsonl')
        twitter = item['twitter']
        fp = os.path.join(path, twitter, fn)
        for tweet in jsonline.load(fp):
            tweet['username'] = twitter
            if (lang is None) or (tweet.get('lang') == lang):
                yield tweet
