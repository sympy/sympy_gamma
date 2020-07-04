from __future__ import absolute_import

import sympy
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django import forms

from .constants import LIVE_PROMOTION_MESSAGES, EXAMPLES
from app.logic.logic import SymPyGamma

from app import settings
from . import models

import os
import random
import json
import six.moves.urllib.request, six.moves.urllib.parse, six.moves.urllib.error
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
import datetime
import traceback

import logging


ndb_client = models.ndb_client


class MobileTextInput(forms.widgets.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['autocorrect'] = 'off'
        attrs['autocapitalize'] = 'off'
        return super(MobileTextInput, self).render(name, value, attrs)


class SearchForm(forms.Form):
    i = forms.CharField(required=False, widget=MobileTextInput())


def app_meta(view):
    def _wrapper(request, *args, **kwargs):
        result = view(request, *args, **kwargs)
        version = os.environ['GAE_VERSION']

        try:
            template, params = result
            params['app_version'] = version
            params['sympy_version'] = sympy.__version__
            params['current_year'] = datetime.datetime.now().year
            return render(request, template, params)
        except ValueError:
            return result
    return _wrapper


@app_meta
def index(request):
    form = SearchForm()

    return ("index.html", {
        "form": form,
        "MEDIA_URL": settings.STATIC_URL,
        "main_active": "selected",
        "history": None,
        "examples": EXAMPLES
        })


def input_exists(input):
    with ndb_client.context():
        return models.Query.query(models.Query.text == input).get()


@app_meta
def input(request):
    logging.info('Got the input from user')
    if request.method == "GET":
        form = SearchForm(request.GET)
        if form.is_valid():
            input = form.cleaned_data["i"]

            if input.strip().lower() in ('random', 'example', 'random example'):
                return redirect('/random')

            g = SymPyGamma()
            r = g.eval(input)

            if not r:
                r = [{
                    "title": "Input",
                    "input": input,
                    "output": "Can't handle the input."
                }]

            if not input_exists(input):
                logging.info('Input does not exists')
                with ndb_client.context():
                    query = models.Query(text=input, user_id=None)
                    logging.info('query: %s' % query)
                    query.put()

            # For some reason the |random tag always returns the same result
            return ("result.html", {
                "input": input,
                "result": r,
                "form": form,
                "MEDIA_URL": settings.STATIC_URL,
                "promote_live": random.choice(LIVE_PROMOTION_MESSAGES)
                })


@app_meta
def about(request):
    return ("about.html", {
        "MEDIA_URL": settings.STATIC_URL,
        "about_active": "selected",
        })


def random_example(request):
    examples = []

    for category in EXAMPLES:
        for subcategory in category[1]:
            for example in subcategory[1]:
                if isinstance(example, tuple):
                    examples.append(example[1])
                else:
                    examples.append(example)

    return redirect('input/?i=' + six.moves.urllib.parse.quote(random.choice(examples)))


def _process_card(request, card_name):
    variable = request.GET.get('variable')
    expression = request.GET.get('expression')
    if not variable or not expression:
        raise Http404

    variable = six.moves.urllib.parse.unquote(variable)
    expression = six.moves.urllib.parse.unquote(expression)

    g = SymPyGamma()

    parameters = {}
    for key, val in request.GET.items():
        parameters[key] = ''.join(val)

    return g, variable, expression, parameters


def eval_card(request, card_name):
    g, variable, expression, parameters = _process_card(request, card_name)

    try:
        result = g.eval_card(card_name, expression, variable, parameters)
    except ValueError as e:
        return HttpResponse(json.dumps({
            'error': str(e)
        }), content_type="application/json")
    except Exception as e:
        logging.error(f'Exception: {e}')
        trace = traceback.format_exc(5)
        return HttpResponse(json.dumps({
            'error': ('There was an error in Gamma. For reference'
                      'the last five traceback entries are: ' + trace)
        }), content_type="application/json")

    return HttpResponse(json.dumps(result), content_type="application/json")


def get_card_info(request, card_name):
    g, variable, expression, _ = _process_card(request, card_name)

    try:
        result = g.get_card_info(card_name, expression, variable)
    except ValueError as e:
        return HttpResponse(json.dumps({
            'error': str(e)
        }), content_type="application/json")
    except Exception as e:
        logging.error(f"Exception: {e}")
        trace = traceback.format_exc(5)
        return HttpResponse(json.dumps({
            'error': ('There was an error in Gamma. For reference'
                      'the last five traceback entries are: ' + trace)
        }), content_type="application/json")

    return HttpResponse(json.dumps(result), content_type="application/json")


def get_card_full(request, card_name):
    g, variable, expression, parameters = _process_card(request, card_name)

    try:
        card_info = g.get_card_info(card_name, expression, variable)
        result = g.eval_card(card_name, expression, variable, parameters)
        card_info['card'] = card_name
        card_info['cell_output'] = result['output']

        html = render_to_string('card.html', {
            'cell': card_info,
            'input': expression
        })
    except ValueError as e:
        card_info = g.get_card_info(card_name, expression, variable)
        return HttpResponse(render_to_string('card.html', {
            'cell': {
                'title': card_info['title'],
                'input': card_info['input'],
                'card': card_name,
                'variable': variable,
                'error': str(e)
            },
            'input': expression
        }), content_type="text/html")
    except Exception as e:
        logging.error(f'Exception: {e}')
        trace = traceback.format_exc(5)
        return HttpResponse(render_to_string('card.html', {
            'cell': {
                'card': card_name,
                'variable': variable,
                'error': trace
            },
            'input': expression
        }), content_type="text/html")

    response = HttpResponse(html, content_type="text/html")
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'

    return response


def find_text_query(query):
    with ndb_client.context():
        return models.Query.query(models.Query.text == query.text)


@app_meta
def view_404(request, exception):
    return "404.html", {}


@app_meta
def view_500(request):
    return "500.html", {}
