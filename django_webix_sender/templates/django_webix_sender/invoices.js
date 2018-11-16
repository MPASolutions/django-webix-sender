{% load static i18n verbose_name field_type %}

{% block content %}
webix.ui([], $$('content_right'));

$$("content_right").addView({
    rows: [
        {
            view: "toolbar",
            elements: [
                {
                    id: 'send_method',
                    view: 'combo',
                    value: "{{ request.GET.send_method }}",
                    label: "{% trans 'Send method' %}",
                    labelWidth: 130,
                    labelAlign: 'right',
                    options: [
                        {id: "", value: "", $empty: true},
                        {% for send_method in send_methods %}
                        {
                            id: "{{ send_method.key|safe|escapejs }}",
                            value: "{{ send_method.value|safe|escapejs }}"
                        },
                        {% endfor %}
                    ],
                    on: {
                        onChange: function (newv, oldv) {
                            var url = "{% url 'django_webix_sender.invoices' %}";
                            url += (url.indexOf('?') >= 0 ? '&' : '?') + $.param({'send_method': newv});
                            load_js(url);
                        }
                    }
                },
                {$template: "Spacer", width: 100},
                {
                    view: 'label',
                    align: 'right',
                    label: "{% trans 'Warning! if there are messages with an unknown status, the data is not updated' %}"
                }
            ]
        },
        {
            view: "scrollview",
            scroll: "y",
            body: {
                rows: [
                    {% for sender in senders %}
                    {
                        autoheight: true,
                        rows: [
                            {
                                view: "template",
                                template: "{{ sender.name|safe|escapejs }} - {{ sender.send_method|safe|escapejs }}",
                                type: "header"
                            },
                            {
                                id: 'datatable_{{ forloop.counter0 }}',
                                view: "datatable",
                                autoheight: true,
                                select: false,
                                navigation: false,
                                columns: [
                                    {
                                        id: "period",
                                        header: "{% trans 'Period' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "messages_unknown",
                                        header: "{% trans 'Unknowm status' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "messages_fail",
                                        header: "{% trans 'Not send' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "invoiced",
                                        header: "{% trans 'Invoiced' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "to_be_invoiced",
                                        header: "{% trans 'To be invoiced' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "price_invoiced",
                                        header: "{% trans 'Price invoiced' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "price_to_be_invoiced",
                                        header: "{% trans 'Price to be invoiced' %}",
                                        fillspace: true
                                    },
                                    {
                                        id: "rating",
                                        header: "",
                                        template: function () {
                                            return "<div class='webix_el_button'><button class='webixtype_base'>{% trans 'marks as billed' %}</button></div>";
                                        },
                                        width: 200
                                    }
                                ],
                                data: [
                                    {% for period in sender.periods %}
                                    {
                                        'period': "{{ period.period|safe|escapejs }}",
                                        'messages_unknown': {{ period.messages_unknown|default:0|safe|escapejs }},
                                        'messages_fail': "{{ period.messages_fail|default:0|safe|escapejs }}",
                                        'invoiced': "{{ period.invoiced|default:0|safe|escapejs }}",
                                        'to_be_invoiced': "{{ period.to_be_invoiced|default:0|safe|escapejs }}",
                                        'price_invoiced': "{{ period.price_invoiced|default:0|safe|escapejs }}",
                                        'price_to_be_invoiced': "{{ period.price_to_be_invoiced|default:0|safe|escapejs }}",
                                        'send_method_code': "{{ sender.send_method_code|safe|escapejs }}",
                                        'sender': "{{ sender.name|safe|escapejs }}"
                                    },
                                    {% endfor %}
                                ],
                                onClick: {
                                    webixtype_base: function (ev, id) {
                                        marks_invoiced(this, id);
                                    }
                                }
                            }
                        ],
                        padding: 10
                    },
                    {% endfor %}
                ]
            }
        }
    ]
});

var marks_invoiced = function (datatable, id) {
    var period = datatable.getItem(id.row).period;
    var messages_unknown = datatable.getItem(id.row).messages_unknown;
    var send_method = datatable.getItem(id.row).send_method_code;
    var sender = datatable.getItem(id.row).sender;
    var masks_billed = function (period) {
        webix.confirm({
            title: "{% trans 'Confirmation' %}",
            text: "{% trans 'Are you sure you want to mark these communications as billed?' %}",
            ok: "{% trans 'Yes' %}",
            cancel: "{% trans 'No' %}",
            callback: function (result) {
                var data = {
                    'period': period,
                    'sender': sender,
                    'send_method': send_method
                }
                {% if request.GET.year %}
                    data['year'] = "{{ request.GET.year }}";
                {% endif %}
                if (result) {
                    // TODO: segnare come fatturati
                    webix.ajax().post("{% url 'django_webix_sender.invoices' %}", data, {
                        error: function (text, data, XmlHttpRequest) {
                            alert("error");
                        },
                        success: function (text, data, XmlHttpRequest) {
                            var url = "{% url 'django_webix_sender.invoices' %}";
                            var send_method = $$('send_method').getValue();
                            var params = {};
                            if (send_method !== '') {
                                params['send_method'] = send_method;
                            }
                            url += (url.indexOf('?') >= 0 ? '&' : '?') + $.param(params);
                            load_js(url);
                        }
                    });
                }
            }
        });
    }

    if (messages_unknown > 0) {
        webix.alert({
            title: "{% trans 'Caution!' %}",
            text: "{% trans 'There are unknown status for this communication' %}",
            callback: function () {
                masks_billed(period);
            }
        });
    } else {
        masks_billed(period);
    }
}

{% endblock %}
