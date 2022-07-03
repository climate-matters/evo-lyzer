import shutil


class FileBackup(object):
    """Backup a file in a provided path."""
    def __init__(self, src, dist=None):
        self.src = src
        if dist is None:
            parts = self.src.split('.')
            parts_1, parts_2 = '.'.join(parts[:-1]), parts[-1]
            dist = '{}.backup.{}'.format(parts_1, parts_2)
        self.bak = dist

    def backup(self):
        """Performs backup operation.

        :return: None.
        """
        shutil.copy2(self.src, self.bak)

    def restore(self):
        """Performs restore operation.

        :return: None.
        """
        shutil.copy2(self.bak, self.src)

# database_path = os.path.join(config['DEFAULT']['project_path'], 'evo-lyzer.sqlite')
# fb = FileBackup(src=database_path)
# fb.restore()