from django.conf.urls import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import os.path
p = os.path.join(os.path.dirname(__file__), 'media/')

urlpatterns = patterns(
    '',

    url(r'^$', 'app.views.index'),

    url(r'^input/', 'app.views.input'),
    url(r'^about/$', 'app.views.about'),
    url(r'^random', 'app.views.random_example'),

    url(r'user/remove/(?P<qid>.*)$', 'app.views.remove_query'),

    url(r'card/(?P<card_name>\w*)$', 'app.views.eval_card'),

    url(r'card_info/(?P<card_name>\w*)$', 'app.views.get_card_info'),

    url(r'card_full/(?P<card_name>\w*)$', 'app.views.get_card_full')
)

handler404 = 'app.views.view_404'
handler500 = 'app.views.view_500'
