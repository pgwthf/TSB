'''
market/models.py v0.1 130218

Created on 130218

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import


import market.algorithms


class MarketType(object):
    '''
    An instance of this class provides market type data for each Pool instance.
    Market type consists of 2 parameters: volatility and trend, both have
    3 possible values:
        trend: down, flat, up
        volatility: low, medium, high
    Trend and volatility may be calculated with the same algorithm or different
    ones.

    '''
    UP = 3
    FLAT = 2
    DOWN = 1
    TREND_VALUES = (UP, FLAT, DOWN)
    HIGH = 3
    NORMAL = 2
    LOW = 1
    VOLATILITY_VALUES = (HIGH, NORMAL, LOW)

    def __init__(self, pool):
        self._trend = {}
        self._volatility = {}
        self.pool = pool


    def trend(self, algorithm):
        '''
        Return a DatedList with trend values.
        '''
        if algorithm not in self._trend:
#            self._load_data(algorithm)
#FIXME: does this work:
            startdate, enddate = self.pool.index.price_date_range

            trend, volatility = getattr(market.algorithms, algorithm)
            if trend is None:
                raise AttributeError('Algorithm {} did not return trend data'\
                        .format(algorithm))
            else:
                self._trend[algorithm] = trend
            if volatility is not None:
                self._volatility[algorithm] = volatility
        return self._trend[algorithm]


    def volatility(self, algorithm):
        '''
        Return a DatedList with volatility values.
        '''
        if algorithm not in self._volatility:

            trend, volatility = getattr(market.algorithms, algorithm)
            if volatility is None:
                raise AttributeError('Algorithm {} did not return volatility '\
                        'data'.format(algorithm))
            else:
                self._volatility[algorithm] = volatility
            if trend is not None:
                self._trend[algorithm] = trend
        return self._volatility[algorithm]

