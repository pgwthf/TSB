'''
systemmanager/tables.py v0.1 120823

Created on 120823

@author: edwin

This file contains helper classes for django_tables2
'''
from __future__ import division
from __future__ import absolute_import

from django.utils.safestring import mark_safe
import django_tables2 as tables

from TSB.utils import make_link
from TSB.tables import MakeNameLinkColumn, MakeSelectColumn
from metasystem.models import MetaSystem
from system.models import OUTPUT_FORMATS



def MakeResultsColumn(rs):

    class ResultsColumn(tables.Column):
        '''
        Generate a custom column with the current results and the max results
        '''
        def render(self, record):
            maxresults = record.get_number_of_calculations()
            if not maxresults:
                maxresults = record.maxresults
            rs_key = 'TSBspeed{}'.format(record.id)
            if rs.get(rs_key):
                speed = float(rs.get(rs_key))
            else:
                speed = 0
            n = MetaSystem.objects.get(id=record.id).system_set.filter().count()
            if n:
                kwargs = {'metasystem_id': record.id}
                n = make_link('show_metasystem', n, kwargs=kwargs)
            html = u'{} / {} ({:1.0f}/hr)'.format(n, maxresults, speed)
            return mark_safe(html)

    return ResultsColumn()



def MakePerformanceColumn(keys):

    class PerformanceColumn(tables.Column):
        empty_values = []
        def render(self, record):
            values = record.get_system_summary(keys)
            if values:
                performance = []
                for key, _ in OUTPUT_FORMATS.items(): # to maintain order
                    value = values.get(key, None)
                    if value is not None:
                        performance.append('{}'.format(value))
            else:
                performance = ('-',) * len(keys)
            return mark_safe('</td><td>'.join(performance))

    return PerformanceColumn()



def MakeMetaSystemsTable(rs, keys, **kwargs):

    class MetaSystemsTable(tables.Table):
        '''
        For django-tables2
        '''
        select = MakeSelectColumn(orderable=False)
        name = MakeNameLinkColumn('metasystem', 'comments')
        def render_pool(self, record):
            return mark_safe(make_link('show_pool', record.pool.name,
                    {'pool_id': record.pool.id}))
        startdate = tables.DateColumn(format='Y-m-d')
        enddate = tables.DateColumn(format='Y-m-d')
        def render_active(self, record):
            return 'Running' if record.active else '-'
        maxresults = MakeResultsColumn(rs)
        def render_group(self, record):
            return mark_safe(make_link('show_metasystems', record.group.name,
                    {'group_id': record.group.id}))
        performance = MakePerformanceColumn(keys)

        class Meta:
            model = MetaSystem
            attrs = {'class': 'paleblue'}
            sequence = ('select', 'id', 'name', 'pool', 'startdate', 'enddate', 
                    'allocation', 'equitymodel', 'active', 'maxresults')
            exclude=('markettype', 'startcash', 'conditions', 'comments')

    return MetaSystemsTable(**kwargs)
