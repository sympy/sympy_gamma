from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django import forms

from google.appengine.api import users

from logic import Eval, SymPyGamma
from logic.resultsets import get_card

import settings
import models

import logging
import cgi
import random
import json

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
        return render_to_response(template, params)
    return _wrapper

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

@authenticate
def input(request, user):
    if request.method == "GET":
        form = SearchForm(request.GET)
        if form.is_valid():
            input = form.cleaned_data["i"]
            g = SymPyGamma()
            r = g.eval(input)

            if not r:
                r =  [{
                    "title": "Input",
                    "input": input,
                    "output": "Can't handle the input."
                }]
            elif user:
                if not models.Query.query(models.Query.text==input).get():
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

@authenticate
def about(request, user):
    return ("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        })

def eval_card(request, card_name, variable, expression):
    card = get_card(card_name)
    if card:
        from logic.logic import PREEXEC, mathjax_latex
        from sympy import sympify, Symbol, latex
        namespace = {}
        exec PREEXEC in {}, namespace
        evaluator = Eval(namespace)
        namespace['input_evaluated'] = sympify(expression)
        var = Symbol(variable.encode('utf-8'))

        r = card.eval(evaluator, var)
        result = {
            'value': repr(r),
            'title': card.format_title(namespace['input_evaluated']),
            'input': card.format_input(expression, var),
            'pre_output': latex(
                card.pre_output_function(expression, var)),
            'output': card.format_output(r, mathjax_latex)
        }
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        raise Http404

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
