# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import importlib

ISO_8859_1_limited = '@èéùìò_ !"#%\\\'()*+,-./0123456789:<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜabcdefghijklmnopqrstuvwxyzäöñüà'


def my_import(name):
    module, function = name.rsplit('.', 1)
    component = importlib.import_module(module)
    return getattr(component, function)


def send_email(recipients, subject, body, message_sent):
    raise NotImplementedError('`send_email` method not implemented!')


def send_sms(recipients, body, message_sent):
    raise NotImplementedError('`send_sms` method not implemented!')
