'''
system/forms.py v0.1 121012

Created on 121012

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django import forms

from pricemanager.models import Stock


class DateForm(forms.Form):
    '''
    For providing start and enddates
    '''
    startdate = forms.DateField()
    enddate = forms.DateField()


class ChartSettingsForm(forms.Form):
    n_ma = forms.IntegerField(min_value=1, max_value=250)
    n_atr = forms.IntegerField(min_value=1, max_value=250)
    trend_zones = forms.IntegerField(min_value=2, max_value=3)
    vol_zones = forms.IntegerField(min_value=2, max_value=3)
    trend_th1 = forms.DecimalField(min_value=-10, max_value=10, decimal_places=1, max_digits=3)
    trend_th2 = forms.DecimalField(min_value=-10, max_value=10, decimal_places=1, max_digits=3)
    vol_th1 = forms.DecimalField(min_value=0, max_value=10, decimal_places=1, max_digits=3)
    vol_th2 = forms.DecimalField(min_value=0, max_value=10, decimal_places=1, max_digits=3)

    def __init__(self, *args, **kwargs):
        super(ChartSettingsForm, self).__init__(*args, **kwargs)
        self.fields['symbol'] = forms.ModelChoiceField(
                                                queryset=Stock.objects.all())
#                        queryset=Stock.objects.filter(name__startswith='^'))
