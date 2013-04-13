'''
utils_python/utils.py v0.1 120815

Created on 120815

@author: edwin

This module contains generic python functions that are not django related.
'''
from __future__ import division
from __future__ import absolute_import

import datetime
import ast
import operator


def datestr2date(date_str):
    '''
    Returns a datetime.date object, extracted from a string <date_str>.
    '''
    valid_formats = '''The following date formats are valid:
    yyyymmdd  yymmdd
    d-m-yy    d-m-yyyy
    m/d/yy    m/d/yyyy
Where in the latter 4 formats m and d may be 1 or 2 digits which may include
a leading zero.
In case of a 2-digit year, it is assumed to be after 2000'''
    if '/' in date_str:
        try:
            m, d, y = date_str.split('/')
        except:
            raise ValueError('Date {} must have no or exactly 2 slashes. {}'.
                    format(date_str, valid_formats))
    elif '-' in date_str:
        try:
            d, m, y = date_str.split('-')
        except:
            raise ValueError('Date {} must have no or exactly 2 dashes. {}'.
                    format(date_str, valid_formats))
    elif len(date_str) == 8 or len(date_str) == 6:
        d = date_str[-2:]
        m = date_str[-4:-2]
        y = date_str[:-4]
    else:
        raise ValueError('Date format not recognised. {}'.format(valid_formats))
    year = int(y)
    if year < 100:
        year += 2000
    try:
        return datetime.date(year, int(m), int(d))
    except ValueError:
        raise ValueError('Invalid date {}. {}'.format(date_str, valid_formats))


def date2datestr(date):
    '''
    Returns a string of the format yyyymmdd that represents the datetime.date
    object <date>.
    '''
    return date.strftime('%Y%m%d')


def compress(in_list):
    '''
    Takes a list of tuples of 2 ints and returns a list of bytes where each
    byte is a concatenation of the first int in 5 bits and the second int in
    3 bits.
    '''
#note: the following would be quicker, but no error checking...
#    return [x + 32*y for (x, y) in in_list]
    out_list = []
    for x,y in in_list:
        if x < 0 or x > 31 or not isinstance(x, int):
            raise ValueError('x must be a 5 bit int, but it is {}'.format(x))
        if y < 0 or y > 7 or not isinstance(y, int):
            raise ValueError('y must be a 3 bit int, but it is {}'.format(y))
        out_list.append(x + 32*y)
    return out_list


def decompress(in_list):
    '''
    Takes a list of ints (bytes) Returns a list of tuples of 2 ints. The first
    int is represented by the first 5 bits of the input byte, the second int
    by the last 3 bits of the input byte 
    '''
#note: the following would be quicker, but no error checking...
#    return [(x % 32 , x // 32) for x in in_list]
    out_list = []
    for x in in_list:
        if x < 0 or x > 255 or not isinstance(x, int):
            raise ValueError('x must be an 8 bit int, but it is {}'.format(x))
        out_list.append((x % 32 , x // 32))
    return out_list


def encode(int_list):
    '''
    Turns a list of integers (0..255) into a string of bytes.
    '''
    return ''.join([chr(i) for i in int_list])


def decode(string):
    '''
    Turns a string of bytes into a list of integers.
    '''
    return [ord(c) for c in string]


def round_by_format(float_number, fmt):
    '''
    Rounds a float using the supplied printing format string. Any characters
    outside { and } are stripped.
    '''
    while fmt[0] != '{': 
        fmt = fmt[1:]
    while fmt[-1] != '}':
        fmt = fmt[:-1]
    string = fmt.format(float_number)
    return float(string)


def is_weekday(date):
    '''
    Returns a boolean that indicates if date is a weekday.

    Args:
        date (datetime or datetime.date)
    Returns:
        (boolean)
    Raises:
        something ivalid date bla bla
    '''
    return True if date.weekday() < 5 else False


def is_weekend(date):
    '''
    Returns a boolean that indicates if date is a weekday.

    Args:
        date (datetime or datetime.date)
    Returns:
        (boolean)
    Raises:
        something ivalid date bla bla
    '''
    return not is_weekday(date)


def previous_weekday(date):
    '''
    Return the last weekday before date
    '''
    weekday = date.weekday()
    if weekday == 0:
        n_days = 3
    elif weekday == 6:
        n_days = 2
    else:
        n_days = 1
    return date - datetime.timedelta(days=n_days)


def next_weekday(date):
    '''
    Return the first weekday after date
    '''
    n_days = 7 - date.weekday()
    if n_days > 3:
        n_days = 1
    return date + datetime.timedelta(days=n_days)


def int_factor(float1, float2):
    '''
    Returns integer division if float1 > float 2, and an int fraction if not.
    '''
    if float1 > float2:
        divider = int(round(float1/float2))
    elif float1 < float2:
        factor = round(float2/float1)
        divider = 1 / factor if factor > 1 else 1
    else:
        divider = 1
    return divider


def last_year(date_):
    '''
    Returns the same date 1 year ago.
    '''
    day = 28 if date_.month == 2 and date_.day == 29 else date_.day
    return datetime.date(date_.year-1, date_.month, day)


def random_string(length=8, charset=None):
    '''
    Returns a string of length random characters selected from charset.
    '''
    import random, string
    if not charset:
        charset = string.letters + string.digits
    return ''.join(random.choice(charset) for unused in xrange(length))


def safe_eval(string):
    '''
    Evaluates string and returns the represented object, if anything goes wrong
    None is returned instead.
    '''
    try:
        some_object = ast.literal_eval(string)
    except:
        some_object = None
    return some_object


def str2dict(dict_string):
    '''
    Returns a dict if dict_string is a valid dict, None otherwise.
    '''
    dict_out = safe_eval(dict_string)
    if not isinstance(dict_out, dict):
        dict_out = None
    return dict_out


def str2tuple(tuple_string):
    '''
    Returns a tuple if tuple_string is a valid tuple, None otherwise.
    '''
    tuple_out = safe_eval(tuple_string)
    if not isinstance(tuple_out, tuple):
        tuple_out = None
    return tuple_out


def get_dict_values(dict_string):
    '''
    Returns a list with the values of <dict_string>, where <dict_string> is a 
    string representation of a dict.
    The values are sorted by their keys in alphabetic order.
    '''
    params = str2dict(dict_string)
    return (params[k] for k in sorted(params))
#    return ('{}'.format(params[k]) for k in sorted(params))


def get_dict_keys(dict_string):
    '''
    Returns a list with the keys of <dict_string>, where <dict_string> is a 
    string representation of a dict.
    The keys are sorted in alphabetic order.
    '''
    return sorted(k for k in str2dict(dict_string))


def eval_conditions(conditions=None, data={}):
    '''
    Evaluates <conditions> and returns Boolean value.

    The format of <conditions> is a tuple:
        (arg1, op, arg2)
    where:
        arg1, arg2 can be numerical values, strings or condition tuples
        op is a valid operator from the operator module
    If arg is a string, and the string is a key in <data> it is treated as
    a variable with value data[arg].
    If no conditions are specified True is returned.
    Note: empty/0 values do *not* equate to booleans
    '''
#CONSIDER: implement addition/subtraction/multiplication/division
    if not conditions:
        return True
    if isinstance(conditions, str) or isinstance(conditions, unicode):
        conditions = str2tuple(conditions)
    if not isinstance(conditions, tuple) or not len(conditions) == 3:
        raise TypeError('conditions must be a tuple with 3 items.')
    arg1 = conditions[0]
    op = conditions[1]
    arg2 = conditions[2]
    if arg1 in data:
        arg1 = data[arg1]
    elif isinstance(arg1, tuple):
        arg1 = eval_conditions(arg1, data)
    if arg2 in data:
        arg2 = data[arg2]
    elif isinstance(arg2, tuple):
        arg2 = eval_conditions(arg2, data)
    if op in ('lt', 'le', 'eq', 'ne', 'ge', 'gt'):
        if not (type(arg1) in (float, int) and type(arg2) in (float,int)) and \
                type(arg1) != type(arg2):
            raise ValueError('both arguments must have the same type {}, {}'.\
                    format(arg1, arg2))
    elif op in ('and', 'or'):
        if not isinstance(arg1, bool) or not isinstance(arg2, bool):
            raise ValueError('boolean operator {} needs boolean arguments {},'\
                    ' {}'.format(op, arg1, arg2))
        op += '_'
    else:
        raise ValueError('operator {} not supported', op)
    return getattr(operator, op)(arg1, arg2)


def div(numerator, denominator):
    '''
    Returns fraction of numerator and denominator.
    This is not mathematically correct, but practically OK.
    If the denominator is 0 the result will be 0 if the numerator = 0 or
    'inf' otherwise.
    Note that 'inf' can be printed with '{:4.2f}'.format(float(x)) 
    '''
    if numerator == 0:
        return 0.
    elif denominator == 0:
#        return float('inf')
        return None
    else:
        return numerator/denominator
#        return float(numerator) / float(denominator)
