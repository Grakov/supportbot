from abc import ABC

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from backend import settings as app_settings
from support.extras.api import APIErrorResponse


class APILoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        return APIErrorResponse(code='login_required', description='Login Required', http_code=403).r()


class GroupRequiredMixin(ABC):
    """
        group_required - list of strings, required param
        Based on https://gist.github.com/ceolson01/206139a093b3617155a6
    """

    group_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            user_groups = []
            for group in request.user.groups.values_list('name', flat=True):
                user_groups.append(group)
            if len(set(user_groups).intersection(self.group_required)) <= 0:
                return self.handle_invalid_group(request)
        return super(GroupRequiredMixin, self).dispatch(request, *args, **kwargs)


class AdminGroupRequiredMixin(GroupRequiredMixin, LoginRequiredMixin):
    def __init__(self, *args, **kwargs):
        super(AdminGroupRequiredMixin, self).__init__(*args, **kwargs)
        self.group_required = ['administrator']

    def handle_invalid_group(self, request):
        staff_user = request.user
        context = {
            "page_title": "Staff",
            "staff_user": staff_user,
        }
        return render(request, "403.html", context=context, status=403)


class APIAdminGroupRequiredMixin(AdminGroupRequiredMixin, APILoginRequiredMixin):
    def handle_invalid_group(self, request):
        return APIErrorResponse(code='administrator_rights_required',
                                description='You need to be an administrator to perform this action',
                                http_code=403).r()


# Mixin for some vulnerable API endpoints (so nesting from APIAdminGroupRequiredMixin is needed)
class DemoDisabledMixin(APIAdminGroupRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if app_settings.DEMO_VERSION and request.method.lower() in ['post', 'delete']:
            return APIErrorResponse(code='demo_limit', description='Not available on demo server', http_code=403).r()

        return super(GroupRequiredMixin, self).dispatch(request, *args, **kwargs)
