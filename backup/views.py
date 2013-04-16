'''
backup/views.py v0.1 121009

Created on 121009

@author: edwin
'''
#TODO: implement as cmd line program
#CONSIDER: use compressed data (tar/bzip)
#CONSIDER: select whether to backup trades/equity

import datetime
import glob

#from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
#from django.core.management import call_command
from pyutillib.string_utils import random_string

import subprocess



#def get_models():
#    '''
#    Do this automatically??
#    '''
#    models = []
#    models.extend(['bugtracker.Tag', 'bugtracker.Ticket'])
#    models.extend(['pricemanager.Stock', 'pricemanager.Pool', 
#            'pricemanager.StockPoolDates']) # skip price
#    models.extend(['metasystem.MetaSystem', 'metasystem.Method', 
#            'metasystem.Entry', 'metasystem.Exit'])
#    models.extend(['system.Bookmark', 'system.System'])
#    models.extend(['equity.Thumbnail'])
##    models.extend(['equity.Equity'])
##    models.extend(['tradesignal.Trade'])
#    return models


@login_required
def backup(request, action=None, file_id=None):
    '''
    Backup and restore
    Using django dumpdata was too slow and took too much RAM, so backups are
    now made using pg_dump (straight from postgresql)
TODO: run this asynchronously
TODO: use subprocess properly using args, PIPE, etc
    '''
    message = ''
    if not file_id and action == 'make_backup':
        backup_folder = '/tmp/'
        filename = 'backup_{}_{}.gz'.format(
                        datetime.date.today().isoformat(), random_string(4))
        command = 'pg_dump -U postgres -Fc django_TSB > {}{}'.format(
                                                    backup_folder, filename)
        subprocess.call(command, shell=True)

#        outfile = open(filename, 'w')
#        models = get_models()
#        call_command('dumpdata', *models, format='json', indent=0, 
#                                                                stdout=outfile)
#        outfile.close()
#        message = {'backup': True, 'text': 'Backup \"{}\" created'.format(
#                                                                    filename)}

    file_list = {}
    for filename in glob.glob('/tmp/backup_????-??-??_*.gz'):
        file_list[filename[-7:-3]] = filename
#    file_list = {}
#    for filename in glob.glob('backup_????-??-??_*.json'):
#        file_list[filename[-9:-5]] = filename

    if file_id:
        if action == 'restore':
            message = {'restore': 'confirmed', 'filename': file_list[file_id], 
                                                    'file_id': file_id}
        elif action == 'restore_confirmed':
            message = {'restore': True, 'text': 
                       'Restore not implemented yet, use pg_restore manually'}
#TODO: implement restore
#        command = 'pg_restore -U postgres -Fc {}'.format(filename)

#            call_command('loaddata', filename)
#            message = {'restore': True, 'text': 'Data from {} restored'.format(
#                                                                    filename)}
        else:
            raise ValueError('action {} is invalid'.format(action))
    return render(request, 'backup.html', 
            {'file_list': file_list,
             'message': message})
