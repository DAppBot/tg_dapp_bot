from aiogram.types.inline_keyboard import (InlineKeyboardButton,
                                           InlineKeyboardMarkup)
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard import ReplyKeyboardRemove

from middleware.i18n import _


def main_menu_btn():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(_('Анонсы'), _('Выбор блокчейна'),
                 _('FAQ'), _('Настройки'),
                 _('Быстрая конвертация'),
                 _('Мои кошельки'), _('Залистить проект')
                 )
    return keyboard

def settings_btn():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(_('Сменить язык'))
    return keyboard

def lang_select_inl():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton('🇷🇺 Русский', callback_data='ru'),
        InlineKeyboardButton('🇺🇸 English', callback_data='en')
        )
    return keyboard

def full_wallets_inl():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(_('Добавить кошелек'), callback_data='add_wallet'),
        InlineKeyboardButton(_('Конвертировать'), callback_data='convert_wallet')
        )
    return keyboard

def no_full_wallets_inl():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(_('Добавить кошелек'), callback_data='add_wallet')
        )
    return keyboard

def select_bch_inl():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton('Ethereum', callback_data='bch_ethereum'),
        InlineKeyboardButton('Tron', callback_data='bch_tron'),
        InlineKeyboardButton(_('Назад'), callback_data='wallets_stat'),
        )
    return keyboard

def remove_btn():
    return ReplyKeyboardRemove()