from django.views import View
from django.utils import html
from django.core.paginator import Paginator

from support.models import Chats, Settings, Lines
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APIAdminGroupRequiredMixin, DemoDisabledMixin


class APILinesListView(DemoDisabledMixin, View):
    def get(self, request):
        lines = Lines.all()
        return APISuccessResponse({
            'lines': {
                'count': len(lines),
                'list': [line.dict() for line in lines],
            }
        }).r()

    def post(self, request):
        # TODO replace with form use
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')

        if '' in [name]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        line = Lines(name=html.escape(name), description=html.escape(description))
        line.save()

        return APISuccessResponse({
            'line': line.dict(),
        }).r()


class APILinesInfoView(DemoDisabledMixin, View):
    def get(self, request, line_id=None):
        line = Lines.get(line_id)
        if line is None:
            return API_ERROR_RESPONSES['line_doesnt_exists'].r()

        return APISuccessResponse({
            'line': line.dict()
        }).r()

    def post(self, request, line_id=None):
        line = Lines.get(line_id)
        if line is None:
            return API_ERROR_RESPONSES['line_doesnt_exists'].r()

        # TODO replace with form use
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')

        if '' in [name]:
            return API_ERROR_RESPONSES['missed_form_parameter'].r()

        line.name = html.escape(name)
        line.description = html.escape(description)
        line.save()

        return APISuccessResponse({
            'line': line.dict(),
        }).r()

    def delete(self, request, line_id=None):
        line = Lines.get(line_id)
        if line is None:
            return API_ERROR_RESPONSES['line_doesnt_exists'].r()

        if line.is_system():
            return APIErrorResponse(code='system_queue_line_protected',
                                    description='Couldn\'t perform action to system queue line')

        Chats.replace_line(line, Lines.get_default_line())
        line.delete()

        return APISuccessResponse({}).r()
