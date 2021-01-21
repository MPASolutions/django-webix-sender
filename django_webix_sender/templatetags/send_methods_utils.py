# -*- coding: utf-8 -*-

from django import template
from django.conf import settings

register = template.Library()

CONF = getattr(settings, "WEBIX_SENDER", None)


@register.simple_tag(takes_context=True)
def is_list_available(context):
    """ Returns boolean to indicate if there are lists configured """

    for send_method in CONF['send_methods']:
        if send_method['show_in_list'] is True:
            return True
    return False


@register.simple_tag(takes_context=True)
def is_chat_available(context):
    """ Returns boolean to indicate if there are chats configured """

    for send_method in CONF['send_methods']:
        if send_method['show_in_chat'] is True:
            return True
    return False
