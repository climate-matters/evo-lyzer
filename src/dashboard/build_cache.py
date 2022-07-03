import os

import numpy as np
import pandas as pd

from src.config import config
from src.corpus.documents import load_documents
from src.dashboard.app import app
from src.dashboard.cache import cache
from src.dashboard.models import Collection, TopicModelLoader
from src.dashboard.plots.topics import prepare_topics
from src.dashboard.plots.analysis import prepare_analysis
from src.preprocessing.documents import filter_documents

num_topics, epochs = 6, 1
fn = 'v0-T{num_topics}-E{epochs}'.format(epochs=epochs, num_topics=num_topics)
model_path = os.path.join(config['DEFAULT']['project_path'], 'models', fn, 'model.pt')

model_loader = None
with app.app_context():
    for model_loader in TopicModelLoader.query.all():
        if (model_loader.model.num_epochs, model_loader.model.num_topics) == (1, 6):
            _ = model_loader.topics
            break

assert model_path == model_loader.path, 'Provided path does not match with the database. ' \
                                        'Found {}, Expected {}'.format(model_loader.path, model_path)


def _rebuild_topics_cache():
    filtered_documents = filter_documents(docs=load_documents(verbose=True), verbose=True)
    prepared_documents = model_loader.model.preprocess(filtered_documents)
    prepared_topic_vis = prepare_topics(topic_model=model_loader.model, documents=prepared_documents)
    cache.set('prepared_topic_vis', prepared_topic_vis)
    #
    document_topics = np.argmax(prepared_topic_vis['doc_topic_dists'], axis=1)
    document_topics_df = pd.DataFrame([
        {'id': _id, 'text': doc.text, 'author': doc.author_id, 'topic': topic}
        for _id, (doc, topic) in enumerate(zip(filtered_documents, document_topics))
    ])
    cache.set('prepared_document_topics', document_topics_df)


def _rebuild_analysis_cache():
    with app.app_context():
        collections = Collection.query.all()
        prepared_analysis = prepare_analysis(model_loader=model_loader, collections=collections)
    cache.set('prepared_analysis', prepared_analysis)


if __name__ == '__main__':
    _rebuild_topics_cache()
    _rebuild_analysis_cache()
