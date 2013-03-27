'''
pricemanager/indicators/multi.py v0.1 120906

Created on 120906

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

from pricemanager.indicators.single import StockPrice, calc_ema

from channel.models import ChannelData

class StockPrices(object):
    '''
    An instance of this class provides price data and indicator values to each
    Stock instance.

    This class then holds OHLC, date and volume objects and methods for 
    calculating indicators.

    Indicators in this class operate on multiple prices, e.g. open *and* close.

    These indicators can be called using:
        stock.price.atr(20) - Returns a PriceList
    or:
        stock.price.atr(20)[date] - Returns the atr value on <date>, but 
                calculates the atr for the entire PriceList first.

    The following is available to every indicator method:
        list of datetime's   self.date
        PriceList of floats  self.open/high/low/close
        PriceList of ints    self.volume
    '''


    def __init__(self, stock):
        self.stock = stock


    @property
    def channel(self):
        if not hasattr(self, '_channel'):
            self._channel = ChannelData(self.stock)
        return self._channel


    def wr(self, n_days, date=None):
        '''
        Return the <n_days> Williams%R indicator. WR values range from 0 to 
        -100.
        '''
        if not isinstance(n_days, int):
            raise TypeError, 'n_days must be an integer'
        if n_days < 1:
            raise ValueError, 'n_days must be > 0'
        wr = []
        dates = self.close.dates if date is None else [date]
        for date in dates:
            high = max(self.high[date:-n_days])
            low = min(self.low[date:-n_days])
            wr.append(-100 * (high - self.close[date]) / (high - low))
        if len(wr) == 1:
            return wr[0]
        else:
            return StockPrice(wr, self.close.dates)


    def atr(self, n_days, date_=None, as_price=True):
        '''
        Returns a StockPrice list with the average true range (ATR) indicator.
        By default the list contains the ATR as a price, set <as_price> to 
        False in order to return a list with the ATR as percentage of the close
        price.
        Because of the EMA this indicator cannot be calculated for a single
        <date_>, the entire list is kept in cache.
NOTE: the cache is a potential risk for memory overflows.
        '''
        if not hasattr(self, '_cache'):
            self._cache = {}
        key = ('ATR', n_days, as_price)
        if key not in self._cache:
            if not isinstance(n_days, int):
                raise TypeError, 'n_days must be an integer'
            if n_days < 1:
                raise ValueError, 'n_days must be > 0'
            tr = []
            for date in self.close.dates:
                yest_close = self.close.offset(date, -1)
                day_range = max(yest_close, self.high[date]) - min(yest_close, 
                                                                self.low[date])
                if not as_price:
                    day_range = day_range / self.close[date]
                tr.append(day_range)
            self._cache[key] = StockPrice(calc_ema(tr, n_days), 
                                                        self.close.dates)
        if date_:
            return self._cache[key][date_]
        else:
            return self._cache[key]


    def dma(self, n_points, mpl=0.5, n_ma=None, date=None):
        '''
        Dynamic Moving Average. Period is based on atr
        Default multiplier (mpl) = 0.5, so we are looking at a range of 1 atr
        (0.5 above, 0.5 below).
        '''
        if not isinstance(n_points, int):
            raise TypeError, 'n_points must be an integer'
        if n_points < 1:
            raise ValueError, 'n_points must be > 0'
        dma = []
        dates = self.close.dates if date is None else [date]
        for startdate in dates:
            startprice = self.close[startdate]
            i_start = self.close.index(startdate)
            i = 0
            for date in self.close.dates[i_start::-1]:
                atr = mpl * self.atr(10)[date]
                if self.low[date] <= startprice - atr:
                    factor = (startprice - self.low[date]) // atr
                    startprice -= factor * atr
                    i += factor
                elif self.high[date] > startprice + atr:
                    factor = (self.high[date] - startprice) // atr
                    startprice += factor * atr
                    i += factor
                if i >= n_points:
                    break
            ma_list = self.close[date:startdate]
            dma.append(sum(ma_list)/len(ma_list))
        if len(dma) == 1:
            return dma[0]
        else:
            if n_ma: #smoothen if desired
                dma = calc_ema(dma, n_ma)
            return StockPrice(dma, self.close.dates)


#    def mc(self, n_ma, n_atr, trend_zones, vol_zones, trend_th, vol_th, 
#            date_=None, **kwargs):
#        '''
#        Returns the market condition, which consists of 2 parameters:
#            trend: up, flat or down
#            volatility: volatile, normal or quiet
#        These parameters can have 2 or 3 values, in case of two, the middle one
#        is dropped.
#        If it is a 3x3, 2x3 or 3x2 matrix there are 2 thresholds for the 3 axis
#            and only one threshold for the 2 axis. In that case the second 
#            value is ignored.
#        If it is a 2x2 matrix, the thresholds are used as follows:
#            * trend th1=th2 and volatility th1=th2: both are considered as a 
#                single threshold.
#            * trend th1=th2 and volatility th1!=th2: v_th1 is used for the DOWN
#                trend and v_th2 is used for the UP trend.
#            * trend th1!=th2 and volatility th1=th2: t_th1 is used for the 
#                QUIET volatility and t_th2 is used for the VOLATILE volatility.
#            * trend th1!=th2 and volatility th1!=th2: illegal
#        '''
#        NORMAL = 1
#        TREND_FIRST = 2
#        VOLATILITY_FIRST = 3
#        if not hasattr(self, '_cache'):
#            self._cache = {}
#        key = ('mc', n_ma, n_atr, trend_zones, vol_zones, trend_th[0], 
#               trend_th[1], vol_th[0], vol_th[1])
#        if key not in self._cache:
#            if (trend_zones == 3 and (trend_th[0] == trend_th[1])) or (
#                    vol_zones == 3 and (vol_th[0] == vol_th[1])):
#                raise ValueError, 'In 3 zones there must be 2 thresholds'
#            order = NORMAL
#            if (trend_zones == 2 and vol_zones == 2):
#                if (trend_th[0] == trend_th[1]) and (vol_th[0] != vol_th[1]):
#                    order = TREND_FIRST
#                elif (trend_th[0] != trend_th[1]) and (vol_th[0] == vol_th[1]):
#                    order = VOLATILITY_FIRST
#                elif (trend_th[0] != trend_th[1]) and (vol_th[0] != vol_th[1]):
#                    raise ValueError('In 2x2 zones at least 1 set of '
#                            'thresholds must be the same')
#            ma = self.close.sma(n_ma)
#            atr = self.atr(n_atr, as_price=False)
#            mc = []
#            for date in self.close.dates:
#                vol_th_ = vol_th[0]
#                if order != VOLATILITY_FIRST :
#                    if self.close[date] < ma[date] * (1 + trend_th[0]):
#                        trend = 'down'
#                    elif trend_zones == 3 and self.close[date] < ma[date] * (
#                            1 + trend_th[1]):
#                        trend = 'flat'
#                    else:
#                        trend = 'up'
#                        if order == TREND_FIRST:
#                            vol_th_ = vol_th[1]
#
#                trend_th_ = trend_th[0]
#                if atr[date] < vol_th_:
#                    volatility = 'quiet'
#                elif vol_zones == 3 and atr[date] < vol_th[1]:
#                    volatility = 'normal'
#                else:
#                    volatility = 'volatile'
#                    if order == VOLATILITY_FIRST:
#                        trend_th_ = trend_th[1]
#
#                if order != TREND_FIRST:
#                    if self.close[date] < ma[date] * (1 + trend_th_):
#                        trend = 'down'
#                    elif trend_zones == 3 and self.close[date] < ma[date] * (
#                            1 + trend_th[1]):
#                        trend = 'flat'
#                    else:
#                        trend = 'up'
#
#                mc.append((trend, volatility))
#            self._cache[key] = StockPrice(mc, self.close.dates)
#        if date_:
#            return self._cache[key][date_]
#        else:
#            return self._cache[key]
