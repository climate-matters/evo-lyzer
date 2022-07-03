"""Contains the Flask app and it's initialization."""
import os

from flask import Flask

from src.config import config
from src.dashboard import views
from src.dashboard.models import db

TEMPLATE_FOLDER = os.path.join(config['DEFAULT']['project_path'], 'templates')
STATIC_TEMPLATE = os.path.join(config['DEFAULT']['project_path'], 'static')
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_TEMPLATE)

# init database
DATABASE_PATH = os.path.join(config['DEFAULT']['project_path'], 'evo-lyzer.sqlite')
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(DATABASE_PATH)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# init blueprints and register them
views.init_app(app)


@app.route('/bkapp', methods=['GET'])
def bkapp_page():
    from flask import render_template
    return render_template("bkapp.html", script=script)
