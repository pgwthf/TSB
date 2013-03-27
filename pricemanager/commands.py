'''
pricemanager/commands.py v0.1 120819

Created on 120819

@author: edwin

This file contains scheduled tasks that are run by huey.
'''

from __future__ import division
from __future__ import absolute_import

from huey.djhuey.decorators import periodic_command, crontab

from pricemanager.models import Price, Stock

import TSB.settings
TSB.settings.DEBUG = False
DEBUG = False


#@periodic_command(crontab(hour='0', minute='6', day_of_week='*')) # in GMT!!
@periodic_command(crontab(hour='22', minute='0', day_of_week='1-5')) # in GMT!!
def update_USD():
    '''
    Update USD stock prices daily.
    '''
    print 'D/L Started'
    Price.download_prices_today(currency=Stock.US_DOLLAR)
    print 'D/L finished'


#@periodic_command(crontab(hour='0', minute='4', day_of_week='*')) # in GMT!!
@periodic_command(crontab(hour='6', minute='0', day_of_week='1-5')) # in GMT!!
def update_AUD():
    '''
    Update AUD stock prices daily.
    '''
    Price.download_prices_today(currency=Stock.AUSTRALIAN_DOLLAR)
