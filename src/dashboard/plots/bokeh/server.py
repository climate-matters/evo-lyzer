# noinspection PyProtectedMember
from flask import _app_ctx_stack

import asyncio
from threading import Thread

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh.embed import server_document
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets


class BokehServer(object):
    """Bokeh Server"""

    def __init__(self, app=None):
        """Initialize instance.

        :param app:
        """
        self.app = app
        self.applications = {}
        self._sockets, self._port = None, None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app.

        :param app:
        :return:
        """
        # This is so that if this app is run using something like "gunicorn -w 4" then
        # each process will listen on its own port
        self._sockets, self._port = bind_sockets('localhost', 0)
        # app.config.setdefault('EXTRA_WEBSOCKET_ORIGINS', '')
        app.teardown_appcontext(self.teardown)

    # noinspection PyMethodMayBeStatic
    def teardown(self, exception):
        """Teardown app context.

        :param exception:
        :return:
        """
        ctx = _app_ctx_stack.top
        if hasattr(ctx, 'sqlite3_db'):
            # ctx.sqlite3_db.close()
            pass

    def register(self, path):
        """Registers a plotting app with server.

        :param path:
        :return:
        """

        def register_app_decorator(func):
            """The decorator for registering the app.

            :param func:
            :return:
            """
            self.applications.update({path: func})

        return register_app_decorator

    def server_document(self, path):
        """Returns server document of the App registered in path.

        :return:
        """
        script = server_document('http://localhost:{port}/{path}'.format(port=self._port, path=path.lstrip('/')))
        return script

    def _worker(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        bokeh_tornado = BokehTornado(self.applications, extra_websocket_origins=['127.0.0.1:5000', 'localhost:5000'])
        bokeh_http = HTTPServer(bokeh_tornado)
        bokeh_http.add_sockets(self._sockets)
        server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
        server.start()
        server.io_loop.start()

    def run(self):
        t = Thread(target=self._worker)
        t.daemon = True
        t.start()
