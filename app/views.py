import logging
import cgi
import uuid

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django import forms

from google.appengine.api import users

from models import Account, Worksheet, Cell
from utils import log_exception
from logic import Eval, SymPyGamma
from jsonrpc import jsonrpc_method

import settings

def login_required(func):
  """Decorator that redirects to the login page if you're not logged in."""

  def login_wrapper(request, *args, **kwds):
    if request.user is None:
      return HttpResponseRedirect(
          users.create_login_url(request.get_full_path().encode('utf-8')))
    return func(request, *args, **kwds)

  login_wrapper.__name__ = func.__name__
  return login_wrapper

def jsonremote(func):

  @jsonrpc_method(func.__name__)
  @log_exception
  def remote(*args, **kwds):
    return func(*args, **kwds)

  remote.__name__ = func.__name__
  return remote


class SearchForm(forms.Form):
    i = forms.CharField(required=False)

class SettingsForm(forms.Form):
    show_prompts = forms.BooleanField(required=False)
    join_nonempty_fields = forms.BooleanField(required=False)

def get_user_info(request, logout_go_main=False, settings_active=""):
    user = users.get_current_user()
    if user:
        if logout_go_main:
            logout_url = users.create_logout_url("/")
        else:
            logout_url = users.create_logout_url(request.get_full_path()
                    .encode('utf-8'))
        return '<span class="email">%s</span>|<a class="%s" "href="/settings/">Settings</a>|<a href="%s">Sign out</a>' % \
                (user.email(), settings_active, logout_url)
    else:
        return '<a href="%s">Sign in</a>' % \
                users.create_login_url(request.get_full_path().encode('utf-8'))

def index(request):
    form = SearchForm()
    return render_to_response("index.html", {
        "form": form,
        "MEDIA_URL": settings.MEDIA_URL,
        "main_active": "selected",
        "user_info": get_user_info(request),
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
                "user_info": get_user_info(request),
                })

def notebook(request):
    account = Account.current_user_account
    if account:
        show_prompts = account.show_prompts
        join_nonempty_fields = account.join_nonempty_fields
    else:
        show_prompts = False
        join_nonempty_fields = True
    return render_to_response("nb.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "nb_active": "selected",
        "user_info": get_user_info(request),
        "show_prompts": show_prompts,
        "join_nonempty_fields": join_nonempty_fields,
        })

def about(request):
    return render_to_response("about.html", {
        "MEDIA_URL": settings.MEDIA_URL,
        "about_active": "selected",
        "user_info": get_user_info(request),
        })

@login_required
def settings_view(request):
    account = Account.current_user_account
    if request.method != "POST":
        form = SettingsForm(initial={
            'show_prompts': account.show_prompts,
            'join_nonempty_fields': account.join_nonempty_fields,
            })
        return render_to_response("settings.html", {
            "form": form,
            "MEDIA_URL": settings.MEDIA_URL,
            "user_info": get_user_info(request, logout_go_main=True,
                settings_active="selected"),
            "account": Account.current_user_account,
            })
    form = SettingsForm(request.POST)
    if form.is_valid():
        account.show_prompts = form.cleaned_data.get('show_prompts')
        account.join_nonempty_fields = \
            form.cleaned_data.get('join_nonempty_fields')
        account.put()
    else:
        HttpResponseRedirect(reverse(settings_view))
    return HttpResponseRedirect(reverse(index))


# ---------------------------------
# A few demo services for testing:

@jsonremote
def echo(request, msg):
    return msg

@jsonremote
def add(request, a, b):
    return a+b

@jsonremote
def reverse(request, msg):
    return msg[::-1]

@jsonremote
def uppercase(request, msg):
    return msg.upper()

@jsonremote
def lowercase(request, msg):
    return msg.lower()

# ---------------------------------

e = Eval()

@jsonremote
def eval_cell(request, code):
    r = e.eval(code)
    return r

@jsonremote
def create_worksheet(request):
    token = str(uuid.uuid4())
    w = Worksheet(session_token=token)
    w.save()
    return token

@jsonremote
def add_cell(request, token, insert_before_id=None):
    w = Worksheet.all().filter("session_token =", token)[0]
    c = Cell(worksheet=w, id=w.max_id()+1)
    c.save()

@jsonremote
def print_worksheet(request, token):
    w = Worksheet.all().filter("session_token =", token)[0]
    return w.print_worksheet()

@jsonremote
def get_cell_ids(request, token):
    w = Worksheet.all().filter("session_token =", token)[0]
    return w.get_cell_ids()
