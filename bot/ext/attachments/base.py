from abc import ABC
import json


class Base(ABC):
    attachment_type = 'base'
    attachment_object = dict()

    def get_file_id(self):
        return self.attachment_object.file_id

    def get_size(self):
        return self.file_size

    def get_readable_size(self, value=None, base=1024):
        if value is None:
            value = self.get_size()

        if value < 0:
            raise ValueError

        value = float(value)

        suffixes = ['B', 'KB', 'MB', 'GB']
        suffix_index = 0
        while value >= base and suffix_index < len(suffixes) - 1:
            value /= base
            suffix_index += 1

        return f"{round(value, 2)} {suffixes[suffix_index]}"

    def set_file_name(self, file_name):
        self.attachment_object["file_name"] = file_name

    def __str__(self):
        return json.dumps(self.attachment_object)

    def __repr__(self):
        return self.__str__()

    def convert_to_dict(self):
        self.attachment_object = dict({
            "type": self.attachment_type
        })

    def dict(self):
        return self.attachment_object

    def update(self, items: dict):
        self.attachment_object.update(items)

    def __dict__(self):
        return self.dict()


class AttachmentEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Base) or issubclass(obj, Base):
            return obj.dict()
        return json.JSONEncoder.default(self, obj)
