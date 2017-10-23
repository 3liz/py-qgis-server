# -*- encoding=utf-8 -*-

import tornado

from .basehandler import BaseHandler
from ..version import __version__
from ..config import config_to_dict


class RootHandler(BaseHandler):
    def get(self):

        response = dict(tornado_ver=tornado.version,
                        version = __version__,
                        author="3Liz",
                        author_url="http://3liz.com",
                        config=config_to_dict(),
                        documentation="http://{}/doc/".format(self.request.host))

        self.write_json(response)
