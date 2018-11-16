# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from django_webix_sender.models import MessageSent, MessageRecipient
from django_webix_sender.settings import CONF

if any(_recipients['model'] == 'django_webix_sender.Customer' for _recipients in CONF['recipients']):
    from django_webix_sender.models import Customer, CustomerTypology

    admin.site.register(Customer)
    admin.site.register(CustomerTypology)

if any(_recipients['model'] == 'django_webix_sender.ExternalSubject' for _recipients in CONF['recipients']):
    from django_webix_sender.models import ExternalSubject, ExternalSubjectTypology

    admin.site.register(ExternalSubject)
    admin.site.register(ExternalSubjectTypology)

if CONF['attachments']['model'] == 'django_webix_sender.MessageAttachment':
    from django_webix_sender.models import MessageAttachment

    admin.site.register(MessageAttachment)

if CONF['typology_model']['enabled']:
    from django_webix_sender.models import MessageTypology

    admin.site.register(MessageTypology)


class MessageRecipientInline(admin.TabularInline):
    _fields = ['recipient', 'recipient_address', 'sent_number', 'status', 'extra', 'creation_date', 'modification_date']

    model = MessageRecipient
    extra = 0
    fields = _fields
    readonly_fields = _fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MessageSentAdmin(admin.ModelAdmin):
    _fields = [
        'send_method', 'subject', 'body', 'cost', 'invoiced', 'user', 'sender', 'extra', 'attachments',
        'creation_date', 'modification_date'
    ]
    if CONF['typology_model']['enabled']:
        _fields.append('typology')

    inlines = [MessageRecipientInline]
    list_display = (
        'id', '_method', '_function', 'subject', 'body', 'cost', 'invoiced', 'user', 'sender',
        'creation_date', 'modification_date'
    )
    fields = _fields
    readonly_fields = _fields

    search_fields = ('send_method', 'user', 'sender', 'subject', 'body')
    list_filter = (
        'send_method', 'user', 'cost', 'invoiced', 'sender', 'creation_date', 'modification_date'
    )

    def _method(self, obj):
        method, function = obj.send_method.split(".", 1)
        return method

    _method.short_description = _('Method')

    def _function(self, obj):
        method, function = obj.send_method.split(".", 1)
        return function

    _function.short_description = _('Function')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(MessageSent, MessageSentAdmin)
