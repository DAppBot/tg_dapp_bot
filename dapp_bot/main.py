import asyncio
import functools

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ChatType

import utils
import sender_utils
import config
from buttons import *
from ethereum import EthereumApi
from exceptions import *
from db import CacheDB
from middleware.i18n import CustomI18n
from tron import TronApi
from backend.storage import pkey_storage
from backend.app import app_coro
from cb_helper import cb_filter


class ModifiedDispatcher(Dispatcher):
    def _prepare_cb(self, cb, cb_args):
        return functools.partial(cb, *cb_args)

    def register_message_handler(self, cb, cb_args, *custom_filters, **kwargs):
        super().register_message_handler(self._prepare_cb(cb, cb_args),
                                         *custom_filters, **kwargs)

    def register_callback_query_handler(self, cb, cb_args, *custom_filters, **kwargs):
        super().register_callback_query_handler(self._prepare_cb(cb, cb_args),
                                                *custom_filters, **kwargs)


async def connect_to_db(*, recreate_tables=False, **params):
    db = CacheDB()
    db.create_connection(**params)
    if recreate_tables:
        db.create_tables()
    return db


async def main():
    bot = Bot(config.token, parse_mode='markdown')
    storage = MemoryStorage()
    dp = ModifiedDispatcher(bot, storage=storage)

    db = await connect_to_db(**config.db_params)

    # для работы локализации
    dp['db'] = db
    i18n = CustomI18n(domain='bot')
    _, __ = i18n.gettext, i18n.lazy_gettext
    dp.middleware.setup(i18n)

    # интерфейсы к блокчейнам
    eth = EthereumApi()
    trx = TronApi()

    list_bch = ['ethereum', 'tron']
    bch_modules = {'ethereum': eth,
                   'tron': trx}
    bch_token_names = {'ethereum': 'ETH',
                       'tron': 'TRX'}

    await register_handlers(_, __, bot=bot, storage=storage, dp=dp,
                            db=db, eth=eth, trx=trx)


def register_handlers(_, __, **kwargs):
    from handlers import main
    main.reg_handlers(_, __, **kwargs)
    from handlers import wallets


async def my_bch_wallets(msg: CallbackQuery, bch):
    if isinstance(msg, CallbackQuery):
        user_id = msg.message.chat.id
    else:
        user_id = msg.chat.id
    text = _('*Мои {bch}-кошельки*').format(bch=bch.capitalize()) + '\n\n'
    wallets = await db.get_user_wallets(user_id, bch)
    btn = list_wallet_inl(wallets, bch)
    if len(btn.inline_keyboard) <= 2:
        text += _('У вас нет добавленных кошельков 😞')
    return text, btn








# выбор блокчейна, кошельки которого хотим посмотреть
@dp.callback_query_handler(text='my_wallets')
async def on_wallets_inl(call: CallbackQuery):
    text, btn = await my_wallets_msg(call.message)
    await call.message.edit_text(text, reply_markup=btn)


# список добавленных кошельков
@dp.callback_query_handler(cb_filter('view', ['bch']))
async def on_select_bch(call: CallbackQuery, bch):
    text, btn = await my_bch_wallets(call, bch)
    await call.message.edit_text(text, reply_markup=btn)


async def view_address(bch, module, wallet_id):
    address, name, is_subscribe = await db.get_wallet_by_id(int(wallet_id))
    balance = await module.get_balance(address)

    text = _('*Кошелек {bch}*').format(bch=bch.capitalize()) + '  `{}`'.format(
        name if name else ' ') + '\n'
    text += '`{}`'.format(address) + '\n\n'
    text += _('*Баланс: *') + '`{}` *{}*'.format(balance, bch_token_names[bch])

    return text, wallet_menu_inl(bch, wallet_id, is_subscribe)


# отображение информации о кошельке
@dp.callback_query_handler(cb_filter('address_info', ['bch', 'wallet_id']))
async def on_view_address(call, bch, wallet_id):
    module = bch_modules[bch]
    text, btn = await view_address(bch, module, wallet_id)
    await call.message.edit_text(text, reply_markup=btn)


@dp.callback_query_handler(cb_filter('try_remove_address', ['bch', 'wallet_id']))
async def on_try_remove_address(call: CallbackQuery, bch, wallet_id):
    await call.answer(_('Перед удалением сохраните приватный ключ'), show_alert=True)
    text = _('Вы действительно хотите удалить кошелек?')
    await call.message.edit_text(text, reply_markup=remove_wallet_inl(bch, wallet_id))


# удаление кошелька
@dp.callback_query_handler(cb_filter('remove_address', ['bch', 'wallet_id']))
async def on_address_remove(call, bch, wallet_id):
    await db.remove_wallet(int(wallet_id))
    text, btn = await my_bch_wallets(call, bch)
    await call.message.edit_text(text, reply_markup=btn)


# предложение задать имя кошельку
@dp.callback_query_handler(cb_filter('set_address_name', ['bch', 'wallet_id']))
async def on_set_wallet_name(call: CallbackQuery, bch, wallet_id):
    await call.message.delete()
    text = _('*Задайте имя кошельку*') + '\n\n'
    await bot.send_message(call.message.chat.id, text,
                           reply_markup=remove_btn())

    text = _('Введите имя ниже (не более 20 символов)')
    await bot.send_message(call.message.chat.id, text, reply_markup=cancel_inl())

    await storage.set_state(user=call.message.chat.id, state='input_address_name')
    await storage.set_data(user=call.message.chat.id,
                           data={'bch': bch, 'wallet_id': wallet_id})


# выбор способа добавления кошелька
@dp.callback_query_handler(cb_filter('choice_method_add_wallet', ['bch']))
async def on_choice_method(call, bch):
    text = _('*Добавление кошелька*') + f'* {bch.capitalize()}*' + '\n\n'
    text += _('Выберите способ добавления кошелька')
    btn = choice_method_add_wallet_inl(bch)
    await call.message.edit_text(text, reply_markup=btn)


# предложение ввести в поле ввода адрес кошелька
@dp.callback_query_handler(cb_filter('add_bch_wallet', ['bch']))
async def on_add_wallet(call: CallbackQuery, bch):
    await call.message.delete()

    text = _('*Добавление кошелька*') + f'* {bch.capitalize()}*'
    await bot.send_message(call.message.chat.id, text,
                           reply_markup=remove_btn())

    text = _('Отправьте адрес кошелька')
    await bot.send_message(call.message.chat.id, text,
                           reply_markup=cancel_inl(),
                           parse_mode='markdown')

    await storage.set_state(user=call.from_user.id, state=f'{bch}_addr_input')


# реакция на ввод кошелька
@dp.message_handler(state='ethereum_addr_input')
@dp.message_handler(state='tron_addr_input')
async def on_input_address(msg: Message, state: FSMContext):
    import time
    t = time.time()

    # имя блокчейна хранится в стейте
    bch = (await state.get_state()).split('_')[0]
    module = bch_modules[bch]
    print(bch, module, msg.text)
    if not module.is_address(msg.text):
        await bot.send_message(msg.chat.id, _('*Неправильный адрес*'))
        return

    await state.reset_state()
    await db.add_bch_address(msg.chat.id, bch, msg.text)
    await bot.send_message(msg.chat.id, _('*Кошелек добавлен*'))
    text, btn = main_menu()
    await bot.send_message(msg.chat.id, text, reply_markup=btn)

    await sender_utils.bonus_if_need(db, bot, trx, msg.chat.id)

    print(time.time() - t)


async def input_address_name_check(msg):
    data = await storage.get_data(user=msg.chat.id)
    return {'bch': data['bch'], 'wallet_id': data['wallet_id']}


# проверка корректности имени кошелька
@dp.message_handler(input_address_name_check, state='input_address_name')
async def on_input_addres_name(msg, bch, wallet_id):
    if len(msg.text) > 20:
        await bot.send_message(msg.chat.id, _('*Неверный формат*'))
        return
    await db.set_wallet_name(int(wallet_id), msg.text)
    await bot.send_message(msg.chat.id, _('Имя `{name}` задано').format(name=msg.text),
                           reply_markup=main_menu_btn())
    await storage.reset_state(user=msg.chat.id)
    text, btn = await my_bch_wallets(msg, bch)
    await bot.send_message(msg.chat.id, text, reply_markup=btn)


# импортирование приватного ключа
@dp.callback_query_handler(cb_filter('import_private_key', ['bch']))
async def on_private_key(call: CallbackQuery, bch):
    await call.message.delete()
    text = _('*Импорт приватного ключа {bch}*').format(bch=bch.capitalize()) + '\n\n'
    text += _('Вставьте приватный ключ')
    await bot.send_message(call.from_user.id, text, reply_markup=cancel_inl())
    await storage.set_state(user=call.from_user.id, state='import_private_key')
    await storage.set_data(user=call.message.chat.id,
                           data={'bch': bch})


@dp.callback_query_handler(cb_filter('subscribe_to_updates', ['bch', 'wallet_id']))
async def on_subscribe_to_updates(call, bch, wallet_id):
    module = bch_modules[bch]
    await db.subscribe_addr_to_updates(int(wallet_id))
    text, btn = await view_address(bch, module, wallet_id)
    await call.message.edit_text(text, reply_markup=btn)


@dp.callback_query_handler(cb_filter('generate_wallet', ['bch']))
async def on_generate_wallet(call: CallbackQuery, bch):
    bch_module = bch_modules[bch]
    public_key, private_key = await bch_module.create_wallet()
    await db.add_bch_address_with_pkey(call.from_user.id, bch, public_key, private_key)
    text = _('*Ваш новый {bch}-кошелек*').format(bch=bch.capitalize()) + '\n\n'
    text += _('*Адрес:* ') + '`{}`'.format(public_key) + '\n\n'
    text += '_{}_'.format(_('Кошелек сохранен. Приватный ключ доступен из меню кошелька'))
    await call.message.edit_text(text)


@dp.message_handler(state='import_private_key')
async def on_input_private_key(msg):
    bch = (await storage.get_data(user=msg.chat.id))['bch']
    module = bch_modules[bch]
    try:
        address = await module.get_addr_from_pkey(msg.text)
    except ValueError:
        await bot.send_message(msg.chat.id, _('*Неверный формат приватного ключа*'))
    else:
        await db.add_bch_address_with_pkey(msg.chat.id, bch, address, msg.text)
        text = _('*Кошелек добавлен*') + '\n\n'
        text += _('_Рекомендуется удалить сообщение с приватным ключом_')
        await bot.send_message(msg.chat.id, text)
        await storage.reset_state(user=msg.chat.id)
        text, btn = main_menu()
        await bot.send_message(msg.chat.id, text, reply_markup=btn)


@dp.callback_query_handler(cb_filter('view_private_key', ['bch', 'wallet_id']))
async def on_get_privatekey_link(call: CallbackQuery, bch, wallet_id):
    try:
        pkey = await db.get_private_key(int(wallet_id))
    except PKeyNotFound:
        await call.answer(text=_('Приватный ключ не добавлен'))
    else:
        pkey_link = pkey_storage.create_link(pkey)
        await call.message.edit_text(pkey_link)


loop = asyncio.get_event_loop()

loop.create_task(app_coro)

executor.start_polling(dp, loop=loop)
