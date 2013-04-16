'''
pricemanager/management/commands/download_today.py

Copyright (C) 2013 Edwin van Opstal

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see `<http://www.gnu.org/licenses/>`.
'''

from __future__ import division
from __future__ import absolute_import

from datetime import datetime
from pytz import timezone
from django.core.management.base import BaseCommand, make_option
from django.conf import settings

from pricemanager.models import Price
from pyutillib.date_utils import is_weekday


class Command(BaseCommand):
    '''
    Without arguments, this command checks if an automated download needs to
    take place (from settings.TSB.downloads #TODO: from market table)
    A manual download can be forced by specifying the market - in that case
    time is ignored.
    '''

    help = "Download price data"
    option_list = BaseCommand.option_list + (
            make_option('--exchange', '-e',
                dest='exchange',
                type = 'str',
                help='Download prices for this exchange'
            ),)

    def handle(self, **options):
#TODO replace settings dict with market table
        exchange = []
        if options.get('exchange'):
            # force download of the specified exchange
            for x in settings.TSB['downloads']:
                if x['exchange'] == options.get('exchange'):
                    exchange.append(x)
                    break
            if not exchange:
                raise SystemExit('Nothing to do: exchange {} not found'.format(
                        options.get('exchange')))
        else:
            # for each exchange, check if it needs to be downloaded
            for x in settings.TSB['downloads']:
                exchange_time = datetime.now(timezone(x.get('timezone')))
                if not is_weekday(exchange_time):
                    continue
                if exchange_time.hour == x.get('time_h'):
                    exchange.append(x)
        for x in exchange:
            #FIXME: retries will cause delay *before* running next exchange!
                # implementing delays in hours could be easy-ish (but how to 
                # remember which symbols need retrying?? - NoRedis??)
            #TODO: implement datasource (now yahoo is always used)
            #TODO: use -verbosity to see output when using cmd line
            #TODO: with -verbosity=0 send *certain* messages to admin
            Price.download_prices_today(currency=x.get('currency'),
                    num_retries=x.get('num_retries'))
