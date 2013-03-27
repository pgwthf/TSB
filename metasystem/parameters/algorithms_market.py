'''
market/algorithms.py v0.1 130218

Created on 130218

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

from pricemanager.indicators.datedlist import DatedList
from channel.models import Channel



def get_market_channel(self, lb):
    '''
    Return 
    EXPECTS UP, DOWN, but products PERCENTAGES!!
    '''
    dates = self.index.price.close.dates
    percentage = []
    for date in dates:
        stock_list = self.get_cached_stocklist(date)
        n_total = len(stock_list)

        if n_total > 0:
            n_pos = sum(1 if s.price.channel.angle(lb)[date] > 0 
                    else 0 for s in stock_list)
            percentage.append(n_pos / n_total)
        else:
            percentage.append(0)
    return DatedList(percentage, dates)
    

#def something(self):
#    for lookback in Channel.LOOKBACKS:
#        self.get_market_channel(lookback)



def cham(self, lb, mode):
    '''
    Return trend that may be UP, FLAT or DOWN, depending on the signs of the
    channel angles up to <lb>
    '''
    angles = []
    length = None
    for lookback in Channel.LOOKBACKS:
        if ((mode == self.ONE) and (lookback == lb)) or (
                (mode == self.UPTO) and (lookback <= lb)) or (
                (mode == self.FROM) and (lookback >= lb)):
#        if lookback <= lb:
            angle = self.pool.index.price.channel.angle(lookback)
            if length is None:
                length = len(angle)
            elif length != len(angle):
                raise ValueError('Angle lists have different lengths')
            angles.append(angle.as_list())
    trends = []
    for a in zip(*angles):
#        print a
        if all(an > 0 for an in a):
            trends.append(self.UP)
        elif all(an < 0 for an in a):
            trends.append(self.DOWN)
        else:
            trends.append(self.FLAT)
#    print len(trends), len(angle.dates)
    return DatedList(trends, angle.dates), None



def chrc(self, lb, th=0.5):
    '''
    Return trend that may be UP or DOWN, depending on whether the rc of the 
    <lb> channel is > or < <th>
    '''
    rc = self.pool.index.price.channel.rc(lb)
    trend = [self.UP if r > th else self.DOWN for r in rc]
    return DatedList(trend, rc.dates), None



def ma2(self, n_ma, hysteresis=0):
    '''
    Return trend that may be UP or DOWN, depending on whether the close is
    higher or lower than the <n_ma> day simple moving average. <hysteresis> is
    specified in %.
    '''
    hysteresis *= 0.01 # turn percentage into fraction
    close = self.pool.index.price.close
    ma = close.sma(n_ma)
    trends = []
    trend = self.DOWN if close[0] < ma[0] else self.UP
    for m, c in zip(ma.as_list(), close.as_list()):
        if c < m * (1 - hysteresis):
            trend = self.DOWN
        elif c > m * (1 + hysteresis):
            trend = self.UP
        trends.append(trend)
    return DatedList(trends, close.dates), None


#def trend_ma3(self, n_ma, th, th_dn=None, hysteresis=0):
#    '''
#    Return trend that may be UP, FLAT or DOWN, depending on the close compared
#    to the <n_ma> day simple moving average. The thresholds <th>, <th_dn> are
#    specified in %, as is  <hysteresis>.
#    '''
#    hysteresis *= 0.01 # turn percentage into fraction
#    th *= 0.01
#    th_dn = -th if th_dn is None else th_dn * 0.01
#    close = self.pool.index.prices.close
#    ma = close.sma(n_ma)
#    trends = []
#    trend = self.DOWN if close[0] < ma[0] * (1 + th_dn) else (self.FLAT if
#            close[0] < ma[0] * (1 + th) else self.UP)
#    for m, c in zip(ma.as_list(), close.as_list()):
#        if trend == self.DOWN:
#            if c < m * (1 + th_dn - hysteresis):
#                trend = self.DOWN
#            elif c <
#            elif c > m * (1 + hysteresis):
#                trend = self.UP
#        trends.append(trend)
#    return DatedList(close.dates, trends), None


def atr2(self, n_atr, hysteresis=0):
    '''
#TODO: enough data??, or store long term average ATR/std_dev in 1900,1,1 ?
    Return volatility that may be LOW or HIGH, depending on the ATR compared
    to its 10 year average (
    '''
    hysteresis *= 0.01
    prices = self.pool.index.prices
    atr = prices.atr(n_atr, as_price=False)
    th = prices.atr(2520, as_price=False) # ON A DATE??
    volatilities = []
    volatility = self.QUIET if atr[0] < th else self.VOLATILE
    for a in atr.as_list():
        if a < th * (1 - hysteresis):
            volatility = self.QUIET
        elif a > th * (1 + hysteresis):
            volatility = self.VOLATILE
        volatilities.append(volatility)
    return None, DatedList(volatilities, prices.close.dates)
