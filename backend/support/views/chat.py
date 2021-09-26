from datetime import date, datetime

from django.shortcuts import render
from django.views import View
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin

from support.models import Chats, Messages, Settings, Lines


class ChatView(LoginRequiredMixin, View):
    def get(self, request, chat_id=None, page=1, page_size=20, *args, **kwargs):
        staff_user = request.user
        current_chat = Chats.get(chat_id)

        # get list of assigned chats
        assigned_chats = Chats.get_by_staff(staff_user)

        pagination = Paginator(Messages.get(current_chat, reverse=True), page_size)
        messages = list(reversed(pagination.page(page)))
        chats_limit = Settings.get_value_by_key(key='system.chats_limit')
        context = {
            "chat": {
                "assigned_chats": [{
                    "chat": chat,
                    "last_message": chat.get_last_real_message(),
                } for chat in assigned_chats],
                "current_chat": current_chat,
                "chats_limit": chats_limit,
                "messages": messages,
                "mapbox_api_token": Settings.get_value_by_key(key='mapbox.api_token', default_value=''),
            },
            "lines": {
                "list": Lines.all(),
            },
            "page_title": "Сообщения",
            "staff_user": staff_user
        }

        return render(request, "chat.html", context=context)
