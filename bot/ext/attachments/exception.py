from ext.attachments.base import Base

BasicBotExceptions = dict({
    "not_supported_attachment": {
        "name": "not_supported_attachment",
        "private_description": None,
        "public_description":
            "К сожалению, данный тип вложения не поддерживается.\n" +
            "Разрешены к отправке: изображения, видео, документы, контакты и геолокация.\n" +
            "Или отправьте текстовое сообщение."
    },
    "file_size_limit_exceeded": {
        "name": "file_size_limit_exceeded",
        "private_description": None,
        "public_description":
            "К сожалению, отправленный файл слишком большой.\n" +
            "Лимит размера файла - {}"
    },
    "file_download_disabled": {
        "name": "file_download_disabled",
        "private_description": None,
        "public_description":
            "Загрузка файлов отключена.\n" +
            "Попробуйте разместить файл в каком-либо облачном хранилище и отправьте ссылку для его загрузки в чат."
    },
    "free_space_limit_exceeded": {
        "name": "free_space_limit_exceeded",
        "private_description": "Не удалось загрузить пользовательский файл: закончилось свободное место.",
        "public_description":
            "К сожалению, нам не удалось скачать данный файл.\n" +
            "Попробуйте отправить его снова через некоторое время."
    },
    "file_download_failed": {
        "name": "file_download_failed",
        "private_description": None,
        "public_description":
            "К сожалению, нам не удалось скачать данный файл.\n" +
            "Попробуйте отправить его снова через некоторое время."
    },
    "internal_bot_error": {
        "name": "internal_bot_error",
        "private_description": "",
        "public_description": ""
    },
    "internal_backend_error": {
        "name": "internal_backend_error",
        "private_description": "",
        "public_description": ""
    },
    "unknown_error": {
        "name": "unknown_error",
        "private_description": "Произошла неизвестная ошибка на стороне бота.",
        "public_description":
            "К сожалению, произошла неизвестная ошибка.\n" +
            "Попробуйте отправить ваше сообщение снова через некоторое время."
    },
})

unknown_error = BasicBotExceptions["unknown_error"]


class AttachmentException(Base):
    attachment_type = 'exception'

    def __init__(self, bot_exception: dict, format_public=None, format_private=None):
        self.file_id = None
        self.file_size = 0

        self.exception_name = bot_exception.get("name", unknown_error["name"])

        self.exception_private_description = bot_exception.get("private_description", unknown_error["private_description"])
        if format_private is not None and self.exception_private_description is not None:
            self.exception_private_description = self.exception_private_description.format(*format_private)

        self.exception_public_description = bot_exception.get("public_description", unknown_error["public_description"])
        if format_public is not None and self.exception_public_description is not None:
            self.exception_public_description = self.exception_public_description.format(*format_public)

        self.convert_to_dict()
        self.update({
            self.attachment_type: {
                "name": self.exception_name,
                "description": self.exception_private_description
            }
        })

    def get_public_description(self):
        return self.exception_public_description
