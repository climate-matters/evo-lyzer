from flask import Flask

from src.dashboard.views.analysis import analysis_page
from src.dashboard.views.index import index_page
from src.dashboard.views.topics import topics_page


def init_app(app: Flask):
    """Initialize blueprints and registers them in the app.

    :param app: Flask app to register the blueprints.
    :return: app.
    """
    app.register_blueprint(index_page)
    app.register_blueprint(topics_page)
    app.register_blueprint(analysis_page)
    return app
