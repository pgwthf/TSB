'''
pricemanager/yahoo.py v0.1 120815

Created on 120815

@author: edwin

Functions for downloading stock prices from Yahoo.
There are two different use cases:
    * download the latest prices ('todays prices')
    * download historical prices
Yahoo has a different web interface for these two scenarios, hence the two 
functions: download_today and download_history.
'''
#CONSIDER: go to other data source later, e.g. eoddata.com

from __future__ import division
from __future__ import absolute_import

import datetime
from urllib import urlopen
from csv import reader
from operator import itemgetter

from TSB.utils import notify_admin


def download_today(stock_list):
    '''
    Download the latest stock prices and return them as a list

    Incoming data is csv format without a header. Each line in the input 
    contains the following fields (in this order):
        stock, date, open, range, close, volume
    where range is a string of the format: 'open - close'

    The return value of this function is a list of dicts with the row headers
    as keys. Types are set to datetime for date, int for volume and float for 
    all prices.
    The keys of the dicts are:
        stock, date, open, high, low, close, volume
    Exceptions to this are:
        * If a stock was not found on Yahoo, its dict will only have 1 key
            (stock)
        * If a stock did not have valid data (yet), its dict will only have 2 
            keys: (stock, date)
    '''
    if not stock_list:
        text = 'WARNING: empty stock_list on {}'.format(datetime.date.today())
        notify_admin(text)
        return None
    data = []
    max_num_stocks = 200 # yahoo limitation
    sub_lists = [stock_list[i:i+max_num_stocks] for i in 
                                    range(0,len(stock_list),max_num_stocks)]
    for sub_list in sub_lists:
        url = _yahoo_today_url(sub_list)
        print url
        response = urlopen(url)
        yahoo_data = reader(response, delimiter=',')
        header = ('stock', 'date', 'open', 'range', 'close', 'volume')
        for row, stock in zip(yahoo_data, sub_list):
            values = {'stock': stock}
            for key, value in zip(header,row):
                print key, value
                if 'N/A' in value:
                    values = {'stock': stock, 'date': values.get('date', 'N/A')}
                    break
                if key == 'date':
                    (m, d, y) = [int(x) for x in value.split('/')]
                    values['date'] = datetime.date(y, m, d)
                elif key == 'range':
                    lo, hi = value.split(' - ')
                    values['low'] = float(lo)
                    values['high'] = float(hi)
                elif key == 'volume':
                    values['volume'] = int(value)
                elif key == 'stock':
                    if value != stock.name:
                        values = {'stock': stock}
                        break
                elif key == 'open' or key == 'close':
                    values[key] = float(value)
                else:
                    raise KeyError
            data.append(values)
    return data


def download_history(stock, fromdate, todate):
    '''
    Download historical stock prices and store them in the database.

    Download prices for <stock> from <fromdate> to <todate> from Yahoo and 
    store them in the database.
    The prices and volume are adjusted for share splits but not for dividends
    and other adjustments.
    Incoming data is csv format with the first row as a header.

    This function returns a list of dicts with the row headers as keys. Types 
    are set to datetime for date, int for volume and float for all prices. The
    stock instance is added to each dict.

    Returns None if no valid response was received from Yahoo.
    '''
    url = _yahoo_history_url(stock.name, fromdate, todate)
    print url
    response = urlopen(url)
    yahoo_data = reader(response, delimiter=',')
    header = [d.lower().replace(' ', '_') for d in yahoo_data.next()]
    if '<' in header[0]: 
        return None
    data = []
    for row in yahoo_data:
        values = {'stock': stock}
        for key, value in zip(header,row):
            if key == 'date':
                (y, m, d) = [int(x) for x in value.split('-')]
                values['date'] = datetime.date(y, m, d)
            elif key == 'adj_close':
                values['adj_close'] = float(value)
            elif key == 'volume':
                values['volume'] = int(value)
            else:
                values[key] = float(value)
        data.append(values)
    if not data:
        text = 'ERROR: {} not found or invalid date range'.format(stock.name)
        notify_admin(text)
        return
    warning = _unsplit(data) #modifies data!
    if warning:
        text = 'WARNING for {}:\n'.format(stock.name, '\n -'.join(warning))
        notify_admin(text)
    return data


def _yahoo_today_url(stock_list):
    '''
    Return a string that is the url for retrieving daily prices from the Yahoo 
    site.
    <stock_list> is a Python list that contains stock instances.
    '''
    if not len(stock_list):
        return None
    stock_string = '+'.join((s.name for s in stock_list))
    return 'http://download.finance.yahoo.com/d/quotes.csv?s={}&f=sd1oml1v'.\
                                                        format(stock_string)


def _yahoo_history_url(stock_name, fromdate, todate):
    '''
    Return a string that is a url for retrieving historical prices from the 
    Yahoo site.
    '''
    (y_from, m_from, d_from) = (fromdate.year, fromdate.month-1, fromdate.day)
    (y_to, m_to, d_to) = (todate.year, todate.month-1, todate.day)
    return 'http://ichart.finance.yahoo.com/table.csv?s={}&amp;a={}&amp;b={}' \
            '&amp;c={}&amp;d={}&amp;e={}&amp;f={}&amp;g=d&amp;ignore=.csv'. \
            format(stock_name, m_from, d_from, y_from, m_to, d_to, y_to)


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


def _unsplit(data):
    '''
    Traverses prices back in time and corrects for (reverse) stock splits.

    Only stock splits are compensated for, dividends and other corrections
    are not affected.
    Returns warning messages if the split_factor was excessively low or high.
    '''
    warning = []
    split_factor = 1
    next_adjust = 1
    #NOTE: the following line 'breaks' the link with incoming data, BUT that
    #    is OK, because the items in the list do still change.
    data = sorted(data, key=itemgetter('date'), reverse=True)
    stock = data[0]['stock']
    for values in data:
        if values['stock'] != stock:
            raise ValueError('unsplit must only process one stock at a time')
        today_adjust = values['close'] / values.pop('adj_close')
        factor = int_factor(next_adjust, today_adjust)
        split_factor *= factor
        next_adjust = today_adjust
        if factor < 0.09 or split_factor > 11.:
            warning.append('split_factor={:4.2f} out of range on {}'.format(
                                                factor, values['date']))
        if abs(split_factor - 1) > 0.01:
            for key in ('open', 'high', 'low', 'close'):
                values[key] *= split_factor
            values['volume'] = int(values['volume'] / split_factor)
    return warning
