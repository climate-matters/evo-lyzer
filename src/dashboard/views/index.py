from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

index_page = Blueprint('index_page', __name__)


@index_page.route('/')
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
