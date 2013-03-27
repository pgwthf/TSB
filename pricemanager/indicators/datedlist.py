'''
datedlist.py v0.1 120702

Created on 11/05/2012

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import datetime


class DatedList(list):
    '''
    This is a standard Python list, but instead of an int, it uses a
    (datetime)date as its index. This index is stored in the list <self.date>
    and must be the same length as the list of values.
    The list can be sliced in the following ways:
    datelist[startdate:enddate] returns the list of values from startdate to 
        enddate, including both startdate and enddate (if available)
    datelist[date:length] (where <length> is an int) returns a list of 
        <length> values, starting at <date>. If <length> is a negative number
        a list is returned from <length> items before <date> to <date>
    datelist[date] returns the value on <date> or the most recent value
        before <date> or the first <date> of <date> is earlier than that.
    datelist.on(date) returns the value on <date> or None if no value is
        available on <date>
    '''


    def __init__(self, values, dates):
        '''
        Constructor takes a list of dates and a list of values as input. These
        two lists must have equal lengths.
        '''
        if len(values) != len(dates):
            raise ValueError, 'value and date lists must be the same length'
        self.dates = dates
        list.__init__(self, values)


    def __contains__(self, date):
        '''
        Returns True if date is in self.dates.
        '''
        return date in self.dates


    def __getitem__(self, date):
        '''
        Retrieve an item from the list:
            datedlist[date]
        Slicing is supported. If slices are used, a standard Python list is
        returned. The following slicing operations are supported:

            datedlist[date_from : date_to]
                NOTE: unlike slicing of a standard list, <date_to> is inclusive!

            datedlist[date : n_days]
                where n_days < 0 returns a list of days *before* <date> and 
                n_days > 0 a list of n_days *after* <date>.

            datedlist[i_from, i_to]
                standard python slicing works, e.g.:
                    x[0] is the first item in the list
                    x[-1] is the last item in the list
        '''
        if isinstance(date, slice):
            if isinstance(date.start, datetime.date):
                i_start = self.index(date.start)
                if isinstance(date.stop, datetime.date):
                    i_stop = min(self.index(date.stop) + 1, len(self.dates))
                elif isinstance(date.stop, int):
                    if not date.stop:
                        raise ValueError, 'slice[date:0] has no meaning'
                    if date.stop < 0:
                        i_start += 1
                    i_stop = i_start + date.stop
                    i_start, i_stop = min(i_start, i_stop), max(i_start, 
                                                                        i_stop)
                    i_start = max(i_start, 0)
                    i_stop = min(i_stop, len(self.dates))
                else:
                    raise TypeError('If first argument of slice is datetime '\
                            'object, the second must be datetime or int.')
            elif isinstance(date.start, int) and isinstance(date.stop, int):
                i_start, i_stop = date.start, date.stop
            else:
                raise TypeError('Slice with two arguments must be [int:int], '\
                        '[datetime:datetime] or [datetime:int]')
            return [list.__getitem__(self, i) for i in range(i_start, i_stop)]
        elif isinstance(date, datetime.date):
            index = self.index(date)
            return list.__getitem__(self, index)
        elif isinstance(date, int):
            return list.__getitem__(self, date)
        else:
            raise TypeError('Invalid argument type.')


    def index(self, date):
        '''
        Returns the index of <date> in self.dates.
        If <date> is not in self.dates the index of the highest date that is
        earlier than <date> is returned.
        If <date> is earlier than the earliest date in self.dates the return
        value is 0
        If <date> is later than the latest date in self.dates the return value
        is the index of the most recent date.
        '''
        if date in self.dates:
            index = self.dates.index(date)
        elif date < self.dates[0]:
            index = 0
        elif date > self.dates[-1]:
            index = len(self.dates) - 1
        else:
            while date not in self.dates:
                date -= datetime.timedelta(days=1)
            index = self.dates.index(date)
        return index


    def latest_date_before(self, date):
        '''
        returns the latest date from self.dates that is <= <date>
        '''
        return self.dates[self.index(date)]


    def offset(self, date, offset):
        '''
        Return the value on <date> + offset days.
        If the target index lies beyond the list, the value at 0 or len(list)
        is returned.
        '''
        index = self.index(date) + offset
        index = max(index, 0)
        index = min(index, len(self.dates) - 1)
        return list.__getitem__(self, index)


    def delta(self, fromdate, todate):
        '''
        Return the number of dates in <self.dates> between <fromdate> and
        <todate>.
        '''
        return self.index(todate) - self.index(fromdate)


    def get_date(self, date, n_days=0):
        '''
        Return the date n_days after (or before if n_days < 0) <date>
        If n_days is not set it returns the latest date before or on <date> that
        is in the database.
        '''
        index = self.index(date) + n_days
        index = max(0, index)
        index = min(index, len(self.dates) - 1)
        return self.dates[index]


    def get_dates(self, fromdate, todate):
        '''
        Return a list of dates from <self.dates> between <fromdate> and <todate>
        (inclusive)
        '''
        i_from = self.index(fromdate)
        i_to = self.index(todate)
        return self.dates[i_from:i_to + 1]


    def on(self, date):
        '''
        Return the value on <date> or None <date> is not in <self.dates>.
        NOTE that this behaves differently from datedlist[<date>] if <date> is
        *not* in the date list.
        '''
        if date in self.dates:
            index = self.dates.index(date)
            return list.__getitem__(self, index)
        else:
            return None


    def append(self, (date, value)):
        '''
        Appends a date, value tuple to the list.
        '''
        if isinstance(date, datetime.date):
            self.dates.append(date)
            super(DatedList, self).append(value)
        else:
            raise ValueError('append needs a (date, value) tuple')


    def extend(self, extension):
        '''
        Appends <extension> to the DatedList, <extension> must also be a 
        DatedList.
        '''
        if isinstance(extension, DatedList):
            self.dates.extend(extension.dates)
            super(DatedList, self).extend(extension)
        else:
            raise ValueError('the argument to extend must be a DatedList')


    def as_list(self):
        '''
        Returns a standard Python list with values, dates are ignored.
        '''
        return self[:]

