#
# from bokeh.embed import components
# from bokeh.plotting import figure
# from bokeh.resources import INLINE
#
# @app.route('/bokeh')
# def bokeh():
#     # init a basic bar chart:
#     # http://bokeh.pydata.org/en/latest/docs/user_guide/plotting.html#bars
#     fig = figure(plot_width=600, plot_height=600)
#     fig.vbar(
#         x=[1, 2, 3, 4],
#         width=0.5,
#         bottom=0,
#         top=[1.7, 2.2, 4.6, 3.9],
#         color='navy'
#     )
#     # grab the static resources
#     js_resources = INLINE.render_js()
#     css_resources = INLINE.render_css()
#     # render template
#     script, div = components(fig)
#     return render_template(
#         'bokeh.html',
#         plot_script=script,
#         plot_div=div,
#         js_resources=js_resources,
#         css_resources=css_resources,
#     )
