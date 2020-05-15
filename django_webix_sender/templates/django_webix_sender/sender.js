{% load static i18n %}

/**
 * Django Webix Sender window class
 *
 * @constructor
 */
function DjangoWebixSender() {
    /**
     * Window object
     *
     * @type {webix.ui.baseview | webix.ui}
     */
    var sender_window = undefined;

    /**
     * Create window helper
     *
     * @param send_method
     * @param recipients
     * @param default_text
     */
    var check_recipients_count = function (send_method, recipients, default_text) {
        if (sender_window) {
            sender_window.destructor();
        }
        sender_window = create_window(send_method, recipients, default_text);
        sender_window.show();
    }

    /**
     * Returns form elements
     *
     * @param send_method
     * @param send_method_original
     * @param recipients
     * @param default_text
     * @returns {*[]}
     */
    var get_elements = function (send_method, send_method_original, recipients, default_text) {
        var elements = [
            {% if typology_model.enabled %}
            {
                view: "combo",
                id: 'django-webix-sender-form-typology',
                name: 'typology',
                label: '{{_("Typology")|escapejs}}',
                suggest: {
                    view: "suggest",
                    keyPressTimeout: 400,
                    body: {
                        dataFeed: '{% url 'webix_autocomplete_lookup' %}?app_label=django_webix_sender&model_name=messagetypology'
                    },
                    url: '{% url 'webix_autocomplete_lookup' %}?app_label=django_webix_sender&model_name=messagetypology&filter[value]='
                }
            },
            {
                view: "template",
                template: "<hr />",
                type: "clean",
                height: 20
            },
            {% endif %}
        ];
        if (send_method === 'email') {
            elements.push({
                view: 'text',
                id: 'django-webix-sender-form-subject',
                name: 'subject',
                label: '{{_("Subject")|escapejs}}'
            });
        }
        elements.push({
            view: 'label',
            label: '{{_("Body")|escapejs}}'
        });
        elements.push({
            view: "textarea",
            id: 'django-webix-sender-form-body',
            name: 'body',
            height: 150,
            value: default_text !== undefined ? default_text : '',
            on: {
                onKeyPress: function () {
                    if (send_method === 'sms') {
                        webix.delay(function () {
                            var count = $$("django-webix-sender-form-body").getValue().length;
                            $$("django-webix-sender-form-length").setValue(count + " {{_("characters")|escapejs}}");
                        });
                    }
                }
            }
        });
        if (send_method === 'sms') {
            elements.push({
                view: "label",
                id: "django-webix-sender-form-length",
                label: "0 {{_("characters")|escapejs}}",
                align: "right"
            });
        }
        if (send_method === 'email') {
            elements.push({
                view: "uploader",
                id: "django-webix-sender-form-attachments",
                value: "{{_("Attach file")|escapejs}}",
                link: "django-webix-sender-form-attachments_list",
                autosend: false
            });
            elements.push({
                view: "list",
                id: "django-webix-sender-form-attachments_list",
                type: "uploader",
                autoheight: true
            });
        }
        elements.push({
            view: 'button',
            label: '{{_("Send")|escapejs}}',
            on: {
                onItemClick: function () {
                    if (!$$("django-webix-sender-form").validate({hidden: true})) {
                        webix.message({
                            type: "error",
                            expire: 10000,
                            text: '{{_("You have to fill in all the required fields")|escapejs}}'
                        });
                        return;
                    }

                    var data = new FormData();
                    {% if typology_model.enabled %}
                        data.append('typology', $$('django-webix-sender-form-typology').getValue());
                    {% endif %}
                    data.append('send_method', send_method_original);
                    if (send_method === 'email') {
                        data.append('subject', $$('django-webix-sender-form-subject').getValue());
                    }
                    data.append('body', $$('django-webix-sender-form-body').getValue());
                    if (send_method === 'email') {
                        $$("django-webix-sender-form-attachments").files.data.each(function (obj) {
                            data.append('file_' + obj.id, obj.file);
                        });
                    }
                    data.append('recipients', JSON.stringify(recipients));

                    $.ajax({
                        type: "POST",
                        enctype: 'multipart/form-data',
                        url: "{% url 'django_webix_sender.send' %}",
                        data: data,
                        processData: false,
                        contentType: false,
                        cache: false,
                        timeout: 600000,
                        success: function (result) {
                            var valids = "{{_("Valid recipients: ")|escapejs}}" + result['valids'];
                            var invalids = "{{_("Invalids recipients: ")|escapejs}}" + result['invalids'];
                            var duplicates = "{{_("Duplicate recipients: ")|escapejs}}" + result['duplicates'];
                            webix.confirm({
                                title: "{{ _('Confirmation')|escapejs }}",
                                text: valids + "<br />" + invalids + "<br />" + duplicates + "<br /><br />" + "{{_("Are you sure to send this message?")|escapejs}}",
                                ok: "{{_("Yes")|escapejs}}",
                                cancel: "{{_("No")|escapejs}}",
                                callback: function (result) {
                                    if (result) {
                                        $$('{{webix_container_id}}').showOverlay("<img src='{% static 'django_webix/loading.gif' %}'>");
                                        data.append('presend', false);
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
                                                $$('{{webix_container_id}}').hideOverlay();
                                                webix.message({
                                                    type: "info",
                                                    expire: 10000,
                                                    text: "{{_("The messages have been sent")|escapejs}}"
                                                });
                                                sender_window.destructor();
                                            },
                                            error: function () {
                                                $$('{{webix_container_id}}').hideOverlay();
                                                webix.message({
                                                    type: "error",
                                                    expire: 10000,
                                                    text: '{{_("Unable to send messages")|escapejs}}'
                                                });
                                            }
                                        });
                                    }
                                }
                            });
                        },
                        error: function () {
                            $$('{{webix_container_id}}').hideOverlay();
                            webix.message({
                                type: "error",
                                expire: 10000,
                                text: '{{_("Unable to send messages")|escapejs}}'
                            });
                        }
                    });
                }
            }
        });

        return elements;
    }

    /**
     * Return form rules
     *
     * @param send_method
     * @returns dictionary
     */
    var get_rules = function (send_method) {
        var rules = {
            {% if typology_model.enabled and typology_model.required %}
                "typology": webix.rules.isNotEmpty,
            {% endif %}
            "body": webix.rules.isNotEmpty
        };

        if (send_method === 'email') {
            rules['subject'] = webix.rules.isNotEmpty
        }

        return rules;
    }

    /**
     * Create webix window form
     *
     * @param send_method
     * @param recipients
     * @param default_text
     * @returns {webix.ui.baseview | webix.ui}
     */
    var create_window = function (send_method, recipients, default_text) {
        var send_method_original = send_method;
        send_method = send_method_original.split(".")[0];
        var title = '';
        if (send_method === 'email') {
            title = "{{_("Send email")|escapejs}}";
        }
        else if (send_method === 'sms') {
            title = "{{_("Send SMS")|escapejs}}";
        }

        return new webix.ui({
            view: "window",
            id: "django-webix-sender",
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
                        label: title
                    },
                    {
                        view: "button",
                        label: '{{_("Close")|escapejs}}',
                        width: 100,
                        align: 'right',
                        click: "$$('django-webix-sender').destructor();"
                    }
                ]
            },
            body: {
                rows: [{
                    view: 'form',
                    id: 'django-webix-sender-form',
                    padding: 10,
                    elements: get_elements(send_method, send_method_original, recipients, default_text),
                    rules: get_rules(send_method)
                }]
            }
        });
    }

    /**
     * Open django webix sender window
     *
     * @param send_methods
     * @param recipients
     * @param default_text
     */
    this.open = function (send_methods, recipients, default_text) {
        var total = 0;
        Object.keys(recipients).forEach(function (key) {
            total += recipients[key].length
        });

        if (total == 0) {
            webix.alert({
                title: "{{_("Caution!")|escapejs}}",
                text: "{{_("There are no recipients for this communication")|escapejs}}",
                callback: function () {
                    check_recipients_count(send_methods, recipients, default_text);
                }
            });
        } else {
            check_recipients_count(send_methods, recipients, default_text);
        }
    }
}
