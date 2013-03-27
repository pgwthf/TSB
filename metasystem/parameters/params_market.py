'''
params_market.py v0.1 130219

Created on 20130219

@author: edwin

This file contains all possible market type classes, they are instantiated 
by the ParamField class (fields.py) and used to generate a prioritised list of
(market) methods.

Every market class MUST:
    * be named market_* and must be a subclass of _Market,
    * have a property called <name> that briefly describes what the class does,
    * have a property called <parameters> which is an OrderedDict with
    definitions of all parameters for the class. <parameters> always has a 
    <rule> member, even if if the class has no parameters.
    * have a method called <description> that takes no arguments ad returns a
    string that describes how the algorithm works, this string should contain
    all parameters of the class (excluding <rule>),

    * have a method called <get_methods> that returns an ordered list of methods
    that may be entered. Note that the return list may have fewer members than
    the input list or may even be empty. This method may take one or more of the
    following inputs:
        - method_list   Python list with all methods of the current metasystem,
                        this list is already ordered by markettype and id.

NOTE: **kwargs is added to the input of all <size> methods to future-proof it.
'''
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict

from metasystem.parameters.fields import _Param, ModeWidget, ModeListField
from metasystem.parameters import algorithms_market
from TSB.utils import get_choice



class _Market(_Param):
    '''
    Methods that are common to all classes go here.
    '''
    IDENTIFIER = 'M'

    ANY = 0
    UP = 1
    FLAT = 2
    DOWN = 4
    QUIET = 8
    NORMAL = 16
    VOLATILE = 32
#    TRENDS = (UP, FLAT, DOWN)
#    VOLATILITIES = (QUIET, NORMAL, VOLATILE)
    MKT_CHOICES = (
            (ANY, 'Any'), # just a label
            (UP, 'Up'),
            (FLAT, 'Flat'),
            (DOWN, 'Down'),
            (QUIET, 'Quiet'),
            (NORMAL, 'Normal'),
            (VOLATILE, 'Volatile'),
            (QUIET + UP, 'Quiet up'),
            (QUIET + FLAT, 'Quiet flat'),
            (QUIET + DOWN, 'Quiet down'),
            (NORMAL + UP, 'Normal up'),
            (NORMAL + FLAT, 'Normal flat'),
            (NORMAL + DOWN, 'Normal down'),
            (VOLATILE + UP, 'Volatile up'),
            (VOLATILE + FLAT, 'Volatile flat'),
            (VOLATILE + DOWN, 'Volatile down'),
    )

    def initialise(self, pool):
        self.pool = pool
        self._trend = {}
        self._volatility = {}
        return {}

    def get_trend(self):
        return None

    def get_volatility(self):
        return None

    def trend(self, algorithm, *args, **kwargs):
        '''
        Return a DatedList with trend values.
        '''
        if algorithm not in self._trend:
            trend, volatility = getattr(algorithms_market, algorithm)(
                    self, *args, **kwargs)
            if trend is None:
                raise AttributeError('Algorithm {} did not return trend data'\
                        .format(algorithm))
            else:
                self._trend[algorithm] = trend
            if volatility is not None:
                self._volatility[algorithm] = volatility
        return self._trend[algorithm]

    def volatility(self, algorithm, *args, **kwargs):
        '''
        Return a DatedList with volatility values.
        '''
        if algorithm not in self._volatility:

            trend, volatility = getattr(algorithms_market, algorithm)(
                    self, *args, **kwargs)
            if volatility is None:
                raise AttributeError('Algorithm {} did not return volatility '\
                        'data'.format(algorithm))
            else:
                self._volatility[algorithm] = volatility
            if trend is not None:
                self._trend[algorithm] = trend
        return self._volatility[algorithm]

    def get_methods(self, date, method_list, **kwargs):
#CONSIDER: traverse entire list and then return list
        trend = self.get_trend()[date]
        for method in method_list:
            if trend & method.markettype or method.markettype == self.ANY:
                return [method,]
        return []



class market_none(_Market):
    '''
    Don't use market type, select the methods in order of their definition.
    '''
    name = 'None'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ])

    def description(self):
        return 'Don\'t use market type'

    def get_methods(self, method_list, **kwargs):
        return method_list



class market_ca(_Market):
    '''
    Trend only market type based on channel angles.

    Trend is UP if angles of all selected channels > 0
    Trend is DOWN if angles of all selected channels < 0
    Trend is FLAT otherwise.

    <mode> determines what channels are included in the 
    All channels with lookbacks below the specified lb are selected.
    '''
    name = 'Channel: multiple Angles'
    UPTO = 'u'
    FROM = 'f'
    ONE = '1'
    MODE_CHOICES = (
            (UPTO, 'up to'),
            (FROM, 'from'),
            (ONE, 'one'),
            )
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', dict(_Param.std_lb, **{'doc': 
                'The angles of all lookback periods up to this one are used',
                'verbose': 'Highest lookback', 
                })),
            ('mo', {'widget': ModeWidget, 
                'field': ModeListField, 
                'format': '{}', 
                'doc': 'Define channels to include',
                'verbose': 'Mode', 
                'default': ONE, 
                'choices': MODE_CHOICES,}),
            ])

    def description(self):
        if self.repr('mo') == get_choice(self.MODE_CHOICES, self.ONE):
            mode = 'angle of channel {} is'.format(self.repr('lb'))
            flat = '.'
        else:
            mode = 'angles of all channels {} {} are'.format(self.repr('mo'), 
                    self.repr('lb'))
            flat = ', Flat otherwise.'
        return 'Market type is Up if the {} positive, Down if negative{}'.\
                format(mode, flat)

    def get_trend(self):
        kwargs = {'lb': self.lb, 'mode': self.mo}
        return self.trend('cham', **kwargs)



class market_cr(_Market):
    '''
    Trend only market type based on channel rc.

    Trend is UP if rc > th
    Trend is DOWN if rc < th
    '''
    name = 'Channel rc'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', dict(_Param.std_lb, **{'doc': 
                'The angles of all lookback periods up to this one are used',
                'verbose': 'Highest lookback', 
                })),
            ('th', dict(_Param.std_flt, **{'doc':
                'Threshold for the channel coefficient rc', 
                'verbose': 'Channel rc threshold', 
                'range': (0., 1.),
                'default': 0.5,
                })),
            ])

    def description(self): 
        return 'Market type is Up if the {} channel rc > {}, Down otherwise.'.\
                format(self.repr('lb'), self.repr('th'))

    def get_trend(self):
        kwargs = {'lb': self.lb, 'th': self.th}
        return self.trend('chrc', **kwargs)



class market_m(_Market):
    '''
    Trend only market type, based on moving average.

    Trend may have the following values: Up, Flat, Down, where Flat is optional
    and only exists if <thu> is different from <thd>.
    <thu> is the lower threshold of an Up trend and <thd> is the upper 
    threshold of a Down trend. If both values are equal, trend may only have 2
    values (Up, Down).

    Set hysteresis to 0 to switch it off (default).
    '''
    name = 'Trend by moving average'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('nma', dict(_Param.std_int, **{'doc':
                'Numbert of days for moving average', 
                'verbose': 'Moving avg. period (days)', 
                'range': (1, 252),
                'default': 250,
                })),
            ('hma', dict(_Param.std_pc, **{'doc':
                'Hysteresis in % for moving average', 
                'verbose': 'Moving avg. hysteresis (%)', 
                'range': (0., 5.),
                'default': 0.,
                })),
            ('thu', dict(_Param.std_pc, **{'doc':
                'Threshold in % of the moving average between Up and Flat (or'\
                ' Down) markets', 
                'verbose': 'Moving avg. threshold for Up market', 
                'range': (-10., 10.),
                'default': 0.,
                })),
            ('thd', dict(_Param.std_pc, **{'doc':
                'Threshold in % of the moving average between Down and Flat '\
                '(or Up) markets', 
                'verbose': 'Moving avg. threshold for Down market', 
                'range': (-10., 10.),
                'default': 0.,
                })),
            ])

    def description(self):
        if self.repr('thu') == self.repr('thd'):
            flat = ', else it is Down.'
        else:
            flat = ', and Down if it is {} lower, Flat if it is between the two.'
        hysteresis = ' Hysteresis is {}.' if self.repr('hma') == '0.0%' else ''
        return 'Market type is Up if the pool index is {} higher than its {} '\
                'day moving average{}{}'.format(self.repr('thu'), 
                self.repr('nma'), flat, hysteresis)

    def get_trend(self):
        kwargs = {'n_ma': self.nma, 'hysteresis': self.hma}#, 'th_u': self.thu,
                #'th_d': self.thd}
        return self.trend('ma2', **kwargs)



class market_ma(_Market):
    '''
    Trend based on moving average and volatility on Avg true range

    Trend may have the following values: Up, Flat, Down, where Flat is optional
    and only exists if <thu> is different from <thd>.
    <thu> is the lower threshold of an Up trend and <thd> is the upper 
    threshold of a Down trend. If both values are equal, trend may only have 2
    values (Up, Down).

    Volatility may have the following values: Quiet, Normal, High, where Normal
    is optional and only exists if <thq> is different from <thv>.

    Both trend and volatility may have hysteresis, set hysteresis to 0 to switch
    it off (default).
    '''
    name = 'MA trend, ATR volatility'
    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('nma', dict(_Param.std_int, **{'doc':
                'Numbert of days for moving average', 
                'verbose': 'Moving avg. period (days)', 
                'range': (1, 252),
                'default': 250,
                })),
            ('hma', dict(_Param.std_pc, **{'doc':
                'Hysteresis in % for moving average', 
                'verbose': 'Moving avg. hysteresis (%)', 
                'range': (0., 5.),
                'default': 0.,
                })),
            ('thu', dict(_Param.std_pc, **{'doc':
                'Threshold in % of the moving average between Up and Flat (or'\
                ' Down) markets', 
                'verbose': 'Moving avg. threshold for Up market', 
                'range': (-10., 10.),
                'default': 0.,
                })),
            ('thd', dict(_Param.std_pc, **{'doc':
                'Threshold in % of the moving average between Down and Flat '\
                '(or Up) markets', 
                'verbose': 'Moving avg. threshold for Down market', 
                'range': (-10., 10.),
                'default': 0.,
                })),
            ])

    def description(self):
        return 'Take {} trades first. Exits {} trades when a signal for the '\
                'opposite trade occurs'.format(self.repr('dir'), 
                self.repr('fe'))

    def get_methods(self, date, method_list, pool, **kwargs):
        self.method = method_list[0] #to get access to DOWN, UP, etc.
        kwargs = {'n_ma': self.nma, 'hysteresis': self.hma, 'th_u': self.thu,
                'th_d': self.thd}
        trend = self.trend('ma2', pool, **kwargs)[date]
        kwargs = {'n_atr': self.na, 'hysteresis': self.ha, 'th_q': self.thq,
                'th_v': self.thv}
        volatility = self.volatility('atr2', pool, **kwargs)[date]
        markettype = trend + volatility
        for method in method_list:
            if method.markettype == markettype:
                return [method]
        return []

#OBSOLETE:

class market_cm(_Market):
    '''
    Trend only market type based on channel angles.

    Trend is UP if angles of all selected channels > 0
    Trend is DOWN if angles of all selected channels < 0
    Trend is FLAT otherwise.

    <mode> determines what channels are included in the 
    All channels with lookbacks below the specified lb are selected.
    '''
    name = 'OBSOLETE Channel: multiple Angles'

    parameters = OrderedDict([
            ('rule', _Param.std_rule),
            ('lb', dict(_Param.std_lb, **{'doc': 
                'The angles of all lookback periods up to this one are used',
                'verbose': 'Highest lookback', 
                })),
            ])

    def description(self):
        mode = 'angles of all channels up to {} are'.format(self.repr('lb'))
        flat = ', Flat otherwise.'
        return 'Market type is Up if the {} positive, Down if negative{}'.\
                format(mode, flat)

    def get_trend(self):
        kwargs = {'lb': self.lb, 'mode': 'u'}
        return self.trend('cham', **kwargs)
