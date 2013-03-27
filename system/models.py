'''
system/models.py v0.1 120925

Created on 120925

@author: edwin
'''
from __future__ import division
from __future__ import absolute_import

import collections

from django.db import models
#from metasystem.parameters import fields

from utils_python.utils import str2dict

# Only fields from the Results table go here:
# title is used for generating title headings on params
OUTPUT_FORMATS = collections.OrderedDict([
    ('select',
        {'type':'all', 'name':'Result id', 'format':'{}', 
         'title':' '}),
    ('id',
        {'type':'all', 'name':'id', 'format':'{}', 
         'title':'Equity'}),
    ('bookmark',
        {'type':'all', 'name':'Bookmark', 'format':'{}', 
         'title':'Book mark'}),
    ('metasystem',
        {'type':'all', 'name':'MetaSystem', 'format':'{}', 
         'title':'Meta Sys'}),
    ('max_win',
        {'type':'performance', 'name':'Highest gain', 'format':'{:2.1f}%', 
         'verbose': 'Highest profit over all trades.'}),
    ('max_loss',
        {'type':'performance', 'name':'Highest loss', 'format':'-{:2.1f}%', 
         'verbose': 'Highest loss over all trades.'}),
    ('avg_win',
        {'type':'performance', 'name':'Average gain on up trades', 
         'format':'{:2.1f}%', 'verbose': 'Average profit of all positive '
         'trades. Note that this is also the definition of 1R, so when '
         'results are expressed in terms of R, they are divided by this '
         'number'}),
    ('avg_loss',
        {'type':'performance', 'name':'Average loss on down trades', 
         'format':'-{:2.1f}%', 'verbose': 'Average profit of all negative '
         'trades (Note that 0 profit is counted as negative).'}),
    ('trades_pa',
        {'type':'performance', 'name':'Trades per year', 
         'format':'{}', 'verbose': 'Average number of trades per year.'}),
    ('reliability',
        {'type':'performance', 'name':'Reliability', 'format':'{:2.1f}%', 
         'title':'Relia bility', 'verbose': 'The number of positive trades, '
         'expressed as a percentage of the total number of trades (Note: 0 is '
         'not positive).'}),
    ('profit_factor',
        {'type':'performance', 'name':'Profit Factor', 'format':'{:3.2f}', 
         'verbose': 'The sum of the profits of all positive trades divided by '
         'the sum of the losses of all negative trades'}),
    ('expectancy',
        {'type':'performance', 'name':'Expectancy', 'format':'{:2.1f}%', 
         'title':'Expec tancy', 'verbose': 'The expected profit per trade, '
         'given by the sum of all gains and losses divided by the total '
         'number of trades.'}),
    ('days_p_trade',
        {'type':'performance', 'name':'Average number of days per trade', 
         'format':'{:2.1f}', 'verbose': 'Average number of days on the market '
         'per trade. Only one of the entry and exit days is counted, so that '
         'entry and exit on the same day would mean 0 days on the market.'}),
    ('sqn',
        {'type':'performance', 'name':'System Quality Number', 'format':'{:2.1f}', 
         'title':'SQN', 'verbose': 'The System Quality Number is defined as '
         'the expectancy times the square root of the number of trades '
         'divided by the standard deviation of the profits of the trades.'}),
    ('std_dev',
        {'type':'performance', 'name':'Standard Deviation', 'format':'{:2.1f}%', 
         'title':'std dev', 'verbose': 'The standard deviation of the profits '
         'of all trades, expressed in %.'}),
    ('exp_p_day',
        {'type':'performance', 'name':'Expectancy per day on the market', 
         'format':'{:3.2f}%', 'verbose': 'Expectancy divided by the average '
         'number of days per trade.'}),
    ('max_n_win',
        {'type':'performance', 'name':'Maximum number of wins in a row', 
         'format':'{}', 'verbose': 'Highest number of consecutive wins in '
         'the entire trading period.'}),
    ('max_n_loss',
        {'type':'performance', 'name':'Maximum number of losses in a row', 
         'format':'{}', 'verbose': 'Highest number of consecutive losses in '
         'the entire trading period.'}),
    ('true_avg_loss',
        {'type':'performance', 'name':'True average loss on all trades.',
         'format':'{:3.2f}', 'verbose': 'Average profit on all '\
         'negative trades. The average is calculated over all trades.'}),
    ('profit_pa',
        {'type':'performance', 'name':'Profit per year as a sum of profits.',
         'format':'{:3.2f}', 'verbose': 'Sum of the profits of '\
         'all trades divided by the number of years of trading.'}),
    ('profit_ratio',
        {'type':'performance', 'name':'profit_pa / (true_avg_loss * trades_pa)',
         'format':'{:3.2f}', 'verbose': 'Sum of all profits per '\
         'year divided by the expected loss on a single trade times the '\
         'average number of trades per year.'}),
    ('max_pos',
        {'type':'performance', 'name':'Highest number of stocks in the '\
         'portfolio', 'format':'{}', 'verbose': 'The highest number of '\
         'stocks in the portfolio at any point.'}),
    ('ann_profit',
        {'type':'result', 'name':'Annualised profit', 'format':'{:2.1f}%', 
         'verbose': 'The average profit per year over the entire (testing) '
         'period expressed in %.'}),
    ('n_neg_month',
        {'type':'result', 'name':'Average number of down months per year', 
         'format':'{}', 'verbose': 'The average number of calendar months per '
         'year with a negative profit.'}),
    ('sum_neg_mths',
        {'type':'result', 'name':'Sum of losses in down months per year', 
         'format':'{:2.1f}%', 'verbose': 'The average annual total sum of the '
         'losses in negative months.'}),
    ('min_year',
        {'type':'result', 'name':'Lowest gain in any 1y period (sliding)', 
         'format':'{:2.1f}%', 'verbose': 'The lowest profit in any one year '
         'period, expressed in %.'}),
    ('max_year',
        {'type':'result', 'name':'Highest gain in any 1y period (sliding)', 
         'format':'{:2.1f}%', 'verbose': 'The highest profit in any one year '
         'period, expressed in %.'}),
    ('min_month',
        {'type':'result', 'name':'Lowest gain in any calendar month', 
         'format':'{:2.1f}%', 'verbose': 'The lowest profit in any calendar '
         'month, expressed in %.'}),
    ('max_month',
        {'type':'result', 'name':'Highest gain in any calendar month', 
         'format':'{:2.1f}%', 'verbose': 'The highest profit in any calendar '
         'month, expressed in %.'}),
    ('max_dd',
        {'type':'result', 'name':'Highest drawdown', 'format':'-{:2.1f}%', 
         'verbose': 'The maximum drawdown over any one year period. The value '
         'is a percentage, e.g. 20% if the lowest low after a high was 80% of '
         'the high.'}),
    ('min_dd_ratio',
        {'type':'result', 'name':'Lowest profit / drawdown ', 
         'format':'{:3.2f}', 'verbose': 'The lowest ratio of profit/max_dd in '
         'any one year period.'}),
])


def get_parameter_list(type_):
    '''
    Returns a list with all parameters from <OUTPUT_FORMATS> for which [type]
    is <type_>
    '''
    return [t for t, d in OUTPUT_FORMATS.items() if d['type'] == type_]


class Bookmark(models.Model):
    '''
    This table holds sections which can contain bookmarked systems.
    '''
    section = models.CharField(max_length=80)
    comments = models.TextField()


class System(models.Model):
    '''
    A system is a set of parameters for a metasystem.
    This table holds performance results from all metasystems.
    A system can be run real-time
    Systems are read-only.
#TODO: replace most of the decimalfields with floats to prevent overflow issues
    '''
    metasystem = models.ForeignKey('metasystem.MetaSystem')
    params = models.TextField() # actual system parameters
    active = models.BooleanField(default=True) # runs real time or not
    enddate = models.DateField() #necessary for real-time?
    bookmark = models.ForeignKey(Bookmark, null=True, default=None)
    # performance parameters:
    max_win = models.DecimalField(max_digits=4, decimal_places=1) # in % >0
    max_loss = models.DecimalField(max_digits=4, decimal_places=1) # in % >0
    avg_win = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True) # in % >0
    avg_loss = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True) # in % >0
    trades_pa = models.PositiveIntegerField()
    reliability = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True) # in % >0
    profit_factor = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    expectancy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # in %
    days_p_trade = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True) # > 0
    sqn = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True) # -
    std_dev = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True) # in %
    exp_p_day = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True) # in %
    max_n_win = models.PositiveIntegerField() # max no of consecutive wins
    max_n_loss = models.PositiveIntegerField() # max no of consecutive losses
    true_avg_loss = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True) # in % > 0
    profit_pa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # sum of profits per year (not compound)
    profit_ratio = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True) # profit_pa / tal
    max_pos = models.IntegerField(null=True, blank=True) # max number of positions
    # result parameters:
    ann_profit = models.DecimalField(max_digits=4, decimal_places=1) # in %
    n_neg_month = models.DecimalField(max_digits=3, decimal_places=1) # mths/y
    sum_neg_mths = models.DecimalField(max_digits=4, decimal_places=1) # in %/y
    min_year = models.DecimalField(max_digits=4, decimal_places=1) # in %
    max_year = models.DecimalField(max_digits=4, decimal_places=1) # in %
    min_month = models.DecimalField(max_digits=4, decimal_places=1) # in %
    max_month = models.DecimalField(max_digits=4, decimal_places=1) # in %
    max_dd = models.DecimalField(max_digits=3, decimal_places=1) # in % >0
    min_dd_ratio = models.DecimalField(max_digits=5, decimal_places=2) # ann_profit / dd


    def get_params(self, method_from=None):
        '''
        Returns a dict with all parameters. If method_from and _to are 
        specified, the method id in the unique parameter name will be translated.
        '''
        param_dict = {}
        for key, value in str2dict(self.params).items():
            key1, unused, key2 = key.partition(' {}'.format(method_from.id))
            param_dict['{} {}'.format(key1, key2)] = value
        return param_dict


    @classmethod
    def delete_duplicates(cls, metasystem):
        systems = cls.objects.filter(metasystem=metasystem)
        for params in systems.values_list('params', flat=True).distinct():
            systems.filter(pk__in=systems.filter(params=params).\
                                  values_list('id', flat=True)[1:]).delete()

    def __unicode__(self):
        return '{}'.format(self.id)
