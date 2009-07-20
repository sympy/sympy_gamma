from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from utils import log_exception, Eval

import logging

e = Eval()

def index(request):
    return render_to_response("index.html")

@log_exception
def eval_cell(request):
    payload = request.POST["payload"]
    payload = simplejson.loads(payload)
    logging.info("-"*70)
    logging.info("Got payload:")
    logging.info(payload)
    logging.info("evaluating...")
    r = e.eval(payload["code"])
    if r != "":
        r = '<pre class="shrunk">' + r + "</pre>"
    logging.info("encoding to JSON...")
    payload = {"result": r}
    payload = simplejson.dumps(payload)
    logging.info("Sending payload: " + payload)
    logging.info("-"*70)
    return HttpResponse(payload)
