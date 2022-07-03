"""Functions related to database abstraction layer with SQLAlchemy."""
import datetime

import tqdm
from dateutil.relativedelta import relativedelta

import pandas as pd
from sqlalchemy.exc import NoResultFound

from src.corpus import load_tweets
from src.dataset import load_dataset
from src.dashboard.models import db, Topic, TopicModelLoader, Collection
from src.models import list_topic_models, format_topic_model_name, get_topic_model_path


def _register_models():
    from src.dashboard import models
    return models


def _create_admin_user(app):
    from src.dashboard.models import User
    with app.app_context():
        admin_user = User(
            username='admin',
            password='admin@123',
            first_name='First',
            last_name='Admin',
            email='admin@example.com'
        )
        db.session.add(admin_user)
        db.session.commit()


def _import_subjects(app):
    from src.dashboard.models import Subject
    from src.dashboard.models import Event
    with app.app_context():
        df = load_dataset()
        for row in df.itertuples():
            if pd.isna(row.position) and pd.isna(row.event_id) and (row.event_id != -1):
                continue
            first_name, last_name = row.name.split(None, 1)
            subject = Subject.query.get(row.subject_id)
            if subject is None:
                subject = Subject(
                    id=row.subject_id,
                    first_name=first_name,
                    last_name=last_name,
                    participant=row.participant,
                    twitter=row.twitter,
                    position=row.position,
                )
                db.session.add(subject)
                db.session.commit()
            event = Event.query.get(row.event_id)
            event_datetime = None
            if not pd.isna(row.datetime):
                event_datetime = row.datetime
            event_type = None
            if not pd.isna(row.event_type):
                event_type = row.event_type
            if event is None:
                event = Event(
                    id=row.event_id,
                    datetime=event_datetime,
                    event_type=event_type,
                )
                subject.events.append(event)
                db.session.commit()


def _import_topic_models(app):
    from src.dashboard.models import TopicModelLoader
    with app.app_context():
        for config in list_topic_models():
            name = format_topic_model_name(**config)
            path = get_topic_model_path(**config)
            model_loader = TopicModelLoader(name=name, path=path)
            model = model_loader.load()
            for i in range(model.num_topics):
                topic = Topic(label='Topic {}'.format(i + 1), is_relevant=False)
                model_loader.topics.append(topic)
            db.session.add(model_loader)
            db.session.commit()


def _import_collections_intra(app, verbose=False):
    from src.dashboard.models import Collection, Document, Subject
    with app.app_context():
        df = load_dataset()
        df_iter = df.itertuples()
        if verbose:
            df_iter = tqdm.tqdm(df_iter, total=df.shape[0], desc='Importing Collections')
        for item in df_iter:
            if pd.isna(item.datetime):
                continue
            # event_time_month_start
            event_time = datetime.datetime.combine(item.datetime, datetime.time.min).replace(day=1)
            # months before event
            start_time = event_time + relativedelta(months=-11)
            current_year, current_month = start_time.year, start_time.month
            before_months = []
            while (current_year < event_time.year) or \
                    ((current_year == event_time.year) and (current_month < event_time.month)):
                before_months.append(
                    {'twitter': item.twitter, 'year': current_year, 'month': current_month, 'lang': 'en'})
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
            # months after event
            end_time = event_time + relativedelta(months=+11)
            current_year, current_month = event_time.year, event_time.month
            after_months = []
            while (current_year < end_time.year) or \
                    ((current_year == end_time.year) and (current_month < end_time.month)):
                # skips the event month
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
                after_months.append(
                    {'twitter': item.twitter, 'year': current_year, 'month': current_month, 'lang': 'en'})
            try:
                subject = Subject.query.get(int(item.subject_id))
                if subject is None:
                    continue
                subject_id = subject.id
                event_id = int(item.event_id)
                collection_1 = Collection(
                    type='intra-subject', group='Before',
                    subject_id=subject_id, event_id=event_id
                )
                db.session.add(collection_1)
                document_ids = set()
                for tweet in load_tweets(filters=before_months, verbose=0):
                    tweet_id = int(tweet['id'])
                    tweet_text = tweet['text']
                    tweet_created_at = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    d = Document.query.get(tweet_id)
                    if d is None:
                        d = Document(id=tweet_id, text=tweet_text, author_id=subject_id, created_at=tweet_created_at)
                    if d.id not in document_ids:
                        collection_1.documents.append(d)
                        document_ids.add(d.id)
                collection_2 = Collection(
                    type='intra-subject', group='After',
                    subject_id=subject_id, event_id=int(item.event_id)
                )
                db.session.add(collection_2)
                document_ids = set()
                for tweet in load_tweets(filters=after_months, verbose=0):
                    tweet_id = int(tweet['id'])
                    tweet_text = tweet['text']
                    tweet_created_at = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    d = Document.query.get(tweet_id)
                    if d is None:
                        d = Document(id=tweet_id, text=tweet_text, author_id=subject_id, created_at=tweet_created_at)
                    if d.id not in document_ids:
                        collection_2.documents.append(d)
                        document_ids.add(d.id)
                db.session.commit()
            except FileNotFoundError as e:
                db.session.rollback()


def _import_collections_inter(app, verbose=False):
    from src.dashboard.models import Collection, Document, Subject
    with app.app_context():
        df = load_dataset()
        df_iter = df.itertuples()
        if verbose:
            df_iter = tqdm.tqdm(df_iter, total=df.shape[0], desc='Importing Collections')
        year = 2020
        for item in df_iter:
            subject = Subject.query.get(int(item.subject_id))
            if subject is None:
                continue
            subject_id = subject.id
            filters = []
            for month in range(1, 13):
                filters.append({'twitter': item.twitter, 'year': year, 'month': month, 'lang': 'en'})
            group = 'Non-Participant'
            if item.participant:
                group = 'Participant'
            try:
                c = Collection(
                    type='inter-subject', group=group,
                    subject_id=subject_id, event_id=None
                )
                db.session.add(c)
                document_ids = set()
                for tweet in load_tweets(filters=filters, verbose=0):
                    tweet_id = int(tweet['id'])
                    tweet_text = tweet['text']
                    tweet_created_at = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    d = Document.query.get(tweet_id)
                    if d is None:
                        d = Document(id=tweet_id, text=tweet_text, author_id=subject_id, created_at=tweet_created_at)
                    if d.id not in document_ids:
                        c.documents.append(d)
                        document_ids.add(d.id)
                db.session.commit()
            except FileNotFoundError as e:
                db.session.rollback()


def _import_collections_intra_consistency(app, verbose=False):
    from src.dashboard.models import Collection, Document, Subject
    with app.app_context():
        df = load_dataset()
        df_iter = df.itertuples()
        if verbose:
            df_iter = tqdm.tqdm(df_iter, total=df.shape[0], desc='Importing Collections')
        for item in df_iter:
            if pd.isna(item.datetime):
                continue
            # event_time_month_start
            event_time = datetime.datetime.combine(item.datetime, datetime.time.min).replace(day=1)
            # months before event
            start_time = event_time + relativedelta(months=-11)
            current_year, current_month = start_time.year, start_time.month
            before_months = []
            while (current_year < event_time.year) or \
                    ((current_year == event_time.year) and (current_month < event_time.month)):
                before_months.append(
                    {'twitter': item.twitter, 'year': current_year, 'month': current_month, 'lang': 'en'})
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
            # months after event
            end_time = event_time + relativedelta(months=+11)
            current_year, current_month = event_time.year, event_time.month
            after_months = []
            while (current_year < end_time.year) or \
                    ((current_year == end_time.year) and (current_month < end_time.month)):
                # skips the event month
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
                after_months.append(
                    {'twitter': item.twitter, 'year': current_year, 'month': current_month, 'lang': 'en'})
            try:
                subject = Subject.query.get(int(item.subject_id))
                if subject is None:
                    continue
                subject_id = subject.id
                event_id = int(item.event_id)
                for i, month in enumerate(before_months):
                    collection_1 = Collection(
                        type='intra-subject-consistency', group='Before-{}'.format(i + 1),
                        subject_id=subject_id, event_id=event_id
                    )
                    db.session.add(collection_1)
                    document_ids = set()
                    for tweet in load_tweets(filters=[month], verbose=0):
                        tweet_id = int(tweet['id'])
                        tweet_text = tweet['text']
                        tweet_created_at = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        d = Document.query.get(tweet_id)
                        if d is None:
                            d = Document(id=tweet_id, text=tweet_text, author_id=subject_id,
                                         created_at=tweet_created_at)
                        if d.id not in document_ids:
                            collection_1.documents.append(d)
                            document_ids.add(d.id)
                for i, month in enumerate(after_months):
                    collection_2 = Collection(
                        type='intra-subject-consistency', group='After-{}'.format(i + 1),
                        subject_id=subject_id, event_id=int(item.event_id)
                    )
                    db.session.add(collection_2)
                    document_ids = set()
                    for tweet in load_tweets(filters=[month], verbose=0):
                        tweet_id = int(tweet['id'])
                        tweet_text = tweet['text']
                        tweet_created_at = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        d = Document.query.get(tweet_id)
                        if d is None:
                            d = Document(id=tweet_id, text=tweet_text, author_id=subject_id,
                                         created_at=tweet_created_at)
                        if d.id not in document_ids:
                            collection_2.documents.append(d)
                            document_ids.add(d.id)
                db.session.commit()
            except FileNotFoundError as e:
                db.session.rollback()


def _import_collections_inter_consistency(app, verbose=False):
    from src.dashboard.models import Collection, Document, Subject
    with app.app_context():
        df = load_dataset()
        df_iter = df.itertuples()
        if verbose:
            df_iter = tqdm.tqdm(df_iter, total=df.shape[0], desc='Importing Collections')
        year = 2020
        for item in df_iter:
            subject = Subject.query.get(int(item.subject_id))
            if subject is None:
                continue
            subject_id = subject.id
            filters = []
            for month in range(1, 13):
                filters.append({'twitter': item.twitter, 'year': year, 'month': month, 'lang': 'en'})
            group = 'Non-Participant-{}'
            if item.participant:
                group = 'Participant-{}'
            try:
                for _filter in filters:
                    c = Collection(
                        type='inter-subject-consistency', group=group.format(_filter['month']),
                        subject_id=subject_id, event_id=None
                    )
                    db.session.add(c)
                    document_ids = set()
                    for tweet in load_tweets(filters=[_filter], verbose=0):
                        tweet_id = int(tweet['id'])
                        tweet_text = tweet['text']
                        tweet_created_at = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        d = Document.query.get(tweet_id)
                        if d is None:
                            d = Document(id=tweet_id, text=tweet_text, author_id=subject_id,
                                         created_at=tweet_created_at)
                        if d.id not in document_ids:
                            c.documents.append(d)
                            document_ids.add(d.id)
                db.session.commit()
            except FileNotFoundError as e:
                db.session.rollback()


def _update_collection_topic_dist(app, num_epochs=1, num_topics=6):
    with app.app_context():
        model_loader = None
        for model_loader in TopicModelLoader.query.all():
            if (model_loader.model.num_epochs, model_loader.model.num_topics) == (num_epochs, num_topics):
                break
        collections = Collection.query.all()
        for c in tqdm.tqdm(collections, desc='Inferring Author Topic Probabilities'):
            try:
                _ = c.get_topic_dist(model_loader)
            except NoResultFound as ex:
                topic_dist = None
                if len(c.documents) == 0:
                    topic_dist = [0.0 for _ in range(model_loader.model.num_topics)]
                if topic_dist is None:
                    processed_docs = model_loader.model.preprocess(c.documents)
                    topic_dist = model_loader.model.get_new_author_topics(processed_docs)
                if len(topic_dist) != model_loader.model.num_topics:
                    msg_fmt = 'Invalid number of topics. Found {} expected {}.'
                    msg = msg_fmt.format(len(topic_dist), model_loader.model.num_topics)
                    raise ValueError(msg)
                for i, proba in enumerate(topic_dist):
                    topic = model_loader.topics[i]
                    assert topic.index == i, 'invalid index access.'
                    try:
                        _ = c.get_topic_proba(topic)
                    except NoResultFound as ex:
                        c.set_topic_proba(topic=topic, proba=proba)
                db.session.commit()
                _ = c.get_topic_dist(model_loader)


def init_db(reset=False):
    """Import all modules here that might define models

     So that they will be registered properly on the metadata.
      Otherwise you will have to import them first before calling
      init_db()

    :return: None
    """
    from src.dashboard.app import app
    if reset:
        with app.app_context():
            db.drop_all()
            _register_models()
            db.create_all()
    _create_admin_user(app=app)
    _import_subjects(app=app)
    _import_topic_models(app=app)
    _import_collections_inter(app=app, verbose=True)
    _import_collections_inter_consistency(app=app, verbose=True)
    _import_collections_intra(app=app, verbose=True)
    _import_collections_intra_consistency(app=app, verbose=True)
    _update_collection_topic_dist(app=app)


if __name__ == '__main__':
    init_db(reset=True)
