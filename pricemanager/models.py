'''
pricemanager/models.py v0.1 120815

Created on 120618

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

import datetime, time
from operator import itemgetter
from collections import defaultdict

from django.db import models
from django.db import transaction
from django.db.models import Max, Min


from pricemanager.yahoo import download_today, download_history

from TSB.utils import notify_admin
from utils_python.utils import previous_weekday, last_year, random_string

from pricemanager.indicators.multi import StockPrices
from pricemanager.indicators.single import StockPrice

from chart.models import Chart

from channel.models import Channel

#from market.models import MarketType


class Stock(models.Model):
    '''
    The Stock table is for stocks as well as indices. Set <name> to the symbol
    and <description> to the full name of the company/index/ETF.
    Set startdate to indicate since when this stock has existed.
    Set enddate to indicate until when this stock existed.
    '''
    AUSTRALIAN_DOLLAR = 'AUD'
    EURO = 'EUR'
    US_DOLLAR = 'USD'
    BRITISH_POUND = 'GBP'
    CURRENCIES = (
        (AUSTRALIAN_DOLLAR, 'Australian dollar'),
        (EURO, 'Euro'),
        (US_DOLLAR, 'US dollar'),
        (BRITISH_POUND, 'British pound'),
    )
    name = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=50, blank=True)
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCIES, 
                                                            default=US_DOLLAR)


    @property
    def global_date_range(self):
        '''
        Returns the class setting for the date range, this is only used if no
        date range is defined for a class instance.
        Don't use this method directly, the value will autmatically be defaulted
        to when <stock.date_range> is called.
        '''
        if hasattr(Stock, '_date_range'):
            return (Stock._date_range[1], Stock._date_range[2])
        else:
            return None
    @global_date_range.setter
    def global_date_range(self, (startdate, enddate)):
        '''
        Set a default date range for all stocks, this will only be used if no
        date range is defined for a stock.
        '''
        Stock._date_range = (last_year(startdate) - datetime.timedelta(days=10),
                startdate, enddate)

    @property
    def date_range(self):
        '''
        Returns a tuple with 2 datetime objects (startdate, enddate) that
        specifies the date range for usage/output, e.g. plotting, calculations, 
        etc. Generally an earlier startdate is required for prices, that date
        is obtained through price_start_range.
        '''
        if hasattr(self, '_date_range'):
            return (self._date_range[1], self._date_range[2])
        else:
            # Should this be valid?
            raise AttributeError('Date range for data was not specified')
#TODO: delete this if above is OK
            return (self.get_earliest_date(), self.get_latest_date())
    @date_range.setter
    def date_range(self, (startdate, enddate)):
        '''
        The date range for USING the data is specified, so the startdate for
        prices must be a year earlier for channels and other indicators to work.
        '''
        self._date_range = (last_year(startdate) - datetime.timedelta(days=10),
                startdate, enddate)

    def has_date_range(self):
        '''
        Returns True if a date range has been defined
        '''
        return hasattr(self, '_date_range')


    @property
    def price_date_range(self):
        '''
        Returns a tuple with 2 datetime objects (startdate, enddate) that
        specifies the date range for price data.
        '''
        if hasattr(self, '_date_range'):
            return (self._date_range[0], self._date_range[2])
        else:
            print 'WARNING: ALL price data is used for {}'.format(self.name)
            return (self.get_earliest_date(), self.get_latest_date())
    @price_date_range.setter
    def price_date_range(self, (startdate, enddate)):
        '''
        Format of the self._date_range tuple is:
            (startdate for price, startdate for *use*, enddate)
        '''
        self._date_range = (startdate, None, enddate)


    @property
    def price(self):
        '''
        If price is called, first check if they are in memory yet.
        The date range is set in the class: Stock.date_range. If that is not
        set, the entire available date range in the database is used.
        '''
        if not hasattr(self, '_price'):
            startdate, enddate = self.price_date_range
            self._price = StockPrices(self)
            qs = Price.objects.filter(stock=self, date__gte=startdate, 
                    date__lte=enddate).order_by('date')
            dates = [s.date for s in qs]
            for column in ['open', 'high', 'low', 'close', 'volume']:
                if column == 'volume':
                    data = [getattr(s, column) for s in qs]
                else:
                    data = [float(getattr(s, column)) for s in qs]
                setattr(self._price, column, StockPrice(data, dates))
        return self._price


    def chart(self, *args, **kwargs):
        '''
        Add a charting class to this stock instance. Pass all arguments EXCEPT
        for prices!
        '''
        if not hasattr(self, '_chart'):
            self._chart = Chart(self, *args, **kwargs)
        return self._chart


    def download_history(self, startdate, enddate):
        '''
        Download prices for the current stock from <startdate> to <enddate>.
        '''
        data = download_history(self, startdate, enddate)
        if data:
            Price.insert_prices(data)


    def get_earliest_date(self):
        '''
        Returns the latest date for which this stock has prices in the database
        '''
        return Price.get_startdate(self)


    def get_latest_date(self):
        '''
        Returns the latest date for which this stock has prices in the database
        '''
        return Price.get_enddate(self)


    def is_current(self, date):
        '''
        Returns True if <date> is inside the stock's date range.
        '''
        return (self.enddate is None or date <= self.enddate) and (
                            self.startdate is None or date >= self.startdate)


#    def has_prices(self, startdate, enddate):
#        '''
#        Checks if all prices for stock exist between <startdate> and <enddate>.
#        If no enddate is defined, it is set to today.
#        '''
#        if not enddate:
#            enddate = datetime.date.today()
#        if self.startdate and self.startdate > startdate:
#            startdate = self.startdate
#        if self.enddate and self.enddate < enddate:
#            enddate = self.enddate
#
#        missing_dates = self.missing_prices(startdate, enddate)
#        if missing_dates:
#            return 'No prices found for {} on the following dates: '.format(
#                    self.name, ', '.join(missing_dates))
#        return []
#
#        num_prices = Price.objects.filter(stock=self, date__gte=startdate, 
#                                                    date__lte=enddate).count()
#        n_days = (enddate - startdate).days
#        short_term_threshold = 5 * ((n_days + 1) // 7)
#        long_term_threshold = (250 * n_days) // 365
#        threshold = min(short_term_threshold, long_term_threshold)
#        warning = None
#        if num_prices < threshold:
#            warning = 'Only {} prices found for {} from {} to {} (target={})'.\
#                    format(num_prices, self.name, startdate, enddate, 
#                           threshold)
#        return warning


    def missing_prices(self, index=None, startdate=None, enddate=None):
        '''
        Returns a list with dates for which no prices were found in <stock>, but
        the index associated with the stocks currency does have a price.
        '''
        if not enddate:
            enddate = datetime.date.today()
        if self.enddate and self.enddate < enddate:
            enddate = self.enddate
        if not startdate:
            startdate = self.get_earliest_date()
        if self.startdate and self.startdate > startdate:
            startdate = self.startdate
        if not index:
            if self.currency == self.AUSTRALIAN_DOLLAR:
                index_name = '^AORD'
            elif self.currency == self.US_DOLLAR:
                index_name = '^GSPC'
            else:
                raise ValueError('currency {} not implemented yet'.format(
                        self.currency))
            index = Stock.objects.get(name=index_name)
        return [d for d in index.price.close.get_dates(startdate, enddate)
                if d not in self.price.close.dates]


    def missing_channels(self, startdate=None, enddate=None):
        '''
        Returns a list with dates for which no channel information was found in
        the database, but prices were found.
        '''
#NOTE: if a channel is available for 1 lookback it assumes all are available
#TODO: date range does nothing
        startdate = self.get_earliest_date() + datetime.timedelta(days=365)
        enddate = self.get_latest_date()
        if startdate < enddate:
            channeldates = Channel.objects.values_list(
                    'date', flat=True).filter(stock=self)
            return [d for d in self.price.close.get_dates(startdate, enddate)
                    if d not in channeldates]


    def correct_splits(self):
        '''
        Adjust prices to remove the effect of stock splits
        '''
        startdate = self.get_earliest_date()
        for enddate, ratio, price in self.check_splits():
            # <date> is the last old price, next day is new
            prices = Price.objects.filter(stock=self, date__gte=startdate, 
                    date__lte=enddate)
            with transaction.commit_on_success():
                for price in prices:
                    price.open *= ratio
                    price.close *= ratio
                    price.high *= ratio
                    price.low *= ratio
                    price.volume /= ratio
                    price.save()


    def check_splits(self):
        '''
        Return a list of dicts with date and split factor.
        '''
        splits = []
        lastclose = self.lastclose()
        for date in reversed(self.price.close.dates):
            open_ = self.price.open[date]
            if open_ <= 0.1 and lastclose < 0.1:
                continue # daily variation may look like split
            ratio = lastclose / open_
            if ratio > 1.8:
                ratio = int(ratio+0.5)
                splits.append((date, ratio, lastclose, open_))
            elif ratio < 0.6:
                ratio = 1/int(1/ratio+0.5)
                splits.append((date, ratio, lastclose, open_))
            lastclose = self.price.close[date]
        return splits


    def data_summary(self, date, lookback):
        '''
        Return a dict with price and channel data on <date>
        '''
        date = self.price.close.get_date(date)
        self.date_range = (date - datetime.timedelta(days=5), date)
        close = self.price.close[date]
        high = self.price.high[date]
        angle = self.price.channel.angle(lookback)[date]
        bottom = self.price.channel.bottom(lookback)[date]
        sl = self.price.channel.stoploss(lookback, date)
        sl_c = 100 * (1 - sl / close)
        sl_h = 100 * (1 - sl / high)

        channels = Channel.with_close.filter(stock=self, date=date).order_by(
                'lookback')

        return {'date': date, 'close': close, 'open': self.price.open[date],
                'high': high, 'low': self.price.low[date],
                'angle': angle,
                'width': self.price.channel.width(lookback)[date],
                'bottom': bottom,
                'sl': sl, 'sl_h': sl_h, 'sl_c': sl_c,
                'channels': channels,
                'lookback': lookback,
                }


    def get_close(self, date):
        '''
        Returns the close price on <date>
        '''
        return float(Price.objects.get(stock=self, date=date).close)


    def lastclose(self):
        '''
        Returns the most recent close price in the Price table
        '''
        return self.get_close(self.get_latest_date)


    def __unicode__(self):
        return '{} - {}'.format(self.name, self.description)



class Price(models.Model):
    '''
    All prices are stored in the price table.
    '''
    stock = models.ForeignKey(Stock)
    date = models.DateField()
    open = models.DecimalField(max_digits=6, decimal_places=2)
    close = models.DecimalField(max_digits=6, decimal_places=2)
    high = models.DecimalField(max_digits=6, decimal_places=2)
    low = models.DecimalField(max_digits=6, decimal_places=2)
    volume = models.BigIntegerField()

    retry = {} # class variable that keeps track of download retries


    @classmethod
    def get_latest_date(cls):
        '''
        Return the date of the most recent price in the database
        '''
        return cls.objects.all().aggregate(models.Max('date'))['date__max']


    @classmethod
    def insert_prices(cls, data):
        '''
        Insert multiple prices into the price table.

        <data> is a list of dicts with a key for each <Price> field.
        If a price record already exists the value will silently be 
        overwritten.
        '''
        with transaction.commit_on_success():
            for row in data:
                cls.objects.get_or_create(stock=row.pop('stock'), 
                date=row.pop('date'), defaults=row)


    @classmethod
    def check_split(cls, stock_list):
        '''
        Return a list of stocks that may have had a stock split overnight.
        '''
        split_list = []
        for stock in stock_list:
            prices = cls.objects.filter(stock=stock).order_by('-date')[0:2]
            if len(prices) > 1:
                ratio = prices[1].close / prices[0].close
                if ratio > 1.8 or ratio < 0.6:
                    split_list.append(stock)
        return split_list


    @classmethod
    def get_startdate(cls, stock):
        '''
        Return the lowest date in the database for <stock>
        '''
        qs = Price.objects.filter(stock=stock).aggregate(Min('date'))
        return qs['date__min']


    @classmethod
    def get_enddate(cls, stock):
        '''
        Return the highest date in the database for <stock>
        '''
        qs = Price.objects.filter(stock=stock).aggregate(Max('date'))
        return qs['date__max']


    @classmethod
    def download_prices_today(cls, download_stocks=None, currency=None, 
                delay=60, dl_id=None, num_retries=3):
        '''
        Download the latest prices for all stocks in <download_stocks> and store
        them in the prices database. If <download_stocks> is not specified, all
        stocks in <currency> will be downloaded. For successfully downloaded
        prices, the channel parameters are calculated and stored in the 
        database.
        Stocks for which the download was not successful will be retried after
        <delay> minutes.
        <dl_id> is used for keeping track of download retries.
        '''
        if dl_id: # this is a retry
            if not cls.retry.get(dl_id):
                raise ValueError('time does not exist for id={}'.format(dl_id))
            # wait for delay minutes if required:
            while(time.time() - cls.retry.get(dl_id)[-1] < delay * 60):
                time.sleep(60) # wait for one minute
            cls.retry[dl_id].append(time.time())
        else: # this is first download
            dl_id = random_string()
            cls.retry[dl_id] = [time.time()]
            if download_stocks is None:
                download_stocks = Pool.get_todays_stocks_for_download(currency)

        if len(download_stocks):
            data = download_today(download_stocks)
        else:
            text = 'ERROR: download prices called with empty stock_list'
            notify_admin(text)
            raise ValueError(text)

        if len(data) != len(download_stocks):
            text = 'ERROR: download_today did not return all stocks'
            notify_admin(text)
            raise ValueError(text)

        error_stocks = [d['stock'] for d in data if len(d) == 1]
        if error_stocks:
            text = 'WARNING: the following stocks were not found: {}'.format(
                    ', '.join(s.name for s in error_stocks))
            notify_admin(text)

        retry_stocks = [d['stock'] for d in data if len(d) == 2]
        if retry_stocks:
            text = 'WARNING: no prices found for:\n\t{}\nDownload will be '\
                    'retried after {} minutes.'.format(', '.join(s.name for s in
                    retry_stocks), delay * 60)
            notify_admin(text)

        downloaded_data = [d for d in data if len(d) == 7]
        downloaded_stocks = [d['stock'] for d in downloaded_data]
        cls.insert_prices(downloaded_data) # destroys downloaded_data!
        split_stocks = cls.check_split(downloaded_stocks)

        if split_stocks:
            text = 'WARNING: a (reverse) split may have occurred for {} stocks: '.\
                    format(len(split_stocks), ', '.join(s.name for s in split_stocks))
            notify_admin(text)

        Channel.calculate_latest(downloaded_stocks)

        if retry_stocks and len(cls.retry[dl_id]) < num_retries:
            cls.download_prices_today(retry_stocks, dl_id=dl_id)
        else:
            del cls.retry[dl_id]


    class Meta:
        ordering = ['stock', 'date']
        unique_together = (("stock", "date"),)


    def __unicode__(self):
        return '{}, {}, {:8.2f}'.format(self.stock, self.date, self.close)


class Pool(models.Model):
    '''
    The Pool table stores pools of stocks.

    Each pool must have an associated index. Usually that will make sense, e.g.
    a pool that contains stocks from the DOW will have the DOW as its index. In
    case no sensible index is connected to the pool, use a broad index like the
    S&P as the pool index. The pool index may be used as a reference plot 
    and/or for selecting which methods to use.

    Each stock entry in the pool has a date range, if no explicit start and 
    date has been defined for the stock, they are the start and enddates of 
    the pool.
    The start and enddates of the pool are there to set during which time
    period the pool is valid.
    Errors are generated if:
        * a (meta)system tries to use the pool outside the pools date range
        * a pool tries to use a stock outside the stocks date range

    A stock may have multiple entries in the pool, provided their date ranges
    to not coincide/overlap.
    '''
    name = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=50)
    index = models.ForeignKey(Stock, related_name='pool_index')
    startdate = models.DateField()
    enddate = models.DateField(null=True, blank=True)
    members = models.ManyToManyField(Stock, through='StockPoolDates')


#    @property
#    def market_type(self):
#        '''
#        Return the market condition class
#        '''
#        if not hasattr(self, '_market_type'):
#            self._market_type = MarketType(self)
#        return self._market_type


    def _get_raw_list(self):
        '''
        Returns an exact list of all members for this Pool, where each member
        is a stock with a start and enddate.
        '''
        raw_pool_list = []
        for stock in self.members.all():
            if stock in (rpl[0] for rpl in raw_pool_list):
                continue
            for member in stock.stockpooldates_set.filter(pool=self):
                raw_pool_list.append((stock, member.startdate, member.enddate))
        return raw_pool_list


    def _get_list(self):
        '''
        Returns a list of all Pool members, including index, with validated
        (adjusted) date ranges.

        Returns a list of tuples of the format (stock, startdate, enddate).
        The list is an exact copy of the contents of the pool, except for the 
        following cases:
            * if a stock has no startdate it is replaced with pool.startdate
            * if a stock has no enddate it is replaced with pool.enddate
            * if the startdate of a stock is earlier than pool.startdate it is
                set to pool.startdate
            * if the enddate of a stock is later than pool.enddate it is set to
                pool.enddate
        The first item of the list is always the index.
        '''
        pool_list = [(self.index, self.startdate, self.enddate)]
        for (stock, startdate, enddate) in self._get_raw_list():
            if not startdate or startdate < self.startdate:
                startdate = self.startdate
            if self.enddate and (not enddate or enddate > self.enddate):
                enddate = self.enddate
            pool_list.append((stock, startdate, enddate))
        return pool_list


    def _get_offset_list(self):
        '''
        Returns a list of all Pool members, including index, with validated
        (adjusted) date ranges. The startdates have been offset 1 year into the
        past to make sure enough price data is available for indicators.

        Returns a list of tuples of the format (stock, startdate, enddate)
        for all stocks in pool. Multiple entries may exist with different date
        ranges.
        '''
        dated_stock_list = []
        for stock, startdate, enddate in self._get_list():
            dated_stock_list.append((stock, last_year(startdate), enddate))
        return dated_stock_list


    def _set_cache(self):
        '''
        Generate a list of all Pool entries (NO index) with their date ranges.

        <self._cache> is a list of tuples of the format (stock, startdate, 
        enddate) for all stocks in pool. Multiple entries may exist with 
        different date ranges. The index is *not* in the list.
        '''
        self._cache = self._get_list()[1:]


    def get_cached_stocklist(self, date):
        '''
        Returns the list of stocks that were in the pool on <date>.
        '''
        stock_list = []
        if not self.enddate or self.startdate <= date <= self.enddate:
            if getattr(self, '_cache', None) is None:
                self._set_cache()
            for stock, startdate, enddate in self._cache:
#FIXME: pool=S&P500, startdate=1/12/2012 -> CBE is not filtered out!!!!!
                if date >= startdate and (not enddate or date <= enddate):
                    stock_list.append(stock)
        return stock_list


    def size(self):
        '''
        Returns the number of stock entries in the pool.
        '''
        return self.stockpooldates_set.count()


    def _get_stock_index_list(self, date):
        '''
        Returns the list of stocks that were in the pool on <date>.

        Includes the index.
        '''
        stock_list = []
        for stock, startdate, enddate in self._get_list():
            if date >= startdate and (not enddate or date <= enddate):
                stock_list.append(stock)
        return stock_list


    def activate(self):
        '''
        Make this pool instance active by resetting its enddate.

        The prices for current stocks in active pools are updated daily.
        '''
        self.enddate = None
        self.save()


    def deactivate(self):
        '''
        Make this pool instance inactive by setting its enddate.

        Prices for stocks in inactive pools are not updated daily (unless they
        are current in an active pool).
        Deactivating sets the enddate to the latest date for which prices are
        found for *all* current stocks in the pool.
        '''
        date = datetime.date.today()
        self.enddate = None
        while not self.enddate:
            if date < self.startdate:
                raise ValueError('Cannot set enddate, because this pool never'\
                                 ' had complete price data.')
            for stock in self._get_stock_index_list(date):
                latest_date = stock.get_latest_date()
                if not latest_date or latest_date < date:
                    break
                self.enddate = date
            date = previous_weekday(date)
        self.save()


#    @staticmethod
#    def _download_prices(stock_list):
#        '''
#        Download the prices for all stocks in <stock_list>.
#
#        <stock_list> is a list of tuples with the format (stock, startdate,
#        enddate).
#        '''
#        for stock, startdate, enddate in stock_list:
#            if not enddate:
#                enddate = datetime.date.today()
#            stock.download_history(startdate, enddate)


    def download_prices(self, fromdate=None, todate=None):
        '''
        Download the prices for all stocks in this pool in their ranges.

        If <fromdate> and <todate> are specified, the stock is downloaded in
        that range, unless its own range is narrower.
        '''
        for stock, startdate, enddate in self._get_list():
            if fromdate is not None:
                startdate = max(startdate, fromdate)
            if enddate is not None:
                enddate = min(enddate, todate)
            elif not enddate:
                enddate = datetime.date.today()
            if enddate >= startdate:
                stock.download_history(startdate, enddate)

#    @classmethod
#    def download_all(cls):
#        '''
#        Downloads the prices for all stocks in all pools.
#        '''
#        download_list = set()
#        for pool in cls.objects.all():
#            download_list.update(set(pool._get_offset_list()))
#        cls._download_prices(download_list)



    def check_splits(self):
        '''
        Return a list with all (potential) splits for all stocks in this pool.
        '''
        splits = []
        for stock, unused, unused in self._get_list():
            stock_splits = stock.check_splits()
            if stock_splits:
                splits.append((stock, stock_splits))
        return splits


    def missing_prices(self, startdate=None, enddate=None):
        '''
        Returns a list with all dates on which there is no price in the stock
        price database, but there is a value for the index of this pool 
        '''
        missing_dates = []
        for stock, unused, unused in self._get_list():
            dates = stock.missing_prices(self.index, startdate, enddate)
            if dates:
                missing_dates.append((stock, dates))
        return missing_dates


    def missing_channels(self, startdate=None, enddate=None):
        '''
        Returns a list with all dates on which there is no channel data in the
        channel database, but there is a value for the index of this pool 
        '''
        missing_dates = []
        for stock, unused, unused in self._get_list():
            dates = stock.missing_channels(startdate, enddate)
            if dates:
                missing_dates.append((stock, dates))
        return missing_dates


    def calculate_channels(self, startdate=None, enddate=None):
        '''
        Calculate channel data for all stocks in the pool. 
        '''
#TODO: dates do nothing
#        skip = True
        for stock, unused, unused in self._get_list():
#            if stock.name == 'STI':
#                skip = False
#            if skip:
#                continue
            Channel.calculate(stock, startdate, enddate)


#    @staticmethod
#    def _check_prices(stock_list, startdate=None, enddate=None):
#        '''
#        Check if all prices are available for all stocks in all pools.
#
#        <stock_list> is a list of tuples with the format (stock, startdate,
#        enddate).
#        '''
#        warnings = []
#        for stock, pool_startdate, pool_enddate in stock_list:
#            if startdate is None:
#                startdate = pool_startdate
#            if enddate is None:
#                enddate = pool_enddate
#            warning = stock.has_prices(startdate, enddate)
#            if warning:
#                warnings.append(warning)
#        return warnings
#
#
#    def check_prices(self, startdate=None, enddate=None):
#        '''
#        Check if all prices are available for all stocks in this pool.
#        '''
#        return self._check_prices(self._get_offset_list(), startdate, enddate)


    @staticmethod
    def _check_date_ranges(stock_list):
        '''
        Checks if any stock in <stock_list> is used outside its date range.

        Returns a list with one string for each warning.
        '''
        warnings = []
        for stock, startdate, enddate in stock_list:
            if stock.startdate and startdate < stock.startdate:
                warnings.append('Pool startdate for {} is {}, but must be ' \
                        'later than {}.'.format(stock.name, startdate,
                                                            stock.startdate))
            if stock.enddate and (not enddate or enddate > stock.enddate):
                warnings.append('Pool enddate for {} is {}, but must be '\
                        'earlier than {}'.format(stock.name, enddate,
                                                            stock.enddate))
        return warnings


    def check_date_ranges(self, startdate=None, enddate=None):
        '''
        Checks if any stock in this pool is used outside its date range.
        If startdate and/or enddate are specified, the pool must lie within
        those dates.
        '''
        warnings = self._check_date_ranges(self._get_offset_list())
        if startdate and self.startdate > startdate:
            warnings.append('Pool startdate later than (meta)system startdate')
        if enddate and self.enddate and self.enddate < enddate:
            warnings.append('Pool enddate is earlier than (meta)system enddate')
        return warnings


    @staticmethod
    def _check_date_overlap(stock_list):
        '''
        Checks if the date range of any stock in <stock_list> overlaps with 
        itself.

        Returns a list with one string for each warning.
        '''
        stock_dict = defaultdict(list)
        for stock in stock_list:
            stock_dict[stock[0]].append(stock)
        warnings = []
        for stock_name, stock_list in stock_dict.items():
            if stock_list[0][2] and stock_list[0][1] >= stock_list[0][2]:
                warnings.append('Startdate is later than enddate for {}'.\
                                                            format(stock_name))
            if len(stock_list) <= 1:
                continue
            sortedlist = sorted(stock_list, key=itemgetter(1))
            prevstart = sortedlist[0][1]
            prevend = sortedlist[0][2] if sortedlist[0][2] else \
                                                        datetime.date.today()
            for stock, startdate, enddate in sortedlist[1:]:
                if not enddate:
                    enddate = datetime.date.today()
                if startdate >= enddate:
                    warnings.append('Startdate is later than enddate for {}'.\
                            format(stock_name))
                if prevstart == startdate:
                    warnings.append('{} has two identical startdates'.format(
                            stock_name))
                if prevend == enddate:
                    warnings.append('{} has two identical enddates'.format(
                            stock_name))
                if startdate <= prevend:
                    warnings.append('Overlap found in {} date ranges'.format(
                            stock_name))
                prevstart = startdate
                prevend = enddate
        return warnings


    def check_date_overlap(self):
        '''
        Checks if any stock in this pool is used outside its date range.
        The index is skipped from this test.
        '''
        return self._check_date_overlap(self._get_list()[1:])


    @classmethod
    def check_all(cls):
        '''
        Check all pools for price availability, date ranges and date overlap.

        Returns a list of strings for each warning.
        '''
        warnings = []
        check_list = set()
        for pool in cls.objects.all():
            warnings.extend(cls._check_date_overlap(pool._get_list()))
            check_list.update(set(pool._get_offset_list()))
        warnings.extend(cls._check_prices(check_list))
        warnings.extend(cls._check_date_ranges(check_list))
        return warnings



    def copy(self):
        '''
        Copies this pool to a new pool with a unique name. It is a deep copy
        for StockPoolDate fields are copied too.
        '''
        new_pool = Pool.objects.create(name=random_string(4), 
                index=self.index, startdate=self.startdate, 
                enddate=self.enddate)
        for (stock, startdate, enddate) in self._get_raw_list():
            StockPoolDates.objects.create(stock=stock, pool=new_pool, 
                                        startdate=startdate, enddate=enddate)
        return new_pool


    @classmethod
    def get_todays_stocks_for_download(cls, currency):
        '''
        Returns a list with all current <currency> stocks in active pools.

        Pools are active if they have no enddate. (Re)setting the enddate is 
        controlled by the system that uses the pool.
        '''
        if currency is None:
            raise ValueError('currency is not set')
#TODO: allow for time zones (i.e. set date depending on currency)
        today = datetime.date.today()
        stock_list = set()
        for pool in cls.objects.filter(enddate=None):
            for stock in pool._get_stock_index_list(today):
                if stock.currency == currency:
                    stock_list.add(stock)
        return list(stock_list)


    def stock_string(self): # this is used in admin
        return ', '.join(self.get_stock_names())
    stock_string.short_description = "Stock list"


    def get_stock_names(self):
        return (s.stock.name for s in self.members.all())


    def __unicode__(self):
        return '{}'.format(self.name)


class StockPoolDates(models.Model):
    '''
    Provides extra dates fields on the Pool-Stocks manytomany relationship.
    Specifies the start and enddates for stocks in the pool.
    '''
    stock = models.ForeignKey(Stock)
    pool = models.ForeignKey(Pool, blank=True) #to avoid form errors
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return '{:10} {:10} {} {}'.format(self.stock.name, self.pool.name, 
                                        self.startdate, self.enddate)
