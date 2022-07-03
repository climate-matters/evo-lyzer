from flask import Blueprint, render_template, url_for, request

from src.dashboard.cache import cache
from src.dashboard.plots.topics import visualize_topic_model
from src.dashboard.models import TopicModelLoader, db

topics_page = Blueprint('topics_page', __name__)


@topics_page.route('/topics', strict_slashes=False)
def topics():
    """Topics page of Dashboard.

    Shows a summary of topic model(s) and provides interface for labeling topics.

    :return: template for index page.
    """
    topic_index = request.args.get('topic', default=0, type=int) - 1
    page_index = request.args.get('page', default=1, type=int) - 1
    # load topic visualization
    ldavis_url = url_for('static', filename='packages/pyLDAvis/ldavis.v1.0.1.js')
    ldavis_css_url = url_for('static', filename='packages/pyLDAvis/ldavis.v1.0.1.css')
    topic_vis = cache.get('prepared_topic_vis')
    topic_vis_comp = visualize_topic_model(ldavis_url=ldavis_url, ldavis_css_url=ldavis_css_url, **topic_vis)
    #
    per_page = 100
    documents_table = ''
    if topic_index > -1:
        document_topics_df = cache.get('prepared_document_topics')
        documents_table = document_topics_df[document_topics_df['topic'] == topic_index] \
                              .drop(['topic', 'author'], axis=1) \
                              .iloc[page_index: (page_index + 1) * per_page, :] \
            .to_html(index=False, classes=['table'], border=0)
    #
    model_loader = None
    for _model_loader in TopicModelLoader.query.all():
        if (_model_loader.num_topics, _model_loader.num_epochs) == (6, 1):
            model_loader = _model_loader
    if model_loader is None:
        return 'Error...'
    selected_topic = None
    if topic_index > -1:
        selected_topic = model_loader.topics[topic_index]
    # updates
    is_relevant = request.args.get('is_relevant', default=None)
    if is_relevant is not None:
        selected_topic.is_relevant = is_relevant == 'true'
        db.session.commit()
    label = request.args.get('label', default=None)
    if label is not None:
        selected_topic.label = label
        db.session.commit()
    # render template
    return render_template(
        'topics.html',
        topic_vis=topic_vis_comp,
        num_topics=model_loader.num_topics,
        topics=model_loader.topics,
        topic=selected_topic,
        topic_index=topic_index,
        documents_table=documents_table,
    )
