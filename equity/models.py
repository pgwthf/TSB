'''
equity/models.py v0.1 121003

Created on 121003

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

import base64
import math

from django.db import models, transaction

from utils_python.utils import compress, encode, decompress, decode, div

from pricemanager.indicators.single import StockPrice


class Equity(models.Model):
    '''
    This table holds the equity position for each trading day.
    Total equity = cash + positions value
    '''
    system = models.ForeignKey('system.System')
    date = models.DateField()
    cash = models.IntegerField()
    positions = models.IntegerField()

    def total(self):
        return "{}".format(self.cash + self.positions)


class EquityHistory(object):
    '''
    This class maintains the history of equity.

    Equity is a DatedList of cash, stock and total value of the positions. 
    These lists are kept in memory.

    The associated database table holds the equity position for each trading day.
    Total equity = cash + positions value on each date.
    '''

    def __init__(self, startcash=None, system_id=None):
        if startcash:
            self.clear(startcash)
        if system_id:
            self.load(system_id)


    def clear(self, startcash=0):
        '''
        (Re-)Initialise the equity table in memory.
        '''
        self.startcash = startcash
        self.cash = StockPrice([], [])
        self.stocks = StockPrice([], [])
        self.total = StockPrice([], [])


    def percentage(self):
        '''
        Return total equity, scaled so that the starting capital is 100.
        '''
        factor = 100 / self.total[0]
        percentages = [t * factor for t in self.total]
        return StockPrice(percentages, self.total.dates)


    def update(self, date, cashflow, positions_value):
        '''
        Store the equity position on <date> in the DatedLists.
        '''
        try:
            lastcash = self.cash[-1]
        except IndexError:
            lastcash = self.startcash
        cash = lastcash + cashflow
        self.cash.append((date, cash))
        self.stocks.append((date, positions_value))
        self.total.append((date, cash + positions_value))


    def exists(self):
        '''
        Returns True if any equity exists in this instance, False otherwise.
        '''
        return bool(self.total)


    def get(self, period='month'):
        '''
        Returns a list of the equity position on each <period>. Where <period>
        may be one of the following: 'day', 'week', 'month' or 'year'.
        '''
        data = zip(self.stocks.dates, self.stocks.as_list(), self.cash, self.total) 
        start_equity = self.total[0]
        period_start = start_equity
        maxlen = len(self.stocks) - 1
        equity = []
        for i, (date, stocks, cash, total) in enumerate(data):
            total = float(total)
            if (period == 'day') or (i == maxlen) or (i == 0) or ( 
                    period == 'year' and 
                    date.year != self.stocks.dates[i+1].year) or (
                    period == 'month' and  
                    date.month != self.stocks.dates[i+1].month) or (
                    period == 'week' and date.isocalendar()[1] != 
                    self.stocks.dates[i+1].isocalendar()[1]):
                period_equity = {
                        'date': date,
                        'cash': cash,
                        'stocks': stocks,
                        'total': total,
                        'gain':100.*(total/start_equity-1)}
                if period != 'day':
                    period_equity['period_gain'] = 100.*(total/period_start-1)
                equity.append(period_equity)
                period_start = total
        return equity


    def calc_results(self):
        '''
        Returns a dict with:
        * max_dd: The maximum drawdown over a 1 year period.
        * min_dd_ratio: The lowest ratio of gain/max_dd in any one year period.
        * min_month: The lowest gain in any calender month (or highest loss)
        * max_month: The highest gain in any calender month (or lowest loss)
        * neg_month: the average number of negative months per year
        * sum_neg_months: the annualised sum of the losses during those months
        * ann_gain: annualised profit in %
        * min_year: The lowest gain in any 1 year period
        * max_year: The highest gain in any 1 year period
        '''
        year = 252 # avg no of trading days in a year
        data = {'max_dd':0, 'min_dd_ratio': 999.99}
        year_gains = self.total.roc(year)[year-1:]
        if len(year_gains):
            data['min_year'] = min(year_gains)
            data['max_year'] = max(year_gains)
        else:
            data['min_year'] = 0
            data['max_year'] = 0

        year_drawdowns = self.total.drawdown(year)
        for year_dd, year_gain in zip(year_drawdowns, year_gains)[year-1:]:
            dd_ratio = div(year_gain, year_dd) # in %/%
            data['max_dd'] = max(data['max_dd'], year_dd)
            if dd_ratio is not None:
                data['min_dd_ratio'] = min(data['min_dd_ratio'], dd_ratio)

        total_gain = max(0, self.total[-1] / self.total[0])
        dt = self.total.dates[-1] - self.total.dates[0]
        data['ann_profit'] = 100 * (total_gain ** (365./dt.days) - 1)

        months = self.get('month')
        data['min_month'] = min([x['period_gain'] for x in months])
        data['max_month'] = max([x['period_gain'] for x in months])
        neg_months = [x['period_gain'] for x in months if x['period_gain'] < 0]
        data['n_neg_month'] = 12. * len(neg_months) / len(months)
        data['sum_neg_mths'] = 12. * sum(neg_months) / len(months)

        # sanitise results:
        data['max_dd'] = min (data['max_dd'], 99)
        for key in ('ann_profit', 'sum_neg_mths', 'min_year', 'max_year',
                'min_month', 'max_month', 'min_dd_ratio'):
            data[key] = min(max(data[key], -999), 999)
        return data


    def save(self, system):
        '''
        Writes the equity history from the lists to the Equity database table.
        '''
        with transaction.commit_on_success(): # for inserting in bulk (quicker)
            for date, cash, stocks in zip(self.cash.dates, self.cash, self.stocks):
                equity = {'system': system, 'date': date, 
                          'cash':cash, 'positions': stocks}
                Equity.objects.create(**equity)


    def load(self, system_id):
        '''
        Read all equity of <system> from the database.
        '''
        equity = Equity.objects.filter(system=system_id).order_by('date')
        dates = []
        cash = []
        stocks = []
        totals = []
        for row in equity:
            dates.append(row.date)
            cash.append(row.cash)
            stocks.append(row.positions)
            totals.append(row.cash + row.positions)
        self.cash = StockPrice(cash, dates)
        self.stocks = StockPrice(stocks, dates)
        self.total = StockPrice(totals, dates)


    def write_thumbnail_to_db(self, system, width=100, height=32):
        '''
        Calculate and store the y coordinates for generating a thumbnail image.
        '''
        totals = self.total.as_list()
        Thumbnail.write_to_db(totals, system, width, height)



class Thumbnail(models.Model):
    '''
    This class stores a thumbnail image of the equity chart in a compressed
    format.

    This format is a string of bytes where each byte represents the equity 
    position in the total period/width. This byte is split in its first 5
    bits and its last 3 bits. The first 5 bits represent the y coordinate 
    (in pixels) of the lowest equity position during its period and the last
    3 bits represent the height (thickness in pixels) of the line (i.e. the 
    distance from the lowest to the highest equity position in its period.

    The first 5 bytes have a special meaning:
    byte 0: (height, 1)
    byte 1: (y location of the starting equity, 1)
    byte 2: (y location of half the starting equity, q)
    byte 3: (y location of double the starting equity, q)
    byte 4 to <width>+4: (y, thickness)
    Where q indicates if the location exists (1 = yes, 2 = no).
    '''
    id = models.ForeignKey('system.System', primary_key=True)
    _data = models.TextField(db_column='data', blank=True)

    def set_data(self, data):
        self._data = base64.encodestring(data)

    def get_data(self):
        return base64.decodestring(self._data)

    data = property(get_data, set_data)

    @classmethod
    def write_to_db(cls, data, system, width=100, height=32):
        '''
        Takes the equity data and saves it in the database as a string of 
        bytes.
        '''
        height = min(height, 32)
        height0 = height - 1
        n_tot = len(data)
        low = math.log(max(0.1, min(data)))
        high = math.log(max(data))
        if high == low:
            high = high * 1.1
            low = low * 0.9
        y_factor = float(height0)/(high-low)
        # y0 = y location of the starting equity, y1=50%, y2=100%
        y0 = height0 - int(y_factor * (math.log(data[0])-low))
        y1tuple = (height0 - int(y_factor * (math.log(data[0]/2)-low)), 1)
        if y1tuple[0] > 0:
            y1tuple = (0,0)
        y2tuple = (height0 - int(y_factor * (math.log(data[0]*2)-low)), 1)
        if y2tuple[0] < height0:
            y2tuple = (height0,0)
        coords = [(height0,1), (y0,1), y1tuple, y2tuple]
        one_pixel = n_tot // width
        for x in xrange(width):
            x_start = (n_tot * x) // width
            if not one_pixel: # there is less data than thumbnail width
                y_min = y_max = math.log(data[x_start])
            else:
                x_range = data[x_start:x_start+one_pixel]
        #            if len(x_range):
                y_min = math.log(max(0.1, min(x_range)))
                y_max = math.log(max(0.1, max(x_range)))
        #            else:
        #                y_min = low
        #                y_max = high
            y1 = height0 - int(y_factor * (y_min-low))
            y2 = height0 - int(y_factor * (y_max-low))
            dy = min(y1 - y2, 7)
            coords.append((y2, dy))
        record = cls(id=system)
        record.data = encode(compress(coords))
        record.save()

    @classmethod
    def read(cls, system_id):
        '''
        Reads and processes the tumbnail data and returns it in a useaable
        format.
        '''
        data = Thumbnail.objects.get(id=system_id).data
        data = decompress(decode(data))
        height = data.pop(0)[0] + 1
        y0 = data.pop(0)[0]
        y1tuple = data.pop(0)
        y2tuple = data.pop(0)
        width = len(data)
        return (width, height, y0, y1tuple, y2tuple, data)
