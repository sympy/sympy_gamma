from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django import forms

from google.appengine.api import users

import sympy
from logic import Eval, SymPyGamma
from logic.logic import mathjax_latex
from logic.resultsets import get_card, fake_sympy_function, find_result_set

import settings
import models

import logging
import cgi
import random
import json
import urllib2

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

@authenticate
def about(request, user):
    return ("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        })

def eval_card(request, card_name):
    card = get_card(card_name)
    if card:
        variable = request.GET.get('variable')
        expression = request.GET.get('expression')
        if not variable or not expression:
            raise Http404

        variable = urllib2.unquote(variable)
        expression = urllib2.unquote(expression)

        g = SymPyGamma()
        evaluator, evaluated, _ = g.eval_input(expression)
        convert_input, _ = find_result_set(evaluated)
        var = sympy.sympify(variable.encode('utf-8'))
        evaluated, var = convert_input(evaluated, var)
        evaluator.set('input_evaluated', evaluated)

        try:
            parameters = {}
            for key, val in request.GET.items():
                parameters[key] = ''.join(val)
            r = card.eval(evaluator, var, parameters)
        except ValueError as e:
            return HttpResponse(json.dumps({
                'error': e.message
            }), mimetype="application/json")

        result = {
            'value': repr(r),
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
