import random

from aiogram.types.inline_keyboard import (InlineKeyboardButton,
                                           InlineKeyboardMarkup)
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard import ReplyKeyboardRemove

from middleware.i18n import i18n
from utils import reduction_addr

_ = i18n.gettext

def main_menu_btn():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    #keyboard.add(_('Анонсы'), _('Выбор блокчейна'),
    #             _('FAQ'), _('Настройки'),
    #             _('Быстрая конвертация'),
    #             _('Мои кошельки'), _('Залистить проект')
    #             )
    keyboard.add(_('Анонсы'),
                 _('Мои кошельки'),
                 _('Настройки'),
                 _('Партнеры')
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

    for ids, name_or_address in wallets:

        keyboard.add(InlineKeyboardButton(reduction_addr(name_or_address),
                                          callback_data='{}_{}_address_info'.format(bch,
                                                                                    ids)))

    keyboard.add(InlineKeyboardButton(_('Добавить кошелек'),
                                      callback_data='{}_choice_method_add_wallet'.format(
                                          bch)))
    keyboard.add(InlineKeyboardButton(_('Назад'), callback_data='my_wallets'))
    return keyboard


def wallet_menu_inl(bch, wallet_id, is_subscribe):
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(InlineKeyboardButton(
        _('Получать обновления: {status}'.format(status='✅' if is_subscribe else '❌')),
        callback_data='{}_{}_subscribe_to_updates'.format(bch, wallet_id)))

    keyboard.add(InlineKeyboardButton(_('Указать имя'),
                                         callback_data='{}_{}_set_address_name'.format(
                                             bch,
                                             wallet_id)))

    keyboard.insert(InlineKeyboardButton(_('Сделать основным'),
                                         callback_data='{}_{}_set_address_as_main'.format(
                                             bch,
                                             wallet_id)))
    keyboard.insert(InlineKeyboardButton(_('Удалить кошелек'),
                                         callback_data='{}_{}_try_remove_address'.format(
                                             bch,
                                             wallet_id)))
    keyboard.insert(InlineKeyboardButton(_('Приватный ключ'),
                                         callback_data='{}_{}_view_private_key'.format(
                                             bch,
                                             wallet_id)))


    keyboard.add(InlineKeyboardButton(_('Назад'),
                                         callback_data=f'{bch}_view'))
    return keyboard


def remove_wallet_inl(bch, wallet_id):
    keyboard = InlineKeyboardMarkup(row_width=2)

    list_buttons = [
        InlineKeyboardButton(_('Нет'),
                             callback_data='{}_{}_address_info'.format(bch,
                                                                       wallet_id)),
        InlineKeyboardButton(_('Нет'),
                             callback_data='{}_{}_address_info'.format(bch,
                                                                       wallet_id)),
        InlineKeyboardButton(_('Нет'),
                             callback_data='{}_{}_address_info'.format(bch,
                                                                       wallet_id)),
        InlineKeyboardButton(_('Да, удалить'),
                             callback_data='{}_{}_remove_address'.format(bch,
                                                                         wallet_id))
        ]
    random.shuffle(list_buttons)
    list_buttons.append(InlineKeyboardButton(_('Назад'),
                                             callback_data='{}_{}_address_info'.format(
                                                 bch,
                                                 wallet_id)))

    for btn in list_buttons:
        keyboard.insert(btn)

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
        # InlineKeyboardButton(_('Импортировать seed-фразу'),
        #                 callback_data=f'{bch}_import_seed_phrase'),
        InlineKeyboardButton(_('Сгенерировать новый кошелек'),
                             callback_data=f'{bch}_generate_wallet'),
        InlineKeyboardButton(_('Назад'),
                             callback_data=f'{bch}_view'))
    return keyboard


def remove_btn():
    return ReplyKeyboardRemove()
