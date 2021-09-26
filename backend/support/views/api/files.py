from datetime import datetime
import os

from django.views import View
from django.utils import html

from support.models import Files, Settings
from support.extras.api import APISuccessResponse, APIErrorResponse, API_ERROR_RESPONSES
from support.extras.mixins import APILoginRequiredMixin, APIAdminGroupRequiredMixin
from support.forms import FileUploadForm


class APIFilesView(APILoginRequiredMixin, View):
    def get(self, request):
        pass

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return APIErrorResponse(code="no_files_attached",
                                    description="No file has been attached.").r()

        files = request.FILES.getlist('files')
        files_list = list()
        for file in files:
            file_uuid = Files.generate_uuid()
            file_size = file.size
            file_type = file.content_type
            file_name = html.escape(file.name.strip())
            if len(file_name) > 255:
                file_ext = os.path.splitext(file_name)[1]
                file_name = file_name[:-(255 - len(file_ext))] + file_ext
            file_upload_date = datetime.now()

            # TODO add check for free disk space

            file_object = Files(file_id=None, uuid=file_uuid, file_name=file_name, size=file_size, original_name=None,
                                uploaded=file_upload_date, last_viewed=None)
            file_object.save()

            file_path = file_object.generate_file_path()
            os.mkdir(os.path.dirname(file_path))
            try:
                with open(file_path, 'wb') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
            except Exception as e:
                print(e)
                return API_ERROR_RESPONSES['general_500'].r()

            files_list.append({
                'uuid': file_uuid,
                'file_name': file_name,
                'file_size': file_object.get_readable_size(),
                'url': file_object.generate_file_url(silent=True),
            })

        return APISuccessResponse({'files': files_list}).r()

    # TODO add method for deleting uploaded (but not submitted with messages) files
