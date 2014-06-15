# -*- encoding: utf-8 -*-

import sys
import os
import os.path
import logging

from glob import glob

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.wrappers import Response

from isso import make_app, wsgi
from isso.core import Config

logger = logging.getLogger("isso")


class Dispatcher(DispatcherMiddleware):
    """
    A dispatcher to support different websites. Dispatches based on
    a relative URI, e.g. /foo.example and /other.bar.
    """

    def __init__(self, *confs):

        self.isso = {}

        for i, conf in enumerate(map(Config.load, confs)):

            if not conf.get("general", "name"):
                logger.warn("unable to dispatch %r, no 'name' set", confs[i])
                continue

            self.isso["/" + conf.get("general", "name")] = make_app(conf)

        super(Dispatcher, self).__init__(self.default, mounts=self.isso)

    def __call__(self, environ, start_response):

        # clear X-Script-Name as the PATH_INFO is already adjusted
        environ.pop('HTTP_X_SCRIPT_NAME', None)

        return super(Dispatcher, self).__call__(environ, start_response)

    def default(self, environ, start_response):
        resp = Response("\n".join(self.isso.keys()), 404, content_type="text/plain")
        return resp(environ, start_response)

settings = os.environ.get("ISSO_SETTINGS")

if settings:
    if os.path.isdir(settings):
        conf_glob = os.path.join(os.environ["ISSO_SETTINGS"], '*.cfg')
        confs = glob(conf_glob)
        application = wsgi.SubURI(Dispatcher(*confs))
    else:
        confs = os.environ["ISSO_SETTINGS"].split(";")
        for path in confs:
            if not os.path.isfile(path):
                logger.fatal("%s: no such file", path)
                sys.exit(1)
    application = wsgi.SubURI(Dispatcher(*confs))
else:
    logger.fatal('environment variable ISSO_SETTINGS or ISSO_SETTINGS_DIR must be set')
