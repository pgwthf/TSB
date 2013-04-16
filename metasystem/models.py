'''
metasystem/models.py v0.1 120823

Created on 120823

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

import copy
import datetime
import time

from django import db
from django.db import models
from django.forms.models import model_to_dict

from pyutillib.string_utils import random_string, str2dict
from pyutillib.math_utils import eval_conditions

from pricemanager.models import Pool
from tradesignal.models import Positions, Trades, Signals #, ExitSignal
from equity.models import EquityHistory
from system.models import System
from TSB.utils import get_choice

from metasystem.parameters import fields
from metasystem.parameters.params_market import _Market

# South is a major PITA...
# from south.modelsinspector import add_introspection_rules
# add_introspection_rules([], ['metasystem.parameters.fields.ParamField'])

# this model is for testing only
class ParamModel(models.Model):
    params = fields.ParamField('parameters', par_type='exit')


class Group(models.Model):
    '''
    This table holds groups of metasystems.
    '''
    name = models.CharField(max_length=80)
    comments = models.TextField()

    def __unicode__(self):
        return '{} {}'.format(self.id, self.name)


class MetaSystem(models.Model):
    '''
    MetaSystem defines the structure of a system. It has a set of variable 
    parameters, setting the parameters turns a MetaSystem into a System. 
    Parameters can be assigned random values at runtime.

    MetaSystems become read-only (and cannot be deleted) as soon as they have 
    Systems. The only fields that can be written after are:
        * name
        * description
        * parameters that were indicated as "variable" - so they appear in
            system.params
    '''
    name = models.CharField(max_length=20, unique=True)
    comments = models.CharField(max_length=100, blank=True)
    startdate = models.DateField()
    enddate = models.DateField()
    pool = models.ForeignKey(Pool)
    markettype = fields.ParamField(par_type='market')
    active = models.BooleanField(default=False)
    allocation = fields.ParamField(par_type='alloc')
    equitymodel = fields.ParamField(par_type='equity')
    maxresults = models.PositiveIntegerField(default=0)
    conditions = models.CharField(max_length=250, blank=True, null=True)
    startcash = models.PositiveIntegerField()
    group = models.ForeignKey(Group, null=True, default=None)


    def build_structure(self):
        '''
        Builds the structure of the MetaSystem in memory.
        '''
        self.methods = self.method_set.all().order_by('markettype', 'id')
        for method in self.methods:
            method.entries = method.entry_set.all()
            method.exits = method.exit_set.all()


    def _traverse_structure(self, function, **kwargs):
        '''
        Traverses the metasystem structure and applies the same method 
        <function> with <kwargs> to every parameter field.
        Return values must be dicts.
        '''
        retval = {}
        retval.update(getattr(self.allocation, function)(**kwargs))
        retval.update(getattr(self.markettype, function)(**kwargs))
        retval.update(getattr(self.equitymodel, function)(**kwargs))
        for method in self.methods:
            retval.update(getattr(method.rank, function)(
                    method_id=method.id, **kwargs))
            for entry in method.entries:
                retval.update(getattr(entry.params, function)(
                    method_id=method.id, **kwargs))
            for exit_ in method.exits:
                retval.update(getattr(exit_.params, function)(
                    method_id=method.id, **kwargs))
        return retval


    def _set_variable_parameters(self, param_dict):
        '''
        Sets all parameters with variable ranges to fixed values.
        <param_dict> is a dict with unique-key: value pairs.
        '''
        self._traverse_structure('set_variable_parameters', 
                parameters=param_dict)


    def _get_variable_parameters(self):
        '''
        Returns a dict with all variable parameters of this metasystem and 
        their (fixed) values. The keys of the dict are the names of the 
        parameters, but modified to be unique.
        '''
        return self._traverse_structure('get_variable_parameter_values')


    def _del_variable_parameters(self):
        '''
        Deletes the fixed value of the variable parameters from every parameter
        in this metasystem.
        '''
        self._traverse_structure('del_variable_parameters')


    def make_system(self, parameters):
        '''
        Sets all parameters with variable ranges to fixed values. This turns
        a MetaSystem into a system.
        '''
        self.build_structure()
        self._set_variable_parameters(str2dict(parameters))
        self._traverse_structure('initialise', pool=self.pool)


    def _init_runs(self):
        '''
        Initialisation of overall running parameters. Must only be used once
        for an MS instance.
        '''
        self.positions = Positions()
        self.trades = Trades()
        self.equity = EquityHistory()
        self.build_structure()
        # the same date range is used for all stocks in the pool:
        self.pool.index.global_date_range = (self.startdate, self.enddate)


    def _reset(self):
        '''
        Clears all positions, trades and equity. Run this before each backtest.
        '''
        self.positions.clear()
        self.trades.clear()
        self.equity.clear(self.startcash)


    def _traverse_parameters(self, value_lists, values=None):
        '''
        Runs the system for all parameter combinations
        '''
        if values is None:
            values = {}
        if len(value_lists) == 0:
#            self._reset()
            self._set_variable_parameters(values)
            self._traverse_structure('initialise', pool=self.pool)
            self._run_once()
        else:
            key, value_list = value_lists[0]
            for value in value_list:
                values[key] = value
                self._traverse_parameters(value_lists[1:], values)


#    def _init_system_run(self):
#        '''
#        Assigns parameters (unique_keys) to the MetaSystem,
#        so it can be used to backtest or real-time run a system.
#        '''
##        self._reset()
#        traverse_lists = self._traverse_structure('assign_values')
#        if traverse_lists:
#            print "TRAVERSE_LIST", traverse_lists
#            self._traverse_parameters(traverse_lists.items())
#        else:
#            self._traverse_structure('initialise', pool=self.pool)
#            self._run_once()
##        # the same date range is used for all stocks in the pool:
##        self.pool.index.global_date_range = (self.startdate, self.enddate)


    def _run_once(self):
        '''
        Run a single backtest for which all parameters have already been set.
        '''
        self._reset()
        signals = Signals()
        for today in self.pool.index.price.close.get_dates(self.startdate, 
                self.enddate):
            print 'TODAY: ', today
            todays_trades = signals.trade(today, self.positions, self.equity)
            self.trades.extend(todays_trades)
            ordered_method_list = self.markettype.get_methods(date=today,
                    method_list=self.methods)
            # generate exit signals for tomorrow:
            signals.set_exits(today, self.positions, self.pool, 
                    ordered_method_list)
            # generate entry signals for tomorrow:
            for method in ordered_method_list:
                signals.set_entries(today, method, self.pool, self.positions)
            # set position size of entry signals:
            signals.set_volume(today, self.allocation, self.equity, 
                    self.equitymodel, self.positions)

#            for signal in signals.entries:
#                print signal.stock, signal.volume
#            raise SystemExit()

        self.trades.extend(self.positions.close_all(today))
        self.trades.calc_performance(self.startdate, self.enddate, 
                                                self.positions.max_positions)
        data = self.trades.data
        sysdata = {'metasystem': self, 'active': False, 
                'params': repr(self._get_variable_parameters()),
                'enddate': self.enddate}
        data.update(sysdata)
        data.update(self.equity.calc_results())

#debugging
#        system = System.objects.create(**data) #keep only this
#the following replaces the previous line for debugging
        try:
            system = System.objects.create(**data)
        except:
            print data
            raise ValueError('ERROR saving system')
#/debugging

        self.equity.write_thumbnail_to_db(system)
        if eval_conditions(self.conditions, data):
            self.trades.write_to_db(system)
            self.equity.save(system)
        self._del_variable_parameters()


    def check_duplicate_entries_exits(self):
        '''
        Returns True if there are multiple entries or exits that use the same
        rule.
        '''
        duplicates = False
        for method in self.method_set.all():
            if method.check_duplicate_entries_exits():
                duplicates = True
        return duplicates


    def check_entries_exits(self):
        '''
        Returns errors if any method does not have at least one exit and one
        entry.
        '''
        errors = []
        for i, method in enumerate(self.methods):
            if not len(method.entries):
                errors.append('no entries found for method {}'.format(i))
            if not len(method.exits):
                errors.append('no exits found for method {}'.format(i))
        return errors


    def set_inactive(self):
        '''
        Set the current (Meta)System instance to inactive.
        '''
        self.active = False
        self.save()


    def set_active(self):
        '''
        Activates the MetaSystem for generating systems, if it has:
            * at least one variable parameter,
            * at least one entry and one exit,
            * a valid end date that is before today, and
            * a pool with a sufficient date range.
#TODO: reconsider if all this errors business is required
        '''
        errors = []
        self._init_runs()
        errors.extend(self.check_entries_exits())
        if not self.enddate or self.enddate >= datetime.date.today():
            errors.append('invalid end date')
        errors.extend(self.pool.check_date_ranges(self.startdate, 
                self.enddate))
        if not errors:
            self.active = True
            self.save()
            self._run_all() # start separate process and return
        return errors


    def has_systems(self):
        '''
        Return True if this metasystems has systems
        '''
        return self.system_set.count() > 0


    def is_discretionary(self):
        '''
        Return True if this metasystem is discretionary
TODO: discr systems should have LONG + SHORT method
        '''
        methods = self.method_set.all()
        if methods.count() != 1:
            return False
        entries = methods[0].entry_set.all()
        exits = methods[0].exit_set.all()
        print entries.count(), exits.count()
        if (entries.count() != 1) or (exits.count() != 1):
            return False
        print entries[0].params.get_dict()
        if entries[0].params.rule != 'd' or exits[0].params.rule != 'disc':
            return False
        return True


    def is_randomisable(self):
        '''
        Return True if this metasystem has random parameters and no parameter
        lists.
        '''
        if not hasattr(self, 'methods'):
            self.build_structure()
        randomisable = self._traverse_structure('is_randomisable')
        traversable = self._traverse_structure('get_lists')
        return randomisable and not traversable


    def is_traversable(self):
        '''
        Return True if this metasystem has at least one parameter list and 
        no random parameters.
        '''
        if not hasattr(self, 'methods'):
            self.build_structure()
        randomisable = self._traverse_structure('is_randomisable')
        n = self.get_number_of_calculations()
        return (n is not None) and (n > 1) and (not randomisable)


    def get_number_of_calculations(self):
        '''
        Return the total number of calculations if this is a traversable 
        metasystem. Return 0 if this metasystem is not traversable, 1 if only
        a single calculation is required.
        '''
        if not hasattr(self, 'methods'):
            self.build_structure()
        if self._traverse_structure('is_randomisable'):
            return 0
        traversable = self._traverse_structure('get_lists')
        n = 1
        for unused, value in traversable.items():
            n *= len(value)
        return n


#    @queue_command
#TODO: start this in separate process
    def _run_all(self):
        '''
TODO: drop speed measurement and move to % of total progress
        Run this MetaSystem with random parameters.
        The average number of calculations per hour is written to the
        database so it can be displayed by a view.
        '''
        self._init_runs()
        if self.is_randomisable():

            rs = None
            rs_key = 'TSBspeed{}'.format(self.id)
            factor_curr = 2./11.         # Exponential moving average over 10
            factor_prev = 1 - factor_curr #     speed measurements
            prev_time = time.time()
            moving_avg = 0
            while MetaSystem.objects.get(id=self.id).active:
                self._traverse_structure('randomise')
                print self._traverse_structure('get_variable_parameter_values')
                self._traverse_structure('initialise', pool=self.pool)
                self._run_once()
            # save running speed:
#TODO: works only for single process, need to count how many were added
                curr_time = time.time()
                speed = 3600 // (curr_time - prev_time)
                prev_time = curr_time
                if not moving_avg:
                    moving_avg = speed
                moving_avg = moving_avg * factor_prev + speed * factor_curr
                rs.set(rs_key, moving_avg)
                db.reset_queries() # this prevents flooding the memory
                if self.system_set.all().count() >= \
                        MetaSystem.objects.get(id=self.id).maxresults:
                    break

        elif self.is_traversable():
            traverse_lists = self._traverse_structure('get_lists')
            self._traverse_parameters(traverse_lists.items())

        elif self.get_number_of_calculations() == 1:
            # run once - all parameters were already stored as properties
            self._traverse_structure('randomise')
            self._traverse_structure('initialise', pool=self.pool)
            self._run_once()

        else:
            print('Random AND lists detected - cannot run')
        self.set_inactive()


    def get_system_summary(self, parameter_list):
        '''
        Return a dict with the best performance statistics of systems in this
        metasystem. If there are no systems, return None
        '''
        systems = self.system_set.all()
        if not systems:
            return None
        values = {}
        for sys in systems:
            for par in parameter_list:
                val = getattr(sys, par)
                if par not in values or val > values[par]:
                    values[par] = val
        return values


    def copy(self):
        '''
        Generate a deep copy of the current MetaSystem instance. Associated 
        Systems are *NOT* copied.
        '''
        return MetaSystem._copy(self)


    @classmethod
    def _copy(cls, instance):
        '''
        Copy <instance> to a new instance with a unique name.

        It is a deep copy for all associated methods, entries and exits are 
        copied too.
        '''
        fields = model_to_dict(instance, exclude=['id'])
        fields['pool'] = instance.pool
        fields['group'] = instance.group
        newname = fields['name'][:19] + random_string(1)
        fields['name'] = newname
        new_system = cls.objects.create(**fields)
        Method.copy_all(instance, new_system)
        return new_system


    def __unicode__(self):
        return self.name



class Method(models.Model):
    '''
    Methods for (Meta)Systems
    '''
    LONG = 1
    SHORT = -1
    DIR_CHOICES = (
            (LONG, 'long'),
            (SHORT, 'short'),
    )

    metasystem = models.ForeignKey(MetaSystem, blank=True, null=True)
    comments = models.CharField(max_length=100, blank=True)
    direction = models.SmallIntegerField(choices=DIR_CHOICES, default=LONG)
    rank = fields.ParamField(par_type='rank') # ranking indicator
    markettype = models.SmallIntegerField(choices=_Market.MKT_CHOICES, 
            default=_Market.ANY)


    def get_ranked_stocklist(self, date, pool):
        '''
        Returns the ranked stock list on <date>. If the list does not exist, it
        is generated first.
        The returned list is sorted with the highest priority item first.
        See for more documentation: parameters/params_rank.py
        '''
        if not hasattr(self, '_rsl') or self._rsl['date'] != date:
            rsl = self.rank.get_list(date=date, 
                    stock_list=pool.get_cached_stocklist(date))
            
#            print "Method.get_ranked_stocklist", date, len(rsl)
            
            self._rsl = {'date': date, 'list': rsl}
        return self._rsl['list']


    def reverse(self):
        '''
        Reverses this method from short to long or vice versa
        '''
        self.direction = self.LONG if self.direction == self.SHORT else \
                self.SHORT
        self.save()
        Entry.reverse(self)
        Exit.reverse(self)


    def check_duplicate_entries_exits(self):
        '''
        Returns True if there are multiple entries or exits that use the same
        rule.
        '''
        duplicates = False
        for nx in (Entry, Exit):
            unique_rules = set()
            rules = nx.objects.filter(method=self)
            for rule in rules:
                unique_rules.add(rule.params.rule)
            if len(rules) != len(unique_rules):
                duplicates = True
        return duplicates


    def markettype_str(self):
        '''
        Return markettype as text
        '''
        return get_choice(_Market.MKT_CHOICES, self.markettype)


    @staticmethod
    def copy_all(metasystem, new_metasystem):
        '''
        Copy all method instances that point to <metasystem> to new instances
        that point to <new_metasystem>.
        '''
        for method in metasystem.method_set.all().order_by('markettype', 'id'):
            method.copy(new_metasystem.id)


    def copy(self, new_ms_id, parameters=None, comment='', reverse=False):
        '''
        Copy this method instance from <metasystem> to another metasystem with 
        <new_ms_id>.
        '''
        new_metasystem = MetaSystem.objects.get(id=new_ms_id)
        rank = copy.deepcopy(self.rank)
        if parameters is not None:
            rank.set_variable_parameters(parameters)
        fields = {'comments': self.comments + comment,
                  'direction': self.direction,
                  'markettype': self.markettype,
                  'rank': rank,
                  'metasystem': new_metasystem}
        new_method = Method.objects.create(**fields)
        if reverse:
            new_method.reverse()
        Entry.copy(self, new_method, parameters)
        Exit.copy(self, new_method, parameters)


    def get_direction(self):
        '''
        Return the trade diretion in human readable format
        '''
        return get_choice(self.DIR_CHOICES, self.direction)


    def __unicode__(self):
        return '{} {}'.format(self.id, self.comments)



class _EntryExit(models.Model):
    '''
    Base class with common attributes and methods for Entries and Exists.
    '''
    comments = models.CharField(max_length=100, blank=True)
    method = models.ForeignKey(Method)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '{} - {}'.format(self.params.get_dict()['rule'], self.comments)


    @classmethod
    def reverse(cls, method):
        '''
        Reverses long and short rules
        '''
        for nx in cls.objects.filter(method=method):
            nx.params.reverse_rule()
            nx.save()


    @classmethod
    def copy(cls, method, new_method, parameters):
        '''
        Copy all instances that point to <method> to new instances that point
        to <new_method>.
        '''
        for nx in cls.objects.filter(method=method).order_by('id'):
            params = copy.deepcopy(nx.params)
            if parameters is not None:
                params.set_variable_parameters(parameters)
            fields = {'comments': nx.comments,
                      'params': params,
                      'method': new_method}
            cls.objects.create(**fields)



class Entry(_EntryExit):
    '''
    Entry rules for methods
    '''
    params = fields.ParamField(par_type='entry')



class Exit(_EntryExit):
    '''
    Exit rules for methods
    '''
    params = fields.ParamField(par_type='exit')
