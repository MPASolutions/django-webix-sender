# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.mail import EmailMessage


def my_import(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


ISO_8859_1_limited = '@èéùìò_ !"#%\\\'()*+,-./0123456789:<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜabcdefghijklmnopqrstuvwxyzäöñüà'


def send_email(to, subject, body, from_email, recipient=None):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to]
    )
    email.content_subtype = "html"
    email.send()


def send_sms(to, body, recipient=None):
    raise NotImplementedError('`send_sms` method not implemented!')
