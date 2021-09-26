from django.shortcuts import render
from django.views import View
from django.core.paginator import Paginator

from support.models import Settings
from support.extras.mixins import AdminGroupRequiredMixin


class SettingsView(AdminGroupRequiredMixin, View):
    def get(self, request, page=1, page_size=20):
        errors = list()
        staff_user = request.user

        pagination = Paginator(Settings.all(), page_size)

        if page > pagination.num_pages or page < 1:
            settings = list()
            errors.append({
                'text': f'Страница #{page} не существует',
                'description': None,
            })
        else:
            settings = pagination.page(page).object_list

        context = {
            "settings": settings,
            "pagination": {
                "page": page,
                "pages_count": pagination.num_pages,
                "list": [i for i in range(max(1, page - 2), min(page + 2, pagination.num_pages) + 1)],
                "base_url": "/settings/page/",
            },
            "page_title": "Настройки",
            "staff_user": staff_user,
            "errors": errors,
        }
        return render(request, "settings.html", context=context)
