Quick Start
===========

Install
-------

``django-webix-sender`` is available on :samp:`https://pypi.python.org/pypi/django-webix/` install it simply with:

.. code-block:: bash

    $ pip install django-webix-sender


Configure
---------

Settings
~~~~~~~~

Add ``django_webix_sender`` to your ``INSTALLED_APPS``

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'django_webix_sender',
        # ...
    ]

Add ``django-webix-sender`` URLconf to your project ``urls.py`` file

.. code-block:: python

    from django.conf.urls import url, include

    urlpatterns = [
        # ...
        url(r'^django-webix-sender/', include('django_webix_sender.urls')),
        # ...
    ]

.. warning::

    This package requires a project with ``django-webix`` setted up.


Usage
-----

Settings
~~~~~~~~

Create the models (e.g. <app_name>/models.py)

.. code-block:: python

    from django.utils.translation import gettext_lazy as _
    from django_webix_sender.send_methods.telegram.handlers import start, check_user

    WEBIX_SENDER = {
        'send_methods': [
            {
                'method': 'skebby',
                'verbose_name': _('Send sms'),
                'function': 'django_webix_sender.send_methods.skebby.send',
                'config': {
                    'region': "IT",
                    'method': SkebbyMessageType.GP,
                    'username': 'username',
                    'password': '********',
                    'sender_string': 'Sender',
                }
            },
            {
                'method': 'email',
                'verbose_name': _('Send email'),
                'function': 'django_webix_sender.send_methods.email.send',
                'config': {
                    'from_email': 'noreply@email.com'
                }
            },
            {
                'method': 'telegram',
                'verbose_name': _('Send telegram'),
                'function': 'django_webix_sender.send_methods.telegram.send',
                'config': {
                    "bot_token": "**********:**********",
                    "webhooks": [
                        "https://mysite.com/django-webix-sender/telegram/webhook/"
                    ],
                    'commands': [
                        BotCommand("start", "Start info"),
                    ],
                    'handlers': [
                        {"handler": MessageHandler(Filters.all, check_user), "group": -1},  # Check enabled users
                        CommandHandler("start", start),  # Example
                    ]
                }
            },
            {
                'method': 'storage',
                'verbose_name': _('Store online'),
                'function': 'django_webix_sender.send_methods.storage.send',
            },
        ],
        'attachments': {
            'model': 'django_webix_sender.MessageAttachment',
            'upload_folder': 'sender/',
            'save_function': 'django_webix_sender.models.save_attachments'
        },
        'typology_model': {
            'enabled': True,
            'required': False
        },
        'recipients': [
            {
                'model': 'django_webix_sender.Customer',
                'datatable_fields': ['user', 'name', 'sms', 'email', 'telegram']
            },
            {
                'model': 'django_webix_sender.ExternalSubject',
                'datatable_fields': ['user', 'name', 'sms', 'email', 'telegram']
            },
        ],
        'invoices_period': 'bimestrial'
    }


.. attribute:: WEBIX_SENDER['send_methods']

    Defines the allowed send methods.

    There are three allowed methods type:

    - ``skebby``

    - ``email``

    - ``telegram``

    - ``storage``


    The methods already implemented in this package are:

    - ``django_webix_sender.send_methods.email.send``

        The default Django email sender.

        .. code:: python

            {
                'method': 'email',
                'verbose_name': _('Send email'),
                'function': 'django_webix_sender.send_methods.email.send',
                'config': {
                    'from_email': 'noreply@email.com'
                }
            }


    - ``django_webix_sender.send_methods.skebby.send``

        Skebby sms APIs.

        .. code:: python

            {
                'method': 'skebby',
                'verbose_name': _('Send sms with Skebby'),
                'function': 'django_webix_sender.send_methods.skebby.send',
                'config': {
                    'region': "IT",
                    'method': SkebbyMessageType.GP,
                    'username': 'username',
                    'password': '********',
                    'sender_string': 'Sender',
                }
            }

    - ``django_webix_sender.send_methods.telegram.send``

        Telegram APIs.

        .. code:: python

            {
                'method': 'telegram',
                'verbose_name': _('Send with Telegram'),
                'function': 'django_webix_sender.send_methods.telegram.send',
                'config': {
                    "bot_token": "**********:**********",
                    "webhooks": [
                        "https://mysite.com/django-webix-sender/telegram/webhook/"
                    ],
                    'commands': [
                        BotCommand("start", "Start info"),
                    ],
                    'handlers': [
                        {"handler": MessageHandler(Filters.all, check_user), "group": -1},  # Check enabled users
                        CommandHandler("start", start),  # Example
                    ]
                }
            }

    - ``django_webix_sender.send_methods.storage.send``

        Storage method

        .. code:: python

            {
                'method': 'storage',
                'verbose_name': _('Store online'),
                'function': 'django_webix_sender.send_methods.storage.send',
            }


.. attribute:: WEBIX_SENDER['attachments']

    Defines the attachments model and the method to store files.

    .. code-block:: python

        {
            'model': 'django_webix_sender.MessageAttachment',
            'upload_folder': 'sender/',
            'save_function': 'django_webix_sender.models.save_attachments'
        }


.. attribute:: WEBIX_SENDER['typology_model']

    Defines if the message typology are enabled.

    .. code-block:: python

        {
            'enabled': True,
            'required': False
        }


.. attribute:: WEBIX_SENDER['recipients']

    Defines the models to show as a list of recipients.

    .. code-block:: python

        {
            'model': 'django_webix_sender.Customer',
            'datatable_fields': ['user', 'name', 'sms', 'email', 'telegram']
        }


Base Template
~~~~~~~~~~~~~

Create a base html template (e.g. <app_name>/templates/base.html)

.. code-block:: html

    {% load i18n %}

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>

        {% include "django_webix/static_meta.html" %}
    </head>
    <body>
    </body>

    <script type="text/javascript" charset="utf-8">
        webix.ready(function () {
            webix.ui({
                id: 'content_right',
                rows: []
            });

            webix.extend($$('content_right'), webix.OverlayBox);

            load_js('{% url 'django_webix_sender.list' %}');
        });
    </script>
    </html>


Customization
-------------

Recipient class
~~~~~~~~~~~~~~~

Create a subclass of ``DjangoWebixSender`` and define ``get_sms``, ``get_telegram``, ``get_email``, ``get_sms_related``, ``get_telegram_related`` and ``get_email_related`` properties.

.. code-block:: python

    class Recipients(DjangoWebixSender):
        name = models.CharField(max_length=255, verbose_name=_('Name'))
        sms = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Sms'))
        telegram = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Telegram'))
        email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email'))
        parent = models.ForeignKey('self', blank=True, null=True, verbose_name=_('Parent'))

        @property
        def get_sms(self):
            return self.sms

        @property
        def get_telegram(self):
            return self.telegram

        @property
        def get_email(self):
            return self.email

        @property
        def get_sms_related(self):
            return self.parent_set.all()

        @property
        def get_telegram_related(self):
            return self.parent_set.all()

        @property
        def get_email_related(self):
            return self.parent_set.all()


Send method
~~~~~~~~~~~

.. code-block:: python

    def send_sms(recipients, body, message_sent):

        # ...
        # API gateway sms send
        # ...

        for recipient, recipient_address in recipients['valids']:
            MessageRecipient.objects.create(
                message_sent=message_sent,
                recipient=recipient,
                sent_number=1,
                status='success',
                recipient_address=recipient_address
            )
        for recipient, recipient_address in recipients['invalids']:
            pass
        for recipient, recipient_address in recipients['duplicates']:
            pass
        return message_sent
