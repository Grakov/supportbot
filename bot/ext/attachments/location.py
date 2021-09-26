import math
import html

from ext.attachments.base import Base
from telebot import types


class Location(Base):
    attachment_type = 'location'

    def __init__(self, location: types.Location, title=None, address=None):
        self.file_id = None
        self.file_size = 0
        self.location_longitude = location.longitude
        self.location_latitude = location.latitude

        self.location_title = title
        if self.location_title is not None:
            self.location_title = html.escape(self.location_title)

        self.location_address = address
        if self.location_address is not None:
            self.location_address = html.escape(self.location_address)

        self.convert_to_dict()
        self.update({
            self.attachment_type: {
                "latitude": self.location_latitude,
                "longitude": self.location_longitude,
                "title": self.location_title,
                "address": self.location_address,
            }
        })
