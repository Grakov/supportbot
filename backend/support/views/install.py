from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import User

from support.extras.passwords import generate_password
from support.extras.staff import StaffRoles, create_staff, check_username
from backend import settings as app_settings
from support.models import Settings


class InstallView(View):
    def get(self, request, errors=None, data=None, *args, **kwargs):
        if InstallView.is_superuser_exists():
            return redirect('/')

        app_setup_password = Settings.get_value_by_key('APP_SETUP_PASSWORD', None)
        if app_setup_password is None:
            app_setup_password = generate_password(length=64)
            setting = Settings(key="APP_SETUP_PASSWORD", type="string", value=app_setup_password,
                               description="APP_SETUP_PASSWORD parameter. "
                                           "Can be deleted after creating first administrator.")
            setting.save()

        print(f'Generated APP_SETUP_PASSWORD = {app_setup_password}')

        context = {
            'page_title': 'Установка',
            'errors': errors,
            'data': data,
        }
        return render(request, 'install.html', context=context)

    def post(self, request, *args, **kwargs):
        if InstallView.is_superuser_exists():
            return redirect('/')

        errors = list()
        # TODO use forms
        app_password = request.POST.get('app_password', None)
        username = request.POST.get('username', None)
        email = request.POST.get('email', None)
        first_name = request.POST.get('first_name', None)
        last_name = request.POST.get('last_name', None)

        if app_password is None:
            errors.append("Не передан APP_SETUP_PASSWORD")

        if app_password != Settings.get_value_by_key('APP_SETUP_PASSWORD', None):
            errors.append("Указан неправильный APP_SETUP_PASSWORD")

        if username is None or email is None or len(email) < 3:
            errors.append("Не передан username и/или email")

        if first_name is None or last_name is None or len(first_name) == 0 or len(last_name) == 0:
            errors.append("Не передано имя и/или фамилия")

        if not check_username(username):
            errors.append("Некорректное имя пользователя. Имя пользователя должно быть длинной от 3 символов и " +
                          "должно содержать только латиницу и знак подчеркивания")

        if len(errors) > 0:
            data = {
                'username': username,
                'email': email,
                'app_password': app_password,
                'first_name': first_name,
                'last_name': last_name,
            }
            return self.get(request, errors, data, *args, **kwargs)

        password = generate_password()
        create_staff(username=username, first_name=first_name, last_name=last_name, email=email, password=password,
                     avatar=None, role=StaffRoles.administrator.value)

        context = {
            'page_title': 'Установка завершена',
            'username': username,
            'password': password,
        }
        return render(request, 'install_complete.html', context=context)

    @staticmethod
    def is_superuser_exists():
        superuser = User.objects.filter(is_superuser=True).first()
        # Check if at least one superuser exists
        if superuser is not None:
            return True

        return False
