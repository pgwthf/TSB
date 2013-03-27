'''
pricemanager/tables.py v0.1 120904

Created on 120904

@author: edwin

This file contains helper classes for django_tables2
'''

from __future__ import division
from __future__ import absolute_import

from django.utils.safestring import mark_safe
import django_tables2 as tables

from TSB.utils import make_link
from TSB.tables import MakeNameLinkColumn

from pricemanager.models import Pool, StockPoolDates, Channel

from TSB.tables import MakeSelectColumn



class UsedColumn(tables.Column):
    empty_values = []
    def render(self, record):
        n_times = record.metasystem_set.count()
        return '{}'.format(n_times) if n_times else ''


class PoolsTable(tables.Table):
    '''
    For django-tables2
    '''
    select = MakeSelectColumn(orderable=False)
    name = MakeNameLinkColumn('pool')
    def render_index(self, record):
        kwargs = {'stock_id': record.index.id}
        return mark_safe(make_link('show_stock', record.index.name, kwargs))
    used = UsedColumn()
    class Meta:
        model = Pool
        attrs = {'class': 'paleblue'}
        sequence = ('select', 'id', 'name', 'description', 'index', 'startdate',
                'enddate', 'used')



class MembersTable(tables.Table):
    '''
    For stocks in pool.
    '''
    def render_id(self, record):
        kwargs = {'stock_id': record.stock.id}
        return mark_safe(make_link('show_stock', record.stock.name, kwargs))
    def render_stock(self, value):
        html = '{}'.format(value.description)
        return mark_safe(html)
    class Meta:
        model = StockPoolDates
        attrs = {'class': 'paleblue'}



class ChannelsTable(MembersTable):
    '''
    For stocks in pool, using channels
TODO: sortable = False on price (bottom, close), sort by stoploss
TODO: right align prices
    '''
    def render_angle(self, value):
        return mark_safe('{:2.1f}'.format(value))
    def render_width(self, value):
        return mark_safe('{:2.1f}'.format(value))
    def render_bottom(self, value):
        return mark_safe('{:3.2f}'.format(value))
    origin = tables.Column
    def render_origin(self, record):
        return '{:3.2f}'.format(record.origin(record.close))
    stoploss = tables.Column()
    def render_stoploss(self, record):
        return '{:2.1f}%'.format(record.stoploss(record.close))
    close = tables.Column()
    def render_close(self, value):
        return '{:3.2f}'.format(value)
    class Meta:
        model = Channel
        attrs = {'class': 'paleblue'}
        exclude = ('date', 'lookback', 'pool', 'startdate', 'enddate')
        sequence = ('id', 'stock', 'angle', 'width', 'bottom', 'close', 
                'stoploss')


class SLshortColumn(tables.Column): #stop loss
    empty_values = []
    def render(self, record):
        bottom = float(record.bottom)
        close = record.stock.price.close[record.date]
        top = bottom * (record.width / 100 + 1)
        return '{:3.1f}'.format(100*(1 - close / top))

class ShortChannelsTable(ChannelsTable):
    '''
    For django-tables2
#TODO: sort out short representation in pool
    '''
    def render_origin(self, record):
        # TODO: NEED TOP CHANNEL LINE HERE??
        origin = float(record.origin)
        close = record.stock.price.close[record.date]
        top = origin * (record.width / 100 + 1)
        return '{:3.2f}'.format((top - close) / (top - origin))
    stop_loss = SLshortColumn()
    class Meta:
        model = Channel
        attrs = {'class': 'paleblue'}
        exclude = ('date', 'lookback')
