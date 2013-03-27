'''
metasystem/admin.py v0.1 120823

Created on 120823

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.contrib import admin
from metasystem.models import MetaSystem, Method, Entry, Exit, Group


class MetaSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'active', 'comments', 'startdate', 
                    'enddate', 'pool')
    ordering = ('-id',)


class MethodAdmin(admin.ModelAdmin):
    list_display = ('id', 'comments')
    ordering = ('-id',)


class EntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'comments')
    ordering = ('-id',)


class ExitAdmin(admin.ModelAdmin):
    list_display = ('id', 'comments')
    ordering = ('-id',)


class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'comments')
    ordering = ('-id',)


admin.site.register(MetaSystem, MetaSystemAdmin)
admin.site.register(Method, MethodAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Exit, ExitAdmin)
admin.site.register(Group, GroupAdmin)
