from aiogram.types.inline_keyboard import (InlineKeyboardButton,
                                           InlineKeyboardMarkup)
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard import ReplyKeyboardRemove

from middleware.i18n import _
from utils import reduction_addr


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
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton('Ethereum', callback_data='ethereum_view'),
        InlineKeyboardButton('Tron', callback_data='tron_view'),
        )
    return keyboard


def list_wallet_inl(wallets, bch):
    keyboard = InlineKeyboardMarkup(row_width=1)

    for wallet in wallets:
        ids = wallet.get('id')
        address = wallet.get('address')
        keyboard.add(InlineKeyboardButton(reduction_addr(address),
                                          callback_data='{}_{}_address_info'.format(bch,
                                                                                    ids)))

    keyboard.add(InlineKeyboardButton(_('Добавить кошелек'),
                                      callback_data='{}_choice_method_add_wallet'.format(
                                          bch)))
    keyboard.add(InlineKeyboardButton(_('Назад'), callback_data='my_wallets'))
    return keyboard


def wallet_menu_inl(bch, address):

    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.insert(InlineKeyboardButton(_('Указать имя'),
                                      callback_data='{}_{}_set_address_name'.format(bch,
                                                                                    address)))

    keyboard.insert(InlineKeyboardButton(_('Сделать основным'),
                                      callback_data='{}_{}_set_address_as_main'.format(
                                          bch,
                                          address)))
    keyboard.insert(InlineKeyboardButton(_('Удалить кошелек'),
                                      callback_data='{}_{}_remove_address'.format(bch,
                                                                                  address)))
    keyboard.insert(InlineKeyboardButton(_('Приватный ключ'),
                                      callback_data='{}_{}_view_private_key'.format(bch,
                                                                                  address)))
    keyboard.insert(InlineKeyboardButton(_('Назад'),
                         callback_data=f'{bch}_view'))
    return keyboard


def cancel_inl():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(_('Отмена'), callback_data='cancel'))
    return keyboard


def choice_method_add_wallet_inl(bch):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(_('Добавить адрес кошелька'),
                             callback_data=f'{bch}_add_bch_wallet'),
        InlineKeyboardButton(_('Импортировать приватный ключ'),
                         callback_data=f'{bch}_import_private_key'),
        #InlineKeyboardButton(_('Импортировать seed-фразу'),
        #                 callback_data=f'{bch}_import_seed_phrase'),
        InlineKeyboardButton(_('Сгенерировать новый кошелек'),
                         callback_data=f'{bch}_generate_wallet'),
        InlineKeyboardButton(_('Назад'),
                         callback_data=f'{bch}_view'))
    return keyboard


def remove_btn():
    return ReplyKeyboardRemove()
