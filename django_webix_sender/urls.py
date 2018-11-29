# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import url

from django_webix_sender.views import SenderList, SenderGetList, SenderSend, DjangoWebixSenderWindow, InvoiceManagement

urlpatterns = [
    url(r'^list$', SenderList.as_view(), name="django_webix_sender.list"),
    url(r'^getlist$', SenderGetList.as_view(), name="django_webix_sender.getlist"),
    url(r'^send$', SenderSend.as_view(), name="django_webix_sender.send"),
    url(r'^sender-window$', DjangoWebixSenderWindow.as_view(), name='django_webix_sender.sender_window'),
    url(r'^invoices$', InvoiceManagement.as_view(), name='django_webix_sender.invoices'),
]
