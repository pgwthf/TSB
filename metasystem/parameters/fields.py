'''
metasystem/parameters/fields.py v0.1 120824

changes from v0.1:

Created on 20120824

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

import random
try:
    import cPickle as pickle
except ImportError:
    import pickle
from collections import OrderedDict

from django.db import models
from django import forms
from django.forms import widgets
from django.core.validators import ValidationError
from django.utils.safestring import mark_safe

from channel.models import Channel

from pyutillib.string_utils import str2dict
#from .utils import round_by_format

from TSB.utils import get_choice


class ReadOnlyChoiceWidget(widgets.Select):

    def __init__(self, *args, **kwargs):
        '''
        ROCW(model=x) to define the model in case of a Foreignkey field
        '''
        self.model = kwargs.pop('model', None)
        self.choices_dict = kwargs.pop('choices', None)
        print kwargs, self.model, self.choices_dict
        widgets.Select.__init__(self, *args, **kwargs)

    def render(self, name, value, attrs=None):
        '''
        Show a fake dropdown with the value.
        '''
        print name, self.model, self.choices_dict
        if self.model:
            val = self.model.objects.get(id=value).name
        elif self.choices_dict:
            val = get_choice(self.choices_dict, value)
        else:
            val = value
        txt = '<select disabled"/>'
        txt += '<option selected="selected">{}</option>'.format(val)
        txt += '</select><input type="hidden" name="{}" value="{}" id="id_{}">'\
                .format(name, value, name)
        return mark_safe(txt)


class ModeWidget(forms.Widget):
    '''
    There are 3 types of parameters: 
        integer     standard python int, represented by a textbox
        float       standard python int, represented by a textbox
        choices     standard Django choices list, represented by a dropdown box
    Each parameter can be in one of 4 modes: 
        fixed       the parameter is defined in the MetaSysten and is used for
                        all associated systems
        random      an upper and lower limit for this parameter are defined and
                        every system will use a new randomly assigned value
        list        the parameter has a list of values and these values will be
                        traversed when systems are generated
        variable    the parameter is defined in the Metasystem, but can be
                        modified for every new system

             |  fixed        random    |     list         variable
    ---------|-------------------------|-----------------------------
        int  |  [=value]   [frm to]    |   [i, j, k]        [value]
             |   int      (int, int)   | [int, int, ...]    [int,]
    ---------|-------------------------|-----------------------------
        flt  |  [=value]   [frm to]    |   [a, b, c]       [value]
             |   flt      (flt, flt)   | [flt, flt, ...]    [flt,]
    ---------|-------------------------|-----------------------------
    choices  | [=value^] [- random -^] |   [- all -^]      [value^]
             |   str    (str, str, ..) | [str, str, ...]    [str,]
    ---------|-------------------------|-----------------------------
    editable |    NO        NO         |      YES            YES
    ---------|-------------------------|-----------------------------
    record in|    NO        YES        |      YES            YES
    systems  |                         |
    -----------------------------------------------------------------
    '''
    FIXED = 1
    RANDOM = 2
    LIST = 4
    VARIABLE = 8

    INTFLT = 16
    CHOICES=32

    def __init__(self, *args, **kwargs):
        '''
        Constructor saves <parameters>, see _Param for documentation.
        '''
        self.parameters = kwargs.pop('parameters')
        forms.Widget.__init__(self, *args, **kwargs)

    def render(self, name, value, attrs=None):
        '''
        Return an html string for this widget.

        <name> is the string containing the name of the field and <value> is a
        variable that contains the value of this parameter, the type of this
        value determines what the mode is.
        '''
        size = 40
        error = False
        readonly = attrs.get('readonly') == 'readonly'

        #determine mode
        mode = self.CHOICES if 'choices' in self.parameters else self.INTFLT
        if isinstance(value, int) or isinstance(value, float) or \
                isinstance(value, str) or isinstance(value, unicode):
            mode += self.FIXED
        elif not len(value):
            raise ValueError('iterable parameter must not be empty')
        else:
            if isinstance(value, tuple):
                mode += self.RANDOM
            elif isinstance(value, list):
                mode += self.VARIABLE if len(value) == 1 else self.LIST
            else:
                raise TypeError('invalid value type: {}'.format(type(value)))
            if isinstance(value[0], int) or isinstance(value[0], float):
                # mode should be self.INTFLT
                pass
            elif isinstance(value[0], str) or isinstance(value[0], unicode):
                # mode should be self.CHOICES
                if mode & self.INTFLT:
                    error = True
            else:
                raise TypeError('invalid type in iterable: {}'.format(type(
                        value[0])))

        print 'MODE = ', mode, name, value

        if mode & self.INTFLT:
            if mode & self.FIXED:
                val = '={}'.format(value)
            elif mode & self.RANDOM:
                val = '{} {}'.format(value[0], value[1])
            elif mode & self.LIST:
                fmt = self.parameters['format'].partition('}')[0].partition('{')
                fmt = '{' + fmt[2] + '}' # remove everything outside {}
                if error:
                    val = value
                else:
                    val = ', '.join(fmt.format(v) for v in value)
            elif mode & self.VARIABLE:
                val = value[0]
            d = ''
            if readonly and ((mode & self.FIXED) or (mode & self.RANDOM)):
                d = ' readonly'
            html = '<input type="text" size="{0}" name="{1}" value="{2}" '\
                    'id="id_{1}"{3}/>'.format(size, name, val, d)

        elif mode & self.CHOICES:
            if readonly and ((mode & self.FIXED) or (mode & self.RANDOM)):
                # show a fake dropdown
                if mode & self.RANDOM:
                    val = '- random -'
                    value = '-RND-'
                else:
                    val = '=' + get_choice(self.parameters['choices'], value)
                    value = '={}'.format(value)
                html = '<select disabled"/><option selected="selected">'
                html += '{}</option></select>'.format(val)
                # The actual value of this parameter is specified here:
                print '**', name, val, value
                html += '<input type="hidden" name="{}" value="{}" id="id_{}">'\
                .format(name, value, name)
            else:
                html = '<select name="{0}" id="id_{0}"/>'.format(name)
                s = ' selected="selected"' if (mode & self.LIST) else ''
                html += '<option value="-ALL-"{}>- all -</option>'.format(s)
                if not readonly or (mode == self.RANDOM):
                    s = ' selected="selected"' if (mode & self.RANDOM) else ''
                    html += '<option value="-RND-"{}>- random -</option>'.\
                            format(s)

                html += '<optgroup label="Variable:">'
                for c1, c2 in self.parameters['choices']:
                    s = ''
                    if (mode & self.VARIABLE) and (str(c1) == str(value[0])):
                        s = ' selected="selected"'
                    html += '<option value="{}"{}>{}</option>'.format(c1, s, c2)
                html += '</optgroup>'

                if not readonly or (mode == self.FIXED) or (mode == self.RANDOM):
                    html += '<optgroup label="Fixed:">'
                    for c1, c2 in self.parameters['choices']:
                        s = ''
                        if (mode & self.FIXED) and (str(c1) == str(value)):
                            s = ' selected="selected"'
                        html += '<option value="={}"{}>={}</option>'.format(
                                c1, s, c2)
                    html += '</optgroup>'

                html += '</select>'

        html += '<input type="hidden" name="{}_MODE" value="{}">'.\
                format(name, mode)
        return mark_safe(html)


    def value_from_datadict(self, data, files, name):
        '''
        Return the python representation of the key-value pairs sent from the
        browser form.

        <data> is a dict with request.POST (GET) parameters and <name> is a
        string containing the name of the field associated with this widget.
        '''
        mode = data.get('{}_MODE'.format(name), None)
        if mode is None: # first time this parameters is used
            return self.parameters['default']

        value = data[name]
        if int(mode) & self.INTFLT:
            if value.startswith('='): # mode = FIXED
                value = value[1:]
            elif ',' in value: # mode = LIST
                value = value.replace(' ', '').rstrip(',').split(',')
                if len(value) > len(set(value)):
                    value = sorted(list(set(value)))
            elif value.count(' ') == 1: # mode = RANDOM
                value = tuple(value.split(' '))
            else: # mode = VARIABLE
                value = [value]
        elif int(mode) & self.CHOICES:
            if value == '-ALL-': # mode = LIST
                value = ['{}'.format(c[0]) for c in self.parameters['choices']]
            elif value == '-RND-': # mode = RANDOM
                value = tuple('{}'.format(c[0]) for c in 
                        self.parameters['choices'])
            elif value.startswith('='): # mode = FIXED
                value = value[1:]
            else: # mode = VARIABLE
                value = [value]
                print "VALUE", value
        else:
            raise ValueError('Invalid mode value {}'.format(mode))
        return value



class ModeListField(forms.CharField):
    '''
    This field may hold a fixed value (string) or a list of options.
    '''
    def clean(self, value):
        print 'VAL', value
        return value


class ModeIntegerField(forms.IntegerField):
    '''
    Return a cleaned (validated) python variable, the type depends on mode:
    This field may hold an integer in 4 different modes:
        FIXED       int         =int
        RANDOM      tuple[0,1]  int int (space)
        LIST        list        int, int, int, ... (comma with or without space
        VARIABLE    list[0]     int
    '''
    def clean(self, value):
        if isinstance(value, tuple) and len(value) == 2:
            return (super(ModeIntegerField, self).clean(value[0]),
                    super(ModeIntegerField, self).clean(value[1]))
        if isinstance(value, list):
            return [super(ModeIntegerField, self).clean(v) for v in value]
        else:
            return super(ModeIntegerField, self).clean(value)



class ModeFloatField(forms.FloatField):
    '''
    Return a cleaned (validated) python variable, the type depends on mode:
    This field may hold an integer in 4 different modes:
        FIXED       flt         =flt
        RANDOM      tuple[0,1]  flt flt (space)
        LIST        list        flt, flt, flt, ... (comma with or without space)
        VARIABLE    list[0]     flt
    '''
    def clean(self, value):
        if isinstance(value, tuple) and len(value) == 2:
            return (super(ModeFloatField, self).clean(value[0]),
                    super(ModeFloatField, self).clean(value[1]))
        if isinstance(value, list):
            return [super(ModeFloatField, self).clean(v) for v in value]
        else:
            return super(ModeFloatField, self).clean(value)



def get_module(param_type):
    '''
    Returns a reference to the module params_<param_type>
    '''
    filename = 'params_{}'.format(param_type)
    return __import__(filename, globals())



class _Param(object):
    '''
    This is the base class for all parameter classes.

TODO: AAA document format of <parameters>
    Every instance of a subclass of _Param must have a .parameters property.
    The format of .parameters is:

    Every instance of a subclass of _Param must have a <par_type> and a 
    <rule> attribute. In addition they must have exactly the attributes as
    specified in the parameters dict of the subclass <par_type>_<rule>
    'params_<par_type>.py' is the file name where all possible subclasses
    are found.
    '''
    OPEN = 'o'
    HIGH = 'h'
    LOW = 'l'
    CLOSE = 'c'
    STOP = 's'
    LIMIT = 'l'
    UNCONDITIONAL_AT_CHOICES = (
            (OPEN, 'open'),
            (CLOSE, 'close'),
            )
    AT_CHOICES = (
            (OPEN, 'open'),
            (CLOSE, 'close'),
            (STOP, 'stop'),
            (LIMIT, 'limit'),
            )
    PRICE_CHOICES = (
            (OPEN, 'open'),
            (HIGH, 'high'),
            (LOW, 'low'),
            (CLOSE, 'close'),
            )
    GREATER_THAN = 'gt'
    LOWER_THAN = 'lt'
    EQUAL = 'eq'
    NOT_EQUAL = 'ne'
    OP_CHOICES = (
            (GREATER_THAN, 'greater than'),
            (LOWER_THAN, 'lower than'),
            )
    EQ_CHOICES = (
            (EQUAL, 'is'),
            (NOT_EQUAL, 'is not')
            )
    ON = 1
    OFF = 0
    SWITCH_CHOICES = (
            (ON, 'on'),
            (OFF, 'off'),
            )

    std_rule = {'widget': widgets.HiddenInput, 
            'field': forms.CharField, 
            'verbose': '', 
            'default': 'test',
            }
    std_pc = {'widget': ModeWidget, 
            'field': ModeFloatField, 
            'format': '{:2.1f}%', 
            'doc': 'any percentage between -100 and 100',
            'verbose': 'Percentage', 
            'default': 8., 
            'range': (-100.,100.), 
            }
    std_flt = {'widget': ModeWidget, 
            'field': ModeFloatField, 
            'format': '{:3.2f}', 
            'doc': 'Just a float, overwrite this to specify',
            'verbose': 'Float', 
            'default': 10000., 
            'range': (0., 1000000.),
            }
    std_int = {'widget': ModeWidget, 
            'field': ModeIntegerField, 
            'format': '{}', 
            'doc': 'just an int, overwrite this to specify',
            'verbose': 'Integer', 
            'default': 1, 
            'range': (1, 1000000),
            }
    std_nd = {'widget': ModeWidget, 
            'field': ModeIntegerField, 
            'format': '{}', 
            'doc': 'Number of days for the indicator',
            'verbose': 'Number of days', 
            'default': 20, 
            'range': (1, 252),
            }
    std_switch = {'widget': ModeWidget, 
            'field': ModeListField, 
            'format': '{}', 
            'doc': 'switch this rule on or off',
            'verbose': 'Active', 
            'default': ON, 
            'choices': SWITCH_CHOICES,
            }
    std_lb = {'widget': ModeWidget,
            'field': ModeListField,
            'format': '{}', 
            'doc': 'lookback period for the channel indicator',
            'verbose': 'Lookback', 
            'default': Channel.YEAR, 
            'choices': Channel.LOOKBACK_CHOICES,
            }
    std_at = {'widget': ModeWidget,
            'field': ModeListField,
            'format': '{}',
            'doc': 'determines when the signal is executed',
            'verbose': 'Trade at', 
            'default': OPEN,
            'choices': UNCONDITIONAL_AT_CHOICES,
            }
    std_all_at = {'widget': ModeWidget, 
            'field': ModeListField, 
            'format': '{}', 
            'doc': 'determines when the signal is executed',
            'verbose': 'Trade at', 
            'default': OPEN, 
            'choices': AT_CHOICES,
            }
    std_price = {'widget': ModeWidget, 
            'field': ModeListField,
            'format': '{}',
            'doc': 'set the price for a stop or limit order',
            'verbose': 'Price is todays', 
            'default': CLOSE,
            'choices': PRICE_CHOICES,
            }
    std_op = {'widget': ModeWidget,
            'field': ModeListField,
            'format': '{}',
            'doc': 'this is the operator of an inequality in the rule',
            'verbose': 'Operator', 
            'default': GREATER_THAN,
            'choices': OP_CHOICES,
            }
    std_eq = {'widget': ModeWidget,
            'field': ModeListField,
            'format': '{}',
            'doc': 'this is the operator of an equality in the rule',
            'verbose': 'Operator', 
            'default': EQUAL,
            'choices': EQ_CHOICES,
            }


    def __init__(self, **kwargs):
        '''
        Stores every parameter in <kwargs> in this instance. Fixed and variable
        parameters are stored differently.
        '''
        self.variables = {}
        self.par_type = kwargs.pop('par_type')
        for key in self.parameters:
            try:
                value = kwargs.pop(key)
            except:
                raise KeyError('Key [{}] not provided.'.format(key))
            self._set_parameter(key, value)
        if len(kwargs):
            raise ValueError('Too many values to unpack: {}'.format(kwargs))


    def _set_parameter(self, parameter, value):
        '''
        Assign values to parameters. Fixed parameters are stored as properties
        of <self> and variable parameters are stored in the dict 
        <self.variables>. 
        In case it is a choices parameter, the type is converted to int if
        necessary.
        '''
        choices = self.parameters[parameter].get('choices', None)
        if isinstance(value, tuple):
            if choices and type(choices[0][0]) == int:
                value = tuple([int(v) for v in value])
            self.variables[parameter] = value
        elif isinstance(value, list):
            if choices and type(choices[0][0]) == int:
                value = [int(v) for v in value]
#UNCOMMENT THIS FOR AT PROBLEM
#            if len(value) == 1:
#                setattr(self, parameter, value[0])
#            else:
#                self.variables[parameter] = value
            self.variables[parameter] = value
        elif isinstance(value, int) or isinstance(value, float):
            setattr(self, parameter, value)
        elif isinstance(value, str) or isinstance(value, unicode):
            if choices and type(choices[0][0]) == int:
                value = int(value)
            setattr(self, parameter, value)
        else:
            raise TypeError('Illegal type for {}={}'.format(parameter, value))


    def num_variables(self, **kwargs):
        '''
        Returns the number of variable parameters.
        '''
        return len(self.variables)


    def _unique_key(self, key, method_id=None):
        '''
        Return a unique key for this key
        '''
        if method_id is None:
            method_id = ''
        return '{}{} {}{}'.format(self.IDENTIFIER, self.rule, method_id, key)


    def get_variable_parameter_values(self, method_id=None):
        '''
        Returns a dict that contains the (fixed) values of all variable 
        parameters of this instance. The keys of the dict are the names of the 
        parameters, but modified to be unique.
        '''
        var_params = {}
        for key in self.variables:
            var_params[self._unique_key(key, method_id)] = getattr(self, key)
        return var_params


    def set_variable_parameters(self, parameters, method_id=None):
        '''
        Creates a property for every parameter in <self.variables> where the
        value is retrieved from <parameters>.
        <parameters> contains key:value pairs where the keys are unique names
        for parameters.
        This method must return a dict, because it is traversed by metasystem.
        '''
        for key in self.variables:
            unique_key = self._unique_key(key, method_id)
            try:
                self._set_parameter(key, parameters[unique_key])
            except:
                raise KeyError('Key {} not found in parameters'.format(
                        unique_key))
        return {}


    def del_variable_parameters(self, **kwargs):
        '''
        Deletes the properties that are fixed values of variable parameters.
        This method must return a dict, because it is traversed by metasystem.
        '''
        for parameter in self.variables:
            delattr(self, parameter)
        return {}


    def get_lists(self, method_id=None):
        '''
        Return a dict with unique keys and a list for each parameter that needs
        to be traversed.
        '''
        retval = {}
        for key in self.parameters:
            value = self._get_value(key)
#            if isinstance(value, list) and len(value) > 1:
            if isinstance(value, list): #NOTE: variable values are included!!!
                retval[self._unique_key(key, method_id)] = value
        return retval


    def is_randomisable(self, method_id=None):
        '''
        Returns dict with unique_key:True for every parameter that gets a 
        randomly assigned value
        '''
        retval = {}
        for key in self.parameters:
            value = self._get_value(key)
            if isinstance(value, tuple):
                retval[self._unique_key(key, method_id)] = True
        return retval


    def randomise(self, method_id=None):
        '''
        Assign values to variable parameters. These values may be randomised
        or selected from a list.
        The resulting values are stored in <self.[parameter]> properties, while
        the original tuple/list (that holds the range) remains in 
        <self.variables>.
        This method must return a dict, because it is traversed by metasystem.
        '''
        def round_by_format(float_number, fmt):
            '''
            Rounds a float using the supplied printing format string. Any characters
            outside { and } are stripped.
            '''
            while fmt[0] != '{': 
                fmt = fmt[1:]
            while fmt[-1] != '}':
                fmt = fmt[:-1]
            string = fmt.format(float_number)
            return float(string)
        for key in self.parameters:
#TODO: AA: consider using mode as in modewidget
            choices = self.parameters[key].get('choices', None)
            value = self._get_value(key)
            if isinstance(value, tuple):
                if isinstance(value[0], float):
                    fmt = self.parameters[key]['format']
                    value = round_by_format(random.uniform(*value), fmt)
                elif isinstance(value[0], int) and not choices:
                    value = random.randint(*value)
                else:
                    value = random.choice(value)
            elif isinstance(value, list) and len(value) == 1:
                value = value[0]
            else:
                continue
            self._set_parameter(key, value)
        return {}


    def initialise(self, **kwargs):
        '''
        Overwrite this method in the (child) class if you need to set initial
        values.
        Initialise is executed prior to every run (i.e. backtest).
        This method must return a dict, because it is traversed by metasystem.
        '''
        return {}


    def _get_value(self, parameter):
        '''
        Returns the value of <parameter>. This value may be fixed or a range.
        If both exist, the fixed value is returned.
        '''
        try:
            # check if a fixed value exists
            value = getattr(self, parameter)
        except AttributeError:
            try:
                # check if a range or list exists
                value = self.variables[parameter]
#TODO: AAA ???                if isinstance(value, list) and len(value)==1:
#                    value = value[0]
            except KeyError:
                raise ValueError('Parameter {} is not defined.'.format(
                                                                    parameter))
        except:
            raise ValueError('Parameter {} is not defined.'.format(parameter))
        return value


    def parameter_is_positive(self, parameter):
        '''
        Returns True if the value of the parameter is positive or if both 
        values are positive in case the parameter is variable.
        '''
        value = self._get_value(parameter)
        try:
            return value[0] > 0 and value[1] > 0
        except TypeError:
            return value > 0


    def parameter_is_negative(self, parameter):
        '''
        Returns True if the value of the parameter is negative or if both 
        values are negative in case the parameter is variable.
        '''
        value = self._get_value(parameter)
        try:
            return value[0] < 0 and value[1] < 0
        except TypeError:
            return value < 0


    def reverse_rule(self):
        '''
        Reverses this rule from long to short vice versa if it has a <reverse>
        property.
        '''
        if self.reverse:
            self.rule = self.reverse


    def repr(self, parameter, negative=False):
        '''
        Returns a formatted string that represents the value of this parameter,
        even if it is a range or a list of choices.
        If <negative> is True, -<value> will be returned in the string.
        '''
#TODO: AA: consider using mode as in ModeWidget 
        choices = self.parameters[parameter].get('choices', None)
        fmt = self.parameters[parameter]['format']
        sign = -1 if negative else 1
        value = self._get_value(parameter)
        if isinstance(value, str) or isinstance(value, unicode):
            if not choices:
                raise ValueError('No choices found for {}'.format(parameter))
            return get_choice(choices, value)
        elif isinstance(value, tuple): # assign a random value
            if choices:
                values = [get_choice(choices, v) for v in value]
                return '({})'.format(', '.join(values))
            else:
                lo = fmt.format(sign * value[0])
                hi = fmt.format(sign * value[1])
                return '[{} to {}]'.format(lo, hi)
        elif isinstance(value, list):
            if len(value) == 1: # variable
                if choices:
                    return get_choice(choices, value[0])
                else:
                    return fmt.format(sign * value[0])
            else: # traverse a list
                if choices:
                    values = [get_choice(choices, v) for v in value]
                    return '[{}]'.format(', '.join(values))
                else:
                    values = [fmt.format(v) for v in value]
                    return '[{}]'.format(', '.join(values))
        elif not isinstance(value, int) and not isinstance(value, float):
            raise TypeError('Invalid type for {}.'.format(parameter))
        return fmt.format(sign * value)


    def get_dict(self):
        '''
        Returns an ordered dict with all parameters of the child instance + 
        [class].
        '''
        output = []
        for key in self.parameters:
            output.append((key, self._get_value(key)))
        return OrderedDict(output)


    @staticmethod
    def get_function_list(module, par_type):
        '''
        Returns a list with all functions (rules) of <par_type>
        '''
        return [f for f in dir(module) if f[:len(par_type)] == par_type]


    @classmethod
    def get_rule_choices(cls, par_type, exclude=None):
        '''
        Return the list of available alternative classes for this class

        Returns a choices list with all available rules for <par_type>, where
        <par_type> may be 'entry', 'exit', ...
        A file must exist with the name rules_<par_type> that contains a class
        for each rule.
        The format of a rule is: <par_type>_<rule>, where <rule> is the rule
        name, e.g.: exit_ma
        Any rule that is in the exclude list will be excluded from the output.
        '''
        if not exclude:
            exclude = []
        exclude.extend(['test', 'default'])
        module = get_module(par_type)
        functions = cls.get_function_list(module, par_type)
        choices = [('', 'Select {}'.format(par_type))]
        for function in sorted(functions):
            if not exclude or not function.split('_')[1] in exclude:
                name = getattr(module, function).name
                choices.append((function[len(par_type)+1:], name))
        return choices


    @classmethod
    def get_doc(cls, par_type):
        '''
        Return all documentation for <par_type>.
        '''
        module = get_module(par_type)
        functions = cls.get_function_list(module, par_type)
        doc_list = []
        for name in sorted(functions):
            if name != par_type + '_test':
                function = getattr(module, name)
                parameters = []
                for key, settings in function.parameters.items():
                    if key != 'rule':
                        parameters.append((key, settings['doc']))
                doc = {'name': name, 'description': function.name, 
                       'doc':function.__doc__, 'parameters': parameters}
                doc_list.append(doc)
        return doc_list


    @staticmethod
    def get_init_parameters(par_type, exclude=None):
        '''
        Returns a (temporary) parameters dict that can be used to generate
        a dropdown with available rules (functions) for this parameter.
        '''
        parameters = {'rule': {'widget': widgets.Select, 'field': 
                forms.ChoiceField, 'format': '{}', 'verbose': 'New rule', 
                'default': None, 'choices': _Param.get_rule_choices(par_type, 
                exclude)}}
        return parameters


    def __unicode__(self):
        # This is to work with readable dict strings in admin
#        return str(dict(self.get_dict()))
        return self.name



class ParamField(models.TextField):
    '''
    Stores a class as a field of parameters.

    Every ParamField definition must specify its <par_type>, which must be an 
    existing params_<par_type>.py file that contains subclasses of _Param.
    Every ParamField field must specify what subclass within the <par_type> it
    refers to, using the parameter rule = '<class_name>', where <class_name>
    refers to an existing <par_type>_<class_name> class in the file.
    '''
    description = "Stores a Parameter class instance as a dict in a CharField"

    # This ensures that the to_python() method will be called every time an 
    # instance of the field is assigned a value
    __metaclass__ = models.SubfieldBase


    def __init__(self, *args, **kwargs):
        '''
        Store all parameters.
        '''
        self.par_type = kwargs.pop('par_type')
        super(ParamField, self).__init__(*args, **kwargs)


# FIXME: the following does not work in admin ??
    def formfield(self, **kwargs):
        '''
        This is a fairly standard way to set up some defaults while letting the
        caller override them.
        '''
        defaults = {'form_class': ParamFormField, 'par_type': self.par_type,
                                                            'parameters': None}
        defaults.update(kwargs)
        return super(ParamField, self).formfield(**defaults)


    def get_internal_type(self):
        return 'TextField'


    def to_python(self, value):
        '''
        Converts a database value to a python object.
        '''
        if not value:
            return
        if isinstance(value, _Param):
            return value
        elif isinstance(value, unicode) and value.startswith('{'):
            # This is to work with readable dict strings in admin
            param_dict = str2dict(value)
        else:
            try:
                param_dict = pickle.loads(str(value))
            except:
                raise TypeError('unable to process {}'.format(value))
        param_dict['par_type'] = self.par_type
        classname = '{}_{}'.format(self.par_type, param_dict['rule'])
        return getattr(get_module(self.par_type), classname)(**param_dict)


    def get_prep_value(self, value):
        '''
        Converts a python object to the correct database format.
        This is the opposite of to_python
        '''
        if isinstance(value, _Param):
            return pickle.dumps(value.get_dict())
        else:
            raise TypeError('This field can only store _Param instances.')


    def value_to_string(self, obj):
        '''
        This method is used by the serializers to convert the field into a 
        string for output.
        '''
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


    def get_prep_lookup(self, lookup_type, value):
        '''
        Prepares the value for passing to the database when used in a database 
        lookup, i.e. perform data validity checks.
        '''
        if lookup_type == 'exact':
            return self.get_prep_value(value)
        elif lookup_type == 'in':
            return [self.get_prep_value(v) for v in value]
        else:
            raise TypeError('Lookup type {} is not supported.'.format(
                                                                lookup_type))


class ParamWidget(forms.MultiWidget):
    '''
    Displays the correct set of (sub)widgets for this parameter.
    '''

    def __init__(self, parameters, attrs=None):
        '''
        Generates the list of (sub)widgets for this widget and passes that to
        the MultiWidget constructor.
        '''
        self.parameters = parameters
        _widgets = []
        for key in parameters:
            kwargs = {}
            if parameters[key].has_key('choices'):
                if parameters[key]['widget'] == ModeWidget or (
                        parameters[key]['widget'] == ModeWidget):
                    kwargs['parameters'] = parameters[key]
                else:
                    kwargs['choices'] = parameters[key]['choices']
            if parameters[key]['widget'] == ModeWidget or (
                        parameters[key]['widget'] == ModeWidget):
                # supply default and range info to ModeWidget
                kwargs['parameters'] = parameters[key]
            _widgets.append(parameters[key]['widget'](**kwargs))
        super(ParamWidget, self).__init__(_widgets, attrs)


    def decompress(self, value):
        '''
        Returns values to put into the widgets. These values are retrieved from
        the params object instance.
        <value> is an instance of a subclass of _Param.
        '''
        if value:
            output = []
            for key in self.parameters:
                output.append(value.get_dict()[key])
        else: # return default values
            output = []
            for key in self.parameters:
                output.append(self.parameters[key]['default'])
        return output


    def format_output(self, rendered_widgets):
        """
        Given a list of rendered widgets (as strings), returns a Unicode string
        representing the HTML for the whole lot.
        """
        for i, key in enumerate(self.parameters):
            text = '<label for="id_address_field_{}">{}</label>'.format(i, 
                    self.parameters[key]['verbose'])
            rendered_widgets.insert(2*i, text)
        rendered_string = ''
        for i, x in enumerate(rendered_widgets):
            if i <= 2 or i % 2:
                rendered_string += x
            else:
                rendered_string += '<br>' + x
        return rendered_string



def get_parameters(field, par_type, **kwargs):
    '''
    Returns the parameters.
    '''
#CONSIDER: turn this function into a method of ParamFormField
    if kwargs.get('instance'):
        return getattr(kwargs.get('instance'), field).parameters
    if kwargs.get('initial'):
#        print '****', kwargs.get('initial')[field].parameters, '****'
        return kwargs.get('initial')[field].parameters
    if kwargs.get('data'):
        prefix = kwargs.get('prefix', '')
        if prefix:
            prefix += '-'
        rule = kwargs.get('data').get(prefix + field + '_0')
#        print 'GET_PARAMETERS_data', field, par_type, rule, prefix
#        print 'DATA', kwargs.get('data')
    else:
        rule = None
#        print 'GET_PARAMETERS_no_data', field, par_type, kwargs
    if rule :
        classname = '{}_{}'.format(par_type, rule)
        parameters = getattr(get_module(par_type), classname).parameters
    else:
# FIXME: AAB if par_type = entry or exit: need exclude list
#    this may be possible using a class variable in _Param that keeps track of
#    all _Param instances, in that case this function can find out which entries
#    or exits are already in use (in this metasystem/method??)
# NOTE: The above will need to take multiple processes into account!
        parameters = {'rule': {'widget': widgets.Select, 'field': 
                forms.ChoiceField, 'format': '{}', 'verbose': 'New rule', 
                'default': None, 'choices': _Param.get_rule_choices(par_type)}}
    return parameters




class ParamFormField(forms.MultiValueField):
    '''
    Use this field for a _Param instance in a form.
    '''
    widget = ParamWidget


    def __init__(self, par_type, parameters, *args, **kwargs):
        attrs = None
        if kwargs.pop('readonly', False):
            attrs = {'readonly': 'readonly'}
        if parameters is None:
            parameters = _Param.get_init_parameters(par_type)
        self.widget = ParamWidget(parameters=parameters, attrs=attrs)
        self.parameters = parameters
        self.par_type = par_type
        fields = []
        for key in parameters:
            field_kwargs = {} # this is for validation
            if parameters[key].get('choices'):
                if parameters[key]['widget'] != ModeWidget and (
                        parameters[key]['widget'] != ModeWidget):
                    field_kwargs['choices'] = parameters[key]['choices']
            elif parameters[key].get('range'):
                field_kwargs['min_value'] = parameters[key]['range'][0]
                field_kwargs['max_value'] = parameters[key]['range'][1]
            fields.append(parameters[key]['field'](**field_kwargs))
        super(ParamFormField, self).__init__(fields, *args, **kwargs)


    def compress(self, data_list):
        '''
        Returns a single value (_Param instance) for the given list of values.
        The values can be assumed to be valid.
        '''
        classname = '{}_{}'.format(self.par_type, data_list[0])
        if len(data_list) != len(self.parameters):
            raise ValidationError('Too many or too few parameters specified.')
        param_dict = {'par_type': self.par_type}
        for key, val in zip(self.parameters, data_list):
            param_dict[key] = val
        return getattr(get_module(self.par_type), classname)(**param_dict)
