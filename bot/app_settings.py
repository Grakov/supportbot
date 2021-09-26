from datetime import datetime

from db import db_session
from models import SettingsTable


class AppSettings:
    def __init__(self):
        self.storage = list()
        self.refresh()

    def find(self, key):
        for row in self.storage:
            if row.key == key:
                return row

        return None

    def get(self, key, default_value=None, force_str_type=False):
        '''
        Get setting value from the storage
        :param key: setting key
        :param default_value: value what will be return if setting key does not exists or value type not equals setting type
        :param force_str_type: don't cast value from storage to setting value-type
        :return: setting value (str, int, bool, datetime)
        '''
        row = self.find(key)

        if row is None or row.value is None:
            return default_value

        value_type = row.type
        value = row.value
        if value_type == 'str' or value_type == 'string':
            return value
        elif self.is_digit(value) and not force_str_type:
            if value_type == 'int':
                return int(value)
            elif value_type == 'bool':
                return int(value) == 1
            elif value_type == 'datetime':
                return datetime.fromtimestamp(value)
        else:
            if force_str_type:
                return value
            else:
                return default_value

    def set(self, key, value, fallback_value='', ignore_value_type=False):
        '''
        Edit existing (only) setting
        :param key: key
        :param value: new value
        :param fallback_value: value, what will be stored, if passed value type has no __str__ function
        :param ignore_types: force writing value as string without proper casting
        :return:
        '''
        row = self.find(key)

        value_type = row.type
        is_str_cast_supported = type(value).__str__ is not object.__str__
        if not is_str_cast_supported:
            row['value'] = fallback_value
        elif value_type == 'str' or value_type == 'string':
            if type(value) is str:
                row['value'] = value
            elif ignore_value_type:
                row['value'] = str(value)
        elif value_type == 'int' and type(value) is int:
            row['value'] = str(value)
        elif value_type == 'bool' and type(value) is bool:
            row['value'] = '1' if value else '0'
        elif value_type == 'datetime' and issubclass(type(value), datetime):
            row['value'] = value.timestamp()
        else:
            row['value'] = str(value)

        db_session.commit()

    def refresh(self):
        self.storage = db_session.query(SettingsTable).all()

    @staticmethod
    def is_digit(string):
        try:
            int(string)
            return True
        except ValueError:
            return False


app_settings = AppSettings()
