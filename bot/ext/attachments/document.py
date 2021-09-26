import html
from ext.attachments.downloadable import DownloadableAttachment
from telebot import types


class Document(DownloadableAttachment):
    attachment_type = 'document'

    # @TODO add file download
    def __init__(self, document: types.Document):
        self.file_id = document.file_id
        self.file_size = document.file_size
        self.document_file_name = html.escape(document.file_name.strip())
        self.document_mime_type = document.mime_type
        self.convert_to_dict()
        self.update({
            self.attachment_type: {
                "file_name": self.document_file_name,
                "mime_type": self.document_mime_type,
            }
        })
