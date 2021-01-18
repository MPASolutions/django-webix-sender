# -*- coding: utf-8 -*-

from django.apps import apps
from django.conf import settings
from django.utils.translation import gettext
from telegram import Update
from telegram.ext import CallbackContext, DispatcherHandlerStop


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(gettext('Hi!'))


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(gettext('Help!'))


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def check_user(update: Update, context: CallbackContext) -> None:
    """Check if user is enabled to chat with bot"""

    CONF = getattr(settings, "WEBIX_SENDER", None)

    # Check in every enabled models
    _exists = False
    for recipient in CONF['recipients']:
        app_label, model = recipient['model'].lower().split(".")
        model_class = apps.get_model(app_label=app_label, model_name=model)
        _exists = model_class.objects.filter(
            **{model_class.get_telegram_fieldpath(): update.message.from_user.id}
        ).exists()
        if _exists:
            break

    if not _exists:
        update.message.reply_text(gettext("Your user is not authorized to use this Bot"))
        raise DispatcherHandlerStop()
