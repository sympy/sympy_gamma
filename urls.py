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
    (r'^result/$', 'app.notebook.result_json'),
    (r'^input/', 'app.views.input'),
    (r'^about/$', 'app.views.about'),
    (r'^random', 'app.views.random_example'),
    (r'user/remove/(?P<qid>.*)$', 'app.views.remove_query'),

    (r'card/(?P<card_name>\w*)$', 'app.views.eval_card'),

    (r'card_info/(?P<card_name>\w*)$', 'app.views.get_card_info'),

    (r'card_full/(?P<card_name>\w*)$', 'app.views.get_card_full')


    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),
)

handler404 = 'app.views.view_404'
handler500 = 'app.views.view_500'
