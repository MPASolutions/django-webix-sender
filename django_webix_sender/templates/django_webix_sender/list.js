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
                            options: {{ datatable.filters|safe }},
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

                            {% if 'sms' in send_method_types %}
                            if (action === "sms") {
                                if (getDatatablesSelectedItems().length == 0) {
                                    webix.alert({
                                        title: "{% trans 'Caution!' %}",
                                        text: "{% trans 'There are no recipients for this communication' %}",
                                        callback: function () {
                                            if (window_sms) {
                                                window_sms.destructor();
                                            }
                                            window_sms = create_window_sms(action_original);
                                            window_sms.show();
                                        }
                                    });
                                } else {
                                    if (window_sms) {
                                        window_sms.destructor();
                                    }
                                    window_sms = create_window_sms(action_original);
                                    window_sms.show();
                                }
                            }
                            {% endif %}

                            {% if 'email' in send_method_types %}
                            if (action === "email") {
                                if (getDatatablesSelectedItems().length == 0) {
                                    webix.alert({
                                        title: "{% trans 'Caution!' %}",
                                        text: "{% trans 'There are no recipients for this communication' %}",
                                        callback: function (result) {
                                            if (window_email) {
                                                window_email.destructor();
                                            }
                                            window_email = create_window_email(action_original);
                                            window_email.show();
                                        }
                                    });
                                } else {
                                    if (window_email) {
                                        window_email.destructor();
                                    }
                                    window_email = create_window_email(action_original);
                                    window_email.show();
                                }
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


/**
 * Funzione che ritorna gli id con il modello delle istanze selezionate
 *
 * @returns {Array} id con modello istanze selezionate
 */
var getDatatablesSelectedItems = function () {
    var recipients = [];
    {% for datatable in datatables %}
    $$("{{ datatable.model }}").getSelectedItem(true).forEach(function (element) {
        recipients.push(element['id'] + '__{{ datatable.model }}');
    })
    {% endfor %}

    return recipients;
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

{% if 'sms' in send_method_types %}
/**
 * Funzione per creare la finestra dove inserire i dati da inviare
 *
 * @returns {webix.ui.baseview | webix.ui} finestra di webix
 */
function create_window_sms(action) {
    return new webix.ui({
        view: "window",
        id: "window_sms",
        width: 600,
        height: 500,
        modal: true,
        move: true,
        resize: false,
        position: "center",
        head: {
            view: "toolbar", cols: [
                {
                    view: "label",
                    label: "{% trans 'Send SMS' %}"
                },
                {
                    view: "button",
                    label: '{% trans 'Close' %}',
                    width: 100,
                    align: 'right',
                    click: "$$('window_sms').destructor();"
                }
            ]
        },
        body: {
            rows: [{
                view: 'form',
                id: 'sms_form',
                padding: 10,
                elements: [
                    {% if typology_model.enabled %}
                        {
                            view: "combo",
                            id: 'typology',
                            name: 'typology',
                            label: '{% trans 'Typology' %}',
                            options: '{% url 'webix_autocomplete_lookup' %}?app_label=django_webix_sender&model_name=messagetypology'
                        },
                        {
                            view: "template",
                            template: "<hr />",
                            type: "clean",
                            height: 20
                        },
                    {% endif %}
                    {
                        view: 'label',
                        label: '{% trans 'Body' %}'
                    },
                    {
                        view: "textarea",
                        id: 'body',
                        name: 'body',
                        height: 150,
                        on: {
                            onKeyPress: function () {
                                webix.delay(function () {
                                    var count = $$("body").getValue().length;
                                    $$("length").setValue(count + " {% trans 'characters' %}");
                                });
                            }
                        }
                    },
                    {
                        view: "label",
                        id: "length",
                        label: "0 {% trans 'characters' %}",
                        align: "right"
                    },
                    {
                        view: 'button',
                        label: '{% trans 'Send' %}',
                        on: {
                            onItemClick: function () {
                                if (!$$("sms_form").validate({hidden: true})) {
                                    webix.message({
                                        type: "error",
                                        expire: 10000,
                                        text: '{% trans 'You have to fill in all the required fields' %}'
                                    });
                                    return;
                                }

                                $$('content_right').showOverlay("<img src='{% static 'webix_custom/loading.gif' %}'>");

                                var data = new FormData();
                                data.append('typology', $$('typology').getValue());
                                data.append('send_method', action);
                                data.append('body', $$('body').getValue());
                                data.append('recipients', getDatatablesSelectedItems());

                                $.ajax({
                                    type: "POST",
                                    url: "{% url 'django_webix_sender.send' %}",
                                    data: data,
                                    processData: false,
                                    contentType: false,
                                    cache: false,
                                    timeout: 600000,
                                    success: function () {
                                        $$('content_right').hideOverlay();
                                        webix.message({type: "info", expire: 10000, text: "{% trans 'The messages have been sent' %}"});
                                        window_sms.destructor();
                                    },
                                    error: function () {
                                        $$('content_right').hideOverlay();
                                        webix.message({
                                            type: "error",
                                            expire: 10000,
                                            text: '{% trans 'Unable to send messages' %}'
                                        });
                                    }
                                });
                            }
                        }
                    }
                ],
                rules: {
                    {% if typology_model.enabled and typology_model.required %}
                        "typology": webix.rules.isNotEmpty,
                    {% endif %}
                    "body": webix.rules.isNotEmpty
                }
            }]
    }
    });
}
var window_sms;
{% endif %}

{% if 'email' in send_method_types %}
/**
 * Funzione per creare la finestra dove inserire i dati da inviare
 *
 * @returns {webix.ui.baseview | webix.ui} finestra di webix
 */
function create_window_email(action) {
    return new webix.ui({
        view: "window",
        id: "window_email",
        width: 600,
        height: 500,
        modal: true,
        move: true,
        resize: false,
        position: "center",
        head: {
            view: "toolbar", cols: [
                {
                    view: "label",
                    label: "{% trans 'Send email' %}"
                },
                {
                    view: "button",
                    label: '{% trans 'Close' %}',
                    width: 100,
                    align: 'right',
                    click: "$$('window_email').destructor();"
                }
            ]
        },
        body: {
            rows: [{
                view: 'form',
                id: 'email_form',
                padding: 10,
                elements: [
                    {% if typology_model.enabled %}
                        {
                            view: "combo",
                            id: 'typology',
                            name: 'typology',
                            label: '{% trans 'Typology' %}',
                            options: '{% url 'webix_autocomplete_lookup' %}?app_label=django_webix_sender&model_name=messagetypology'
                        },
                        {
                            view: "template",
                            template: "<hr />",
                            type: "clean",
                            height: 20
                        },
                    {% endif %}
                    {
                        view: 'text',
                        id: 'subject',
                        name: 'subject',
                        label: '{% trans 'Subject' %}'
                    },
                    {
                        view: 'label',
                        label: '{% trans 'Body' %}'
                    },
                    {
                        view: "textarea",
                        id: 'body',
                        name: 'body',
                        height: 150
                    },
                    {
                        view: "uploader",
                        id: "attachments",
                        value: "{% trans 'Attach file' %}",
                        link: "attachments_list",
                        autosend: false
                    },
                    {
                        view: "list",
                        id: "attachments_list",
                        type: "uploader",
                        autoheight: true
                    },
                    {
                        view: 'button',
                        label: '{% trans 'Send' %}',
                        on: {
                            onItemClick: function () {
                                if (!$$("email_form").validate({hidden: true})) {
                                    webix.message({
                                        type: "error",
                                        expire: 10000,
                                        text: '{% trans 'You have to fill in all the required fields' %}'
                                    });
                                    return;
                                }

                                $$('content_right').showOverlay("<img src='{% static 'webix_custom/loading.gif' %}'>");

                                var data = new FormData();
                                data.append('typology', $$('typology').getValue());
                                data.append('send_method', action);
                                data.append('subject', $$('subject').getValue());
                                data.append('body', $$('body').getValue());
                                $$("attachments").files.data.each(function (obj) {
                                    data.append('file_' + obj.id, obj.file);
                                });
                                data.append('recipients', getDatatablesSelectedItems());

                                $.ajax({
                                    type: "POST",
                                    enctype: 'multipart/form-data',
                                    url: "{% url 'django_webix_sender.send' %}",
                                    data: data,
                                    processData: false,
                                    contentType: false,
                                    cache: false,
                                    timeout: 600000,
                                    success: function () {
                                        $$('content_right').hideOverlay();
                                        webix.message({type: "info", expire: 10000, text: "{% trans 'The messages have been sent' %}"});
                                        window_sms.destructor();
                                    },
                                    error: function () {
                                        $$('content_right').hideOverlay();
                                        webix.message({
                                            type: "error",
                                            expire: 10000,
                                            text: '{% trans 'Unable to send messages' %}'
                                        });
                                    }
                                });
                            }
                        }
                    }
                ],
                rules: {
                    {% if typology_model.enabled and typology_model.required %}
                        "typology": webix.rules.isNotEmpty,
                    {% endif %}
                    "subject": webix.rules.isNotEmpty,
                    "body": webix.rules.isNotEmpty
                }
            }]
        }
    });
}
var window_email;
{% endif %}
{% endblock %}
