from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, url

urlpatterns = patterns('tradesignal.views',

    url(r'^export/trades/(?P<system_id>\w+).csv$', 
            'export_trades_to_csv', 
            name='export_trades'),
)
