let support = {
    vars: {
        append: function(obj) {
            $.each(obj, function(key, value) {
                if (key !== 'append') support.vars[key] = value;
            });
        },
        ready: false,
    },
    config: {
        urls: {
            api: {
                update: '/api/update',
                chats: {
                    list: '/api/chats/list',
                    dialogs: '/api/chats/dialogs',
                    info: '/api/chats/{%s}/info',
                    assignment: '/api/chats/{%s}/assignment',
                    messages: {
                        index: '/api/chats/{%s}/messages/',
                        before: '/api/chats/{%s}/messages/before/',
                        after: '/api/chats/{%s}/messages/after/',
                    },
                    queue: '/api/chats/{%s}/queue',
                    status: '/api/chats/{%s}/status',
                },
                users: {
                    finder: '/api/users/finder',
                    info: '/api/users/{%s}/info',
                    extra: '/api/users/{%s}/extra',
                    comments: '/api/users/{%s}/comments',
                    block: '/api/users/{%s}/block',
                },
                staff: {
                    meta: '/api/staff/meta',
                    list: '/api/staff/list',
                    info: '/api/staff/{%s}/info',
                    password: '/api/staff/{%s}/password',
                    block: '/api/staff/{%s}/block',
                },
                settings: {
                    list: '/api/settings/list',
                    info: '/api/settings/{%s}',
                },
                queue: {
                    list: '/api/queue/list',
                    assign: '/api/queue/assign',
                },
                lines: {
                    list: '/api/lines/list',
                    info: '/api/lines/{%s}',
                },
                files: '/api/files/'
            },
            chat: {
                default_value: '/chat/',
                build_value: '/chat/{%s}',
            },
            queue: {
                default_value: '/queue/',
                build_value: '/queue/{%s}',
            },
            build: (url, x=false) => {
                if (x) url = url.replace('{%s}', x)
                return url;
            }
        },
        methods: {
            get: 'get',
            post: 'post',
            delete: 'delete'
        }
    },
    request: function({method, url, data, success_callback, error_callback}) {
        $.ajax({
            url: url,
            type: method,
            headers: {
                'X-CSRFToken': support.vars.csrf_token
            },
            data: data,
            processData: method == support.config.methods.post ? false : true,
            contentType: method == support.config.methods.post ? false : null,
            success: success_callback,
            error: error_callback
        });
    },
    fileUploadRequest({url, data, success_callback, error_callback}) {
        $.ajax({
            url: url,
            type: support.config.methods.post,
            headers: {
                'X-CSRFToken': support.vars.csrf_token
            },
            data: data,
            processData: false,
            contentType: false,
            success: success_callback,
            error: error_callback,
        });
    },
    compatibilityCheck: function(checking_object, expected_type, silent=false) {
        let result = (typeof checking_object === expected_type);
        if (!silent && !result) {
            // TODO add compatibility error message
        }
        return result;
    },
    checkRequiredProperties: function(obj, required_properties) {
        if (!Array.isArray(required_properties)) return false;

        required_properties.forEach((property) => {
            if (typeof(property) === 'object') {
                for (var prop_key in property) {
                    if (Object.prototype.hasOwnProperty.call(property, prop_key)) {
                        if (!obj.hasOwnProperty(prop_key) || !support.checkRequiredProperties(obj[prop_key], property[prop_key])) {
                            return false;
                        }
                    }
                }
            } else {
                if (!obj.hasOwnProperty(property)) return false;
            }
        });

        return true;
    },
    parseFormData: function(form) {
        if (!support.compatibilityCheck(FormData, 'function'))
            return false;

        return new FormData(form);
    },
    sendForm: function(form, success_callback, error_callback) {
        let formData = support.parseFormData(form);
        // TODO add error message popup
        if (formData === false) return;

        let method = $(form).attr('method').toLowerCase();
        if (method == 'delete') formData = {};

        let url = form.action;
        form.reset();
        support.request({
            method: method,
            url: url,
            data: formData,
            success_callback: success_callback,
            error_callback: error_callback,
        });
    },
    setFormHandler: function({form, url, method, success_callback, error_callback}) {
        form.action = url;
        form.method = method;
        $(form).off('submit').on('submit', (event) => {
            event.preventDefault();
            support.sendForm(form, success_callback, error_callback);
        });
    },
    user: {
        getInfo: function(client_id, callback) {
            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.users.info, client_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['user']}])) {
                        let user = data.response.user;
                        callback(user);
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        getExtra: function(client_id, callback) {
            if (client_id === null) {
                return;
            }

            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.users.extra, client_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['comments', 'known_names']}])) {
                        let comments = data.response.comments;
                        let known_names = data.response.known_names;
                        callback({
                            comments: comments,
                            known_names: known_names,
                        });
                    }
                    callback(data);
                },
                error_callback: support.defaultErrorCallback,
            });
        },
    },
    chat: {
        bindForms: function() {
            support.setFormHandler({
                form: $("#message_form").get(0),
                url: support.config.urls.build(support.config.urls.api.chats.messages.index, support.vars.current_chat),
                method: support.config.methods.post,
                success_callback: support.chat.messageSendSuccessCallback,
                error_callback: support.defaultErrorCallback
                });
            support.setFormHandler({
                form: $("#user_block")[0],
                url: support.config.urls.build(support.config.urls.api.users.block, support.vars.chats[support.vars.current_chat].client.id),
                method: support.vars.chats[support.vars.current_chat].client.is_blocked ? support.config.methods.delete : support.config.methods.post,
                success_callback: (data, textStatus, jqXHR) => {

                    let actions = {
                        block: {
                            text: 'Пользователь заблокирован',
                            button: 'Разблокировать',
                        },
                        unblock: {
                            text: 'Пользователь разблокирован',
                            button: 'Заблокировать',
                        },
                    };

                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['is_blocked']}])) {
                        support.vars.chats[support.vars.current_chat].client.is_blocked = data.response.is_blocked;

                        let action = support.vars.chats[support.vars.current_chat].client.is_blocked ? 'block' : 'unblock';

                        $("#user_block").find('button').html(actions[action].button);

                        support.makeSuccessToast({
                            text: actions[action].text,
                            small_text: null,
                        });
                    } else {
                        support.makeErrorToast({
                            text: 'Ошибка ответа сервера',
                            small_text: null,
                        });
                    }
                },
                error_callback: support.defaultErrorCallback
            });
            support.setFormHandler({
                form: $("#comments_form").get(0),
                url: support.config.urls.build(support.config.urls.api.users.comments, support.vars.current_chat),
                method: support.config.methods.post,
                success_callback: support.chat.commentSendSuccessCallback,
                error_callback: support.defaultErrorCallback
            });
        },
        bindDialogsList: function() {
            $('.message-box').on('click', (event) => {
                let selectedElement = $( event.currentTarget );
                selectedElement.addClass('bg-light');

                let chat_id = parseInt(selectedElement.attr('data-chat-id'));
                let client_id = support.vars.chats[chat_id].client.id;

                if (chat_id != support.vars.current_chat) {
                    support.chat.pushState(chat_id, client_id);
                }

                support.chat.select(chat_id, client_id);
            });
        },
        repaintDialogs: function() {
            let dialog_list = $('.dialogs-list').html('');
            let template = $('.chat__templates .message-box');
            Object.values(support.vars.chats).sort((a, b) => {
                // for inverse order by timestamp
                return a.last_action < b.last_action;
            }).forEach((chat) => {
                if (chat.assignee === null || chat.assignee.id !== support.vars.current_staff) return;

                let base = template.clone();
                base.attr({'data-chat-id': chat.id});
                if (chat.id === support.vars.current_chat) {
                    base.addClass(base.attr('data-current-chat-class'));
                } else {
                    base.removeClass(base.attr('data-current-chat-class'));
                }

                // username
                base.find('.message-box__username').html(chat.client.full_name);
                // user avatar
                base.find('.message-box__user-avatar').attr({'src': chat.client.avatar})
                // last action
                base.find('.message-box__time').html(chat.last_action_str);
                // message
                let message_container = base.find('.message-box__message-data');
                if (chat.last_readable_message.is_from_client) {
                    message_container.removeClass(message_container.attr('data-staff-class'));
                    message_container.addClass(message_container.attr('data-client-class'));
                } else {
                    message_container.addClass(message_container.attr('data-staff-class'));
                    message_container.removeClass(message_container.attr('data-client-class'));
                }

                if (chat.last_readable_message.text !== null) {
                    base.find('.message-box__message-text').html(chat.last_readable_message.text);
                }

                // badge
                let chat_msg_info = support.storage.chats.get(chat.id);
                if (chat_msg_info !== null) {
                    support.chat.setDialogBadge(base, chat_msg_info.unread);
                }

                dialog_list.append(base);
            });

            support.chat.bindDialogsList();
        },
        setDialogBadge: function(chat, size) {
            // chat: int (chat id) or jQuery Element
            if (typeof chat === 'number') {
                chat = $('.message-box[data-chat-id=' + chat + ']')
            }

            if (typeof chat !== 'object' || chat.length === undefined || chat.length === 0) return;

            if (size > 0) {
                chat.find('.message-box__message-badge').html(size).removeClass('d-none');
            } else {
                chat.find('.message-box__message-badge').html('').addClass('d-none')
            }
        },
        updateChatInfo: function(chat) {
            $('.chat-box__controls').removeClass('d-none');

            let assign_button = $('.chat-box__control-assign');
            let unassign_button = $('.chat-box__control-unassign');
            if (chat.assignee === null || chat.assignee.id != support.vars.current_staff) {
                assign_button.removeClass('d-none');
                unassign_button.addClass('d-none');
            } else {
                assign_button.addClass('d-none');
                unassign_button.removeClass('d-none');
            }

            let open_button = $('.chat-box__control-open');
            let close_button = $('.chat-box__control-close');
            if (chat.status == 'closed') {
                open_button.removeClass('d-none');
                close_button.addClass('d-none');
            } else {
                open_button.addClass('d-none');
                close_button.removeClass('d-none');
            }

            // Line assign button
            let select_element = $('.chat-box__control-queue');
            let option_element = select_element.find('option[data-line-id=' + support.vars.chats[support.vars.current_chat].line.id + ']')
            if (option_element.length == 0)
                location.reload();

            option_element.prop('selected', true);

            support.chat.printUserInfo(chat.client);
        },
        getInfo: function(chat_id, callback) {
            if (chat_id === null) return;

            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.chats.info, chat_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['chat']}])) {
                        let chat = data.response.chat;
                        callback(chat);
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        loadPreviousMessages: function(callback) {
            if (support.vars.is_message_loading_locked) return;

            support.vars.is_message_loading_locked = true;

            let chat_id = support.vars.current_chat;
            if (chat_id === null) return;

            let progress_bar = $('.chat-box__progress').removeClass('d-none');

            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.chats.messages.before, chat_id) + (support.vars.scroll_message_back || ''),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    if (chat_id !== support.vars.current_chat) return;

                    data = JSON.parse(data);
                    if (!support.checkRequiredProperties(data, [{'response': ['messages', 'first_message', 'last_message']}])) return;

                    let chatbox = $('.chat-box__messages');
                    let first_child = chatbox.first()[0];

                    support.chat.keepPosition(first_child);
                    chatbox.prepend(data.response.messages);
                    progress_bar.addClass('d-none');

                    support.vars.scroll_message_back = data.response.first_message;
                    if (support.vars.scroll_message_front === null)
                        support.vars.scroll_message_front = data.response.last_message;
                    support.vars.is_message_loading_locked = false;

                    if (callback !== undefined) {
                        callback();
                    }
                },
                error_callback: (jqXHR, textStatus, errorThrown) => {
                    if (jqXHR.status == 410) {
                        // api return code 410 if we tried to get messages before a first one (last)
                        // where are no need to allow further requests
                        support.vars.is_message_loading_locked = true;
                        support.silentErrorCallback(jqXHR, textStatus, errorThrown);
                    } else {
                        support.vars.is_message_loading_locked = false;
                        support.defaultErrorCallback(jqXHR, textStatus, errorThrown);
                    }

                    progress_bar.addClass('d-none');
                },
            });
        },
        loadNextMessages: function(callback) {
            support.vars.is_message_loading_locked = true;

            let chat_id = support.vars.current_chat;
            if (chat_id === null) return;

            let progress_bar = $('.chat-box__progress').removeClass('d-none');

            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.chats.messages.after, chat_id) + (support.vars.scroll_message_front || ''),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    if (chat_id !== support.vars.current_chat) return;

                    data = JSON.parse(data);
                    if (!support.checkRequiredProperties(data, [{'response': ['messages', 'first_message', 'last_message']}])) return;

                    let chatbox = $('.chat-box__messages');

                    chatbox.append(data.response.messages);
                    progress_bar.addClass('d-none');

                    support.vars.scroll_message_front = data.response.last_message;
                    if (support.vars.scroll_message_back === null)
                        support.vars.scroll_message_back = data.response.first_message;
                    support.vars.is_message_loading_locked = false;

                    if (callback !== undefined) {
                        callback();
                    }
                },
                error_callback: (jqXHR, textStatus, errorThrown) => {
                    if (jqXHR.status == 410) {
                        // api return code 410 if we tried to get message after a last one
                        support.silentErrorCallback(jqXHR, textStatus, errorThrown);
                    } else {
                        support.defaultErrorCallback(jqXHR, textStatus, errorThrown);
                    }

                    progress_bar.addClass('d-none');
                },
            });
        },
        repaint: function(full_load) {
            let chat_id = support.vars.current_chat;

            if (chat_id == null) {
                $('.chat-box__messages').html('');
                $('.user-box__wrapper').hide();
                $('.send-form').hide();
                $('.chat-box__controls').addClass('d-none');
            } else {
                let client_id = support.vars.chats[support.vars.current_chat].client.id;
                if (support.vars.chats[chat_id] !== undefined) {
                    support.chat.repaintDialogs();
                    support.chat.bindForms();
                    support.chat.updateChatInfo(support.vars.chats[chat_id]);
                } else {
                    support.chat.getInfo(chat_id, (chat) => {
                        support.vars.chats[chat.id] = chat;
                        support.chat.repaintDialogs();
                        support.chat.bindForms();
                        support.chat.updateChatInfo(support.vars.chats[chat.id]);
                    });
                }

                if (full_load !== undefined && full_load) {
                    support.user.getExtra(client_id, support.chat.printUserExtra);
                    support.update();
                }
            }
        },
        pushState: function(chat_id, client_id) {
            let url = support.config.urls.chat.default_value;
            if (chat_id !== null)
                url = support.config.urls.build(support.config.urls.chat.build_value, chat_id);

            window.history.pushState({
                chat_id: chat_id,
                client_id: client_id,
            },"", url);
        },
        select: function(chat_id, client_id) {
            support.vars.is_scroll_locked = false;

            if (chat_id != support.vars.current_chat) {
                support.vars.current_chat = chat_id;
                support.vars.scroll_message_front = null;
                support.vars.scroll_message_back = null;
                support.vars.is_message_loading_locked = false;
                $('.chat-box__messages').html('');
                if (chat_id !== null) {
                    support.chat.repaint(true);
                    support.chat.loadPreviousMessages(() => {
                        support.chat.scrollDown();
                        support.chat.markRead(chat_id);
                    });
                }
            } else {
                support.chat.repaint();
                support.chat.scrollDown();
                support.chat.markRead(chat_id);
            }

            $('.user-box__wrapper').show();
            $('.send-form').show();
        },
        markRead: function(chat_id) {
            support.markChatRead(chat_id);
            support.markMessagesRead(chat_id);
            support.updateChatsBadge();
        },
        messageSendSuccessCallback: function(data, textStatus, jqXHR) {
            $("#message_form").trigger('reset');
            support.chat.removeAllAttachments();
            support.chat.markRead();
            support.chat.repaint();
        },
        commentSendSuccessCallback: function(data, textStatus, jqXHR) {
            support.user.getComments(support.vars.chats[support.vars.current_chat].client.id, support.chat.printUserExtra);
        },
        printUserInfo: function(user) {
            $('.user-box__base-avatar').attr('src', user.avatar);

            let name = (user.first_name !== null ? user.first_name + ' ' : '') + (user.last_name !== null ? user.last_name : '')
            $('.user-box__base-name').html(name);

            let username_object = $('.user-box__base-username-link')
            if (user.username === null) {
                username_object.html('').attr('href', '').hide();
            } else {
                username_object.html('@' + user.username).attr('href', user.link).show();
            }

            $('.user-box__base-source').html(support.capitalize(user.source) + ' (ID ' + user.uid + ')');
        },
        printUserExtra: function({comments, known_names}) {
            $('.user-box__comments').html(comments);
            $('.user-box__alter-names-list').html(known_names);
        },
        getAttachments: function() {
            let attachments_input = $('.send-form__attachments_input').get(0);
            let attachments_array = [];

            if (attachments_input.value !== '')
                try {
                    attachments_array = JSON.parse(attachments_input.value);
                } catch(e) {
                    console.log(e);
                }
            return attachments_array;
        },
        setAttachments: function(attachments_array) {
            let attachments_input = $('.send-form__attachments_input').get(0);
            attachments_input.value = JSON.stringify(attachments_array)
        },
        removeAttachment: function(data_type, target) {
            support.chat.attachmentsLoading('start');
            let current_element = $(target);

            let needle = null;
            switch (data_type) {
                case 'file':
                    needle = current_element.data('uuid');
                    break;
                case 'location':
                    needle = current_element.data('location');
                    break;
            }

            try {
                let current_list = support.chat.getAttachments();
                current_list = current_list.filter((element, index, array) => {
                    if (data_type == 'file' && element.type == 'file' && element.uuid == needle)
                        return false;
                    if (data_type == 'location' && element.type == 'location' &&
                        [element.latitude, element.longitude, element.title, element.address].join('|') == needle)
                        return false;
                    return true;
                });

                support.chat.setAttachments(current_list);
                current_element.parent('div').remove();
                // TODO send delete request to backend
            } catch (e) {
                console.log(e);
            }
            support.chat.attachmentsLoading('stop');
        },
        removeAllAttachments: function() {
            $('.send-form__attachments').html('');
            support.chat.setAttachments([]);
        },
        attachmentsCallback: function(data_type, attachments) {
            let attachments_container = $('.send-form__attachments');
            let attachments_list = support.chat.getAttachments();

            attachments.forEach((attachment) => {
                let element = $('<div>').addClass('send-form__attachments-item d-flex p-2 me-2 mb-2 rounded-3 border border-secondary');

                if (data_type == 'files') {
                    let file = attachment;
                    attachments_list.push({
                        type: 'file',
                        uuid: file.uuid,
                    });
                    let file_name = $('<div>').addClass('fw-bolder').html(file.file_name);
                    let file_link = $('<a>').attr('href', file.url).attr('target', '_blank').addClass('text-decoration-none text-dark').append(file_name);
                    let file_size = $('<div>').addClass('ms-2 text-secondary').html(file.file_size);
                    let delete_button = $('<span>').addClass('ms-2 material-icons-round selectable').html('clear').data('uuid', file.uuid);
                    delete_button.on('click', (event) => {
                        support.chat.removeAttachment('file', event.target)
                    });

                    element.append(file_link, file_size, delete_button);
                } else if (data_type == 'location') {
                    let loc = attachment;
                    let loc_latitude = loc.latitude !== undefined ? loc.latitude : null;
                    let loc_longitude = loc.longitude !== undefined ? loc.longitude : null;
                    let loc_title = loc.title !== undefined ? loc.title : null;
                    let loc_address = loc.address !== undefined ? loc.address : null;

                    let url = 'https://yandex.ru/maps/?mode=whatshere&whatshere[point]=' + loc_longitude + '%2C' + loc_latitude + '&whatshere[zoom]=15&z=15'

                    let title = $('<div>').addClass('ms-2')
                    if (loc_title !== null)
                        title.addClass('fw-bolder').html(loc_title);
                    else
                        title.addClass('text-secondary').html(loc_latitude + ' ' + loc_longitude );

                    let delete_button = $('<span>').addClass('ms-2 material-icons-round selectable').html('clear');
                    delete_button.data('location', [loc_latitude, loc_longitude, loc_title, loc_address].join('|'));
                    delete_button.on('click', (event) => {
                        support.chat.removeAttachment('location', event.target)
                    });

                    let map_logo = $('<span>').addClass('material-icons-round').html('place');
                    let map_link = $('<a>').attr('href', url).attr('target', '_blank').addClass('text-decoration-none text-dark d-flex').append(map_logo, title);
                    element.append(map_link, delete_button);

                    attachments_list.push({
                        type: 'location',
                        latitude: loc_latitude,
                        longitude: loc_longitude,
                        title: loc_title,
                        address: loc_address,
                    });
                }
                attachments_container.append(element);
            });

            support.chat.setAttachments(attachments_list);
        },
        attachmentsLoading: function(state) {
            let upload_button = $('.send-form__upload-button');
            let upload_spinner = upload_button.children('.spinner-border')
            let upload_clip = upload_button.children('.material-icons-round')
            if (state === 'start') {
                upload_button.prop('disabled', true);
                upload_clip.addClass('d-none');
                upload_spinner.removeClass('d-none');
            } else if (state === 'stop') {
                upload_button.prop('disabled', false);
                upload_spinner.addClass('d-none');
                upload_clip.removeClass('d-none');
            }
        },
        pickupLocationAttachment: function() {
            let iframe_document = $('.map-pickup-modal__iframe').get(0).contentWindow.document;
            let latitude = iframe_document.getElementById('loc_lat').value;
            latitude = latitude != 'null' ? parseFloat(latitude) : null;

            let longitude = iframe_document.getElementById('loc_lon').value;
            longitude = longitude != 'null' ? parseFloat(longitude) : null;

            let title = iframe_document.getElementById('loc_title').value;
            title = title != 'null' && title.length > 0 ? title : null;

            let address = iframe_document.getElementById('loc_address').value;
            address = address != 'null' && address.length > 0 ? address : null;

            support.chat.attachmentsCallback('location', [{
                'latitude': latitude,
                'longitude': longitude,
                'title': title,
                'address': address,
            }])
        },
        setLine: function(line_id) {
            let formData = new FormData();
            formData.append('line', line_id);

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.chats.queue, support.vars.current_chat),
                data: formData,
                success_callback: function(data, textStatus, jqXHR) {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['chat_id', 'line']}])) {
                        let line = data.response.line;
                        let chat = data.response.chat;
                        support.makeSuccessToast({
                            text: 'Очередь для обращения изменена',
                            small_text: 'Обращение переведено в очередь \"' + line.name + '\"',
                        })
                        support.chat.repaint(true);
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        assign: function() {
            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.chats.assignment, support.vars.current_chat),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    support.chat.repaint(true);
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        unassign: function() {
            support.request({
                method: support.config.methods.delete,
                url: support.config.urls.build(support.config.urls.api.chats.assignment, support.vars.current_chat),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    support.chat.repaint(true);
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        closeChat: function() {
            support.request({
                method: support.config.methods.delete,
                url: support.config.urls.build(support.config.urls.api.chats.status, support.vars.current_chat),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    support.chat.repaint(true);
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        openChat: function() {
            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.chats.status, support.vars.current_chat),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    support.chat.repaint(true);
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        getCurrentChat: function() {
            let current_chat = support.vars.current_chat;
            if (current_chat === null) return null;
            return support.vars.chats[current_chat];
        },
        isCurrentChatAssigned: function() {
            let current_chat = support.vars.current_chat;
            if (current_chat === null || support.vars.chats[current_chat].assignee === null ||
                support.vars.chats[current_chat] !== support.vars.staff_user) return false;

            return true;
        },
        receiveUpdate: function(chats, deleted_chats) {
            let chats_with_updates = [];
            chats.forEach((chat) => {

                // copy object
                let chat_obj = JSON.parse(JSON.stringify(chat));
                // remove system fields
                ['updates', 'count'].forEach((property) => {
                    delete chat_obj[property];
                });
                support.vars.chats[chat.id] = chat_obj;

                if (chat.count > 0) {
                    chats_with_updates.push(chat.id);

                    if (chat.id === support.vars.current_chat) {
                        support.chat.loadNextMessages();
                        support.chat.repaint();
                    }
                }
            });

            deleted_chats.forEach((chat_id) => {
                if (chat_id === support.vars.current_chat) return;

                support.chat.markRead(chat_id);
                delete support.vars.chats[chat_id];
            });

            if (chats_with_updates.length > 0 || deleted_chats.length > 0) {
                support.chat.repaintDialogs();
            }
        },
        scrollDown: function() {
            let chatbox_messages = $('.chat-box__messages')[0];

            if (support.vars.observers.scroll_down === null) {
                support.vars.observers.scroll_down = new ResizeObserver(entries => {
                    for (let entry of entries) {
                        if (!support.vars.is_scroll_locked)
                            support.scrollToBottom(chatbox_messages);
                    }
                });
            }
            // first scroll (fix for moments, when size of chat-box__messages doesn't change
            support.scrollToBottom(chatbox_messages);
            support.vars.observers.scroll_down.observe(chatbox_messages);
        },
        stopScroll: function() {
            if (support.vars.observers.scroll_down !== null)
                support.vars.observers.scroll_down.unobserve($('.chat-box__messages')[0]);
        },
        keepPosition: function(follow_element) {
            let chatbox_messages = $('.chat-box__messages')[0];

            support.vars.observers.scroll_up = new ResizeObserver(entries => {
                for (let entry of entries) {
                    if (!support.vars.is_scroll_locked)
                        support.scrollToTop(follow_element);
                }
            });

            // first scroll (fix for moments, when size of chat-box__messages doesn't change
            support.scrollToTop(follow_element);
            support.vars.observers.scroll_down.observe(chatbox_messages);
        },
        freePosition: function() {
            if (support.vars.observers.scroll_up !== null)
                support.vars.observers.scroll_up.unobserve($('.chat-box__messages')[0]);
        },
    },
    queue: {
        auto_assign: function(callback=null) {
            support.request({
                method: support.config.methods.post,
                url: support.config.urls.api.queue.assign,
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['chat_id', 'current_chats']}])) {
                        let assigned_chat = data.response.chat_id;
                        let current_chats = data.response.current_chats;
                        if (callback !== null && assigned_chat !== null) callback(assigned_chat, current_chats);
                    }
                },
                error_callback: support.defaultErrorCallback,
            })
        },
        assign: function(chat_id, callback=null) {
            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.chats.assignment, chat_id),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['chat_id', 'current_chats']}])) {
                        let assigned_chat = data.response.chat_id;
                        let current_chats = data.response.current_chats;
                        if (callback !== null && assigned_chat !== null) callback(assigned_chat, current_chats);
                    }
                },
                error_callback: support.defaultErrorCallback,
            })
        }
    },
    files: {
        uploadWrapper: function(event) {
            let button = $(event.target)
            let wrapper = button.data('target');

            if (wrapper === undefined || button.prop('disabled') === true) return;

            $(wrapper).click();
        },
        upload: function({input, loading, callback}) {
            if (!support.compatibilityCheck(FormData, 'function'))
                return false;

            loading('start');

            let data = new FormData()
            $.each(input.files, (i, file) => {
                data.append(input.name, file);
            });

            let url = support.config.urls.api.files;
            let method = support.config.methods.post;

            support.fileUploadRequest({
                method: method,
                url: url,
                data: data,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['files']}])) {
                        files = data.response.files;
                        callback(files);
                        loading('stop');
                    }
                },
                error_callback: (jqXHR, textStatus, errorThrown) => {
                    loading('stop');
                    support.defaultErrorCallback(jqXHR, textStatus, errorThrown);
                },
            })

        },
    },
    settings: {
        getAvailableTypes: function() {
            return ['string', 'bool', 'int', 'datetime'];
        },
        getIconByType: function(setting_type) {
            switch(setting_type) {
                case 'bool':
                    return 'flaky';
                    break;
                case 'int':
                    return 'pin';
                    break;
                case 'datetime':
                    return 'event';
                    break;
                default:
                    return 'keyboard';
                    break;
            }
        },
        createInputGroup: function({value_type, value, readonly, input_name, left_icon, left_id, description, print_type}) {
            let input_group = $('<div>').addClass('input-group mb-3');
            let left_text = $('<div>').addClass('input-group-text').attr('id', left_id).append(
                $('<span>').addClass('material-icons-round').html(left_icon)
            );

            input_group.append(left_text);
            let input;

            if (value_type == 'bool') {
                input = $('<select>').addClass('form-select').attr({
                    name: input_name,
                    'aria-label': description,
                    'aria-describedby': '#' + left_id,
                });

                if (readonly) input.attr('disabled', 'disabled');

                let false_val = $('<option>').val('0').html('false');
                let true_val = $('<option>').val('1').html('true');

                if (value) {
                    true_val.attr('selected', 'selected');
                } else {
                    false_val.attr('selected', 'selected');
                }

                input.append(false_val, true_val);
            } else {
                input = $('<input>').addClass('form-control').attr({
                    type: 'text',
                    name: input_name,
                    placeholder: description,
                    'aria-label': description,
                    'aria-describedby': '#' + left_id,
                }).val(value);

                if (readonly) input.attr('readonly', 'readonly');
            }

            input_group.append(input);

            if (print_type) {
                let right_text = $('<div>').addClass('input-group-text px-2').append(
                    $('<span>').addClass('small border border-secondary rounded bg-light p-1').html(value_type)
                );

                input_group.append(right_text);
            }

            return input_group;
        },
        buildForm: function(setting) {
            let modal = $('#settingEditModal');
            let form = $('#settingEditForm');
            form.empty();

            form.append(support.settings.createInputGroup({
                value_type: 'string',
                value: setting.key,
                readonly: setting.is_system,
                input_name: 'key',
                left_icon: 'settings',
                left_id: 'settingEditKeyAddon',
                description: 'Имя параметра',
                print_type: false,
            }));

            form.append(support.settings.createInputGroup({
                value_type: setting.type,
                value: setting.value,
                readonly: false,
                input_name: 'value',
                left_icon: support.settings.getIconByType(setting.type),
                left_id: 'settingEditValueAddon',
                description: 'Значение',
                print_type: true,
            }));

            let setting_description = setting.description;
            if (setting.description === null || setting.description === '') {
                setting_description = '<i>Пустое описание</i>'
            }

            form.append( $('<div>').addClass('p-3 border').html(setting_description) );
            form.append( $('<input>').attr({
                name: 'id',
                type: 'hidden',
            }).val(setting.id));

            modal.modal('show');
        },
        showDeleteModal: function(setting) {
            let modal = $('#settingDeleteModal');
            modal.data('id', setting.id);
            modal.find('#settingDeleteKey').html(setting.key);
            modal.modal('show');
        },
        getSetting: function({setting_id, success_callback, error_callback}) {
            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.settings.info, setting_id),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['setting']}])) {
                        success_callback(data.response.setting);
                    }
                },
                error_callback: error_callback,
            });
        },
        loadEditModal: function(setting_id) {
            support.settings.getSetting({
                setting_id: setting_id,
                success_callback: support.settings.buildForm,
                error_callback: support.defaultErrorCallback,
            });
        },
        loadDeleteModal: function(setting_id) {
            support.settings.getSetting({
                setting_id: setting_id,
                success_callback: support.settings.showDeleteModal,
                error_callback: support.defaultErrorCallback,
            });
        },
        showCreateModal: function() {
            let modal = $('.setting-create-modal');
            let base_div = modal.find('.setting-create-modal__form-base').empty();
            let value_div = modal.find('.setting-create-modal__form-value').empty();

            let select_options = [];
            support.settings.getAvailableTypes().forEach((element) => {
                select_options.push(
                    $('<option>').attr({
                        value: element,
                    }).html(element)
                )
            });

            let type_select = $('<select>').addClass('form-select flex-grow-0 w-auto').attr({'name': 'type'}).append(
                select_options
            ).on('input', (event) => {
                value_div.empty();
                let value_type = event.target.value;

                value_div.append(
                    support.settings.createInputGroup({
                        value_type: value_type,
                        value: '',
                        readonly: false,
                        input_name: 'value',
                        left_icon: support.settings.getIconByType(value_type),
                        left_id: 'settingCreateValueAddon',
                        description: 'Значение',
                        print_type: true,
                    })
                );
            });

            let base_key_field = support.settings.createInputGroup({
                value_type: 'string',
                value: '',
                readonly: false,
                input_name: 'key',
                left_icon: 'settings',
                left_id: 'settingCreateKeyAddon',
                description: 'Имя параметра',
                print_type: false,
            }).append(type_select);

            let base_key_input = base_key_field.find('input');
            let warning_popover = new bootstrap.Popover(base_key_input[0], {
                animation: true,
                placement: 'top',
                title: 'Использование имени <code>system</code>',
                content: 'Создание параметра с именем, начинающимся с <code>system.</code>, делает его системным. ' +
                         'Из-за этого его удалние в дальнейшем может быть затруднено: системные параметры нельзя удалить.',
                html: true,
                trigger: 'manual',
            });
            warning_popover.hide();
            base_key_input.on('keyup focus', (event) => {
                if (base_key_input[0].value.indexOf('system.') == 0) {
                    warning_popover.show();
                } else {
                    warning_popover.hide();
                }
            }).on('blur', (event) => {
                warning_popover.hide();
            });

            let base_description_field = support.settings.createInputGroup({
                value_type: 'string',
                value: '',
                readonly: false,
                input_name: 'description',
                left_icon: 'description',
                left_id: 'settingCreateDescriptionAddon',
                description: 'Описание',
                print_type: false,
            });

            base_div.append(
                base_key_field,
                base_description_field,
            );

            type_select.trigger('input');
            modal.modal('show');
        },
        saveSetting: function() {
            let form = $('#settingEditForm')[0];
            let formData = support.parseFormData(form);
            let setting_id = formData.get('id');

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.settings.info, setting_id),
                data: formData,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['setting']}])) {
                        let setting = data.response.setting;
                        let modal = $('.setting-edit-modal');
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Параметр успешно сохранён.',
                            small_text: null,
                        });

                        let setting_container = $('.setting-entity__container[data-setting-id=\'' + setting.id + '\']');
                        let setting_key_el = setting_container.find('.setting-entity__name');
                        let setting_value_el = setting_container.find('.setting-entity__value');

                        setting_key_el.html(setting.key);
                        setting_value_el.html(setting.value.toString());
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        createSetting: function() {
            let form = $('#settingCreateForm')[0];
            let formData = support.parseFormData(form);

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.api.settings.list,
                data: formData,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['setting']}])) {
                        let setting = data.response.setting;
                        let modal = $('.setting-create-modal');
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Параметр успешно создан.',
                            small_text: null,
                        });

                        // TODO reload
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        deleteSetting: function() {
            let modal = $('#settingDeleteModal');
            let setting_id = modal.data('id');

            support.request({
                method: support.config.methods.delete,
                url: support.config.urls.build(support.config.urls.api.settings.info, setting_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, ['response'])) {
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Параметр успешно удалён.',
                            small_text: null,
                        });
                        // TODO reload data
                    }
                },
                error_callback: (jqXHR, textStatus, errorThrown) => {
                    modal.modal('hide');
                    support.defaultErrorCallback(jqXHR, textStatus, errorThrown);
                },
            });
        },
    },
    staff: {
        getMeta: function({lines_callback, roles_callback, error_callback}) {
            support.request({
                method: support.config.methods.get,
                url: support.config.urls.api.staff.meta,
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, ['response'])) {
                        if (lines_callback !== null) lines_callback(data.response.lines);
                        if (roles_callback !== null) roles_callback(data.response.roles);
                    }
                },
                error_callback: error_callback,
            });
        },
        generateSelect: function(elements, name, description) {
            let input_group = $('<div>').addClass('input-group mb-3');

            let description_element = $('<div>').addClass('input-group-text').html(description);
            let select_element = $('<select>').addClass('form-select').attr({
                'name': name,
                'aria-label': description,
            });

            let options = [];
            let has_selected = false;
            elements.forEach((element) => {

                let option_element = $('<option>').val(element.value).html(element.text);
                if (element.selected !== undefined) {
                    option_element.attr({'selected': 'selected'});
                    has_selected = true;
                }

                if (!has_selected && element.length > 0) options[0].attr({'selected': 'selected'})

                options.push(option_element);
            });

            select_element.append(options);
            input_group.append(description_element, select_element);
            return input_group;
        },
        generateLineSelect: function(lines, target) {
            let converted_lines = [];
            lines.forEach((element) => {
                converted_lines.push({
                    'value': element.id,
                    'text': element.name,
                })
            });
            target.append(support.staff.generateSelect(converted_lines, 'line', 'Линия'));
        },
        generateRoleSelect: function(roles, target) {
            let converted_roles = [];
            roles.forEach((element) => {
                converted_roles.push({
                    'value': element,
                    'text': element,
                })
            });
            target.append(support.staff.generateSelect(converted_roles, 'role', 'Роль'));
        },
        getUser: function({user_id, success_callback, error_callback}) {
            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.staff.info, user_id),
                data: {},
                success_callback: function(data, textStatus, jqXHR) {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['user']}])) {
                        success_callback(data.response.user);
                    }
                },
                error_callback: error_callback,
            });
        },
        loadEditModal: function(user_id) {
            support.staff.getUser({
                user_id: user_id,
                success_callback: (user) => {
                    let modal = $('.user-edit-modal');

                    modal.find('#editFirstName').val(user.first_name);
                    modal.find('#editLastName').val(user.last_name);
                    modal.find('#editUsername').val(user.username);
                    modal.find('#editEmail').val(user.email);

                    modal.find('#editId').val(user_id);

                    modal.find('#editResetPassword').data('user-id', user.id);

                    let block_button = modal.find('#editBlock').data('user-id', user.id);
                    let unblock_button = modal.find('#editUnblock').data('user-id', user.id);

                    if (user.is_blocked) {
                        block_button.hide();
                        unblock_button.show();
                    } else {
                        block_button.show();
                        unblock_button.hide();
                    }

                    modal.modal('show');
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        loadCreateModal: function() {
            let modal = $('.user-create-modal');
            let form = modal.find('form');
            form[0].reset();

            let dynamic_fields = form.find('.dynamic-fields');
            dynamic_fields.empty();

            support.staff.getMeta({
                lines_callback: (lines) => {
                    support.staff.generateLineSelect(lines, dynamic_fields);
                },
                roles_callback: (roles) => {
                    support.staff.generateRoleSelect(roles, dynamic_fields);
                },
                error_callback: support.defaultErrorCallback,
            });

            modal.modal('show');
        },
        saveUser: function() {
            let modal = $('.user-edit-modal');
            let form = modal.find('form')[0];
            let formData = support.parseFormData(form);
            let user_id = modal.find('#editId').val();

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.staff.info, user_id),
                data: formData,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['user']}])) {
                        let user = data.response.user;
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Пользователь успешно изменён',
                            small_text: null,
                        });

                        // TODO reload
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        createUser: function() {
            let modal = $('.user-create-modal');
            let form = modal.find('form');
            let formData = support.parseFormData(form[0]);

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.api.staff.list,
                data: formData,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['user']}])) {
                        let user = data.response.user;
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Пользователь успешно создан',
                            small_text: 'Пароль отправлен на почту, указанную для этого пользователя',
                        });

                        // TODO reload
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        blockUser: function(action) {
            let modal = $('.user-edit-modal');
            let block_button = modal.find('#editBlock');
            let unblock_button = modal.find('#editUnblock');

            let method, toast_message, user_id;
            if (action == 'block') {
                method = support.config.methods.post;
                toast_message = 'Пользователь заблокирован';
                user_id = block_button.data('user-id');
            } else if (action == 'unblock') {
                method = support.config.methods.delete;
                toast_message = 'Пользователь разблокирован';
                user_id = unblock_button.data('user-id');
            } else {
                return;
            }

            support.request({
                method: method,
                url: support.config.urls.build(support.config.urls.api.staff.block, user_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['user']}])) {
                        let user = data.response.user;

                        if (action == 'block') {
                            block_button.hide();
                            unblock_button.show();
                        } else {
                            block_button.show();
                            unblock_button.hide();
                        }

                        support.makeSuccessToast({
                            text: toast_message,
                            small_text: null,
                        });
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        resetPassword: function() {
            let modal = $('.user-edit-modal');
            let user_id = modal.find('#editId').val();

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.staff.password, user_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['user']}])) {
                        let user = data.response.user;

                        support.makeSuccessToast({
                            text: 'Пароль успешно сброшен',
                            small_text: 'На почту пользователя отправлен новый пароль',
                        });
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
    },
    lines: {
        getLine: function({line_id, success_callback, error_callback}) {
            support.request({
                method: support.config.methods.get,
                url: support.config.urls.build(support.config.urls.api.lines.info, line_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['line']}])) {
                        let line = data.response.line;
                        success_callback(line);
                    }
                },
                error_callback: error_callback,
            });
        },
        loadEditModal: function(line_id) {
            support.lines.getLine({
                line_id: line_id,
                success_callback: (line) => {
                    let modal = $('.line-edit-modal');

                    modal.find('#editName').val(line.name);
                    modal.find('#editDescription').val(line.description);
                    modal.find('.line-id').val(line.id);

                    modal.modal('show');
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        saveLine: function() {
            let modal = $('.line-edit-modal');
            let form = modal.find('form');
            let line_id = modal.find('.line-id').val();
            let formData = support.parseFormData(form[0]);

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.build(support.config.urls.api.lines.info, line_id),
                data: formData,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['line']}])) {
                        let line = data.response.line;
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Очередь изменена',
                            small_text: null,
                        });

                        let line_entity = $('.lines-entity[data-line-id=\'' + line.id + '\']');
                        let line_name_el = line_entity.find('.lines-entity__name');
                        let line_description_el = line_entity.find('.lines-entity__description');

                        line_name_el.html(line.name);
                        line_description_el.html(line.description);
                        // TODO escape HTML
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        loadCreateModal: function() {
            let modal = $('.line-create-modal');
            let form = modal.find('#lineCreateForm');
            form[0].reset();
            modal.modal('show');
        },
        createLine: function() {
            let modal = $('.line-create-modal');
            let form = modal.find('form');
            let formData = support.parseFormData(form[0]);

            support.request({
                method: support.config.methods.post,
                url: support.config.urls.api.lines.list,
                data: formData,
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, [{'response': ['line']}])) {
                        let line = data.response.line;
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Очередь создана',
                            small_text: null,
                        });

                        // TODO reload
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        loadDeleteModal: function(line_id) {
            support.lines.getLine({
                line_id: line_id,
                success_callback: (line) => {
                    let modal = $('.line-delete-modal');
                    let line_name = modal.find('#lineDeleteName');
                    let delete_button = modal.find('.line-delete-modal__delete');

                    delete_button.data('line-id', line.id);
                    line_name.html(line.name);

                    modal.modal('show');
                },
                error_callback: support.defaultErrorCallback,
            });
        },
        deleteLine: function(line_id) {
            support.request({
                method: support.config.methods.delete,
                url: support.config.urls.build(support.config.urls.api.lines.info, line_id),
                data: {},
                success_callback: (data, textStatus, jqXHR) => {
                    data = JSON.parse(data);
                    if (support.checkRequiredProperties(data, ['response'])) {
                        let modal = $('.line-delete-modal');
                        modal.modal('hide');

                        support.makeSuccessToast({
                            text: 'Очередь удалена',
                            small_text: 'Обращения перенесены на очередь по-умолчанию',
                        });
                    }
                },
                error_callback: support.defaultErrorCallback,
            });
        },
    },
    storage: {
        get: function(key) {
            return window.localStorage.getItem(key);
        },
        set: function(key, value) {
            window.localStorage.setItem(key, value);
        },
        remove: function(key) {
            window.localStorage.removeItem(key);
        },
        clear: function() {
            window.localStorage.clear();
        },
        chats: {
            prefix: 'chats_',
            list: {
                name: 'chats_list',
                get: function() {
                    let result = support.storage.chats.get(support.storage.chats.list.name);
                    if (result !== null)
                        return result;

                    return [];
                },
                set: function(value) {
                    support.storage.chats.set(support.storage.chats.list.name, value);
                },
                append: function(chat_id) {
                    if (!support.storage.chats.list.exists(chat_id)) {
                        let current = support.storage.chats.list.get();
                        current.push(chat_id);
                        support.storage.chats.list.set(current);
                    }
                },
                remove: function(chat_id) {
                    let pos = support.storage.chats.list.find(chat_id)
                    if (pos !== -1) {
                        let current = support.storage.chats.list.get();
                        current.splice(pos, 1);
                        support.storage.chats.list.set(current);
                    }
                },
                find: function(chat_id) {
                    return support.storage.chats.list.get().indexOf(chat_id);
                },
                exists: function(chat_id) {
                    if (support.storage.chats.list.find(chat_id) == -1)
                        return false;
                    else
                        return true;
                },
            },
            get: function(key) {
                let result = support.storage.get(support.storage.chats.prefix + key);
                if (result !== null)
                    return JSON.parse(result);

                return null;
            },
            set: function(key, value) {
                if (value !== null) value = JSON.stringify(value);
                support.storage.set(support.storage.chats.prefix + key, value);
            },
            remove: function(key) {
                support.storage.remove(support.storage.chats.prefix + key);
            },
            clear: function() {
                for (var i = 0; i < window.localStorage.length; i++) {
                    let key = window.localStorage.key(i);
                    if (key.indexOf(support.storage.chats.prefix) == 0)
                        support.storage.chats.remove(key);
                }
            },
        }
    },
    update: function() {
        let formData = new FormData();

        let stored_chats = {};

        support.storage.chats.list.get().forEach((chat_id) => {
            let stored_chat_data = support.storage.chats.get(chat_id);
            if (stored_chat_data === null || stored_chat_data.last_message === undefined) {
                stored_chats[chat_id] = null;
            } else {
                stored_chats[chat_id] = stored_chat_data.last_message
            }
        });

        if (support.vars.current_chat !== undefined && support.vars.current_chat !== null) {
            current_chat = support.chat.getCurrentChat();
            if (!support.chat.isCurrentChatAssigned() && current_chat !== null) {
                stored_chats[current_chat.id] = current_chat.last_message;
            }
        }

        formData.append('chats', JSON.stringify(stored_chats));

        support.request({
            method: support.config.methods.post,
            url: support.config.urls.api.update,
            data: formData,
            success_callback: (data, textStatus, jqXHR) => {
                data = JSON.parse(data);
                if (support.checkRequiredProperties(data, [{'response': ['chats', 'deleted_chats', 'line']}])) {
                    let line = data.response.line;
                    let chats = data.response.chats;
                    let deleted_chats = data.response.deleted_chats;

                    unread_chats = [];
                    chats.forEach((chat) => {
                        let chat_id = chat.id;
                        let chat_name = chat.client.full_name;
                        let updates = chat.updates;
                        let updates_count = chat.count;
                        let last_message = chat.last_message;

                        if (chat_id === undefined || chat_name === undefined || last_message === undefined ||
                            updates === undefined || updates_count === undefined) return;


                        if (updates_count > 0) {
                            unread_chats.push(chat_id);
                        }

                        support.storage.chats.list.append(chat_id);
                        let current_chat_status = support.storage.chats.get(chat_id);

                        let current_unread_count = 0;
                        if (current_chat_status !== null && current_chat_status.unread !== undefined)
                            current_unread_count = current_chat_status.unread;

                        support.storage.chats.set(chat_id, {
                            id: chat_id,
                            last_message: last_message,
                            name: chat_name,
                            unread: current_unread_count + updates_count,
                        });

                        if (updates_count > 0 && support.vars.current_chat === undefined) {
                            let title = 'Новое сообщение в чате';
                            if (updates_count > 1) {
                                title = 'Новые сообщения в чате (' + updates_count + ')';
                            }

                            let message = updates[updates_count - 1].text;
                            if (message.length > 48) {
                                message = message.substring(0, 44) + '...';
                            }

                            support.makeNotificationToast({
                                header: title,
                                text: chat_name,
                                small_text: message,
                                onclick: (event) => {
                                    location.href = support.config.urls.build(support.config.urls.chat.build_value, chat_id);
                                },
                            });
                        }
                    });

                    let current_unread_chats = support.storage.chats.get('unread');
                    if (current_unread_chats === null) current_unread_chats = [];

                    unread_chats.forEach((chat_id) => {
                        if (current_unread_chats.indexOf(chat_id) == -1) {
                            current_unread_chats.push(chat_id);
                        }
                    });
                    support.storage.chats.set('unread', current_unread_chats);

                    support.updateChatsBadge();

                    deleted_chats.forEach((chat_id) => {
                        support.storage.chats.list.remove(chat_id);
                        support.storage.chats.remove(chat_id);
                    });

                    if (line.tickets !== undefined)
                        $('.queue-counter').html(line.tickets)

                    if (support.vars.current_chat !== undefined) {
                        support.chat.receiveUpdate(chats, deleted_chats);
                    }
                }
            },
            error_callback: support.silentErrorCallback,
        });
    },
    updateChatsBadge: function() {
        let chats_badge = $('.chats-counter');
        let unread_chats = support.storage.chats.get('unread');
        if (unread_chats === null) unread_chats = [];
        let unread_count = unread_chats.length;

        if (unread_count > 0) {
            chats_badge.html(unread_count).removeClass('d-none');
        } else {
            chats_badge.html('').addClass('d-none');
        }
    },
    markChatRead: function(chat_id) {
        // remove chat from unread chats
        let unread_chats = support.storage.chats.get('unread');
        let index = unread_chats.indexOf(chat_id);
        if (index != -1) {
            unread_chats.splice(index, 1);
        }
        support.storage.chats.set('unread', unread_chats);
    },
    markMessagesRead: function(chat_id) {
        // remove unread messages from chat
        let chat = support.storage.chats.get(chat_id);
        if (chat === null || chat.unread === 0) return;

        chat.unread = 0;
        support.storage.chats.set(chat_id, chat);

        // remove badge
        if (support.vars.current_chat === undefined) return;
        support.chat.setDialogBadge(chat_id, chat.unread);
    },
    defaultErrorCallback: function(jqXHR, textStatus, errorThrown) {
        let error_text =  errorThrown;
        let error_code = textStatus;
        try {
            let error_response = JSON.parse(jqXHR.responseText);
            if (error_response.status === 'error') {
                error_text = error_response.error.description;
                error_code = error_response.error.code;
            }
        } catch(e) {
            console.log("HTTP Error");
        }
        support.makeErrorToast({
            text: error_text,
            small_text: error_code,
        });
    },
    silentErrorCallback: function(jqXHR, textStatus, errorThrown) {
        let error_text =  errorThrown;
        let error_code = textStatus;
        try {
            let error_response = JSON.parse(jqXHR.responseText);
            if (error_response.status === 'error') {
                error_text = error_response.error.description;
                error_code = error_response.error.code;
            }
        } catch(e) {
            console.log("HTTP Error");
        }
        console.log(error_code + ": " + error_text);
    },
    defaultSuccessCallback: function(data, textStatus, jqXHR) {
        console.log(data);
    },
    makeToast: function({header, header_icon, text, small_text, style, ttl, onclick}) {
        let toast_container = $('.toast-container');
        let toast = $('<div>').addClass('toast').attr({
            role: 'alert',
            'aria-live': 'assertive',
            'aria-atomic': 'true',
        });

        if (onclick !== null) {
            toast.addClass('pointer').on('click', onclick);
        }

        if (style !== null) {
            toast.addClass(style);
        }

        let toast_header = $('<div>').addClass('toast-header');

        toast_header.append(
            $('<strong>').addClass('me-auto').html(header)
        );

        if (header_icon !== null) {
            let header_icon_obj;
            if (typeof(header_icon) == 'string') {
                header_icon_obj = $('<span>').addClass('material-icons-round').html(header_icon);
            } else {
                header_icon_obj = header_icon;
            }
            toast_header.append(header_icon_obj);
        }

        toast_header.append(
            $('<button>').addClass('btn-close').attr({
                type: 'button',
                'aria-label': 'Close',
                'data-bs-dismiss': 'toast',
            })
        );
        let toast_body = $('<div>').addClass('toast-body').append(
            $('<div>').addClass('fw-bold').html(text)
        );

        if (small_text !== null) {
            toast_body.append(
                $('<div>').addClass('small').html(small_text)
            );
        }

        toast.append(toast_header, toast_body);

        let toast_obj = new bootstrap.Toast(toast[0], {
            animation: true,
            autohide: true,
            delay: ttl,
        });
        toast_container.append(toast);

        toast_obj.show();
        toast.on('hide.bs.toast', function () {
            toast.remove();
        });
    },
    makeErrorToast: function({text, small_text}) {
        support.makeToast({
            header: 'Ошибка',
            header_icon: null,
            text: text,
            small_text: small_text,
            style: 'toast-error',
            ttl: 10000,
            onclick: null,
        });
    },
    makeSuccessToast: function({text, small_text}) {
        support.makeToast({
            header: 'Уведомление',
            header_icon: null,
            text: text,
            small_text: small_text,
            style: 'toast-success',
            ttl: 10000,
            onclick: null,
        });
    },
    makeNotificationToast: function({header, text, small_text, onclick}) {
        support.makeToast({
            header: header,
            header_icon: null,
            text: text,
            small_text: small_text,
            style: 'toast-notify',
            ttl: 10000,
            onclick: onclick
        });
    },
    scrollToBottom: function(element) {
        element.scrollIntoView({
            block: 'end',
            inline: 'nearest',
        });
    },
    scrollToTop: function(element) {
        element.scrollIntoView({
            block: 'start',
            inline: 'nearest',
        });
    },
    capitalize: function(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    },
};