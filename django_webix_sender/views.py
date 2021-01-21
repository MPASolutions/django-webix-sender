# -*- coding: utf-8 -*-

import json
from decimal import Decimal

import telegram
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.db.models import Q, Sum, F, DecimalField, Case, When, IntegerField, Value, CharField, Subquery, OuterRef
from django.db.models.functions import StrIndex, Substr
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from telegram import Update
from telegram.ext import Dispatcher

from django_webix.views import WebixTemplateView, WebixListView
from django_webix_sender.models import MessageSent, MessageRecipient, MessageUserRead
from django_webix_sender.send_methods.telegram.persistences import DatabaseTelegramPersistence
from django_webix_sender.utils import send_mixin

if apps.is_installed('filter'):
    from filter.models import Filter
    from filter.utils import get_aggregates_q_by_id

CONF = getattr(settings, "WEBIX_SENDER", None)

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class SenderListView(WebixTemplateView):
    """
    Sender list page
    """

    template_name = 'django_webix_sender/list.js'
    http_method_names = ['get', 'head', 'options']

    def dispatch(self, request, *args, **kwargs):
        if "groups_can_send" in CONF and \
            not request.user.groups.intersection(Group.objects.filter(name__in=CONF['groups_can_send'])).exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SenderListView, self).get_context_data(**kwargs)
        use_dynamic_filters = apps.is_installed('filter')

        context['use_dynamic_filters'] = use_dynamic_filters

        context['send_methods'] = CONF['send_methods']
        context['send_method_types'] = [i['method'] for i in CONF['send_methods']]

        context['datatables'] = []
        for recipient in CONF['recipients']:
            app_label, model = recipient['model'].lower().split(".")
            model_class = apps.get_model(app_label=app_label, model_name=model)
            _dict = {
                'model': recipient['model'].lower(),
                'verbose_name': model_class._meta.verbose_name,
                'fields': [i for i in recipient['datatable_fields']],
                'collapsed': recipient.get('collapsed', False)
            }
            if use_dynamic_filters:
                _dict['filters'] = [{
                    'id': i.pk,
                    'value': i.label
                } for i in Filter.objects.filter(model__iexact=recipient['model'].lower())]
            context['datatables'].append(_dict)

        return context


@method_decorator(login_required, name='dispatch')
class SenderGetListView(View):
    http_method_names = ['get', 'head', 'options']

    def dispatch(self, request, *args, **kwargs):
        if "groups_can_send" in CONF and \
            not request.user.groups.intersection(Group.objects.filter(name__in=CONF['groups_can_send'])).exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

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
        filters_exists = False
        if use_dynamic_filters is True:
            filters_exists = Filter.objects.filter(model__iexact=contentype.lower()).exists()

        if contentype is None or (use_dynamic_filters and pks in [None, '', []] and filters_exists):
            return JsonResponse({'status': 'Invalid content type'}, status=400)

        app_label, model = contentype.lower().split(".")
        model_class = apps.get_model(app_label=app_label, model_name=model)
        queryset = model_class.objects.all()
        qset = Q()

        if use_dynamic_filters and filters_exists:
            filters = []
            for pk in pks:
                filter = get_object_or_404(Filter, pk=pk)
                if contentype.lower() != filter.model.lower():
                    return JsonResponse({'status': _('Content type doesn\'t match')}, status=400)
                filters.append(filter)

            and_or_filter = request.GET.get('and_or_filter', 'and')
            if and_or_filter not in ['and', 'or']:
                return JsonResponse({'message': _('Not valid and/or filter')})

            for filter in filters:
                aggregates, q = get_aggregates_q_by_id(model, filter.pk)
                if and_or_filter == 'and':
                    qset &= q
                elif and_or_filter == 'or':
                    qset |= q
                if aggregates:
                    queryset = queryset.annotate(*aggregates)

        queryset = queryset.filter(qset).distinct()
        queryset = queryset.select_related(*model_class.get_select_related())
        queryset = queryset.prefetch_related(*model_class.get_prefetch_related())
        queryset = queryset.filter(model_class.get_filters_viewers(request.user, request=request))

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
class SenderSendView(View):
    http_method_names = ['post', 'head', 'options']

    def dispatch(self, request, *args, **kwargs):
        if "groups_can_send" in CONF and \
            not request.user.groups.intersection(Group.objects.filter(name__in=CONF['groups_can_send'])).exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Funzione per inviare la corrispondenza.

        :param request: Django request
        :return: Json con lo stato dell'invio della corrispondenza
        """

        send_methods = request.POST.get("send_methods", None)
        typology = request.POST.get("typology", None)
        subject = request.POST.get("subject", "")
        body = request.POST.get("body", "")
        recipients = json.loads(request.POST.get("recipients", "{}"))
        presend = request.POST.get("presend", None)

        extra = None
        if 'session' in CONF.get('extra', {}):
            extra = {}
            for key in CONF.get('extra', {})['session']:
                extra[key] = request.session.get(key)

        results = []
        for send_method in send_methods.split(","):
            result, status = send_mixin(send_method, typology, subject, body, recipients, presend,
                                        user=request.user, files=request.FILES, extra=extra)
            results.append({
                "send_method": send_method,
                "result": result,
                "status": status
            })

        return JsonResponse(results, safe=False)


@method_decorator(login_required, name='dispatch')
class SenderWindowView(WebixTemplateView):
    template_name = 'django_webix_sender/sender.js'

    def dispatch(self, request, *args, **kwargs):
        if "groups_can_send" in CONF and \
            not request.user.groups.intersection(Group.objects.filter(name__in=CONF['groups_can_send'])).exists():
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SenderWindowView, self).get_context_data(**kwargs)

        context['send_methods'] = CONF['send_methods']
        context['typology_model'] = CONF['typology_model']
        context['send_method_types'] = [i['method'] for i in CONF['send_methods']]
        context['initial_send_methods'] = CONF.get('initial_send_methods', [])

        return context


@method_decorator(login_required, name='dispatch')
class SenderMessagesListView(WebixListView):
    model = MessageRecipient

    fields = [
        {
            'field_name': 'send_method_type',
            'datalist_column': '''{id: "send_method_type", header: ["Send method", {content: "textFilter"}], adjust: "all", fillspace: true}'''
        },
        {
            'field_name': 'message_sent__subject',
            'datalist_column': '''{id: "message_sent__subject", header: ["Subject", {content: "textFilter"}], adjust: "all", fillspace: true}'''
        },
        {
            'field_name': 'message_sent__body',
            'datalist_column': '''{id: "message_sent__body", header: ["Body", {content: "textFilter"}], adjust: "all", fillspace: true}'''
        },
    ]

    url_pattern_list = 'django_webix_sender.messages_list'
    add_permission = False
    change_permission = False
    delete_permission = False
    enable_column_delete = False
    enable_column_copy = False
    enable_row_click = False
    enable_json_loading = True

    def get_queryset(self, initial_queryset=None):
        qs = super().get_queryset(initial_queryset=initial_queryset)

        # Only sent messages
        qs = qs.filter(message_sent__status='sent')

        # Limit filter by user
        if self.request.user.is_anonymous:
            qs = qs.none()
        qset = Q()
        for recipient_config in CONF['recipients']:
            app_label, model = recipient_config['model'].lower().split(".")
            model_class = apps.get_model(app_label=app_label, model_name=model)
            recipient_queryset = model_class.objects.all()
            recipient_queryset = recipient_queryset.select_related(*model_class.get_select_related())
            recipient_queryset = recipient_queryset.prefetch_related(*model_class.get_prefetch_related())
            recipient_queryset = recipient_queryset.filter(
                model_class.get_filters_viewers(self.request.user, request=self.request)
            )
            qset |= Q(**{"{}_message_recipients__in".format(model): recipient_queryset})
        qs = qs.filter(qset)

        # Limit queryset to only list enabled in settings
        methods_show = ["{}.{}".format(i['method'], i['function']) for i in filter(
            lambda x: x['show_in_list'] is True,
            CONF['send_methods']
        )]
        qs = qs.filter(message_sent__send_method__in=methods_show)

        # Annotate send method types
        qs = qs.annotate(
            send_method_type=Substr(
                expression=F('message_sent__send_method'),
                pos=1,
                length=StrIndex(F('message_sent__send_method'), Value('.')) - 1,
                output_field=CharField()
            )
        )

        # Filter by send_method
        if self.request.GET.get('send_method') is not None:
            qs = qs.filter(send_method_type=self.request.GET.get('send_method'))

        return qs.distinct()


@method_decorator(login_required, name='dispatch')
class SenderMessagesChatView(WebixTemplateView):
    template_name = "django_webix_sender/chat.js"

    def get_template_names(self):
        template_name = None
        section = self.kwargs.get("section", "users")
        if section == "users":
            template_name = "django_webix_sender/chat.js"
        elif section == "messages":
            template_name = "django_webix_sender/chat_messages.js"
        return [template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        section = kwargs.get("section", "users")
        contenttype = self.request.GET.get("contenttype")
        send_method = self.request.GET.get("send_method")
        recipient_pk = self.request.GET.get("recipient")

        # Get enable chat methods
        methods_show = ["{}.{}".format(i['method'], i['function']) for i in filter(
            lambda x: x['show_in_chat'] is True,
            CONF['send_methods']
        )]

        if section == "users":
            recipients = []
            for recipient_config in CONF['recipients']:
                app_label, model = recipient_config['model'].lower().split(".")
                model_class = apps.get_model(app_label=app_label, model_name=model)
                recipient_queryset = model_class.objects.all()
                recipient_queryset = recipient_queryset.select_related(*model_class.get_select_related())
                recipient_queryset = recipient_queryset.prefetch_related(*model_class.get_prefetch_related())
                recipient_queryset = recipient_queryset.filter(
                    model_class.get_filters_viewers(self.request.user, request=self.request)
                ).annotate(
                    send_method=F("message_recipients__message_sent__send_method"),
                )
                recipient_queryset = recipient_queryset.filter(send_method__in=methods_show)
                recipient_queryset = recipient_queryset.annotate(
                    contenttype=Value(recipient_config['model'].lower(), output_field=CharField()),
                    last_message=Subquery(MessageRecipient.objects.filter(**{
                        "{}_message_recipients".format(model): OuterRef('pk'),
                        "message_sent__send_method": OuterRef('send_method')
                    }).order_by('-message_sent__creation_date').values('message_sent__creation_date')[:1]),
                ).filter(last_message__isnull=False).values(
                    'id',
                    'contenttype',
                    'last_message',
                    representation=model_class.get_representation(),
                    send_method=F("message_recipients__message_sent__send_method")
                ).order_by().distinct()
                recipients += list(recipient_queryset)
            context['recipients'] = sorted(recipients, key=lambda x: x['last_message'], reverse=True)
        elif section == "messages" and contenttype is not None and recipient_pk is not None and send_method is not None:
            app_label, model = contenttype.split(".")
            model_class = apps.get_model(app_label=app_label, model_name=model)
            recipient_queryset = model_class.objects.all()
            recipient_queryset = recipient_queryset.select_related(*model_class.get_select_related())
            recipient_queryset = recipient_queryset.prefetch_related(*model_class.get_prefetch_related())
            recipient_queryset = recipient_queryset.filter(
                model_class.get_filters_viewers(self.request.user, request=self.request)
            )
            recipient_queryset = recipient_queryset.filter(pk=recipient_pk)
            recipient_queryset = recipient_queryset.annotate(representation=model_class.get_representation())
            recipient = recipient_queryset.first()

            if recipient is not None:
                messages = (MessageSent.objects.filter(
                    status='sent',
                    pk__in=recipient.message_recipients.filter(
                        Q(message_sent__send_method=send_method) &
                        Q(message_sent__send_method__in=methods_show),
                        Q(**{"{}_message_recipients".format(model): recipient})
                    ).values('message_sent')
                ) | MessageSent.objects.filter(
                    status='received',
                    pk__in=recipient.message_recipients.filter(
                        Q(message_sent__send_method=send_method) &
                        Q(message_sent__send_method__in=methods_show),
                        Q(**{"{}_message_recipients".format(model): recipient}),
                        Q(is_sender=True)
                    ).values('message_sent'),
                ).order_by('creation_date')).order_by('creation_date')

                # Set messages as read
                for message in messages:
                    MessageUserRead.objects.get_or_create(
                        message_sent=message,
                        user=self.request.user,
                    )

                inverted = False
                if "groups_can_send" in CONF and \
                    self.request.user.groups.intersection(
                        Group.objects.filter(name__in=CONF['groups_can_send'])
                    ).exists():
                    inverted = True

                context['typology_model'] = CONF['typology_model']
                context['send_method'] = send_method
                context['send_method_type'] = send_method.split(".", 1)[0]
                context['recipient'] = recipient
                if CONF is not None and CONF['typology_model']['enabled']:
                    from django_webix_sender.models import MessageTypology
                    context['typology'], _ = MessageTypology.objects.get_or_create(typology='Response')
                context['contenttype'] = contenttype
                _messages = []
                for message in messages:
                    _message = {
                        'id': message.pk,
                        'sender': message.sender,
                        'body': message.body,
                        'status': message.status,
                        'creation_date': message.creation_date,
                        'user': message.user,
                    }
                    if not inverted:
                        _message['position'] = 'left' if message.status != 'received' else 'right'
                        _message['backgroundcolor'] = '#e3e3e5' if message.status != 'received' else '#1982fb'
                        _message['color'] = '#262626' if message.status != 'received' else "#fbfdff"
                    else:
                        _message['position'] = 'left' if message.status == 'received' else 'right'
                        _message['backgroundcolor'] = '#e3e3e5' if message.status == 'received' else '#1982fb'
                        _message['color'] = '#262626' if message.status == 'received' else "#fbfdff"
                    _messages.append(_message)
                context['messages'] = _messages

        else:
            raise Http404("Invalid request")

        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class SenderInvoiceManagementView(WebixTemplateView):
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
        context = super(SenderInvoiceManagementView, self).get_context_data(**kwargs)

        _send_methods = {}
        for i in CONF['send_methods']:
            _send_methods['{}.{}'.format(i['method'], i['function'])] = i['verbose_name']

        context['send_methods'] = [{'key': key, 'value': value} for key, value in _send_methods.items()]

        # Prelievo i filtri
        year = self.request.GET.get('year', timezone.now().year)
        send_method = self.request.GET.get('send_method', None)
        group = CONF.get('invoices_period', 'monthly')

        # Controllo che i filtri siano validi
        if not group in self.groups:
            return Http404

        # Prendo tutti i tipi di sender dei vari messaggi per i filtri impostati
        senders = MessageSent.objects.filter(
            creation_date__year=year,
            status='sent'
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
                send_method=send_method,
                status='sent'
            )
            if not sender:
                sender = _('Sender not specified')

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
                    messages_success=Sum(Case(
                        When(
                            messagerecipient__status='success',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=0,
                        output_field=IntegerField()
                    )),
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
                    messages_invoiced=Sum(Case(
                        When(
                            invoiced=True,
                            messagerecipient__status='success',
                            then=F('messagerecipient__sent_number')
                        ),
                        default=Decimal('0'),
                        output_field=IntegerField()
                    )),
                    messages_to_be_invoiced=Sum(Case(
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
        if sender == _('Sender not specified'):
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
            send_method=send_method,
            status='sent'
        )
        _filter = Q()
        for _month in _months:
            _filter |= Q(creation_date__month=_month)
        qs = qs.filter(_filter)

        # Update
        qs.update(invoiced=True)

        return JsonResponse({'status': _('Invoiced')})


@method_decorator(csrf_exempt, name='dispatch')
class SenderTelegramWebhookView(View):
    def post(self, request, *args, **kwargs):
        TELEGRAM = next(
            (item for item in settings.WEBIX_SENDER['send_methods'] if item["method"] == "telegram"), {}
        )
        CONFIG_TELEGRAM = TELEGRAM.get("config")

        response = json.loads(request.body)

        # Check user
        recipients = []
        for recipient in CONF['recipients']:
            app_label, model = recipient['model'].lower().split(".")
            model_class = apps.get_model(app_label=app_label, model_name=model)
            if model_class.get_telegram_fieldpath():
                recipients += list(model_class.objects.filter(
                    **{model_class.get_telegram_fieldpath(): response['message']['from']['id']}
                ))

        # Save only text messages (exclude commands)
        if "message" in response and "text" in response["message"] and not response["message"]["text"].startswith("/"):
            # Create db record
            for recipient in recipients:
                message_sent_data = {
                    "send_method": "{}.{}".format(TELEGRAM['method'], TELEGRAM['function']),
                    "subject": None,
                    "body": response['message']['text'],
                    "status": 'received',
                    "extra": response,
                    "sender": response['message']['from'].get('username'),
                }
                if CONF is not None and CONF['typology_model']['enabled']:
                    from django_webix_sender.models import MessageTypology
                    message_sent_data["typology"], _ = MessageTypology.objects.get_or_create(typology='Response')
                message_sent = MessageSent.objects.create(**message_sent_data)

                MessageRecipient.objects.create(
                    message_sent=message_sent,
                    recipient=recipient,
                    recipient_address='webhook',
                    sent_number=1,
                    status='success',
                    is_sender=True
                )

        # Create bot instance
        bot = telegram.Bot(token=CONFIG_TELEGRAM.get('bot_token'))
        dispatcher = Dispatcher(bot, None, workers=0, persistence=DatabaseTelegramPersistence())

        # Set handlers
        for handler in CONFIG_TELEGRAM.get('handlers', []):
            if isinstance(handler, dict):
                dispatcher.add_handler(**handler)
            elif isinstance(handler, tuple):
                dispatcher.add_handler(*handler)
            else:
                dispatcher.add_handler(handler)

        # Update dispatcher
        dispatcher.process_update(Update.de_json(json.loads(request.body), bot))

        return JsonResponse({"ok": "POST request processed"})
