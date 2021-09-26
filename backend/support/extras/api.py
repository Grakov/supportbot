import json

from django.http import HttpResponse


class APIBaseResponse:
    def __init__(self, http_code, status, response, response_field='response'):
        self.container = {
            'status': status,
            response_field: response
        }
        self.http_code = http_code
        pass

    def r(self):
        return HttpResponse(str(self), status=self.http_code)

    def __str__(self):
        return json.dumps(self.container)


class APISuccessResponse(APIBaseResponse):
    def __init__(self, response={}):
        super().__init__(http_code=200, status='ok', response=response)


class APIErrorResponse(APIBaseResponse):
    def __init__(self, code, description='', http_code=500):
        super().__init__(http_code=http_code, status='error', response_field='error', response={
            'code': code,
            'description': description
        })


API_ERROR_RESPONSES = {
    'chat_object_not_exists': APIErrorResponse(code='chat_object_not_exists',
                                               description='Chat with this id doesn\'t exists'),
    'general_500': APIErrorResponse(code='general_500',
                                    description='Internal server error'),
    'client_doesnt_exists': APIErrorResponse(code='client_doesnt_exists',
                                             description='User not found'),
    'user_already_blocked': APIErrorResponse(code='user_already_blocked',
                                             description='User already blocked'),
    'user_already_unblocked': APIErrorResponse(code='user_already_unblocked',
                                               description='User already unblocked'),
    'staff_user_doesnt_exists': APIErrorResponse(code='staff_user_doesnt_exists',
                                                 description='User not found'),
    'username_exists': APIErrorResponse(code='username_exists',
                                        description='Can\'t select this username: username exists'),
    'invalid_username': APIErrorResponse(code='invalid_username',
                                         description='Invalid format of username: allowed only letters, digits and underlines'),
    'line_doesnt_exists': APIErrorResponse(code='line_doesnt_exists',
                                           description='Selected queue line id doesn\'t exists'),
    'role_doesnt_exists': APIErrorResponse(code='role_doesnt_exists',
                                           description='Selected user role doesn\'t exists'),
    'invalid_json': APIErrorResponse(code='invalid_json',
                                     description='Incorrect JSON string was send'),
    'setting_not_exists': APIErrorResponse(code='setting_not_exists',
                                           description='Setting with this id doesn\'t exists'),
    'missed_form_parameter': APIErrorResponse(code='missed_form_parameter',
                                              description='One of form parameters is missed'),
    'setting_type_value_mismatch': APIErrorResponse(code='setting_type_value_mismatch',
                                                    description='Sent value for this setting doesn\'t match is\'s type'),
}
