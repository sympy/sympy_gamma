from __future__ import absolute_import
from django.conf.urls import url

from app import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import os.path
p = os.path.join(os.path.dirname(__file__), 'media/')

urlpatterns = [
    # Example:
    # (r'^notebook/', include('notebook.foo.urls')),
    url(r'^$', views.index),

    url(r'^input/', views.input),
    url(r'^about/$', views.about),
    url(r'^random', views.random_example),

    url(r'card/(?P<card_name>\w*)$', views.eval_card),

    url(r'card_info/(?P<card_name>\w*)$', views.get_card_info),

    url(r'card_full/(?P<card_name>\w*)$', views.get_card_full)


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
]

handler404 = views.view_404
handler500 = views.view_500
