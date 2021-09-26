from django.views import View

from support.models import Settings
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APIAdminGroupRequiredMixin, DemoDisabledMixin


class APISettingsListView(DemoDisabledMixin, View):
    def get(self, request):
        pass

    def post(self, request):
        setting_key = request.POST.get('key', '')
        setting_type = request.POST.get('type', '')
        setting_value = request.POST.get('value', '')
        setting_description = request.POST.get('description', '')

        if '' in [setting_key, setting_type, setting_value]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        if Settings.get(setting_key) is not None:
            return APIErrorResponse(code='key_for_setting_exists',
                                    description='Setting with this key already exists.').r()

        if setting_description is None:
            setting_description = ''

        # TODO add html-escape? (for name also) Or escape on render time?
        setting_description = setting_description.strip()

        if not Settings.check_value(setting_value, setting_type):
            return API_ERROR_RESPONSES['setting_type_value_mismatch'].r()

        new_setting = Settings(key=setting_key, type=setting_type, value=setting_value, description=setting_description)
        new_setting.save()

        return APISuccessResponse({
            'setting': {
                'id': new_setting.id,
                'key': new_setting.key,
                'type': new_setting.type,
                'value': new_setting.get_value(),
                'description': new_setting.description,
                'is_system': new_setting.is_system(),
            }
        }).r()


class APISettingsInfoView(DemoDisabledMixin, View):
    def get(self, request, setting_id=None):
        setting = Settings.get_by_id(setting_id)
        if setting is None:
            return API_ERROR_RESPONSES['setting_not_exists'].r()

        return APISuccessResponse({
            'setting': {
                'id': setting.id,
                'key': setting.key,
                'type': setting.type,
                'value': setting.get_value(),
                'description': setting.description,
                'is_system': setting.is_system(),
            }
        }).r()

    def post(self, request, setting_id=None):
        setting = Settings.get_by_id(setting_id)
        if setting is None:
            return API_ERROR_RESPONSES['setting_not_exists'].r()

        # TODO use forms
        setting_key = request.POST.get('key', '')
        setting_value = request.POST.get('value', '')

        if '' in [setting_key, setting_value]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        if setting_key != setting.key and setting.is_system():
            return APIErrorResponse(code='system_setting_key_immutable',
                                    description='Can\'t edit system setting key.').r()

        try:
            setting.key = setting_key
            # set_value contains setting.save call
            setting.set_value(setting_value)
        except TypeError:
            return API_ERROR_RESPONSES['setting_type_value_mismatch'].r()

        return APISuccessResponse({
            'setting': {
                'id': setting.id,
                'key': setting.key,
                'type': setting.type,
                'value': setting.get_value(),
                'description': setting.description,
                'is_system': setting.is_system(),
            }
        }).r()

    def delete(self, request, setting_id=None):
        setting = Settings.get_by_id(setting_id)
        if setting is None:
            return API_ERROR_RESPONSES['setting_not_exists'].r()

        if setting.is_system():
            return APIErrorResponse(code='system_setting_delete_attempt',
                                    description='Can\'t delete system setting.').r()

        setting_id = setting.id
        setting.delete()

        return APISuccessResponse({
            'setting': {
                'id': setting_id,
                'status': 'deleted',
            }
        }).r()
