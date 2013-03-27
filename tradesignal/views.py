'''
tradesignal/views.py v0.1 121004

Created on 121004

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

import csv

from django.shortcuts import HttpResponse

from pricemanager.models import Stock
from metasystem.models import Method

from tradesignal.models import Trade

def export_trades_to_csv(request, system_id):
    '''
    Return csv file with all trades for this system.
    '''
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename="trades_{}.csv"'.\
            format(system_id)
    writer = csv.DictWriter(response, ('stock_symbol', 'stock_name', 
            'method_id', 'ls', 'volume', 'date_entry', 'price_entry', 
            'rule_entry', 'date_exit', 'price_exit', 'rule_exit',), 
            extrasaction='ignore')
    trades = Trade.objects.filter(system=system_id).values()
    writer.writeheader()
    for trade in trades:
        stock = Stock.objects.get(id=trade['stock_id'])
        trade['stock_symbol'] = stock.name
        trade['stock_name'] = stock.description
        trade['direction'] = Method.objects.get(id=trade['method_id']).direction
        writer.writerow(trade)
    return response