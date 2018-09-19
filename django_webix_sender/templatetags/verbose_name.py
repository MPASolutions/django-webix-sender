# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import template
from django.contrib.contenttypes.models import ContentType

register = template.Library()


@register.assignment_tag(takes_context=True)
def get_verbose_field_name(context, model, field_name):
    """ Returns verbose_name for a field. """

    app_label, model = model.split(".")
    model_class = ContentType.objects.get(app_label=app_label, model=model).model_class()
    return model_class._meta.get_field(field_name).verbose_name
