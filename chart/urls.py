from __future__ import division
from __future__ import absolute_import

from django.conf.urls import patterns, url


urlpatterns = patterns('chart.views',

# equity thumbnail
    url(r'^small/(?P<system_id>\d+).png$', 
            'draw_thumbnail',
            name='show_thumbnail'),

# equity chart
    url(r'^big/(?P<system_id>\d+).png$', 
            'draw_equity_chart',
            name='show_equity_chart'),


# stock chart
    url(r'^stock/(?P<symbol>\w+).png$', 
            'draw_stock_chart',
            name='show_stock_chart'),

# stock chart from a specified date to a specified date with a preset lookback
    url(r'^stock/(?P<startdate_str>\d+)/(?P<enddate_str>\d+)/'\
                '(?P<symbol>[.^\-\w]+)_(?P<lookback>\d+).png$', 
            'draw_stock_chart',
            name='show_stock_chart_from_to_lookback'),

# stock chart from a specified date to a specified date
    url(r'^stock/(?P<startdate_str>\d+)/(?P<enddate_str>\d+)/'\
                '(?P<symbol>[.^\-\w]+).png$', 
            'draw_stock_chart',
            name='show_stock_chart_from_to'),



# custom stock chart 
    url(r'^stock/custom/(?P<startdate_str>\d+)/(?P<enddate_str>\d+)/'\
                '(?P<symbol>[.^\-\w]+).png$', 
            'custom_stock_chart',
            name='show_custom_stock_chart'),



# market conditions chart from a specified date to a specified date
#    url(r'^market/(?P<startdate_str>\d+)/(?P<enddate_str>\d+)/'\
#                '(?P<symbol>\w+).png$',
#            'draw_market_chart',
#            name='show_market_chart'),
    url(r'^market/(?P<system_id>\d+).png$',
            'draw_market_chart',
            name='show_market_chart'),

#    url(r'^market/(?P<startdate_str>\d+)/(?P<enddate_str>\d+)/'\
#                '(?P<system_id>\d+).png$',
#            'draw_market_chart',
#            name='show_market_chart'),




# stock chart of trade (or open position)
    url(r'^trade/(?P<trade_id>\d+).png$', 
            'draw_trade_chart',
            name='draw_trade_chart'),

# trade page
    url(r'^trade/show/(?P<trade_id>\d+)$', 
            'show_trade',
            name='show_trade'),

)
