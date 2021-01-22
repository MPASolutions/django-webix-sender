{% extends "django_webix/generic/list.js" %}
{% load static %}

{% block webix_content %}
    {% get_media_prefix as media_prefix %}

    var attachmentsTemplate = function (obj, common, value, config) {
        var values = String(value).split('|').filter(Boolean);
        var result = "";
        for (var index = 0; index < values.length; ++index) {
            result += "<a style='text-decoration: none; color: black; padding-right: 5px;' target='_blank' href='{{ media_prefix }}" + values[index] + "'><i class='far fa-file-alt'></i></a>";
        }
        return result;
    };

    {{ block.super }}

    $$('{{ view_prefix }}datatable').attachEvent("onAfterLoad", function () {
        this.adjustRowHeight();
        this.render();
    });
{% endblock %}

{% block datatable_headermenu %}
    fixedRowHeight: false,
    rowLineHeight: 25,
    rowHeight: 25,
{% endblock %}
