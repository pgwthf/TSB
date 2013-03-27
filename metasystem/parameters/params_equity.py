'''
params_equity.py v0.1 130107

Created on 130107

This file contains all possible equity model classes, they are instantiated by
the ParamField class (fields.py) and they are used to set limits to how equity
is allocated by adjusting (or deleting) the volume of entry signals.

Every equity class MUST:
    * be named equity_* and must be a subclass of _Equity,
    * have a property called <name> that briefly describes what the class does,
    * have a property called <parameters> which is an OrderedDict with
    definitions of all parameters for the class. <parameters> always has a 
    <rule> member, even if if the class has no parameters.
    * have a method called <description> that takes no arguments ad returns a
    string that describes how the algorithm works, this string should contain
    all parameters of the class (excluding <rule>),
    * have a method called <adjust_volume> that returns the adjusted number of 
    stocks to enter, this method may take one or more of the following inputs:
        - entry_signal  EntrySignal instance to calculate the volume for
        - date          datetime instance, the allocation is calculated using
                        price data on <date> (the day before entry)
        - total_equity  integer that holds the total equity (cash + value of
                        stocks) on <date>
        - cash          integer that holds the cash part of equity on <date>
        - positions     Positions instance
        - signals       Signals instance
        - volume        integer that holds the suggested volume as calculated by
                        the allocation algorithm

NOTE: **kwargs is added to the input of all <size> methods to future-proof it.
'''
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict

from TSB.utils import get_choice
from metasystem.parameters.fields import _Param, ModeWidget, ModeFloatField, \
        ModeListField



class _Equity(_Param):
    '''
    Methods that are common to all alloc_* classes go here.
    '''
    IDENTIFIER = 'E'

    SCALE = 's'
    MARGIN = 'm'
    NOT = 'n'
    ALL = 'a'
    EXCEED_CHOICES = (
            (SCALE, 'scale trade'), 
            (MARGIN, 'use margin'),
            (NOT, 'don\'t enter'), 
            (ALL, 'take trade'),
            )
    std_exceed = {'widget': ModeWidget, 
            'field': ModeListField,
            'format': '{}', 
            'doc': 'action if a trade exceeds the available cash',
            'verbose': 'Exceed equity', 
            'default': MARGIN,
            'choices': EXCEED_CHOICES, 
            }
    std_pce = {'widget': ModeWidget, 
            'field': ModeFloatField, 
            'format': '{:2.1f}%', 
            'doc': 'Minimum available cash for position',
            'verbose': 'Percentage cash available', 
            'default': 50., 
            'range': (0.,100.), 
            }


class equity_c(_Equity):
    '''
    Whether the trade is taken depends on the availability of cash and the value
    of <self.xc>. The options are:
        a: take any trade,
        n: only take trades when all cash is available
        m: only take a trade if at least <pce>% of the cash is available, 
            margin is used for the remainder
        s: only take a trade if at least <pce>% of the cash is available, the
            trade is scaled down to fit available cash
    Note that this class can be subclassed to combine the cash limit with other
        conditions.
    '''
    name = 'Available cash'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('xc', _Equity.std_exceed),
            ('pce', _Equity.std_pce),
            ])

    def description(self):
        if self.repr('xc') in (
                get_choice(_Equity.EXCEED_CHOICES, _Equity.NOT), 
                get_choice(_Equity.EXCEED_CHOICES, _Equity.ALL)):
            exceed = '{}'.format(self.repr('xc'))
        else:
            exceed = '{} if at least {} of the required cash is available'.\
                    format(self.repr('xc'), self.repr('pce'))
        return 'If there is not enough cash available for the next trade, ' \
                '{}.'.format(exceed)

    def adjust_volume(self, date, volume, cash, entrysignal, signals, **kwargs):
        available_cash = cash + signals.exits_cash(date) - \
                signals.entries_cash(date)
        price = entrysignal.get_price(date)
        if (volume * price < available_cash) or (self.xc == _Equity.ALL):
            return volume
        elif (available_cash < 0.01 * self.pce * volume * price) or (
                self.xc == _Equity.NOT):
            return 0
        elif self.xc == _Equity.MARGIN:
            return volume
        elif self.xc == _Equity.SCALE:
            return available_cash // price
        else:
            raise ValueError('xc = {}'.format(self.xc))



class equity_n(equity_c):
    '''
    Take trades up to a pre-set number of positions. Cash limits can also be set
    see equity_cashlimit for documentation.
    '''
    name = 'Max no of positions'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('xc', _Equity.std_exceed),
            ('pce', _Equity.std_pce),
            ('np', dict(_Param.std_int, **{
                'doc': 'maximum number of positions in the portfolio',
                'verbose': 'Max. number of positions', 
                'default': 5, 
                'range': (1, 20),
                })),
            ])

    def description(self):
        return 'Take trades up to a maximum of {} positions.'.format( \
                self.repr('np')) + super(equity_n, self).description()

    def adjust_volume(self, date, volume, cash, entrysignal, signals, 
            positions, **kwargs):
        if positions.size() + signals.count_executable_entries() + \
                signals.count_unconditional_exits() >= self.np:
            return 0
        return super(equity_n, self).adjust_volume(date=date, volume=volume,
                cash=cash, entrysignal=entrysignal, signals=signals, **kwargs)



class equity_sr(equity_c):
    '''
    Take trades up to a pre-set Total Stop Loss Risk (TSLR). TSLR is the sum of
    all stop loss values that are below their entry, i.e. TSLR is the maximum
    total loss if all positions would sell at their current stop loss.
    Cash limits can also be set, see equity_cashlimit for documentation.
    '''
    name = 'Max total stop risk'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('xc', _Equity.std_exceed),
            ('pce', _Equity.std_pce),
            ('pcr', dict(_Param.std_pc, **{
                'doc': 'Maximum Total Stop Loss Risk as a percentage of equity',
                'verbose': 'Maximum TSLR',
                'default': 1.,
                'range': (0.1, 10.), 
                })),
            ])

    def description(self):
        return 'Take trades up to a TSLR of {}.'.format(self.repr('pcr')) \
                + super(equity_sr, self).description()

    def adjust_volume(self, date, volume, cash, entrysignal, signals, 
                total_equity, positions, **kwargs):
        available_risk = 0.01 * self.pcr * total_equity - \
                positions.stop_loss_risk(date) - signals.stop_loss_risk(date)
        entry_risk = entrysignal.stop_loss_risk(date, volume)
        if (entry_risk < available_risk) or (self.xc == _Equity.ALL):
            pass # keep volume
        elif (available_risk < 0.01 * self.pce * entry_risk) or (
                self.xc == _Equity.NOT):
            return 0
        elif self.xc == _Equity.MARGIN:
            pass # keep volume
        elif self.xc == _Equity.SCALE:
            volume = int(volume * available_risk / entry_risk)
        else:
            raise ValueError('exceed = {}'.format(self.xc))
        return super(equity_sr, self).adjust_volume(date=date, volume=volume,
                cash=cash, entrysignal=entrysignal, signals=signals, **kwargs)


class equity_ter(equity_c):
    '''
    Take trades up to a pre-set Total Equity Risk (TER). TER is the sum of
    all stop values, i.e. TER is the maximum total drop of equity if all
    positions would sell at their current stop (loss).
    Cash limits can also be set, see equity_cashlimit for documentation.
    '''
    name = 'Max total equity risk'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('xc', _Equity.std_exceed),
            ('pce', _Equity.std_pce),
            ('pcr', dict(_Param.std_pc, **{
                'doc': 'Maximum Total Equity Risk as a percentage of equity',
                'verbose': 'Maximum TER',
                'default': 1.,
                'range': (0.1, 25.), 
                })),
            ])

    def description(self):
        return 'Take trades up to a TER of {}.'.format(self.repr('pc_risk')) \
                + super(equity_ter, self).description()

    def adjust_volume(self, date, volume, cash, entrysignal, signals, 
                total_equity, positions, **kwargs):
        available_risk = 0.01 * self.pc_risk * total_equity - \
                positions.equity_risk(date) - signals.equity_risk(date)
        entry_risk = entrysignal.equity_risk(date, volume)
        if (entry_risk < available_risk) or (self.exceed == _Equity.ALL):
            pass # keep volume
        elif (available_risk < 0.01 * self.pc_eq * entry_risk) or (
                self.exceed == _Equity.NOT):
            return 0
        elif self.exceed == _Equity.MARGIN:
            pass # keep volume
        elif self.exceed == _Equity.SCALE:
            volume = int(volume * available_risk / entry_risk)
        else:
            raise ValueError('exceed = {}'.format(self.exceed))
        return super(equity_ter, self).adjust_volume(date=date, volume=volume,
                cash=cash, entrysignal=entrysignal, signals=signals, **kwargs)
