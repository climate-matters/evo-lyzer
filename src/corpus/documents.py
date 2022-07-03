"""Convert tweets to documents for training and testing Topic Models."""
import json
import os
import re

import tqdm
from flashtext import KeywordProcessor
from gensim.parsing import preprocessing as gpp

from src.config import config
from src.corpus import keywords


class CorpusDocument(object):
    """Represents a document for topic modeling."""
    keyword_processor = None
    url_pattern = re.compile('http[s]?://\S+')
    url_pattern_2 = re.compile('\Bhttp[s]?\S+')
    hashtag_pattern = re.compile('\B\#[a-zA-Z0-9_]+')
    mention_pattern = re.compile('\B\@[a-zA-Z0-9_]+')

    def __init__(self, text, author=None):
        self._text = text
        self._author = author
        self._hashtags = CorpusDocument.hashtag_pattern.findall(self._text)
        self._tokens = gpp.preprocess_string(self._text, filters=[
            gpp.lower_to_unicode,
            lambda x: CorpusDocument.url_pattern.sub(' ', x),
            lambda x: CorpusDocument.hashtag_pattern.sub(' ', x),
            lambda x: CorpusDocument.mention_pattern.sub(' ', x),
            lambda x: CorpusDocument.url_pattern_2.sub(' ', x),
            gpp.strip_tags,
            gpp.strip_punctuation,
            gpp.strip_numeric,
            lambda x: x + ' '.join(self._hashtags),
            gpp.remove_stopwords,
            gpp.strip_short,
            gpp.strip_multiple_whitespaces,
        ])
        if CorpusDocument.keyword_processor is None:
            CorpusDocument.keyword_processor = KeywordProcessor(case_sensitive=False)
            CorpusDocument.keyword_processor.add_keywords_from_dict(keywords)
        self.keywords = CorpusDocument.keyword_processor.extract_keywords(self._text)

    @property
    def text(self):
        """Gets text of document.

        :return:
            text: str
        """
        return self._text

    @property
    def author_id(self):
        """Gets author of document.

        :return:
            author: str
        """
        return self._author

    @property
    def tokens(self):
        """Gets a list of tokens of this document.

        :return:
            tokens: list[str]
        """
        return self._tokens

    @property
    def has_keyword(self):
        """Gets whether there is a keyword

        :return:
        """
        return len(self.keywords) > 0


def load_documents(path=None, verbose=False):
    """Loads all documents in the path provided.
    Each line should indicate a document with fields 'tweet', 'subject_id' at least.

    :param path: path to the jsonline file containing documents in each line.
    :param verbose: whether to print the loading progress.
    :return: generator of documents.
    """
    if path is None:
        path = os.path.join(config['DEFAULT']['project_path'], 'data', 'interim', 'tweets_intra_subject_analysis.jsonl')
    with open(path, 'r') as fp:
        lines = fp.readlines()
        # if not isinstance(verbose, bool) and (verbose is not None):
        #     lines = _progress(lines, verbose)
        # else:
        if verbose:
            lines = tqdm.tqdm(lines, desc='Loading Documents')
        for line in lines:
            record = json.loads(line)
            text = record['tweet']['text']
            author = record['subject_id']
            cd = CorpusDocument(text=text, author=author)
            yield cd


def _progress(lines, verbose):
    n = len(lines)
    for i, line in enumerate(lines):
        verbose((i + 1) * 100 // n)
        yield line
