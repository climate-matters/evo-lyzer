"""Wrapper around gensim's AuthorTopicModel."""
import copy
import json
import logging

import numpy as np
import pandas as pd
from gensim.models import AuthorTopicModel as GensimAuthorTopicModel, Phrases, CoherenceModel
from gensim.test.utils import temporary_file
import tqdm

from src.models.callbacks import CallbackList
from src.models.topic_model import TopicModel
from src.preprocessing.documents import preprocess_documents
from src.preprocessing.keywords import create_eta

__all__ = [
    'AuthorTopicModel',
]

logger = logging.getLogger(__name__)


class AuthorTopicModel(TopicModel):
    """Wrapper around gensim's AuthorTopicModel.

    The model correlates the authorship information with the topics to give a better insight
      on the subject knowledge of an author.

    Wrapper around the Gensim implementation of Rosen-Zvi and co-authors' paper by title:
      “The Author-Topic Model for Authors and Documents”.
    """

    def __init__(self, num_topics, passes=1, iterations=1, keywords=None, phrases_model=None,
                 callbacks=None, verbose=False):
        super(AuthorTopicModel, self).__init__()
        self.num_topics = num_topics
        self.num_epochs = passes
        self.iterations = iterations
        self.keywords = keywords
        self.phrases_model = phrases_model
        self.verbose = verbose
        self.callbacks = callbacks
        self._base_model = None
        self._current_epoch = 0

    def _get_iter(self, items, desc=None):
        if self.verbose:
            return tqdm.tqdm(items, desc=desc)
        return self.verbose

    def _get_callbacks(self):
        callbacks = []
        for x in self.callbacks:
            x = copy.copy(x)
            x.model = self
            callbacks.append(x)
        callbacks = CallbackList(callbacks)
        callbacks.model = self
        return callbacks

    def fit(self, docs, y=None):
        """Trains LDA model.

        :param docs:
        :param y:
        :return:
        """
        corpus, author2doc, _, dictionary, phrases_model = self.preprocess(docs)
        self.phrases_model = phrases_model
        self._current_epoch = 0
        epoch = 1
        eta = create_eta(self.keywords, dictionary, self.num_topics, len(corpus) // 100, normalize=True)
        callbacks = self._get_callbacks()
        with temporary_file('serialized') as s_path:
            callbacks.on_epoch_start(epoch=epoch)
            self._base_model = GensimAuthorTopicModel(
                self._get_iter(corpus, desc='Training the Model (Epoch {})'.format(epoch)),
                author2doc=author2doc,
                passes=1,
                iterations=self.iterations,
                id2word=dictionary,
                num_topics=self.num_topics,
                eta=eta,
                serialized=True,
                serialization_path=s_path,
                eval_every=None, )
            self._current_epoch = epoch
            callbacks.on_epoch_end(epoch=epoch)
            epoch += 1
            while epoch <= self.num_epochs:
                callbacks.on_epoch_start(epoch=epoch)
                self._base_model.update(
                    self._get_iter(corpus, desc='Training the Model (Epoch {})'.format(epoch)),
                    author2doc=author2doc
                )
                self._current_epoch = epoch
                callbacks.on_epoch_end(epoch=epoch)
                epoch += 1
        return self

    def transform(self, docs):
        """Infer the topics for the provided documents.

        :param docs: documents to extract the topics.
        :return: topic probability matrix.
        """
        corpus, _, _, _, _ = self.preprocess(docs)
        output = []
        for i in self._get_iter(range(len(corpus)), desc='Inferring the Document Topic Probabilities'):
            topic_proba = self._base_model.get_new_author_topics(corpus[i:i + 1])
            output.append(list(zip(*topic_proba))[1])
        return np.array(output)

    @property
    def corpus(self):
        """Returns corpus the model is trained on.

        :return: corpus
        """
        return self._base_model.corpus

    @property
    def author2doc(self):
        """Gets author2doc from topic model.

        :return: author2doc mapping.
        """
        return self._base_model.author2doc

    @property
    def dictionary(self):
        """Gets the fitted dictionary object.

        :return: `Dictionary` object
        """
        return self._base_model.id2word

    @property
    def id2word(self):
        """Alias for `self.dictionary`

        :return: self.dictionary
        """
        return self.dictionary

    def get_topic_terms(self, topic_id):
        """Gets topic terms.

        :param topic_id: int
            Topic id to extract the terms.
        :return:
            matrix: Term probability pairs.
        """
        return self._base_model.get_topic_terms(topic_id)

    def get_coherence(self, docs, coherence='u_mass'):
        """Get coherence value on the provided corpus.

        :param docs:
        :param coherence: {'u_mass', 'c_v', 'c_uci', 'c_npmi'}, optional
            Coherence measure to be used.
        :return:
        """
        corpus, author2doc, tokenized_docs, _, _ = self.preprocess(docs)
        if coherence == 'c_v':
            cm = CoherenceModel(model=self._base_model, texts=tokenized_docs, coherence='c_v')
        else:
            cm = CoherenceModel(model=self._base_model, corpus=corpus, coherence=coherence)
        return cm.get_coherence()

    def inference(self, docs):
        """Infer the document probabilities assuming all docs are from same new author.

        :param docs: documents.
        :return: document probability matrix.
        """
        corpus, _, _, _, _ = self.preprocess(docs)

        def _rho():
            return pow(self._base_model.offset + 1 + 1, -self._base_model.decay)

        def _rollback_new_author_changes():
            self._base_model.state.gamma = self._base_model.state.gamma[0:-1]

            del self._base_model.author2doc[new_author_name]
            a_id = self._base_model.author2id[new_author_name]
            del self._base_model.id2author[a_id]
            del self._base_model.author2id[new_author_name]

            for _new_doc_id in corpus_doc_idx:
                del self._base_model.doc2author[_new_doc_id]

        try:
            len_input_corpus = len(corpus)
        except TypeError:
            logger.warning('input corpus stream has no len(); counting documents')
            len_input_corpus = sum(1 for _ in corpus)
        if len_input_corpus == 0:
            raise ValueError('AuthorTopicModel.get_new_author_topics() called with an empty corpus')

        new_author_name = 'placeholder_name'
        # indexes representing the documents in the input corpus
        corpus_doc_idx = list(range(self._base_model.total_docs, self._base_model.total_docs + len_input_corpus))

        # Add the new placeholder author to author2id/id2author dictionaries.
        num_new_authors = 1
        author_id = self._base_model.num_authors
        if new_author_name in self._base_model.author2id:
            raise ValueError('self.author2id already has \'placeholder_name\' author')
        self._base_model.author2id[new_author_name] = author_id
        self._base_model.id2author[author_id] = new_author_name

        # Add new author in author2doc and doc into doc2author.
        self._base_model.author2doc[new_author_name] = corpus_doc_idx
        for new_doc_id in corpus_doc_idx:
            self._base_model.doc2author[new_doc_id] = [new_author_name]

        gamma_new = self._base_model.random_state.gamma(100., 1. / 100., (num_new_authors, self._base_model.num_topics))
        self._base_model.state.gamma = np.vstack([self._base_model.state.gamma, gamma_new])

        # Should not record the sstats, as we are going to delete the new author after calculated.
        try:
            results = self._base_model.inference(
                corpus, self._base_model.author2doc, self._base_model.doc2author, _rho(),
                collect_sstats=False, chunk_doc_idx=corpus_doc_idx
            )
        finally:
            _rollback_new_author_changes()
        return results

    def get_new_author_topics(self, docs, return_type=None):
        """Gets the topic distribution for new author based on the corpus provided.

        :param docs: documents
        :param return_type: return type [dict, np.ndarray, None]
        :return: topic probabilities
        """
        corpus, _, _, _, _ = self.preprocess(docs)
        topic_proba = self._base_model.get_new_author_topics(corpus)
        if return_type == dict:
            return dict(topic_proba)
        elif return_type == tuple:
            return topic_proba
        topic_proba = pd.DataFrame(topic_proba) \
            .set_index(0) \
            .reindex(range(self.num_topics)) \
            .fillna(0.0) \
            .reset_index(drop=True)
        if return_type is None:
            return topic_proba.iloc[:, 0].to_numpy()
        elif return_type == list:
            return topic_proba.iloc[:, 0].values.tolist()
        elif return_type == pd.DataFrame:
            return topic_proba
        elif return_type == pd.Series:
            return topic_proba.iloc[:, 0].drop_index()
        # defaults to numpy array
        return topic_proba.iloc[:, 0].to_numpy()

    def preprocess(self, docs):
        """Run default preprocessing on docs if required.

        :param docs: list[Document]
            Documents or processed docs. If already processed nothing to do.
        :return: tuple of (corpus, author2doc, tokenized_docs, dictionary, phrases_model)
            Processed data.
        """
        if isinstance(docs, dict):
            corpus = docs.get('corpus')
            author2doc = docs.get('author2doc')
            dictionary = docs.get('dictionary')
            tokenized_docs = docs.get('tokenized_docs')
            phrases_model = docs.get('phrases_model')
            return corpus, author2doc, tokenized_docs, dictionary, phrases_model
        elif isinstance(docs, tuple):
            return docs
        else:
            return preprocess_documents(
                docs, phrases_model=self.phrases_model, dictionary=self.dictionary,
                author2doc=self.author2doc, verbose=self.verbose,
            )

    def save(self, path):
        """Saves TopicModel at provided path.

        :param path: str
            Path to save the model.
        :return: None
        """
        model_config = dict(
            num_topics=self.num_topics,
            passes=self._current_epoch,
            iterations=self.iterations,
            keywords=self.keywords,
        )
        model_config_path = '{}.config.json'.format(path)
        with open(model_config_path, 'w', encoding='utf-8') as fp:
            json.dump(model_config, fp)
        phrases_model_path = '{}.phrases.pt'.format(path)
        self.phrases_model.save(phrases_model_path)
        self._base_model.save(path)

    @classmethod
    def load(cls, path):
        """Loads TopicModel from provided path.

        :param path: str
            Path to saved model.
        :return: saved model object of type `AuthorTopicModel`
        """
        model_config_path = '{}.config.json'.format(path)
        with open(model_config_path, 'r', encoding='utf-8') as fp:
            model_config = json.load(fp)
        phrases_model_path = '{}.phrases.pt'.format(path)
        phrases_model = Phrases.load(phrases_model_path)
        model_config['phrases_model'] = phrases_model
        base_model = GensimAuthorTopicModel.load(path)
        topic_model = AuthorTopicModel(**model_config)
        topic_model._base_model = base_model
        return topic_model
