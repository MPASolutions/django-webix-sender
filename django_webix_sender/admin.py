# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin
from django.db.models import Count, Sum, Case, When, IntegerField
from django.utils.translation import ugettext_lazy as _

from django_webix_sender.models import MessageSent, MessageRecipient
from django_webix_sender.settings import CONF

if CONF is not None and \
    any(_recipients['model'] == 'django_webix_sender.Customer' for _recipients in CONF['recipients']):
    from django_webix_sender.models import Customer, CustomerTypology

    admin.site.register(Customer)
    admin.site.register(CustomerTypology)

if CONF is not None and \
    any(_recipients['model'] == 'django_webix_sender.ExternalSubject' for _recipients in CONF['recipients']):
    from django_webix_sender.models import ExternalSubject, ExternalSubjectTypology

    admin.site.register(ExternalSubject)
    admin.site.register(ExternalSubjectTypology)

if CONF is not None and \
    CONF['attachments']['model'] == 'django_webix_sender.MessageAttachment':
    from django_webix_sender.models import MessageAttachment

    admin.site.register(MessageAttachment)

if CONF is not None and \
    CONF['typology_model']['enabled']:
    from django_webix_sender.models import MessageTypology

    admin.site.register(MessageTypology)


class MessageRecipientInline(admin.TabularInline):
    _fields = ['recipient', 'recipient_address', 'sent_number', 'status', 'extra', 'creation_date',
               'modification_date']

    model = MessageRecipient
    extra = 0
    fields = _fields
    readonly_fields = _fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MessageSent)
class MessageSentAdmin(admin.ModelAdmin):
    _fields = [
        'send_method', 'subject', 'body', 'cost', 'invoiced', 'user', 'sender', 'extra', 'attachments',
        'creation_date', 'modification_date'
    ]
    if CONF is not None and CONF['typology_model']['enabled']:
        _fields.append('typology')

    inlines = [MessageRecipientInline]
    list_display = (
        'id', '_method', '_function', 'subject', 'body', 'cost', 'recipients_count', 'recipients_success',
        'recipients_failed', 'recipients_unknown', 'recipients_invalid', 'recipients_duplicate', 'invoiced', 'user',
        'sender', 'creation_date', 'modification_date'
    )
    fields = _fields
    readonly_fields = _fields

    search_fields = ('send_method', 'user', 'sender', 'subject', 'body')
    list_filter = (
        'send_method', 'user', 'cost', 'invoiced', 'sender', 'creation_date', 'modification_date'
    )

    def get_queryset(self, request):
        qs = super(MessageSentAdmin, self).get_queryset(request)
        return qs.annotate(
            recipients_count=Count('messagerecipient'),
            recipients_success=Sum(Case(
                When(messagerecipient__status='success', then=1), default=0, output_field=IntegerField()
            )),
            recipients_failed=Sum(Case(
                When(messagerecipient__status='failed', then=1), default=0, output_field=IntegerField()
            )),
            recipients_unknown=Sum(Case(
                When(messagerecipient__status='unknown', then=1), default=0, output_field=IntegerField()
            )),
            recipients_invalid=Sum(Case(
                When(messagerecipient__status='invalid', then=1), default=0, output_field=IntegerField()
            )),
            recipients_duplicate=Sum(Case(
                When(messagerecipient__status='duplicate', then=1), default=0, output_field=IntegerField()
            ))
        )

    def recipients_count(self, obj):
        return obj.recipients_count

    recipients_count.short_description = _('Total recipients')
    recipients_count.admin_order_field = 'recipients_count'

    def recipients_success(self, obj):
        return obj.recipients_success

    recipients_success.short_description = _('Success recipients')
    recipients_success.admin_order_field = 'recipients_success'

    def recipients_failed(self, obj):
        return obj.recipients_failed

    recipients_failed.short_description = _('Failed recipients')
    recipients_failed.admin_order_field = 'recipients_failed'

    def recipients_unknown(self, obj):
        return obj.recipients_unknown

    recipients_unknown.short_description = _('Unknown recipients')
    recipients_unknown.admin_order_field = 'recipients_unknown'

    def recipients_invalid(self, obj):
        return obj.recipients_invalid

    recipients_invalid.short_description = _('Invalid recipients')
    recipients_invalid.admin_order_field = 'recipients_invalid'

    def recipients_duplicate(self, obj):
        return obj.recipients_duplicate

    recipients_duplicate.short_description = _('Duplicate recipients')
    recipients_duplicate.admin_order_field = 'recipients_duplicate'

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
