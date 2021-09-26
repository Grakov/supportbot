from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, Boolean, ForeignKey

import config

Base = declarative_base()


class SettingsTable(Base):
    __tablename__ = f'{config.MYSQL_PREFIX}settings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(config.MAX_VARCHAR_LENGTH), nullable=False)
    type = Column(String(config.MAX_VARCHAR_LENGTH), nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)

    def __repr__(self):
        return f"{self.key} = {self.value}"


class ClientsTable(Base):
    __tablename__ = f'{config.MYSQL_PREFIX}clients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(config.MAX_VARCHAR_LENGTH), nullable=False)
    uid = Column(BigInteger, nullable=False)
    source_chat = Column(BigInteger, nullable=False)
    username = Column(String(config.MAX_VARCHAR_LENGTH), nullable=False)
    avatar_id = Column(Integer, nullable=False)
    comments = Column(Text)
    first_name = Column(String(config.MAX_VARCHAR_LENGTH))
    last_name = Column(String(config.MAX_VARCHAR_LENGTH))
    name_history = Column(Text)
    phone_number = Column(String(config.MAX_VARCHAR_LENGTH))
    is_blocked = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        name = ""
        if self.first_name is not None:
            name += self.first_name
        if self.last_name is not None:
            name += f" {self.last_name}"
        if self.username is not None:
            name += f" @{self.username}"
        return f"{name} ({self.source}:{self.uid})"


class LinesTable(Base):
    __tablename__ = f'{config.MYSQL_PREFIX}lines'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text)


class ChatsTable(Base):
    __tablename__ = f'{config.MYSQL_PREFIX}chats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer)
    assignee = Column(Integer, nullable=True)
    status = Column(String(config.MAX_VARCHAR_LENGTH))
    line_id = Column(Integer, ForeignKey(f'{LinesTable.__tablename__}.id'), nullable=False)
    last_action = Column(DateTime)

    def __repr__(self):
        return f"{self.client_id} ({self.level}) {self.status} {self.last_action.isoformat(sep=' ', timespec='seconds')}"


class MessagesTable(Base):
    __tablename__ = f'{config.MYSQL_PREFIX}messages'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(Integer, nullable=True)
    staff_id = Column(Integer, nullable=True)
    chat_id = Column(Integer, nullable=False)
    is_service = Column(Boolean, nullable=False, default=False)
    time = Column(DateTime, nullable=False)
    text = Column(Text, nullable=True)
    attachments = Column(Text)
    markdown = Column(Boolean, default=False)

    def __repr__(self):
        return f"{self.id}: {self.client_id} {self.time.isoformat(sep=' ', timespec='seconds')} {self.is_service}"


class FilesTable(Base):
    __tablename__ = f'{config.MYSQL_PREFIX}files'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(String(config.MAX_VARCHAR_LENGTH), nullable=False)
    file_id = Column(String(config.MAX_VARCHAR_LENGTH), nullable=True)
    file_name = Column(Text, nullable=False)
    size = Column(BigInteger, nullable=False)
    original_name = Column(Text)
    uploaded = Column(DateTime, nullable=False)
    last_viewed = Column(DateTime)

    def __repr__(self):
        return f"{self.id} ({self.file_id})\n{self.hash}\n{self.file_name}\n" + \
               f"{self.uploaded.isoformat(sep=' ', timespec='seconds')}"
