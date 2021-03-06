from __future__ import division
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = patterns('metasystem.views',

    url(r'^show/all$', 
            'show_metasystems', 
            name='show_metasystems'),

    url(r'^show/group/(?P<group_id>\d+)$', 
            'show_metasystems', 
            name='show_metasystems'),


    url(r'^show/(?P<metasystem_id>\d+)$', 
            'show_metasystem', 
            name='show_metasystem'),


    url(r'^edit/new$', 
            'edit_metasystem', 
            {'metasystem_id': 'new'}, 
            name='new_metasystem'),

    url(r'^edit/(?P<metasystem_id>\d+)$', 
            'edit_metasystem', 
            name='edit_metasystem'),

    url(r'^edit/(?P<metasystem_id>\d+)/force$', 
            'edit_metasystem', 
            {'force_edit': True}, 
            name='force_edit_metasystem'),

)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 
            'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT,}),
   )
urlpatterns += staticfiles_urlpatterns()