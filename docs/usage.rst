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

    from django.utils.translation import ugettext_lazy as _

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
                'datatable_fields': ['user', 'name', 'sms', 'email']
            },
            {
                'model': 'django_webix_sender.ExternalSubject',
                'datatable_fields': ['user', 'name', 'sms', 'email']
            },
        ],
        'invoices_period': 'bimestrial'
    }


.. attribute:: WEBIX_SENDER['send_methods']

    Defines the allowed send methods.

    There are two allowed methods type:

    - ``sms``

    - ``email``


    The methods already implemented in this package are:

    - ``django_webix_sender.send_methods.email.send_email``

        The default Django email sender.

        .. code:: python

            {
                'method': 'email',
                'verbose_name': _('Send email'),
                'function': 'django_webix_sender.send_methods.email.send_email'
            }


    - ``django_webix_sender.send_methods.skebby.send_sms``

        Skebby sms APIs.

        .. code:: python

            {
                'method': 'sms',
                'verbose_name': _('Send sms with Skebby'),
                'function': 'django_webix_sender.send_methods.skebby.send_sms'
            }

    - ``django_webix_sender.send_methods.skebby.send_sms_old``

        Old Skebby sms APIs.

        .. code:: python

            {
                'method': 'sms',
                'verbose_name': _('Send sms with Skebby'),
                'function': 'django_webix_sender.send_methods.skebby.send_sms_old'
            },


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
            'datatable_fields': ['user', 'name', 'sms', 'email']
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

Create a subclass of ``DjangoWebixSender`` and define ``get_sms``, ``get_email``, ``get_sms_related`` and ``get_email_related`` properties.

.. code-block:: python

    class Recipients(DjangoWebixSender):
        name = models.CharField(max_length=255, verbose_name=_('Name'))
        sms = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Sms'))
        email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email'))
        parent = models.ForeignKey('self', blank=True, null=True, verbose_name=_('Parent'))

        @property
        def get_sms(self):
            return self.sms

        @property
        def get_email(self):
            return self.email

        @property
        def get_sms_related(self):
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
            message_recipient = MessageRecipient(
                message_sent=message_sent,
                recipient=recipient,
                sent_number=1,
                status='success',
                recipient_address=recipient_address
            )
            message_recipient.save()
        for recipient in recipients['invalids']:
            pass
        for recipient, recipient_address in recipients['duplicates']:
            pass
        return message_sent
