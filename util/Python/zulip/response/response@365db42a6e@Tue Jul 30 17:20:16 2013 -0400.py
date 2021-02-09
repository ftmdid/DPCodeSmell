from __future__ import absolute_import

from django.http import HttpResponse, HttpResponseNotAllowed
import ujson

class HttpResponseUnauthorized(HttpResponse):
    status_code = 401

    def __init__(self, realm):
        HttpResponse.__init__(self)
        self["WWW-Authenticate"] = 'Basic realm="%s"' % (realm,)

def json_unauthorized(message):
    resp = HttpResponseUnauthorized("humbug")
    resp.content = ujson.dumps({"result": "error",
                                "msg": message})
    return resp

def json_method_not_allowed(methods):
    resp = HttpResponseNotAllowed(methods)
    resp.content = ujson.dumps({"result": "error",
        "msg": "Method Not Allowed",
        "allowed_methods": methods})
    return resp

def json_response(res_type="success", msg="", data={}, status=200):
    content = {"result": res_type, "msg": msg}
    content.update(data)
    return HttpResponse(content=ujson.dumps(content),
                        mimetype='application/json', status=status)

def json_success(data={}):
    return json_response(data=data)

def json_error(msg, data={}, status=400):
    return json_response(res_type="error", msg=msg, data=data, status=status)