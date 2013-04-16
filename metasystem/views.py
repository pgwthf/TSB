'''
metasystem/views.py v0.1 120820

Created on 120820

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.shortcuts import render, render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.safestring import mark_safe

from django_tables2 import RequestConfig

from TSB.utils import Notify

from metasystem.tables import MakeMetaSystemsTable
from metasystem.models import MetaSystem, Group
from metasystem.forms import MetaSystemForm, MakeMethodFormset

from system.forms import CopyForm
from system.models import OUTPUT_FORMATS
from system.models import System
from system.tables import MakeSystemsTable

from pyutillib.string_utils import str2dict_keys


@login_required
def show_metasystems(request, group_id=None):
    '''
    Show overview of all (meta)systems in the (Meta)Systems database.
    '''
    notify = None

    if request.method == 'POST' and request.POST.get('action'):
        metasystem_list = request.POST.getlist('id')

        if request.POST.get('action') == 'Copy':
            if not len(metasystem_list):
                notify = Notify('Copy failed, select a MetaSystem to copy')
            elif len(metasystem_list) > 1:
                notify = Notify('Copy failed, select only one MetaSystem to '\
                        'copy')
            else:
                for metasystem_id in metasystem_list:
                    metasystem = MetaSystem.objects.get(id=metasystem_id)
                    new_metasystem = metasystem.copy()
                    name = new_metasystem.name
                notify = Notify('MetaSystem "{}" copied to "{}"'.format(name, 
                        new_metasystem.name))

        elif request.POST.get('action') == 'Delete':
            if not len(metasystem_list):
                notify = Notify('Delete failed, select MetaSystem(s) to delete')
            else:
                notify = Notify('Delete MetaSystem(s) {}?'.format(', '.join(
                        metasystem_list)))
                notify.set_replies(request, ('Yes', 'No'))
                request.session['metasystem_delete_list'] = metasystem_list

    elif request.method == 'POST' and request.POST.get('reply'):
        metasystem_list = request.session.get('metasystem_delete_list')
        if not metasystem_list:
            raise AttributeError('session has no valid metasystem_delete_list')
        del request.session['metasystem_delete_list']
        if request.POST.get('reply') == 'Yes':
            MetaSystem.objects.get(id__in=metasystem_list).delete()
#            for metasystem_id in metasystem_list:
#                metasystem = MetaSystem.objects.get(id=metasystem_id)
#                metasystem.delete()
            notify = Notify('MetaSystem(s) {} deleted'.format(','.join(
                    metasystem_list)))
        elif request.POST.get('reply') == 'No':
            notify = Notify('Delete cancelled')

    if group_id:
        group = Group.objects.get(id=group_id)
        metasystems = MetaSystem.objects.filter(group=group)
        exclude = ('group')
    else:
        metasystems = MetaSystem.objects.all()
        group = None
        exclude = ()

    rs = None
    keys = ('reliability', 'profit_factor', 'exp_p_day', 'profit_pa', 
            'ann_profit', 'min_year', 'min_dd_ratio', 'sqn')

    metasystems_table = MakeMetaSystemsTable(rs, keys, data=metasystems, 
            order_by=('-id',),exclude=exclude)

    # generate titles for performance columns:
    titles = []
    for key, params in OUTPUT_FORMATS.items():
        if key in keys:
            if 'title' in params:
                key = params['title']
            else:
                key = key.replace('_', ' ')
            titles.append(key)
    metasystems_table.base_columns['performance'].verbose_name = mark_safe(
            '</th><th>'.join(titles))

    RequestConfig(request, paginate=None).configure(metasystems_table)
    return render(request, 'show_metasystems.html', {
            'metasystems_table': metasystems_table,
            'group': group,
            'notify': notify,
            'groups': Group.objects.all(),
            })



@login_required
def show_metasystem(request, metasystem_id):
    '''
    Show MetaSystem with <metasystem_id> along with it
    '''
    notify = None

    if request.method == 'POST' and request.POST.get('action'):
        system_list = request.POST.getlist('id')

        if request.POST.get('action') == 'Delete':
            if not len(system_list):
                notify = Notify('Delete failed, select System(s) to delete')
            else:
                notify = Notify('Delete System(s) {}?'.format(', '.join(
                        system_list)))
                notify.set_replies(request, ('Yes', 'No'))
                request.session['system_delete_list'] = system_list

    elif request.method == 'POST' and request.POST.get('reply'):
        system_list = request.session.get('system_delete_list')
        if not system_list:
            raise AttributeError('session has no valid system_delete_list')
        del request.session['system_delete_list']
        if request.POST.get('reply') == 'Yes':
            for system_id in system_list:
                system = System.objects.get(id=system_id)
                system.delete()
            notify = Notify('System(s) {} deleted'.format(','.join(
                    system_list)))
        elif request.POST.get('reply') == 'No':
            notify = Notify('Delete cancelled')

    metasystem = MetaSystem.objects.get(id=metasystem_id)

    if request.method == 'POST' and request.POST.get('action'):

        if request.POST.get('action') == 'Start calculations':
            errors = metasystem.set_active()
            if errors:
                notify = Notify('MetaSystem NOT started: {}'.format(', '.join(
                        errors)))
            else:
                notify = Notify('MetaSystem {} started'.format(metasystem.name))

        elif request.POST.get('action') == 'Stop calculations':
            metasystem.set_inactive()
            notify = Notify('MetaSystem {} stopped'.format(metasystem.name))

    values = metasystem.get_system_summary(('reliability', 'profit_factor',
            'exp_p_day', 'profit_pa', 'ann_profit', 'min_year', 'min_dd_ratio',
            'sqn'))
    if values:
        performance = []
        for key, fmt in OUTPUT_FORMATS.items(): # to maintain order
            value = values.get(key, None)
            if value is not None:
                performance.append((fmt['name'], fmt['format'].format(value)))
    else:
        performance = None 

    metasystem.build_structure()

    # copy system to method if required
    if request.method == 'POST' and request.POST.get('copy'):
        copyform = CopyForm(data=request.POST)
        if copyform.is_valid():
            new_ms_id = copyform.cleaned_data['metasystem']
            reverse = copyform.cleaned_data['reverse']
            for method in metasystem.method_set.all():
                method.copy(new_ms_id, reverse=reverse, 
                        comment='copy from metasystem {}'.format(metasystem.id))
            notify = Notify('{} methods copied to metasystem {}'.format(
                    metasystem.method_set.count(), metasystem.id))
    else:
        copyform = CopyForm()

    systems = System.objects.filter(metasystem__id=metasystem_id)

    view_settings = {
            'parameters': True,
            'performance': True,
            'result': True
            }

    systems_table = MakeSystemsTable(data=systems, order_by=('-id',), 
            show=view_settings, excludes=['metasystem'])

    # generate column_titles
    if systems.count():
        systems_table.base_columns['params'].verbose_name = mark_safe(
                        '</th><th>'.join(str2dict_keys(systems[0].params)))
        for key, params in OUTPUT_FORMATS.items():
            if 'title' in params:
                systems_table.base_columns[key].verbose_name = params['title']
    RequestConfig(request, paginate={'per_page': 100}).configure(systems_table)


    return render(request, 'show_metasystem.html', {
            'metasystem': metasystem,
            'copyform': copyform,
            'notify': notify,
            'performance': performance,
            'systems_table': systems_table, 
#            'filterformset': filterformset,
#            'bookmarkform': bookmarkform,

            })



@login_required
def edit_metasystem(request, metasystem_id=None, force_edit=False):
    '''
    Edit MetaSystem with <metasystem_id>.
    If any Systems exist for this MetaSystem, the system is read-only, but a 
    few fields can still be edited.

    NOTE: force_edit can be used to edit a locked system
    '''
    readonly = False
    if metasystem_id == 'new':
        metasystem = None
    else:
        metasystem = MetaSystem.objects.get(id=metasystem_id)
        if not force_edit and metasystem.system_set.all().count():
            readonly = True

    errors = False
    if request.method == 'POST':
        metasystemform = MetaSystemForm(data=request.POST, instance=metasystem,
            readonly=readonly)
        if metasystemform.is_valid():
            savedsys = metasystemform.save(commit=False)
            methodformset = MakeMethodFormset(data=request.POST, 
                    instance=savedsys, readonly=readonly)
            if readonly or methodformset.is_valid():
                savedsys.save()
                if methodformset:
                    methodformset.save_all()
                return redirect('edit_metasystem', metasystem_id=savedsys.id)
            else:
                errors = True
        else:
            errors = True
            methodformset = MakeMethodFormset(data=request.POST, 
                    instance=metasystem, readonly=readonly)
    else:
        metasystemform = MetaSystemForm(instance=metasystem, readonly=readonly)
        methodformset = MakeMethodFormset(instance=metasystem, 
                readonly=readonly)

#tmp TODO: Remove the following once exclude works
    duplicates = metasystem.check_duplicate_entries_exits() if metasystem \
                                                                    else False
#/tmp
    return render_to_response('edit_metasystem.html',
            {'metasystem': metasystem,
            'metasystemform': metasystemform, 
            'methodformset': methodformset,
            'errors': errors,
            'duplicates': duplicates,},
            context_instance=RequestContext(request))
