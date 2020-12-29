# -*- coding: utf-8 -*-

from typing import Dict, List

import six
from django.conf import settings

from django_webix_sender.send_methods.skebby.enums import SkebbyBoolean
from django_webix_sender.send_methods.skebby.exceptions import SkebbyException
from django_webix_sender.send_methods.skebby.gateway import Skebby


def send(recipients: Dict[str, List[int]], body: str, message_sent):
    """
    Send Sebby sms

    :param recipients: Dict {'<app_label>.<model>': [<id>, <id>]}
    :param body: Body of message
    :param message_sent: MessageSent instance
    :return: MessageSent instance
    """

    from django_webix_sender.models import MessageRecipient, MessageSent

    if 'django_webix_sender' not in settings.INSTALLED_APPS:
        raise Exception("Django Webix Sender is not in INSTALLED_APPS")

    # Controllo correttezza parametri
    if not isinstance(recipients, dict) or \
        'valids' not in recipients or not isinstance(recipients['valids'], list) or \
        'duplicates' not in recipients or not isinstance(recipients['duplicates'], list) or \
        'invalids' not in recipients or not isinstance(recipients['invalids'], list):
        raise Exception("`recipients` must be a dict")
    if not isinstance(body, six.string_types):
        raise Exception("`body` must be a string")
    if not isinstance(message_sent, MessageSent):
        raise Exception("`message_sent` must be MessageSent instance")

    result = {'status': 'failed'}  # Default failed, cambia poi se inviato con successo
    sent_per_recipient = 0

    try:
        CONFIG_SKEBBY = next(
            (item for item in settings.WEBIX_SENDER['send_methods'] if item["method"] == "skebby"), {}
        ).get("config")

        # Connection
        skebby = Skebby()
        skebby.authentication.session_key(
            username=CONFIG_SKEBBY['username'],
            password=CONFIG_SKEBBY['password']
        )

        # Set message configuration
        send_configuration = {
            "message_type": CONFIG_SKEBBY['method'],
            "message": body,
            "recipient": [number for _, number in recipients['valids']],
            "sender": CONFIG_SKEBBY['sender_string'],
            "return_credits": SkebbyBoolean.TRUE
        }
        if 'encoding' in CONFIG_SKEBBY:
            send_configuration['encoding'] = CONFIG_SKEBBY['encoding']
        if 'truncate' in CONFIG_SKEBBY:
            send_configuration['truncate'] = CONFIG_SKEBBY['truncate']
        if 'max_fragments' in CONFIG_SKEBBY:
            send_configuration['max_fragments'] = CONFIG_SKEBBY['max_fragments']
        if 'allow_invalid_recipients' in CONFIG_SKEBBY:
            send_configuration['allow_invalid_recipients'] = CONFIG_SKEBBY['allow_invalid_recipients']

        # Send message
        result = skebby.sms_send.send_sms(**send_configuration)
        result['status'] = 'success'
    except SkebbyException as e:
        result['error'] = '{}'.format(e)

    # Setto il numero dell'ordine per recuperare successivamente lo stato dei vari messaggi
    if result['status'] == 'success' and 'total_sent' in result:
        sent_per_recipient = int(result['total_sent']) / len(recipients['valids'])

    # Per ogni utente con numero creo un record
    for recipient, recipient_address in recipients['valids']:
        _result = ""
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=sent_per_recipient,
            status='unknown' if result['status'] == 'success' else 'failed',  # Sconosciuto se con successo
            recipient_address=recipient_address
        )
        message_recipient.save()

    # Salvo i destinatari senza numero e quindi ai quali non è stato inviato il messaggio
    for recipient, recipient_address in recipients['invalids']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='invalid',
            recipient_address=recipient_address,
            extra={'status': "Mobile number not present or not valid ({}) and therefore SMS not sent".format(recipient)}
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
            extra={'status': "Mobile number duplicated ({})".format(recipient)}
        )
        message_recipient.save()

    message_sent.extra = result
    message_sent.save()

    return message_sent
