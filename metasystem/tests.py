from __future__ import division
from __future__ import absolute_import

import datetime
#from copy import deepcopy

from django.test import TestCase
from django.forms.models import model_to_dict
#from django.db import models
from django.core import serializers

from metasystem.models import MetaSystem, Method, Entry, Exit, ParamModel

from pricemanager.models import Pool, Stock

from metasystem.parameters import params_entry, params_exit
from metasystem.parameters.fields import _Param, ParamField, ParamFormField

from pyutillib.string_utils import str2dict

class CustomField(TestCase):

    def test_defer(self):
        test_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        params = params_exit.exit_test(**test_dict)
        pm = ParamModel.objects.create(params=params)
        self.assertIsInstance(pm.params, _Param)

        pm = ParamModel.objects.get(pk=pm.pk)
        self.assertIsInstance(pm.params, _Param)
        self.assertEqual(pm.params.get_dict(), params.get_dict())

        pm = ParamModel.objects.defer('params').get(pk=pm.pk)
        pm.save()

        pm = ParamModel.objects.get(pk=pm.pk)
        self.assertIsInstance(pm.params, _Param)
        self.assertEqual(pm.params.get_dict(), params.get_dict())


    def test_custom_field(self):
        test_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        params = params_exit.exit_test(**test_dict)
        pm = ParamModel.objects.create(params=params)

        self.assertEqual(pm._meta.get_field('params').verbose_name, 'parameters')
        self.assertEqual(pm.params._nd, 5)
        self.assertEqual(pm.params.rule, 'test')
        self.assertEqual(pm.params.par_type, 'exit')

        pm1 = ParamModel.objects.get(pk=pm.pk)
        self.assertIsInstance(pm1.params, _Param)
        self.assertEqual(str2dict(unicode(pm1.params)), {'rule': 'test', 'nd': 5})

        test_dict2 = {'rule': 'test', 'nd': 8, 'par_type': 'exit'}
        params2 = params_exit.exit_test(**test_dict2)
        self.assertQuerysetEqual(ParamModel.objects.filter(
                params__in=[params, params2]), [{'rule': 'test', 'nd': 5}],
                lambda qs: str2dict(unicode(qs.params)))
        self.assertRaises(TypeError, lambda: ParamModel.objects.filter(
                                                        params__lt=params))

        stream = serializers.serialize("json", ParamModel.objects.all())
        self.assertEqual(stream, '[{"pk": %d, "model": "metasystem.parammodel", "fields": {"params": "ccollections\\nOrderedDict\\np1\\n((lp2\\n(lp3\\nS\'rule\'\\np4\\naS\'test\'\\np5\\naa(lp6\\nS\'nd\'\\np7\\naI5\\naatRp8\\n."}}]' % pm1.pk)

        obj = list(serializers.deserialize("json", stream))[0]
        self.assertEqual(obj.object, pm)

        pm.delete()

        test_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        params = params_exit.exit_test(**test_dict)
        pm1 = ParamModel.objects.create(params=params)
        test_dict = {'rule': 'test', 'nd': 8, 'par_type': 'exit'}
        params = params_exit.exit_test(**test_dict)
        pm2 = ParamModel.objects.create(params=params)

        self.assertQuerysetEqual(
            ParamModel.objects.all(), [
                {'rule': 'test', 'nd': 5},
                {'rule': 'test', 'nd': 8},
            ],
            lambda qs: str2dict(unicode(qs.params))
        )


class customFormField(TestCase):

    def test_ParamFormField(self):
        test_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        params = params_exit.exit_test(**test_dict)
        parameters = params.parameters

        from django import forms
        class ParamTestForm(forms.Form):
            chars = forms.CharField()
            params = ParamFormField(par_type='exit', parameters=parameters)

        # empty form
        ptf = ParamTestForm()
        self.assertFalse(ptf.is_bound)
        self.assertFalse(ptf.is_valid())
        self.assertFalse(ptf.errors)
        self.assertIn('value="20"', str(ptf['params']))
        self.assertIn('value="test"', str(ptf['params']))
        self.assertNotIn('value="exit"', str(ptf['params']))

        # bound_form
        ptf2 = ParamTestForm({'params_0': 'test', 'params_1': 5, 'chars': 'Hello'})
        self.assertIsInstance(params, _Param)
        self.assertTrue(ptf2.is_bound)
        self.assertTrue(ptf2.is_valid())
        self.assertFalse(ptf2.errors)
        self.assertIsInstance(ptf2.cleaned_data['params'], _Param)
        self.assertEqual(str2dict(unicode(ptf2.cleaned_data['params'])), str2dict(unicode(params)))


    def test_ParamFormField_MODEL(self):
        test_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        params = params_exit.exit_test(**test_dict)
        pm = ParamModel.objects.create(params=params)
        parameters = params.parameters
        from django import forms
        class ParamTestForm(forms.ModelForm):
            params = ParamFormField(par_type='exit', parameters=parameters)
            class Meta:
                model = ParamModel

        # create an empty form
        ptf = ParamTestForm()
        self.assertFalse(ptf.is_bound)
        self.assertFalse(ptf.is_valid())
        self.assertFalse(ptf.errors)
        self.assertIn('value="20"', str(ptf['params']))
        self.assertIn('value="test"', str(ptf['params']))
        self.assertNotIn('value="exit"', str(ptf['params']))

        # create an unbound form
        pm = ParamModel.objects.get(pk=pm.pk)
        ptf2 = ParamTestForm(instance=pm)
        self.assertFalse(ptf2.is_bound)
        self.assertFalse(ptf2.errors)
        self.assertIn('value="5"', str(ptf2['params']))
        self.assertIn('value="test"', str(ptf2['params']))
        self.assertNotIn('value="exit"', str(ptf2['params']))

        # create an bound form
        ptf2 = ParamTestForm({'params_0': 'test', 'params_1': 5, 'chars': 'Hello'})
        self.assertIsInstance(params, _Param)
        self.assertTrue(ptf2.is_bound)
        self.assertTrue(ptf2.is_valid())
        self.assertFalse(ptf2.errors)
        self.assertIsInstance(ptf2.cleaned_data['params'], _Param)
        self.assertEqual(str2dict(unicode(ptf2.cleaned_data['params'])), str2dict(unicode(params)))


class modelsTests(TestCase):

    def setUp(self):
        somedate = datetime.date.today()
        snp = Stock.objects.create(name='^GSPC', description='S&P500', 
                currency=Stock.US_DOLLAR, startdate=somedate, enddate=somedate)
        pool = Pool.objects.create(name='test', description='test', index=snp, 
                startdate=somedate, enddate=somedate)
        self.system1 = MetaSystem.objects.create(name='test', 
                comments='comments', startdate=datetime.date.today(),
                enddate=datetime.date.today(), pool=pool, startcash=1,
                methodselector=u"{'rule': 'test'}", maxresults=0,
        self.method1 = Method.objects.create(metasystem=self.system1,
                ls=1, n_pos=1, rank=u"{'rule': 'test'}")
        in_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        param = params_exit.exit_test(**in_dict)
        self.exit1 = Exit.objects.create(params=param, method=self.method1)
        in_dict = {'rule': 'ma', 'nd':12, 'at':'open', 'op': 'lt', 'par_type': 'entry'}
        param = params_entry.entry_ma(**in_dict)
        self.entry1 = Entry.objects.create(params=param, method=self.method1)


    def test_Param(self):
        '''
        Tests of static/class methods go here
        '''
        exit_list = _Param.get_rule_choices('exit')
        self.assertIsInstance(exit_list, list)
        n_exits = len(exit_list)
        self.assertTrue(n_exits > 2)
        for item in exit_list:
            self.assertIsInstance(item, tuple)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], str)
        self.assertEqual(exit_list[0], ('', 'Select exit'))
        self.assertIn(('test', 'Test'), exit_list)
        for exit_name in ('ma', 'sl', 'pts', 'rank'):
            self.assertIn(exit_name, (x[0] for x in exit_list))

        exit_list = _Param.get_rule_choices('exit', exclude=['ma','sl'])
        self.assertIsInstance(exit_list, list)
        self.assertTrue(len(exit_list) == n_exits - 2)
        for item in exit_list:
            self.assertIsInstance(item, tuple)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], str)
        self.assertEqual(exit_list[0], ('', 'Select exit'))
        self.assertIn(('test', 'Test'), exit_list)
        for exit_name in ('pts', 'rank'):
            self.assertIn(exit_name, (x[0] for x in exit_list))
        for exit_name in ('ma', 'sl'):
            self.assertNotIn(exit_name, (x[0] for x in exit_list))

        params = _Param.get_init_parameters('exit')
        self.assertIsInstance(params, dict)
        self.assertEqual(len(params), 1)
        self.assertIn('rule', params)
        self.assertEqual(len(params['rule']), 6)
        for key in ('widget', 'field', 'format', 'verbose', 'default', 
                                                                    'choices'):
            self.assertIn(key, params['rule'])

    def test_exit_param(self):
        '''
        Non-static/class methods of _Param are tested here too
        '''
        test_dict = {'rule': 'test', 'nd': 5, 'par_type': 'exit'}
        x = params_exit.exit_test(**test_dict)
        self.assertEqual(x.name, 'Test')
        self.assertEqual(x.repr('nd'), '5')
        self.assertEqual(x.description(), 'Test 5')
        del test_dict['par_type']
        self.assertEqual(x.get_dict(), test_dict)
#        self.assertEqual(x.get_rule_text(['nd']), 'test5')
        udict = unicode(x)
        self.assertTrue(udict.startswith('{'))
        self.assertTrue(udict.endswith('}'))
        self.assertEqual(len(udict), 25)
        _Param._unique_keys = {}
        self.assertFalse(_Param._unique_keys) # must be empty dict
#        x.randomise()
#        self.assertFalse(_Param._unique_keys) # must be empty dict

        x = None
        test_dict = {'rule': 'test', 'nd': (6,9), 'par_type': 'exit'}
        x = params_exit.exit_test(**test_dict)
        self.assertFalse(_Param._unique_keys) # must be empty dict
        self.assertEqual(x.name, 'Test')
        self.assertEqual(x.repr('nd'), '[6 to 9]')
        self.assertEqual(x.description(), 'Test [6 to 9]')
        del test_dict['par_type']
        self.assertEqual(x.get_dict(), test_dict)
#        self.assertEqual(x.get_rule_text(['nd']), None)
        udict = unicode(x)
        self.assertTrue(udict.startswith('{'))
        self.assertTrue(udict.endswith('}'))
        self.assertEqual(len(udict), 30)
        self.assertFalse(_Param._unique_keys) # must be empty dict
        x.randomise('test1', 0)
        self.assertIn('Xtest 0nd', _Param._unique_keys['test1'])
        nd = _Param._unique_keys['test1']['Xtest 0nd']
        self.assertIsInstance(nd, int)
        self.assertGreaterEqual(nd, 6)
        self.assertLessEqual(nd, 9)
        _Param.unique_keys = {}

        x = None
        test_dict = {'rule': 'test', 'nd': (6,9), 'par_type': 'exit'}
        x = params_exit.exit_test(**test_dict)
        self.assertIn('Xtest 0nd', _Param._unique_keys['test1'])
        nd = _Param._unique_keys['test1']['Xtest 0nd']
        self.assertIsInstance(nd, int)
        self.assertGreaterEqual(nd, 6)
        self.assertLessEqual(nd, 9)
        self.assertEqual(x.name, 'Test')
        self.assertEqual(x.repr('nd'), '[6 to 9]')
        self.assertEqual(x.description(), 'Test [6 to 9]')
        del test_dict['par_type']
        test_dict['nd'] = nd
#        self.assertEqual(x.get_dict(), test_dict)
#        self.assertEqual(x.get_rule_text(['nd']), 'test{}'.format(nd))
#        udict = unicode(x)
#        self.assertTrue(udict.startswith('{'))
#        self.assertTrue(udict.endswith('}'))
#        self.assertEqual(len(udict), 26)


# test sys/method: check_duplicate_entries_exits

    def test_Exit(self):
        out_test = {'rule': 'test', 'nd': 5}
        in_test = out_test.copy()
        in_test['par_type'] = 'exit'
        param = params_exit.exit_test(**in_test)
        x = Exit.objects.create(params=param, method=self.method1)
        self.assertEqual(type(x.params.description()), str)
        self.assertEqual(x.params.get_dict(), out_test)
        self.assertRaises(TypeError, Exit.objects.create, params=str(in_test))
        self.assertRaises(TypeError, Exit.objects.create, params=in_test)
        self.assertRaises(TypeError, Exit.objects.create, params='')
        self.assertRaises(TypeError, Exit.objects.create, params=None)
        self.assertRaises(TypeError, Exit.objects.create, params='asf')

## test all exits?
##        from parameters import params_exit
        out_test = {'rule': 'ma', 'nd':8, 'bd':5, 'at':'open', 'op': 'gt'}
        in_test = out_test.copy()
        in_test['par_type'] = 'exit'
        param = params_exit.exit_ma(**in_test)
        x = Exit.objects.create(params=param, method=self.method1)
        self.assertEqual(type(x.params.description()), str)
        self.assertEqual(x.params.get_dict(), out_test)
        self.assertRaises(TypeError, Exit.objects.create, params=str(in_test))
        self.assertRaises(TypeError, Exit.objects.create, params=in_test)
        self.assertRaises(TypeError, Exit.objects.create, params='')
        self.assertRaises(TypeError, Exit.objects.create, params=None)
        self.assertRaises(TypeError, Exit.objects.create, params='asf')


    def test_Entry(self):
        out_test = {'rule': 'ma', 'nd':12, 'at':'open', 'op': 'lt'}
        in_test = out_test.copy()
        in_test['par_type'] = 'entry'
        param = params_entry.entry_ma(**in_test)
        n = Entry.objects.create(params=param, method=self.method1)
        self.assertEqual(type(n.params.description()), str)
        self.assertEqual(n.params.get_dict(), out_test)
        self.assertRaises(TypeError, Entry.objects.create, params=str(in_test))
        self.assertRaises(TypeError, Entry.objects.create, params=in_test)
        self.assertRaises(TypeError, Entry.objects.create, params='')
        self.assertRaises(TypeError, Entry.objects.create, params=None)
        self.assertRaises(TypeError, Entry.objects.create, params='asf')
# test all entries?


    def test_entry_exit(self):
        dictN1 = {'rule': 'ma', 'nd':(1,10), 'at':'open', 'op': 'lt',
                 'par_type': 'entry'}
        dictX1 = {'rule': 'ma', 'nd':(6,18), 'bd':5, 'at':'open', 'op': 'lt',
                 'par_type': 'exit'}
        dictX2 = {'rule': 'sl', 'pc':(5.,10.), 'bd':2, 'par_type': 'exit'}
        dictX3 = {'rule': 'pts', 'pc':(-5.,-1.), 'bd':1, 'par_type': 'exit'}
        param1 = params_entry.entry_ma(**dictN1)
        param2 = params_exit.exit_ma(**dictX1)
        param3 = params_exit.exit_sl(**dictX2)
        param4 = params_exit.exit_pts(**dictX3)
        param1.randomise('test1', 0)
        param2.randomise('test2', 0)
        param3.randomise('test2', 0)
        param4.randomise('test2', 0)
        self.assertEqual(len(param1._unique_keys['test1']), 1)
        self.assertEqual(len(param2._unique_keys['test2']), 3)
        self.assertIn('Xsl 0pc', param1._unique_keys['test2'])
        self.assertIn('Xpts 0pc', param1._unique_keys['test2'])
        self.assertIn('Xma 0nd', param1._unique_keys['test2'])
        self.assertIn('Nma 0nd', param1._unique_keys['test1'])


    def test_Method(self):
        # create an entry
        out_test = {'rule': 'ma', 'nd':12, 'at':'open', 'op': 'lt'}
        in_test = out_test.copy()
        in_test['par_type'] = 'entry'
        param = params_entry.entry_ma(**in_test)
        Entry.objects.create(params=param, method=self.method1)
        #create an exit
        out_test = {'rule': 'test', 'nd': 5}
        in_test = out_test.copy()
        in_test['par_type'] = 'exit'
        param = params_exit.exit_test(**in_test)
        Exit.objects.create(params=param, method=self.method1)


    def test_MetaSystem(self):
    # copy (also tests Method.copy and Entry/Exit.copy
        new_system = self.system1.copy()
        exclude = ['id', 'name']
        fields = model_to_dict(self.system1, exclude=exclude)
        new_fields = model_to_dict(new_system, exclude=exclude)
        self.assertNotEqual(self.system1.id, new_system.id)
        self.assertNotEqual(self.system1.name, new_system.name)
        self.assertEqual(fields, new_fields)

        methods = Method.objects.filter(metasystem=self.system1)
        new_methods = Method.objects.filter(metasystem=new_system)
        self.assertEqual(len(methods), len(new_methods))
        self.assertEqual(len(methods), 1)
        for method, new_method in zip(methods, new_methods):
            exclude = ['id', 'metasystem', 'rank']
            fields = model_to_dict(method, exclude=exclude)
            new_fields = model_to_dict(new_method, exclude=exclude)
            self.assertNotEqual(method.id, new_method.id)
            self.assertEqual(fields, new_fields)
            self.assertEqual(str2dict(unicode(method.rank)), str2dict(unicode(new_method.rank)))
            self.assertEqual(method.rank.get_dict(), new_method.rank.get_dict())

            entries = Entry.objects.filter(method=method)
            new_entries = Entry.objects.filter(method=new_method)
            self.assertEqual(len(entries), len(new_entries))
            self.assertEqual(len(entries), 1)
            for entry, new_entry in zip(entries, new_entries):
                self.assertNotEqual(entry.id, new_entry.id)
                self.assertEqual(entry.method, self.method1)
                self.assertEqual(new_entry.method, new_method)
                self.assertEqual(entry.comments, new_entry.comments)
                self.assertEqual(str2dict(unicode(entry.params)), str2dict(unicode(new_entry.params)))
                self.assertEqual(entry.params.get_dict(), new_entry.params.get_dict())

            exits = Exit.objects.filter(method=method)
            new_exits = Exit.objects.filter(method=new_method)
            self.assertEqual(len(exits), len(new_exits))
            for exit_, new_exit in zip(exits, new_exits):
                self.assertNotEqual(exit_.id, new_exit.id)
                self.assertEqual(exit_.method, self.method1)
                self.assertEqual(new_exit.method, new_method)
                self.assertEqual(exit_.comments, new_exit.comments)
                self.assertEqual(str2dict(unicode(exit_.params)), str2dict(unicode(new_exit.params)))
                self.assertEqual(exit_.params.get_dict(), new_exit.params.get_dict())
