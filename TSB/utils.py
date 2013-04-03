'''
TSB/utils.py v0.1 120815

Created on 120815@author: edwin

This module contains TSB related functions that are not app specific.
'''

from __future__ import division
from __future__ import absolute_import

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.middleware.csrf import get_token

import redis

import TSB.settings


def notify_admin(text):
    '''
    Send an email to the admin, <text> may be an error or warning.
    '''
#FIXME: sending email throws [Errno 61] Connection refused
    print 'TMP MESSAGE - TODO: make sending email work'
    print text
    return
    send_mail('TSB notification', text, 'edenka1993@gmail.com', 
            ['evo@se-technology.com'], fail_silently=False)


def init_redis():
    '''
    Returns a redis object based on the HUEY_CONFIG settings for Django.
    '''
    server = TSB.settings.HUEY_CONFIG['RESULT_STORE_CONNECTION']['host']
    return redis.Redis(server)


def make_link(name, text, kwargs=None, newtab=False, title=None):
    link = reverse(name, kwargs=kwargs)
    extra = ''
    if newtab:
        extra += ' target="_blank"'
    if title:
        extra += title
    return '<a href="{}"{}>{}</a>'.format(link, extra, text)



def get_choice(choices, choice):
    '''
    Lookup and return the human readable form of <choice> from <choices> where
    <choices> is a standard django CHOICES constant (tuple).
    '''
    return dict(choices)[choice]


class Notify():
    '''
    Puts notifications and confirmations in the status bar
    '''

    def __init__(self, notification):
        '''
        '''
        self.notification = notification
        self.replies = []
        self.request = None


    def set_replies(self, request, replies, name='reply'):
        '''
        Set replies for confirmation. <replies> is a tuple or list of strings
        that specify the text on the submit button and <name> is the name of 
        the submit button.
        '''
        self.request = request
        self.replies = replies
        self.name = name


    def render(self):
        '''
        Return html for use in the template
        '''
        html = '<form method="POST">{} '.format(self.notification)
        if self.request is not None:
            html += '<input type="hidden" name="csrfmiddlewaretoken" '\
                    'value="{}" />'.format(get_token(self.request))
        for reply in self.replies:
            html += '<input type="submit" name="{}" value="{}">'.format(
                    self.name, reply)
        html += '</form>'
        return mark_safe(html)
