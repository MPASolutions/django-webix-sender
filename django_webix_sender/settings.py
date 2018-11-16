# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings

CONF = getattr(settings, "WEBIX_SENDER", None)

"""
Sample settings `WEBIX_SENDER` configuration

WEBIX_SENDER = {
    'send_methods': [
        {
            'method': 'sms',
            'verbose_name': _('Send sms'),
            'function': 'django_webix_sender.utils.send_sms'
        },
        {
            'method': 'email',
            'verbose_name': _('Send email'),
            'function': 'django_webix_sender.utils.send_email'
        }
    ],
    'attachments': {
        'model': 'django_webix_sender.MessageAttachment',
        'upload_folder': 'sender/',  # TODO: fare in modo di passare una funzione
        'save_function': 'django_webix_sender.models.save_attachments'
    },
    'typology_model': {
        'enabled': True,
        'required': False
    },
    'recipients': [
        {
            'model': 'django_webix_sender.Customer',
            'datatable_fields': ['user', 'name', 'sms', 'email']
        },
        {
            'model': 'django_webix_sender.ExternalSubject',
            'datatable_fields': ['user', 'name', 'sms', 'email']
        },
    ],
    'invoices_period': 'bimestrial'
}
"""
