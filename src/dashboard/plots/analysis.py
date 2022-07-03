import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.resources import INLINE
from scipy import stats
import tqdm

POSITIONS_MAP = {
    'Meteorologist': 'Meteorologist',
    'Reporter': 'Reporter',
    'Producer': 'Reporter',
    'Journalist': 'Reporter',
    'Editor': 'Reporter',
    'Other': 'Other',
    'Student': 'Other',
    'Academic': 'Other',
    'Met Producer': 'Meteorologist',
    'News Director': 'Reporter',
    'Vice President': 'Reporter',
    'Photographer': 'Reporter'
}


def _index_filter(df, **kwargs):
    filters = None
    for key, value in kwargs.items():
        item_filter = df.index.get_level_values(key) == value
        if filters is None:
            filters = item_filter
        else:
            filters = filters & item_filter
    return filters


def _histplot(data=None, *, x=None, y=None, weights=None, bins='auto', stat='count', hue=None,
              cumulative=False, kde=False, kde_kws=None, legend=True, legend_kws=None, fig_kwgs=None):
    if legend_kws is None:
        legend_kws = {}
    if fig_kwgs is None:
        fig_kwgs = {}
    if kde_kws is None:
        kde_kws = {}
    density = stat == 'density'
    group_index = data[hue]
    measured = data.loc[:, y if y is not None else x] if isinstance(data, pd.DataFrame) else data
    default_x_axis_label = x if x is not None else y if y is not None else 'x'
    fig_kwgs['x_axis_label'] = fig_kwgs.get('x_axis_label', default_x_axis_label)
    fig_kwgs['y_axis_label'] = fig_kwgs.get('y_axis_label', 'Density' if density else 'Frequency')
    # plot
    fig = figure(tools='', background_fill_color="#fafafa",
                 sizing_mode='scale_width', **fig_kwgs)
    group_values = group_index.unique()
    _colors = ['dodgerblue', 'coral']
    group_colors = dict(zip(group_values, _colors))
    edges = np.histogram_bin_edges(measured, bins=bins, range=None, weights=weights)
    x = np.linspace(edges[0], edges[-1], 2000)
    for group in group_values:
        group_color = group_colors[group]
        xs = measured[group_index == group]
        hist, _ = np.histogram(xs, density=density, bins=edges)
        fig.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color=group_color,
                 line_color='white', alpha=0.5, legend_label=group)
        if kde:
            kernel = stats.gaussian_kde(xs)
            pdf = kernel(x)
            fig.line(x, pdf, line_color=group_color, line_width=2, alpha=0.5)
        if cumulative:
            # cdf = (1+scipy.special.erf((x-mu)/np.sqrt(2*sigma**2)))/2
            # fig.line(x, cdf, line_color="orange", line_width=2, alpha=0.7, legend_label="CDF")
            pass
    fig.y_range.start = 0
    if legend:
        fig.legend.location = legend_kws.get('location', 'center_right')
        fig.legend.background_fill_color = legend_kws.get('background_fill_color', '#fefefe')
    fig.xaxis.axis_label = fig_kwgs.get('x_axis_label', 'x')
    fig.yaxis.axis_label = fig_kwgs.get('y_axis_label', 'y')
    fig.grid.grid_line_color = fig_kwgs.get('grid_line_color', 'white')
    return fig


def prepare_analysis(model_loader, collections):
    data, tuples = [], []
    for c in tqdm.tqdm(collections, desc='Collecting Collection Probabilities'):
        topics = c.get_topic_dist(model_loader)
        proba_sum = 0
        for t in topics:
            proba_sum += t.proba
        if c.subject is None:
            continue
        event_id = 'None'
        event_type = 'None'
        if c.event:
            event_id = c.event.id
            event_type = c.event.event_type
        groups = c.group.split('-')
        index = 0
        try:
            index = int(groups[-1])
            group = '-'.join(groups[:-1])
        except ValueError as ex:
            group = '-'.join(groups)
        tuples += [(c.id, c.type, group, index, c.subject_id, event_id, event_type, c.subject.position)]
        data.append({topic_proba.topic.label: topic_proba.proba for i, topic_proba in enumerate(topics)})
    index_names = ['id', 'type', 'group', 'index', 'subject_id', 'event_id', 'event_type', 'position']
    index = pd.MultiIndex.from_tuples(tuples, names=index_names)
    df = pd.DataFrame.from_records(data)
    df.index = index
    return df


def visualize_inter_subject_topic_relevance_distribution_divergence(df, **kwargs):
    """Gets html components of topic visualization.

    :return:
    """
    relevant_topics_cols = kwargs.get('relevant_topics_cols')
    if relevant_topics_cols is None:
        relevant_topics_cols = kwargs.get('relevant_topics', df.columns[:-1].tolist())
    fig_df = df[_index_filter(df, type='inter-subject')].loc[:, relevant_topics_cols] \
        .sum(axis=1) \
        .reset_index(drop=False, name='Topic Relevance')
    fig_df = fig_df.assign(Group=fig_df['group'])
    fig_df = fig_df.assign(Position=fig_df['position'].map(POSITIONS_MAP))
    fig_df = fig_df[fig_df['event_type'] == 'None']
    fig_df = fig_df[fig_df['Position'] == 'Meteorologist']
    fig_kwgs = dict(x_axis_label='Topic Relevance')
    fig = _histplot(fig_df, x='Topic Relevance', hue='Group', kde=True, stat='density', fig_kwgs=fig_kwgs)
    plots = []
    script, div = components(fig)
    plots.append(dict(
        div=div,
        script=script,
        css_resources=INLINE.render_css(),
        js_resources=INLINE.render_js(),
        properties=[
            dict(name='Event Type', value='None'),
            dict(name='Position', value='Meteorologist'),
        ]
    ))
    return plots


def visualize_intra_subject_topic_relevance_distribution_divergence(df, **kwargs):
    """Gets html components of topic visualization.

    :return:
    """
    relevant_topics_cols = kwargs.get('relevant_topics_cols')
    if relevant_topics_cols is None:
        relevant_topics_cols = kwargs.get('relevant_topics', df.columns[:-1].tolist())
    fig_df = df[_index_filter(df, type='intra-subject')].loc[:, relevant_topics_cols] \
        .sum(axis=1) \
        .reset_index(drop=False, name='Topic Relevance')
    fig_df = fig_df.assign(EventType=fig_df['event_type'])
    fig_df = fig_df.assign(Group=fig_df['group'])
    fig_df = fig_df.assign(Position=fig_df['position'].map(POSITIONS_MAP))
    fig_kwgs = dict(x_axis_label='Topic Relevance')
    rows = list(fig_df['Position'].unique()) + [None]
    cols = list(fig_df['EventType'].unique()) + [None]
    plots = []
    for i, position in enumerate(rows):
        if position == 'Other':
            continue
        for j, event_type in enumerate(cols):
            if (event_type is None) and (position is None):
                sub_fig_df = fig_df
            elif event_type is None:
                sub_fig_df = fig_df[fig_df['Position'] == position]
            elif position is None:
                sub_fig_df = fig_df[fig_df['EventType'] == event_type]
            else:
                sub_fig_df = fig_df[(fig_df['Position'] == position) & (fig_df['EventType'] == event_type)]
            plot = _histplot(
                sub_fig_df, x='Topic Relevance', hue='Group',
                kde=True, stat='density', fig_kwgs=fig_kwgs
            )
            script, div = components(plot)
            plots.append(dict(
                div=div,
                script=script,
                css_resources=INLINE.render_css(),
                js_resources=INLINE.render_js(),
                properties=[
                    dict(name='Event Type', value=str(event_type)),
                    dict(name='Position', value=str(position)),
                ],
            ))
    return plots
