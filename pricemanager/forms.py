'''
pricemanager/forms.py v0.1 120821

Created on 120821

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.forms import ModelForm, Form
from django import forms
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper, \
                                                                AdminDateWidget
from django.forms.models import modelformset_factory

from pricemanager.models import Pool, Stock, StockPoolDates

from channel.models import Channel

class PoolForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['startdate'].widget = AdminDateWidget()
        self.fields['enddate'].widget = AdminDateWidget()
        self.fields['description'].widget = forms.Textarea(
                                                attrs={'cols': 40, 'rows': 2})
        self.fields['index'] = forms.ModelChoiceField(
                        queryset=Stock.objects.filter(name__startswith='^'))

    class Meta:
        model = Pool
        exclude = ('members')


class MemberForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        self.fields['stock'] = forms.ModelChoiceField(queryset=
                Stock.objects.exclude(name__startswith='^').order_by('name'))
        rel = StockPoolDates._meta.get_field('stock').rel #@UndefinedVariable
        self.fields['stock'].widget = RelatedFieldWidgetWrapper(
                self.fields['stock'].widget, rel, self.admin_site) 

    class Meta:
        model = StockPoolDates


MemberFormset = modelformset_factory(StockPoolDates, form=MemberForm, 
                                                        can_delete=True)

class StockChartForm(Form):
    startdate = forms.DateField(required=False)
    enddate = forms.DateField(required=False)
    lookback_period = forms.ChoiceField(choices=Channel.LOOKBACK_CHOICES)


class DateRangeForm(Form):
    startdate = forms.DateField(label='from')
    enddate = forms.DateField(label='to')
    
    def __init__(self, *args, **kwargs):
        super(DateRangeForm, self).__init__(*args, **kwargs)
        self.fields['startdate'].widget.attrs['size'] = 10
        self.fields['enddate'].widget.attrs['size'] = 10
