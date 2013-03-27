from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.views import login, logout

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/login/$',  login),
    (r'^accounts/logout/$', logout),
)

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pool/', include('pricemanager.urls')),
    url(r'^system/', include('system.urls')),
    url(r'^metasystem/', include('metasystem.urls')),
    url(r'^chart/', include('chart.urls')),
    url(r'^tradesignal/', include('tradesignal.urls')),
    url(r'^documentation/', include('documentation.urls')),
    url(r'^backup/', include('backup.urls')),
    url(r'^market/', include('market.urls')),
#    url(r'helpdesk/', include('helpdesk.urls')),
)
