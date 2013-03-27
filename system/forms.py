'''
system/forms.py v0.1 121012

Created on 121012

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django import forms
from django.forms import Form
from django.forms.models import formset_factory

from django.contrib.admin.widgets import AdminDateWidget

from metasystem.models import MetaSystem

from system.models import OUTPUT_FORMATS, Bookmark

COMP_CHOICES = (('gt', '>'),('gte', '>='),('lt', '<'),('lte', '<='))
COMP_REVERSE = {'lte': 'gt', 'gte': 'lt', 'lt': 'gte', 'gt': 'lte'}


def get_filter_choices():
    '''
    Returns a list with choices for the filter parameter name.
    '''
    choices = []
    for key, params in OUTPUT_FORMATS.items():
        if params['type'] == 'performance':
            choices.append((key, '{} - {}'.format(key, params['name'])))
    return choices


class FilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.fields['parameter'] = forms.ChoiceField(required=True,
                                        choices=get_filter_choices(), label='')
        self.fields['parameter'].choices.insert(0, ('', '---'))
        self.fields['comp'] = forms.ChoiceField(choices=COMP_CHOICES, label='',
                                                                required=True)
        self.fields['comp'].choices.insert(0, ('', '---'))
        self.fields['threshold'] = forms.DecimalField(max_digits=8, label='',
                widget=forms.TextInput(attrs={'size':'10'}), decimal_places=2, 
                required=True)

FilterFormSet = formset_factory(FilterForm, can_delete=True, extra=1)


def get_metasystem_choices():
    choices = []
    for ms in MetaSystem.objects.all().order_by('-id'):
        choices.append((ms.id, '{} - {}'.format(ms.id, ms.name)))
    return choices


class CopyForm(Form):
    '''
    For copying a system to another metasystem
    '''
    reverse = forms.BooleanField(required=False)
    def __init__(self, *args, **kwargs):
        super(CopyForm, self).__init__(*args, **kwargs)
        self.fields['metasystem'] = forms.ChoiceField(required=True,
                                            choices=get_metasystem_choices())
        self.fields['metasystem'].choices.insert(0, ('', '---------'))

def get_bookmark_choices():
    choices = []
    for bm in Bookmark.objects.all().order_by('-id'):
        choices.append((bm.id, '{} - {}'.format(bm.id, bm.section)))
    return choices

class BookmarkForm(Form):
    '''
    For bookmarking systems
    '''
    def __init__(self, *args, **kwargs):
        super(BookmarkForm, self).__init__(*args, **kwargs)
        self.fields['bookmark'] = forms.ChoiceField(required=True,
                                            choices=get_bookmark_choices())
        self.fields['bookmark'].choices.insert(0, ('', '---------'))


class TradeForm(Form):
    '''
    Enter a new trade
    '''
    symbol = forms.CharField(required=False, 
            widget=forms.TextInput(attrs={'size':'5'}))
    volume = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'5'}))
    price = forms.DecimalField(required=True, max_digits=6, decimal_places=2,
            widget=forms.TextInput(attrs={'size':'5'}), label='at')
    date = forms.DateField(required=True, widget = AdminDateWidget())
