from django.views import View
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.utils import html

from support.models import Settings, Lines, StaffMeta
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mail import send_mail
from support.extras.mixins import APILoginRequiredMixin, APIAdminGroupRequiredMixin, DemoDisabledMixin
from support.extras.staff import StaffRoles, create_staff, check_username
from support.extras.passwords import generate_password


class APIStaffMetaView(APILoginRequiredMixin, View):
    def get(self, request):
        lines = Lines.all()
        line_response = [{'id': line.id, 'name': line.name, 'description': line.description} for line in lines]

        roles_response = [role.value for role in StaffRoles]

        return APISuccessResponse({
            'lines': line_response,
            'roles': roles_response,
        }).r()


class APIStaffListView(DemoDisabledMixin, View):
    def get(self, request):
        pass

    def post(self, request):
        # TODO add form support
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        line = request.POST.get('line', '')
        role = request.POST.get('role', '')

        if '' in [first_name, last_name, username, email, line, role]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        line = Lines.get(line)
        if line is None:
            return API_ERROR_RESPONSES['line_doesnt_exists'].r()

        if role not in [role.value for role in StaffRoles]:
            return API_ERROR_RESPONSES['role_doesnt_exists'].r()

        if not check_username(username):
            return API_ERROR_RESPONSES['invalid_username'].r()

        username_count = len(User.objects.filter(username=username).all())
        if username_count > 0:
            return API_ERROR_RESPONSES['username_exists'].r()

        password_length = Settings.get_value_by_key('system.password_length', 8)
        generated_password = generate_password(password_length)

        # TODO add email check
        new_user = create_staff(username=username, first_name=html.escape(first_name), last_name=html.escape(last_name),
                                email=email, password=generated_password, avatar=None, role=role, line=line)

        send_mail(
            subject='Ваш аккаунт успешно создан',
            to=[new_user.email],
            template='emails/user_created.html',
            context={
                'first_name': new_user.first_name,
                'last_name': new_user.last_name,
                'username': new_user.username,
                'password': generated_password,
            },
        )

        return APISuccessResponse({
            'user': StaffMeta.dict(new_user),
        }).r()


class APIStaffInfoView(DemoDisabledMixin, View):
    def get(self, request, user_id=None):
        staff_user = User.objects.filter(id=user_id).first()
        if staff_user is None:
            return API_ERROR_RESPONSES['staff_user_doesnt_exists'].r()

        return APISuccessResponse({
            'user': StaffMeta.dict(staff_user),
        }).r()

    def post(self, request, user_id=None):
        staff_user = User.objects.filter(id=user_id).first()
        if staff_user is None:
            return API_ERROR_RESPONSES['staff_user_doesnt_exists'].r()

        # TODO add form
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')

        if '' in [first_name, last_name, username, email]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        if not check_username(username):
            return API_ERROR_RESPONSES['invalid_username'].r()

        username_count = len(User.objects.filter(username=username).all())
        if username_count > 1:
            return API_ERROR_RESPONSES['username_exists'].r()

        staff_user.first_name = html.escape(first_name)
        staff_user.last_name = html.escape(last_name)
        staff_user.username = username
        staff_user.email = email
        staff_user.save()

        return APISuccessResponse({
            'user': StaffMeta.dict(staff_user),
        }).r()


class APIStaffPasswordView(DemoDisabledMixin, View):
    def get(self, request, user_id=None):
        # lol
        staff_user = User.objects.filter(id=user_id).first()
        if staff_user is None:
            return API_ERROR_RESPONSES['staff_user_doesnt_exists'].r()

        return APISuccessResponse({
            'id': user_id,
            'password': generate_password(),
        })

    def post(self, request, user_id=None):
        staff_user = User.objects.filter(id=user_id).first()
        if staff_user is None:
            return API_ERROR_RESPONSES['staff_user_doesnt_exists'].r()

        # TODO add setting for length
        generated_password = generate_password()
        staff_user.set_password(generated_password)
        staff_user.save()

        send_mail(
            subject='Новый пароль для доступа к порталу поддержки',
            to=[staff_user.email],
            template='emails/user_password_reset.html',
            context={
                'first_name': staff_user.first_name,
                'last_name': staff_user.last_name,
                'username': staff_user.username,
                'password': generated_password,
            },
        )

        return APISuccessResponse({
            'user': StaffMeta.dict(staff_user),
        }).r()


class APIStaffBlockView(DemoDisabledMixin, View):
    def post(self, request, user_id=None):
        staff_user = User.objects.filter(id=user_id).first()
        if staff_user is None:
            return API_ERROR_RESPONSES['staff_user_doesnt_exists'].r()

        if not staff_user.is_active:
            return API_ERROR_RESPONSES['user_already_blocked'].r()

        staff_user.is_active = False
        staff_user.save()

        return APISuccessResponse({
            'user': StaffMeta.dict(staff_user),
        }).r()

    def delete(self, request, user_id=None):
        staff_user = User.objects.filter(id=user_id).first()
        if staff_user is None:
            return API_ERROR_RESPONSES['staff_user_doesnt_exists'].r()

        if staff_user.is_active:
            return API_ERROR_RESPONSES['user_already_unblocked'].r()

        staff_user.is_active = True
        staff_user.save()

        return APISuccessResponse({
            'user': StaffMeta.dict(staff_user),
        }).r()
