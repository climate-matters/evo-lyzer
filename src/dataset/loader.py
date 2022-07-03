"""Loads data from the files (specific format).

Output of `load_*(path)` should be a `pandas.DataFrame` with following columns/attributes:
    subject_id - Unique ID of subject. Required.
    name - Name of subject. Required.
    position - Position of Subject. Nullable.
    event_id - ID of event. Nullable.
    event_type - Type of event. Nullable.
    datetime - Time of event. Nullable.
    twitter - Twitter ID of event. `np.null` values will be ignored in analysis. Nullable.
    participant - Whether subject is a participant. Nullable.
"""

import hashlib
import os

import numpy as np
import pandas as pd

from src.config import config

__all__ = [
    'load_dataset',
]

from src.errors import ValidationError


def _build_id(*args):
    col = args[0].replace(' ', '_', regex=True)
    for rows in args[1:]:
        col += '_' + rows.replace(' ', '_', regex=True)
    col = col.str.encode('utf-8')
    hash_ids = []
    hash_id2text = {}
    for text in col:
        hash_id = int(hashlib.sha1(text).hexdigest()[:10], 16)
        if (hash_id in hash_id2text) and (hash_id2text[hash_id] != text):
            raise BufferError
        hash_id2text[hash_id] = text
        hash_ids.append(hash_id)
    return hash_ids


def _load_participants(path=None):
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'external')
        path = os.path.join(path, 'Local and National CM CMN list May 2021.csv')
    df = pd.read_csv(path)
    df = df.assign(
        first_name=df['first_name'].str.title(),
        last_name=df['last_name'].str.title(),
        participant=np.nan,
    )
    df = df.assign(
        subject_id=_build_id(df['first_name'], df['last_name']),
        name=df['first_name'] + ' ' + df['last_name'],
        datetime=pd.to_datetime(df['join_date']),
        twitter=df['twitter'].str.replace(u'\u200f', '').str.strip().str.replace(r'(^@+)|([,.]+$)', '', regex=True),
        event_type='Joined'
    )
    df = df.assign(event_id=_build_id(df['datetime'].astype(str), df['event_type']))
    df = df.assign(event_id=df['event_id'].fillna(-1).astype(int))
    valid_idx = df['twitter'].str.match(r'^[A-Za-z0-9_]+$').astype(bool)
    df.loc[~valid_idx, ['twitter']] = np.nan
    columns = ['subject_id', 'name', 'position', 'participant', 'event_id', 'event_type', 'datetime', 'twitter']
    return df[columns] \
        .dropna(subset=['twitter']) \
        .drop_duplicates(subset=['subject_id', 'twitter']) \
        .reset_index(drop=True)


def _load_workshops(path=None):
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'external')
        path = os.path.join(path, 'Workshop Attendees - Version 1.csv')
    df = pd.read_csv(path)
    df = df.rename({
        'Climate Reporting Masterclass': 'Masterclass',
        'Online': 'Online',
        'In-person': 'In-person',
    }, axis=1)
    df = df.assign(
        first_name=df['First Name'].str.title(),
        last_name=df['Last Name'].str.title(),
        participant=np.nan,
    )
    df = df.assign(
        subject_id=_build_id(df['first_name'], df['last_name']),
        name=df['first_name'] + ' ' + df['last_name'],
        datetime=pd.to_datetime(df['First day postworkshop']),
        twitter=df['twitter'].str.replace(u'\u200f', '').str.strip().str.replace(r'(^@+)|([,.]+$)', '', regex=True),
        event_type='Workshop',
    )
    df = df.assign(event_id=_build_id(df['datetime'].astype(str), df['event_type']))
    df = df.assign(event_id=df['event_id'].fillna(-1).astype(int))
    valid_idx = df['twitter'].str.match(r'^[A-Za-z0-9_]+$').astype(bool)
    df.loc[~valid_idx, ['twitter']] = np.nan
    columns = ['subject_id', 'name', 'position', 'participant', 'event_id', 'event_type', 'datetime', 'twitter']
    return df[columns] \
        .dropna(subset=['twitter']) \
        .drop_duplicates(subset=['subject_id', 'twitter']) \
        .reset_index(drop=True)


def _load_weathercasters(path=None):
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'external')
        path = os.path.join(path, 'Wx Twitter Handles - Version 1.csv')
    df = pd.read_csv(path)
    df = df.assign(
        subject_id=_build_id(df['name']),
        event_id=-1,
        event_type=np.nan,
        twitter=df['twitter'].str.replace(u'\u200f', '').str.strip().str.replace(r'(^@+)|([,.]+$)', '', regex=True),
        datetime=np.nan,
        position='Meteorologist',
        participant=np.nan,
    )
    valid_idx = df['twitter'].str.match(r'^[A-Za-z0-9_]+$').astype(bool)
    df.loc[~valid_idx, ['twitter']] = np.nan
    columns = ['subject_id', 'name', 'position', 'participant', 'event_id', 'event_type', 'datetime', 'twitter']
    return df[columns] \
        .dropna(subset=['twitter']) \
        .drop_duplicates(subset=['subject_id', 'twitter']) \
        .reset_index(drop=True)


def _not_duplicated(df, raise_error=True):
    is_duplicated = df[['subject_id', 'twitter', 'event_id']].duplicated(keep=False)
    if is_duplicated.any():
        if raise_error:
            duplicates_df = df[is_duplicated]
            raise ValidationError('The subject\'s-events not uniquely identified. \n {}'.format(duplicates_df))
        return False
    return True


def load_dataset(path=None):
    """Loads the dataset containing the records.

    :param path: path to the root directory with files to load.
    :return: `pandas.DataFrame` with required fields for analysis.
    """
    if path is not None:
        path_1 = os.path.join(path, 'Local and National CM CMN list May 2021.csv')
        path_2 = os.path.join(path, 'Workshop Attendees - Version 1.csv')
        path_3 = os.path.join(path, 'Wx Twitter Handles - Version 1.csv')
    else:
        path_1, path_2, path_3 = None, None, None
    df_1 = _load_participants(path_1)
    _not_duplicated(df_1)
    df_2 = _load_workshops(path_2)
    _not_duplicated(df_2)
    df_3 = _load_weathercasters(path_3)
    _not_duplicated(df_3)
    df_c = pd.concat([df_1, df_2]) \
        .drop_duplicates(subset=['subject_id', 'twitter', 'event_id']) \
        .reset_index(drop=True)
    df = pd.concat([df_c, df_3]) \
        .drop_duplicates(subset=['subject_id', 'twitter', 'event_id'], keep='first') \
        .reset_index(drop=True)
    df = df.assign(participant=df['subject_id'].isin(df_c['subject_id']))
    columns = ['subject_id', 'name', 'position', 'participant', 'event_id', 'event_type', 'datetime', 'twitter']
    return df[columns]
