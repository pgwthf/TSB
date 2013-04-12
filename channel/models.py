'''
channel/models.py v0.1 130118

Created on 130118

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import math

from django.db import models, transaction
from django.db.models import Max, Min

from utils_python.utils import div
from pricemanager.indicators.datedlist import DatedList



class ChannelPriceManager(models.Manager):
    '''
    This manager provides the close price in an extra field
    '''
    def get_query_set(self):
        return super(ChannelPriceManager, self).get_query_set().extra(select={
                    'close': 'select close from pricemanager_price where '\
                    'stock_id=channel_channel.stock_id and '\
                    'date=channel_channel.date'},)


class Channel(models.Model):
    '''
    Channel data - so it only needs calculation once
        angle  - angle of the lower trend line in % increase per day
        width  - (vertical) width of the channel in %
        origin - point where lower channel line intersects <date> (today) as
                    a price
    '''
    YEAR = 252
    SIXMONTHS = 126
    QUARTER = 63
    TWOMONTHS = 42
    SIXWEEKS = 31
    MONTH = 21
    LOOKBACKS = (YEAR, SIXMONTHS, QUARTER, TWOMONTHS, SIXWEEKS, MONTH)
    LOOKBACK_CHOICES = (
            (YEAR, '1 year'),
            (SIXMONTHS, '6 months'),
            (QUARTER, '1 quarter'),
            (TWOMONTHS, '2 months'),
            (SIXWEEKS, '6 weeks'),
            (MONTH, '1 month'))

    stock = models.ForeignKey('pricemanager.Stock')
    date = models.DateField()
    lookback = models.PositiveSmallIntegerField(choices=LOOKBACK_CHOICES)
    angle = models.FloatField()
    width = models.FloatField()
    bottom = models.DecimalField(max_digits=6, decimal_places=2)

    objects = models.Manager()
    with_close = ChannelPriceManager()

    @classmethod
    def calculate_latest(cls, stocklist):
        '''
        Calculate the latest channel data for every stock in <stocklist> and
        save the results to the table.
        '''
        for stock in stocklist:
            date = stock.get_latest_date()
            stock.date_range = (date, date)
            data = []
            for lookback in cls.LOOKBACKS:
                if len(stock.price.close) <= lookback:
                    print('skipping {} {} days'.format(stock.name, lookback))
                    continue
                else:
                    print stock.name, lookback
                width, angle, bottom = channel(
                        stock.price.low[date:-lookback], 
                        stock.price.high[date:-lookback])
                data.append({'stock': stock, 'date': date, 'lookback': lookback,
                        'angle': angle, 'width': width, 'bottom': bottom})
            print 'Writing {} channels to DB...'.format(stock.name)
            cls._insert_data(data)
            print 'Written'
        print 'All channels done'


    @classmethod
    def calculate(cls, stock, startdate=None, enddate=None):
        '''
        Calculate channels for a stock in the specified date range and save the
        results to the channels table. If start and enddate are not specified, 
        all channel data is calculated.
        '''
        if startdate is None and enddate is None:
            # Calculate channel parameters for ALL available price data, note
            # that stock.date_range *should* not be set!
            unused, enddate = stock.price_date_range
        elif startdate is not None and enddate is not None:
            stock.date_range = (startdate, enddate)
        else:
            raise ValueError('startdate and enddate must both have a value or '\
                    'both be None')
        data = []
        for lookback in cls.LOOKBACKS:
            if len(stock.price.close) <= lookback:
                continue
            if startdate is None:
                # start every lookback calculation at the earliest possible time
                stock.date_range = (stock.price.close.dates[lookback], enddate)
            result = calc_channel(stock, lookback)
            for date in result['angle'].dates:
                data.append({'stock': stock, 'date': date, 'lookback': lookback,
                        'angle': result['angle'][date],
                        'width': result['width'][date],
                        'bottom': result['bottom'][date]})
        print 'Writing {} channels to DB...'.format(stock.name)
        cls._insert_data(data)
        print 'Written'


    @classmethod
    def _insert_data(cls, data):
        '''
        Insert multiple channel records into the table at once.

        <data> is a list of dicts with a key for each <Channel> field.
        If a channel record already exists the values will silently be 
        overwritten.
        '''
        with transaction.commit_on_success():
            for row in data:
                cls.objects.get_or_create(stock=row.pop('stock'), 
                date=row.pop('date'), lookback=row.pop('lookback'),
                defaults=row)


    @classmethod
    def get_startdate(cls, stock):
        '''
        Return the lowest date for <stock>
        '''
        qs = Channel.objects.filter(stock=stock).aggregate(Min('date'))
        return qs['date__min']


    @classmethod
    def get_enddate(cls, stock):
        '''
        Return the highest date for <stock>
        '''
        qs = Channel.objects.filter(stock=stock).aggregate(Max('date'))
        return qs['date__max']


    def stoploss(self, close=None):
        if close is None:
            close = self.stock.get_close(self.date)
        else:
            close = float(close)
        return 100 * (1 - float(self.bottom) / close)


    def top(self, close=None):
#TODO: should return decimal
        return float(self.bottom) * (self.width / 100 + 1)


    def rc(self, close=None):
        if close is None:
            close = self.stock.get_close(self.date)
        else:
            close = float(close)
        bottom = float(self.bottom)
        return (close - bottom) / (self.top(close) - bottom)


    def quality(self):
        return self.angle / self.width

    class Meta:
        ordering = ['stock', 'date', 'lookback']
        unique_together = (('stock', 'date', 'lookback'),)


    def __unicode__(self):
        return '{}, {}, {}, {:3.2f}'.format(self.stock, self.date, 
                self.lookback, self.angle)



class ChannelData(object):
    '''
    This class provides an interface to channel data from the database. It is 
    not used for calculating channels.
    If no channel data is available in the database, it is calculated 
    automatically (but not stored in the database).
    '''

    def __init__(self, stock):
        self._data = {}
        self.stock = stock


    @staticmethod
    def pool_market(pool, lookback):
        
        
        dates = pool.index.price.close.dates
        percentage = []
        for date in dates:
            stock_list = pool.get_cached_stocklist(date)
            n_total = len(stock_list)
    
            if n_total > 0:
                n_pos = sum(1 if s.price.channel.angle(lookback)[date] > 0 
                        else 0 for s in stock_list)
                percentage.append(n_pos / n_total)
            else:
                percentage.append(0)
        return DatedList(percentage, dates)


    def sumangle(self):
        '''
        Return a DatedList with the sum of all balanced angles
        Angles are balanced by multiplying them with lookback/100
#NOTE: 21 and 42 are set to 0 for now
#CONSIDER: add 15 as lowest channel (and delete 21/42?)
        '''
        if 'sumangle' not in self._data:
#            for lookback in Channel.LOOKBACKS:
            data = [(0*a*Channel.MONTH + b*Channel.SIXWEEKS + 
                    0*c*Channel.TWOMONTHS
                    + d*Channel.QUARTER + e*Channel.SIXMONTHS + f*Channel.YEAR)
                    /100 for a,b,c,d,e,f in zip(
                    self.angle(Channel.MONTH).as_list(), 
                    self.angle(Channel.SIXWEEKS).as_list(), 
                    self.angle(Channel.TWOMONTHS).as_list(), 
                    self.angle(Channel.QUARTER).as_list(), 
                    self.angle(Channel.SIXMONTHS).as_list(), 
                    self.angle(Channel.YEAR).as_list())]
            self._data['sumangle'] = DatedList(data, 
                    self.angle(Channel.YEAR).dates)
        return self._data['sumangle']


    def sumwidth(self):
        '''
        Return a DatedList with the sum of all balanced widths
        Widths are balanced by multiplying them with 10/sqrt(lookback)
#NOTE: 21 and 42 are set to 0 for now
        '''
        srY = Channel.YEAR ** -0.5
        srSM = Channel.SIXMONTHS ** -0.5
        srQ = Channel.QUARTER ** -0.5
        srTM = Channel.TWOMONTHS ** -0.5
        srSW = Channel.SIXWEEKS ** -0.5
        srM = Channel.MONTH ** -0.5
        if 'sumwidth' not in self._data:
            data = [(0*a*srM + b*srSW + 0*c*srTM + d*srQ + e*srSM + f*srY)*10
                    for a,b,c,d,e,f in zip(
                    self.width(Channel.MONTH).as_list(), 
                    self.width(Channel.SIXWEEKS).as_list(), 
                    self.width(Channel.TWOMONTHS).as_list(), 
                    self.width(Channel.QUARTER).as_list(), 
                    self.width(Channel.SIXMONTHS).as_list(), 
                    self.width(Channel.YEAR).as_list())]
            self._data['sumwidth'] = DatedList(data, 
                    self.angle(Channel.YEAR).dates)
        return self._data['sumwidth']


    def angle(self, lookback):
        '''
        Return a DatedList with angles for <lookback> days.
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        return self._data[lookback]['angle']


    def angle_n(self, lookback):
        '''
        Return a DatedList with the normalised channel angle. This is the angle
        multiplied by (lookback / lb_1year)
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        if 'angle_n' not in self._data[lookback]:
            factor = lookback / Channel.YEAR
            data = [a * factor for a in self.angle(lookback).as_list()]
            self._data[lookback]['angle_n'] = DatedList(data, 
                    self.angle(lookback).dates)
        return self._data[lookback]['angle_n']


    def angle_max(self):
        '''
        Return a DatedList with the highest normalised channel angle.
        '''
        if 'angle_max' not in self._data:
            data = [max(angles) for angles in zip(
                    self.angle_n(Channel.MONTH).as_list(), 
                    self.angle_n(Channel.SIXWEEKS).as_list(), 
                    self.angle_n(Channel.TWOMONTHS).as_list(), 
                    self.angle_n(Channel.QUARTER).as_list(), 
                    self.angle_n(Channel.SIXMONTHS).as_list(), 
                    self.angle_n(Channel.YEAR).as_list())]
            self._data['angle_max'] = DatedList(data, 
                    self.angle(Channel.MONTH).dates)
        return self._data['angle_max']


    def angle_min(self):
        '''
        Return a DatedList with the lowest normalised channel angle.
        '''
        if 'angle_min' not in self._data:
            data = [min(angles) for angles in zip(
                    self.angle_n(Channel.MONTH).as_list(), 
                    self.angle_n(Channel.SIXWEEKS).as_list(), 
                    self.angle_n(Channel.TWOMONTHS).as_list(), 
                    self.angle_n(Channel.QUARTER).as_list(), 
                    self.angle_n(Channel.SIXMONTHS).as_list(), 
                    self.angle_n(Channel.YEAR).as_list())]
            self._data['angle_min'] = DatedList(data, 
                    self.angle(Channel.MONTH).dates)
        return self._data['angle_min']


    def width(self, lookback):
        '''
        Return a DatedList with widths for <lookback> days.
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        return self._data[lookback]['width']


    def width_n(self, lookback):
        '''
        Return a DatedList with the normalised channel width. This is the width
        multiplied by sqrt(lb_1year / lookback)
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        if 'width_n' not in self._data[lookback]:
            factor = (Channel.YEAR / lookback) ** 0.5
            data = [w * factor for w in self.width(lookback).as_list()]
            self._data[lookback]['width_n'] = DatedList(data, 
                    self.width(lookback).dates)
        return self._data[lookback]['width_n']


    def width_min(self):
        '''
        Return a DatedList with the lowest normalised channel width.
        '''
        if 'width_min' not in self._data:
            data = [min(widths) for widths in zip(
                    self.width_n(Channel.MONTH).as_list(), 
                    self.width_n(Channel.SIXWEEKS).as_list(), 
                    self.width_n(Channel.TWOMONTHS).as_list(), 
                    self.width_n(Channel.QUARTER).as_list(), 
                    self.width_n(Channel.SIXMONTHS).as_list(), 
                    self.width_n(Channel.YEAR).as_list())]
            self._data['width_min'] = DatedList(data, 
                    self.width(Channel.MONTH).dates)
        return self._data['width_min']


    def width_max(self):
        '''
        Return a DatedList with the lowest normalised channel width.
        '''
        if 'width_max' not in self._data:
            data = [max(widths) for widths in zip(
                    self.width_n(Channel.MONTH).as_list(), 
                    self.width_n(Channel.SIXWEEKS).as_list(), 
                    self.width_n(Channel.TWOMONTHS).as_list(), 
                    self.width_n(Channel.QUARTER).as_list(), 
                    self.width_n(Channel.SIXMONTHS).as_list(), 
                    self.width_n(Channel.YEAR).as_list())]
            self._data['width_max'] = DatedList(data, 
                    self.width(Channel.MONTH).dates)
        return self._data['width_max']


    def bottom(self, lookback):
        '''
        Return a DatedList with the bottom channel line for <lookback> days.
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        return self._data[lookback]['bottom']


    def top(self, lookback):
        '''
        Return a DatedList with the top channel position
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        if 'top' not in self._data[lookback]:
            data = [o * (1 + 0.01*w) for o, w in zip(self.bottom(
                    lookback).as_list(), self.width(lookback).as_list())]
            self._data[lookback]['top'] = DatedList(data, 
                    self.bottom(lookback).dates)
        return self._data[lookback]['top']


    def quality(self, lookback):
        '''
        Return a DatedList with the channel quality for <lookback> days.
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        if 'quality' not in self._data[lookback]:
            data = [div(a, w) for a, w in zip(self.angle(lookback).as_list(), 
                    self.width(lookback).as_list())]
            self._data[lookback]['quality'] = DatedList(data, 
                    self.angle(lookback).dates)
        return self._data[lookback]['quality']


    def quality_n(self, lookback):
        '''
        Return a DatedList with the normalised channel quality for <lookback> 
        days.
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        if 'quality_n' not in self._data[lookback]:
            data = [div(a, w) for a, w in zip(self.angle_n(lookback).as_list(), 
                    self.width_n(lookback).as_list())]
            self._data[lookback]['quality_n'] = DatedList(data, 
                    self.angle(lookback).dates)
        return self._data[lookback]['quality_n']


    def stoploss(self, lookback, date, date_entry=None):
        '''
THIS IS OBSOLETE, ONLY USE stoptop or stopbottom
        '''
        if date_entry is None:
            date_signal = date
            n_days = 1
        else:
            date_signal = self.stock.price.close.get_date(date_entry, -1)
            n_days = self.stock.price.close.delta(date_signal, date) + 1
        angle = self.angle(lookback)[date_signal]
        bottom = self.bottom(lookback)[date_signal]
        return bottom * (1 + 0.01 * angle) ** (n_days/252)


    def _stop(self, lookback, date, date_entry=None, mode='top'):
        '''
        Return the stoploss for the next trading day, based on the top or bottom
        line of the <lookback> channel.

        <lookback> is the lookback period for the channel indicator in days
        <date_signal> is the date for which the angle and price data will be
        used <date> is the date on which the signal is generated (i.e. the stop
        is for the next trading day after <date>
        <date_entry> is the entry date, which is the day after the signal date,
        if the entry date is not specified, the signal date is today (=<date>)
        and the entry date will (may) be tomorrow.
        '''
        if date_entry is None:
            date_signal = date
            n_days = 1
        else:
            date_signal = self.stock.price.close.get_date(date_entry, -1)
            n_days = self.stock.price.close.delta(date_signal, date) + 1
        angle = self.angle(lookback)[date_signal]
        line = getattr(self, mode)(lookback)[date_signal]
        return line * (1 + 0.01 * angle) ** (n_days/252)


    def stoptop(self, lookback, date, date_entry=None):
        '''
        Return the stoploss for the next trading day, based on the top line of
        the <lookback> channel.
        '''
        return self._stop(lookback, date, date_entry, mode='top')
#
#        if date_entry is None:
#            date_signal = date
#            n_days = 1
#        else:
#            date_signal = self.stock.price.close.get_date(date_entry, -1)
#            n_days = self.stock.price.close.delta(date_signal, date) + 1
#        angle = self.angle(lookback)[date_signal]
#        top = self.top(lookback)[date_signal]
#        return top * (1 + 0.01 * angle) ** (n_days/252)


    def stopbottom(self, lookback, date, date_entry=None):
        '''
        Return the stoploss for the next trading day, based on the bottom line
        of the <lookback> channel.
        '''
        return self._stop(lookback, date, date_entry, mode='bottom')
#
#        if date_entry is None:
#            date_signal = date
#            n_days = 1
#        else:
#            date_signal = self.stock.price.close.get_date(date_entry, -1)
#            n_days = self.stock.price.close.delta(date_signal, date) + 1
#        angle = self.angle(lookback)[date_signal]
#        bottom = self.bottom(lookback)[date_signal]
#        return bottom * (1 + 0.01 * angle) ** (n_days/252)


    def rc(self, lookback):
        '''
        Return a the relative channel indicator for <lookback> period. This is
        a DatedList with the relative channel position between bottom and top.
        '''
        if lookback not in self._data:
            self._load_data(lookback)
        if 'rc' not in self._data[lookback]:
            dates = self.angle(lookback).dates
            close_prices = self.stock.price.close[dates[0]:dates[-1]]
            if len(close_prices) != len(self.angle(lookback)):
                print self.stock.missing_channels()
                raise ValueError('prices are not same length as channels: {} != {}'\
                        .format(len(close_prices), len(self.angle(lookback))))
            rc = [max(0, min(1, (c - o) / (t - o))) for c, o, t in zip(close_prices,
                    self.bottom(lookback).as_list(), self.top(lookback).as_list())]
            self._data[lookback]['rc'] = DatedList(rc, 
                    self.bottom(lookback).dates)
        return self._data[lookback]['rc']

#        dates = self.angle(lookback).dates
#        close_prices = self.stock.price.close[dates[0]:dates[-1]]
#        if len(close_prices) != len(self.angle(lookback)):
#            print self.stock.missing_channels()
#            raise ValueError('prices are not same length as channels: {} != {}'\
#                    .format(len(close_prices), len(self.angle(lookback))))
#        rc = [max(0, min(1, (c - o) / (t - o))) for c, o, t in zip(close_prices,
#                self.bottom(lookback).as_list(), self.top(lookback).as_list())]
#        return DatedList(rc, dates)


    def _load_data(self, lookback):
        '''
        Load channel data from the database and store it in DatedList objects.
        Note that StockPrice objects are not used, because the indicator 
        functionality is not necessary (for now).
        '''
        startdate, enddate = self.stock.date_range
        self._data[lookback] = {}
        qs = Channel.objects.filter(stock=self.stock, date__gte=startdate,
                lookback=lookback, date__lte=enddate).order_by('date')
        qs = None
        if qs:
            # Retrieve the channel information from the database
            dates = [s.date for s in qs]
            for field in ('angle', 'width', 'bottom'):
                data = [float(getattr(s, field)) for s in qs]
                self._data[lookback][field] = DatedList(data, dates)
        else:
            # Channel information does not exist in the database, calculate it
            data = calc_channel(self.stock, lookback)
            for field in ('angle', 'width', 'bottom'):
                self._data[lookback][field] = data[field]


# the following functions are only used for calculating channels

#TODO: check algorithm for behaviour with min/max at 1st or last data point

def calc_channel(stock, lookback):
    '''
    Returns a dict with a DatedLists for the channel parameters: angle, width
    and bottom for <lookback> period. The parameters are calculated from the
    available price data for this stock as set by the date_range.
    '''
    angles = []
    widths = []
    bottoms = []
    dates = stock.price.close.get_dates(*stock.date_range)
    for date in dates:
        width, angle, bottom = channel(stock.price.low[date:-lookback], 
                stock.price.high[date:-lookback])
        angles.append(angle)
        widths.append(width)
        bottoms.append(bottom)
    return {'angle': DatedList(angles, dates), 
            'width': DatedList(widths, dates), 
            'bottom': DatedList(bottoms, dates)}


def get_width(lows, highs, index_lo, index_hi, alpha):
    '''
    Returns the width of the channel that is defined by:
        alpha - the angle of the channel
        hi - the highest high for alpha, i.e. a point on the high line
        lo - the lowest low for alpha, i.e. a point on the low line
        i_h - the index of hi
        i_l - the index of lo
    This function works for any alpha.
    '''
    return highs[index_hi] - lows[index_lo] - (index_hi - index_lo) * alpha


def get_alpha_left(values, i_pivot):
    '''
    Returns a list with the angles of the polar coordinates of each point in
    <values> using <i_pivot> as the origin. Only points to the left of the
    pivot are calculated
    '''
    val_pivot = values[i_pivot]
    return ((val_pivot - val) / (i_pivot - i) for i, val in enumerate(
            values[:i_pivot]))


def get_alpha_right(values, i_pivot):
    '''
    Returns a list with the angles of the polar coordinates of each point in
    <values> using <i_pivot> as the origin. Only points to the right of the
    pivot are calculated
    '''
    val_pivot = values[i_pivot]
    return ((val - val_pivot) / (i + 1) for i, val in enumerate(
            values[i_pivot + 1:]))


def get_alpha_highs_up(values, i_pivot):
    '''
    Return the angle that the cloud of <values> needs to be rotated by for the
    next point in the cloud *left* of the pivot to be on the x-axis. The cloud
    is rotated clockwise.
    '''
    return min(get_alpha_left(values, i_pivot))


def get_alpha_lows_down(values, i_pivot):
    '''
    Return the angle that the cloud of <values> needs to be rotated by for the
    next point in the cloud *left* of the pivot to be on the x-axis. The cloud
    is rotated counter clockwise.
    '''
    return max(get_alpha_left(values, i_pivot))


def get_alpha_lows_up(values, i_pivot):
    '''
    Return the angle that the cloud of <values> needs to be rotated by for the
    next point in the cloud *right* of the pivot to be on the x-axis. The cloud
    is rotated clockwise.
    '''
    return min(get_alpha_right(values, i_pivot))


def get_alpha_highs_down(values, i_pivot):
    '''
    Return the angle that the cloud of <values> needs to be rotated by for the
    next point in the cloud *right* of the pivot to be on the x-axis. The cloud
    is rotated counter clockwise.
    '''
    return max(get_alpha_right(values, i_pivot))


def rotate_list(values, angle, i_pivot=0):
    '''
    A positive angle rotates the cloud of points clockwise (so the line rotates
    counter clockwise = up).
    '''
    return [val + (i_pivot - i) * angle for i, val in enumerate(values)]


def get_indices(values, value):
    '''
    Return a list with the indices of all occurences of <value> in <values>
    '''
    return [i for i, val in enumerate(values) if abs(val - value) < 1e-6]
#    return [i for i, val in enumerate(values) if val == value]


def get_maxlist(values):
    '''
    Return a list with the indices of all maximum <values>.
    '''
    return get_indices(values, max(values))


def get_minlist(values):
    '''
    Return a list with the indices of all minimum <values>.
    '''
    return get_indices(values, min(values))


def get_channel(lows, highs, low_angle, high_angle, current_angle):
    '''
    Recursive function that returns the raw channel parameters: angle, width 
    and bottom. Because the <lows>, <highs> lists are logarithmic, so are the
    channel parameters.
    '''
    low_indices = get_minlist(rotate_list(lows, current_angle))
    high_indices = get_maxlist(rotate_list(highs, current_angle))
    if high_indices[0] > low_indices[-1]:
        # rotate up
        if low_angle < high_angle:
            angle = low_angle
            low_angle = get_alpha_lows_up(lows, low_indices[-1])
        elif low_angle > high_angle:
            angle = high_angle
            high_angle = get_alpha_highs_up(highs, high_indices[0])
        else: # they are equal, refresh both
            angle = low_angle
            low_angle = get_alpha_lows_up(lows, low_indices[-1])
            high_angle = get_alpha_highs_up(highs, high_indices[0])
    elif high_indices[-1] < low_indices[0]:
        # rotate down
        if low_angle > high_angle: # because the angle is negative
            angle = low_angle
            low_angle = get_alpha_lows_down(lows, low_indices[0])
        elif low_angle < high_angle:
            angle = high_angle
            high_angle = get_alpha_highs_down(highs, high_indices[-1])
        else: # they are equal, refresh both
            angle = low_angle
            low_angle = get_alpha_lows_down(lows, low_indices[0])
            high_angle = get_alpha_highs_down(highs, high_indices[-1])
    else: 
        # angle found
        index_low = low_indices[0]
        index_high = high_indices[0]
        width = get_width(lows, highs, index_low, index_high, current_angle)
        bottom = lows[index_low] + current_angle * (len(lows) - (index_low + 1))
        return (current_angle, width, bottom)
    return get_channel(lows, highs, low_angle, high_angle, angle)


def channel(lows, highs):
    '''
    Returns the smallest width and corresponding angle of the price data in 
    <lows> and <highs> 
    '''
    year = 252 # Average number of trading days per year

    lows = [math.log10(l) for l in lows]
    highs = [math.log10(h) for h in highs]
    a, w, b = get_channel(lows, highs, 0, 0, 0)
    angle = 10 ** a
    width = 10 ** w
    bottom = 10 ** b

#    print width, angle, origin
    width = 100 * (width - 1)
    angle = 100 * (angle ** year - 1)
    return width, angle, bottom
