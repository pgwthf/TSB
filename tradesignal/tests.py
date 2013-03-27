from __future__ import division
from __future__ import absolute_import

from datetime import date

from django.test import TestCase

from pricemanager.models import Stock

from tradesignal.models import _BaseSignal, EntrySignal, ExitSignal


class TestSignal(TestCase):
    fixtures = ['PriceData.json']

    def setUp(self):
        self.aapl = Stock.objects.get(name='AAPL')
        self.intc = Stock.objects.get(name='INTC')
        self.aapl.set_prices(date(2012,1,1), date(2012,6,30))

    def test__Base_Signal(self):
        self.assertEqual(_BaseSignal.OPEN, 'o')
        self.assertEqual(_BaseSignal.CLOSE, 'c')
        self.assertEqual(_BaseSignal.LIMIT, 'l')
        self.assertEqual(_BaseSignal.STOP, 's')
        bs = _BaseSignal(1, 2, 3, _BaseSignal.OPEN)
        self.assertEqual(bs.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': None, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': 1})
        self.assertTrue(bs.is_unconditional())
        self.assertFalse(bs.is_conditional())
        self.assertTrue(bs.is_entry_signal())
        self.assertFalse(bs.is_exit_signal())
        self.assertFalse(bs.is_position())
        self.assertFalse(bs.is_trade())
        self.assertEqual(bs.at, bs.OPEN)
        self.assertEqual(bs.stock, 1)
        self.assertEqual(bs.method, 2)
        self.assertEqual(bs.rule_entry, 3)
        self.assertIsNone(bs.price)
        del bs.at
        self.assertRaises(AttributeError, getattr, bs, '_at')
        bs.at = bs.CLOSE
        self.assertEqual(bs.at, bs.CLOSE)
        del bs.at
        with self.assertRaises(ValueError):
            bs.at = 'a'
        self.assertRaises(AttributeError, getattr, bs, '_at')
        with self.assertRaises(ValueError):
            bs = _BaseSignal(1, 2, 3, _BaseSignal.OPEN, 4)
        with self.assertRaises(ValueError):
            bs = _BaseSignal(1, 2, 3, _BaseSignal.CLOSE, 4)
        with self.assertRaises(ValueError):
            bs = _BaseSignal(1, 2, 3, _BaseSignal.LIMIT)
        with self.assertRaises(ValueError):
            bs = _BaseSignal(1, 2, 3, _BaseSignal.STOP)
        with self.assertRaises(ValueError):
            bs = _BaseSignal(1, 2, 3, 'x')
        with self.assertRaises(ValueError):
            bs = _BaseSignal(1, 2, 3, 'y', 4)
        bs = _BaseSignal(1, 2, 3, _BaseSignal.LIMIT, 4)
        self.assertEqual(bs.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': 4, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': 1})
        self.assertEqual(bs.price, 4)
        self.assertFalse(bs.is_unconditional())
        self.assertTrue(bs.is_conditional())
        self.assertTrue(bs.is_entry_signal())
        self.assertFalse(bs.is_exit_signal())
        self.assertFalse(bs.is_position())
        self.assertFalse(bs.is_trade())

    # test _execute
        bs = _BaseSignal(self.aapl, 2, 3, _BaseSignal.OPEN)
        self.assertEqual(bs._execute(date(2012, 6, 8)), 571.6)
        bs = _BaseSignal(self.aapl, 2, 3, _BaseSignal.CLOSE)
        self.assertEqual(bs._execute(date(2012, 6, 11)), 571.17)
        testdate = date(2012, 6, 22)
        p1 = 574.12
        p2 = 577.12
        p3 = 580.12
        p4 = 584.12
        p_open = 579.04
        for price, nl, ns, xl, xs in (
                (p1, None,   p_open, p_open, None),
                (p2, p2,     p_open, p_open, p2),
                (p3, p_open, p3,     p3,     p_open),
                (p4, p_open, None,   None,   p_open),):
            # entry at (or below) limit
            bs = _BaseSignal(self.aapl, 2, 3, _BaseSignal.LIMIT, price)
            self.assertEqual(bs.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': price, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
            self.assertFalse(bs.is_unconditional())
            self.assertTrue(bs.is_conditional())
            self.assertTrue(bs.is_entry_signal())
            self.assertFalse(bs.is_exit_signal())
            self.assertFalse(bs.is_position())
            self.assertFalse(bs.is_trade())
            self.assertEqual(bs._execute(testdate, entry=True), nl)
            # entry at (or above) stop
            bs = _BaseSignal(self.aapl, 2, 3, _BaseSignal.STOP, price)
            self.assertEqual(bs.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': price, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
            self.assertTrue(bs.is_entry_signal())
            self.assertFalse(bs.is_exit_signal())
            self.assertFalse(bs.is_position())
            self.assertFalse(bs.is_trade())
            self.assertEqual(bs._execute(testdate, entry=True), ns)
            # exit at (or above) limit
            bs = _BaseSignal(self.aapl, 2, 3, _BaseSignal.LIMIT, 1)
            self.assertEqual(bs.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': 1, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
            bs.price = price
            bs.price_entry = 1
            self.assertEqual(bs._execute(testdate, entry=False), xl)
            # exit at (or below) stop
            bs = _BaseSignal(self.aapl, 2, 3, _BaseSignal.STOP, 1)
            self.assertEqual(bs.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': 1, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
            bs.price = price
            bs.price_entry = 1
            self.assertEqual(bs._execute(testdate, entry=False), xs)

    def test_EntrySignal(self):
        es = EntrySignal(self.aapl, 2, 3, EntrySignal.OPEN)
        self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': None, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
        self.assertTrue(es.is_unconditional())
        self.assertFalse(es.is_conditional())
        self.assertTrue(es.is_entry_signal())
        self.assertFalse(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertFalse(es.is_trade())
        self.assertEqual(es.at, es.OPEN)
        self.assertEqual(es.stock, self.aapl)
        self.assertEqual(es.method, 2)
        self.assertEqual(es.rule_entry, 3)
        self.assertIsNone(es.price)
        testdate = date(2012, 6, 11)
        p1 = 570.12
        p2 = 575.12
        p3 = 588.12
        p4 = 590.12
        p_open = 587.72
        for price, nl, ns in (
                (p1, None,   p_open),
                (p2, p2,     p_open),
                (p3, p_open, p3),
                (p4, p_open, None)):
            # entry at (or below) limit
            es = EntrySignal(self.aapl, 2, 3, EntrySignal.LIMIT, price)
            self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': price, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
            self.assertFalse(es.is_unconditional())
            self.assertTrue(es.is_conditional())
            self.assertTrue(es.is_entry_signal())
            self.assertFalse(es.is_exit_signal())
            self.assertFalse(es.is_position())
            self.assertFalse(es.is_trade())
            self.assertEqual(es.execute(testdate), bool(nl))
            if bool(nl):
                self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': nl, 'rule_exit': None, 'date_entry': testdate, 'buydelay': None, 'stock': self.aapl})
                self.assertRaises(AttributeError, es.is_unconditional)
                self.assertRaises(AttributeError, es.is_conditional)
                self.assertFalse(es.is_entry_signal())
                self.assertFalse(es.is_exit_signal())
                self.assertTrue(es.is_position())
                self.assertFalse(es.is_trade())
                self.assertEqual(es.price_entry, nl)
                self.assertRaises(AttributeError, getattr, es, 'price')
                self.assertEqual(es.date_entry, testdate)
                with self.assertRaises(AttributeError):
                    x = es.at
            else:
                self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': price, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
                self.assertFalse(es.is_unconditional())
                self.assertTrue(es.is_conditional())
                self.assertTrue(es.is_entry_signal())
                self.assertFalse(es.is_exit_signal())
                self.assertFalse(es.is_position())
                self.assertFalse(es.is_trade())
                self.assertEqual(es.price, price)
                self.assertRaises(AttributeError, getattr, es, 'price_entry')
                self.assertRaises(AttributeError, getattr, es, 'date_entry')
                self.assertEqual(es.at, es.LIMIT)
            # entry at (or above) stop
            es = EntrySignal(self.aapl, 2, 3, EntrySignal.STOP, price)
            self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': price, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
            self.assertFalse(es.is_unconditional())
            self.assertTrue(es.is_conditional())
            self.assertTrue(es.is_entry_signal())
            self.assertFalse(es.is_exit_signal())
            self.assertFalse(es.is_position())
            self.assertFalse(es.is_trade())
            self.assertEqual(es.execute(testdate), bool(ns))
            if bool(ns):
                self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': ns, 'rule_exit': None, 'date_entry': testdate, 'buydelay': None, 'stock': self.aapl})
                self.assertRaises(AttributeError, es.is_unconditional)
                self.assertRaises(AttributeError, es.is_conditional)
                self.assertFalse(es.is_entry_signal())
                self.assertFalse(es.is_exit_signal())
                self.assertTrue(es.is_position())
                self.assertFalse(es.is_trade())
                self.assertEqual(es.price_entry, ns)
                self.assertRaises(AttributeError, getattr, es, 'price')
                self.assertEqual(es.date_entry, testdate)
                with self.assertRaises(AttributeError):
                    x = es.at
            else:
                self.assertEqual(es.get_data(), {'price_exit': None, 'date_exit': None, 'rule_entry': 3, 'method': 2, 'volume': None, 'price_entry': price, 'rule_exit': None, 'date_entry': None, 'buydelay': None, 'stock': self.aapl})
                self.assertFalse(es.is_unconditional())
                self.assertTrue(es.is_conditional())
                self.assertTrue(es.is_entry_signal())
                self.assertFalse(es.is_exit_signal())
                self.assertFalse(es.is_position())
                self.assertFalse(es.is_trade())
                self.assertEqual(es.price, price)
                self.assertRaises(AttributeError, getattr, es, 'price_entry')
                self.assertRaises(AttributeError, getattr, es, 'date_entry')
                self.assertEqual(es.at, es.STOP)

        # test cashflow (need method)

    def test_ExitSignal(self):
        position = EntrySignal(self.aapl, 2, 3, EntrySignal.CLOSE)
        position.volume = 1
        position.price_entry = 580
        position.date_entry = date(2012, 5, 1)
        del position.price
        self.assertFalse(position.is_entry_signal())
        self.assertFalse(position.is_exit_signal())
        self.assertTrue(position.is_position())
        self.assertFalse(position.is_trade())
        es = ExitSignal(position, 4, 5, ExitSignal.OPEN)
        self.assertFalse(es.is_entry_signal())
        self.assertTrue(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertFalse(es.is_trade())
        self.assertEqual(es.at, es.OPEN)
        self.assertEqual(es.stock, self.aapl)
        self.assertEqual(es.method, 2)
        self.assertEqual(es.rule_entry, 3)
        self.assertEqual(es.rule_exit, 5)
        self.assertEqual(es.price_entry, 580)
        self.assertIsNone(es.price)
        self.assertEqual(es.buydelay, 4)
        self.assertFalse(es.is_conditional())
        self.assertTrue(es.is_unconditional())
        self.assertTrue(es.is_for(position))
        es = ExitSignal(position, 4, 5, ExitSignal.STOP, 300)
        self.assertTrue(es.is_conditional())
        self.assertFalse(es.is_unconditional())
        self.assertFalse(es.is_entry_signal())
        self.assertTrue(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertFalse(es.is_trade())
        self.assertTrue(es.is_for(position))
        position2 = EntrySignal(self.aapl, 8, 3, EntrySignal.STOP, 580)
        self.assertFalse(es.is_for(position2))
        position2 = EntrySignal(self.intc, 2, 3, EntrySignal.STOP, 580)
        self.assertFalse(es.is_for(position2))
        position2 = EntrySignal(self.intc, 8, 3, EntrySignal.STOP, 580)
        self.assertFalse(es.is_for(position2))

        es = ExitSignal(position, 4, 5, ExitSignal.OPEN)
        self.assertFalse(es.is_entry_signal())
        self.assertTrue(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertFalse(es.is_trade())
        self.assertTrue(es.execute(date(2012, 6, 8)))
        self.assertEqual(es.price_exit, 571.6)
        self.assertFalse(es.is_entry_signal())
        self.assertFalse(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertTrue(es.is_trade())
        es = ExitSignal(position, 4, 5, ExitSignal.CLOSE)
        self.assertFalse(es.is_entry_signal())
        self.assertTrue(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertFalse(es.is_trade())
        self.assertTrue(es.execute(date(2012, 6, 11)))
        self.assertEqual(es.price_exit, 571.17)
        self.assertFalse(es.is_entry_signal())
        self.assertFalse(es.is_exit_signal())
        self.assertFalse(es.is_position())
        self.assertTrue(es.is_trade())

        testdate = date(2012, 6, 1)
        p1 = 560.12
        p2 = 565.12
        p3 = 570.12
        p4 = 575.12
        p_open = 569.16
        
#        position = EntrySignal(self.aapl, 2, 3, EntrySignal.CLOSE)
#        position.volume = 1
#        position.price_entry = 580
#        position.date_entry = date(2012, 5, 1)
#        del position.price
#        es = ExitSignal(position, 4, 5, ExitSignal.OPEN)
        
        for price, xs, xl in (
                (p1, None,   p_open),
                (p2, p2,     p_open),
                (p3, p_open, p3),
                (p4, p_open, None)):
            # entry at (or below) limit
#            es = ExitSignal(self.aapl, 2, 3, EntrySignal.LIMIT, price)
            es = ExitSignal(position, 4, 5, ExitSignal.LIMIT, price)
            self.assertEqual(es.execute(testdate), bool(xl))
            if bool(xl):
                self.assertFalse(es.is_entry_signal())
                self.assertFalse(es.is_exit_signal())
                self.assertFalse(es.is_position())
                self.assertTrue(es.is_trade())
                self.assertEqual(es.price_exit, xl)
                self.assertRaises(AttributeError, getattr, es, 'price')
                self.assertEqual(es.date_exit, testdate)
                with self.assertRaises(AttributeError):
                    x = es.at
            else:
                self.assertFalse(es.is_entry_signal())
                self.assertTrue(es.is_exit_signal())
                self.assertFalse(es.is_position())
                self.assertFalse(es.is_trade())
                self.assertEqual(es.price, price)
                self.assertRaises(AttributeError, getattr, es, 'price_exit')
                self.assertRaises(AttributeError, getattr, es, 'date_exit')
                self.assertEqual(es.at, es.LIMIT)
            # entry at (or above) stop
#            es = ExitSignal(self.aapl, 2, 3, EntrySignal.STOP, price)
            es = ExitSignal(position, 4, 5, ExitSignal.STOP, price)
            self.assertEqual(es.execute(testdate), bool(xs))
            if bool(xs):
                self.assertFalse(es.is_entry_signal())
                self.assertFalse(es.is_exit_signal())
                self.assertFalse(es.is_position())
                self.assertTrue(es.is_trade())
                self.assertEqual(es.price_exit, xs)
                self.assertRaises(AttributeError, getattr, es, 'price')
                self.assertEqual(es.date_exit, testdate)
                with self.assertRaises(AttributeError):
                    x = es.at
            else:
                self.assertFalse(es.is_entry_signal())
                self.assertTrue(es.is_exit_signal())
                self.assertFalse(es.is_position())
                self.assertFalse(es.is_trade())
                self.assertEqual(es.price, price)
                self.assertRaises(AttributeError, getattr, es, 'price_exit')
                self.assertRaises(AttributeError, getattr, es, 'date_exit')
                self.assertEqual(es.at, es.STOP)


        # test cashflow (need method)
