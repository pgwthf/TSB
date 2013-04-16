"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from __future__ import division
from __future__ import absolute_import

from django.test import TestCase

from utils_python.utils import *

class SimpleTest(TestCase):

    def test_compress(self): # compress and decompress
        for i5,i3 in ((-1,0), (0,-1,), (-1,-1), (31,8), (32,7), (32,8), 
                      (1.5, 2), (2, 3.1)):
            self.assertRaises(ValueError, compress, [(i5, i3),])
        for i in (-1, 256, 1.3):
            self.assertRaises(ValueError, decompress, [i,])
        list_in = [(0,0), (31,0), (0,7), (31,7)]
        list_out = [0, 31, 224, 255]
        self.assertEqual(compress(list_in), list_out)
        self.assertEqual(decompress(list_out), list_in)

    def test_encode(self): # encode and decode
        self.assertEqual(encode([0]), '\x00')
        self.assertEqual(encode([255]), '\xFF')
        for i in (-1, 256):
            self.assertRaises(ValueError, encode, [i,])
        self.assertRaises(TypeError, encode, [1.7,])
        for c in (1.7, '3'):
            self.assertRaises(TypeError, encode, c)
        self.assertEqual(decode('\x00'), [0,])
        self.assertEqual(decode('\xFF'), [255,])
        for c in (8, 1.7, [1,2,3]):
            self.assertRaises(TypeError, decode, c)

    def test_round_by_format(self):
        self.assertEqual(round_by_format(1.234, '{:2.1f}'), 1.2)
        self.assertEqual(round_by_format(1.276, '{:2.1f}'), 1.3)
        self.assertEqual(round_by_format(1.251, '{:2.1f}'), 1.3)
        self.assertEqual(round_by_format(1.249, '{:2.1f}'), 1.2)
        self.assertEqual(round_by_format(1.249, '{:3.2f}'), 1.25)
        self.assertEqual(round_by_format(1, '{:3.2f}'), 1.)
        self.assertEqual(round_by_format(1.49, '{:3.0f}'), 1.)
        self.assertEqual(round_by_format(1.50, '{:3.0f}'), 2.)
        self.assertEqual(round_by_format(1.251, '{:2.1f}%'), 1.3)
        self.assertEqual(round_by_format(1.251, '-${:2.1f}'), 1.3)

    def test_previous_weekday(self):
        for day1, day2 in ((8,7), (9,7), (10,7), (11,10), (12,11), (13,12), 
                           (14,13), (15,14), (16,14), (17,14)):
            self.assertEqual(previous_weekday(datetime.date(2000,1,day1)), 
                                                    datetime.date(2000,1,day2))

    def test_next_weekday(self):
        for day1, day2 in ((6, 7), (7, 10), (8,10), (9,10), (10,11), (11,12), 
                           (12,13), (13,14), (14,17), (15,17), (16,17)):
            self.assertEqual(next_weekday(datetime.date(2000,1,day1)), 
                                                    datetime.date(2000,1,day2))

    def test_int_factor(self):
        self.assertEqual(int_factor(1., 1.), 1)
        self.assertEqual(int_factor(3., 1.), 3)
        self.assertEqual(int_factor(3.4, 1.), 3)
        self.assertEqual(int_factor(3.5, 1.), 4)
        self.assertEqual(int_factor(3., 0.9), 3)
        self.assertEqual(int_factor(3., 1.2), 3)
        self.assertEqual(int_factor(1., 3.), 1./3.)
        self.assertEqual(int_factor(1., 3.4), 1./3.)
        self.assertEqual(int_factor(1., 3.5), 1./4.)
        self.assertEqual(int_factor(0.9, 3.), 1./3.)
        self.assertEqual(int_factor(1.2, 3.), 1./3.)


    def test_last_year(self):
        self.assertEqual(last_year(datetime.date(2000,3,29)), 
                                    datetime.date(1999,3,29))
        self.assertEqual(last_year(datetime.date(2000,2,27)), 
                                    datetime.date(1999,2,27))
        self.assertEqual(last_year(datetime.date(2000,2,29)), 
                                    datetime.date(1999,2,28))


    def test_random_string(self):
        # test default length
        self.assertEqual(len(random_string()), 8)
        # test length setting
        for length in xrange(5,10):
            self.assertEqual(len(random_string(length)), length)
        # test uniqueness - could theoretically fail, but very unlikely
        testlist = (random_string() for unused in xrange(10))
        self.assertEqual(len(set(testlist)), 10)
        # test charset - could theoretically fail, but very unlikely
        charset = 'ABC'
        abc = random_string(100, charset)
        self.assertEqual(set(abc), {'A', 'B', 'C'})


    def test_safe_eval(self):
        self.assertEqual(safe_eval('15'), 15)
        self.assertEqual(safe_eval('8.45'), 8.45)
        self.assertEqual(safe_eval('(1,2)'), (1,2))
        self.assertEqual(safe_eval('[1,2,3]'), [1,2,3])
        self.assertEqual(safe_eval("{'a':1, 4:'asdf'}"), {'a':1, 4:'asdf'})
        self.assertIsNone(safe_eval('1y3'))
        self.assertIsNone(safe_eval('[3,1'))
        self.assertIsNone(safe_eval('import sys'))
        self.assertIsNone(safe_eval('raise SystemExit'))
        self.assertIsNone(safe_eval(''))


    def test_str2dict(self):
        self.assertEqual(str2dict("{'a':1, 4:'asdf'}"), {'a':1, 4:'asdf'})
        self.assertIsNone(str2dict("{'a':1 4:'asdf'}"))
        self.assertIsNone(str2dict('raise SystemExit'))
        self.assertIsNone(str2dict('(1,2,3)'))

    def test_get_dict_values(self): # get_dict_keys and get_dict_values
        dict_string = '{"a":1, 2:"3"}'
        self.assertEqual(tuple(get_dict_values(dict_string)), ('3', 1))
        self.assertRaises(ValueError(get_dict_values, 'asdf'))
        self.assertEqual(tuple(get_dict_keys(dict_string)), (2, 'a'))
        self.assertRaises(ValueError(get_dict_keys, 'asdf'))

    def test_eval_conditions(self):
        self.assertTrue(eval_conditions(None))
        self.assertRaises(TypeError, eval_conditions, 'a')
        self.assertRaises(TypeError, eval_conditions, (1,2,3,4))

        # simple conditions
        for conditions in ( (2, 'gt', 1), 
                            ('a', 'eq', 'a'),
                            ('a', 'lt', 'b'),
                            (2., 'gt', 1),
                            (1, 'eq', 1.),
                            (True, 'eq', True),
                            (True, 'or', False),
                            ):
            self.assertTrue(eval_conditions(conditions), conditions)
        for conditions in ( (2, 'lt', 1), 
                            ('a', 'eq', 'b'),
                            (3, 'gt', 4.2),
                            (True, 'eq', False),
                            (True, 'and', False),
                            ):
            self.assertFalse(eval_conditions(conditions), conditions)
        for conditions in ( ('a', 'eq', 1),
                            (True, 'eq', 3),
                            (3, 'and', True),
                            (1, 'abc', 2),
                            ):
            self.assertRaises(ValueError, eval_conditions, conditions)

        # simple conditions with data
        for conditions, data in ( (('x', 'lt', 2), {'x': 1}),
                                  (('y', 'eq', 1.3), {'y': 1.3}),
                                  (('y', 'and', True), {'y': True}),
                                 ):
            self.assertTrue(eval_conditions(conditions, data), conditions)
        for conditions, data in ( (('x', 'lt', 1), {'x': 2}),
                                  (('x', 'eq', 1), {'x': 1.1}),
                                  ((True, 'and', 'abc'), {'abc': False}),
                                 ):
            self.assertFalse(eval_conditions(conditions, data), conditions)
        for conditions, data in ( (('x', 'gt', 1), {'y': 2}),
                                  (('x', 'abc', 1), {'abc': 'and'}),
                                 ):
            self.assertRaises(ValueError, eval_conditions, conditions, data)

        # complex conditions
        for conditions, data in ( ((True, 'and', ('x', 'eq', 2)), {'x': 2}),
                                  (('x', 'eq', (1, 'ne', 'y')), {'x': True, 'y': 2}),
                                 ):
            self.assertTrue(eval_conditions(conditions, data), conditions)
        for conditions, data in ( ((('x', 'lt', 1), 'and', (2, 'lt', 'y')), {'x': 2, 'y': 1}),
                                 ):
            self.assertFalse(eval_conditions(conditions, data), conditions)
        for conditions, data in ( ((2, ('lt' , 'or', 'gt'), 1), {}),
                                  (('x', 'abc', 1), {'abc': 'and'}),
                                 ):
            self.assertRaises(ValueError, eval_conditions, conditions, data)


    def test_div(self):
        self.assertEqual(div(0,0), 0)
        self.assertEqual(div(0,1), 0)
        self.assertEqual(div(1,0), float('inf'))
        self.assertEqual(div(2,1), 2.)
        self.assertEqual(div(2,1.25), 1.6)
        self.assertEqual(div(2,0.5), 4.)
        self.assertEqual(div(0.5,0.25), 2.)
        self.assertEqual(div(0.2, 0.1), 2.)
