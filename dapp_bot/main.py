from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, CallbackQuery, ChatType

from config import token, db_params
from middleware.i18n import i18n, _
from ethereum import EthereumApi
from tron import TronApi
from exceptions import *
from db import CacheDB
from buttons import *


bot = Bot(token)
dp = Dispatcher(bot)

dp.middleware.setup(i18n)
__ = i18n.lazy_gettext

db = CacheDB()
db.create_tables(**db_params)
db.create_connection(**db_params)
dp['db'] = db

eth = EthereumApi('project_id')
trx = TronApi()


@dp.message_handler(ChatType.is_private, commands=['start'])
async def on_start_msg(msg: Message):
    try:
        await db.save_new_user(msg.from_user.id,
                               msg.from_user.first_name,
                               msg.from_user.username)
    except ExistingUser:  # пользователь существует
        await select_language(msg)
    else:  # новый пользователь
        await select_language(msg)


async def main_menu(msg):
    await bot.send_message(msg.chat.id, _('Главное меню'),
                           reply_markup=main_menu_btn())


async def select_language(msg):
    await bot.send_message(msg.chat.id, _('Выберите язык'),
                           reply_markup=lang_select_inl())


@dp.message_handler(text=__('Настройки'))
async def on_settings_btn(msg: Message):
    await bot.send_message(msg.chat.id, _('Настройки'), reply_markup=settings_btn())


@dp.message_handler(text=__('Сменить язык'))
async def on_settings_btn(msg: Message):
    await select_language(msg)


async def wallets_msg(msg):
    eth_w, trx_w = await db.get_user_wallets(msg.chat.id)
    text = _('*Мои кошельки*') + '\n\n'
    text += '*Tron:*\n' if trx_w else ''
    for w in trx_w:
        text += f'➖`{w}`\n'
    text += '*Ethereum:*\n' if eth_w else ''
    for w in eth_w:
        text += f'➖`{w}`\n'
    if len(text.split('\n')) == 3:
        text += _('У вас нет добавленных кошельков 😞')
        return text, no_full_wallets_inl()
    return text, full_wallets_inl()


@dp.message_handler(text=__('Мои кошельки'))
async def on_wallets_btn(msg: Message):
    text, btn = await wallets_msg(msg)
    await bot.send_message(msg.chat.id, text, reply_markup=btn, parse_mode='markdown')


@dp.callback_query_handler(lambda c: c.data in ['ru', 'en'])  # выбор языка
async def on_select_lang(call: CallbackQuery):
    await db.set_user_locale(call.from_user.id, call.data)
    await call.message.delete()
    await main_menu(call.message)


@dp.callback_query_handler(text='wallets_stat')
async def on_wallet_stat(call: CallbackQuery):
    text, btn = await wallets_msg(call.message)
    await call.answer()
    await call.message.edit_text(text, reply_markup=btn, parse_mode='markdown')


@dp.callback_query_handler(text='add_wallet')  # добавление кошелька
async def on_add_wallet(call: CallbackQuery):
    text = _('*Добавление кошелька*\n\n')
    text += _('Выберите блокчейн')
    await call.answer()
    await call.message.edit_text(text, reply_markup=select_bch_inl(),
                                 parse_mode='markdown')


def select_bch_check(call: CallbackQuery):
    if call.data in ['bch_ethereum', 'bch_tron']:
        return {'bch': call.data.split('_')[-1]}


@dp.callback_query_handler(select_bch_check)  # выбор блокчейна
async def on_add_wallet(call: CallbackQuery, bch):
    text = _('*Добавление кошелька*') + f'* ▪ {bch.capitalize()}*\n\n'
    text += _('Отправьте адрес кошелька')
    await call.message.delete()
    await bot.send_message(call.message.chat.id, text, reply_markup=remove_btn(),
                                 parse_mode='markdown')


executor.start_polling(dp)
