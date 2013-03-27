'''
TSB/template_tags/tabtags.py v0.1 121025

Created on 121025

@author: edwin

Usage:

{% load tabtags %}
{% make_tabs 'Home' 'Structure' 'Equity' %}
content of Home tab
{% next_tab %}
content of Structure tab
{% next_tab %}
content of Equity tab
{% end_tabs %}

Alternative usage:
{% make_tabs 'Home' 'Method' some_list %}

results in tab titles Method n (the list is just used as a counter)

CONSIDER: look at assignment tags:
https://docs.djangoproject.com/en/dev/howto/custom-template-tags/#assignment-tags
'''

from __future__ import division
from __future__ import absolute_import

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def tabs_js(context, *args):
    tab_titles = []
    for arg in args:
        if isinstance(arg, list):
            text = tab_titles.pop()
            for i, unused in enumerate(arg):
                tab_titles.append(text + ' {}'.format(i + 1))
        else:
            tab_titles.append(arg)
    context.dicts[0]['tab_titles'] = tab_titles
    context.dicts[0]['i_tab'] = 1
    n_tabs = len(tab_titles)
    html = '<script>function tab(tab) {'
    for i in range(n_tabs):
        html += 'document.getElementById(\'tab{}\').style.display = \'none\';'.\
                format(i+1)
    for i in range(n_tabs):
        html += 'document.getElementById(\'li_tab{}\').setAttribute("class", "");'.\
                format(i+1)
    html += 'document.getElementById(tab).style.display = \'block\'; document.getElementById(\'li_\'+tab).setAttribute("class", "active");}</script>'
    return html

@register.simple_tag(takes_context=True)
def start_tabs(context):
    tab_titles = context['tab_titles']
    html = '<div id="Tabs"><ul>'
    for i, title in enumerate(tab_titles):
        extra = 'class="active"' if i==0 else ''
        html += '<li id="li_tab{}" {} onclick="tab(\'tab{}\')" ><a>{}</a></li>'.\
                format(i+1, extra, i+1, title)
    html += '</ul><div id="Content_Area"><div id="tab1">'
    return html


@register.simple_tag(takes_context=True)
def next_tab(context):
    i_tab = context['i_tab'] + 1
    context['i_tab'] = i_tab
    return '</div><div id="tab{}" style="display: none;">'.\
            format(i_tab)

@register.simple_tag()
def end_tabs():
    return '</div></div><!--/Content--></div><!--/Tabs-->'
