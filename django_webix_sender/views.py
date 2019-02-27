# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
from decimal import Decimal

from django.apps import apps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum, F, DecimalField, Case, When, IntegerField
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView

from django_webix_sender.models import MessageSent, DjangoWebixSender
from django_webix_sender.send_methods.skebby import SkebbyGateway
from django_webix_sender.settings import CONF
from django_webix_sender.utils import my_import, ISO_8859_1_limited

if apps.is_installed('filter'):
    from filter.models import Filter
    from filter.utils2 import get_aggregates_q_by_id


@method_decorator(login_required, name='dispatch')
class SenderList(TemplateView):
    template_name = 'django_webix_sender/list.js'
    http_method_names = ['get', 'head', 'options']

    def get_context_data(self, **kwargs):
        context = super(SenderList, self).get_context_data(**kwargs)
        use_dynamic_filters = apps.is_installed('filter')

        context['use_dynamic_filters'] = use_dynamic_filters

        context['send_methods'] = CONF['send_methods']
        context['send_method_types'] = [i['method'] for i in CONF['send_methods']]

        context['datatables'] = []
        for recipient in CONF['recipients']:
            _dict = {
                'model': recipient['model'].lower(),
                'fields': [i for i in recipient['datatable_fields']]
            }
            if use_dynamic_filters:
                _dict['filters'] = [{
                    'id': i.pk,
                    'value': i.label
                } for i in Filter.objects.filter(model__iexact=recipient['model'].lower())]
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
        pks = request.GET.getlist('filter_pk', None)
        use_dynamic_filters = apps.is_installed('filter')

        if contentype is None or (use_dynamic_filters and pks in [None, '', []]):
            return JsonResponse({'status': 'Invalid content type'}, status=400)

        app_label, model = contentype.lower().split(".")
        model_class = apps.get_model(app_label=app_label, model_name=model)
        queryset = model_class.objects.all()
        qset = Q()

        if use_dynamic_filters:
            filters = []
            for pk in pks:
                filter = get_object_or_404(Filter, pk=pk)
                if contentype.lower() != filter.model.lower():
                    return JsonResponse({'status': 'Content type doesn\'t match'}, status=400)
                filters.append(filter)

            for filter in filters:
                aggregates, q = get_aggregates_q_by_id(model, filter.pk)
                qset &= q
                if aggregates:
                    queryset = queryset.annotate(*aggregates)

        queryset = queryset.filter(qset).distinct()
        queryset = queryset.select_related(*model_class.get_select_related())
        queryset = queryset.select_related(*model_class.get_prefetch_related())
        queryset = queryset.filter(model_class.get_filters(request))

        for recipient in CONF['recipients']:
            if recipient['model'].lower() == contentype.lower():
                recipients = []
                for record in queryset:
                    _json = {
                        'id': record.pk
                    }
                    for i in recipient['datatable_fields']:
                        _value = record
                        for field in i.split('__'):
                            if _value is None:
                                break
                            _value = getattr(_value, field)
                        try:
                            json.dumps(_value)
                            _json[i] = _value
                        except Exception:
                            _json[i] = str(_value)
                    recipients.append(_json)
                return JsonResponse(recipients, safe=False)

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
        presend = request.POST.get("presend", None)

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
                # Contatto non ancora presente nella lista
                if recipient.get_sms and not recipient.get_sms in _recipients['valids']['address']:
                    _recipients['valids']['address'].append(recipient.get_sms)
                    _recipients['valids']['recipients'].append(recipient)
                # Contatto già presente nella lista (duplicato)
                elif recipient.get_sms:
                    _recipients['duplicates']['address'].append(recipient.get_sms)
                    _recipients['duplicates']['recipients'].append(recipient)
                # Indirizzo non presente
                else:
                    _recipients['invalids'].append(recipient)
        elif method == "email":
            for recipient in _recipients_instance:
                # Contatto non ancora presente nella lista
                if recipient.get_email and not recipient.get_email in _recipients['valids']['address']:
                    _recipients['valids']['address'].append(recipient.get_email)
                    _recipients['valids']['recipients'].append(recipient)
                # Contatto già presente nella lista (duplicato)
                elif recipient.get_email:
                    _recipients['duplicates']['address'].append(recipient.get_email)
                    _recipients['duplicates']['recipients'].append(recipient)
                # Indirizzo non presente
                else:
                    _recipients['invalids'].append(recipient)

        _recipients['valids'] = list(zip(_recipients['valids']['recipients'], _recipients['valids']['address']))
        _recipients['duplicates'] = list(zip(_recipients['duplicates']['recipients'], _recipients['duplicates']['address']))

        # 4 Verifica prima dell'invio (opzionale)
        if presend is None:
            if method == "sms":
                # Verifico che il corpo dell'sms sia valido
                invalid_characters = ''
                for c in body:
                    if c not in ISO_8859_1_limited:
                        invalid_characters += c
                if invalid_characters != '':
                    return JsonResponse({
                        'status': _('Invalid characters'),
                        'data': invalid_characters
                    }, status=400)
            return JsonResponse({
                'valids': len(_recipients['valids']),
                'duplicates': len(_recipients['duplicates']),
                'invalids': len(_recipients['invalids'])
            })

        # 5. Creo istanza `MessageAttachment` senza collegarlo alla m2m -> da collegare al passo 5
        attachments = my_import(CONF['attachments']['save_function'])(
            request.FILES,
            send_method=send_method,
            typology=typology,
            subject=subject,
            body=body,
            recipients=_recipients
        )

        # 6. aggiungo il link del file in fondo al corpo
        if len(attachments) > 0:
            body += "\n\n"
            for attachment in attachments:
                body += "%s\n" % attachment.get_url()

        # 7. Creo il log e collego gli allegati
        # Costo del messaggio
        _cost = 0
        if hasattr(request.user, 'get_cost'):
            _cost = request.user.get_cost(send_method)

        # Mittente del messaggio
        _sender = None
        if hasattr(request.user, 'get_sender'):
            _sender = request.user.get_sender()

        message_sent = MessageSent(
            send_method=send_method,
            subject=subject,
            body=body,
            cost=_cost,
            user=request.user,
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
            return JsonResponse({
                'status': _('Sms sent'),
                'extra': result.extra
            })
        elif method == "email":
            # Invio i messaggi
            result = send_function(_recipients, subject, body, message_sent)
            return JsonResponse({
                'status': _('Emails sent'),
                'extra': result.extra
            })
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


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class InvoiceManagement(TemplateView):
    template_name = 'django_webix_sender/invoices.js'

    groups = {
        'monthly': [
            _('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _('Jun'), _('Jul'), _('Aug'), _('Sep'), _('Oct'),
            _('Nov'), _('Dec')
        ],
        'bimestrial': [
            _('Jan - Feb'), _('Mar - Apr'), _('May - Jun'), _('Jul - Aug'), _('Sep - Oct'), _('Nov - Dec')
        ],
        'quarter': [
            _('First quarter'), _('Second quarter'), _('Third quarter'), _('Fourth quarter')
        ],
        'half-yearly': [
            _('First semester'), _('Second semester')
        ],
        'yearly': [
            _('Year')
        ]
    }

    def get_context_data(self, **kwargs):
        context = super(InvoiceManagement, self).get_context_data(**kwargs)

        _send_methods = {}
        for i in CONF['send_methods']:
            _send_methods['{}.{}'.format(i['method'], i['function'])] = i['verbose_name']

        context['send_methods'] = [{'key': key, 'value': value} for key, value in _send_methods.items()]

        # Prelievo i filtri
        year = self.request.GET.get('year', timezone.now().year)
        send_method = self.request.GET.get('send_method', None)
        group = CONF.get('invoices_period', 'monthly')

        # Aggiorno tutti i messaggi
        for messagesent in MessageSent.objects.filter(
            send_method='sms.django_webix_sender.send_methods.skebby.send_sms',
            creation_date__year=year,
            extra__order_id__isnull=False
        ).annotate(
            unknown_sum=Sum(
                Case(When(messagerecipient__status='unknown', then=1), default=0, output_field=IntegerField())
            )
        ).filter(unknown_sum__gt=0):
            SkebbyGateway.check_state.delay(messagesent.extra['order_id'])

        # Controllo che i filtri siano validi
        if not group in self.groups:
            return Http404

        # Prendo tutti i tipi di sender dei vari messaggi per i filtri impostati
        senders = MessageSent.objects.filter(
            creation_date__year=year
        )
        if send_method:
            senders = senders.filter(send_method=send_method)
        senders = senders \
            .distinct('sender', 'send_method') \
            .values_list('sender', 'send_method')

        context['senders'] = []

        # Genero la lista dei mesi per periodo
        _periods = [
            [i * (12 // len(self.groups[group])) + j for j in range(1, (12 // len(self.groups[group])) + 1)]
            for i in range(0, len(self.groups[group]))
        ]

        # Per ogni sender creo un dizionario con i vari periodi e costi
        for idx, (sender, send_method) in enumerate(senders):
            qs = MessageSent.objects.filter(
                creation_date__year=year,
                sender=sender,
                send_method=send_method
            )
            if not sender:
                sender = _('Not specified')

            _sender = {
                'name': '{}'.format(sender),
                'send_method': '{}'.format(_send_methods[send_method] if send_method in _send_methods else send_method),
                'send_method_code': '{}'.format(send_method),
                'periods': [],
                'x': idx % 2,
                'y': idx // 2
            }

            # Per ogni periodo estrapolo i dati
            for index, period in enumerate(_periods):
                _filter = Q()
                for _month in period:
                    _filter |= Q(creation_date__month=_month)
                totals = qs.filter(_filter).aggregate(
                    messages_unknown=Sum(Case(
                        When(
                            messagerecipient__status='unknown',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=0,
                        output_field=IntegerField()
                    )),
                    messages_fail=Sum(Case(
                        When(
                            messagerecipient__status='failed',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=0,
                        output_field=IntegerField()
                    )),
                    messages_success=Sum(Case(
                        When(
                            messagerecipient__status='success',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=0,
                        output_field=IntegerField()
                    )),
                    invoiced=Sum(Case(
                        When(
                            invoiced=True,
                            messagerecipient__status='success',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=Decimal('0'),
                        output_field=IntegerField()
                    )),
                    to_be_invoiced=Sum(Case(
                        When(
                            invoiced=False,
                            messagerecipient__status='success',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=Decimal('0'),
                        output_field=IntegerField()
                    )),
                    price_invoiced=Sum(Case(
                        When(
                            invoiced=True,
                            messagerecipient__status='success',
                            then=F('cost') * F('messagerecipient__sent_number')
                        ),
                        default=Decimal('0'),
                        output_field=DecimalField()
                    )),
                    price_to_be_invoiced=Sum(Case(
                        When(
                            invoiced=False,
                            messagerecipient__status='success',
                            then=F('cost') * F('messagerecipient__sent_number')
                        ),
                        default=Decimal('0'),
                        output_field=DecimalField()
                    ))
                )
                totals['period'] = self.groups[group][index]
                _sender['periods'].append(totals)
            context['senders'].append(_sender)

        return context

    def post(self, request, *args, **kwargs):
        group = CONF.get('invoices_period', 'monthly')
        year = self.request.POST.get('year', timezone.now().year)
        period = request.POST.get('period', None)
        sender = request.POST.get('sender', None)
        send_method = request.POST.get('send_method', None)
        if period is None or period not in self.groups[group]:
            return JsonResponse({'status': _('Invalid period')}, status=400)
        if send_method is None:
            return JsonResponse({'status': _('Invalid send method')}, status=400)
        if sender == _('Not specified'):
            sender = None

        # Genero la lista dei mesi per periodo
        _periods = [
            [i * (12 // len(self.groups[group])) + j for j in range(1, (12 // len(self.groups[group])) + 1)]
            for i in range(0, len(self.groups[group]))
        ]
        _months = _periods[self.groups[group].index(period)]

        # Prelevo i messaggi da fatturare
        qs = MessageSent.objects.filter(
            creation_date__year=year,
            sender=sender,
            send_method=send_method
        )
        _filter = Q()
        for _month in _months:
            _filter |= Q(creation_date__month=_month)
        qs = qs.filter(_filter)

        # Update
        qs.update(invoiced=True)

        return JsonResponse({'status': _('Invoiced')})
