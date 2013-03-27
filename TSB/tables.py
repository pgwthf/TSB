'''
TSB/tables.py v0.1 130122

Created on 130122

@author: edwin

NOTE: this file contains generic helper classes for django_tables2
'''
from __future__ import division
from __future__ import absolute_import

from django.utils.safestring import mark_safe

import django_tables2 as tables

from TSB.utils import make_link


def MakeNameLinkColumn(model, title=None):
    class NameLinkColumn(tables.Column):
        '''
        Generates an id field as a url.
        Set <title> to a field name to show that on hover of the link
        '''
        def render(self, record):
            if title is not None:
                titletxt = ' title="{}"'.format(getattr(record, title))
            else:
                titletxt = '*'
            return mark_safe(make_link('show_' + model, record.name,
                    kwargs={model + '_id': record.id}, title=titletxt))
    return NameLinkColumn()


def MakeSelectColumn(prefix='', **kwargs):
    '''
    Prefix must be a string
    '''
    class SelectColumn(tables.Column):
        '''
        Generates a checkbox that can be used to select this row.
        '''
        empty_values = []
        def render(self, record):
            html = u'<input type="checkbox" name="{}id" value="{}"/>'\
                    .format(prefix, record.id)
            return mark_safe(html)
    return SelectColumn()


class SymbolColumn(tables.Column):
    def render(self, value):
        return mark_safe(make_link('show_stock', value.name, 
                {'stock_id': value.id}))

class CompanyColumn(tables.Column):
    def render(self, value):
        return mark_safe(value.description)

def MakeFloatColumn(fmt):
    class Column(tables.Column):
        def render(self, value):
            return mark_safe(fmt.format(value))
    return Column()
