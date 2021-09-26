import json
from datetime import datetime

from django.db import models
from support.extras.containers import DictContainer, DictFilter


class CommentsField(models.TextField):
    description = "Wrapper for parsing/encoding comments of clients' accounts"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # TODO remove username field
    def to_python(self, value):
        return DictContainer(str_obj=value, required_fields=["text", "author_id", "username", "timestamp"],
                             filters=[
                                 DictFilter(decode=datetime.fromtimestamp, encode=datetime.timestamp, field_type=int,
                                            field_name="timestamp")
                             ])

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj: DictContainer):
        return str(obj)

    def get_prep_value(self, value: DictContainer):
        return self.value_to_string(value)


class KnownNamesField(models.TextField):
    description = "Wrapper for parsing/encoding known names of clients' accounts"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return DictContainer(str_obj=value, required_fields=["name", "timestamp"],
                             filters=[
                                 DictFilter(decode=datetime.fromtimestamp, encode=datetime.timestamp, field_type=int,
                                            field_name="timestamp")
                             ])

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj: DictContainer):
        return str(obj)

    def get_prep_value(self, value: DictContainer):
        return self.value_to_string(value)
