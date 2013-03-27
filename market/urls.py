from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, url


urlpatterns = patterns('market.views',

# market conditions page
    url(r'^market/type$', 
            'show_market_type',
            name='show_market_type'),

)
