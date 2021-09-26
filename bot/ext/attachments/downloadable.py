from abc import ABC
from uuid import uuid4
import os
from datetime import datetime

from telebot.apihelper import ApiTelegramException
import config
from models import FilesTable
from db import db_session
from bot import bot
from app_settings import app_settings
from ext.attachments.base import Base
from ext.files import generate_uuid, generate_path


class FileSizeLimitExceededException(Exception):
    pass


class FileDownloadDisabledException(Exception):
    pass


# TODO add check for free disk space (or catch IO exception)
class FreeSpaceLimitExceededException(Exception):
    pass


class DownloadableAttachment(Base):
    def generate_file_name(self, file_info):
        file_ext = os.path.splitext(file_info.file_path)[1]
        file_name = self.attachment_type
        if file_ext != '':
            file_name = f"{file_name}{file_ext}"

        return file_name

    def download(self):
        try:
            file_info = bot.get_file(self.file_id)
        except ApiTelegramException as e:
            if str(e).find('file is too big') >= 0:
                raise FileSizeLimitExceededException()
            else:
                raise e

        if not app_settings.get('system.file_download_enabled', False):
            raise FileDownloadDisabledException()

        file_size_limit = app_settings.get('download_file_size_limit', 0)
        if file_size_limit != 0 and self.file_size > file_size_limit:
            raise FileSizeLimitExceededException()

        downloaded_file = bot.download_file(file_info.file_path)

        file_uuid = generate_uuid()

        file_original_name = None
        if hasattr(self, 'document_file_name'):
            file_original_name = self.document_file_name

        file_name = self.generate_file_name(file_info)
        file_path = generate_path(file_name, file_uuid)
        file_upload_datetime = datetime.now()
        file_object = FilesTable(file_id=self.file_id, uuid=file_uuid, file_name=file_name,
                                 size=self.file_size, original_name=file_original_name,
                                 uploaded=file_upload_datetime, last_viewed=None)
        db_session.add(file_object)
        db_session.commit()

        self.update({
            'file_id': file_object.id
        })

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as output_file:
            output_file.write(downloaded_file)
