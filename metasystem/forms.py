'''
tradingsystem/forms.py v0.1 120711

Created on 120621

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django import forms
from django.forms import ModelForm
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.models import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.forms.formsets import DELETION_FIELD_NAME

from pricemanager.models import Pool

from metasystem.models import MetaSystem, Method, Exit, Entry
from metasystem.parameters.fields import ParamFormField, get_parameters, \
        ReadOnlyChoiceWidget


def MakeMethodFormset(readonly=False, **kwargs):
    '''
    Allows making writable or readonly formset.
    A readonly formset shows no extra (empty) forms and sends readonly=True
    to all its form fields that must not be written after a metasystem has
    systems.
    '''
    extra = 0 if readonly else 1

    class EntryForm(ModelForm):
        def __init__(self, *args, **kwargs):
            super(EntryForm, self).__init__(*args, **kwargs)
            self.fields['params'] = ParamFormField(par_type='entry', 
                    readonly=readonly, parameters=
                    get_parameters(field='params', par_type='entry', **kwargs))
            self.fields['comments'].widget = forms.Textarea(
                    attrs={'cols': 40, 'rows': 2})
        class Meta:
            model = Entry


    class ExitForm(ModelForm):
        def __init__(self, *args, **kwargs):
            super(ExitForm, self).__init__(*args, **kwargs)
            self.fields['params'] = ParamFormField(par_type='exit', 
                    readonly=readonly, parameters=
                    get_parameters(field='params', par_type='exit', **kwargs))
            self.fields['comments'].widget = forms.Textarea(
                    attrs={'cols': 40, 'rows': 2})
        class Meta:
            model = Exit

    EntryFormset = inlineformset_factory(Method, Entry, form=EntryForm, 
            extra=extra, can_delete=not readonly)
    ExitFormset = inlineformset_factory(Method, Exit, form=ExitForm,
            extra=extra, can_delete=not readonly)


    class BaseMethodFormset(BaseInlineFormSet):
        def get_queryset(self):
            '''
            Copied this method from Django code and modified the ordering 
            statement
            '''
            if not hasattr(self, '_queryset'):
                if self.queryset is not None:
                    qs = self.queryset
                else:
                    qs = self.model._default_manager.get_query_set()
                # If the queryset isn't already ordered it needs to be ordered
                # now to make sure that all formsets from this queryset have the
                # same form order.
                if not qs.ordered:
                    qs = qs.order_by('markettype', 'id')
                self._queryset = qs
            return self._queryset

        def add_fields(self, form, index):
            # allow the super class to create the fields as usual
            super(BaseMethodFormset, self).add_fields(form, index)
            # create the nested formsets
            try:
                instance = self.get_queryset()[index]
                pk_value = instance.pk
            except IndexError:
                instance=None
                pk_value = hash(form.prefix)
            # store the formsets in the .nested_... properties
            if self.data == {}:
                data = None
            else:
                data = self.data
            form.nested_entries = [EntryFormset(data=data, instance = instance,
                    prefix = 'ENTRIES_{}'.format(pk_value))]
            form.nested_exits = [ExitFormset(data=data, instance = instance,
                    prefix = 'EXITS_{}'.format(pk_value))]

        def is_valid(self):
            result = super(BaseMethodFormset, self).is_valid()
            for form in self.forms:
                if hasattr(form, 'nested_entries'):
                    for n in form.nested_entries:
                        # make sure each nested formset is valid as well
                        result = n.is_valid() and result
                if hasattr(form, 'nested_exits'):
                    for x in form.nested_exits:
                        # make sure each nested formset is valid as well
                        result = x.is_valid() and result
            return result

        def save_new(self, form, commit=True):
            '''Saves and returns a new model instance for the given form.'''
            instance = super(BaseMethodFormset, self).save_new(form,
                    commit=commit)
            # update the form's instance reference:
            form.instance = instance
            # update the instance reference on nested forms:
            for nested in form.nested_entries:
                nested.instance = instance
                # iterate over the cleaned_data of the nested formset and update
                # the foreign key reference:
                for cd in nested.cleaned_data:
                    cd[nested.fk.name] = instance
            for nested in form.nested_exits:
                nested.instance = instance
                for cd in nested.cleaned_data:
                    cd[nested.fk.name] = instance
            return instance

        def should_delete(self, form):
            '''
            Convenience method for determining if the form's object will
            be deleted; cribbed from BaseModelFormSet.save_existing_objects.
            '''
            if self.can_delete:
                raw_delete_value = form._raw_value(DELETION_FIELD_NAME)
                should_delete = form.fields[DELETION_FIELD_NAME].clean(
                        raw_delete_value)
                return should_delete
            return False

        def save_all(self, commit=True):
            '''
            Save all formsets and along with their nested formsets.
            '''
            # Save without committing (so self.saved_forms is populated)
            # -- We need self.saved_forms so we can go back and access
            #    the nested formsets
            objects = self.save(commit=False)
            # Save each instance if commit=True
            if commit:
                for o in objects:
                    o.save()
            # save many to many fields if needed
            if not commit:
                self.save_m2m()
            # save the nested formsets
            for form in set(self.initial_forms + self.saved_forms):
                if self.should_delete(form): continue
                for nested in form.nested_entries:
                    nested.save(commit=commit)
                for nested in form.nested_exits:
                    nested.save(commit=commit)


    class MethodForm(ModelForm):
        '''
        drop-down lists for entries/exits + custom form for parameters
        '''
        def __init__(self, *args, **kwargs):
            super(MethodForm, self).__init__(*args, **kwargs)
            if readonly:
                self.fields['markettype'].widget = ReadOnlyChoiceWidget()
                self.fields['direction'].widget = ReadOnlyChoiceWidget(
                        choices=Method.DIR_CHOICES)
            self.fields['rank'] = ParamFormField(par_type='rank', 
                    readonly=readonly, parameters=
                    get_parameters(field='rank', par_type='rank', **kwargs))
            self.fields['comments'].widget = forms.Textarea(attrs={'cols': 40, 
                    'rows': 2})
        class Meta:
            model = Method

    MethodFormset = inlineformset_factory(MetaSystem, Method, form=MethodForm,
            formset=BaseMethodFormset, extra=extra, can_delete=not readonly)
    return MethodFormset(**kwargs)



class MetaSystemForm(ModelForm):
    '''
    set which fields can be edited if results exist (maxresults, name, 
    description)
    '''

    def __init__(self, *args, **kwargs):
        attrs = None
        readonly = kwargs.pop('readonly', False)
        if readonly:
            attrs = {'readonly': True}
        super(MetaSystemForm, self).__init__(*args, **kwargs)

        if readonly:
            self.fields['pool'].widget = ReadOnlyChoiceWidget(model=Pool)
            self.fields['startcash'].widget.attrs['readonly'] = readonly

        self.fields['startdate'].widget = AdminDateWidget(attrs=attrs)
        self.fields['enddate'].widget = AdminDateWidget(attrs=attrs)
        self.fields['markettype'] = ParamFormField(par_type='market',
                readonly=readonly,
                parameters=get_parameters(field='markettype', 
                par_type='market', **kwargs))
        self.fields['allocation'] = ParamFormField(par_type='alloc', 
                readonly=readonly,
                parameters=get_parameters(field='allocation', 
                par_type='alloc', **kwargs))
        self.fields['equitymodel'] = ParamFormField(par_type='equity', 
                readonly=readonly,
                parameters=get_parameters(field='equitymodel', 
                par_type='equity', **kwargs))
        self.fields['comments'].widget = forms.Textarea(attrs={'cols': 40, 
                'rows': 3})
    class Meta:
        model = MetaSystem
        exclude = ('active')
