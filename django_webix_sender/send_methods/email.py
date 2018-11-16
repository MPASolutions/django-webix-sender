# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import six
from django.conf import settings
from django.core.mail import EmailMessage

from django_webix_sender.models import MessageSent, MessageRecipient


def send_email(recipients, subject, body, message_sent):
    # Controllo correttezza parametri
    if not isinstance(recipients, dict) or \
        'valids' not in recipients or not isinstance(recipients['valids'], list) or \
        'duplicates' not in recipients or not isinstance(recipients['duplicates'], list) or \
        'invalids' not in recipients or not isinstance(recipients['invalids'], list):
        raise Exception("`recipients` must be a dict")
    if not isinstance(subject, six.string_types):
        raise Exception("`subject` must be a string")
    if not isinstance(body, six.string_types):
        raise Exception("`body` must be a string")
    if not isinstance(message_sent, MessageSent):
        raise Exception("`message_sent` must be MessageSent instance")

    # Per ogni istanza di destinatario ciclo
    for recipient, recipient_address in recipients['valids']:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_address]
        )
        email.content_subtype = "html"

        try:
            email.send()

            _extra = {'status': "Email {} ({}) inviata con successo".format(recipient_address, recipient)}
            _status = 'success'
        except Exception as e:
            _extra = {'status': "{}".format(e)}
            _status = 'failed'

        MessageRecipient.objects.create(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=1,
            status=_status,
            recipient_address=recipient_address,
            extra=_extra,
        )

    # Salvo i destinatari senza numero e quindi ai quali non è stato inviato il messaggio
    for recipient in recipients['invalids']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='invalid',
            extra={'status': "Email non presente ({}) e quindi non inviata".format(recipient)}
        )
        message_recipient.save()

    # Salvo i destinatari duplicati e quindi ai quali non è stato inviato il messaggio
    for recipient, recipient_address in recipients['duplicates']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='duplicate',
            recipient_address=recipient_address,
            extra={'status': "Email duplicata".format(recipient)}
        )
        message_recipient.save()

    return message_sent
