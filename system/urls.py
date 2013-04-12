from __future__ import division
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = patterns('system.views',

# show a table with all bookmark sections
    url(r'^show/bookmarks$', 
            'show_bookmark_sections', 
            name='show_bookmark_sections'),

# show a table with all systems in a bookmark section
    url(r'^show/bookmarks/(?P<bookmark_id>\d+)$', 
            'show_bookmarks', 
            name='show_bookmarked_systems'),

## show a table with all systems for metasystem <metasystem_id>:
#    url(r'^show/metasystem/(?P<metasystem_id>\d+)$', 
#            'show_systems', 
#            name='show_metasystem_systems'),
#
##TODO: implement:
## show a table with all systems for metasystem group <group_id>:
#    url(r'^show/group/(?P<group_id>\d+)$', 
#            'show_systems', 
#            name='show_group_systems'),

# show a single system:
    url(r'^show/(?P<system_id>\d+)$', 
            'show_system', 
            name='show_system'),

# edit trades for a discretionary system:
    url(r'^edit/(?P<system_id>\d+)$', 
            'edit_system', 
            name='edit_system'),

    url(r'^export/all/(?P<metasystem_id>\d+).csv$',
            'export_systems_to_csv', 
            name='export_systems'),

## delete all systems for <metasystem_id>:
#    url(r'^delete/all/(?P<metasystem_id>\d+)$',
#            'show_systems', 
#            {'action': 'delete'}, 
#            name='delete_systems'),

)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 
            'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT,}),
   )
urlpatterns += staticfiles_urlpatterns()
