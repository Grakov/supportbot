import json


class DictFilter:
    """
    DictFilter contains info about encode/decode functions for fields in DictContainer

    For example you can store some dict in DB as JSON string. One filed contains datetime, stored as int in JSON string.
    And you want to use it as datetime in your code. So, encode/decode values will be as listed below:
        decode = datetime.datetime.fromtimestamp
        encode = datetime.timestamp

    filed_type provides additional cast call while encoding.
    For this example, datetime.timestamp returns float value. So, you can cast float timestamp to int:
        filed_type = int
    """
    def __init__(self, decode, encode, field_type, field_name):
        self.encode = encode
        self.decode = decode
        self.field_type = field_type
        self.field_name = field_name


class DictContainer:
    """
    Class used for storing list of dicts, parsed from JSON string
    Allows to check, if required fields are defined in passed dicts, and cast data on their fields from JSON to needed
    types (and vice versa, while casting DictContainer to JSON string)

    Used for custom typed DB fields: Messages.attachments, Clients.comments, Clients.name_history
    """
    def __init__(self, str_obj=None, required_fields=[], filters=[]):
        self.container = []
        self.required_fields = required_fields
        self.filters = filters
        if str_obj is not None:
            dict_list = json.loads(str_obj)

            if isinstance(dict_list, list):
                for dict_obj in dict_list:
                    if isinstance(dict_obj, dict):
                        self.append(self.filter_dict(dict_obj))

    def append(self, dict_obj: dict):
        if self.check_dict(dict_obj):
            self.container.append(dict_obj)
            return True
        else:
            return False

    def remove(self, index: int):
        if 0 <= index < len(self):
            del self.container[index]

    def all(self):
        return self.container

    '''
    Function for checking if passed dictionary contains all required fields for container data type
    '''
    def check_dict(self, dict_obj):
        for field in self.required_fields:
            if field not in dict_obj:
                return False
        return True

    '''
    Converting single dict fields by types, listed in DictContainer.filters (encode/decode)
    '''
    def filter_dict(self, dict_obj, encode=False):
        result = dict_obj.copy()
        for dict_filter in self.filters:
            if dict_filter.field_name in result:
                if encode:
                    result[dict_filter.field_name] = dict_filter.encode(result.get(dict_filter.field_name))
                    if dict_filter.field_type is not None:
                        result[dict_filter.field_name] = dict_filter.field_type(result.get(dict_filter.field_name))
                else:
                    result[dict_filter.field_name] = dict_filter.decode(result.get(dict_filter.field_name))
        return result

    def __len__(self):
        return len(self.container)

    def __str__(self):
        result_container = []
        for dict_obj in self.container:
            result_container.append(self.filter_dict(dict_obj, encode=True))

        return json.dumps(result_container)
