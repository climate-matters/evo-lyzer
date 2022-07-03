from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

data_page = Blueprint('data_page', __name__)


@data_page.route('/data')
def index():
    """Index page of Dashboard.

    Shows a summary of dashboard content and provides links to
    relevant pages for more information.

    :return: template for index page.
    """
    try:
        return render_template('index.html')
    except TemplateNotFound as ex:
        abort(404)
