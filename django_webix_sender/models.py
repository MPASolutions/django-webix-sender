# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from django_webix_sender.settings import CONF
from django_webix_sender.utils import my_import


def save_attachments(files):
    attachments = []
    for filename, file in files.items():
        attachment = MessageAttachment.objects.create(
            file=file
        )
        attachments.append(attachment)
    return attachments


class DjangoWebixSender(models.Model):
    class Meta:
        abstract = True

    @property
    def get_sms(self):
        raise NotImplementedError("`get_sms` not implemented!")

    @property
    def get_email(self):
        raise NotImplementedError("`get_email` not implemented!")

    @property
    def get_sms_related(self):
        return []

    @property
    def get_email_related(self):
        return []


if any(_recipients['model'] == 'django_webix_sender.Customer' for _recipients in CONF['recipients']):
    @python_2_unicode_compatible
    class Customer(DjangoWebixSender):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                                 verbose_name=_('User'))
        name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Name'))
        vat_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Vat number'))
        fiscal_code = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Fiscal code'))
        sms = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Sms'))
        email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email'))
        note = models.TextField(blank=True, null=True, verbose_name=_('Note'))
        extra = JSONField(blank=True, null=True, verbose_name=_('Extra'))
        typology = models.ForeignKey('django_webix_sender.CustomerTypology', blank=True, null=True,
                                     verbose_name=_('Typology'))

        class Meta:
            verbose_name = _('Customer')
            verbose_name_plural = _('Customers')

        def __str__(self):
            return '{}'.format(self.name)

        @property
        def get_sms(self):
            return self.sms

        @property
        def get_email(self):
            return self.email


    @python_2_unicode_compatible
    class CustomerTypology(models.Model):
        typology = models.CharField(max_length=255, unique=True, verbose_name=_('Typology'))

        class Meta:
            verbose_name = _('Customer typology')
            verbose_name_plural = _('Customer typologies')

        def __str__(self):
            return '{}'.format(self.typology)

if any(_recipients['model'] == 'django_webix_sender.ExternalSubject' for _recipients in CONF['recipients']):
    @python_2_unicode_compatible
    class ExternalSubject(DjangoWebixSender):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE,
                                 verbose_name=_('User'))
        name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Name'))
        vat_number = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Vat number'))
        fiscal_code = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Fiscal code'))
        sms = models.CharField(max_length=32, blank=True, null=True, verbose_name=_('Sms'))
        email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_('Email'))
        note = models.TextField(blank=True, null=True, verbose_name=_('Note'))
        extra = JSONField(blank=True, null=True, verbose_name=_('Extra'))
        typology = models.ForeignKey('django_webix_sender.ExternalSubjectTypology', blank=True, null=True,
                                     verbose_name=_('Typology'))

        class Meta:
            verbose_name = _('External subject')
            verbose_name_plural = _('External subjects')

        def __str__(self):
            return '{}'.format(self.name)

        @property
        def get_sms(self):
            return self.sms

        @property
        def get_email(self):
            return self.email


    @python_2_unicode_compatible
    class ExternalSubjectTypology(models.Model):
        typology = models.CharField(max_length=255, unique=True, verbose_name=_('Typology'))

        class Meta:
            verbose_name = _('External subject typology')
            verbose_name_plural = _('External subject typologies')

        def __str__(self):
            return '{}'.format(self.typology)


@python_2_unicode_compatible
class MessageAttachment(models.Model):
    file = models.FileField(upload_to=CONF['attachments']['upload_folder'], verbose_name=_('Document'))
    insert_date = models.DateTimeField(auto_now_add=True, verbose_name=_('Insert date'))

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    def __str__(self):
        return '{}'.format(self.file.name)

    def get_url(self):
        return '{}'.format(self.file.url)


if CONF['typology_model']['enabled']:
    @python_2_unicode_compatible
    class MessageTypology(models.Model):
        typology = models.CharField(max_length=255, unique=True, verbose_name=_('Typology'))

        class Meta:
            verbose_name = _('Message typology')
            verbose_name_plural = _('Message typologies')

        def __str__(self):
            return '{}'.format(self.typology)

        @staticmethod
        def autocomplete_search_fields():
            return "typology__icontains",


@python_2_unicode_compatible
class MessageSent(models.Model):
    if CONF['typology_model']['enabled']:
        typology = models.ForeignKey(
            'django_webix_sender.MessageTypology',
            blank=not CONF['typology_model']['required'],
            null=not CONF['typology_model']['required'],
            verbose_name=_('Typology')
        )
    send_method = models.CharField(max_length=255, verbose_name=_('Send method'))
    subject = models.TextField(blank=True, null=True, verbose_name=_('Subject'))
    body = models.TextField(blank=True, null=True, verbose_name=_('Body'))
    attachments = models.ManyToManyField(
        CONF['attachments']['model'],
        blank=True,
        db_constraint=False,
        verbose_name=_('Attachments')
    )

    class Meta:
        verbose_name = _('Sent message')
        verbose_name_plural = _('Sent messages')

    def __str__(self):
        return "[{}] {}".format(self.send_method, self.typology)

    def save_attachments(self, files):
        method = my_import(CONF['attachments']['save_function'])
        if not callable(method):
            raise Exception(_('Attachments `save_function` must be a callable method'))
        method(self, files)


@python_2_unicode_compatible
class MessageRecipient(models.Model):
    message_sent = models.ForeignKey('django_webix_sender.MessageSent', verbose_name=_('Message sent'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    recipient = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('Recipient')
        verbose_name_plural = _('Recipients')

    def __str__(self):
        return str(self.recipient)
