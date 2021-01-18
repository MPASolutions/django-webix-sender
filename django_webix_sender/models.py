# -*- coding: utf-8 -*-

from decimal import Decimal
from typing import List, Any

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

CONF = getattr(settings, "WEBIX_SENDER", None)

try:
    from mpadjango.db.models import MpaModel as Model
except ImportError:
    from django.db.models import Model


def save_attachments(files, *args, **kwargs):
    attachments = []
    for filename, file in files.items():
        attachment = MessageAttachment.objects.create(file=file)
        attachments.append(attachment)
    return attachments


class DjangoWebixSender(Model):
    class Meta:
        abstract = True

    @property
    def get_sms(self):
        raise NotImplementedError(_("`get_sms` not implemented!"))

    @property
    def get_email(self) -> str:
        raise NotImplementedError(_("`get_email` not implemented!"))

    @property
    def get_telegram(self) -> str:
        raise NotImplementedError(_("`get_telegram` not implemented!"))

    @staticmethod
    def get_sms_fieldpath() -> str:
        return NotImplementedError(_("`get_sms_fieldpath` not implemented!"))

    @staticmethod
    def get_email_fieldpath() -> str:
        return NotImplementedError(_("`get_email_fieldpath` not implemented!"))

    @staticmethod
    def get_telegram_fieldpath() -> str:
        return NotImplementedError(_("`get_telegram_fieldpath` not implemented!"))

    @property
    def get_sms_related(self) -> List[Any]:
        return []

    @property
    def get_email_related(self) -> List[Any]:
        return []

    @property
    def get_telegram_related(self) -> List[Any]:
        return []

    @classmethod
    def get_select_related(cls) -> List[str]:
        return []

    @classmethod
    def get_prefetch_related(cls) -> List[str]:
        return []

    @classmethod
    def get_filters(cls, request) -> Q:
        return Q()


if CONF is not None and \
    any(_recipients['model'] == 'django_webix_sender.Customer' for _recipients in CONF.get('recipients', [])):
    class Customer(DjangoWebixSender):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                                 verbose_name=_('User'))
        name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Name'))
        vat_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Vat number'))
        fiscal_code = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Fiscal code'))
        sms = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Sms'))
        email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email'))
        telegram = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Telegram'))
        note = models.TextField(blank=True, null=True, verbose_name=_('Note'))
        extra = JSONField(blank=True, null=True, verbose_name=_('Extra'))
        typology = models.ForeignKey('django_webix_sender.CustomerTypology', blank=True, null=True,
                                     on_delete=models.CASCADE, verbose_name=_('Typology'))

        creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
        modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

        class Meta:
            verbose_name = _('Customer')
            verbose_name_plural = _('Customers')

        def __str__(self):
            return '{}'.format(self.name)

        @property
        def get_sms(self) -> str:
            return self.sms

        @property
        def get_email(self) -> str:
            return self.email

        @property
        def get_telegram(self) -> str:
            return self.telegram

        @staticmethod
        def get_sms_fieldpath() -> str:
            return "sms"

        @staticmethod
        def get_email_fieldpath() -> str:
            return "email"

        @staticmethod
        def get_telegram_fieldpath() -> str:
            return "telegram"


    class CustomerTypology(Model):
        typology = models.CharField(max_length=255, unique=True, verbose_name=_('Typology'))

        creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
        modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

        class Meta:
            verbose_name = _('Customer typology')
            verbose_name_plural = _('Customer typologies')

        def __str__(self):
            return '{}'.format(self.typology)

if CONF is not None and \
    any(_recipients['model'] == 'django_webix_sender.ExternalSubject' for _recipients in CONF.get('recipients', [])):
    class ExternalSubject(DjangoWebixSender):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                                 verbose_name=_('User'))
        name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Name'))
        vat_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Vat number'))
        fiscal_code = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Fiscal code'))
        sms = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Sms'))
        email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email'))
        telegram = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Telegram'))
        note = models.TextField(blank=True, null=True, verbose_name=_('Note'))
        extra = JSONField(blank=True, null=True, verbose_name=_('Extra'))
        typology = models.ForeignKey('django_webix_sender.ExternalSubjectTypology', blank=True, null=True,
                                     on_delete=models.CASCADE, verbose_name=_('Typology'))

        creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
        modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

        class Meta:
            verbose_name = _('External subject')
            verbose_name_plural = _('External subjects')

        def __str__(self):
            if self.name:
                return self.name
            else:
                return _('Not defined')

        @property
        def get_sms(self) -> str:
            return self.sms

        @property
        def get_email(self) -> str:
            return self.email

        @property
        def get_telegram(self) -> str:
            return self.telegram

        @staticmethod
        def get_sms_fieldpath() -> str:
            return "sms"

        @staticmethod
        def get_email_fieldpath() -> str:
            return "email"

        @staticmethod
        def get_telegram_fieldpath() -> str:
            return "telegram"


    class ExternalSubjectTypology(Model):
        typology = models.CharField(max_length=255, unique=True, verbose_name=_('Typology'))

        creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
        modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

        class Meta:
            verbose_name = _('External subject typology')
            verbose_name_plural = _('External subject typologies')

        def __str__(self):
            return '{}'.format(self.typology)

if CONF is not None and CONF['attachments']['model'] == 'django_webix_sender.MessageAttachment':
    class MessageAttachment(Model):
        file = models.FileField(upload_to=CONF['attachments']['upload_folder'], verbose_name=_('Document'))
        insert_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Insert date'))

        creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
        modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

        class Meta:
            verbose_name = _('Attachment')
            verbose_name_plural = _('Attachments')

        def __str__(self):
            return '{}'.format(self.file.name)

        def get_url(self):
            return '{}'.format(self.file.url)

if CONF is not None and CONF['typology_model']['enabled']:
    class MessageTypology(Model):
        typology = models.CharField(max_length=255, unique=True, verbose_name=_('Typology'))

        creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
        modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

        class Meta:
            verbose_name = _('Message typology')
            verbose_name_plural = _('Message typologies')

        def __str__(self):
            return '{}'.format(self.typology)

        @staticmethod
        def autocomplete_search_fields():
            return "typology__icontains",


class MessageSent(Model):
    if CONF is not None and CONF['typology_model']['enabled']:
        typology = models.ForeignKey(
            'django_webix_sender.MessageTypology',
            blank=not CONF['typology_model']['required'],
            null=not CONF['typology_model']['required'],
            on_delete=models.CASCADE,
            verbose_name=_('Typology')
        )
    send_method = models.CharField(max_length=255, verbose_name=_('Send method'))
    subject = models.TextField(blank=True, null=True, verbose_name=_('Subject'))
    body = models.TextField(blank=True, null=True, verbose_name=_('Body'))
    extra = JSONField(blank=True, null=True, verbose_name=_('Extra'))
    attachments = models.ManyToManyField(
        CONF['attachments']['model'],
        blank=True,
        db_constraint=False,
        verbose_name=_('Attachments')
    )

    # Invoice
    cost = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal('0.0000'), verbose_name=_('Cost'))
    invoiced = models.BooleanField(default=False, verbose_name=_('Invoiced'))

    # Sender info
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                             verbose_name=_('User'))
    sender = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Sender'))

    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
    modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

    class Meta:
        verbose_name = _('Sent message')
        verbose_name_plural = _('Sent messages')

    def __str__(self):
        if CONF is not None and CONF['typology_model']['enabled']:
            return "[{}] {}".format(self.send_method, self.typology)
        return "{}".format(self.send_method)


class MessageRecipient(Model):
    message_sent = models.ForeignKey('django_webix_sender.MessageSent', on_delete=models.CASCADE,
                                     verbose_name=_('Message sent'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    recipient = GenericForeignKey('content_type', 'object_id')
    recipient_address = models.CharField(max_length=255, verbose_name=_('Recipient address'))
    sent_number = models.IntegerField(default=1, verbose_name=_('Sent number'))
    status = models.CharField(max_length=32, choices=(
        ('success', _('Success')),
        ('failed', _('Failed')),
        ('unknown', _('Unknown')),
        ('invalid', _('Invalid')),
        ('duplicate', _('Duplicate'))
    ), default='unknown')
    extra = models.TextField(blank=True, null=True, verbose_name=_('Extra'))

    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Creation date'))
    modification_date = models.DateTimeField(auto_now=True, verbose_name=_('Modification data'))

    class Meta:
        verbose_name = _('Recipient')
        verbose_name_plural = _('Recipients')

    def __str__(self):
        return str(self.recipient)


# Telegram
class TelegramPersistence(Model):
    typology = models.CharField(max_length=32, choices=[
        (i, i) for i in ['user_data', 'chat_data', 'bot_data', 'conversations']
    ], unique=True)
    data = JSONField()

    class Meta:
        verbose_name = _("Telegram Persistence")
        verbose_name_plural = _("Telegram Persistences")
