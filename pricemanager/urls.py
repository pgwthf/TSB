from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, url

urlpatterns = patterns('pricemanager.views',

    url(r'^show/all$', 
            'show_pools', 
            name='show_pools'),

    url(r'^show/stock/(?P<stock_id>\d+)$', 
            'show_stock', 
            name='show_stock'),

    url(r'^show/stock/(?P<symbol>[.\^\-\w]+)$', 
            'show_stock', 
            name='show_symbol'),

    url(r'^show/new$', 
            'show_pool', 
            {'pool_id': 'new'}, 
            name='new_pool'),

    url(r'^show/(?P<pool_id>\d+)$', 
            'show_pool', 
            name='show_pool'),

    url(r'^show/s(?P<system_id>\d+)$', 
            'show_system_pool', 
            name='show_system_pool'),
)
