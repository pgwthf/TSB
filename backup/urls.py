from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, url


urlpatterns = patterns('backup.views',
    url(r'^$', 
            'backup',
            name='backup'),

    url(r'^create$', 
            'backup',
            {'action': 'make_backup'},
            name='make_backup'),

    url(r'^restore/(?P<file_id>\w+)$', 
            'backup', 
            {'action': 'restore'},
            name='restore?'),

    url(r'^restore_confirmed/(?P<file_id>\w+)$', 
            'backup', 
            {'action': 'restore_confirmed'}, 
            name='restore!'),
)
