from datetime import datetime
import os
import json
import mimetypes
from PIL import Image
from moviepy.editor import VideoFileClip

from django.shortcuts import render
from django.template.loader import get_template
from django.views import View
from django.contrib.auth import get_user
from django.core.paginator import Paginator
from django.utils import html

from support.models import Chats, Files, Messages, Settings, Lines
from support.tasks import send_message
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APILoginRequiredMixin, APIAdminGroupRequiredMixin


class APIChatsListView(APILoginRequiredMixin, View):
    def get(self, request):
        pass


class APIChatsInfoView(APILoginRequiredMixin, View):
    def get(self, request, chat_id=None):
        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        return APISuccessResponse({
            'chat': chat.dict(),
        }).r()


class APIChatsAssignmentView(APILoginRequiredMixin, View):
    def post(self, request, chat_id=None):
        staff_user = get_user(request)
        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        # TODO fix undefined behaviour while user tries to take chat from another staff user
        if chat.assignee == staff_user:
            return APIErrorResponse(code='staff_already_assigned',
                                    description='Staff user has already been assigned for this chat').r()

        chat.assign(staff_user)
        # TODO return list of assigned chats
        return APISuccessResponse({
            'chat': chat.dict(),
            'chat_id': chat_id,
            'current_chats': Chats.get_by_staff_api(staff_user)
        }).r()

    def delete(self, request, chat_id=None):
        staff_user = get_user(request)
        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        if chat.assignee != staff_user:
            return APIErrorResponse(code='staff_already_unassigned',
                                    description='Staff user has already been unassigned for this chat').r()

        chat.unassign(staff_user)
        return APISuccessResponse({
            'current_chats': Chats.get_by_staff_api(staff_user)
        }).r()


class APIChatsMessagesBeforeView(APILoginRequiredMixin, View):
    def get(self, request, first_message=None, page_size=20, chat_id=None):
        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        messages = Messages.get(chat, before=first_message, reverse=True)[:page_size:-1]

        if len(messages) == 0:
            return APIErrorResponse(code='no_more_messages',
                                    description='Where are no older messages',
                                    http_code='410').r()

        return APISuccessResponse({
            'messages': get_template('chat_messages.html').render(context={
                "messages": messages
            }),
            'first_message': messages[0].id,
            'last_message': messages[-1].id,
        }).r()


class APIChatsMessagesAfterView(APILoginRequiredMixin, View):
    def get(self, request, last_message=None, page_size=20, chat_id=None):
        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        messages = Messages.get(chat, after=last_message, reverse=True)[:page_size:-1]

        if len(messages) == 0:
            return APIErrorResponse(code='no_new_messages',
                                    description='Where are no new messages',
                                    http_code='410').r()

        return APISuccessResponse({
            'messages': get_template('chat_messages.html').render(context={
                "messages": messages
            }),
            'first_message': messages[0].id,
            'last_message': messages[-1].id,
        }).r()


class APIChatsMessagesView(APILoginRequiredMixin, View):
    def post(self, request, chat_id=None):
        staff_user = get_user(request)
        message_text = request.POST.get('message', None)
        attachments = request.POST.get('attachments', '[]')
        time = datetime.now()

        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        received_attachments = list()
        if attachments == '':
            attachments = '[]'
        try:
            received_attachments = json.loads(attachments)

            # check, if attachments_list is list of strings
            if type(received_attachments) is not list:
                raise ValueError

            for element in received_attachments:
                if type(element) is not dict or element.get('type', None) is None:
                    raise ValueError
        except ValueError:
            return API_ERROR_RESPONSES['invalid_json'].r()

        if message_text is None or len(message_text.strip()) == 0:
            if len(received_attachments) == 0:
                return APIErrorResponse(code='empty_message',
                                        description="Empty message was sent: text or attachment required").r()
        else:
            message_text = html.escape(message_text.strip())

        attachments_list = list()
        for attachment in received_attachments:
            received_type = attachment.get('type')
            attachment_object = dict()

            if received_type == 'file':
                attachment_uuid = attachment.get('uuid')
                file = Files.get_by_uuid(attachment_uuid)
                if file is None:
                    return APIErrorResponse(code='non_existing_file_attached',
                                            description="Attachments contains non-existing file.").r()

                file_mimetype_text = mimetypes.guess_type(file.file_name)[0]

                # default value
                attachment_type = 'document'
                if file_mimetype_text is not None:
                    file_mimetype = file_mimetype_text.split('/')
                    file_type = file_mimetype[0]
                    file_subtype = None
                    if len(file_mimetype) == 2:
                        file_subtype = file_mimetype[1]

                    if file_type == 'image' and file_subtype in ['jpeg', 'png', 'gif']:
                        attachment_type = 'photo'
                    elif file_type == 'video' and file_subtype in ['mp4']:
                        attachment_type = 'video'
                    else:
                        attachment_type = 'document'

                attachment_object.update({
                    'type': attachment_type,
                    'file_id': file.id,
                })

                if attachment_type == 'photo':
                    # Check if we work with real image
                    try:
                        photo = Image.open(file.generate_file_path())

                        attachment_object.update({
                            attachment_type: {
                                'width': photo.width,
                                'height': photo.height,
                            }
                        })
                    except Exception:
                        attachment_type = 'document'

                if attachment_type == 'video':
                    # Check if we work with real video
                    try:
                        video_clip = VideoFileClip(file.generate_file_path())
                        video_width = video_clip.w
                        video_height = video_clip.h
                        video_duration = video_clip.duration

                        # Generating thumbnail
                        preview_image = Image.fromarray(video_clip.get_frame(0))

                        preview_file = Files.create(None, 'preview.jpg', 0, None)
                        preview_path = preview_file.generate_file_path()
                        preview_image.save(preview_path, quality=95)

                        preview_file.size = os.path.getsize(preview_path)
                        preview_file.save()
                        video_clip.close()

                        # TODO fix this mess
                        attachment_object.update({
                            attachment_type: {
                                'width': video_width,
                                'height': video_height,
                                'duration': video_duration,
                                'thumb': {
                                    'type': 'photo',
                                    'file_id': preview_file.id,
                                    'photo': {
                                        'width': video_width,
                                        'height': video_height,
                                    }
                                },
                            }
                        })
                    except Exception:
                        attachment_type = 'document'

                if attachment_type == 'document':
                    attachment_object.update({
                        attachment_type: {
                            'file_name': None if file.file_name is None else html.escape(file.file_name),
                            'mime_type': 'application/octet-stream' if file_mimetype_text is None else file_mimetype_text,
                        }
                    })
            elif received_type == 'location':
                latitude = attachment.get('latitude', None)
                longitude = attachment.get('longitude', None)
                title = attachment.get('title', None)

                if title is not None:
                    title = html.escape(title)

                address = attachment.get('address', None)
                if address is not None:
                    address = html.escape(address)

                if latitude is None or longitude is None:
                    return API_ERROR_RESPONSES['invalid_json'].r()

                attachment_object.update({
                    'type': 'location',
                    'location': {
                        'latitude': latitude,
                        'longitude': longitude,
                        'title': title,
                        'address': address,
                    }
                })

            attachments_list.append(attachment_object)

        message = Messages.send(client=None, staff=staff_user, chat=chat, is_service=False, time=time,
                                text=message_text, attachments=attachments_list, markdown=True)
        if not message.is_service:
            send_message.delay(message.id)
            chat.set_status('answered')

        return APISuccessResponse({
            'chat': chat.dict(),
            'message_id': message.id,
        }).r()


class APIChatsQueueView(APILoginRequiredMixin, View):
    def post(self, request, chat_id):
        staff_user = get_user(request)
        new_queue = request.POST.get('line', None)

        if '' in [new_queue]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        new_line = Lines.get(new_queue)
        if new_line is None:
            return API_ERROR_RESPONSES['line_doesnt_exists'].r()

        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        chat.set_line(line=new_line, staff_user=staff_user)
        chat.save()

        return APISuccessResponse({
            'chat_id': chat.id,
            'line': new_line.dict(),
        }).r()


class APIChatsStatusView(APILoginRequiredMixin, View):
    def post(self, request, chat_id):
        staff_user = get_user(request)

        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        status = 'answered'
        chat.set_status(status, staff_user)
        return APISuccessResponse({
            'chat': chat.dict(),
            'chat_id': chat.id,
            'status': status,
        }).r()

    def delete(self, request, chat_id):
        staff_user = get_user(request)

        chat = Chats.get(chat_id)
        if chat is None:
            return API_ERROR_RESPONSES['chat_object_not_exists'].r()

        chat.unassign(staff_user)
        status = 'closed'
        chat.set_status(status, staff_user)

        return APISuccessResponse({
            'chat': chat.dict(),
            'chat_id': chat.id,
            'status': status,
        }).r()
