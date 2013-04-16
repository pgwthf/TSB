'''
system/views.py v0.1 121003

Created on 121003

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

import csv

from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
#from django.forms.formsets import formset_factory
#from django.db import transaction
#from django.db import connection

from django_tables2 import RequestConfig

from pyutillib.date_utils import next_weekday
from pyutillib.string_utils import str2dict_keys, str2dict


from TSB.utils import Notify
from tradesignal.models import Trade
from equity.models import EquityHistory
#from metasystem.models import MetaSystem
from system.models import System, OUTPUT_FORMATS, Bookmark
from system.tables import MakeSystemsTable, TradesTable, EquityTable, \
        PortfolioTable
from system.forms import CopyForm, BookmarkForm, COMP_REVERSE #, FilterFormSet
from pricemanager.models import Stock



@login_required
def show_bookmark_sections(request):
    bookmarks = Bookmark.objects.all()
    return render(request, 'show_bookmark_sections.html',
                {'bookmarks': bookmarks})



@login_required
def show_bookmarks(request, bookmark_id):

    if request.method == 'POST':
        system_list = request.POST.getlist('id')
        if request.POST.get('todo') == 'Drop bookmark':
            for sys in System.objects.filter(id__in=system_list):
                sys.bookmark = None
                sys.save()


    view_settings = {
            'parameters': False,
            'performance': True,
            'result': True}

    bookmark = Bookmark.objects.get(id=bookmark_id)
    systems = System.objects.filter(bookmark=bookmark)
    systems_table = MakeSystemsTable(data=systems, order_by=('-id',),
            show=view_settings, excludes=['params', 'bookmark'])

    # generate column_titles
    if systems.count():
        systems_table.base_columns['params'].verbose_name = mark_safe(
                        '</th><th>'.join(str2dict_keys(systems[0].params)))
        for key, params in OUTPUT_FORMATS.items():
            if 'title' in params:
                systems_table.base_columns[key].verbose_name = params['title']
    RequestConfig(request, paginate={'per_page': 100}).configure(systems_table)

    return render(request, 'show_bookmarks.html',
                {'systems_table': systems_table, 
                 'bookmark': bookmark})



def apply_filters(filter_data, kwargs_in={}, reverse=False):
    '''
    Returns kwargs, suitable for filtering a queryset. <filter_data> contains 
    filter settings from filterform. <kwargs_in> can be used to pass default
    values.
    Set <reverse> to True for deleting, so that the filter removes what is NOT
    in the filter set.
    '''
    kwargs = kwargs_in.copy()
    for data in filter_data:
        if not data:
            continue # ignore empty dict on new form
        if data['parameter'] != u'-':
            comp = data['comp']
            if reverse:
                comp = COMP_REVERSE[comp]
            kwargs['{}__{}'.format(data['parameter'], comp)
                                                        ] = data['threshold']
    return kwargs



def process_bookmarkform(bookmarkform, post, system_list):
    '''
    Process data from the bookmark form.
    '''
    if post.get('todo') == 'Bookmark Selected' and \
            bookmarkform.is_valid():
        bookmark_id = int(bookmarkform.cleaned_data['bookmark'])
        bookmark = Bookmark.objects.get(id=bookmark_id)
        for sys in System.objects.filter(id__in=system_list):
            sys.bookmark = bookmark
            sys.save()



#@login_required
#def show_systems(request, metasystem_id, action=None):
#    '''
#    Show all systems for MetaSystem <metasystem_id>
#    '''
#    message = ''
#
#    # clean up session:
#    if request.session.get('confirm_systems_delete') and action != 'delete':
#        del request.session['confirm_systems_delete']
#
#    # get (default) view settings:
#    key = 'show_systems_view_settings'
#    view_settings = request.session.get(key, {'parameters': True, 
#            'performance': True, 'result': True})
#
#    kwargs = {'metasystem__id': metasystem_id}
#
#    if request.method == 'POST':
#        system_list = request.POST.getlist('id')
#
#        bookmarkform = BookmarkForm(data=request.POST)
#        process_bookmarkform(bookmarkform, request.POST, system_list)
#
#        filterformset = FilterFormSet(data=request.POST)
#
#        del_kwargs = None
#        if request.POST.get('todo') == 'Delete Selected':
#            System.objects.filter(id__in=system_list).filter(
#                                            bookmark__isnull=True).delete()
#        elif request.POST.get('todo') == 'Change View':
##            print request.POST
#            view_settings = {
#                    'parameters': request.POST.get('parameters'),
#                    'performance': request.POST.get('performance'),
#                    'result': request.POST.get('result')}
#            request.session[key] = view_settings
##            print "VS", view_settings
#
#        elif request.POST.get('todo') == 'Delete filtered systems' and \
#                request.POST.get('confirm') == 'filtered':
#            del_kwargs = apply_filters(filterformset.cleaned_data, 
#                                                        kwargs, reverse=True)
#        elif request.POST.get('todo') == 'Delete displayed systems' and \
#                request.POST.get('confirm') == 'displayed':
#            del_kwargs = apply_filters(filterformset.cleaned_data, 
#                                                        kwargs, reverse=False)
#        if del_kwargs:
#            del_list = System.objects.filter(**del_kwargs).filter(
#                    bookmark__isnull=True).values_list('id', flat=True)
#            message = '{} systems deleted'.format(len(del_list))
#            i=0
#
#            cursor = connection.cursor()
#            for dl in [del_list[x:x+1000] for x in range(0, len(del_list), 1000)]:
#                with transaction.commit_on_success():
## use raw SQL here to speed up delete
#                    i+=1
#                    id_str = '({})'.format(', '.join(str(j) for j in dl))
#                    cursor.execute("delete from equity_equity where system_id in {}".format(id_str))
#                    cursor.execute("delete from tradesignal_trade where system_id in {}".format(id_str))
#                    cursor.execute("delete from equity_thumbnail where id_id in {}".format(id_str))
#                    cursor.execute("delete from system_system where id in {}".format(id_str))
#                    print 'deleted', i
#        clean_data = []
#        if filterformset.is_valid():
#            kwargs = apply_filters(filterformset.cleaned_data, kwargs)
#            for form in filterformset.cleaned_data:
#                if not form or form['DELETE']:
#                    continue
#                clean_data.append(form)
#            filterformset = FilterFormSet(initial=clean_data)
#
#    else: # this is the first page load
#        filterformset = FilterFormSet()
#        bookmarkform = BookmarkForm()
#
#
#    systems = System.objects.filter(**kwargs)
#
#    # check for actions on all systems
#    if action:
#        if action == 'delete':
#            if request.session.get('confirm_systems_delete'):
#                del request.session['confirm_systems_delete']
#                systems.delete()
#                message = 'All systems deleted'
#            else:
#                request.session['confirm_systems_delete'] = True
#                message = {'confirm': 'delete'}
#        else:
#            raise ValueError('action {} is invalid'.format(action))
#
##    if request.session.get['show_systems_parameters'] is None:
#    systems_table = MakeSystemsTable(data=systems, order_by=('-id',), 
#            show=view_settings, excludes=['metasystem'])
#
#    # generate column_titles
#    if systems.count():
#        systems_table.base_columns['params'].verbose_name = mark_safe(
#                        '</th><th>'.join(get_dict_keys(systems[0].params)))
#        for key, params in OUTPUT_FORMATS.items():
#            if 'title' in params:
#                systems_table.base_columns[key].verbose_name = params['title']
#    RequestConfig(request, paginate={'per_page': 100}).configure(systems_table)
#
#    metasystem = MetaSystem.objects.get(id=metasystem_id)
#    metasystem.build_structure()
#
#    return render(request, 'show_systems.html', {
#            'systems_table': systems_table, 
#            'metasystem_id': metasystem_id,
#            'view_settings': view_settings,
#            'n_systems': systems.count(),
#            'filterformset': filterformset,
#            'bookmarkform': bookmarkform,
#            'metasystem': metasystem,
#            'message': message,
#            })



@login_required
def show_system(request, system_id=None):
    '''
    Show System with <system_id>
    '''
    notify = None

    system = System.objects.get(id=system_id)
    metasystem = system.metasystem
    metasystem.make_system(system.params)

    # generate performance list
    performance = []
    results = []
    for param, fmt in OUTPUT_FORMATS.items():
        value = getattr(system, param, None)
        if fmt['type'] == 'performance' and value is not None: # 0 is allowed!
            performance.append((fmt['name'], fmt['format'].format(value)))
        if fmt['type'] == 'result' and value is not None:
            results.append((fmt['name'], fmt['format'].format(value)))

    #generate equity table
    equity = EquityHistory(system_id=system.id)
    if equity.exists():
        total_equity = equity.get('year')
        equity_table = EquityTable(total_equity, order_by=('date',))
        RequestConfig(request, paginate=None).configure(equity_table)
    else:
        equity_table = None
    #/equity table

    # copy system to method if required
    if request.method == 'POST':
        copyform = CopyForm(data=request.POST)
        if request.POST.get('action') == 'Copy System' and copyform.is_valid():
            new_ms_id = copyform.cleaned_data['metasystem']
            reverse = copyform.cleaned_data['reverse']
            for method in metasystem.method_set.all():
                parameters = system.get_params(method)
                method.copy(new_ms_id, parameters, reverse=reverse,
                        comment='copy from system {}'.format(system.id))
    else:
        copyform = CopyForm()

    # bookmark system if required
    if request.method == 'POST':
        bookmarkform = BookmarkForm(data=request.POST)
        if request.POST.get('action') == 'Bookmark Selected':
            process_bookmarkform(bookmarkform, request.POST, [system_id])
    elif system.bookmark:
        bookmarkform = BookmarkForm(initial={'bookmark': system.bookmark.id})
    else:
        bookmarkform = BookmarkForm()

    # process trades/positions
    tradeform = TradeForm()
    if request.method == 'POST':
        if request.POST.get('action') in ('Delete trade', 'Delete position'):
            trade_list = request.POST.getlist('tradeid')
            trades = ','.join(Trade.objects.get(id=t).stock.name for t in 
                    trade_list)
            if not len(trade_list):
                notify = Notify('Delete failed, select position to delete')
            else:
                notify = Notify('Delete Trade(s) {}?'.format(trades))
                notify.set_replies(request, ('Yes', 'No'))
                request.session['trade_delete_list'] = trade_list

        elif request.POST.get('reply'):
            trade_list = request.session.get('trade_delete_list')
            if not trade_list:
                raise AttributeError('session has no valid trade_delete_list')
            del request.session['trade_delete_list']
            if request.POST.get('reply') == 'Yes':
                trades = ','.join(Trade.objects.get(id=t).stock.name for t in 
                        trade_list)
                Trade.objects.filter(id__in=trade_list).delete()
                notify = Notify('Trade(s) {} deleted'.format(trades))
            elif request.POST.get('reply') == 'No':
                notify = Notify('Delete cancelled')

        else:
            tradeform = TradeForm(data=request.POST)
            if tradeform.is_valid():
                name = tradeform.cleaned_data.get('symbol').upper()
                volume = tradeform.cleaned_data.get('volume')
                price = tradeform.cleaned_data.get('price')
                date = tradeform.cleaned_data.get('date')
                method = system.metasystem.method_set.all()[0]
                if request.POST.get('action') == 'Enter position': 
                    if not volume:
                        notify = Notify('volume must be specified for entry')
                    else: 
                        try:
                            stock = Stock.objects.get(name=name)
                            print 'NAME', stock.name
                            trade = Trade(system=system, stock=stock,
                                    method=method, rule_entry='discret.',
                                    price_entry=price, date_entry=date,
                                    volume=volume)
                            trade.save()
                            notify = Notify('Position entered')
                        except:
                            notify = Notify('Failed to enter position')
                elif request.POST.get('action') == 'Exit position':
                    position_list = request.POST.getlist('positionid')
                    if len(position_list) != 1:
                        notify = Notify('One position must be selected to exit')
                    else:
                        position_id = position_list[0]
                        stock = Trade.objects.get(id=position_id).stock
                        try:
                            trade = Trade.objects.get(id=position_id,
                                    system=system, stock=stock, method=method, 
                                    rule_entry='discret.', rule_exit=None)
                            trade.rule_exit = 'discret.'
                            trade.price_exit = price
                            trade.date_exit = date
                            trade.save()
                            notify = Notify('Position exited')
                        except:
                            notify = Notify('Failed to exit position')

    else: # this is the first page load
        tradeform = TradeForm()

    #generate portfolio table
    trades = Trade.objects.filter(system=system, rule_exit=None)
    if len(trades):
        latest_date = trades[0].stock.get_latest_date()
        stoploss_date = next_weekday(latest_date)
    else:
        stoploss_date = None
    portfolio_table = PortfolioTable(trades, order_by=('date_entry',))
    RequestConfig(request, paginate=None).configure(portfolio_table)

    #generate trades table
    trades = Trade.objects.filter(system=system).exclude(rule_exit=None)
    trades_table = TradesTable(trades, order_by=('date_entry',))
    RequestConfig(request, paginate=None).configure(trades_table)
    #/trades table


    return render(request, 'show_system.html', {
            'metasystem': metasystem,
            'system': system,
            'trades_table': trades_table,
            'equity_table': equity_table,
            'performance': performance,
            'result': results,
            'copyform': copyform,
            'bookmarkform': bookmarkform,
            'portfolio_table': portfolio_table,
            'stoploss_date': stoploss_date,
            'tradeform': tradeform,
            'notify': notify,
            })



from system.forms import TradeForm

@login_required
def edit_system(request, system_id=None):
    '''
    Show System with <system_id>
    '''
    message = ''
    system = System.objects.get(id=system_id)

    # generate performance list
    performance = []
    results = []
    for param, fmt in OUTPUT_FORMATS.items():
        value = getattr(system, param, None)
        if fmt['type'] == 'performance' and value is not None: # 0 is allowed!
            performance.append((fmt['name'], fmt['format'].format(value)))
            results.append((fmt['name'], fmt['format'].format(value)))

    #generate equity table
    equity = EquityHistory(system_id=system.id)
    if equity.exists():
        total_equity = equity.get('year')
        equity_table = EquityTable(total_equity, order_by=('date',))
        RequestConfig(request, paginate=None).configure(equity_table)
    else:
        equity_table = None
    #/equity table

    #generate portfolio table
    trades = Trade.objects.filter(system=system, rule_exit=None)
    if len(trades):
        latest_date = trades[0].stock.get_latest_date()
        stoploss_date = next_weekday(latest_date)
    else:
        stoploss_date = None
    portfolio_table = PortfolioTable(trades, order_by=('date_entry',))
    RequestConfig(request, paginate=None).configure(portfolio_table)

    #generate trades table
    trades = Trade.objects.filter(system=system, rule_exit__isnull=False)
    trades_table = TradesTable(trades, exclude=('id', 'system'),
                                                    order_by=('date_entry',))
    RequestConfig(request, paginate=None).configure(trades_table)
    #/trades table

    # copy system to method if required
    if request.method == 'POST':
        if request.POST.get('todo') == 'Delete trade':
            trade_list = request.POST.getlist('tradeid')
            Trade.objects.filter(id__in=trade_list).delete()
            tradeform = TradeForm()
        else:
            tradeform = TradeForm(data=request.POST)
            if tradeform.is_valid():
                name = tradeform.cleaned_data.get('symbol').upper()
                volume = tradeform.cleaned_data.get('volume')
                price = tradeform.cleaned_data.get('price')
                date = tradeform.cleaned_data.get('date')
                method = system.metasystem.method_set.all()[0]
                if request.POST.get('todo') == 'Enter position': 
                    if not volume:
                        message = 'volume must be specified for entry'
                    else: 
                        try:
                            stock = Stock.objects.get(name=name)
                            print 'NAME', stock.name
                            trade = Trade(system=system, stock=stock,
                                    method=method, rule_entry='discret.',
                                    price_entry=price, date_entry=date,
                                    volume=volume)
                            trade.save()
                            message = 'Position entered'
                        except:
                            message = 'Failed to enter position'
                elif request.POST.get('todo') == 'Exit position':
                    position_list = request.POST.getlist('positionid')
                    if len(position_list) != 1:
                        message = 'One position must be selected to exit'
                    else:
                        position_id = position_list[0]
                        stock = Trade.objects.get(id=position_id).stock
                        try:
                            trade = Trade.objects.get(id=position_id,
                                    system=system, stock=stock, method=method, 
                                    rule_entry='discret.', rule_exit=None)
                            trade.rule_exit = 'discret.'
                            trade.price_exit = price
                            trade.date_exit = date
                            trade.save()
                            message = 'Position exited'
                        except:
                            message = 'Failed to exit position'

    else: # this is the first page load
        tradeform = TradeForm()


    return render(request, 'edit_system.html', 
            {'system': system,
            'trades_table': trades_table,
            'stoploss_date': stoploss_date,
            'equity_table': equity_table,
            'portfolio_table': portfolio_table,
            'tradeform': tradeform,
            'performance': performance,
            'result': results,
            'message': message })


def export_systems_to_csv(request, metasystem_id):
    '''
    View that returns csv files with all trades for this system/result.
    '''
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename="results_{}.csv"'.\
                                                        format(metasystem_id)
    results = System.objects.filter(metasystem=metasystem_id).values()
    column_list = [k for k in OUTPUT_FORMATS]
    column_list.extend(str2dict_keys(results[0]['params']))
    writer = csv.DictWriter(response, column_list, extrasaction='ignore')
    writer.writeheader()
    for result in results:
        result.update(str2dict(result['params']))
        writer.writerow(result)
    return response

