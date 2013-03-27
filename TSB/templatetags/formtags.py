from __future__ import division
from __future__ import absolute_import

from django.template import Library

register = Library()


'''
usage e.g.:
{% load formtags %}
{% for entry in method.entry_set.all|order_by:"id" %}
'''

@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)



@register.filter
def invert_if_lt1(value):
    '''
    Inverts <value> if it is lower than 1
    '''
    if value < 1:
        return '1/{:1.0f}'.format(1/value)
    else:
        return '{:2.1f}'.format(value)
