from ext.attachments.downloadable import DownloadableAttachment
from telebot import types


class Photo(DownloadableAttachment):
    attachment_type = 'photo'

    # @TODO add file download
    def __init__(self, photo: types.PhotoSize):
        self.file_id = photo.file_id
        self.file_size = photo.file_size
        self.image_width = photo.width
        self.image_height = photo.height
        self.convert_to_dict()
        self.update({
            self.attachment_type: {
                "width": self.image_width,
                "height": self.image_height
            }
        })

    @staticmethod
    def get_largest_photo(photos_list: list):
        return sorted(photos_list, key=lambda x: x.width, reverse=True)[0]
