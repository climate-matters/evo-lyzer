import json
import random
import re

import gensim
import jinja2
import numpy as np

import pyLDAvis
from pyLDAvis import urls
from pyLDAvis.utils import get_id

__all__ = [
    'prepare_topics',
    'visualize_topic_model',
]

_div_template = jinja2.Template('<div id={{ visid }} style="width:100%;"></div>')
_script_template = jinja2.Template('''<script type="text/javascript">
    let {{ visid_raw }}_data = {{ vis_json }};
    let ldavis = null;
    function LDAvis_load_lib(url, callback) {
        var s = document.createElement('script');
        s.src = url;
        s.async = true;
        s.onreadystatechange = s.onload = callback;
        s.onerror = function () {
            console.warn("failed to load library " + url);
        };
        document.getElementsByTagName("head")[0].appendChild(s);
    }
    if (typeof (LDAvis) !== "undefined") {
        // already loaded: just create the visualization
        !function (LDAvis) {
            ldavis = new LDAvis("#" + {{ visid }}, {{ visid_raw }}_data);
            return ldavis
        }(LDAvis);
    } else if (typeof define === "function" && define.amd) {
        // require.js is available: use it to load d3/LDAvis
        require.config({paths: {d3: "{{ d3_url[:-3] }}"}});
        require(["d3"], function (d3) {
            window.d3 = d3;
            LDAvis_load_lib("{{ ldavis_url }}", function () {
                ldavis = new LDAvis("#" + {{ visid }}, {{ visid_raw }}_data);
            });
        });
    } else {
        // require.js not available: dynamically load d3 & LDAvis
        LDAvis_load_lib("{{ d3_url }}", function () {
            LDAvis_load_lib("{{ ldavis_url }}", function () {
                ldavis = new LDAvis("#" + {{ visid }}, {{ visid_raw }}_data);
            })
        });
    };
</script>''')
_css_resource_template = jinja2.Template('<link rel="stylesheet" type="text/css" href="{{ ldavis_css_url }}">')
_js_resources = '''
            <script type="text/javascript">
                (function(history) {
                    var pushState = history.pushState;
                    history.pushState = function(state) {
                        if (typeof history.onchange == "function") {
                            history.onchange({state: state});
                        }
                        return pushState.apply(history, arguments);
                    };
                    var replaceState = history.replaceState;
                    history.replaceState = function(state) {
                        if (typeof history.onchange == "function") {
                            history.onchange({state: state});
                        }
                        return replaceState.apply(history, arguments);
                    };
                })(window.history);
                history.addEventListener = function (type, listener) {
                    if (type == 'change') {
                        history.onchange = listener;
                    }
                }
                function state_url(state) {
                    return location.origin + location.pathname + "#topic=" + state.topic +
                        "&lambda=" + state.lambda + "&term=" + state.term;
                }
            </script>
            '''


def prepare_topics(topic_model, documents):
    """Computes the topic visualization parameters for the provided documents.

    :param topic_model: Topic Model Builder.
    :param documents: Documents or preprocessed documents output.
    :return: self
    """
    corpus, _, _, _, _ = topic_model.preprocess(documents)
    _corpus = corpus
    if not gensim.matutils.ismatrix(corpus):
        corpus_csc = gensim.matutils.corpus2csc(corpus, num_terms=len(topic_model.dictionary))
    else:
        corpus_csc = corpus
        # Need corpus to be a streaming gensim list corpus for len and inference functions below:
        corpus = gensim.matutils.Sparse2Corpus(corpus_csc)
    vocab = list(topic_model.dictionary.token2id.keys())
    # TODO: add the hyperparam to smooth it out? no beta in online LDA impl.. hmm..
    # for now, I'll just make sure we don't ever get zeros...
    beta = 0.01
    fnames_argsort = np.asarray(list(topic_model.dictionary.token2id.values()), dtype=np.int_)
    term_freqs = corpus_csc.sum(axis=1).A.ravel()[fnames_argsort]
    term_freqs[term_freqs == 0] = beta
    doc_lengths = corpus_csc.sum(axis=0).A.ravel()
    assert term_freqs.shape[0] == len(topic_model.dictionary), \
        'Term frequencies and dictionary have different shape {} != {}'.format(
            term_freqs.shape[0], len(topic_model.dictionary))
    assert doc_lengths.shape[0] == len(corpus), \
        'Document lengths and corpus have different sizes {} != {}'.format(
            doc_lengths.shape[0], len(corpus))
    num_topics = topic_model.num_topics
    gamma, _ = topic_model.inference({'corpus': corpus})
    doc_topic_dists = gamma / gamma.sum(axis=1)[:, None]
    # check if document topics and number of topics do not match
    assert doc_topic_dists.shape[1] == num_topics, \
        'Document topics and number of topics do not match {} != {}'.format(
            doc_topic_dists.shape[1], num_topics)
    # get the topic-term distribution straight from gensim without
    # iterating over tuples
    base_model = topic_model._base_model
    if hasattr(base_model, 'lda_beta'):
        topic = base_model.lda_beta
    else:
        topic = base_model.state.get_lambda()
    topic = topic / topic.sum(axis=1)[:, None]
    topic_term_dists = topic[:, fnames_argsort]
    # assert topic sizes are correct
    assert topic_term_dists.shape[0] == doc_topic_dists.shape[1]
    # prepared docs
    return {
        'topic_term_dists': topic_term_dists,
        'doc_topic_dists': doc_topic_dists,
        'doc_lengths': doc_lengths,
        'vocab': vocab,
        'term_frequency': term_freqs
    }


def visualize_topic_model(topic_term_dists=None, doc_topic_dists=None, doc_lengths=None, vocab=None,
                          term_frequency=None, **kwargs):
    """Gets html components of topic visualization.

    :return:
    """
    visid = kwargs.get('visid', None)
    use_http = kwargs.get('use_http', True)
    data = pyLDAvis.prepare(
        topic_term_dists=topic_term_dists,
        doc_topic_dists=doc_topic_dists,
        doc_lengths=doc_lengths,
        vocab=vocab,
        term_frequency=term_frequency,
        sort_topics=False
    )
    d3_url = kwargs.get('d3_url', urls.D3_URL)
    ldavis_url = kwargs.get('ldavis_url', urls.LDAVISMIN_URL)
    ldavis_css_url = kwargs.get('ldavis_css_url', urls.LDAVIS_CSS_URL)
    if use_http:
        d3_url = d3_url.replace('https://', 'http://')
        ldavis_url = ldavis_url.replace('https://', 'http://')
    if visid is None:
        visid = 'ldavis_' + get_id(data) + str(int(random.random() * 1E10))
    elif re.search(r'\s', visid):
        raise ValueError('visid must not contain spaces')
    script = _script_template.render(
        visid=json.dumps(visid),
        visid_raw=visid,
        d3_url=d3_url,
        ldavis_url=ldavis_url,
        vis_json=data.to_json(),
        ldavis_css_url=ldavis_css_url
    )
    return dict(
        div=_div_template.render(visid=json.dumps(visid)),
        script=script,
        css_resources=_css_resource_template.render(ldavis_css_url=ldavis_css_url),
        js_resources=_js_resources
    )
