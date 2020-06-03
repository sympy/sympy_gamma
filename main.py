from __future__ import absolute_import
import os, sys

# Force sys.path to have our own directory first, in case we want to import
# from it.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Must set this env var *before* importing any part of Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.wsgi import get_wsgi_application

# https://cloud.google.com/appengine/docs/standard/python/issue-requests#requests
# import requests_toolbelt.adapters.appengine
# Use the App Engine Requests adapter. This makes sure that Requests uses URLFetch.
# requests_toolbelt.adapters.appengine.monkeypatch()

application = get_wsgi_application()
