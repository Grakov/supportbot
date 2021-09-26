import html

from ext.attachments.base import Base
from telebot import types


class Contact(Base):
    attachment_type = 'contact'

    def __init__(self, contact: types.Contact):
        self.file_id = None
        self.file_size = 0
        self.contact_phone_number = html.escape(contact.phone_number)
        self.contact_first_name = html.escape(contact.first_name)
        self.contact_last_name = html.escape(contact.last_name)
        self.contact_user_id = contact.user_id
        self.convert_to_dict()
        self.update({
            self.attachment_type: {
                "phone_number": self.contact_phone_number,
                "first_name": self.contact_first_name,
                "last_name": self.contact_last_name,
                "user_id": self.contact_user_id
            }
        })
