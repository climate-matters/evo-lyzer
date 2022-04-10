"""Reads config file (config[.dev|.prod].ini) from project path."""

from configparser import ConfigParser
import os

__all__ = [
    'config',
]

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

ENVIRONMENT = 'production'
CONFIG_PATH = os.path.join(PROJECT_PATH, 'config.prod.ini')

if not os.path.exists(CONFIG_PATH):
    ENVIRONMENT = 'development'
    CONFIG_PATH = os.path.join(PROJECT_PATH, 'config.dev.ini')

if not os.path.exists(CONFIG_PATH):
    ENVIRONMENT = 'default'
    CONFIG_PATH = os.path.join(PROJECT_PATH, 'config.ini')

config = ConfigParser()
config.read(CONFIG_PATH)

config['DEFAULT']['project_path'] = PROJECT_PATH

ENV = ENVIRONMENT
