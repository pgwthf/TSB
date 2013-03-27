'''
channel/view.py v0.1 130118

Created on 130118

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import datetime

from django.shortcuts import render


#from TSB.utils import init_redis
from utils_python.utils import str2dict

from market.forms import DateForm, ChartSettingsForm
#from chart.models import get_market_condition

from pricemanager.models import Stock


def get_settings(data):
    '''
    Extracts the settings from the validated form data.
    '''
    settings = {}
    for key in ('n_ma', 'n_atr', 'vol_zones', 'trend_zones'):
        settings[key] = data[key]
    settings['symbol'] = data['symbol'].name
    settings['vol_th'] = (float(data['vol_th1'])/100, 
                                                float(data['vol_th2'])/100)
    settings['trend_th'] = (float(data['trend_th1'])/100, 
                                                float(data['trend_th2'])/100)
    return settings


def get_initial(settings):
    '''
    Translates the (redis) settings to initial values for the form.
    '''
    initial = {}
    for key in ('n_ma', 'n_atr', 'vol_zones', 'trend_zones'):
        initial[key] = settings[key]
    initial['symbol'] = Stock.objects.get(name=settings['symbol']) 
    initial['vol_th1'] = settings['vol_th'][0] * 100
    initial['vol_th2'] = settings['vol_th'][1] * 100
    initial['trend_th1'] = settings['trend_th'][0] * 100
    initial['trend_th2'] = settings['trend_th'][1] * 100
    return initial


def show_market_type(request):
    '''
    Market conditions page
    '''
#    rs = init_redis()
    rs = None
    message = ''
    startdate = datetime.date(2010,1,1)
    enddate = datetime.date.today()
    data = None
    if request.method == 'POST':
        dateform = DateForm(request.POST, prefix='chart1')
        if dateform.is_valid():
            startdate = dateform.cleaned_data['startdate']
            enddate = dateform.cleaned_data['enddate']
        settingsform = ChartSettingsForm(request.POST)
        if settingsform.is_valid():
            data = settingsform.cleaned_data
            settings = get_settings(data)
            rs.set('market_conditions_settings', settings)
    else:
        # get initial data from redis
        settings = str2dict(rs.get('market_conditions_settings'))
        if settings:
            data = get_initial(settings)
            settingsform = ChartSettingsForm(initial=data)
        else:
            settingsform = ChartSettingsForm()
    dateform = DateForm(initial={'startdate': startdate, 'enddate': enddate}, 
            prefix='chart1')
    if data:
        stock = data['symbol']
        today = datetime.date.today()
#        stock.set_prices(last_year(today), today)
        current = '{} {}'.format(*get_market_condition(stock.price, today, 
                                                                    settings))
        if stock.name[0] == '^':
            symbol = '0' + stock.name[1:]
        else:
            symbol = stock.name
    else:
        symbol = None
        current = None
    return render(request, 'show_market.html',
                {'symbol': symbol,
                 'dateform': dateform,
                 'settingsform': settingsform,
                 'current_condition': current,
                 'message': message})
