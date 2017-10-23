# -*- encoding=utf-8 -*-

import logging
import sys
import json
import traceback

from time import time

class MSGException(Exception):
    def __init__( code, errid, exc=None):
        super(Exception, self).__init__(code, errid, exc)


def parse_message(body):
    """ Parse message body as json

        :param str body: A valid json message

            {
                'commmmand': 'name',
                'args'     : {
                }
            }

        :return: A tuple (name, args)
        :raises: MSGException: with code 400 if the parsing fail 
    """
    try:
        data=json.loads(body)
        name = data['command']
        args = data['args']
        return name, args 
    except Exception as e:
        traceback.print_exc()
        raise MSGException(400,"invalid_message",exc=e)



class BasicHandler(object):
    """ Basic commands handler
    """
    def __init__(self):
        self._registry = {}
        self.logger = logging

    def command(self,  name):
        """ Decorator for registering function as a
            command
        """
        def wrapper( fun ):
            self._registry[name] = fun
            return fun

        return wrapper

    def handle_error( self, request, e ):
        """ handle messge error """
        if not isinstance(e, MSGException):
            code, errid, exc = 500,"internal_error",e
        else:
            code, errid, exc = e.args

        self.logger.error("{} {} {}".format(code, errid, exc))
        return code, errid, exc


    def __call__( self, request ):
        """ Handle command
        """
        try:
            name, args = parse_message(request.body)
            fun = self._registry.get(name)
            if fun is None:
                raise MSGException(400,"invalid_command")
            
            fun( request, **args )

        except Exception as e:
            if not isinstance(e, MSGException):
                traceback.print_exc()
            self.handle_error(request, e)


class RPCHandler(BasicHandler):
    """ RPC commands handler
    """
    def handle_error(self, request, e):
        """ handle rpc message error 

            override BasicHandler to return an error reply 
            to the client
        """
        code, errid, exc = super(RPCHandler, self).handle_error(request, e)
        error_msg = dict( code=code, errid=errid, error=str(exc) )
        request.reply( json.dumps(error_msg), 
                content_type="application/json", 
                content_encoding="utf-8",
                headers={'x-return-code':code})
        return code, errid, exc



