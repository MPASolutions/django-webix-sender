# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView

from django_webix_sender.models import MessageSent, MessageRecipient, DjangoWebixSender
from django_webix_sender.settings import CONF
from django_webix_sender.utils import my_import, ISO_8859_1_limited

if apps.is_installed('filter'):
    from filter.models import Filter
    from filter.utils2 import get_aggregates_q_by_id


@method_decorator(login_required, name='dispatch')
class SenderList(TemplateView):
    template_name = 'django_webix_sender/list.js'
    http_method_names = ['get', 'head', 'options']

    def __init__(self):
        super(SenderList, self).__init__()
        self.use_dynamic_filters = apps.is_installed('filter')

    def get_context_data(self, **kwargs):
        context = super(SenderList, self).get_context_data(**kwargs)

        context['use_dynamic_filters'] = self.use_dynamic_filters

        context['send_methods'] = CONF['send_methods']
        context['send_method_types'] = [i['method'] for i in CONF['send_methods']]

        context['datatables'] = []
        for recipient in CONF['recipients']:
            _dict = {
                'model': recipient['model'].lower(),
                'fields': [i for i in recipient['datatable_fields']]
            }
            if self.use_dynamic_filters:
                _dict['filters'] = [{
                    'id': i.pk,
                    'value': i.label
                } for i in Filter.objects.filter(model=recipient['model'].lower())]
            context['datatables'].append(_dict)

        return context


@method_decorator(login_required, name='dispatch')
class SenderGetList(View):
    http_method_names = ['get', 'head', 'options']

    def get(self, request, *args, **kwargs):
        """
        Funzione che ritorna un JSON con i record del ContentType passato come parametro.

        Se nella richiesta viene passata una lista di ID e nel file `settings.py` è abilitato l'utilizzo dei filtri
        dinamici, allora il QuerySet viene filtrato, altrimenti ritorna tutti i valori presenti nel database.

        :param request: Django request
        :return: Json contentente le istanze richieste e filtrate in caso di `filters` in `INSTALLED_APPS`
        """

        contentype = request.GET.get('contentype', None)
        pks = request.GET.getlist('filters_pk', None)
        use_dynamic_filters = apps.is_installed('filter')

        if contentype is None or (use_dynamic_filters and pks in [None, '', []]):
            return JsonResponse({}, status=400)

        app_label, model = contentype.lower().split(".")
        model_class = apps.get_model(app_label=app_label, model_name=model)
        queryset = model_class.objects.all()
        qset = Q()

        if use_dynamic_filters:
            filters = []
            for pk in pks:
                filter = get_object_or_404(Filter, pk=pk)
                if contentype != filter.model:
                    return JsonResponse({}, status=400)
                filters.append(filter)

            for filter in filters:
                aggregates, q = get_aggregates_q_by_id(model, filter.pk)
                qset &= q
                if aggregates:
                    queryset = queryset.annotate(*aggregates)

        queryset = queryset.filter(qset).distinct()

        for destinatario in CONF['recipients']:
            if destinatario['model'].lower() == contentype.lower():
                destinatari = []
                for record in queryset:
                    _json = {
                        'id': record.pk
                    }
                    for i in destinatario['datatable_fields']:
                        try:
                            json.dumps(getattr(record, i))
                            _json[i] = getattr(record, i)
                        except:
                            _json[i] = str(getattr(record, i))
                    destinatari.append(_json)
                return JsonResponse(destinatari, safe=False)

        return JsonResponse({})


@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class SenderSend(View):
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        """
        Funzione per inviare la corrispondenza.

        :param request: Django request
        :return: Json con lo stato dell'invio della corrispondenza
        """

        send_method = request.POST.get("send_method", None)
        typology = request.POST.get("typology", None)
        subject = request.POST.get("subject", "")
        body = request.POST.get("body", "")
        recipients = json.loads(request.POST.get("recipients", "{}"))

        # 1. Recupero la lista delle istanze a cui inviare il messaggio
        _recipients_instance = []
        for key, value in recipients.items():
            app_label, model = key.lower().split(".")
            model_class = apps.get_model(app_label=app_label, model_name=model)
            if not issubclass(model_class, DjangoWebixSender):
                raise Exception('{}.{} is not subclass of `DjangoWebixSender`'.format(app_label, model))
            _recipients_instance += list(model_class.objects.filter(pk__in=value))
        _recipients_instance = list(set(_recipients_instance))

        # 2. Recupero la funzione per inviare
        method, function = send_method.split(".", 1)
        send_function = my_import(function)

        # 3. Creo istanza `MessageAttachment` senza collegarlo alla m2m -> da collegare al passo 3
        attachments = my_import(CONF['attachments']['save_function'])(request.FILES)

        # 4. aggiungo il link del file in fondo al corpo
        if len(attachments) > 0:
            body += "\n\n"
            for attachment in attachments:
                body += "%s\n" % attachment.get_url()

        # 5. Creo il log e collego gli allegati
        message_sent = MessageSent(
            send_method=send_method,
            subject=subject,
            body=body
        )
        _extra = {}
        if CONF['typology_model']['enabled']:
            message_sent.typology_id = typology
        message_sent.save()
        message_sent.attachments.add(*attachments)

        # 6. Send messages
        if method == "sms":
            # Verifico che l'sms sia valido
            invalid_characters = ''
            for c in body:
                if c not in ISO_8859_1_limited:
                    invalid_characters += c
            if invalid_characters != '':
                return JsonResponse({
                    'status': _('Invalid characters'),
                    'data': invalid_characters
                }, status=404)

            # Tengo nota dei contatti collegati ai quali ho inviato il messaggio per non inviarlo nuovamente
            _related = []

            # Invio i messaggi
            for recipient in _recipients_instance:
                # Invio al contatto principale
                result = send_function(recipient.get_sms, body, recipient)
                MessageRecipient.objects.create(
                    message_sent=message_sent,
                    recipient=recipient
                )
                if result:
                    _extra["{}|{}.{}".format(recipient.pk, recipient.__class__.__module__,
                                             recipient.__class__.__name__)] = result
                # Invio anche ai contatti collegati tenendo conto dei contatti a cui l'ho già inviato
                if hasattr(recipient, 'get_sms_related'):
                    for related in [i for i in recipient.get_sms_related if i not in _related]:
                        if not issubclass(related.__class__, DjangoWebixSender):
                            raise Exception(_('Related is not subclass of `DjangoWebixSender`'))
                        if related not in _related:
                            result = send_function(related.get_sms, body, related)
                            MessageRecipient.objects.create(
                                message_sent=message_sent,
                                recipient=related
                            )
                            if result:
                                _extra["{}|{}.{}".format(related.pk, related.__class__.__module__,
                                                         related.__class__.__name__)] = result
                            _related.append(related)
            message_sent.extra = _extra
            message_sent.save()
            return JsonResponse({'status': _('Sms sent'), 'extra': message_sent.extra})
        elif method == "email":
            # Tengo nota dei contatti collegati ai quali ho inviato il messaggio per non inviarlo nuovamente
            _related = []

            for recipient in _recipients_instance:
                # Invio al contatto principale
                result = send_function(recipient.get_email, subject, body, settings.DEFAULT_FROM_EMAIL, recipient)
                MessageRecipient.objects.create(
                    message_sent=message_sent,
                    recipient=recipient
                )
                if result:
                    _extra["{}|{}.{}".format(recipient.pk, recipient.__class__.__module__,
                                             recipient.__class__.__name__)] = result
                # Invio anche ai contatti collegati tenendo conto dei contatti a cui l'ho già inviato
                if hasattr(recipient, 'get_email_related'):
                    for related in [i for i in recipient.get_email_related if i not in _related]:
                        if not issubclass(related.__class__, DjangoWebixSender):
                            raise Exception(_('Related is not subclass of `DjangoWebixSender`'))
                        if related not in _related:
                            result = send_function(related.get_email, subject, body, settings.DEFAULT_FROM_EMAIL,
                                                   related)
                            MessageRecipient.objects.create(
                                message_sent=message_sent,
                                recipient=related
                            )
                            if result:
                                _extra["{}|{}.{}".format(related.pk, related.__class__.__module__,
                                                         related.__class__.__name__)] = result
                            _related.append(related)
            message_sent.extra = _extra
            message_sent.save()
            return JsonResponse({'status': _('Emails sent'), 'extra': message_sent.extra})
        else:
            return JsonResponse({'status': _('Invalid send method')}, status=400)


@method_decorator(login_required, name='dispatch')
class DjangoWebixSenderWindow(TemplateView):
    template_name = 'django_webix_sender/sender.js'

    def get_context_data(self, **kwargs):
        context = super(DjangoWebixSenderWindow, self).get_context_data(**kwargs)

        context['send_methods'] = CONF['send_methods']
        context['typology_model'] = CONF['typology_model']

        return context
