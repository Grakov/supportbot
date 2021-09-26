from datetime import datetime, date
import os
import uuid
import json
from typing import Union

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User

from backend import settings as app_settings
from support.extras.containers import DictContainer
from support.extras.clients import CommentsField, KnownNamesField
from support.extras.location import deg2num, generate_tile_url, generate_map_url


class Files(models.Model):
    file_id = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH, null=True)
    uuid = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    file_name = models.TextField()
    size = models.BigIntegerField()
    original_name = models.TextField(null=True)
    uploaded = models.DateTimeField()
    last_viewed = models.DateTimeField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_touched = False

    @staticmethod
    def get(file_id: int):
        return Files.objects.filter(id=file_id).first()

    @staticmethod
    def get_by_uuid(file_uuid: str):
        return Files.objects.filter(uuid=file_uuid).first()

    @staticmethod
    def generate_uuid():
        file_uuid = str(uuid.uuid4())
        while Files.get_by_uuid(file_uuid) is not None:
            file_uuid = str(uuid.uuid4())

        return file_uuid

    @staticmethod
    def create(file_id, file_name, file_size, original_name):
        file_uuid = Files.generate_uuid()
        current_time = datetime.now()
        # TODO add free space check
        file = Files(file_id=file_id, uuid=file_uuid, size=file_size, original_name=original_name,
                     uploaded=current_time, last_viewed=None)
        file.save()
        return file

    def generate_file_path(self):
        file_path = os.path.join(app_settings.UPLOAD_DIR, str(self.uuid), str(self.file_name))
        return file_path

    def generate_file_url(self, silent=False):
        file_url = os.path.join(app_settings.UPLOAD_URL, str(self.uuid), str(self.file_name))

        # Fix to avoid multiple SQL UPDATE queries on one variable lifetime
        if not self.is_touched and not silent:
            self.mark_viewed()
            self.is_touched = True

        return file_url

    def mark_viewed(self):
        self.last_viewed = datetime.now()
        self.save(update_fields=['last_viewed'])

    def get_readable_size(self, value=None, base=1024):
        if value is None:
            value = self.size

        if value < 0:
            raise ValueError

        value = float(value)

        suffixes = ['B', 'KB', 'MB', 'GB']
        suffix_index = 0
        while value >= base and suffix_index < len(suffixes) - 1:
            value /= base
            suffix_index += 1

        return f"{round(value, 2)} {suffixes[suffix_index]}"


class Settings(models.Model):
    key = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    type = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    value = models.TextField()
    description = models.TextField()

    @staticmethod
    def get(key: str):
        setting = Settings.objects.filter(key=key).first()
        if setting is None:
            return None

        return setting

    @staticmethod
    def get_by_id(setting_id: int):
        return Settings.objects.filter(id=setting_id).first()

    def get_value(self, default_value=None, force_str_type=False):
        if self.type == 'str' or self.type == 'string':
            return self.value
        elif Settings.is_digit(self.value) and not force_str_type:
            if self.type == 'int':
                return int(self.value)
            elif self.type == 'bool':
                return int(self.value) == 1
            elif self.type == 'datetime':
                return datetime.fromtimestamp(self.value)
        else:
            if force_str_type:
                return str(self.value)
            else:
                return default_value

    @staticmethod
    def get_value_by_key(key: str, default_value=None, force_str_type=False):
        setting = Settings.get(key)
        if setting is None:
            return default_value

        return setting.get_value(default_value, force_str_type)

    def set_value(self, value, ignore_value_type=False):
        is_str_cast_supported = type(value).__str__ is not object.__str__
        if not is_str_cast_supported:
            raise TypeError('Type of passed value could not be casted to string')

        is_acceptable_value = False

        if self.type == 'str' or self.type == 'string':
            if isinstance(value, str):
                self.value = value
            elif ignore_value_type:
                self.value = str(value)
            is_acceptable_value = True
        elif self.type == 'int':
            if isinstance(value, int):
                self.value = str(value)
                is_acceptable_value = True
            elif isinstance(value, str) and self.is_digit(value):
                self.value = value
                is_acceptable_value = True
        elif self.type == 'bool':
            if isinstance(value, bool):
                self.value = '1' if value else '0'
                is_acceptable_value = True
            elif isinstance(value, str) and value in ['0', '1']:
                self.value = value
                is_acceptable_value = True
        elif self.type == 'datetime':
            if isinstance(value, datetime):
                self.value = str(datetime.timestamp())
                is_acceptable_value = True
            elif isinstance(value, str) and self.is_digit(value):
                self.value = value
                is_acceptable_value = True

        if not is_acceptable_value:
            raise TypeError('Type of passed value don\'t match field type')

        self.save()

    @staticmethod
    def all():
        return Settings.objects.all()

    @staticmethod
    def set_value_by_key(key: str, value, ignore_value_type=False):
        setting = Settings.get(key)
        if setting is None:
            raise KeyError(f'Setting for key \'{key}\' doesn\'t exist')

        setting.set_value(value, ignore_value_type)

    @staticmethod
    def is_digit(string):
        try:
            int(string)
            return True
        except ValueError:
            return False

    def is_system(self):
        return self.key.startswith('system.')

    @staticmethod
    def check_value(setting_value, setting_type):
        is_str_cast_supported = type(setting_value).__str__ is not object.__str__

        if not is_str_cast_supported:
            return False

        if setting_type == 'str' or setting_type == 'string':
            return True
        elif setting_type == 'int':
            if isinstance(setting_value, int):
                return True
            elif isinstance(setting_value, str) and Settings.is_digit(setting_value):
                return True
        elif setting_type == 'bool':
            if isinstance(setting_value, bool):
                return True
            elif isinstance(setting_value, str) and setting_value in ['0', '1']:
                return True
        elif setting_type == 'datetime':
            if isinstance(setting_value, datetime):
                return True
            elif isinstance(setting_value, str) and Settings.is_digit(setting_value):
                return True

        return False


class Clients(models.Model):
    source = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    uid = models.BigIntegerField()
    source_chat = models.BigIntegerField()
    username = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    avatar = models.ForeignKey(Files, on_delete=models.CASCADE)
    comments = CommentsField(null=True)
    first_name = models.CharField(null=True, max_length=settings.MAX_CHARFIELD_LENGTH)
    last_name = models.CharField(null=True, max_length=settings.MAX_CHARFIELD_LENGTH)
    name_history = KnownNamesField(null=True)
    phone_number = models.CharField(null=True, max_length=settings.MAX_CHARFIELD_LENGTH)
    is_blocked = models.BooleanField(null=False, default=False)

    @staticmethod
    def get(user_id: int):
        return Clients.objects.filter(id=user_id).first()

    def block(self):
        self.is_blocked = True
        self.save(update_fields=['is_blocked'])

    def unblock(self):
        self.is_blocked = False
        self.save(update_fields=['is_blocked'])

    def get_name(self):
        name = ''
        if self.first_name is not None or self.last_name is not None:
            if self.first_name is not None:
                name = self.first_name
            if self.last_name is not None:
                name += f' {self.last_name}'
        else:
            name = f'{self.source} {self.username}'
        return name

    def generate_link(self):
        if self.source == 'telegram':
            if self.username is not None:
                return f'https://t.me/{self.username}'
            else:
                return f'tg://user?id={self.uid}'

    def dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'uid': self.uid,
            'username': self.username,
            'avatar': self.avatar.generate_file_url(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.get_name(),
            'is_blocked': self.is_blocked,
            'link': self.generate_link(),
        }

    def json(self):
        return json.dumps(self.dict())


class Lines(models.Model):
    name = models.TextField()
    description = models.TextField(null=True)

    @staticmethod
    def get(line_id):
        return Lines.objects.filter(id=line_id).first()

    @staticmethod
    def all():
        return Lines.objects.all()

    @staticmethod
    def get_default_line():
        return Lines.get(1)

    def get_opened_chats_count(self):
        return Chats.get_opened_chats_count(self)

    def is_system(self):
        return self.id == 1

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_system': self.is_system(),
        }

    def json(self):
        return json.dumps(self.dict())


# @TODO add assigned_timestamp DATETIME
# @TODO add last_read_message -> Messages
class Chats(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, null=True, db_column='assignee')
    status = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    line = models.ForeignKey(Lines, on_delete=models.CASCADE)
    last_action = models.DateTimeField()

    @staticmethod
    def get(chat_id: int):
        return Chats.objects.filter(id=chat_id).first()

    @staticmethod
    def get_by_staff(staff_user):
        if staff_user is None:
            return

        return Chats.objects.filter(assignee=staff_user).order_by('-last_action').all()

    @staticmethod
    def get_by_staff_api(staff_user):
        assigned_chats = Chats.get_by_staff(staff_user)
        if assigned_chats is None:
            return []
        return [chat.id for chat in assigned_chats]

    @staticmethod
    def get_open_status_query():
        return Q(status='new') | Q(status='open')

    @staticmethod
    def get_opened_chats(line=None, assigned=False, reverse=False):
        if line is None:
            line = Lines.get(1)

        show_assigned = ~Q(assignee=None) if assigned else Q(assignee=None)

        opened_chats = Chats.objects.filter(Chats.get_open_status_query(), show_assigned, Q(line=line)).all()
        opened_chats = sorted(opened_chats,
                              key=lambda chat:
                                  (reverse if chat.status == 'new' else not reverse, chat.last_action),
                              reverse=reverse)
        return opened_chats

    @staticmethod
    def get_opened_chats_count(line=None, assigned=False):
        chats = Chats.get_opened_chats(line, assigned)
        if chats is None:
            return 0
        else:
            return len(chats)

    def get_last_real_message(self):
        return Messages.objects.filter(chat_id=self).exclude(is_service=True).order_by('-time').first()

    def get_last_message(self):
        return Messages.objects.filter(chat_id=self).order_by('-time').first()

    def dict(self):
        last_readable_message = self.get_last_real_message()
        last_readable_message_text = last_readable_message.text
        if len(last_readable_message_text) > 64:
            last_readable_message_text = last_readable_message_text[0:61] + '...'

        last_message = self.get_last_message()

        return {
            'id': self.id,
            'client': self.client.dict(),
            'assignee': None if self.assignee is None else StaffMeta.dict_short(self.assignee),
            'status': self.status,
            'line': self.line.dict(),
            'last_action': None if self.last_action is None else int(self.last_action.timestamp()),
            'last_action_str': self.get_last_action_str(),
            'last_readable_message': {
                'id': last_readable_message.id,
                'text': last_readable_message_text,
                'is_from_client': last_readable_message.staff is None,
            },
            'last_message': last_message.id,
        }

    def json(self):
        return json.dumps(self.dict())

    def get_last_action_str(self):
        today = date.today()
        last_message_time = self.last_action

        time_string = last_message_time.strftime("%d %b")
        if last_message_time.year != today.year:
            time_string += last_message_time.strftime(" %Y")
        if last_message_time.date() == today:
            time_string = last_message_time.strftime("%H:%M")

        return time_string

    def get_base_info(self):
        return {
            "chat": self,
            "last_message": self.get_last_real_message(),
            "time": self.get_last_action_str(),
        }

    @staticmethod
    def auto_assign(staff_user):
        if staff_user is None:
            return None

        limit = Settings.get_value_by_key(key='system.chats_limit')
        limit = int(limit) if limit is not None else None
        if limit is not None and len(Chats.get_by_staff(staff_user)) >= limit:
            return None

        chat = Chats.objects.filter(Chats.get_open_status_query(), assignee=None, line=staff_user.meta.line).\
            order_by('last_action').first()
        if chat is not None:
            chat.unassign(staff_user)
            chat.assign(staff_user)
        return chat

    def assign(self, staff_user):
        if not isinstance(staff_user, User) and staff_user is not None:
            raise Exception(f"Invalid type of staff_user: {type(staff_user)}, {type(User)} or None expected")

        if self.assignee != staff_user:
            self.assignee = staff_user
            self.save()

            if staff_user is not None:
                message_text = f"{staff_user.username} назначил обращение на себя"
                Messages.send(client=None, staff=staff_user, chat=self, is_service=True, time=datetime.now(),
                              text=message_text, attachments=[], markdown=False)

    def unassign(self, staff_user):
        assignee = self.assignee

        if assignee is not None:
            self.assign(None)

            message_text = f"{staff_user.username} снял обращение с "
            if staff_user != assignee:
                message_text += assignee.username
            else:
                message_text += 'себя'
            Messages.send(client=None, staff=staff_user, chat=self, is_service=True, time=datetime.now(),
                          text=message_text, attachments=[], markdown=False)

    def touch(self, time=datetime.now()):
        self.last_action = time
        self.save()

    def set_status(self, status, staff_user=None):
        if self.status != status:
            self.status = status
            self.save()

            if staff_user is not None:
                message_text = f"{staff_user.username} "
                if status == 'closed':
                    message_text += f"закрыл обращение"
                else:
                    message_text += f"открыл обращение"

                Messages.send(client=None, staff=staff_user, chat=self, is_service=True, time=datetime.now(),
                              text=message_text, attachments=[], markdown=False)

    def set_line(self, line, staff_user=None, silent=False):
        if self.line != line:
            self.line = line
            self.save()

        if not silent:
            if staff_user is not None:
                message_text = f'{staff_user.username} перевёл обращение в очередь {line.name} ({line.id})'
            else:
                message_text = f'Обращение переведено в очередь {line.name} ({line.id})'

            Messages.send(client=None, staff=staff_user, chat=self, is_service=True, time=datetime.now(),
                          text=message_text, attachments=[], markdown=False)

    @staticmethod
    def replace_line(needle, new_line):
        chats = Chats.objects.filter(line=needle).all()
        for chat in chats:
            chat.set_line(new_line)


# Messages related classes
# @TODO add check for $exceptionType field existence on check_dict or append function
class AttachmentsContainer(DictContainer):
    def __init__(self, str_obj=None):
        super().__init__(str_obj, required_fields=['type'])

    # some fixes :(
    def append(self, dict_obj: dict):
        if super().append(dict_obj):
            if 'file_id' in dict_obj:
                file_id = dict_obj['file_id']
                file_object = Files.get(file_id)

                if file_object is not None:
                    dict_obj['file'] = file_object

            if dict_obj['type'] == 'location':
                loc_zoom = settings.LOCATION_TILE_TARGET
                loc_latitude = dict_obj['location']['latitude']
                loc_longitude = dict_obj['location']['longitude']
                loc_title = dict_obj['location'].get('title', None)
                loc_address = dict_obj['location'].get('address', None)

                loc_x, loc_y = deg2num(loc_latitude, loc_longitude, loc_zoom)
                tile_url = generate_tile_url(loc_x, loc_y, loc_zoom)
                map_url = generate_map_url(loc_latitude, loc_longitude, loc_zoom, title=loc_title, address=loc_address)

                dict_obj['location']['tile_url'] = tile_url
                dict_obj['location']['map_url'] = map_url

            if dict_obj['type'] == 'video':
                if 'video' in dict_obj and 'thumb' in dict_obj['video'] and 'file_id' in dict_obj['video']['thumb']:
                    thumb_file_id = dict_obj['video']['thumb']['file_id']
                    dict_obj['video']['thumb']['file'] = Files.get(thumb_file_id)

            return True
        else:
            return False

    def find_attachments(self, requested_type, limit=None):
        results = []
        for attachment in self.container:
            attachment_type = attachment.get("type", None)
            if attachment_type is not None and attachment_type == requested_type:
                results.append(attachment)
                if limit is not None and len(results) >= limit:
                    break
        return results

    def find_exceptions(self, limit=None):
        return self.find_attachments("exception", limit)


class AttachmentsField(models.TextField):
    description = "Wrapper for parsing/encoding attachments"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        return AttachmentsContainer(str_obj=value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj: Union[AttachmentsContainer, list]):
        if type(obj) is list:
            return json.dumps(obj)
        else:
            return str(obj)

    def get_prep_value(self, value: Union[AttachmentsContainer, list]):
        return self.value_to_string(value)


class Messages(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    chat = models.ForeignKey(Chats, on_delete=models.CASCADE)
    is_service = models.BooleanField(null=False, default=False)
    time = models.DateTimeField()
    text = models.TextField(null=True)
    attachments = AttachmentsField(null=True)
    markdown = models.BooleanField(default=False)

    @staticmethod
    def send(client: Union[Clients, None], staff, chat: Chats, is_service: bool, time: datetime, text: Union[str, None],
             attachments, markdown: bool):
        message = Messages(client=client, staff=staff, chat=chat, is_service=is_service, time=time,
                           text=text, attachments=attachments, markdown=markdown)
        message.save()
        if not is_service:
            chat.set_status('answered')
            chat.touch(time)
        return message

    @staticmethod
    def get(chat_obj: Chats, before=None, after=None, reverse=False):
        if chat_obj is None:
            return []
        query = Messages.objects.filter(chat=chat_obj)

        if after is not None:
            query = query.filter(id__gt=after)

        if before is not None:
            query = query.filter(id__lt=before)

        if reverse:
            query = query.order_by('-id')

        return query.all()


class StaffMeta(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meta', primary_key=True)
    role = models.CharField(max_length=settings.MAX_CHARFIELD_LENGTH)
    line = models.ForeignKey(Lines, on_delete=models.CASCADE)
    avatar = models.ForeignKey(Files, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(null=True)

    @staticmethod
    def get(user_obj: Union[User, None]):
        if user_obj is None:
            return None
        return StaffMeta.objects.filter(user=user_obj).first()

    @staticmethod
    def dict(user: User):
        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'email': user.email,
            'avatar': user.meta.avatar.generate_file_url(),
            'role': user.meta.role,
            'line': user.meta.line.id,
            'is_blocked': not user.is_active,
            'is_online': user.meta.is_online(),
            'last_seen': user.meta.last_seen,
        }

    @staticmethod
    def dict_short(user: User):
        if user is None:
            return None

        return {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'avatar': user.meta.avatar.generate_file_url(),
            'line': user.meta.line.id,
            'is_online': user.meta.is_online(),
            'last_seen': user.meta.last_seen,
        }

    @staticmethod
    def get_by_id(user_id: int):
        return StaffMeta.get(User.objects.filter(id=user_id).first())

    def is_admin(self):
        return self.role == 'administrator'

    def is_online(self):
        pass

    def touch(self):
        pass
