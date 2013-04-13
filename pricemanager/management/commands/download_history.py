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

from django.core.management.base import BaseCommand, make_option
from django.core.exceptions import ObjectDoesNotExist

from pricemanager.models import Pool
from utils_python.utils import datestr2date


class Command(BaseCommand):
    help = "Download historical stock prices for a specified pool"
    option_list = BaseCommand.option_list + (
            make_option('--startdate', '-s',
                dest='startdate',
                type = 'str',
                help='Download prices from this date'
            ),
            make_option('--enddate', '-e',
                dest='enddate',
                type = 'str',
                help='Download prices to this date'
            ),
            make_option('--pool', '-p',
                dest='pool',
                type='str',
                help='Name of the pool'
            ),
            make_option('--pool_id', '-i',
                dest='pool_id',
                type='int',
                help='id of the pool'
            ),)

    def handle(self, **options):
#TODO: verbose option on (any) function that can be called
        if options.get('pool'):
            if options.get('pool_id'):
                print 'Error: pool and pool_id were found, only 1 must be '\
                        'specified'
                raise SystemExit
            try:
                pool = Pool.objects.get(name=options.get('pool'))
            except ObjectDoesNotExist:
                print 'Error: pool {} was not found'.format(options.get('pool'))
                raise SystemExit
        elif options.get('pool_id'):
            try:
                pool = Pool.objects.get(id=options.get('pool_id'))
            except ObjectDoesNotExist:
                print 'Error: pool_id {} was not found'.format(options.get(
                        'pool_id'))
                raise SystemExit
        else:
            raise SystemExit('Error: A pool or pool_id must be specified')
        kwargs = {}
        if options.get('startdate'):
            try:
                kwargs['fromdate'] = datestr2date(options.get('startdate'))
            except ValueError, e:
                raise SystemExit('Error: {}'.format(e))
        if options.get('enddate'):
            try:
                kwargs['todate'] = datestr2date(options.get('enddate'))
            except ValueError, e:
                raise SystemExit('Error: {}'.format(e))
        if options.get('verbosity') and options['verbosity'] > 0:
            output = ''
            if kwargs.get('fromdate'):
                output += ' from {}'.format(kwargs.get('fromdate'))
            if kwargs.get('todate'):
                output += ' to {}'.format(kwargs.get('todate'))
            print 'Download prices for pool {}:{}{}'.format(pool.id, pool.name,
                    output)
        pool.download_prices(**kwargs)
