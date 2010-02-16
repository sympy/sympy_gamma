from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import os.path
p = os.path.join(os.path.dirname(__file__), 'media/')

urlpatterns = patterns('',
    # Example:
    # (r'^notebook/', include('notebook.foo.urls')),
    (r'^$', 'app.views.index'),
    (r'^eval_cell/$', 'app.views.eval_cell'),

    (r'^input/', 'app.views.input'),
    (r'^nb/$', 'app.views.notebook'),
    (r'^nb/(nb.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(p, "js")}),
    (r'^about/$', 'app.views.about'),
    (r'^settings/$', 'app.views.settings_view'),

    (r'^media_files/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': p}),


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)
