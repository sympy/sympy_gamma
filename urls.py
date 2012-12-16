from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import os.path
p = os.path.join(os.path.dirname(__file__), 'media/')

urlpatterns = patterns(
    '',
    # Example:
    # (r'^notebook/', include('notebook.foo.urls')),
    (r'^$', 'app.views.index'),

    (r'^input/', 'app.views.input'),
    (r'^about/$', 'app.views.about'),

    (r'user/remove/(?P<qid>.*)$', 'app.views.remove_query'),

    (r'card/(?P<card_name>\w*)$', 'app.views.eval_card')


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)
