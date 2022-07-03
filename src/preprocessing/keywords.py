"""Functions related to creating word priors for training topic models."""

import numpy as np

__all__ = [
    'create_eta',
    'create_word_prior_matrix',
]


def create_eta(keywords, vocab, num_topics, pseudo_count=1e7, normalize=True):
    """Creates word prior matrix.

    :param keywords:
    :param vocab:
    :param num_topics:
    :param pseudo_count:
    :param normalize:
    :param beta:
    :return:
    """
    # smoothing parameter
    beta = 0.01
    # create a (ntopics, nterms) matrix and fill with 1
    eta = np.full(shape=(num_topics, len(vocab)), fill_value=beta)
    if keywords is not None:
        # for each topic in the seed dict
        topic2id = {topic: i for i, topic in enumerate(keywords)}
        # for each topic in the seed dict
        for topic, tokens in keywords.items():
            # for each seed token that is in vocab
            for token in tokens:
                if token in vocab.token2id:
                    eta[topic2id[topic], vocab.token2id[token]] = pseudo_count + beta
    if normalize or (keywords is None):
        eta = np.divide(eta, eta.sum(axis=0))
    return eta


# alias
create_word_prior_matrix = create_eta
