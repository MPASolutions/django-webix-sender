# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import time

import requests
import six
from celery import shared_task
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from django_webix_sender.models import MessageRecipient, MessageSent


class SkebbyException(Exception):
    pass


class SkebbyGatewayOld(object):
    def __init__(self, username, password, text, sms_type='basic', sender_number='', sender_string='',
                 charset='ISO-8859-1', headers=None):
        self.url = "http://gateway.skebby.it/api/send/smseasy/advanced/http.php"
        self.sender_number = sender_number
        self.sender_string = sender_string
        self.headers = headers if headers is not None else {'User-Agent': 'Generic Client'}

        if sms_type == 'classic':
            method = 'send_sms_classic'
        elif sms_type == 'report':
            method = 'send_sms_classic_report'
        else:
            method = 'send_sms_basic'

        self.parameters = {
            'method': method,
            'username': username,
            'password': password,
            'text': text,
            'charset': 'UTF-8' if charset != 'ISO-8859-1' else 'ISO-8859-1'
        }

        # Sender number
        if sender_number != '':
            self.parameters['sender_number'] = sender_number
        if sender_string != '':
            self.parameters['sender_string'] = sender_string

    def send(self, recipients):
        if self.sender_number != '' and self.sender_string != '':
            return {
                'status': 'failed',
                'message': "Puoi specificare solo un tipo di mittente, numerico o alfanumerico"
            }

        self.parameters['recipients'] = recipients

        response = requests.post(self.url, data=self.parameters, headers=self.headers)

        if response.status_code != 200:
            result = {
                'status': 'failed',
                'code': '{}'.format(response.status_code),
                'message': response.text
            }
        else:
            results = response.text.split('&')
            result = {}
            for r in results:
                temp = r.split('=')
                result[temp[0]] = temp[1]
        return result


def send_sms_old(recipients, body, message_sent):
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

    _extra = {}

    gateway = SkebbyGatewayOld
    try:
        gateway = SkebbyGatewayOld(
            username=settings.CONFIG_SKEBBY['username'],
            password=settings.CONFIG_SKEBBY['password'],
            text=body,
            sms_type=settings.CONFIG_SKEBBY['method'],
            sender_number=settings.CONFIG_SKEBBY['sender_number'],
            sender_string=settings.CONFIG_SKEBBY['sender_string'],
            charset=settings.CONFIG_SKEBBY['charset'],
        )
    except SkebbyException as e:
        _extra['error'] = '{}'.format(e)

    # Per ogni istanza di destinatario ciclo
    for recipient, recipient_address in recipients['valids']:
        _result = ""
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=1
        )

        try:
            result = gateway.send(["+39{}".format(recipient_address)])

            if result['status'] == 'success':
                message_recipient.status = result['status']
                _result = "SMS {} ({}) inviato con successo, rimanenti: {}".format(
                    recipient_address,
                    recipient,
                    result['remaining_sms']
                )
            else:
                message_recipient.status = result['status']
                _result = "Invio fallito  {} ({}), Codice: {}, Motivo: {}".format(
                    recipient_address,
                    recipient,
                    result['code'],
                    result['message']
                )
        except Exception as e:
            message_recipient.status = 'failed'
            _result = '{}'.format(e)

        message_recipient.extra = {'status': _result}
        message_recipient.save()

    # Salvo i destinatari senza numero e quindi ai quali non è stato inviato il messaggio
    for recipient in recipients['invalids']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='invalid',
            extra={'status': "Cellulare non presente ({}) e quindi SMS non inviato".format(recipient)}
        )
        message_recipient.save()

    # Salvo i destinatari duplicati e quindi ai quali non è stato inviato il messaggio
    for recipient, recipient_address in recipients['duplicates']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='duplicate',
            recipient_address="+39{}".format(recipient_address),
            extra={'status': "Numero telefonico duplicato".format(recipient)}
        )
        message_recipient.save()

    message_sent.extra = _extra
    message_sent.save()

    return message_sent


class SkebbyGateway(object):
    def __init__(self, username, password):
        self.url = "https://api.skebby.it/API/v1.0/REST/"

        # Login
        response = requests.get("{}login?username={}&password={}".format(self.url, username, password))
        if response.status_code != 200:
            raise SkebbyException('Impossible to login in Skebby')
        self.user_key, self.session_key = response.text.split(';')

        # Header
        self.headers = {
            'user_key': self.user_key,
            'Session_key': self.session_key,
            'Content-type': 'application/json'
        }

    def send(self, recipients, message, message_type='basic', parametric=False, **kwargs):
        """Sends an SMS"""

        if message_type == 'classic':
            message_type = 'TI'
        elif message_type == 'report':
            message_type = 'GP'
        else:
            message_type = 'SI'

        parameters = {
            "message_type": message_type,
            "message": message,
            "recipient": recipients,
            "sender": kwargs.get('sender', ''),
            "scheduled_delivery_time": kwargs.get('scheduled_delivery_time'),
            "returnCredits": kwargs.get('returnCredits', False),  # False -> sms sent; True -> credit used
            "allowInvalidRecipients": kwargs.get('allowInvalidRecipients', False),
            "encoding": kwargs.get('encoding', 'gsm'),  # 'gsm' or 'ucs2'
        }

        if parametric:
            parameters['recipients'] = parameters.pop('recipient')

        if kwargs.get('order_id') is not None:
            parameters['order_id'] = kwargs.get('order_id')

        response = requests.post(
            "{}{}".format(
                self.url,
                'sms' if not parametric else 'paramsms'
            ),
            headers=self.headers,
            data=json.dumps(parameters, cls=DjangoJSONEncoder)
        )

        if response.status_code != 201:
            result = {
                'status': 'failed',
                'code': '{}'.format(response.status_code),
                'message': response.content
            }
        else:
            result = json.loads(response.text)
            result['status'] = 'success'
        return result

    @staticmethod
    @shared_task
    def check_state(order_id, times=1, interval=60 * 5):
        def _state(_gateway, _order_id):
            # ### Funzione per aggiornare lo stato dei log degli sms
            try:
                message_sent = MessageSent.objects.get(extra__order_id=_order_id)
            except MessageSent.DoesNotExist:
                return {'status': 'Invalid order id'}
            if message_sent.messagerecipient_set.filter(status='unknown').count() > 0:
                response = requests.get("{}sms/{}".format(_gateway.url, _order_id), headers=_gateway.headers)
                if response.status_code != 200:
                    return {'status': 'Error'}
                recipients = json.loads(response.text)['recipients']
                for recipient in recipients:
                    _recipients = message_sent.messagerecipient_set.filter(
                        recipient_address=recipient['destination'],
                        status='unknown'
                    )
                    for r in _recipients:
                        if recipient['status'] in ['SENT', 'DLVRD']:
                            r.status = 'success'
                        elif recipient['status'] in ['WAITING', 'WAIT4DLVR', 'SCHEDULED']:
                            r.status = 'unknown'
                        else:
                            r.status = 'failed'
                        r.extra = recipient
                        r.save()
                    message_sent.save()
                if message_sent.messagerecipient_set.filter(status='unknown').count() > 0:
                    return {'status': 'updated'}
            return {'status': 'all_updated'}

        try:
            gateway = SkebbyGateway(
                username=settings.CONFIG_SKEBBY['username'],
                password=settings.CONFIG_SKEBBY['password']
            )

            for i in range(1, times + 1):
                result = _state(gateway, order_id)
                if result['status'] == 'all_updated':
                    return {
                        'status': 'all_updated',
                        'iteration': i,
                        'times': times,
                        'interval': interval
                    }
                if i != times:
                    time.sleep(interval)

            return {
                'status': 'incomplete',
                'times': times,
                'interval': interval
            }
        except SkebbyException as e:
            return {'status': e}


def send_sms(recipients, body, message_sent):
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

    # Setto il numero totale di numeri validi e non validi
    _extra = {}

    result = {'status': 'failed'}  # Default failed, cambia poi se inviato con successo
    sent_per_recipient = 0
    try:
        gateway = SkebbyGateway(
            username=settings.CONFIG_SKEBBY['username'],
            password=settings.CONFIG_SKEBBY['password']
        )
        result = gateway.send(
            recipients=["+39{}".format(number) for _, number in recipients['valids']],
            message=body,
            message_type=settings.CONFIG_SKEBBY['method'],
            sender=settings.CONFIG_SKEBBY['sender_string']
        )
        _extra = result
    except SkebbyException as e:
        _extra['error'] = '{}'.format(e)

    # Setto il numero dell'ordine per recuperare successivamente lo stato dei vari messaggi
    if result['status'] == 'success':
        sent_per_recipient = result['total_sent'] / len(recipients['valids'])

    # Per ogni utente con numero creo un record
    for recipient, recipient_address in recipients['valids']:
        _result = ""
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=sent_per_recipient,
            status='unknown' if result['status'] == 'success' else 'failed',  # Sconosciuto se con successo
            recipient_address="+39{}".format(recipient_address)
        )
        message_recipient.save()

    # Salvo i destinatari senza numero e quindi ai quali non è stato inviato il messaggio
    for recipient in recipients['invalids']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='invalid',
            extra={'status': "Cellulare non presente ({}) e quindi SMS non inviato".format(recipient)}
        )
        message_recipient.save()

    # Salvo i destinatari duplicati e quindi ai quali non è stato inviato il messaggio
    for recipient, recipient_address in recipients['duplicates']:
        message_recipient = MessageRecipient(
            message_sent=message_sent,
            recipient=recipient,
            sent_number=0,
            status='duplicate',
            recipient_address="+39{}".format(recipient_address),
            extra={'status': "Numero telefonico duplicato".format(recipient)}
        )
        message_recipient.save()

    message_sent.extra = _extra
    message_sent.save()

    return message_sent
