from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils import simplejson
from django import forms

from logic import Eval, SymPyGamma

import settings

import logging
import cgi
import random

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

e = Eval()

def index(request):
    form = SearchForm()
    return render_to_response("index.html", {
        "form": form,
        "MEDIA_URL": settings.MEDIA_URL,
        "main_active": "selected",
        })

def input(request):
    if request.method == "GET":
        form = SearchForm(request.GET)
        if form.is_valid():
            input = form.cleaned_data["i"]
            g = SymPyGamma()
            r = g.eval(input)

            # For some reason the |random tag always returns the same result
            return render_to_response("result.html", {
                "input": input,
                "result": r,
                "form": form,
                "MEDIA_URL": settings.MEDIA_URL,
                "promote_live": random.choice(LIVE_PROMOTION_MESSAGES)
                })

def about(request):
    return render_to_response("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        })
