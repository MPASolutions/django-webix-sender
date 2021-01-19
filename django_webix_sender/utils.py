# -*- coding: utf-8 -*-

import importlib
from typing import List, Dict, Any, Optional, Tuple

import phonenumbers
from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from django_webix_sender.models import MessageSent, DjangoWebixSender

CONF = getattr(settings, "WEBIX_SENDER", None)

ISO_8859_1_limited = '@èéùìò_ !"#%\\\'()*+,-./0123456789:<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜabcdefghijklmnopqrstuvwxyzäöñüà'


def my_import(name: str) -> callable:
    """
    Load a function from a string

    :param name: function path name (e.g. django_webix_sender.send_methods.email.send_utils)
    :return: callable
    """

    module, function = name.rsplit('.', 1)
    component = importlib.import_module(module)
    return getattr(component, function)


def send_mixin(send_method: str, typology: Optional[int], subject: str, body: str, recipients: Dict[str, List[int]],
               presend: Optional[Any], **kwargs) -> Tuple[Dict[str, Any], int]:
    """
    Function to send the message

    :param send_method: <skebby|email|telegram|storage>.<function> (eg. "skebby.django_webix_sender.send_methods.email.send_utils")
    :param typology: MessageTypology ID
    :param subject: Subject of message
    :param body: Body of message (email, skebby, telegram or storage)
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
        if hasattr(_recipient, 'get_email_related'):
            for related in _recipient.get_email_related:
                if not issubclass(related.__class__, DjangoWebixSender):
                    raise Exception(_('Related is not subclass of `DjangoWebixSender`'))
                _recipients_instance.append(related)
        if hasattr(_recipient, 'get_telegram_related'):
            for related in _recipient.get_telegram_related:
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
        'invalids': {
            'recipients': [],
            'address': []
        }
    }
    if method == "skebby":
        CONFIG_SKEBBY = next(
            (item for item in settings.WEBIX_SENDER['send_methods'] if item["method"] == "skebby"), {}
        ).get("config")

        for recipient in _recipients_instance:
            # Prelevo il numero di telefono e lo metto in una lista se non è già una lista
            _get_sms = recipient.get_sms
            if not isinstance(_get_sms, list):
                _get_sms = [_get_sms]

            # Per ogni numero verifico il suo stato e lo aggiungo alla chiave corretta
            for _sms in _get_sms:
                # Verifico che il numero sia valido
                try:
                    number = phonenumbers.parse(_sms, CONFIG_SKEBBY['region'])
                    _sms = phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
                    # Contatto non ancora presente nella lista
                    if phonenumbers.is_valid_number(number) and _sms not in _recipients['valids']['address']:
                        _recipients['valids']['address'].append(_sms)
                        _recipients['valids']['recipients'].append(recipient)
                    # Contatto già presente nella lista (duplicato)
                    elif phonenumbers.is_valid_number(number):
                        _recipients['duplicates']['address'].append(_sms)
                        _recipients['duplicates']['recipients'].append(recipient)
                    # Indirizzo non presente o non valido
                    else:
                        raise Exception("Invalid number")
                except Exception:
                    _recipients['invalids']['address'].append(_sms)
                    _recipients['invalids']['recipients'].append(recipient)
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
                    _recipients['invalids']['address'].append(_email)
                    _recipients['invalids']['recipients'].append(recipient)
    elif method == "telegram":
        for recipient in _recipients_instance:
            # Prelevo l'ID telegram e lo metto in una lista se non è già una lista
            _get_telegram = recipient.get_telegram
            if not isinstance(_get_telegram, list):
                _get_telegram = [_get_telegram]

            # Per ogni email verifico il suo stato e lo aggiungo alla chiave corretta
            for _telegram in _get_telegram:
                # Contatto non ancora presente nella lista
                if _telegram and not _telegram in _recipients['valids']['address']:
                    _recipients['valids']['address'].append(_telegram)
                    _recipients['valids']['recipients'].append(recipient)
                # Contatto già presente nella lista (duplicato)
                elif _telegram:
                    _recipients['duplicates']['address'].append(_telegram)
                    _recipients['duplicates']['recipients'].append(recipient)
                # Indirizzo non presente
                else:
                    _recipients['invalids']['address'].append(_telegram)
                    _recipients['invalids']['recipients'].append(recipient)
    elif method == "storage":
        for recipient in _recipients_instance:
            # Prelevo l'ID user e lo metto in una lista se non è già una lista
            if not recipient.pk in _recipients['valids']['address']:
                _recipients['valids']['address'].append(recipient.pk)
                _recipients['valids']['recipients'].append(recipient)
            # Contatto già presente nella lista (duplicato)
            elif recipient.pk in _recipients['valids']['address']:
                _recipients['duplicates']['address'].append(recipient.pk)
                _recipients['duplicates']['recipients'].append(recipient)
            # Indirizzo non presente
            else:
                _recipients['invalids']['address'].append(recipient.pk)
                _recipients['invalids']['recipients'].append(recipient)

    # Convert dict in list of tuples
    _recipients['valids'] = list(zip(_recipients['valids']['recipients'], _recipients['valids']['address']))
    _recipients['duplicates'] = list(
        zip(_recipients['duplicates']['recipients'], _recipients['duplicates']['address'])
    )
    _recipients['invalids'] = list(zip(_recipients['invalids']['recipients'], _recipients['invalids']['address']))

    # 4 Verifica prima dell'invio (opzionale)
    if presend is None:
        if method == "skebby":
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
    if len(attachments) > 0 and method == "skebby":
        body += "\n\n"
        for attachment in attachments:
            body += "{attachment}\n".format(attachment=attachment.get_url())
    elif len(attachments) > 0 and method == "email":
        body += "</br></br>"
        for attachment in attachments:
            body += "<a href='{attachment}'>{attachment}</a></br>".format(attachment=attachment.get_url())
    elif len(attachments) > 0 and method == "telegram":
        pass  # TODO: create attachments function
    elif len(attachments) > 0 and method == "storage":
        pass  # ignore this step, file already in db

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
    if CONF['typology_model']['enabled']:
        message_sent.typology_id = typology
    message_sent.save()
    message_sent.attachments.add(*attachments)

    # 8. Send messages
    if method == "skebby":
        result = send_function(_recipients, body, message_sent)
        status = _('Skebby sent')
    elif method == "email":
        result = send_function(_recipients, subject, body, message_sent)
        status = _('Emails sent')
    elif method == "telegram":
        result = send_function(_recipients, body, message_sent)
        status = _('Telegram sent')
    elif method == "storage":
        result = send_function(_recipients, subject, body, message_sent)
        status = _('Storage sent')
    else:
        return {'status': _('Invalid send method')}, 400

    # Add optional extra params
    if kwargs.get('extra') is not None and isinstance(kwargs.get('extra'), dict):
        if result.extra is None:
            result.extra = {}
        result.extra.update(kwargs.get('extra'))
        result.save()

    return {'status': status, 'extra': result.extra}, 200
