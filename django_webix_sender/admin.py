# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin

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
    model = MessageRecipient


class MessageSentAdmin(admin.ModelAdmin):
    inlines = [MessageRecipientInline]


admin.site.register(MessageSent, MessageSentAdmin)
