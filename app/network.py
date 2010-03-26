# This file was copied from http://lkcl.net/libcommonDjango.tgz and modified
# by Ondrej Certik

from django.utils import simplejson
from django.http import HttpResponse
import sys

class JSONRPCService:

    def __init__(self, method_map={}):
        self.method_map = method_map

    def add_method(self, name, method):
        self.method_map[name] = method

    def __call__(self, request):
        data = simplejson.loads(request.raw_post_data)
        id = data["id"]
        method = data["method"]
        params = [request,] + data["params"]
        if method in self.method_map:
            result = self.method_map[method](*params)
            return HttpResponse(simplejson.dumps({'id': id, 'result': result}))
        else:
            return HttpResponse(simplejson.dumps({'id': id,
                        'error': "No such method", 'code': -1}))


def jsonremote(service):
    """
    makes JSONRPCService a decorator so that you can write :

    from network import JSONRPCService, jsonremote

    chatservice = JSONRPCService()

    @jsonremote(chatservice)
    def login(request, user_name):
    (...)

    """

    def remotify(func):
        if isinstance(service, JSONRPCService):
            service.add_method(func.__name__, func)
        else:
            raise NotImplementedError('Service "%s" not found' % \
                    str(service.__name__))
        return func

    return remotify
