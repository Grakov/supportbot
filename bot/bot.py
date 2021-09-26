import telebot
import logging

import config

bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode=None)
if config.DEBUG:
    telebot.logger.setLevel(logging.DEBUG)
