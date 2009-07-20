from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from utils import log_exception, Eval

e = Eval()

def index(request):
    return render_to_response("index.html")

@log_exception
def eval_cell(request):
    payload = request.POST["payload"]
    payload = simplejson.loads(payload)
    print "-"*70
    print "Got payload:"
    print payload
    print "evaluating"
    r = e.eval(payload["code"])
    print r
    print "-"*70
    return HttpResponse(r)
