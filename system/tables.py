'''
systemmanager/tables.py v0.1 121003

Created on 121003

@author: edwin

NOTE: this file contains helper classes for django_tables2
'''
from __future__ import division
from __future__ import absolute_import

import datetime

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

import django_tables2 as tables

from pyutillib.string_utils import str2dict_values
from TSB.utils import make_link, get_choice
from TSB.tables import MakeSelectColumn
from tradesignal.models import Trade
from channel.models import Channel
from system.models import System, get_parameter_list


class ClickableImageColumn(tables.Column):
    '''
    Generates a clickable thumbnail image of the equity curve that links to
    the summary view of this system/result <sysview>
    '''
    def render(self, record):
        kwargs={'system_id': record.id}
        link = reverse('show_thumbnail', kwargs=kwargs)
        linktxt = '<img src="{}" />'.format(link)
        html = make_link('show_system', linktxt, kwargs=kwargs)
        return mark_safe(html)


class BookmarkColumn(tables.Column):
    '''
    Generates a link to the bookmark or an empty cell if there is no bookmark
    '''
    empty_values = []
    def render(self, record):
        if record.bookmark:
            return mark_safe(make_link('show_bookmarked_systems', 
                    record.bookmark.id, {'bookmark_id': record.bookmark.id}))
        else: return ''


def MakeSystemsTable(show={'parameters': True, 'performance': True, 
            'result': False}, excludes=[], **kwargs):
    '''
    Returns a table for displaying systems.
    '''
    exclude=['active', 'enddate',] + excludes

    if not show['parameters']:
        exclude.extend(['params'])
    if not show['performance']:
        exclude.extend(get_parameter_list('performance'))
    if not show['result']:
        exclude.extend(get_parameter_list('result'))
    kwargs['exclude'] = exclude

    class SystemsTable(tables.Table):
        select = MakeSelectColumn(orderable=False)
        id = ClickableImageColumn()
        max_pos = tables.Column(attrs={"td": {"class": "number"}})
        bookmark = BookmarkColumn()
        params = tables.Column(orderable=False)
        def render_params(self, record):
            return mark_safe('</td><td>'.join(('{}'.format(v) for v in 
                    str2dict_values(record.params))))
        def render_metasystem(self, record):
            return mark_safe(make_link('show_metasystem', record.metasystem.id, 
                    {'metasystem_id': record.metasystem.id}))
        class Meta:
            model = System
            attrs = {'class': 'paleblue', 'id': 'systable'}
            sequence = ('select', 'id', 'bookmark', 'max_win', 'max_loss',
                    'avg_win', 'avg_loss', 'trades_pa', 'reliability',
                    'profit_factor', 'expectancy', 'days_p_trade', 'sqn', 
                    'std_dev', 'exp_p_day', 'max_n_win', 'max_n_loss', 
                    'true_avg_loss', 'profit_pa', 'profit_ratio', 'ann_profit',
                    'n_neg_month', 'sum_neg_mths', 'min_year', 'max_year',
                    'min_month', 'max_month', 'max_dd', 'min_dd_ratio', 
                    'params', 'max_pos')
    return SystemsTable(**kwargs)



class PpaColumn(tables.Column):
    empty_values = []
    def render(self, record):
        date = record.stock.get_latest_date()
        n_days = max(1, record.stock.price.close.delta(record.date_entry, date))
        gain = float(record.stock.lastclose()/float(record.price_entry))
        return '{:1.0f}%'.format(min(999, 100 * (gain**(252/n_days) - 1)))


class PriceColumn(tables.Column):
    empty_values = []
    def render(self, record):
        return '{:3.2f}'.format(record.stock.lastclose())


class StoplossColumn(tables.Column):
    empty_values = []
    def render(self, record):
        stoploss = record.stoploss()
        if stoploss is not None:
            return '{:3.2f} ({:2.1f}%)'.format(stoploss, 100 * (
                    stoploss / float(record.price_entry) - 1))
        latest_date = record.stock.get_latest_date()
        # offset the entry date by 5 days, because channel date from the day
        #    before entry are required.
        record.stock.date_range = (record.date_entry - 
                    datetime.timedelta(days=5), latest_date)
#TODO: gcl = obsolete
        lookback = record.method.rank.get_channel_lookback()
        if lookback is None:
            lookback = Channel.YEAR
        stoploss = record.stock.price.channel.stoploss(lookback, latest_date,
                    record.date_entry)
        return mark_safe('<em>{:3.2f} ({:2.1f}%)</em>'.format(stoploss,
                100 * (stoploss / float(record.price_entry) - 1)))



class BaseTradeTable(tables.Table):
    gain = tables.Column()
    def render_gain(self, value):
        return '{:2.1f}%'.format(value)
    date_entry = tables.DateColumn(format='Y-m-d')
    date_exit = tables.DateColumn(format='Y-m-d')
    def render_id(self, record):
        kwargs = {'trade_id': record.id}
        return mark_safe(make_link('show_trade', record.stock.name, kwargs))
    def render_stock(self, record):
        kwargs = {'stock_id': record.stock.id}
        return mark_safe(make_link('show_stock', record.stock.description, kwargs))
    def render_price_entry(self, value):
        return '{:3.2f}'.format(value)
    def render_price_exit(self, value):
        return '' if value is None else '{:3.2f}'.format(value)
    def render_method(self, record):
        return '{}'.format(get_choice(record.method.DIR_CHOICES, 
                record.method.direction))


class TradesTable(BaseTradeTable):
    '''
    For django-tables2
    '''
    select = MakeSelectColumn('trade')
    class Meta:
        model = Trade
        attrs = {'class': 'paleblue'}
        sequence = ('select', 'id', 'stock', 'volume', 'date_entry', 
                'price_entry', 'rule_entry', 'date_exit', 'price_exit', 
                'rule_exit', 'method', 'gain', '...')
        exclude = ('system',)


class PortfolioTable(BaseTradeTable):
    '''
    Shows the current portfolio for discretionary systems
    '''
    select = MakeSelectColumn('position')
    ppa = PpaColumn()
    price = PriceColumn()
    stoploss = StoplossColumn()
    class Meta:
        model = Trade
        attrs = {'class': 'paleblue'}
        sequence = ('select', 'id', 'stock', 'volume', 'date_entry', 
                'price_entry', 'rule_entry', 'method', 'gain', 'ppa', 'price', 
                'stoploss', '...')
        exclude =  ('system', 'date_exit', 'price_exit', 'rule_exit')


class EquityTable(tables.Table):
    '''
    For django-tables2
    '''
    date = tables.Column()
    total = tables.Column()
    gain = tables.Column()
    period_gain = tables.Column()
    def render_total(self, value):
        return '{:3.2f}'.format(value)
    def render_gain(self, value):
        return '{:2.1f}%'.format(value)
    def render_period_gain(self, value):
        return '{:2.1f}%'.format(value)
    class Meta:
        attrs = {'class': 'paleblue'}
