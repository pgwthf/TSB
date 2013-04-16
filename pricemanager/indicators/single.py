'''
pricemanager/indicators/single.py v0.1 120906

Created on 120906

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from pyutillib.math_utils import div
from pricemanager.indicators.datedlist import DatedList


def drawdown(dd_list):
    '''
    Returns the highest drawdown in dd_list.
    '''
    max_dd = 1
    high = 0
    for value in dd_list:
        if value > high:
            high = value
        else:
            dd = div(value, high)
            if dd is not None and dd < max_dd:
                max_dd = dd
    return 100. * (1 - max_dd)


def calc_ema(in_list, n_days):
    '''
    Returns a list with the exponential moving average of <in_list>. The return
    list will have the same length, so the first n_days * x items will not be
    accurate.
    '''
    new_mpl = 2 / (n_days + 1)
    prev_mpl = 1 - new_mpl
    ema = []
    ma_list = in_list[:n_days]
    avg = sum(ma_list)/len(ma_list)
    for item in in_list:
        avg = prev_mpl * avg + new_mpl * item
        ema.append(avg)
    return ema


class StockPrice(DatedList):
    '''
    Each instance of this class holds a DatedList of one of (OHLC or Volume)
    with associated indicator methods.
    Indicators in this class operate on *one* price only (e.g. open, close, or
    ma,..)
    '''


    def roc(self, n_days, date=None):
        '''
        Returns the <n_days> Rate Of Change on <date> in percent.
        ROC is defined as the percentage increase between today's close and
        the close <n_days> trading days back.
        If <date> is not specified, a PricesList with the <n_day> roc for each
        day is returned.
        '''
        if not isinstance(n_days, int):
            raise TypeError, 'n_days must be an integer'
        if n_days < 1:
            raise ValueError, 'n_days must be > 0'
        roc = []
        dates = self.dates if date is None else [date]
        for date in dates:
            roc.append(100 * (self[date]/self.offset(date, -n_days) - 1))
        if len(roc) == 1:
            return roc[0]
        else:
            return StockPrice(roc, self.dates)


    def ema(self, n_days, date_=None, cache=True):
        '''
        Returns the <n_days> exponential moving average.
        '''
        if not hasattr(self, '_cache'):
            self._cache = {}
        if n_days not in self._cache:
            if not isinstance(n_days, int):
                raise TypeError, 'n_days must be an integer'
            if n_days < 1:
                raise ValueError, 'n_days must be > 0'
            ema = calc_ema(self, n_days)
            if not cache:
                return StockPrice(ema, self.dates)
            self._cache[n_days] = StockPrice(ema, self.dates)
        if date_:
            return self._cache[n_days][date_]
        else:
            return self._cache[n_days]


    def sma(self, n_days, date_=None):
        '''
        Returns the <n_days> simple moving average on <date>. 
        If <date> is not specified, a PricesList with the <n_days> simple moving
        average is returned.
        '''
        if not hasattr(self, '_cache'):
            self._cache = {}
        if n_days not in self._cache:
            if not isinstance(n_days, int):
                raise TypeError, 'n_days must be an integer'
            if n_days < 1:
                raise ValueError, 'n_days must be > 0'

            sma = []
#            for date in self.dates:
#                ma_list = self[date:-n_days]
#                sma.append(sum(ma_list)/len(ma_list))
#new
            ma_sum = sum(self[:n_days])
            ma = ma_sum / n_days
            for date in self.dates[0:n_days]:
                sma.append(ma)
            for date in self.dates[n_days:]:
                ma_sum = ma_sum + self[date] - self.offset(date, -n_days)
                sma.append(ma_sum/n_days)
            self._cache[n_days] = StockPrice(sma, self.dates)
        if date_:
            return self._cache[n_days][date_]
        else:
            return self._cache[n_days]
#/new
#        if len(sma) == 1:
#            return sma[0]
#        else:
#            return StockPrice(sma, self.dates)


    def drawdown(self, n_days=None, date=None):
        '''
        Returns the highest drawdown over the past <n_days>.
        The drawdown is returned as a percentage, e.g. 20%, if the lowest low
        after a high was 80% of the high.

        If <n_days> is not specified the total time period is considered.
        '''
#CONSIDER: cleverer algorithm should be faster
        if n_days is not None:
            if not isinstance(n_days, int):
                raise TypeError, 'n_days must be an integer'
            if n_days < 0:
                raise ValueError, 'n_days must be > 0'
        dd_list = []
        dates = self.dates if date is None else [date]
        for date in dates:
            dd_list.append(drawdown(self[date:-n_days]))
        if len(dd_list) == 1:
            return dd_list[0]
        else:
            return StockPrice(dd_list, self.dates)


    def monthly_gains(self):
        '''
        Returns the months gain on the last date of each month.
        '''
        maxlen = len(self) - 1
        start_value = self[0]
        gains = []
        dates = []
        for i, (value, date) in enumerate(zip(self, self.dates)):
            if (i == maxlen) or (i == 0) or (
                                date.month != self.dates[i+1].month):
                gains.append(100 * (value / start_value - 1))
                dates.append(date)
                start_value = value
        if len(gains):
            return StockPrice(gains, dates)
