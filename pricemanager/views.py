'''
pricemanager/views.py v0.1 120820

Created on 120820

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from django_tables2 import RequestConfig

from utils_python.utils import date2datestr

from pricemanager.models import Pool, StockPoolDates, Stock
from pricemanager.forms import PoolForm, StockChartForm, DateRangeForm, \
        MemberForm
from pricemanager.tables import PoolsTable, MembersTable
from pricemanager.commands import dl_latest_prices

from TSB.utils import Notify
from channel.models import Channel
from system.models import System



@login_required
def show_pools(request):
    '''
    Show overview of all pools in the Pools database.
    '''
    notify = None

    if request.method == 'POST' and request.POST.get('action'):
        pool_list = request.POST.getlist('id')

        if request.POST.get('action') == 'Copy':
            if not len(pool_list):
                notify = Notify('Copy failed, select a pool to copy')
            elif len(pool_list) > 1:
                notify = Notify('Copy failed, select only one pool to copy')
            else:
                for pool_id in pool_list: # NOTE: only pool_list[0] is used!
                    pool = Pool.objects.get(id=pool_id)
                    name = pool.name
                    new_pool = pool.copy()
                notify = Notify('Pool "{}" copied to "{}"'.format(name, 
                        new_pool.name))

        elif request.POST.get('action') == 'Delete':
            if not len(pool_list):
                notify = Notify('Delete failed, select pool(s) to delete')
            else:
                notify = Notify('Delete pool(s) {}?'.format(', '.join(
                        pool_list)))
                notify.set_replies(request, ('Yes', 'No'))
                request.session['pool_delete_list'] = pool_list

    elif request.method == 'POST' and request.POST.get('reply'):
        pool_list = request.session.get('pool_delete_list')
        if not pool_list:
            raise AttributeError('session has no valid pool_delete_list')
        del request.session['pool_delete_list']
        if request.POST.get('reply') == 'Yes':
            Pool.objects.filter(pk__in=pool_list).delete()
            notify = Notify('Pool(s) {} deleted'.format(','.join(pool_list)))
        elif request.POST.get('reply') == 'No':
            notify = Notify('Delete cancelled')

    elif request.method == 'POST' and request.POST.get('upload'):
        upload_file = request.FILES['poolfile']
        pool_name, unused = '{}'.format(upload_file).split('.', 1)
        startdate = datetime.date(2012,1,1)
        currency = Stock.US_DOLLAR
        index_name = '^GSPC'
        index = Stock.objects.get(name=index_name)
        pool, unused = Pool.objects.get_or_create(name=pool_name, 
                index=index, startdate=startdate)
        pool.import_csv(upload_file, index_name, currency)

    pools = Pool.objects.all()
    pools_table = PoolsTable(pools, order_by=('-id',))
    RequestConfig(request, paginate={'per_page': 100}).configure(pools_table)
    return render(request, 'show_pools.html', {
            'pools_table': pools_table,
            'notify': notify,
            })


#from pricemanager.commands import dl_prices

@login_required
def show_pool(request, pool_id=None):
    '''
    Show contents of pool <pool_id>.
    '''
    notify = None
    splits = None
    missing_prices = None
    missing_channels = None
    pool = None if pool_id == 'new' else Pool.objects.get(id=pool_id)

    if request.method == 'POST' and request.POST.get('action'):
        daterangeform = DateRangeForm(request.POST)
        if not daterangeform.is_valid():
            notify = Notify('Invalid date(s)')
        else:
            startdate = daterangeform.cleaned_data['fromdate']
            enddate = daterangeform.cleaned_data['todate']

#FIXME: running separate (huey) processes does not work
            if request.POST.get('action') == 'Download latest prices':
#                dl_latest_prices(pool)
                pool.download_latest_prices()
            elif request.POST.get('action') == 'Download index':
                pool.index.download_history(startdate, enddate)
            elif request.POST.get('action') == 'Calculate index channels':
                Channel.calculate(pool.index, startdate, enddate)
            elif request.POST.get('action') == 'Download all stock prices':
#                dl_prices(pool, startdate, enddate)
                pool.download_prices(startdate, enddate)
            elif request.POST.get('action') == 'Check for missing prices':
                missing_prices = pool.missing_prices(startdate, enddate)
            elif request.POST.get('action') == 'Check for stock splits':
                splits = pool.check_splits()
            elif request.POST.get('action') == 'Check for missing channels':
                missing_channels = pool.missing_channels(startdate, enddate)
            elif request.POST.get('action') == 'Calculate all stock channels':
                pool.calculate_channels(startdate, enddate)
    elif pool:
        enddate = datetime.date.today() if not pool.enddate else pool.enddate
        daterangeform = DateRangeForm(initial={
                'fromdate':pool.startdate, 'todate': enddate})
    else:
        daterangeform = None

    if request.method == 'POST' and request.POST.get('save'):
        poolform = PoolForm(request.POST, instance=pool)
        memberform = MemberForm(request.POST, prefix='stock')
        if poolform.is_valid():
            pool = poolform.save()
            if memberform.is_valid():
                obj = memberform.save(commit=False)
                obj.pool = pool
                obj.save()
    else: # first entry - no POST data
        poolform = PoolForm(instance=pool)
        memberform = MemberForm(prefix='stock')

    if request.method == 'POST' and request.POST.get('action'):
        stock_list = request.POST.getlist('id')

        if request.POST.get('action') == 'Delete':
            if not len(stock_list):
                notify = Notify('Delete failed, select stock(s) to delete')
            else:
                notify = Notify('Delete stocks(s) {}?'.format(', '.join(
                        StockPoolDates.objects.get(id=s).stock.name for s in 
                        stock_list)))
                notify.set_replies(request, ('Yes', 'No'))
                request.session['stock_delete_list'] = stock_list

    elif request.method == 'POST' and request.POST.get('reply'):
        stock_list = request.session.get('stock_delete_list')
        if not stock_list:
            raise AttributeError('session has no valid stock_delete_list')
        del request.session['stock_delete_list']
        if request.POST.get('reply') == 'Yes':
            stocks = [StockPoolDates.objects.get(id=s).stock.name for s in 
                    stock_list]
            StockPoolDates.objects.filter(id__in=stock_list).delete()
            notify = Notify('Stock(s) {} deleted'.format(', '.join(stocks)))
        elif request.POST.get('reply') == 'No':
            notify = Notify('Delete cancelled')


    members = StockPoolDates.objects.filter(pool=pool).order_by('stock__name',)
    stocks_table = MembersTable(members, exclude=['pool',])

    RequestConfig(request, paginate={'per_page': 100}).configure(stocks_table)
    return render(request, 'show_pool.html', {
            'pool': pool,
            'poolform': poolform,
            'memberform': memberform,
            'stocks_table': stocks_table,
            'daterangeform': daterangeform,
            'notify': notify,
            'splits': splits,
            'missing_prices': missing_prices,
            'missing_channels': missing_channels,
            })



@login_required
def show_system_pool(request, system_id=None):
    '''
    Show contents of pool <pool_id>.
    Tries to make a channel pool, but falls back to normal pool if no channel
    def is available in metasystem
    '''
    system = System.objects.get(id=system_id)
    metasystem = system.metasystem
    metasystem.make_system(system.params)
    pool = metasystem.pool

    date = pool.index.get_latest_date()
    stock_tables = []
    for method in metasystem.methods:
        rsl = method.rank.get_table(date=date, 
                stock_list=pool.get_cached_stocklist(date))
        stock_table = method.rank.make_table(data=rsl)
        stock_tables.append(stock_table)
        RequestConfig(request, paginate={'per_page': 100}).configure(
                stock_table)
    return render(request, 'show_system_pool.html', {
            'pool': pool,
            'system': system,
            'stock_tables': stock_tables,
            })



def show_stock(request, stock_id=None, symbol=None):
    '''
    Show stock chart and metrics. 
    '''
#CONSIDER: add indicators that can dynamically be selected/changed
    if stock_id:
        stock = Stock.objects.get(id=stock_id)
    elif symbol:
        stock = Stock.objects.get(name=symbol.upper())
    else:
        raise SystemExit('Fatal Error: no stock_id or symbol specified.')

    missing_prices = stock.missing_prices()
    if not missing_prices:
        missing_channels = stock.missing_channels()
        splits = stock.check_splits()
    else:
        missing_channels = []
        splits = []

    #set default date range and lookback period:
    lookback = request.session.get('channel_lookback_period', Channel.YEAR)
    enddate = datetime.date.today()
    startdate = enddate - datetime.timedelta(days=365)

    if request.method == 'POST':
        reload_ = False

        if request.POST.get('todo') == 'Download missing prices':
            fromdate = min(missing_prices)
            todate = max(missing_prices)
            stock.download_history(fromdate, todate)
            reload_ = True

        if request.POST.get('todo') == 'Calculate missing channels':
            fromdate = min(missing_channels)
            todate = max(missing_channels)
            Channel.calculate(stock, fromdate, todate)
            reload_ = True

        if request.POST.get('todo') == 'Correct prices for split':
            stock.correct_splits()
            reload_ = True

        if reload_:
            if symbol:
                return redirect('show_symbol', symbol=symbol)
            else:
                return redirect('show_stock', stock_id=stock_id)

        if request.POST.get('todo') == 'Save settings':
            stockchartform = StockChartForm(request.POST)
            if stockchartform.is_valid():
                sd = stockchartform.cleaned_data['startdate']
                ed = stockchartform.cleaned_data['enddate']
                if sd:
                    startdate = sd
                if ed:
                    enddate = ed
                lookback = int(stockchartform.cleaned_data['lookback_period'])
                request.session['channel_lookback_period'] = lookback
        else:
            stockchartform = StockChartForm(initial={'startdate': startdate,
                    'enddate': enddate, 'lookback_period': lookback})
    else:
        stockchartform = StockChartForm(initial={'startdate': startdate,
                'enddate': enddate, 'lookback_period': lookback})

    stockchart = reverse('show_stock_chart_from_to', kwargs={
            'symbol': stock.name,
            'startdate_str': date2datestr(startdate),
            'enddate_str': date2datestr(enddate),})

    return render(request, 'show_stock.html',
                {'stock': stock,
                 'data': stock.data_summary(enddate, lookback),
                 'missing_prices': missing_prices,
                 'missing_channels': missing_channels,
                 'splits': splits,
                 'stockchart': stockchart,
                 'stockchartform': stockchartform})
