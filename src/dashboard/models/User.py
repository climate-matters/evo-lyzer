"""User Model"""
from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug import security

from src.dashboard.models import db


class User(db.Model):
    """User Model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(50), unique=True)
    last_name = db.Column(db.String(50), unique=True)
    _password = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username=None, password=None, first_name=None, last_name=None, email=None):
        super(User, self).__init__()
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    @hybrid_property
    def password(self):
        """Password property.

        :return: gets the password.
        """
        return self._password

    @password.setter
    def password(self, plaintext):
        self._password = security.generate_password_hash(plaintext)

    def verify_password(self, plaintext):
        """Verify whether the password is correct.

        :param plaintext:
        :return:
        """
        return security.check_password_hash(self._password, plaintext)

    def __repr__(self):
        return '<User {0!r}>'.format(self.username)
