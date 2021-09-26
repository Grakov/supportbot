import json
import datetime
from threading import Thread
import requests

import pika
import sqlalchemy
import pymysql
from telebot import types
from telebot.apihelper import ApiTelegramException
import html

import config
from bot import bot
from models import ClientsTable, ChatsTable, MessagesTable, FilesTable, LinesTable
from db import get_db_session
from app_settings import app_settings
from ext.attachments import photo, exception, video, document, contact, location, container, downloadable
from ext.files import get_profile_avatar, download_avatar, is_file_upload_enabled, generate_path


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Здравствуйте!\n\n" +
                     "Вы можете задать интересующий вас вопрос здесь и наши специалисты ответят как можно быстрее " +
                     "(или нет, это тестовый бот).\n\n" +
                     "Можете ответить себе самостоятельно: ")


@bot.message_handler(func=lambda m: True, content_types=config.CONTENT_TYPES)
def process_message_wrapper(message: types.Message, attempts_count=1):
    if attempts_count == 4:
        return

    try:
        db_session = get_db_session()
        process_message(message, db_session)
    except (requests.exceptions.ConnectionError, sqlalchemy.exc.SQLAlchemyError, ApiTelegramException, pymysql.err.MySQLError, Exception) as e:
        print(e)

        if issubclass(type(e), (sqlalchemy.exc.SQLAlchemyError, pymysql.err.MySQLError)):
            print(e)
            db_session.close()

        print(f'Trying to get message one more time: retry {attempts_count + 1}')
        process_message_wrapper(message, attempts_count + 1)


def process_message(message: types.Message, db_session):
    message_text = ""
    message_time = datetime.datetime.fromtimestamp(message.date)
    is_service = False
    attachments = container.AttachmentsContainer()

    source_chat = message.chat.id
    user: types.User = message.from_user

    # get user object
    client_obj = db_session.query(ClientsTable).filter(ClientsTable.uid == user.id).first()

    # @TODO SANITIZE ALL STRINGS WITH TG USER DATA VIA html.escape/django.utils.html.escape !!!
    # Meh, we can't get user phone number
    if client_obj is None:
        username = html.escape(user.username) if user.username is not None else None
        first_name = html.escape(user.first_name) if user.first_name is not None else None
        last_name = html.escape(user.last_name) if user.last_name is not None else None
        avatar = download_avatar(bot, user)

        client_obj = ClientsTable(source='telegram', uid=user.id, source_chat=source_chat, username=username,
                                  avatar_id=avatar, comments='[]', first_name=first_name,
                                  last_name=last_name, name_history='[]', phone_number=None, is_blocked=False)
        db_session.add(client_obj)
        db_session.commit()

    else:
        # Downloading user avatar
        current_avatar = get_profile_avatar(bot, user)
        user_avatar = db_session.query(FilesTable).filter(FilesTable.id == client_obj.avatar_id).first()

        if user_avatar is not None and user_avatar.file_id is not None and user_avatar.file_id != current_avatar.file_id or \
                (user_avatar is None or user_avatar.file_id is None) and current_avatar is not None and is_file_upload_enabled():
            client_obj.avatar_id = download_avatar(bot, user)
            db_session.commit()

    # KnowNames
    if client_obj.name_history is None:
        client_obj.name_history = '[]'
        db_session.commit()

    known_names = json.loads(client_obj.name_history)
    current_firstname = html.escape(user.first_name) if user.first_name is not None else None
    current_lastname = html.escape(user.last_name) if user.last_name is not None else None

    if current_firstname != client_obj.first_name or current_lastname != client_obj.last_name:
        previous_firstname = client_obj.first_name
        previous_lastname = client_obj.last_name
        client_obj.first_name = current_firstname
        client_obj.last_name = current_lastname

        previous_name = previous_firstname if previous_firstname is not None else ''
        previous_name += (' ' + previous_lastname) if previous_lastname is not None else ''

        is_found = False
        for entry in known_names:
            if issubclass(type(entry), dict) and entry.get('name', None) == previous_name:
                is_found = True
                break

        if not is_found:
            known_names.append({
                'name': previous_name,
                'timestamp': datetime.datetime.now().timestamp(),
            })
            client_obj.name_history = json.dumps(known_names)

        db_session.commit()

    # Check if username was changed
    if user.username != client_obj.username:
        client_obj.username = user.username
        db_session.commit()

    chat_obj = db_session.query(ChatsTable).filter(ChatsTable.client_id == client_obj.id).first()

    # @TODO add enum for chat statuses
    if chat_obj is None:
        default_line = db_session.query(LinesTable).filter(LinesTable.id == 1).first()
        chat_obj = ChatsTable(client_id=client_obj.id, assignee=None, status='new', line_id=default_line.id,
                              last_action=message_time)
        db_session.add(chat_obj)
    else:
        # @TODO technically this is shit - we need use enums
        if chat_obj.status == 'closed':
            chat_obj.status = 'new'
        elif chat_obj.status != 'new':
            chat_obj.status = 'open'
        chat_obj.last_action = message_time
    db_session.commit()

    # Check if client has been banned
    if client_obj.is_blocked:
        bot.send_message(message.chat.id, "Ваш аккаунт заблокирован")
        return

    # Get attachments
    if message.content_type == 'text':
        message_text = message.text.strip()

    elif message.content_type == 'photo':
        photo_obj = photo.Photo.get_largest_photo(message.photo)
        attachments.append(photo.Photo(photo_obj))

    elif message.content_type == 'video':
        video_obj = video.Video(message.video)
        attachments.append(video_obj)

    elif message.content_type == 'document':
        document_obj = document.Document(message.document)
        attachments.append(document_obj)

    elif message.content_type == 'location':
        attachments.append(location.Location(message.location))

    elif message.content_type == 'venue':
        venue_obj = message.venue
        location_obj = location.Location(venue_obj.location, title=venue_obj.title, address=venue_obj.address)
        attachments.append(location_obj)

    elif message.content_type == 'contact':
        attachments.append(contact.Contact(message.contact))

    else:
        attachments.append(exception.AttachmentException(
            exception.BasicBotExceptions["not_supported_attachment"]
        ))

    # download attachments
    for attachment in attachments.all():
        if issubclass(type(attachment), downloadable.DownloadableAttachment):
            try:
                attachment.download()
                if attachment.attachment_type == 'video':
                    attachment.video_thumb.download()
            except downloadable.FileSizeLimitExceededException:
                file_size_limit = attachment.get_readable_size(
                    value=app_settings.get('download_file_size_limit',
                                           default_value=config.TELEGRAM_API_FILE_DOWNLOAD_LIMIT)
                )
                attachments.remove(attachment)
                attachments.append(exception.AttachmentException(
                    exception.BasicBotExceptions["file_size_limit_exceeded"],
                    [file_size_limit]
                ))
            except downloadable.FileDownloadDisabledException:
                attachments.remove(attachment)
                attachments.append(exception.AttachmentException(
                    exception.BasicBotExceptions["file_download_disabled"]
                ))
            except downloadable.FreeSpaceLimitExceededException:
                attachments.remove(attachment)
                attachments.append(exception.AttachmentException(
                    exception.BasicBotExceptions["free_space_limit_exceeded"]
                ))

    if len(attachments) > 0:
        if message.caption is not None:
            message_text = message.caption

        exception_attachment = attachments.find_exception()
        if exception_attachment is not None:
            if exception_attachment.exception_public_description is not None:
                bot.send_message(message.chat.id, exception_attachment.get_public_description())

            if exception_attachment.exception_private_description is not None:
                is_service = True
            else:
                print('Attached exception has not both public and private description: unhandled exception')
                return

    # HTML-escape
    message_text = html.escape(message_text)

    if source_chat != client_obj.source_chat:
        client_obj.source_chat = source_chat
        db_session.commit()

    # write data to MySQL
    message = MessagesTable(client_id=client_obj.id, staff_id=None, chat_id=chat_obj.id, is_service=is_service,
                            time=message_time, text=message_text, attachments=str(attachments), markdown=False)
    db_session.add(message)
    db_session.commit()
    db_session.close()
    # @TODO Post data to RabbitMQ


def send_message_wrapper(channel: pika.channel.Channel, method: pika.spec.Basic.Deliver,
                         properties: pika.spec.BasicProperties, body: bytes, attempts_count=1):
    if attempts_count == 4:
        return

    try:
        db_session = get_db_session()
        send_message(body, db_session)
    except (requests.exceptions.ConnectionError, sqlalchemy.exc.SQLAlchemyError, ApiTelegramException, pymysql.err.MySQLError) as e:
        print(e)

        if issubclass(type(e), (sqlalchemy.exc.SQLAlchemyError, pymysql.err.MySQLError)):
            db_session.close()

        print(f'Trying to send message one more time: retry {attempts_count + 1}')
        send_message_wrapper(channel, method, properties, body, attempts_count + 1)


# Sending reply message
def send_message(body: bytes, db_session):
    message_id = body.decode("utf-8")
    if not message_id.isnumeric():
        return

    message_id = int(message_id)

    message_obj: MessagesTable = db_session.query(MessagesTable).filter(MessagesTable.id == message_id).\
        with_for_update().populate_existing().first()
    if message_obj is None:
        print(f"Missed message! id={message_id}")
        return

    chat_obj: ChatsTable = db_session.query(ChatsTable).filter(ChatsTable.id == message_obj.chat_id).first()
    if chat_obj is None:
        return

    user_obj: ClientsTable = db_session.query(ClientsTable).filter(ClientsTable.id == chat_obj.client_id).first()
    if user_obj is None:
        return

    parse_mode = None
    if message_obj.markdown:
        parse_mode = "Markdown"

    attachments = json.loads(message_obj.attachments)
    if len(attachments) == 0 and len(message_obj.text) > 0:
        bot.send_message(user_obj.source_chat, message_obj.text, parse_mode=parse_mode)
    else:
        media_container = list()
        documents_container = list()
        location_container = list()

        is_first_attachment = True
        for attachment in attachments:
            attachment_type = attachment.get('type', None)

            if attachment_type != 'location':
                db_session.commit()
                file_obj = db_session.query(FilesTable).filter(FilesTable.id == attachment.get('file_id', None)).first()
                file_path = generate_path(file_name=file_obj.file_name, file_uuid=file_obj.uuid)
                file_resource = open(file_path, 'rb')

                if attachment_type == 'photo':
                    media_container.append(types.InputMediaPhoto(file_resource,
                                                                 caption=message_obj.text if is_first_attachment else None))
                elif attachment_type == 'video':
                    media_container.append(types.InputMediaVideo(file_resource,
                                                                 caption=message_obj.text if is_first_attachment else None))
                elif attachment_type == 'document':
                    documents_container.append(types.InputMediaDocument(file_resource,
                                                                        caption=message_obj.text if is_first_attachment else None))

                if is_first_attachment:
                    is_first_attachment = False
            else:
                location_obj = attachment.get('location', None)
                if location_obj is None:
                    return

                latitude = location_obj.get('latitude')
                longitude = location_obj.get('longitude')

                title = location_obj.get('title', None)
                if title is not None:
                    title = html.unescape(title)

                address = location_obj.get('address', None)
                if address is not None:
                    address = html.unescape(address)

                location_container.append({
                    'latitude': latitude,
                    'longitude': longitude,
                    'title': title,
                    'address': address,
                })

        # TODO fix 10 attachments limit
        if len(media_container) > 0:
            bot.send_media_group(user_obj.source_chat, media_container)

        if len(documents_container) > 0:
            bot.send_media_group(user_obj.source_chat, documents_container)

        if is_first_attachment and len(message_obj.text) > 0:
            bot.send_message(user_obj.source_chat, message_obj.text, parse_mode=parse_mode)

        for venue in location_container:
            bot.send_venue(user_obj.source_chat, latitude=venue.get('latitude'), longitude=venue.get('longitude'),
                           title=venue.get('title'), address=venue.get('address'))

    db_session.close()


def pika_receiver(bot_config, callback):
    # Pika setup
    pika_receiver_connection = pika.BlockingConnection(
        pika.ConnectionParameters(config.RABBITMQ_HOST, config.RABBITMQ_PORT)
    )
    pika_receiver_channel = pika_receiver_connection.channel()
    queue_name = bot_config.RABBITMQ_QUEUE_NAMES['backend2bot']
    pika_receiver_channel.queue_declare(queue=queue_name)
    pika_receiver_channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    try:
        pika_receiver_channel.start_consuming()
    except KeyboardInterrupt:
        pika_receiver_channel.stop_consuming()
    pika_receiver_connection.close()


if __name__ == "__main__":
    pika_receiver_thread = Thread(target=pika_receiver, args=(config, send_message_wrapper, ))

    try:
        pika_receiver_thread.start()
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        bot.stop_polling()
        pika_receiver_thread.join()
        exit()
