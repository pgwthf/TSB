'''
params_entry.py v0.2 130110

Created on 20120825

@author: edwin

This file contains all possible entry classes, they are instantiated by the
ParamField class (fields.py) and they are used to generate entry signals.

Every entry class MUST:
    * be named entry_* and must be a subclass of _Entry,
    * have a property called <name> that briefly describes what the entry does,
    * have a property called <parameters> which is an OrderedDict with
    definitions of all parameters for the class. <parameters> always has a
    <rule> member, even if if the class has no parameters.
    * have a method called <description> that takes no arguments ad returns a
    string that describes how the algorithm works, this description should
    contain all parameters of the class (excluding rule),
    * have a method called <signal> that returns an EntrySignal instance, the
    <signal> method may take one or more of the following inputs:
        - stock     Stock instance
        - method    Method instance
        - date      datetime instance, this signal is generated based on the
                    price data on date, the resulting entry signal is for 
                    execution on the next trading day

NOTE: **kwargs is added to the input of all <signal> methods to future-proof it.
'''
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict
import operator

from TSB.utils import get_choice
from tradesignal.models import EntrySignal
from metasystem.parameters.fields import _Param
from channel.models import Channel


class _Entry(_Param):
    '''
    Methods that are common to all entry_* classes go here.
    '''
    reverse = None
    IDENTIFIER = 'N'



class entry_d(_Entry):
    '''
    Does not return an entry signal - use this for discretionary systems
    '''
    name = 'Discretionary entry'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ])

    def description(self):
        return 'No automatic entries are generated'

    def signal(self, **kwargs):
        return None



class entry_day(_Entry):
    '''
    Returns an entry signal for the next trading day. The entry signal may be
    conditional or unconditional. In case of a conditional signal the reference
    price is todays open, high, low or close, as specified by <pr>.
    '''
    name = 'Daily entry'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('at', _Param.std_all_at),
            ('pr', _Param.std_price),
            ])

    def description(self):
        if self.repr('at') == get_choice(self.AT_CHOICES, self.STOP) or (
                self.repr('at') == get_choice(self.AT_CHOICES, self.LIMIT)):
            price = ' = todays {}'.format(self.repr('pr'))
        else:
            price = ''
        return 'Enter tomorrow at {}{}.'.format(self.repr('at'), price)

    def signal(self, stock, method, date, **kwargs):
        if self.at == self.OPEN or self.at == self.CLOSE:
            price = None
        elif self.pr == self.HIGH:
            price = stock.price.high[date]
        elif self.pr == self.LOW:
            price = stock.price.low[date]
        elif self.pr == self.OPEN:
            price = stock.price.open[date]
        elif self.pr == self.CLOSE:
            price = stock.price.close[date]
        return EntrySignal(stock, method, self.rule, self.at, price)



class entry_ndd(entry_day):
    '''
    '''
    name = 'n days down'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('at', _Param.std_all_at),
            ('pr', _Param.std_price),
            ('nd', _Param.std_nd),
            ('cd', dict(_Param.std_switch, **{
                'verbose': 'close down',
                })),
            ('rc', dict(_Param.std_switch, **{
                'verbose': 'red candles',
                })),
            ])

    def description(self):
        day = super(entry_ndd, self).description()
        condition = ''
        if self.repr('rc') == self.ON:
            condition = 'had red candles'
        if self.repr('cd') == self.ON:
            if self.repr('rc'):
                condition += ', and '
            condition += 'closed down'
        return 'If for the past {} days this stock {}: {}'.format(
                self.repr('nd'), condition, day)

    def signal(self, stock, method, date, **kwargs):
        close_down = True
        red_candles = True
        if self.cd:
            if not all(stock.price.close.offset(date, -nd - 1) >
                   stock.price.close.offset(date, -nd) for nd in 
                   range(self.nd)) :
                close_down = False
        if self.rc:
            if not all(stock.price.open.offset(date, -nd) > 
                      stock.price.close.offset(date, -nd) for nd in 
                      range(self.nd)) :
                red_candles = False
        if close_down and red_candles:
            return super(entry_ndd, self).signal(stock, method, date, **kwargs)


class entry_wk(_Entry):
    '''
    Returns an unconditional entry signal if the current trading day is in a
    new week.
    '''
    name = 'Entry on the first day of the week'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('at', _Param.std_at),
            ])

    def description(self):
        return 'Enter on the first trading day of the week at {}.'.format(
                self.repr('at'))

    def signal(self, stock, method, date, **kwargs):
        if date.isocalendar()[1] != stock.price.close.get_date(
                date, 1).isocalendar()[1]:
            return EntrySignal(stock, method, self.rule, self.at)


class entry_mt(_Entry):
    '''
    Returns an unconditional entry signal if the next trading day is in a new
    month.
    '''
    name = 'Entry on the first day of the month'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('at', _Param.std_at),
            ])

    def description(self):
        return 'Enter on the first trading day of the month at {}.'.format(
                self.repr('at'))

    def signal(self, stock, method, date, **kwargs):
        if date.month != stock.price.close.get_date(date, 1).month:
            return EntrySignal(stock, method, self.rule, self.at)



class entry_wr(_Entry):
    '''
    Returns an entry signal if <stock>'s Williams R on <date> is <op> the value
    of <th>, where the operator <op> is 'gt'or 'lt'. The entry may be at open
    or close, depending on the value of 'at'.
    This signal *will* be executed on the next trading day.
    '''
    name = 'Williams R'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('nd', _Param.std_nd),
            ('op', _Param.std_op),
            ('th', dict(_Param.std_int, **{
                'verbose': 'Threshold',
                'default': -20,
                'range': (-99, -1),
                'doc'  : 'Threshold for WR',
                })),
            ('at', _Param.std_at),
            ])

    def description(self):
        return 'Enter tomorrow at {} if todays {} day WR is {} {}.'.format(
                self.repr('at'), self.repr('nd'), self.repr('op'), 
                self.repr('th'))

    def signal(self, stock, method, date, **kwargs):
        wr = stock.price.wr(self.nd, date)
        if getattr(operator, self.op)(wr, self.th):
            return EntrySignal(stock, method, self.rule, self.at)



class entry_wrm(_Entry):
    '''
    Returns an entry signal if <stock>'s Williams R on <date> is <op> the value
    of <th> AND <stock>'s close price on <date> is <op> its <n_ma> day moving
    average, where the operator <op> is 'gt'or 'lt'. The entry may be at open
    or close, depending on the value of 'at'.
    '''
    name = 'Williams R and moving average'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('ndw', dict(_Param.std_nd, **{
                'verbose': 'Number of days for WR',
                'default': 10,
                })),
            ('opw', dict(_Param.std_op, **{
                'verbose': 'Operator for WR',
                })),
            ('thw', dict(_Param.std_int, **{
                'verbose': 'Threshold',
                'default': -20,
                'range': (-99, -1),
                'doc'  : 'Threshold for WR',
                })),
            ('at', _Param.std_at),
            ('ndm', dict(_Param.std_nd, **{
                'verbose': 'Number of days for MA',
                'default': 20,
                })),
            ('opm', dict(_Param.std_op, **{
                'verbose': 'Operator for MA',
                })),
            ])

    def description(self):
        return 'Enter tomorrow at {} if todays {} day WR is {} {} AND '\
                'todays close price is {} the {} day simple moving average.'\
                .format(self.repr('at'), self.repr('ndw'), self.repr('opw'), 
                self.repr('thw'), self.repr('opm'), self.repr('ndm'))

    def signal(self, stock, method, date, **kwargs):
        wr = stock.price.wr(self.ndw, date)
        if getattr(operator, self.opm)(stock.price.close[date], 
                stock.price.close.sma(self.ndm, date)) and \
                getattr(operator, self.opw)(wr, self.thw):
            return EntrySignal(stock, method, self.rule, self.at)



class entry_bo(_Entry):
    '''
    Returns an entry signal if <stock>'s close on <date> is <op> its <n_days>
    moving average + <mpl> * the <n_days> atr.
    '''
    name = 'Breakout entry'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('at', _Param.std_at),
            ('ndm', dict(_Param.std_nd, **{
                'verbose': 'No. of days for the MA',
                })),
            ('op', _Param.std_op),
            ('mpl', dict(_Param.std_flt, **{
                 'verbose': 'Multiplier for ATR',
                 'default': 1, 
                 'range': (-5., 5.),
                 })),
            ('nda', dict(_Param.std_nd, **{
                'verbose': 'No. of days for the ATR',
                'default': 10,
                })),
            ])

    def description(self):
        return 'Enter tomorrow at {} if todays close is {} (the {} day simple'\
                ' moving average plus {} times the {} day average true range)'\
                .format(self.repr('at'), self.repr('op'), self.repr('ndm'), 
                self.repr('mpl'), self.repr('nda'))

    def signal(self, stock, method, date, **kwargs):
        if getattr(operator, self.op)(stock.price.close[date], 
                stock.price.close.sma(self.ndm, date) + self.mpl *
                stock.price.atr(self.nda, date)):
            return EntrySignal(stock, method, self.rule, self.at)


class entry_ma(_Entry):
    '''
    Returns an entry signal if <stock>'s close price on <date> is <op> its 
    <n_ma> day moving average, where the operator <op> is 'gt'or 'lt'. The
    entry may be at open or close, depending on the value of 'at'. 
    This signal *will* be executed on the next trading day.
    '''
    name = 'Moving average crossover entry.'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('nd', _Param.std_nd),
            ('op', _Param.std_op),
            ('at', _Param.std_at),
            ])

    def description(self):
        return 'Enter tomorrow at {} if todays close price is {} the {} day '\
                'simple moving average.'.format(self.repr('at'), 
                self.repr('op'), self.repr('nd'))

    def signal(self, stock, method, date, **kwargs):
        if getattr(operator, self.op)(stock.price.close[date], 
                                      stock.price.close.sma(self.nd, date)):
            return EntrySignal(stock, method, self.rule, self.at)


# channel based entries
class entry_cwm(_Entry):
    '''
    '''
    name = 'ChW(1m)==ChWmin && ChAmin > 0'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('at', _Param.std_at),
            ])

    def description(self):
        return 'Enter tomorrow at {} if todays 1 month normalised channel '\
                'width is the lowest of all widths AND todays lowest '\
                'normalised channel angle > 0.'.format(self.repr('at'))

    def signal(self, stock, method, date, **kwargs):
        if (stock.price.channel.angle_min()[date] > 0) and (
                stock.price.channel.width_n(Channel.MONTH)[date] == 
                stock.price.channel.width_min()[date]):
            return EntrySignal(stock, method, self.rule, self.at)
