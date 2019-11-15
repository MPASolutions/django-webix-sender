# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.urls import path

from django_webix_sender.views import SenderList, SenderGetList, SenderSend, DjangoWebixSenderWindow, InvoiceManagement

urlpatterns = [
    path('list', SenderList.as_view(), name="django_webix_sender.list"),
    path('getlist', SenderGetList.as_view(), name="django_webix_sender.getlist"),
    path('send', SenderSend.as_view(), name="django_webix_sender.send"),
    path('sender-window', DjangoWebixSenderWindow.as_view(), name='django_webix_sender.sender_window'),
    path('invoices', InvoiceManagement.as_view(), name='django_webix_sender.invoices'),
]
