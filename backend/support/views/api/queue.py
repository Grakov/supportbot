import json

from django.views import View
from django.contrib.auth import get_user

from support.models import Chats, Clients, Files, Messages, Settings, Lines, StaffMeta
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APILoginRequiredMixin, APIAdminGroupRequiredMixin


class APIQueueListView(APILoginRequiredMixin, View):
    def get(self, request, setting_id=None):
        pass


class APIQueueAssignView(APILoginRequiredMixin, View):
    def post(self, request, setting_id=None):
        staff_user = get_user(request)
        assigned_chat = Chats.auto_assign(staff_user)

        if assigned_chat is None:
            return APIErrorResponse(code='no_available_chats',
                                    description='No available chats to assign').r()
        else:
            chat_id = assigned_chat.id

        return APISuccessResponse({
            'chat_id': chat_id,
            'current_chats': Chats.get_by_staff_api(staff_user)
        }).r()
