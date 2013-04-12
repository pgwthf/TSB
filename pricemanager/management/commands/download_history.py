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
            ))

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
