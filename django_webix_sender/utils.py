# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import importlib
from typing import List, Dict, Any, Optional, Tuple

from django.apps import apps
from django.utils.translation import ugettext_lazy as _

from django_webix_sender.models import MessageSent, DjangoWebixSender
from django_webix_sender.settings import CONF

ISO_8859_1_limited = '@èéùìò_ !"#%\\\'()*+,-./0123456789:<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜabcdefghijklmnopqrstuvwxyzäöñüà'


def my_import(name):
    module, function = name.rsplit('.', 1)
    component = importlib.import_module(module)
    return getattr(component, function)


def send_email(recipients, subject, body, message_sent):
    raise NotImplementedError(_('`send_email` method not implemented!'))


def send_sms(recipients, body, message_sent):
    raise NotImplementedError(_('`send_sms` method not implemented!'))


def send_mixin(send_method: str, typology: Optional[int], subject: str, body: str, recipients: Dict[str, List[int]],
               presend: Optional[Any], **kwargs) -> Tuple[Dict[str, Any], int]:
    """
    Function to send the message

    :param send_method: <sms|email>.<function> (eg. "sms.django_webix_sender.utils.send_sms")
    :param typology: MessageTypology ID
    :param subject: Subject of email
    :param body: Body of message (email or sms)
    :param recipients: Dict {'<app_label>.<model>': [<id>, <id>]}
    :param presend: None: verify before the send; Otherwise: send the message
    :param kwargs: `user` and `files` (default: user=None, files={})
    :return: Tuple[Dict, Code]
    """

    user = kwargs.get('user')
    files = kwargs.get('files', {})

    # 1.a Recupero la lista delle istanze a cui inviare il messaggio (modello, lista destinatari)
    _recipients_instance = []
    for key, value in recipients.items():
        app_label, model = key.lower().split(".")
        model_class = apps.get_model(app_label=app_label, model_name=model)
        if not issubclass(model_class, DjangoWebixSender):
            raise Exception('{}.{} is not subclass of `DjangoWebixSender`'.format(app_label, model))
        _recipients_instance += list(model_class.objects.filter(pk__in=value))
    _recipients_instance = list(set(_recipients_instance))

    # 1.b Recupero i contatti collegati ai destinatari principali
    for _recipient in _recipients_instance:
        if hasattr(_recipient, 'get_sms_related'):
            for related in _recipient.get_sms_related:
                if not issubclass(related.__class__, DjangoWebixSender):
                    raise Exception(_('Related is not subclass of `DjangoWebixSender`'))
                _recipients_instance.append(related)
    _recipients_instance = list(set(_recipients_instance))

    # 2. Recupero la funzione per inviare
    method, function = send_method.split(".", 1)
    send_function = my_import(function)

    # 3. Creo dizionario dei destinatari
    _recipients = {
        'valids': {
            'recipients': [],
            'address': []
        },
        'duplicates': {
            'recipients': [],
            'address': []
        },
        'invalids': []
    }
    if method == "sms":
        for recipient in _recipients_instance:
            # Prelevo il numero di telefono e lo metto in una lista se non è già una lista
            _get_sms = recipient.get_sms
            if not isinstance(_get_sms, list):
                _get_sms = [_get_sms]

            # Per ogni numero verifico il suo stato e lo aggiungo alla chiave corretta
            for _sms in _get_sms:
                # Contatto non ancora presente nella lista
                if _sms and not _sms in _recipients['valids']['address']:
                    _recipients['valids']['address'].append(_sms)
                    _recipients['valids']['recipients'].append(recipient)
                # Contatto già presente nella lista (duplicato)
                elif _sms:
                    _recipients['duplicates']['address'].append(_sms)
                    _recipients['duplicates']['recipients'].append(recipient)
                # Indirizzo non presente
                else:
                    _recipients['invalids'].append(recipient)
    elif method == "email":
        for recipient in _recipients_instance:
            # Prelevo l'indirizzo email e lo metto in una lista se non è già una lista
            _get_email = recipient.get_email
            if not isinstance(_get_email, list):
                _get_email = [_get_email]

            # Per ogni email verifico il suo stato e lo aggiungo alla chiave corretta
            for _email in _get_email:
                # Contatto non ancora presente nella lista
                if _email and not _email in _recipients['valids']['address']:
                    _recipients['valids']['address'].append(_email)
                    _recipients['valids']['recipients'].append(recipient)
                # Contatto già presente nella lista (duplicato)
                elif _email:
                    _recipients['duplicates']['address'].append(_email)
                    _recipients['duplicates']['recipients'].append(recipient)
                # Indirizzo non presente
                else:
                    _recipients['invalids'].append(recipient)

    _recipients['valids'] = list(zip(_recipients['valids']['recipients'], _recipients['valids']['address']))
    _recipients['duplicates'] = list(
        zip(_recipients['duplicates']['recipients'], _recipients['duplicates']['address'])
    )

    # 4 Verifica prima dell'invio (opzionale)
    if presend is None:
        if method == "sms":
            # Verifico che il corpo dell'sms sia valido
            invalid_characters = ''
            for c in body:
                if c not in ISO_8859_1_limited:
                    invalid_characters += c
            if invalid_characters != '':
                return {'status': _('Invalid characters'), 'data': invalid_characters}, 400
        return {
                   'valids': len(_recipients['valids']),
                   'duplicates': len(_recipients['duplicates']),
                   'invalids': len(_recipients['invalids'])
               }, 200

    # 5. Creo istanza `MessageAttachment` senza collegarlo alla m2m -> da collegare al passo 5
    attachments = my_import(CONF['attachments']['save_function'])(
        files,
        send_method=send_method,
        typology=typology,
        subject=subject,
        body=body,
        recipients=_recipients
    )

    # 6. aggiungo il link del file in fondo al corpo
    if len(attachments) > 0 and method == "sms":
        body += "\n\n"
        for attachment in attachments:
            body += "{attachment}\n".format(attachment=attachment.get_url())
    elif len(attachments) > 0 and method == "email":
        body += "</br></br>"
        for attachment in attachments:
            body += "<a href='{attachment}'>{attachment}</a></br>".format(attachment=attachment.get_url())

    # 7. Creo il log e collego gli allegati
    # Costo del messaggio
    _cost = 0
    if hasattr(user, 'get_cost'):
        _cost = user.get_cost(send_method)

    # Mittente del messaggio
    _sender = None
    if hasattr(user, 'get_sender'):
        _sender = user.get_sender()

    message_sent = MessageSent(
        send_method=send_method,
        subject=subject,
        body=body,
        cost=_cost,
        user=user,
        sender=_sender
    )
    _extra = {}
    if CONF['typology_model']['enabled']:
        message_sent.typology_id = typology
    message_sent.save()
    message_sent.attachments.add(*attachments)

    # 8. Send messages
    if method == "sms":
        # Invio i messaggi
        result = send_function(_recipients, body, message_sent)
        return {'status': _('Sms sent'), 'extra': result.extra}, 200
    elif method == "email":
        # Invio i messaggi
        result = send_function(_recipients, subject, body, message_sent)
        return {'status': _('Emails sent'), 'extra': result.extra}, 200
    else:
        return {'status': _('Invalid send method')}, 400
