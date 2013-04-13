from __future__ import division
from __future__ import absolute_import

from datetime import date, timedelta
from copy import deepcopy

from django.test import TestCase

from utils_python.utils import last_year, previous_weekday, next_weekday

from pricemanager.models import Stock, Price, Pool, StockPoolDates
from pricemanager.yahoo import _yahoo_today_url, _yahoo_history_url, _unsplit,\
        download_today, download_history
from pricemanager.indicators.datedlist import DatedList


class DatedListTests(TestCase):

    def setUp(self):
        pass

    def test_datedlist(self):
        # test continuous list
        dates = [date(2012,1,x) for x in range(2,6)]
        values = range(2,6)
        self.assertEqual(len(dates), len(values))
        dl = DatedList(values, dates)
        self.assertEqual(dl, values)
        self.assertEqual(len(dl), len(values))
        self.assertEqual(dl[0], 2)
        self.assertEqual(dl[-1], 5)
        for d in range(2,6):
            self.assertEqual(dl[date(2012,1,d)], d)
            self.assertEqual(dl.index(date(2012,1,d)), d-2)
            self.assertTrue(date(2012,1,d) in dl)
        for d in (1,6):
            self.assertFalse(date(2012,1,d) in dl)
            self.assertIsNone(dl.on(date(2012,1,d)))
        self.assertEqual(dl[date(2012,1,1)], 2)
        self.assertEqual(dl[date(2012,1,6)], 5)
        self.assertEqual(dl.delta(date(2012,1,2), date(2012,1,4)), 2)
        self.assertEqual(dl.offset(date(2012,1,2), 2), 4)
        self.assertEqual(dl.offset(date(2012,1,4), -2), 2)
        self.assertEqual(dl[date(2012,1,2):date(2012,1,4)], [2,3,4])
        self.assertEqual(dl[date(2012,1,2):2], [2,3])
        self.assertEqual(dl[date(2012,1,4):-2], [3,4])
        self.assertRaises(TypeError, dl[1:2])
        with self.assertRaises(TypeError):
            dl[1:date(2012,1,4)]

    # discontinuities in list
        extradates = [date(2012,1,x) for x in range(10,13)]
        extravalues = range(10,13)
        dl_extra = DatedList(extravalues, extradates)
    # extend
        dl.extend(dl_extra)
        self.assertEqual(dl, values + extravalues)
        self.assertEqual(len(dl), len(values) + len(extravalues))
    # append
        dl.append((date(2012,1,13),13))
        self.assertEqual(dl, values + extravalues + [13,])
        self.assertEqual(len(dl), len(values) + len(extravalues) + 1)
        for d in range(2,6):
            self.assertEqual(dl[date(2012,1,d)], d)
            self.assertEqual(dl.index(date(2012,1,d)), d-2)
            self.assertTrue(date(2012,1,d) in dl)
        for d in range(10,14):
            self.assertEqual(dl[date(2012,1,d)], d)
            self.assertEqual(dl.index(date(2012,1,d)), d-6)
            self.assertTrue(date(2012,1,d) in dl)
        for d in (1,6,9,14):
            self.assertFalse(date(2012,1,d) in dl)
            self.assertIsNone(dl.on(date(2012,1,d)))
        self.assertEqual(dl[date(2012,1,1)], 2)
        self.assertEqual(dl[date(2012,1,6)], 5)
        self.assertEqual(dl[date(2012,1,9)], 5)
        self.assertEqual(dl[date(2012,1,14)], 13)
        self.assertEqual(dl.delta(date(2012,1,3), date(2012,1,12)), 5)
        self.assertEqual(dl.delta(date(2012,1,3), date(2012,1,18)), 6)
        self.assertEqual(dl.delta(date(2012,1,1), date(2012,1,12)), 6)
        self.assertEqual(dl.offset(date(2012,1,3), 4), 11)
        self.assertEqual(dl.offset(date(2012,1,11), -4), 3)
        self.assertEqual(dl.offset(date(2012,1,3), -5), 2)
        self.assertEqual(dl.offset(date(2012,1,12), 5), 13)
        self.assertEqual(dl[date(2012,1,3):date(2012,1,11)], [3,4,5,10,11])
        self.assertEqual(dl[date(2012,1,4):3], [4,5,10])
        self.assertEqual(dl[date(2012,1,11):-3], [5,10,11])
        self.assertRaises(TypeError, dl[1:2])
        with self.assertRaises(TypeError):
            dl[1:date(2012,1,4)]



class YahooTests(TestCase):

    def setUp(self):
        Stock.objects.create(name='nonexist')
        Stock.objects.create(name='^GSPC')
        Stock.objects.create(name='FDX')
        Stock.objects.create(name='BHP.AX')

    def test_yahoo_today_url(self):
        self.assertEqual(_yahoo_today_url(Stock.objects.filter(name='^GSPC')), 
                'http://download.finance.yahoo.com/d/quotes.csv?s=^GSPC&f=sd' \
                '1oml1v')
        self.assertEqual(_yahoo_today_url(Stock.objects.exclude(name=
                'nonexist')), 'http://download.finance.yahoo.com/d/quotes' \
                '.csv?s=^GSPC+FDX+BHP.AX&f=sd1oml1v')
        self.assertIsNone(_yahoo_today_url([]))

    def test_download_today(self):
        self.assertIsNone(download_today([]))
        data = download_today(Stock.objects.filter(name='^GSPC'))
        self.assertEqual(len(data), 1)
        data = download_today(Stock.objects.all())
        self.assertEqual(len(data), 4)
        len_data = []
        for row in data:
            len_data.append(len(row))
            self.assertIn(len(row), (1,2,7))
            keylist = ('stock',)
            if len(row) > 1:
                keylist += ('date',)
            if len(row) > 2:
                keylist += ('open', 'high', 'low', 'close', 'volume')
            for key in keylist:
                self.assertIn(key, row)
        self.assertEqual(len_data.count(1), 1)
        if not 2 in len_data:
            print('WARNING: no N/A results found in data, retry test later!')
        if not 7 in len_data:
            print('WARNING: no valid results found in data, retry test later!')

    def test_yahoo_history_url(self):
        self.assertEqual(_yahoo_history_url('^GSPC', date(2010,1,1), 
                date(2011,2,2)), 'http://ichart.finance.yahoo.com/t' \
                'able.csv?s=^GSPC&amp;a=0&amp;b=1&amp;c=2010&amp;d=1&amp;e=2' \
                '&amp;f=2011&amp;g=d&amp;ignore=.csv')

    def test_unsplit(self):
        #generate test data:
        stock = Stock.objects.get(name='^GSPC')
        data_in = ((1,64.,15.8,25), (2,64.,15.6,25), (3,64.,15.5,25), 
                (4,64.,15.3,25), (5,320.,15.2,5), (6,320.,12.6,5), 
                (7,320.,12.5,5), (8,320.,12.4,5), (9,16.,12.3,100), 
                (10,16.,12.2,100), (11,16.,12.0,100), (12,160.,11.9,10), 
                (13,160.,11.8,10), (14,80.,10.7,20), (15,80.,10.6,20), 
                (16,20.,10.5,80), (17,20.,10.4,80), (18,10.,10.3,160), 
                (19,10.,10.2,160), (20,10.,10.1,160), (21,10.,10.0,160), )
        data = []
        for day, price, adj_close, volume in data_in:
            values = {'stock': stock, 'open': price, 'high': price, 
                      'low': price, 'close': price, 'volume': volume,
                      'date': date(2010, 1, day), 
                      'adj_close': adj_close}
            data.append(values)
        #make a deep copy to get two separate data sets
        test_data = deepcopy(data[:2])
        test_data[0]['stock'] = Stock.objects.get(name='FDX')
        self.assertRaises(ValueError, _unsplit, test_data)
        warning = _unsplit(data)
        self.assertEqual(len(warning), 1)
        self.assertEqual(len(data), 21)
        keylist = ('stock', 'date', 'open', 'high', 'low', 'close', 'volume')
        for row in data:
            self.assertEqual(len(row), 7)
            for key in keylist:
                self.assertIn(key, row)
            self.assertEqual(row['volume'], 160)
            self.assertEqual(row['close'], 10)

    def test_download_history(self):
        date1 = date(2010,1,1)
        date2 = date(2010,1,10)
        stock = Stock.objects.get(name='nonexist')
        self.assertIsNone(download_history(stock, date1, date2))
        stock = Stock.objects.get(name='^GSPC')
        self.assertIsNone(download_history(stock, date2, date1))
        data = download_history(stock, date1, date2)
        self.assertEqual(len(data), 5)
        keylist = ('stock', 'date', 'open', 'high', 'low', 'close', 'volume')
        for row in data:
            self.assertEqual(len(row), 7)
            for key in keylist:
                self.assertIn(key, row)
        date1 = date(1999,5,3)
        date2 = date(1999,5,14)
        stock = Stock.objects.get(name='FDX')
        data = download_history(stock, date1, date2)
        self.assertEqual(len(data), 10)
        self.assertEqual(data[0]['volume'], 1204800)
        self.assertEqual(data[9]['volume'], 2812400)
        self.assertEqual(data[0]['close'], 59.87)
        self.assertEqual(data[9]['close'], 57.435)


class modelsTestsFixture(TestCase):
    fixtures = ['PriceData.json']

    def test_Stock(self):
    # set_prices
        aapl = Stock.objects.get(name='AAPL')
        with self.assertRaises(AttributeError):
            price = aapl.price
        aapl.set_prices(date(2012,1,1), date(2012,6,30))
        self.assertEqual(len(aapl.price.open), 125)
        testdate = date(2012, 5, 31)
        self.assertEqual(aapl.price.open[testdate], 580.74)
        self.assertEqual(aapl.price.high[testdate], 581.50)
        self.assertEqual(aapl.price.low[testdate], 571.46)
        self.assertEqual(aapl.price.close[testdate], 577.73)
        self.assertEqual(aapl.price.volume[testdate], 17559800)


class modelsTests(TestCase):

    def setUp(self):
        Stock.objects.create(name='AAPL', description='Apple', 
                                                    currency=Stock.US_DOLLAR)
        Stock.objects.create(name='FDX', description='FedEx', 
                                                    currency=Stock.US_DOLLAR)
        Stock.objects.create(name='INTC', description='Intel', 
                                                    currency=Stock.US_DOLLAR)

    def test_Price(self):
        stock = Stock.objects.get(name='AAPL')
        date1 = date(2010,1,5)
        date2 = date(2010,1,10)
        date3 = date(2010,1,15)
        date4 = date(2010,1,20)
        price_record = {'stock': stock, 'date': date2, 'open': 1., 'high': 1.,
                        'low': 1., 'close': 1., 'volume': 1 }

    # _update_or_create
        Price._update_or_create(**price_record)
        self.assertEqual(Price.objects.all().count(), 1)
        self.assertEqual(Price.objects.get(stock=stock).volume, 1)
        price_record['volume'] = 100
        Price._update_or_create(**price_record)
        self.assertEqual(Price.objects.all().count(), 1)
        self.assertEqual(Price.objects.get(stock=stock).volume, 100)

    # get_latest_date
        price_record['date'] = date1
        Price._update_or_create(**price_record)
        self.assertEqual(Price.get_latest_date(), date2)
        price_record['date'] = date4
        Price._update_or_create(**price_record)
        self.assertEqual(Price.get_latest_date(), date4)
        price_record['date'] = date3
        Price._update_or_create(**price_record)
        self.assertEqual(Price.get_latest_date(), date4)
        self.assertEqual(Price.objects.all().count(), 4)

    # insert_prices
        data = []
        for x in range(11,15):
            data.append({'stock': stock, 'date': date(2010,1,x),
                    'open': 1., 'high': 1., 'low': 1., 'close': 1., 
                    'volume': x })
        Price.insert_prices(data)
        self.assertEqual(Price.objects.all().count(), 8)
        Price.insert_prices([])
        self.assertEqual(Price.objects.all().count(), 8)

    # check_split



    def test_Stock(self):
        date1 = date(2000,1,1)
        date2 = date(2010,1,5)
        date3 = date(2010,1,20)
        date4 = date(2011,1,5)
        date5 = date(2011,1,18)
        date6 = date(2012,1,1)
        fdx = Stock.objects.get(name='FDX')
        aapl = Stock.objects.get(name='AAPL')
        intc = Stock.objects.get(name='INTC')

    # set_dates
        self.assertIsNone(fdx.startdate)
        self.assertIsNone(fdx.enddate)
        fdx.set_dates(date1, False)
        self.assertEqual(fdx.startdate, date1)
        self.assertIsNone(fdx.enddate)
        aapl.set_dates(False, date6)
        self.assertIsNone(aapl.startdate)
        self.assertEqual(aapl.enddate, date6)
        intc.set_dates(date3, date4)
        self.assertEqual(intc.startdate, date3)
        self.assertEqual(intc.enddate, date4)

    # download_history
        aapl.download_history(date2, date3)
        self.assertEqual(Price.objects.filter(date__year=2010).count(), 11)
        fdx.download_history(date4, date5)
        self.assertEqual(Price.objects.filter(date__year=2011).count(), 9)

    # get_latest_date
        self.assertEqual(fdx.get_latest_date(), date5)
        self.assertEqual(aapl.get_latest_date(), date3)

    # is_current
        # use prev/next_weekday??
        one_day = timedelta(days=1)
        self.assertFalse(fdx.is_current(date1 - one_day))
        self.assertTrue(fdx.is_current(date1))
        self.assertTrue(fdx.is_current(date6))
        self.assertTrue(aapl.is_current(date1))
        self.assertTrue(aapl.is_current(date6))
        self.assertFalse(aapl.is_current(date6 + one_day))
        self.assertFalse(intc.is_current(date3 - one_day))
        self.assertTrue(intc.is_current(date3))
        self.assertTrue(intc.is_current(date4))
        self.assertFalse(intc.is_current(date4 + one_day))

    # has_prices
        # test with enddate=None
        self.assertIsNone(aapl.has_prices(date2, date3))
        self.assertIsNone(fdx.has_prices(date4, date5))
        self.assertIsNotNone(intc.has_prices(date2, date3))
        intc.download_history(date3, date4)
        self.assertIsNone(intc.has_prices(date3, date4))
        self.assertIsNotNone(intc.has_prices(date2, date4))
        self.assertIsNotNone(intc.has_prices(date3, date5))


    def test_Pool(self):
        date1 = date(2000,1,1)
        date2 = date(2010,1,5)
        date3 = date(2010,1,20)
        date4 = date(2011,1,5)
        date5 = date(2011,1,18)
        date6 = date(2012,1,4)
        aapl = Stock.objects.get(name='AAPL')
        intc = Stock.objects.get(name='INTC')
        fdx = Stock.objects.get(name='FDX')
        snp = Stock.objects.create(name='^GSPC', description='S&P500', 
                currency=Stock.US_DOLLAR, startdate=date1, enddate=date4)
        pool = Pool.objects.create(name='test', description='test', index=snp, 
                startdate=date2, enddate=date5)
        StockPoolDates.objects.create(stock=aapl, pool=pool)
        StockPoolDates.objects.create(stock=intc, pool=pool)
        StockPoolDates.objects.create(stock=fdx, pool=pool)

        print 'SIZE', pool.size()

    # _get_raw_list
        temp = StockPoolDates.objects.create(stock=fdx, pool=pool)
        raw_list = pool._get_raw_list()
        self.assertEqual(len(raw_list), 4) # does not include index 
        temp.delete()
        raw_list = pool._get_raw_list()
        self.assertEqual(len(raw_list), 3) # does not include index 


#TMP
#        pool2 = Pool.objects.create(name='test2', description='test2', 
#                index=intc, startdate=date2, enddate=date5)
#        StockPoolDates.objects.create(stock=intc, pool=pool2)
#        print 'set prices'
#        print 'WARNINGS', pool2.set_prices(date2, date5)
#        print 'INDEX', pool2.index.price.close[date3]
#        print 'INTC', intc.index.price.close[date3]
#/TMP


    # _get_list
        #

    # _get_offset_list
        dated_stock_list = pool._get_offset_list()
        self.assertEqual(len(dated_stock_list), 4) #must include index 
        for stockdates in dated_stock_list:
            self.assertEqual(stockdates[2], date5) 
            self.assertLessEqual(stockdates[1], last_year(date2))
        # change the date ranges of the stocks in the pool
        for st,sd,ed in ((aapl,date3,date6), (intc,date3,date4),
                                                        (fdx,date1,date4)):
            spd = StockPoolDates.objects.get(stock=st, pool=pool)
            spd.startdate = sd
            spd.enddate = ed
            spd.save()

        dated_stock_list = pool._get_offset_list()
        self.assertEqual(len(dated_stock_list), 4) #must include index
        for row in ((snp, last_year(date2), date5),
                    (aapl, last_year(date3), date5),
                    (intc, last_year(date3), date4),
                    (fdx, last_year(date2), date4)):
            self.assertIn(row, dated_stock_list)

        pool.enddate = None
        today = date.today()
        dated_stock_list = pool._get_offset_list()
        self.assertEqual(len(dated_stock_list), 4) #must include index
        for row in ((snp, last_year(date2), None),
                    (aapl, last_year(date3), date6),
                    (intc, last_year(date3), date4),
                    (fdx, last_year(date2), date4)):
            self.assertIn(row, dated_stock_list)

#    # validate_dates
        pool.enddate = date5
        warnings = pool.check_date_ranges()
        self.assertEqual(len(warnings), 1)
        self.assertIn('enddate', warnings[0])

        snp.set_dates(date3, date6)
        warnings = pool.check_date_ranges()
        self.assertEqual(len(warnings), 1)
        self.assertIn('startdate', warnings[0])

        snp.set_dates(date1, date6)
        warnings = pool.check_date_ranges()
        self.assertFalse(warnings)

    # _set_cache
        self.assertFalse(hasattr(pool, '_cache'))
        pool._set_cache()
        self.assertTrue(hasattr(pool, '_cache'))
        self.assertEqual(len(pool._cache), 3)
        for row in ((aapl, date3, date5),
                    (intc, date3, date4),
                    (fdx,  date2, date4)):
            self.assertIn(row, pool._cache)

    # get_cached_stocklist
        del pool._cache
        self.assertFalse(hasattr(pool, '_cache'))
        self.assertEqual(pool.get_cached_stocklist(last_year(date1)), [])
        self.assertEqual(pool.get_cached_stocklist(date1), [])
        self.assertFalse(hasattr(pool, '_cache'))
        self.assertEqual(pool.get_cached_stocklist(date2), [fdx,])
        self.assertTrue(hasattr(pool, '_cache'))
        self.assertEqual(set(pool.get_cached_stocklist(date3)), set([aapl, intc, fdx]))
        self.assertEqual(set(pool.get_cached_stocklist(date4)), set([aapl, intc, fdx]))
        self.assertEqual(pool.get_cached_stocklist(date5), [aapl,])
        self.assertEqual(pool.get_cached_stocklist(date6), [])

    #  _get_stock_index_list
        self.assertEqual(pool._get_stock_index_list(last_year(date1)), [])
        self.assertEqual(pool._get_stock_index_list(date1), [])
        self.assertEqual(set(pool._get_stock_index_list(date2)), set([snp, fdx,]))
        self.assertEqual(set(pool._get_stock_index_list(date3)), set([snp, aapl, intc, fdx]))
        self.assertEqual(set(pool._get_stock_index_list(date4)), set([snp, aapl, intc, fdx]))
        self.assertEqual(set(pool._get_stock_index_list(date5)), set([snp, aapl,]))
        self.assertEqual(pool._get_stock_index_list(date6), [])
        #

    # activate
        self.assertIsNotNone(pool.enddate)
        pool.activate()
        self.assertIsNone(pool.enddate)

    # deactivate
        self.assertRaises(ValueError, pool.deactivate)
    # download_prices
        self.assertEqual(Price.objects.all().count(), 0)
        snp.set_dates(False, None)
        pool.download_prices()

        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=snp, 
                                    date=previous_weekday(last_year(date3)))
        self.assertTrue(Price.objects.get(stock=snp, 
                                    date=next_weekday(last_year(date3))))
# why use today???
#        self.assertTrue(Price.objects.get(stock=snp, 
#                                    date=previous_weekday(today)))

        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=aapl, 
                                    date=previous_weekday(last_year(date3)))
        self.assertTrue(Price.objects.get(stock=aapl, 
                                    date=next_weekday(last_year(date3))))
        self.assertTrue(Price.objects.get(stock=aapl, 
                                    date=previous_weekday(date6)))
        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=aapl, 
                                    date=next_weekday(date6))

        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=intc, 
                                    date=previous_weekday(last_year(date3)))
        self.assertTrue(Price.objects.get(stock=intc, 
                                    date=next_weekday(last_year(date3))))
        self.assertTrue(Price.objects.get(stock=intc, 
                                    date=previous_weekday(date4)))
        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=intc, 
                                    date=next_weekday(date4))

        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=fdx, 
                                    date=previous_weekday(last_year(date2)))
        self.assertTrue(Price.objects.get(stock=fdx, 
                                    date=next_weekday(last_year(date2))))
        self.assertTrue(Price.objects.get(stock=fdx, 
                                    date=previous_weekday(date4)))
        self.assertRaises(Price.DoesNotExist, Price.objects.get, stock=fdx, 
                                    date=next_weekday(date4))

    # deactivate
        pool.deactivate()
        self.assertEqual(pool.enddate, previous_weekday(today))

    # check_prices
        self.assertEqual(pool.check_prices(), [])
        # intc,date3,date4),

        spd = StockPoolDates.objects.get(stock=intc, pool=pool)
        spd.startdate = date3
        spd.enddate = date5
        spd.save()
        self.assertEqual(len(pool.check_prices()), 1)

        spd = StockPoolDates.objects.get(stock=intc, pool=pool)
        spd.startdate = date2
        spd.enddate = date4
        spd.save()
        self.assertEqual(len(pool.check_prices()), 1)

    # get_todays_stocks_for_download
        spd = StockPoolDates.objects.get(stock=aapl, pool=pool)
        spd.enddate = None
        spd.save()
        del pool._cache
        self.assertEqual(Pool.get_todays_stocks_for_download(
                                                        Stock.US_DOLLAR), [])
        pool.activate()
        self.assertEqual(Pool.get_todays_stocks_for_download(Stock.EURO), [])
        self.assertEqual(set(Pool.get_todays_stocks_for_download(
                                    Stock.US_DOLLAR)), set([aapl, snp]))
        self.assertEqual(Pool.get_todays_stocks_for_download(
                                    Stock.BRITISH_POUND), [])

    # download_prices_today

        #
 
#        import cPickle as pickle
#        stock_list = Pool.get_todays_stocks_for_download(Stock.US_DOLLAR)
#        print stock_list
#        pickle.dump(stock_list, open('save.p', 'wb'))
        # what if stock does not exist!??

#
    # export_all
#        self.assertEqual(Pool.objects.all().count(), 1)
#        self.assertEqual(Stock.objects.all().count(), 4)
#        self.assertEqual(StockPoolDates.objects.all().count(), 3)
#        out = open("test.json", "w")
#        Pool.export_all(out)
#        out.close()
#        Pool.objects.all().delete()
#        StockPoolDates.objects.all().delete()
#        self.assertEqual(Pool.objects.all().count(), 0)
#        self.assertEqual(Stock.objects.all().count(), 4)
#        self.assertEqual(StockPoolDates.objects.all().count(), 0)
#        Pool.import_all("test.json")
#        print Pool.objects.all()
#        print Stock.objects.all()
#        print StockPoolDates.objects.all()
#        self.assertEqual(Pool.objects.all().count(), 1)
#        self.assertEqual(Stock.objects.all().count(), 4)
        self.assertEqual(StockPoolDates.objects.all().count(), 3)


    # copy
        pool = Pool.objects.get(name='test')
        new = pool.copy()
        copy = Pool.objects.get(name=new.name)
        self.assertEqual(pool.index, copy.index)
        self.assertEqual(pool.startdate, copy.startdate)
        self.assertEqual(pool.enddate, copy.enddate)
        for s_pool,s_copy in zip(pool.members.all(), copy.members.all()):
            self.assertEqual(s_pool, s_copy)
            poolmember = s_pool.stockpooldates_set.get(pool=pool)
            copymember = s_copy.stockpooldates_set.get(pool=copy)
            self.assertEqual(poolmember.startdate, copymember.startdate)
            self.assertEqual(poolmember.enddate, copymember.enddate)
            self.assertEqual(poolmember.stock, copymember.stock)


#class commandsTests(TestCase):
#
#    def setUp(self):
#        Stock.objects.create(name='AAPL', description='Apple', 
#                                                    currency=Stock.US_DOLLAR)
#        Stock.objects.create(name='FDX', description='FedEx', 
#                                                    currency=Stock.US_DOLLAR)
#        Stock.objects.create(name='INTC', description='Intel', 
#                                                    currency=Stock.US_DOLLAR)
#
#    def test_download_today(self):
#        stock = Stock.objects.get(name='AAPL')
#        date1 = date(2010,1,5)
#
#        
#        download_today(Stock.US_DOLLAR)
