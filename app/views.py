from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django import forms
import django

from google.appengine.api import users
from google.appengine.runtime import DeadlineExceededError

import sympy
from logic import Eval, SymPyGamma
from logic.logic import mathjax_latex
from logic.resultsets import get_card, find_result_set

import settings
import models

import os
import random
import json
import urllib2
import datetime
import traceback

LIVE_URL = '<a href="http://live.sympy.org">SymPy Live</a>'
LIVE_PROMOTION_MESSAGES = [
    'Need more control? Try ' + LIVE_URL + '.',
    'Want a full Python shell? Use ' + LIVE_URL + '.',
    'Experiment with SymPy at ' + LIVE_URL + '.',
    'Want to compute something more complicated?' +
    ' Try a full Python/SymPy console at ' + LIVE_URL + '.'
]

class MobileTextInput(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['autocorrect'] = 'off'
        attrs['autocapitalize'] = 'off'
        return super(MobileTextInput, self).render(name, value, attrs)

class SearchForm(forms.Form):
    i = forms.CharField(required=False, widget=MobileTextInput())

def authenticate(view):
    def _wrapper(request, **kwargs):
        user = users.get_current_user()
        template, params = view(request, user, **kwargs)
        if user:
            params['auth_url'] = users.create_logout_url("/")
            params['auth_message'] = "Logout"
        else:
            params['auth_url'] = users.create_login_url("/")
            params['auth_message'] = "Login"
        return template, params
    return _wrapper

def app_version(view):
    def _wrapper(request, **kwargs):
        template, params = view(request, **kwargs)
        version, deployed = os.environ['CURRENT_VERSION_ID'].split('.')
        deployed = datetime.datetime.fromtimestamp(long(deployed) / pow(2, 28))
        deployed = deployed.strftime("%d/%m/%y %X")
        params['app_version'] = version
        params['app_deployed'] = deployed
        return render_to_response(template, params)
    return _wrapper

@app_version
@authenticate
def index(request, user):
    form = SearchForm()

    if user:
        history = models.Query.query(models.Query.user_id==user.user_id())
        history = history.order(-models.Query.date).fetch(10)
    else:
        history = None

    return ("index.html", {
        "form": form,
        "MEDIA_URL": settings.MEDIA_URL,
        "main_active": "selected",
        "history": history
        })

@app_version
@authenticate
def input(request, user):
    if request.method == "GET":
        form = SearchForm(request.GET)
        if form.is_valid():
            input = form.cleaned_data["i"]
            g = SymPyGamma()
            r = g.eval(input)

            if not r:
                r = [{
                    "title": "Input",
                    "input": input,
                    "output": "Can't handle the input."
                }]
            elif user and not models.Query.query(models.Query.text==input).get():
                query = models.Query(text=input, user_id=user.user_id())
                query.put()

            # For some reason the |random tag always returns the same result
            return ("result.html", {
                "input": input,
                "result": r,
                "form": form,
                "MEDIA_URL": settings.MEDIA_URL,
                "promote_live": random.choice(LIVE_PROMOTION_MESSAGES)
                })

@app_version
@authenticate
def about(request, user):
    return ("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        })

def eval_card(request, card_name):
    variable = request.GET.get('variable')
    expression = request.GET.get('expression')
    if not variable or not expression:
        raise Http404

    variable = urllib2.unquote(variable)
    expression = urllib2.unquote(expression)

    g = SymPyGamma()

    parameters = {}
    for key, val in request.GET.items():
        parameters[key] = ''.join(val)

    try:
        result = g.eval_card(card_name, expression, variable, parameters)
    except ValueError as e:
        return HttpResponse(json.dumps({
            'error': e.message
        }), mimetype="application/json")
    except DeadlineExceededError:
        return HttpResponse(json.dumps({
            'error': 'Computation timed out.'
        }), mimetype="application/json")
    except:
        trace = traceback.format_exc(5)
        return HttpResponse(json.dumps({
            'error': ('There was an error in Gamma. For reference'
                      'the last five traceback entries are: ' + trace)
        }), mimetype="application/json")

    return HttpResponse(json.dumps(result), mimetype="application/json")

def remove_query(request, qid):
    user = users.get_current_user()

    if user:
        models.ndb.Key(urlsafe=qid).delete()
        response = {
            'result': 'success',
        }
    else:
        response = {
            'result': 'error',
            'message': 'Not logged in or invalid user.'
        }

    return HttpResponse(json.dumps(response), mimetype='application/json')

@app_version
def view_404(request):
    return ("404.html", {})

@app_version
def view_500(request):
    return ("500.html", {})
