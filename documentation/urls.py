from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, url


urlpatterns = patterns('documentation.views',
    url(r'show$', 
            'documentation',
            name='show_documentation'),
    url(r'show/(?P<par_type>\w+)$', 
            'param_documentation',
            name='param_documentation'),
)
