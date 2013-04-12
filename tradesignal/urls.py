from __future__ import division
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = patterns('tradesignal.views',

    url(r'^export/trades/(?P<system_id>\w+).csv$', 
            'export_trades_to_csv', 
            name='export_trades'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 
            'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT,}),
   )
urlpatterns += staticfiles_urlpatterns()