# -*- coding: utf-8 -*-

import telegram
from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _


class DjangoWebixSenderConfig(AppConfig):
    name = 'django_webix_sender'
    verbose_name = 'Django Webix Sender'

    def ready(self):
        from django_webix_sender.utils import my_import

        CONF = getattr(settings, "WEBIX_SENDER", None)

        if CONF is None:
            raise ImproperlyConfigured(_('`WEBIX_SENDER` is not configured in your settings.py file'))

        # Check configurations
        for send_method in CONF['send_methods']:
            # Check common keys
            if 'method' not in send_method:
                raise ImproperlyConfigured(_("`method` is not configured in send method"))
            if 'verbose_name' not in send_method:
                raise ImproperlyConfigured(_("`verbose_name` is not configured in send method"))
            if 'function' not in send_method:
                raise ImproperlyConfigured(_("`function` is not configured in send method"))
            if 'show_in_list' not in send_method:
                raise ImproperlyConfigured(_("`show_in_list` is not configured in send method"))
            if 'show_in_chat' not in send_method:
                raise ImproperlyConfigured(_("`show_in_chat` is not configured in send method"))

            # Try to import function
            my_import(send_method['function'])

            # Count method
            num = len([i for i in CONF['send_methods'] if i['method'] == send_method['method']])
            if num > 1:
                raise ImproperlyConfigured(
                    _('`{}` method is used {} times instead of 1'.format(send_method['method'], num))
                )

            # Init Email
            if send_method['method'] == 'email':
                # Check Email config
                if not 'config' in send_method or \
                    not 'from_email' in send_method['config']:
                    raise ImproperlyConfigured(_('Email `config` is not configured in your settings.py file'))

            # Init Skebby
            elif send_method['method'] == 'skebby':
                # Check Skebby config
                if not 'config' in send_method or \
                    not 'region' in send_method['config'] or \
                    not 'method' in send_method['config'] or \
                    not 'username' in send_method['config'] or \
                    not 'password' in send_method['config'] or \
                    not 'sender_string' in send_method['config']:
                    raise ImproperlyConfigured(_('Skebby `config` is not configured in your settings.py file'))

            # Init Telegram
            elif send_method['method'] == 'telegram':
                # Check Telegram config
                if not 'config' in send_method or \
                    not 'bot_token' in send_method['config']:
                    raise ImproperlyConfigured(_('Telegram `config` is not configured in your settings.py file'))
                # Update webhooks
                if 'webhooks' in send_method['config'] and \
                    isinstance(send_method['config']['webhooks'], list) and \
                    len(send_method['config']['webhooks']) > 0:
                    webhooks = send_method['config']['webhooks']
                    if not isinstance(webhooks, list):
                        webhooks = [webhooks]
                    bot = telegram.Bot(token=send_method['config']['bot_token'])
                    # Remove old webhooks
                    bot.deleteWebhook()
                    # Add new webhooks
                    for webhook in webhooks:
                        bot.setWebhook(webhook)
                # Update commands
                if 'commands' in send_method['config'] and \
                    isinstance(send_method['config']['commands'], list) and \
                    len(send_method['config']['commands']) > 0:
                    bot = telegram.Bot(token=send_method['config']['bot_token'])
                    bot.set_my_commands(send_method['config']['commands'])

            # Init storage
            elif send_method['method'] == 'storage':
                pass  # Nothing to check

        # Check attachments model
        app_label, model = CONF['attachments']['model'].lower().split(".")
        try:
            apps.get_model(app_label=app_label, model_name=model)
        except Exception:
            raise NotImplementedError(_('Attachment model `{}` is not valid'.format(CONF['attachments']['model'])))

        # Check extra
        if 'extra' in CONF and not isinstance(CONF['extra'], dict):
            raise NotADirectoryError('`extra` value must be a dict')

        # Try to import Attachments save function
        my_import(CONF['attachments']['save_function'])

        # Check recipients models
        for recipient in CONF['recipients']:
            app_label, model = recipient['model'].lower().split(".")
            try:
                apps.get_model(app_label=app_label, model_name=model)
            except Exception:
                raise NotImplementedError(_('Recipient model `{}` is not valid'.format(recipient['model'])))
