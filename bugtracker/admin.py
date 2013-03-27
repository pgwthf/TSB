from django.contrib import admin
from bugtracker.models import Ticket, Tag, Task

class TicketAdmin(admin.ModelAdmin):
    list_display = ('priority', 'title', 'summary', 'status', 'tag_list', 'modified')
    list_display_links = ('title',)
    list_filter = ['modified', 'status']
    search_fields = ['title', 'description']
    date_hierarchy = 'modified'
    ordering = ['priority']
    actions = ['close_tickets']

    def close_tickets(self, request, queryset):
        tickets_updated = queryset.update(status='closed')
        if tickets_updated == 1:
            tickets_msg = "1 ticket was"
        else:
            tickets_msg = "%s tickets were" % tickets_updated
        self.message_user(request, "%s succesfully marked as closed." % tickets_msg)
    close_tickets.short_description = 'Close selected tickets'


class TagAdmin(admin.ModelAdmin):
    pass

admin.site.register(Ticket, TicketAdmin)
admin.site.register(Tag, TagAdmin)



#from django.contrib import admin
#from bugtracker.pomodoro.models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'pomodoros', 'is_done')
    list_display_links = ('title',)
    list_filter = ['date', 'is_done']
    search_fields = ['title']
    date_hierarchy = 'date'
    ordering = ['-date']
    list_editable = ['pomodoros']
    actions = ['done_tasks']

    def done_tasks(self, request, queryset):
        tasks_updated = queryset.update(is_done=True)
        if tasks_updated == 1:
            tasks_msg = "1 task was"
        else:
            tasks_msg = "%s tasks were" % tasks_updated
        self.message_user(request, "%s succesfully marked as done." % tasks_msg)
    done_tasks.short_description = 'Close selected tasks'

admin.site.register(Task, TaskAdmin)