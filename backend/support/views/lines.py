from django.shortcuts import render, redirect
from django.views import View
from django.core.paginator import Paginator

from support.models import Chats, Clients, Settings, Lines
from support.extras.mixins import AdminGroupRequiredMixin


class LinesView(AdminGroupRequiredMixin, View):
    def get(self, request, page=1, page_size=10, *args, **kwargs):
        errors = list()

        staff_user = request.user
        pagination = Paginator(Lines.all(), page_size)

        if page > pagination.num_pages or page < 1:
            lines = list()
            errors.append({
                'text': f'Страница #{page} не существует',
                'description': None,
            })
        else:
            lines = pagination.page(page).object_list

        context = {
            "lines": {
                "list": lines,
            },
            "pagination": {
                "page": page,
                "pages_count": pagination.num_pages,
                "list": [i for i in range(max(1, page - 2), min(page + 2, pagination.num_pages) + 1)],
                "base_url": '/lines/page/'
            },
            "page_title": "Линии поддержки",
            "staff_user": staff_user,
            "errors": errors,
        }
        return render(request, "lines.html", context=context)