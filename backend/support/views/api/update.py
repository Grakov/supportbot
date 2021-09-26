import json

from django.views import View
from django.contrib.auth import get_user
from django.utils import html

from support.models import Chats, Files, Messages, Settings, StaffMeta, Lines
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APILoginRequiredMixin


class APIUpdateView(APILoginRequiredMixin, View):
    def post(self, request):
        staff_user = get_user(request)
        assigned_chats = Chats.get_by_staff(staff_user)

        response_chats = list()
        try:
            stored_chats = json.loads(request.POST.get('chats', '{}'))
            if not issubclass(type(stored_chats), dict):
                raise TypeError
        except (json.JSONDecodeError, TypeError, KeyError):
            return API_ERROR_RESPONSES['invalid_json'].r()

        for chat in assigned_chats:
            last_message_id = stored_chats.get(str(chat.id), None)

            response_chats.append(
                APIUpdateView.get_update_data_from_chat(chat, last_message_id)
            )

        deleted_chats = list(set([int(chat) for chat in stored_chats.keys()]) - set([chat.id for chat in assigned_chats]))

        for chat_id in deleted_chats:
            chat = Chats.get(chat_id)
            if chat is None:
                return

            last_message_id = stored_chats.get(str(chat_id), None)

            response_chats.append(
                APIUpdateView.get_update_data_from_chat(chat, last_message_id)
            )

        return APISuccessResponse({
            "chats": response_chats,
            "deleted_chats": deleted_chats,
            "line": {
                "id": staff_user.meta.line.id,
                "name": staff_user.meta.line.name,
                "tickets": Chats.get_opened_chats_count(staff_user.meta.line),
            }
        }).r()

    @staticmethod
    def get_update_data_from_chat(chat: Chats, last_message_id) -> dict:
        chat_data = chat.dict()

        if last_message_id is None:
            new_messages = list()
        else:
            messages = Messages.get(chat, after=last_message_id)
            new_messages = [{
                "id": message.id,
                "text": message.text,
                "is_from_client": message.staff is None,
                "is_service": message.is_service,
            } for message in messages]

        chat_data.update({
            "updates": new_messages,
            "count": len(new_messages),
        })

        return chat_data
