from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator

from support.models import Chats, Clients, Settings


class UsersView(LoginRequiredMixin, View):
    def get(self, request, page=1, page_size=15, user_id=None, *args, **kwargs):
        errors = list()

        # Check if current url is /users/<int> for redirection to client's chat
        if user_id is not None:
            chat_obj = Chats.objects.filter(client=user_id).first()
            if chat_obj is not None:
                return redirect(f'/chat/{chat_obj.id}')
            else:
                errors.append({
                    'text': 'Пользователь не найден',
                    'description': None,
                })

        staff_user = request.user
        pagination = Paginator(Clients.objects.all(), page_size)

        if page > pagination.num_pages or page < 1:
            users = list()
            errors.append({
                'text': f'Страница #{page} не существует',
                'description': None,
            })
        else:
            users = pagination.page(page).object_list

        context = {
            "users": {
                "list": users,
            },
            "pagination": {
                "page": page,
                "pages_count": pagination.num_pages,
                "list": [i for i in range(max(1, page - 2), min(page + 2, pagination.num_pages) + 1)],
                "base_url": '/users/page/'
            },
            "page_title": "Пользователи",
            "staff_user": staff_user,
            "errors": errors,
        }
        return render(request, "users.html", context=context)
