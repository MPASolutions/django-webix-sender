# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django_webix_sender.models import MessageSent, MessageRecipient


class MessageRecipientInline(admin.TabularInline):
    model = MessageRecipient


class MessageSentAdmin(admin.ModelAdmin):
    inlines = [MessageRecipientInline]


admin.site.register(MessageSent, MessageSentAdmin)
