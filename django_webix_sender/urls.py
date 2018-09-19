# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf.urls import url

from django_webix_sender.views import SenderList, SenderGetList, SenderSend

urlpatterns = [
    url(r'^list$', SenderList.as_view(), name="django_webix_sender.list"),
    url(r'^getlist$', SenderGetList.as_view(), name="django_webix_sender.getlist"),
    url(r'^send$', SenderSend.as_view(), name="django_webix_sender.send"),
]
