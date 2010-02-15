from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils import simplejson
from django import forms

from google.appengine.api import users

from utils import log_exception
from logic import Eval, SymPyGamma

import settings

import logging
import cgi

class SearchForm(forms.Form):
    i = forms.CharField(required=False)

e = Eval()

def get_user_info():
    user = users.get_current_user()
    if user:
        return '<span class="email">%s</span>|<a href="">Settings</a>|<a href="%s">Sign out</a>' % \
                (user.email(), users.create_logout_url("/"))
    else:
        return '<a href="%s">Sign in</a>' % \
                                users.create_login_url("/")

def index(request):
    form = SearchForm()
    return render_to_response("index.html", {
        "form": form,
        "MEDIA_URL": settings.MEDIA_URL,
        "main_active": "selected",
        "user_info": get_user_info(),
        })

def input(request):
    if request.method == "GET":
        form = SearchForm(request.GET)
        if form.is_valid():
            input = form.cleaned_data["i"]
            g = SymPyGamma()
            r = g.eval(input)
            return render_to_response("result.html", {
                "input": input,
                "result": r,
                "form": form,
                "MEDIA_URL": settings.MEDIA_URL,
                "user_info": get_user_info(),
                })

def notebook(request):
    return render_to_response("nb.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "nb_active": "selected",
        "user_info": get_user_info(),
        })

def about(request):
    return render_to_response("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        "user_info": get_user_info(),
        })

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
        r = cgi.escape(r)
        r = '<pre class="shrunk">' + r + "</pre>"
    logging.info("encoding to JSON...")
    payload = {"result": r}
    payload = simplejson.dumps(payload)
    logging.info("Sending payload: " + payload)
    logging.info("-"*70)
    return HttpResponse(payload)
