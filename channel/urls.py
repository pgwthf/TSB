from __future__ import division
from __future__ import absolute_import

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns



urlpatterns = patterns('channel.views',

)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^static/(?P<path>.*)$', 
            'django.views.static.serve',
            {'document_root': settings.STATIC_ROOT,}),
   )
urlpatterns += staticfiles_urlpatterns()