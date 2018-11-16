{% load static i18n verbose_name field_type %}

{% block content %}
webix.ui([], $$('content_right'));

var custom_bool = function (obj, common, value) {
  if (value === true)
    return "<img style='width:12px;' src='/static/admin/img/icon-yes.svg'>";
  else
    return "<img style='width:12px;' src='/static/admin/img/icon-no.svg'>";
};

function match(a, b) {
    return a.toString() == b;
}

$$("content_right").addView({
    rows: [
        {
            padding: 10,
            cols: [
                {% for datatable in datatables %}
                {
                    gravity: 1,
                    rows: [
                        {% if use_dynamic_filters %}
                        {
                            id: 'filter_{{ datatable.model }}',
                            view: "multicombo",
                            placeholder: "{% trans 'Filter the list by applying filters' %}",
                            labelWidth: 0,
                            options: [
                                {% for filter in datatable.filters %}
                                {
                                    'id': "{{ filter.id }}",
                                    'value': "{{ filter.value|safe|escapejs }}"
                                },
                                {% endfor %}
                            ],
                            on: {
                                onChange: function (newv, oldv) {
                                    var dt = $$("{{ datatable.model }}");
                                    dt.clearAll();

                                    if (newv !== '') {
                                        var pks = newv.split(",");
                                        for (var i = 0; i < pks.length; i++) {
                                            pks[i] = "pk=" + pks[i];
                                        }
                                        pks = pks.join("&");
                                        dt.load('{% url 'django_webix_sender.getlist' %}?contentype={{ datatable.model }}&' + pks);
                                    }
                                }
                            }
                        },
                        {view: "spacer", height: 10},
                        {% endif %}
                        {
                            id: '{{ datatable.model }}',
                            view: "datatable",
                            multiselect: true,
                            navigation: true,
                            select: "row",
                            scheme: {
                                $init: function (obj) {
                                    obj.index = this.count();
                                }
                            },
                            columns: [
                                {
                                    id: "index",
                                    header: "",
                                    width: 40,
                                    minWidth: 40
                                },
                                {
                                    id: "checkbox_action",
                                    header: {content: "masterCheckbox", css: "center"},
                                    template: "{common.checkbox()}",
                                    width: 40,
                                    minWidth: 40,
                                    maxWidth: 40
                                },
                                {% for field in datatable.fields %}
                                {
                                    id: "{{ field }}",
                                    header: ["{% get_verbose_field_name datatable.model field %}",
                                        {% field_type datatable.model field as field_t %}
                                        {% if field_t == "BooleanField" %}
                                            {
                                                content: 'selectFilter',
                                                options: [
                                                    {id: '', value: '{% trans 'All' %}'},
                                                    {id: 'true', value: '{% trans 'Yes' %}'},
                                                    {id: 'false', value: '{% trans 'No' %}'}
                                                ],
                                                compare:match
                                            },
                                        {% else %}
                                            {content: "textFilter"}
                                        {% endif %}
                                    ],
                                    {% if field_t == "BooleanField" %}
                                        template: custom_bool,
                                    {% endif %}
                                    adjust: "all"
                                },
                                {% endfor %}
                            ],
                            data: [],
                            on: {
                                onBeforeLoad: function () {
                                    $$('content_right').showOverlay("<img src='{% static 'webix_custom/loading.gif' %}'>");
                                },
                                onAfterLoad: function () {
                                    $$('content_right').hideOverlay();
                                },
                                onCheck: function (rowId, colId, state) {
                                    if (state) {
                                        this.select(rowId, true);
                                    } else {
                                        this.unselect(rowId, true);
                                    }
                                },
                                "data->onStoreUpdated": function () {
                                    this.data.each(function (obj, i) {
                                        if (obj !== undefined) {
                                            obj.index = i + 1;
                                        }
                                    })
                                }
                            }
                        }
                    ]
                },
                {view: "spacer", width: 10},
                {% endfor %}
            ]
        },
        {
            view: "toolbar",
            margin: 5,
            cols: [
                {
                    view: "richselect",
                    id: "action_combo",
                    maxWidth: "300",
                    value: 1,
                    label: '{% trans 'Action' %}',
                    options: [
                        {id: 1, value: "------------"},
                        {% for send_method in send_methods %}
                            {id: "{{ send_method.method }}.{{ send_method.function }}", value: "{{ send_method.verbose_name }}"},
                        {% endfor %}
                    ]
                },
                {
                    view: "button",
                    id: "action_button",
                    value: "{% trans 'Go' %}",
                    inputWidth: 50,
                    width: 50,
                    on: {
                        onItemClick: function () {
                            var action_original = $$("action_combo").getValue();
                            action = action_original.split(".")[0];

                            var recipients = {};
                            {% for datatable in datatables %}
                                $$("{{ datatable.model }}").getSelectedItem(true).forEach(function (element) {
                                    if (recipients["{{ datatable.model }}"] === undefined) {
                                        recipients["{{ datatable.model }}"] = [];
                                    }
                                    recipients["{{ datatable.model }}"].push(element['id']);
                                })
                            {% endfor %}

                            {% if 'sms' in send_method_types %}
                            if (action === "sms") {
                                django_webix_sender.open(action_original, recipients);
                            }
                            {% endif %}

                            {% if 'email' in send_method_types %}
                            if (action === "email") {
                                django_webix_sender.open(action_original, recipients);
                            }
                            {% endif %}
                        }
                    }
                },
                {
                    view: "label",
                    id: "count_bottom_label_selected",
                    label: "0 {% trans 'selected of' %}",
                    hidden: true,
                    width: 150,
                    paddingX: 0,
                    align: "right"
                },
                {
                    view: "label",
                    id: "count_bottom_label_total",
                    label: "0",
                    hidden: true,
                    width: 40,
                    paddingX: 0,
                    align: "left"
                }
            ]
        }
    ]
});

/**
 * Funzione per contare il numero di elementi nelle varie datatables
 *
 * @returns {number} numero di elementi nelle datatables
 */
var getDatatablesItems = function () {
    var total = 0;
    var selected = 0;
    {% for datatable in datatables %}
        total += $$('{{ datatable.model }}').count();
        selected += $$('{{ datatable.model }}').getSelectedItem(true).length;
    {% endfor %}

    $$("count_bottom_label_selected").setValue(selected + " {% trans 'selected of' %}");
    $$("count_bottom_label_total").setValue(total);
    $$("count_bottom_label_selected").show();
    $$("count_bottom_label_total").show();

    return total;
}

{# Attach events to datatables and loads data if `filters` is not installed #}
{% for datatable in datatables %}
    $$("{{ datatable.model }}").on_click.webix_cell = function () {
      return false;
    };
    $$("{{ datatable.model }}").$view.oncontextmenu = function () {
      return false;
    };

    $$('{{ datatable.model }}').attachEvent("onAfterLoad", getDatatablesItems);
    $$('{{ datatable.model }}').attachEvent("onAfterFilter", getDatatablesItems);
    $$('{{ datatable.model }}').attachEvent("onAfterDelete", getDatatablesItems);
    $$('{{ datatable.model }}').attachEvent("onAfterSelect", getDatatablesItems);
    $$('{{ datatable.model }}').attachEvent("onAfterUnSelect", getDatatablesItems);
    {% if not use_dynamic_filters %}
        var dt = $$("{{ datatable.model }}");
        dt.load("{% url 'django_webix_sender.getlist' %}?contentype={{ datatable.model }}");
    {% endif %}
{% endfor %}

// Include window class
var django_webix_sender = undefined;
$.ajax({
    url: "{% url 'django_webix_sender.sender_window' %}",
    dataType: "script",
    success: function () {
        django_webix_sender = new DjangoWebixSender();
    },
    error: function () {
        webix.message({
            type: "error",
            expire: 10000,
            text: '{% trans 'Unable to load sender class' %}'
        });
    }
});

{% endblock %}
