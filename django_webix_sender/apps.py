# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.apps import AppConfig, apps
from django.utils.translation import ugettext_lazy as _


class DjangoWebixSenderConfig(AppConfig):
    name = 'django_webix_sender'
    verbose_name = 'Django Webix Sender'

    def ready(self):
        from django_webix_sender.settings import CONF
        from django_webix_sender.utils import my_import

        if CONF is None:
            raise Exception(_('`WEBIX_SENDER` is not configured in your settings.py file'))

        # Try to import all functions
        for send_method in CONF['send_methods']:
            my_import(send_method['function'])

        app_label, model = CONF['attachments']['model'].lower().split(".")
        try:
            apps.get_model(app_label=app_label, model_name=model)
        except Exception:
            raise NotImplementedError(_('Attachment model is not valid'))

        # Try to import Attachments save function
        my_import(CONF['attachments']['save_function'])

        for recipient in CONF['recipients']:
            app_label, model = recipient['model'].lower().split(".")
            try:
                model_class = apps.get_model(app_label=app_label, model_name=model)
            except Exception:
                raise NotImplementedError(_('Recipient model is not valid'))
