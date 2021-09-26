import json

from ext.attachments.exception import AttachmentException
from ext.attachments.base import Base, AttachmentEncoder


class AttachmentsContainer:
    def __init__(self):
        self.container = []

    def __len__(self):
        return len(self.container)

    def all(self):
        return self.container

    def append(self, attachment):
        if issubclass(type(attachment), Base):
            self.container.append(attachment)

    def remove(self, item):
        if item in self.container:
            self.container.remove(item)

    def pop(self, pos: int):
        return self.container.pop(pos)

    def length(self):
        return self.__len__()

    def find_exception(self):
        for attachment in self.container:
            if isinstance(attachment, AttachmentException):
                return attachment
        return None

    def __str__(self):
        return json.dumps(self.container, cls=AttachmentEncoder)

    def __repr__(self):
        return self.__str__()
