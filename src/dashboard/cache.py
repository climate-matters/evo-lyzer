import os

from cachelib import FileSystemCache

from src.config import config

path = os.path.join(config['DEFAULT']['project_path'], '.cache')
cache = FileSystemCache(path, threshold=0, default_timeout=0)
