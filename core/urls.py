from django.conf.urls.defaults import *
from django.conf import settings
from core import views

urlpatterns = patterns(
    '',
    url(r'^$', 'django.views.generic.simple.direct_to_template', {'template':'index.html'}),
    url(r'entries/(?P<entry_id>\d*)$', views.ApiView.as_view())
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^500/$', 'django.views.generic.simple.direct_to_template', {'template': '500.html'}),
        url(r'^404/$', 'django.views.generic.simple.direct_to_template', {'template': '404.html'}),
        )
