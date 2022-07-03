import os
import sys

if os.path.abspath('../..') not in sys.path:
    sys.path.append(os.path.abspath('../..'))
    
import pickle    
    
from multiprocess import Pool
import tqdm

from src.dashboard.models import db, Collection, CollectionTopicProba, Document, TopicModelLoader, Topic, Subject
from src.dashboard.app import app

collection_docs = []
with app.app_context():
    for collection in tqdm.tqdm(Collection.query.all()):
        collection_docs.append([d.text for d in collection.documents])
        
model_loader = None
with app.app_context():
    for model_loader in TopicModelLoader.query.all():
        if (model_loader.model.num_epochs, model_loader.model.num_topics) == (1, 6):
            break
            
model_loader_pk = pickle.dumps(model_loader)

def get_new_author_topics_parallel(texts):
    if len(texts) == 0:
        return
    model_loader = pickle.loads(model_loader_pk)
    processed_docs = model_loader.model.preprocess(texts)
    topic_dist = model_loader.model.get_new_author_topics(processed_docs)
    return None

results = []
with Pool(4) as pool:
    for result in tqdm.tqdm(pool.imap(get_new_author_topics_parallel, collection_docs), total=len(collection_docs)):
        results.append(result)