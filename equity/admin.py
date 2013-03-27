'''
system/admin.py v0.1 120823

Created on 120823

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.contrib import admin
from equity.models import Equity, Thumbnail


class EquityAdmin(admin.ModelAdmin):
    list_display = ('id', 'positions', 'date', 'cash', 'total')
    ordering = ('-id',)

class TNAdmin(admin.ModelAdmin):
    list_display = ('id', '_data')
    ordering = ('-id',)


admin.site.register(Equity, EquityAdmin)
admin.site.register(Thumbnail, TNAdmin)
