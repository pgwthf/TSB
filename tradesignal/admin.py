'''
tradesignal/admin.py v0.1 121002

Created on 121002

@author: edwin
'''

from __future__ import division
from __future__ import absolute_import

from django.contrib import admin
from tradesignal.models import Trade


class TradeAdmin(admin.ModelAdmin):
    list_display = ('system', 'stock', 'method', 'volume', 'price_entry', 
                    'date_entry', 'price_exit', 'date_exit')
    search_fields = ('system',)
    ordering = ('-id',)


admin.site.register(Trade, TradeAdmin)
