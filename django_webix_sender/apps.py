# -*- coding: utf-8 -*-

import phonenumbers
from django.apps import AppConfig, apps
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


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

            # Check Skebby config
            if send_method['function'] == 'django_webix_sender.send_methods.skebby.send_sms':
                if not hasattr(settings, 'CONFIG_SKEBBY') or \
                    not 'region' in settings.CONFIG_SKEBBY or \
                    not 'method' in settings.CONFIG_SKEBBY or \
                    not 'username' in settings.CONFIG_SKEBBY or \
                    not 'password' in settings.CONFIG_SKEBBY or \
                    not 'sender_string' in settings.CONFIG_SKEBBY:
                        raise Exception(_('`CONFIG_SKEBBY` is not configured in your settings.py file'))

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
