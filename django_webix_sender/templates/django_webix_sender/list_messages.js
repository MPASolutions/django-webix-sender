{% extends "django_webix/generic/list.js" %}
{% load static i18n %}

{% block webix_content %}
    {% get_media_prefix as media_prefix %}

    function download_attachment(pk) {
      webix.ajax().get("{% url 'django_webix_sender.attachment_check' %}" + '?pk_attachment=' + pk, {
        success: function (text, data, XmlHttpRequest) {
          var result = data.json();
          if ('exist' in result && result.exist) {
            var file_path = '{{ media_prefix }}' + result.path;
            var a = document.createElement('A');
            a.href = file_path;
            a.download = file_path.substr(file_path.lastIndexOf('/') + 1);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
          }else {
            webix.alert({
              title: "{{ _("File mancante")|escapejs }}",
              ok: "{{ _("Ok")|escapejs }}",
              text: "{{ _("File ancora non presente.")|escapejs }}",
            });
          }
        },
        error: function (text, data, XmlHttpRequest) {
          webix.alert({
            title: "{{ _("File mancante")|escapejs }}",
            ok: "{{ _("Ok")|escapejs }}",
            text: "{{ _("File ancora non presente.")|escapejs }}",
          });
        },
      });
    }

    var attachmentsTemplate = function (obj, common, value, config) {
        var values = String(value).split('|').filter(Boolean);
        var result = "";
        for (var index = 0; index < values.length; ++index) {
            result += "<span style='text-decoration: none; color: black; padding-right: 5px;' > <i onclick='download_attachment(\"" + values[index] + "\")' class='far fa-file-alt'></i> </span>";
            // result += "<a style='text-decoration: none; color: black; padding-right: 5px;' target='_blank' href='{{ media_prefix }}" + values[index] + "'><i class='far fa-file-alt'></i></a>";
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
