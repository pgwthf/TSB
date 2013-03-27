from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=6, blank=True)

    def __unicode__(self):
        return self.name

class Ticket(models.Model):
    PRIORITIES = (
        (0, u'High'),
        (1, u'Medium'),
        (2, u'Low'),
    )
    STATUSES = (
        ('open', u'Open'),
        ('in_progress', u'In progress'),
        ('closed', u'Closed'),
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default='open', choices=STATUSES)
    tags = models.ManyToManyField(Tag, blank=True)
    priority = models.PositiveIntegerField(default=1, choices=PRIORITIES)

    def __unicode__(self):
        return self.title

    def tag_list(self):
        tags = []
        for tag in self.tags.all():
            if tag.color_code:
                tags.append('<span style="padding: 0 2px; background-color: #%s;">%s</span>' % (tag.color_code, tag.name))
            else:
                tags.append('<span>%s</span>' % tag.name)
        return " ".join(tags)
    tag_list.short_description = 'Tags'
    tag_list.allow_tags = True

    def summary(self):
        MAX_LENGTH = 26 
        if len(self.description) > MAX_LENGTH:
            return "%s..." % self.description[:MAX_LENGTH]
        else:
            return self.description
    summary.short_description = 'Description'

import datetime
#from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField(default=datetime.datetime.today())
    pomodoros = models.PositiveIntegerField(default=0)
    is_done = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.title