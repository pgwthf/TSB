'''
system/admin.py v0.1 120823

Created on 120823

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.contrib import admin
from system.models import System, Bookmark


class SystemAdmin(admin.ModelAdmin):
    list_display = ('id', 'metasystem', 'active', 'enddate', 'params',
                    'max_win', 'max_loss', 'trades_pa',
                    'reliability', 'expectancy', 'exp_p_day', )
    ordering = ('-id',)
    list_filter = ('metasystem',)

class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('id', 'section', 'comments' )
    ordering = ('-id',)


admin.site.register(System, SystemAdmin)
admin.site.register(Bookmark, BookmarkAdmin)
