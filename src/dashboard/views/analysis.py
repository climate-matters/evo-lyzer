from flask import Blueprint, render_template

from src.dashboard.cache import cache
from src.dashboard.models import TopicModelLoader
from src.dashboard.plots.analysis import (
    visualize_inter_subject_topic_relevance_distribution_divergence,
    visualize_intra_subject_topic_relevance_distribution_divergence,
)

analysis_page = Blueprint('analysis_page', __name__)


@analysis_page.route('/analysis')
def analysis():
    """Analysis page of Dashboard.

    :return: template for analysis page.
    """
    df = cache.get('prepared_analysis')
    model_loader = None
    for model_loader in TopicModelLoader.query.all():
        if (model_loader.model.num_epochs, model_loader.model.num_topics) == (1, 6):
            _ = model_loader.topics
            break
    relevant_topics_cols = []
    for topic in model_loader.topics:
        if topic.is_relevant:
            relevant_topics_cols.append(topic.label)
    plots = dict(
        intra_subject=dict(
            divergence=visualize_intra_subject_topic_relevance_distribution_divergence(
                df, relevant_topics_cols=relevant_topics_cols),
            consistency=[],
        ),
        inter_subject=dict(
            divergence=visualize_inter_subject_topic_relevance_distribution_divergence(
                df, relevant_topics_cols=relevant_topics_cols),
            consistency=[],
        ),
    )
    return render_template('analysis.html', plots=plots)
