'''
params_rank.py v0.1 1208030

Created on 20120830

@author: edwin

This file contains all possible rank classes, they are instantiated by the
ParamField class (fields.py) and used to prioritise the list of entry signals.

Every rank class MUST:
    * be named rank_* and must be a subclass of _Rank,
    * have a property called <name> that briefly describes what the class does,
    * have a property called <parameters> which is an OrderedDict with
    definitions of all parameters for the class. <parameters> always has a 
    <rule> member, even if if the class has no parameters.
    * have a method called <description> that takes no arguments ad returns a
    string that describes how the algorithm works, this string should contain
    all parameters of the class (excluding <rule>),
    * have a method called <get_list> that returns the ranked stock list, this
    method may take one or more of the following inputs:
        - date       datetime instance, the ranked list is calculated using
                     price data on <date> (the day before entry)
        - stock_list list that holds all stocks from the pool on <date>

NOTE: **kwargs is added to the input of all <get_list> methods to future-proof 
it.

Generally each ranking algorithm has an <op> and a <th> parameter that
specify the sorting order and a threshold for validity. In addition to those
parameters any other parameter can be added for the ranking value calculation.

The format of the ranked stock list (the return value of <get_list>) is a list
of tuples (stock, rank, valid) where:
    stock = the stock instance
    value = the value of the ranking parameter/index
    valid = boolean that indicates if the rank satisfies the threshold
'''
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict
import operator

import django_tables2 as tables

import TSB.tables as TSBtables
from pyutillib.math_utils import div
from metasystem.parameters.fields import _Param
from channel.models import Channel



class _Rank(_Param):
    '''
    Methods that are common to all rank_* classes go here.
    '''

    IDENTIFIER = 'R'

#TODO: gcl = obsolete
    def get_channel_lookback(self, trade=None):
        '''
        Return the lookback period of this trade if it is a channel based trade,
        None otherwise.
        It only checks for a channel in ranking (even though it is theoretically
        possible that a channel is used as an exit, but not rank !)
        '''
        try:
            self.repr('lb')
        except:
            return None
        lb = self._get_value('lb')
        print lb
        if isinstance(lb, int):
            return lb
        elif isinstance(lb, list) and len(lb) == 1:
            return lb[0]
        elif trade: 
            # lookback is a list or tuple with multiple values, so a trade
            #    must be specified
            metasystem = trade.system.metasystem
            metasystem.make_system(trade.system.params)
            for m in metasystem.methods:
                if m.id == trade.method.id:
                    return m.rank.lb
            return None
        else:
            return None



class rank_none(_Rank):
    '''
    Returns a list of stocks ordered by their symbol. All stocks are valid.
    '''
    name = 'Alphabetic ranking.'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ])

    def description(self):
        return 'The stocklist is ranked by stock name in alphabetic order.'

    def get_list(self, stock_list, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            value = stock.name
            valid = True
            ranked_stocklist.append((stock, value, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1))
        return ranked_stocklist


class rank_roc(_Rank):
    '''
    Returns a ranked list based on the rate of change between <date> and <n_d>
    trading days before <date> as a percentage.
    The list is ordered by the roc percentage in descending order if <op> is 
    'gt', and in ascending order if <op> is 'lt'.
    Stocks are valid if their roc is <op> the threshold <th>.
    '''
    name = 'Rate of change based ranking.'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('nd', _Param.std_nd),
            ('op', _Param.std_op),
            ('th', dict(_Param.std_pc, **{
                'doc': 'threshold for the rank',
                'verbose': 'Threshold for ROC', 
                'default': 0.,
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day roc. Only consider roc values {} '\
                '{}.'.format(self.repr('nd'), self.repr('op'), 
                self.repr('th'))

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            value = stock.price.close.roc(self.nd, date)
            valid = getattr(operator, self.op)(value, self.th)
            ranked_stocklist.append((stock, value, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), 
                reverse=(self.op == 'gt'))
        return ranked_stocklist



class rank_cha(_Rank):
    '''
    Returns a ranked list based on the channel data over the past <n_days>
    trading days before <date> as a percentage.
    The list is ordered by the channel angle in descending order if <op> is 
    'gt', and in ascending order if <op> is 'lt'.
    Stocks are valid if their angle is <op> the threshold <tha>.
    '''
    name = 'Channel angle based ranking.'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', _Param.std_lb),
            ('op', _Param.std_op),
            ('tha', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel angle',
                'verbose': 'Threshold for angle', 
                'default': 0.,
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day channel angle. Only consider '\
                'angles {} {}.'.format(self.repr('lb'), self.repr('op'), 
                self.repr('tha'))

    def _get_rank(self, angle):
        return angle, getattr(operator, self.op)(angle, self.tha)

    def get_table(self, stock_list, date, **kwargs):
        channels = Channel.with_close.filter(stock__in=stock_list, date=date,
                lookback=self.lb)
        newlist = []
        for c in channels:
            value, valid = self._get_rank(c.angle)
            if valid:
                newlist.append({
                        'symbol': c.stock,
                        'company': c.stock,
                        'quality': c.quality,
                        'angle': value,
                        'width': c.width,
                        'bottom': c.bottom,
                        'close': c.close,
                        'rc': c.rc,
                        'stoploss': c.stoploss,
                        })
        newlist.sort(key=operator.itemgetter('angle'), 
                reverse=(self.op == 'gt'))
        return newlist

    def make_table(self, **kwargs):
        class RankTable(tables.Table):
            symbol = TSBtables.SymbolColumn()
            company = TSBtables.CompanyColumn()
            quality = TSBtables.MakeFloatColumn('{:3.2f}')
            angle = TSBtables.MakeFloatColumn('{:2.1f}%')
            width = TSBtables.MakeFloatColumn('{:2.1f}%')
            bottom = TSBtables.MakeFloatColumn('{:3.2f}')
            close = TSBtables.MakeFloatColumn('{:3.2f}')
            rc = TSBtables.MakeFloatColumn('{:3.2f}')
            stoploss = TSBtables.MakeFloatColumn('{:2.1f}%')
            class Meta:
                attrs = {'class': 'paleblue'}
        return RankTable(**kwargs)

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            value, valid = self._get_rank(
                    stock.price.channel.angle(self.lb)[date])
#             value = stock.price.channel.angle(self.lb)[date]
#             valid = getattr(operator, self.op)(value, self.tha)
            ranked_stocklist.append((stock, value, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), 
                reverse=(self.op == 'gt'))
        return ranked_stocklist



class rank_chq(_Rank):
    '''
    Returns a ranked list based on the channel data over the past <n_days>
    trading days before <date> as a percentage.
    The list is ordered by the channel angle in descending order if <op> is 
    'gt', and in ascending order if <op> is 'lt'.
    Stocks are valid if their quality is <op> the threshold <thq>.
    '''
    name = 'Channel quality based ranking.'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', _Param.std_lb),
            ('op', _Param.std_op),
            ('thq', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel quality',
                'verbose': 'Threshold for quality', 
                'default': 0.,
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day channel quality. Only consider '\
                'quality {} {}.'.format(self.repr('lb'), self.repr('op'), 
                self.repr('thq'))

    def _get_rank(self, angle, width):
        value = div(angle, width)
        valid = getattr(operator, self.op)(value, self.thq)
        return value, valid

    def get_table(self, stock_list, date, **kwargs):
        channels = Channel.with_close.filter(stock__in=stock_list, date=date,
                lookback=self.lb)
        newlist = []
        for c in channels:
            value, valid = self._get_rank(c.angle, c.width)
            if valid:
                newlist.append({
                        'symbol': c.stock,
                        'company': c.stock,
                        'quality': value,
                        'angle': c.angle,
                        'width': c.width,
                        'bottom': c.bottom,
                        'close': c.close,
                        'rc': c.rc,
                        'stoploss': c.stoploss,
                        })
        newlist.sort(key=operator.itemgetter('quality'), 
                reverse=(self.op == 'gt'))
        return newlist

    def make_table(self, **kwargs):
        class RankTable(tables.Table):
            symbol = TSBtables.SymbolColumn()
            company = TSBtables.CompanyColumn()
            quality = TSBtables.MakeFloatColumn('{:3.2f}')
            angle = TSBtables.MakeFloatColumn('{:2.1f}%')
            width = TSBtables.MakeFloatColumn('{:2.1f}%')
            bottom = TSBtables.MakeFloatColumn('{:3.2f}')
            close = TSBtables.MakeFloatColumn('{:3.2f}')
            rc = TSBtables.MakeFloatColumn('{:3.2f}')
            stoploss = TSBtables.MakeFloatColumn('{:2.1f}%')
            class Meta:
                attrs = {'class': 'paleblue'}
        return RankTable(**kwargs)

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            value, valid = self._get_rank(
                    stock.price.channel.angle(self.lb)[date],
                    stock.price.channel.width(self.lb)[date])
#            value = div(stock.price.channel.angle(self.lb)[date],
#                    stock.price.channel.width(self.lb)[date])
#            valid = getattr(operator, self.op)(value, self.thq)
            ranked_stocklist.append((stock, value, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), 
                reverse=(self.op == 'gt'))
        return ranked_stocklist


class rank_chq2(_Rank):
    '''
    Returns a ranked list based on the channel data over the past <n_days>
    trading days before <date> as a percentage.
    The list is ordered by the channel angle in descending order if <op> is 
    'gt', and in ascending order if <op> is 'lt'.
    Stocks are valid if their quality is <op> the threshold <thq>.
    '''
    name = 'Channel quality based ranking 2'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', _Param.std_lb),
            ('op', _Param.std_op),
            ('thq', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel quality',
                'verbose': 'Threshold for quality', 
                'default': 0.,
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day channel quality. Only consider '\
                'quality {} {}.'.format(self.repr('lb'), self.repr('op'), 
                self.repr('thq'))

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
#            value = div(stock.price.channel.angle(self.lb)[date] *
#                    stock.price.channel.bottom(self.lb)[date],
#                    stock.price.channel.width(self.lb)[date] *
#                    stock.price.close[date])
            value = div(stock.price.channel.angle(self.lb)[date],
                    stock.price.channel.width(self.lb)[date]
                    ) * (1 - stock.price.channel.rc(self.lb)[date])
            valid = getattr(operator, self.op)(value, self.thq)
            ranked_stocklist.append((stock, value, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), 
                reverse=(self.op == 'gt'))
        return ranked_stocklist



#FIXME: exit must know lb, so use ctha or ctls
class rank_chqn(_Rank):
    '''
    Returns a ranked list based on normalised channel data.
    The list is ordered by the channel quality in descending order if <op> is 
    'gt', and in ascending order if <op> is 'lt'.
    Stocks are valid if their quality is <op> the threshold <thq>.
    '''
    name = 'Channel quality - normalised'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('op', _Param.std_op),
            ('thq', dict(_Param.std_pc, **{
                'doc': 'threshold for the normalised channel quality',
                'verbose': 'Threshold for quality', 
                'default': 0.,
                })),
            ])

    def description(self):
        return 'Rank stocks by their normalised channel quality. Only consider'\
                ' quality {} {}.'.format(self.repr('op'), self.repr('thq'))

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for lb in Channel.LOOKBACKS:
            for stock in stock_list:
                value = stock.price.channel.quality_n(lb)[date]
                valid = getattr(operator, self.op)(value, self.thq)
# ? is this a good idea?
                if valid:
                    ranked_stocklist.append((stock, value, valid))
# ?
        if ranked_stocklist:
            ranked_stocklist.sort(key=operator.itemgetter(1), 
                    reverse=(self.op == 'gt'))
        return ranked_stocklist



class rank_chqs(_Rank):
    '''
    Returns a ranked list ordered by channel quality over the past <n_days>
    trading days before <date>. Quality below <q_th> are cut from the list, as
    are virtual stop losses above <vsl_th>.
    The list is ordered by the channel quality in descending order.
    '''
    name = 'Channel quality based ranking with virtual stop loss threshold.'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', _Param.std_lb),
            ('thq', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel quality',
                'verbose': 'Threshold for quality', 
                'default': 0.,
                })),
            ('ths', dict(_Param.std_pc, **{
                'doc': 'threshold for the virtual stop loss',
                'verbose': 'Threshold for stop loss', 
                'default': 1.,
                'range': (0.5, 100.),
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day channel quality. Only consider '\
                'stocks with quality greater than {} and VSL lower than {}.'.\
                format(self.repr('lb'), self.repr('thq'), self.repr('ths'))

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            quality = div(stock.price.channel.angle(self.lb)[date],
                    stock.price.channel.width(self.lb)[date])
            vsl = stock.price.channel.stoploss(self.lb, date)
            vsl_p = 100 * (1 - vsl / stock.price.close[date])
            valid = (quality > self.thq) and (vsl_p < self.ths)
            ranked_stocklist.append((stock, quality, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), reverse=True)
        return ranked_stocklist



class rank_chas(_Rank):
    '''
    Returns a ranked list ordered by channel angle over the past <n_days>
    trading days before <date>. Angles below <tha> are cut from the list, as
    are virtual stop losses above <ths>.
    The list is ordered by the channel angle in descending order.
    '''
    name = 'Channel angle based ranking with virtual stop loss threshold.'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', _Param.std_lb),
            ('tha', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel angle',
                'verbose': 'Threshold for angle', 
                'default': 0.,
                })),
            ('ths', dict(_Param.std_pc, **{
                'doc': 'threshold for the virtual stop loss',
                'verbose': 'Threshold for stop loss', 
                'default': 1.,
                'range': (0.5, 100.),
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day channel angle. Only consider '\
                'stocks with angles greater than {} and VSL lower than {}.'.\
                format(self.repr('lb'), self.repr('tha'), self.repr('ths'))

    def _get_rank(self, angle, stoploss, close):
        vsl = 100 * (1 - stoploss / float(close))
        valid = (angle > self.tha) and (vsl < self.ths)
        return angle, valid

    def get_table(self, stock_list, date, **kwargs):
        channels = Channel.with_close.filter(stock__in=stock_list, date=date,
                lookback=self.lb)
        newlist = []
        for c in channels:
            value, valid = self._get_rank(c.angle, c.stoploss(), c.close)
            if valid:
                newlist.append({
                        'symbol': c.stock,
                        'company': c.stock,
#                        'quality': value,
                        'angle': c.angle,
                        'width': c.width,
                        'bottom': c.bottom,
                        'close': c.close,
                        'rc': c.rc,
                        'stoploss': c.stoploss,
                        })
        newlist.sort(key=operator.itemgetter('angle'), 
                reverse=(self.op == 'gt'))
        return newlist

    def make_table(self, **kwargs):
        class RankTable(tables.Table):
            symbol = TSBtables.SymbolColumn()
            company = TSBtables.CompanyColumn()
#            quality = TSBtables.MakeFloatColumn('{:3.2f}')
            angle = TSBtables.MakeFloatColumn('{:2.1f}%')
            width = TSBtables.MakeFloatColumn('{:2.1f}%')
            bottom = TSBtables.MakeFloatColumn('{:3.2f}')
            close = TSBtables.MakeFloatColumn('{:3.2f}')
            rc = TSBtables.MakeFloatColumn('{:3.2f}')
            stoploss = TSBtables.MakeFloatColumn('{:2.1f}%')
            class Meta:
                attrs = {'class': 'paleblue'}
        return RankTable(**kwargs)

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            angle, valid = self._get_rank(
                    stock.price.channel.angle(self.lb)[date],
                    stock.price.channel.stoploss(self.lb, date),
                    stock.price.close[date])
#             angle = stock.price.channel.angle(self.lb)[date]
#             vsl = stock.price.channel.stoploss(self.lb, date)
#             vsl_p = 100 * (1 - vsl / stock.price.close[date])
#             valid = (angle > self.tha) and (vsl_p < self.ths)
            ranked_stocklist.append((stock, angle, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), reverse=True)
        return ranked_stocklist



class rank_chasw(_Rank):
    '''
    Returns a ranked list ordered by channel angle over the past <n_days>
    trading days before <date>. Angles below <tha> are cut from the list, as
    are virtual stop losses above <ths> and widths above <thw>.
    The list is ordered by the channel angle in descending order.
    '''
    name = 'Channel angle based ranking with sl and w threshold.'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', _Param.std_lb),
            ('tha', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel angle',
                'verbose': 'Threshold for angle', 
                'default': 0.,
                })),
            ('thw', dict(_Param.std_pc, **{
                'doc': 'threshold for the channel width',
                'verbose': 'Threshold for width', 
                'default': 25.,
                'range': (1., 100.),
                })),
            ('ths', dict(_Param.std_pc, **{
                'doc': 'threshold for the virtual stop loss',
                'verbose': 'Threshold for stop loss', 
                'default': 1.,
                'range': (0.5, 100.),
                })),
            ])

    def description(self):
        return 'Rank stocks by their {} day channel angle. Only consider '\
                'stocks with angles greater than {}, width lower than {} and '\
                'VSL lower than {}.'.format(self.repr('lb'), self.repr('tha'),
                self.repr('thw'), self.repr('ths'))

    def get_list(self, stock_list, date, **kwargs):
        ranked_stocklist = []
        for stock in stock_list:
            angle = stock.price.channel.angle(self.lb)[date]
            width = stock.price.channel.width(self.lb)[date]
            vsl = stock.price.channel.stoploss(self.lb, date)
            vsl_p = 100 * (1 - vsl / stock.price.close[date])
            valid = (angle > self.tha) and (vsl_p < self.ths) and (
                    width < self.thw)
            ranked_stocklist.append((stock, angle, valid))
        ranked_stocklist.sort(key=operator.itemgetter(1), reverse=True)
        return ranked_stocklist
