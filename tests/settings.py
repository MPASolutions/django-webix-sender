# -*- coding: utf-8

from __future__ import unicode_literals, absolute_import

import django

from django_webix_sender.send_methods.skebby.enums import SkebbyMessageType

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "=================================================="

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",

    "django_webix_sender",
]

ROOT_URLCONF = 'tests.urls'

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = (
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WEBIX_SENDER = {
    'send_methods': [
        {
            'method': 'email',
            'verbose_name': 'Send email',
            'function': 'django_webix_sender.send_methods.email.send',
            'config': {
                'from_email': 'info@mpasol.it'
            }
        },
        {
            'method': 'skebby',
            'verbose_name': 'Send sms',
            'function': 'django_webix_sender.send_methods.skebby.send',
            'config': {
                'region': "IT",
                'method': SkebbyMessageType.GP,
                'username': 'username',
                'password': 'password',
                'sender_string': 'Sender',
            }
        },
        {
            'method': 'telegram',
            'verbose_name': 'Send telegram',
            'function': 'django_webix_sender.send_methods.telegram.send',
            'config': {
                "bot_token": "token",
                "webhooks": [],
                'commands': [],
                'handlers': []
            }
        },
        {
            'method': 'storage',
            'verbose_name': 'Store online',
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
