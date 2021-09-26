import os
from typing import Union
from datetime import datetime
from enum import Enum
from shutil import copy2
import re

from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

from support.models import Files, Lines, StaffMeta
from backend import settings as app_settings


class StaffRoles(Enum):
    support = 'support'
    administrator = 'administrator'


def create_staff(username: str, first_name: str, last_name: Union[str, None], email: str, password: str,
                 avatar: Union[Files, None], role=StaffRoles.support.value, line=None) -> User:
    if avatar is None:
        avatar_uuid = Files.generate_uuid()
        avatar_filename = 'avatar.png'
        avatar_size = os.path.getsize(app_settings.DEFAULT_AVATAR_PATH)
        avatar = Files(file_id=None, uuid=avatar_uuid, file_name=avatar_filename, size=avatar_size,
                       original_name=avatar_filename, uploaded=datetime.now(), last_viewed=None)

        avatar_file_path = avatar.generate_file_path()
        os.makedirs(os.path.dirname(avatar_file_path), exist_ok=True)
        copy2(app_settings.DEFAULT_AVATAR_PATH, avatar_file_path)

        # save new avatar
        avatar.save()
    if line is None:
        line = Lines.get_default_line()

    user_group = None
    is_superuser = False
    if role == StaffRoles.support.value:
        user_group = Group.objects.get(name='support')
    elif role == StaffRoles.administrator.value:
        user_group = Group.objects.get(name='administrator')
        is_superuser = True

    with transaction.atomic():
        new_user = User(username=username, first_name=first_name, last_name=last_name, email=email, is_active=True,
                        is_superuser=is_superuser, is_staff=True)
        new_user.set_password(password)
        meta = StaffMeta(user=new_user, role=role, line=line, avatar=avatar, last_seen=None)
        new_user.save()
        new_user.groups.add(user_group)
        new_user.save()
        meta.save()

    return new_user


def check_username(username):
    pattern = r'^[a-zA-Z0-9_]{3,}$'
    return True if re.match(pattern, username) else False
