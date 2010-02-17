import logging
import cgi

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django import forms

from google.appengine.api import users

from models import Account
from utils import log_exception
from logic import Eval, SymPyGamma

import settings

def login_required(func):
  """Decorator that redirects to the login page if you're not logged in."""

  def login_wrapper(request, *args, **kwds):
    if request.user is None:
      return HttpResponseRedirect(
          users.create_login_url(request.get_full_path().encode('utf-8')))
    return func(request, *args, **kwds)

  return login_wrapper


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
                "user_info": get_user_info(result),
                })

def notebook(request):
    account = Account.current_user_account
    if account:
        show_prompts = account.show_prompts
        join_nonempty_fields = account.join_nonempty_fields
    else:
        show_prompts = True
        join_nonempty_fields = False
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


e = Eval()

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
