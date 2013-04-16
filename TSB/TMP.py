'''
This file contains temporary functions, e.g. for maintenance or modifications
'''
from __future__ import division
from __future__ import absolute_import


import TSB.settings


TSB.settings.DEBUG = False
DEBUG = False



def tmp_translate():
    '''
    Use (rewrite) this to translate columns
    '''
    import datetime
    from system.models import System
    from pyutillib.math_utils import div
    from django.db import transaction
    systems = System.objects.all()
    with transaction.commit_on_success():
        for sys in systems:
            tp = float(sys.expectancy) * sys.n_total
            dt = datetime.date(2012, 6, 30) - datetime.date(2008, 1, 1)
            sys.profit_pa = tp * 365./dt.days
            sys.true_avg_loss = float(sys.avg_loss) * (1 - float(sys.reliability)/100.)
            sys.profit_ratio = div(float(sys.profit_pa), float(sys.true_avg_loss))
            if sys.profit_ratio > 99.99: sys.profit_ratio = 99.99
            sys.save()



def calc_channels(pool_name, skipstock=None):
    '''
    Calculate all channels for the specified pool.
    '''
    from pricemanager.models import Channel
    from pricemanager.models import Pool
    import datetime, time
    pool = Pool.objects.get(name=pool_name)
    starttime = time.time()
    skip = True if skipstock else False
    for stock, _, _ in pool._get_offset_list():
        dt = time.time() - starttime
        print stock.name, datetime.datetime.now(), '{:1.0f}:{:02.0f}'.format(dt // 60, dt % 60)
        starttime = time.time()
        if not skip:
            from pricemanager.models import Channel
            Channel.calculate(stock)
            del Channel
        if stock.name == skipstock:
            skip = False
        del stock # prevent memory overflow (?)


def mod_ranks():
    '''
    rename a rule and parameters within it
    '''
    from metasystem.models import Method
    from metasystem.parameters import params_rank
    methods = Method.objects.all()

# set renames here:
    rule_from = 'channel_pullback2'
    rule_to = u'chasw'
    renames = (
#            ('nd', 'lb'),
#            ('a_th', 'tha'),
#            ('vsl_th', 'ths'),
#            ('w_th', 'thw'),
            )
#/set

    for method in methods:
        p = method.rank.get_dict()
        if p['rule'] == rule_from:
            print method.metasystem.id, p
            params = dict(p)
            params['par_type'] = 'rank'
            params['rule'] = rule_to
            for frm, to in renames:
                params[to] = params.pop(frm)
#            print params
#            method.rank = params_rank.rank_cha(**params)
            method.rank = getattr(params_rank, 'rank_' + rule_to)(**params)
            print method.rank.get_dict()

            for system in method.metasystem.system_set.all():
                print 'FROM:', system.params
                new_params = system.params.replace('R' + rule_from, 'R' + rule_to)
                for frm, to in renames:
                    new_params = new_params.replace(frm + '\'', to + '\'')
                system.params = new_params
                print 'TO:', system.params
                system.save()
            method.save()
            print "saved"
            break


def mod_exits():
    '''
    rename a rule and parameters within it
    '''
    from metasystem.models import Exit
    from metasystem.parameters import params_exit
    exits = Exit.objects.all()

# set renames here:
    type_ = 'exit'
    rule_from = 'd'
    rule_to = u'disc'
    renames = (
#            ('nd', 'lb'),
#            ('a_th', 'tha'),
#            ('vsl_th', 'ths'),
#            ('w_th', 'thw'),
            )
#/set

    for exit_ in exits:
        p = exit_.params.get_dict()
        if p['rule'] == rule_from:
            print exit_.method.metasystem.id, p
            params = dict(p)
            params['par_type'] = type_
            params['rule'] = rule_to
            for frm, to in renames:
                params[to] = params.pop(frm)
            exit_.params = getattr(params_exit, type_ + '_' + rule_to)(**params)
            print exit_.params.get_dict()

            for system in exit_.method.metasystem.system_set.all():
                print 'FROM:', system.params
                new_params = system.params.replace('X' + rule_from, 'X' + rule_to)
                for frm, to in renames:
                    new_params = new_params.replace(frm + '\'', to + '\'')
                system.params = new_params
                print 'TO:', system.params
#                system.save()

            exit_.save()
            print "saved"
#            break


def mod_entries():
    '''
    rename a rule and parameters within it
    '''
    from metasystem.models import Entry
    from metasystem.parameters import params_entry
    entries = Entry.objects.all()

# set renames here:
    type_ = 'entry'
    short = 'N'
    rule_from = 'breakout'
    rule_to = u'bo'
    renames = (
#            ('nd', 'lb'),
#            ('a_th', 'tha'),
#            ('vsl_th', 'ths'),
#            ('price', 'pr'),
            )
#/set

    for entry in entries:
        p = entry.params.get_dict()
        if p['rule'] == rule_from:
            print entry.method.metasystem.id, p
            params = dict(p)
            params['par_type'] = type_
            params['rule'] = rule_to
            for frm, to in renames:
                params[to] = params.pop(frm)
            entry.params = getattr(params_entry, type_ + '_' + rule_to)(**params)
            print entry.params.get_dict()

            rule_f = short + rule_from
            rule_t = short + rule_to
            for system in entry.method.metasystem.system_set.all():
                print 'FROM:', system.params
                new_params = system.params.replace(rule_f, rule_t)
                for frm, to in renames:
                    new_params = new_params.replace(frm + '\'', to + '\'')
                system.params = new_params
                print 'TO:', system.params
                system.save()

            entry.save()
            print "saved"
            break


def mod_alloc():
    '''
    rename a rule and parameters within it
    '''
    from metasystem.models import MetaSystem
    from metasystem.parameters import params_alloc
    mss = MetaSystem.objects.all()

# set renames here:
    type_ = 'alloc'
    short = 'A'
    rule_from = 'risk'
    rule_to = u'r'
    renames = (
#            ('nd', 'lb'),
#            ('a_th', 'tha'),
#            ('vsl_th', 'ths'),
#            ('price', 'pr'),
            )
#/set

    for ms in mss:
        p = ms.allocation.get_dict()
        if p['rule'] == rule_from:
            print ms.id, p
            params = dict(p)
            params['par_type'] = type_
            params['rule'] = rule_to
            for frm, to in renames:
                params[to] = params.pop(frm)
            ms.allocation = getattr(params_alloc, type_ + '_' + rule_to)(**params)
            print ms.allocation.get_dict()

            rule_f = short + rule_from
            rule_t = short + rule_to
            for system in ms.system_set.all():
                print 'FROM:', system.params
                new_params = system.params.replace(rule_f, rule_t)
                for frm, to in renames:
                    new_params = new_params.replace(frm + '\'', to + '\'')
                system.params = new_params
                print 'TO:', system.params
                system.save()

            ms.save()
            print "saved"
            break


def mod_equity():
    '''
    rename a rule and parameters within it
    '''
    from metasystem.models import MetaSystem
    from metasystem.parameters import params_equity
    mss = MetaSystem.objects.all()
    type_ = 'equity'
    short = 'E'

# set renames here:
    rule_from = 'ter'
    rule_to = u'tr'
    renames = (
            ('exceed', 'xc'),
            ('pc_eq', 'pce'),
            ('pc_risk', 'prc'),
#            ('price', 'pr'),
            )
#/set

    for ms in mss:
        p = ms.equitymodel.get_dict()
        if p['rule'] == rule_from:
            print ms.id, p
            params = dict(p)
            params['par_type'] = type_
            params['rule'] = rule_to
            for frm, to in renames:
                params[to] = params.pop(frm)
            ms.equitymodel = getattr(params_equity, type_ + '_' + rule_to)(**params)
            print ms.equitymodel.get_dict()

            rule_f = short + rule_from
            rule_t = short + rule_to
            for system in ms.system_set.all():
                print 'FROM:', system.params
                new_params = system.params.replace(rule_f, rule_t)
                for frm, to in renames:
                    new_params = new_params.replace(frm + '\'', to + '\'')
                system.params = new_params
                print 'TO:', system.params
                system.save()

            ms.save()
            print "saved"
            break


def mod_mkttype():
    '''
    rename a rule and parameters within it
    '''
    from metasystem.models import MetaSystem
    from metasystem.parameters import params_market
    mss = MetaSystem.objects.all()
    type_ = 'market'
    short = 'M'

# set renames here:
    rule_from = 'order'
    rule_to = u'none'
    renames = (
#            ('price', 'pr'),
            )
#/set

    for ms in mss:
        p = ms.markettype.get_dict()
        if p['rule'] == rule_from:
            print ms.id, p
            params = dict(p)
            params['par_type'] = type_
            params['rule'] = rule_to
            for frm, to in renames:
                params[to] = params.pop(frm)
            ms.markettype = getattr(params_market, type_ + '_' + rule_to)(**params)
            print ms.markettype.get_dict()

#            rule_f = short + rule_from
#            rule_t = short + rule_to
#            for system in ms.system_set.all():
#                print 'FROM:', system.params
#                new_params = system.params.replace(rule_f, rule_t)
#                for frm, to in renames:
#                    new_params = new_params.replace(frm + '\'', to + '\'')
#                system.params = new_params
#                print 'TO:', system.params
#                system.save()

            ms.save()
            print "saved"
            break



