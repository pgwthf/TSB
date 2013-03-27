'''
params_alloc.py v0.2 130109

Created on 20120907

@author: edwin

This file contains all possible alloc classes, they are instantiated by the
ParamField class (fields.py) and they are used to calculate the position size.

Every alloc class MUST:
    * be named alloc_* and must be a subclass of _Alloc,
    * have a property called <name> that briefly describes what the class does,
    * have a property called <parameters> which is an OrderedDict with
    definitions of all parameters for the class. <parameters> always has a 
    <rule> member, even if if the class has no parameters.
    * have a method called <description> that takes no arguments ad returns a
    string that describes how the algorithm works, this string should contain
    all parameters of the class (excluding <rule>),
    * have a method called <size> that returns the number of stocks to enter,
    this method may take one or more of the following inputs:
        - entry_signal  EntrySignal instance to calculate the volume for
        - date          datetime instance, the allocation is calculated using
                        price data on <date> (the day before entry)
        - total_equity  integer that holds the total equity (cash + value of
                        stocks) on <date>

NOTE: **kwargs is added to the input of all <size> methods to future-proof it.
'''
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict

from metasystem.parameters.fields import _Param



class _Alloc(_Param):
    '''
    Methods that are common to all alloc_* classes go here.
    '''

    IDENTIFIER = 'A'



class alloc_n(_Alloc):
    '''
    Allocate a fixed number of shares.
    '''
    name = 'No. of shares'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('ns', dict(_Param.std_flt, **{'doc':
                'Number of shares that is allocated to each trade', 
                'verbose': 'Number of shares', 
                'range': (1, 1000000),
                'default': 1,
                })),
            ])

    def description(self):
        return 'Allocate {} shares to each entry.'.format(self.repr('ns'))

    def size(self, **kwargs):
        return self.ns



class alloc_val(_Alloc):
    '''
    Allocate a fixed currency value.
    '''
    name = 'Currency value'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('val', dict(_Param.std_flt, **{'doc':
                'Currency value that is allocated to each trade',
                'verbose': 'Trade size (currency value)',
                'range': (5000., 10000000.),
                'default': 10000.,
                'format': '${:3.2f}',
                })),
            ])

    def description(self):
        return 'Allocate {} to each entry.'.format(self.repr('val'))

    def size(self, entry_signal, date, **kwargs):
        return self.val // entry_signal.stock.price.close[date]



class alloc_pc(_Alloc):
    '''
    Allocate a fixed percentage of available equity (account value).
    '''
    name = 'Perc. of equity'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('pc', dict(_Param.std_pc, **{'doc':
                'Percentage of equity that is allocated to each trade',
                'verbose': 'Trade size (perc. equity)',
                'range': (5., 100.),
                'default': 20.,
                })),
            ])

    def description(self):
        return 'Allocate {} of the total equity each entry.'.format(
                self.repr('pc'))

    def size(self, entry_signal, date, total_equity, **kwargs):
        value = 0.01 * self.pc * total_equity
        return value // entry_signal.stock.price.close[date]



class alloc_r(_Alloc):
    '''
    Set allocation so that the risk of this trade is equal to a fixed percentage
    of the total equity.
    '''
    name = 'Risk'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('pc', dict(_Param.std_pc, **{'doc':
                'Percentage of equity that is risked in each trade',
                'verbose': 'Risk per trade (perc. equity)',
                'range': (0.1,2.),
                'default': 0.5,
                })),
            ])

    def description(self):
        return 'Allocate the amount of shares that results in a {}% risk.'.\
                format(self.repr('pc'))

    def size(self, entry_signal, date, total_equity, **kwargs):
        if entry_signal.method.direction != entry_signal.method.LONG:
            raise ValueError('only long trades are supported at the moment')
        price = entry_signal.get_price(date)
        stop = entry_signal.get_stop(date)
        sl = 100 * (1 - stop/price)
        sl = max(sl, 2) # stop loss (risk) is never less than 2%
        position_value = self.pc * total_equity / sl
        return position_value // price



class alloc_rl(_Alloc):
    '''
    Set allocation so that the risk of this trade is equal to a fixed percentage
    of the total equity, with a definition for an upper and lower limit for the 
    resulting allocation.
    '''
    name = 'Risk with limits'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('pc', dict(_Param.std_pc, **{'doc':
                'Risk per trade in % of the total equity',
                'verbose': 'Risk per trade (perc. equity)',
                'range': (0.1,2.),
                'default': 0.5,
                })),
            ('pch', dict(_Param.std_pc, **{'doc': 
                'Upper limit on the allocation size in % of total equity',
                'verbose': 'Max. allocation size (perc. eq.)',
                'range': (10.,100.),
                'default': 33.,
                })),
            ('pcl', dict(_Param.std_pc, **{'doc': 
                'Lower limit on the allocation size in % of total equity',
                'verbose': 'Min. allocation size (perc. eq.)',
                'range': (1.,50.),
                'default': 7.,
                })),
            ])

    def description(self):
        return 'Allocate the amount of shares that results in a {} risk, '\
                'limit the allocation between {} and {}.'.format(
                self.repr('pc'), self.repr('pcl'), self.repr('pch'))

    def size(self, entry_signal, date, total_equity, **kwargs):
        if entry_signal.method.direction != entry_signal.method.LONG:
            raise ValueError('only long trades are supported at the moment')
        price = entry_signal.get_price(date)
        stop = entry_signal.get_stop(date)
        sl = 100 * (1 - stop/price)
        sl = max(sl, 0.1) # prevent issues with div by 0
        # place an upper limit on the allocation size:
        allocation_fraction = min(self.pc / sl, 0.01 * self.pch)
        # only enter if the risk is low (i.e. allocation size is not too small):
        if allocation_fraction >  0.01 * self.pcl:
            position_value = allocation_fraction * total_equity
            return position_value // price
        else:
            return 0
