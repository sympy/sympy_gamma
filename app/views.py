from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from utils import log_exception

def index(request):
    return render_to_response("index.html")

@log_exception
def eval_cell(request):
    payload = request.POST["payload"]
    print payload
    payload = simplejson.loads(payload)
    print payload
    return HttpResponse("OK")
