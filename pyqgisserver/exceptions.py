""" Service exceptions
"""
import tornado.web

class HTTPError2(tornado.web.HTTPError):
    def __init__(self, status_code=500, log_message=None, *args, **kwargs):
        super(HTTPError2,self).__init__(status_code=status_code,
                                        log_message=log_message,
                                        *args,**kwargs)
        self.kwargs = kwargs



