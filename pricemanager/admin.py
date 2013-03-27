from __future__ import division
from __future__ import absolute_import

from django.contrib import admin
from pricemanager.models import Stock, Price, Pool, StockPoolDates


class StockAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'currency', 'startdate', 'enddate',)
    search_fields = ('name',)
    list_filter = ('currency',)
    date_hierarchy = 'startdate'
    ordering = ('name',)


class PriceAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'open', 'close', 'high', 'low', 'volume',)
    date_hierarchy = 'date'
    ordering = ('stock', 'date')
    list_filter = ('stock',)


class PoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'index', 'startdate', 'enddate',
                                                            'stock_string')
    filter_horizontal = ('members',)
    ordering = ('name',)


class StockPoolDatesAdmin(admin.ModelAdmin):
    list_display = ('stock', 'pool', 'startdate', 'enddate')
    ordering = ('pool', 'stock')

    def __init__(self, model, admin_site):
        self.form.admin_site = admin_site 
        super(StockPoolDatesAdmin, self).__init__(model, admin_site)


admin.site.register(Stock, StockAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(Pool, PoolAdmin)
admin.site.register(StockPoolDates, StockPoolDatesAdmin)
