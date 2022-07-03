"""Process documents."""
import random
from collections import defaultdict

import numpy as np
import six
import tqdm
from gensim.corpora import Dictionary
from gensim.models import Phrases
from gensim.models.phrases import ENGLISH_CONNECTOR_WORDS
# noinspection PyPackageRequirements
from imblearn.under_sampling import RandomUnderSampler

__all__ = [
    'filter_documents',
    'filter_documents_for_topic_modeling',
    'preprocess_documents',
]


def filter_documents_for_topic_modeling(docs, verbose=False):
    """Filter documents for training topic models.

    :param docs: documents to filter.
    :param verbose: whether to show progress in terminal.
    :return: filtered documents.
    """
    filtered = []
    for doc in docs:
        if len(doc.tokens) > 5:
            filtered.append(doc)
    docs = filtered
    unique_docs = []
    observed_set = set()
    docs_iter = docs
    if verbose:
        docs_iter = tqdm.tqdm(docs, desc='Extracting Unique Documents')
    for doc in docs_iter:
        doc_tokens = tuple(sorted(doc.tokens))
        if doc_tokens not in observed_set:
            unique_docs.append(doc)
            observed_set.add(doc_tokens)
    if verbose:
        print('{} duplicates removed from a total of {} documents.'.format(len(docs) - len(unique_docs), len(docs)))
    labels = set()
    for i, doc in enumerate(unique_docs):
        labels.update(doc.keywords)
    labels = list(labels) + ['other']
    label2id = dict(zip(labels, range(len(labels))))
    rus = RandomUnderSampler(sampling_strategy='majority', random_state=42)
    X, y = [], []
    for i, doc in enumerate(unique_docs):
        X.append([i])
        y_doc = [0 for _ in range(len(label2id))]
        label = 'other'
        if len(doc.keywords) > 0:
            label = random.choice(doc.keywords)
        y_doc[label2id[label]] = 1
        y.append(y_doc)
    X = np.array(X)
    y = np.array(y)
    X_res, y_res = rus.fit_resample(X, y)
    docs_sample = [unique_docs[x[0]] for x in tqdm.tqdm(X_res, desc='Selecting Documents')]
    return docs_sample


def _get_corpus_documents(docs):
    from src.dashboard.models import Document
    from src.corpus.documents import CorpusDocument
    result = []
    for doc in docs:
        if isinstance(doc, Document):
            cd = CorpusDocument(doc.text, author=doc.author_id)
            result.append(cd)
        elif isinstance(doc, six.string_types):
            cd = CorpusDocument(doc, author='<Unknown>')
            result.append(cd)
        elif isinstance(doc, CorpusDocument):
            result.append(doc)
        else:
            raise ValueError('invalid corpus document format.')
    assert len(result) == len(docs), 'documents went missing during processing.'
    return result


def preprocess_documents(docs, return_type='tuple', phrases_model=None, dictionary=None,
                         author2doc=None, verbose=False):
    """Preprocess documents and returns a dict containing dictionary, corpus, and author2doc.

    :param docs: the documents to process.
    :param phrases_model: a prebuilt phrase model available.
    :param dictionary: dictionary.
    :param author2doc: dictionary.
    :param return_type: return type as string.
    :param verbose: whether to show progress in terminal.
    :return:
    """
    # TODO: add params min_df=0, max_df=1.0, keep_n=None,
    # :param min_df: minimum document frequency of token.
    # :param max_df: maximum document frequency of token (as a fraction of number of documents).
    # :param keep_n: number of words to keep in dictionary.
    docs = _get_corpus_documents(docs)
    tokenized_docs = []
    docs_iter = docs
    if verbose:
        docs_iter = tqdm.tqdm(docs, desc='Extracting Tokens')
    for i, doc in enumerate(docs_iter):
        tokenized_docs.append(doc.tokens)
    # Add phrases to docs (only ones that appear 20 times or more).
    if isinstance(phrases_model, str):
        try:
            phrases_model = Phrases.load(phrases_model)
        except FileNotFoundError as ex:
            phrases_model = None
    if phrases_model is None:
        phrases_model = Phrases(tokenized_docs, min_count=10, threshold=1, connector_words=ENGLISH_CONNECTOR_WORDS)
        phrases_model.freeze()
    tokenized_docs_iter = range(len(tokenized_docs))
    if verbose:
        tokenized_docs_iter = tqdm.tqdm(tokenized_docs_iter, desc='Extracting Phrases')
    for idx in tokenized_docs_iter:
        for token in phrases_model[tokenized_docs[idx]]:
            if '_' in token:
                tokenized_docs[idx].append(token)
    # dictionary
    if dictionary is None:
        dictionary = Dictionary(tokenized_docs)
    _ = dictionary[0]  # initialize dictionary.id2token
    # keep_tokens = [y.lower() for x in keywords.values() for y in x]
    # dictionary.filter_extremes(no_below=min_df, no_above=max_df, keep_n=keep_n, keep_tokens=keep_tokens)
    # corpus
    corpus = []
    tokenized_docs_iter = tokenized_docs
    if verbose:
        tokenized_docs_iter = tqdm.tqdm(tokenized_docs, desc='Extracting Bag of Words')
    for tokenized_doc in tokenized_docs_iter:
        corpus.append(dictionary.doc2bow(tokenized_doc))
    # author2doc
    if author2doc is None:
        author2doc = defaultdict(list)
        docs_iter = docs
        if verbose:
            docs_iter = tqdm.tqdm(docs, desc='Extracting Author Docs')
        for i, doc in enumerate(docs_iter):
            author2doc[doc.author_id].append(i)
        author2doc = dict(author2doc)
    # return all params
    if return_type == 'dict':
        return {
            'corpus': corpus,
            'author2doc': author2doc,
            'tokenized_docs': tokenized_docs,
            'dictionary': dictionary,
            'phrases_model': phrases_model,
        }
    else:
        return corpus, author2doc, tokenized_docs, dictionary, phrases_model


# alias
filter_documents = filter_documents_for_topic_modeling
