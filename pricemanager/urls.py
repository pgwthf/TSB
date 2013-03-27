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

#    url(r'^export/all$', 'show_pools', {'action': 'export'}, 
#                                                        name='export_pools'),
#    url(r'^download/all$', 'show_pools', {'action': 'download'}, 
#                                                        name='download_pools'),
#    url(r'^check/all$', 'show_pools', {'action': 'check'}, 
#                                                        name='check_pools'),
    url(r'^edit/new$', 'edit_pool', {'pool_id': 'new'}, name='new_pool'),


    url(r'^show/(?P<pool_id>\d+)$', 
            'show_pool', 
            name='show_pool'),

#    url(r'^show/p(?P<pool_id>\d+)/ms(?P<metasystem_id>\d+)$', 
#            'show_pool', 
#            name='show_channel_pool'),

    url(r'^show/s(?P<system_id>\d+)$', 
            'show_system_pool', 
            name='show_system_pool'),

#    url(r'^show/short/(?P<pool_id>\d+)$', 
#            'show_pool', 
#            {'short': True},
#            name='show_short_pool'),

    url(r'^edit/(?P<pool_id>\d+)$', 'edit_pool', name='edit_pool'),
#    url(r'^copy/(?P<pool_id>\d+)$', 'show_pools', {'action': 'copy'}, 
#                                                        name='copy_pool'),
#    url(r'^check/(?P<pool_id>\d+)$', 'show_pools', {'action': 'check'}, 
#                                                        name='check_pool'),
#    url(r'^download/(?P<pool_id>\d+)$', 'show_pools', {'action': 'download'}, 
#                                                        name='download_pool'),
#
#    url(r'^delete/(?P<pool_id>\d+)$', 'show_pools', {'action': 'delete'}, 
#                                                        name='delete_pool'),
)
