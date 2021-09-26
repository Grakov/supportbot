import os
from uuid import uuid4
from shutil import copy2
from datetime import datetime

import config
from db import db_session
from app_settings import app_settings
from models import FilesTable, ClientsTable
from ext.attachments import photo


def generate_uuid():
    file_uuid = str(uuid4())
    while db_session.query(FilesTable).filter(FilesTable.uuid == file_uuid).first() is not None:
        file_uuid = str(uuid4())

    return file_uuid


def generate_path(file_name, file_uuid):
    file_dir = os.path.join(config.UPLOAD_DIR, file_uuid)
    file_path = os.path.join(file_dir, file_name)
    return file_path


# TODO add check for free space
def create_file_from_disk(file_path, new_file_name):
    file_uuid = generate_uuid()
    new_file_path = generate_path(new_file_name, file_uuid)
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    copy2(file_path, new_file_path)
    new_file_size = os.path.getsize(new_file_path)
    new_file_object = FilesTable(uuid=file_uuid, file_id=None, file_name=new_file_name, size=new_file_size,
                                 original_name=new_file_name, uploaded=datetime.now(), last_viewed=None)
    db_session.add(new_file_object)
    db_session.commit()

    return new_file_object


def is_file_upload_enabled():
    return app_settings.get('system.file_download_enabled', False)


def get_profile_avatar(bot, user):
    user_avatar_photos = bot.get_user_profile_photos(user.id)
    if user_avatar_photos.total_count > 0:
        return photo.Photo(photo.Photo.get_largest_photo(user_avatar_photos.photos[0]))
    else:
        return None


def create_avatar_from_disk():
    avatar_file = create_file_from_disk(config.DEFAULT_AVATAR_PATH, 'avatar.png')
    return avatar_file.id


def download_avatar(bot, user):
    if is_file_upload_enabled():
        try:
            user_avatar = get_profile_avatar(bot, user)
            if user_avatar is not None:
                user_avatar.download()
                return user_avatar.dict().get('file_id', None)
        except Exception as e:
            print(e)

    return create_avatar_from_disk()
