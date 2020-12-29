# -*- coding: utf-8 -*-

from django.conf import settings
from django.urls import path

from django_webix_sender.views import (
    SenderList, SenderGetList, SenderSend, DjangoWebixSenderWindow, InvoiceManagement,
    TelegramWebhookView
)

CONF = getattr(settings, "WEBIX_SENDER", None)

urlpatterns = [
    path('list', SenderList.as_view(), name="django_webix_sender.list"),
    path('getlist', SenderGetList.as_view(), name="django_webix_sender.getlist"),
    path('send', SenderSend.as_view(), name="django_webix_sender.send"),
    path('sender-window', DjangoWebixSenderWindow.as_view(), name='django_webix_sender.sender_window'),
    path('invoices', InvoiceManagement.as_view(), name='django_webix_sender.invoices'),
]

# Telegram
if CONF is not None and any(_send_method['method'] == 'telegram' for _send_method in CONF.get('send_methods', [])):
    urlpatterns.append(
        path('telegram/webhook/', TelegramWebhookView.as_view()),
    )
