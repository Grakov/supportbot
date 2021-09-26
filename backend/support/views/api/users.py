from datetime import datetime

from django.template.loader import get_template
from django.views import View
from django.contrib.auth import get_user
from django.utils import html

from support.models import Clients, Settings
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APILoginRequiredMixin, APIAdminGroupRequiredMixin


class APIUsersInfoView(APILoginRequiredMixin, View):
    def get(self, request, user_id=None):
        client = Clients.get(user_id)
        if client is None:
            return API_ERROR_RESPONSES['client_doesnt_exists'].r()

        return APISuccessResponse({
            'user': client.dict(),
        }).r()


class APIUsersExtraView(APILoginRequiredMixin, View):
    def get(self, request, user_id):
        client = Clients.get(user_id)
        if client is None:
            return API_ERROR_RESPONSES['client_doesnt_exists'].r()

        comments = client.comments
        names_history = client.name_history.container
        return APISuccessResponse({
            'comments': get_template('components/chat_comments.html').render(context={
                'comments': comments
            }),
            'known_names': get_template('components/chat_known_names.html').render(context={
                'names_container': names_history
            }),
        }).r()


class APIUsersCommentsView(APILoginRequiredMixin, View):
    def post(self, request, user_id):
        staff_user = get_user(request)
        comment_text = request.POST.get('comment', None)

        client = Clients.get(user_id)
        if client is None:
            return API_ERROR_RESPONSES['client_doesnt_exists'].r()

        if comment_text is None or len(comment_text) < 3:
            return APIErrorResponse(code='empty_comment',
                                    description="Empty or too short comment was sent: text with 4+ characters required").r()
        else:
            comment_text = html.escape(comment_text)

        client.comments.append({
            'text': comment_text,
            'author_id': staff_user.id,
            'username': staff_user.username,
            'timestamp': datetime.now()
        })
        client.save()
        return APISuccessResponse({
            'user': client.dict(),
            'user_id': user_id,
        }).r()


class APIUsersBlockView(APILoginRequiredMixin, View):
    def post(self, request, user_id):
        client = Clients.get(user_id)
        if client is None:
            return API_ERROR_RESPONSES['client_doesnt_exists'].r()

        if client.is_blocked:
            return API_ERROR_RESPONSES['user_already_blocked'].r()

        client.is_blocked = True
        client.save()
        return APISuccessResponse({
            'user': client.dict(),
            'user_id': user_id,
            'is_blocked': True
        }).r()

    def delete(self, request, user_id):
        client = Clients.get(user_id)
        if client is None:
            return API_ERROR_RESPONSES['client_doesnt_exists'].r()

        if not client.is_blocked:
            return API_ERROR_RESPONSES['user_already_unblocked'].r()

        client.is_blocked = False
        client.save()
        return APISuccessResponse({
            'user': client.dict(),
            'user_id': user_id,
            'is_blocked': False
        }).r()


class APIUsersFinderView(APILoginRequiredMixin, View):
    def post(self, request):
        pass
