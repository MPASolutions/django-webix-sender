# -*- coding: utf-8 -*-

from django.conf import settings
from django.urls import path, re_path

from django_webix_sender.views import (
    SenderListView, SenderGetListView, SenderSendView, SenderWindowView, SenderInvoiceManagementView,
    SenderTelegramWebhookView, SenderMessagesListView, SenderMessagesChatView, CheckAttachmentView
)

CONF = getattr(settings, "WEBIX_SENDER", None)

urlpatterns = [
    path('list', SenderListView.as_view(), name="django_webix_sender.list"),
    path('getlist', SenderGetListView.as_view(), name="django_webix_sender.getlist"),
    path('send', SenderSendView.as_view(), name="django_webix_sender.send"),
    path('sender-window', SenderWindowView.as_view(), name='django_webix_sender.sender_window'),
    path('invoices', SenderInvoiceManagementView.as_view(), name='django_webix_sender.invoices'),
    path('messages_list', SenderMessagesListView.as_view(), name='django_webix_sender.messages_list'),
    path('attachment_check', CheckAttachmentView.as_view(), name='django_webix_sender.attachment_check'),
    re_path('^messages_chat/(?P<section>users|messages)$', SenderMessagesChatView.as_view(),
            name='django_webix_sender.messages_chat'),
]

# Telegram
if CONF is not None and any(_send_method['method'] == 'telegram' for _send_method in CONF.get('send_methods', [])):
    urlpatterns.append(
        path('telegram/webhook/', SenderTelegramWebhookView.as_view()),
    )
