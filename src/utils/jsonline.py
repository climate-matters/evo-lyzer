import json

from src.errors import JSONLineDecodeError


def load(path):
    """Loads a jsonline file.

    :param path: path to jsonline file.
    """
    if path.endswith('.jsonl') or path.endswith('.jsonline'):
        with open(path) as fp:
            for line in fp.read().strip().split('\n'):
                line = line.strip()
                if len(line) == 0:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    raise JSONLineDecodeError('Error in line with content: {}'.format(line))
