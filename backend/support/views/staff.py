from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator

from support.extras.mixins import AdminGroupRequiredMixin


class StaffView(AdminGroupRequiredMixin, View):
    def get(self, request, page=1, page_size=10, user_id=None, *args, **kwargs):
        errors = list()
        staff_user = request.user

        pagination = Paginator(User.objects.all(), page_size)

        # that's not good method to determine page num for specific user_id
        if user_id is not None:
            page = 1
            is_user_found = False
            for (index, value) in enumerate(User.objects.all()):
                if value.id == user_id:
                    print(index, value.id)
                    c_index = index + 1
                    page = c_index // page_size + (1 if c_index % page_size != 0 else 0)
                    is_user_found = True
                    break

            if not is_user_found:
                errors.append({
                    'text': f'Пользователь не найден',
                    'description': None,
                })

        if page > pagination.num_pages or page < 1:
            staff_users = list()
            errors.append({
                'text': f'Страница #{page} не существует',
                'description': None,
            })
        else:
            staff_users = pagination.page(page).object_list

        context = {
            "users": {
                "list": staff_users,
                "edit": user_id,
            },
            "pagination": {
                "page": page,
                "pages_count": pagination.num_pages,
                "list": [i for i in range(max(1, page - 2), min(page + 2, pagination.num_pages) + 1)],
                "base_url": '/staff/page/',
            },
            "page_title": "Сотрудники",
            "staff_user": staff_user,
            "errors": errors,
        }
        return render(request, "staff.html", context=context)
