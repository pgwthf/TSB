from __future__ import division
from __future__ import absolute_import

from django.contrib import admin
from channel.models import Channel


class ChannelAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'lookback', 'angle', 'width', 'bottom')
    date_hierarchy = 'date'
    ordering = ('stock', 'date')
    list_filter = ('lookback', 'stock')


admin.site.register(Channel, ChannelAdmin)
