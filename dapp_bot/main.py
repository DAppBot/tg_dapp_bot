import asyncio

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher import FSMContext
# from aiogram.dispatcher.filters.state import StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ChatType

from config import token, db_params, infura_id
from middleware.i18n import i18n, _
from ethereum import EthereumApi
from tron import TronApi
from exceptions import *
from db import CacheDB
from buttons import *
from utils import reduction_addr

bot = Bot(token, parse_mode='markdown')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

dp.middleware.setup(i18n)
__ = i18n.lazy_gettext

db = CacheDB()
# db.create_tables(**db_params)
db.create_connection(**db_params)
dp['db'] = db

eth = EthereumApi(infura_id)
trx = TronApi()

list_bch = ['ethereum', 'tron']
bch_modules = {'ethereum': eth,
               'tron': trx}

bch_token_names = {'ethereum': 'ETH',
                   'tron': 'TRX'}


@dp.message_handler(ChatType.is_private, commands=['start'])
async def on_start_msg(msg: Message):
    try:
        await db.save_new_user(msg.from_user.id,
                               msg.from_user.first_name,
                               msg.from_user.username)
    except ExistingUser:  # пользователь существует
        text, btn = main_menu()
        await bot.send_message(msg.chat.id, text, reply_markup=btn)
    else:  # новый пользователь
        await select_language(msg)


def main_menu():
    return _('Главное меню'), main_menu_btn()


async def select_language(msg):
    await bot.send_message(msg.chat.id, _('Выберите язык'),
                           reply_markup=lang_select_inl())


@dp.message_handler(text=__('Мои кошельки'))
async def on_wallets_btn(msg: Message):
    text, btn = await my_wallets_msg(msg)
    await bot.send_message(msg.chat.id, text, reply_markup=btn)


@dp.message_handler(text=__('Настройки'))
async def on_settings_btn(msg: Message):
    await bot.send_message(msg.chat.id, _('Настройки'), reply_markup=settings_btn())


@dp.message_handler(text=__('Сменить язык'))
async def on_settings_btn(msg: Message):
    await select_language(msg)


# async def wallets_msg(msg):
#     eth_w, trx_w = await db.get_user_wallets(msg.chat.id)
#     text = _('*Мои кошельки*') + '\n'
#     text += '\n*Tron:*\n' if trx_w else ''
#     for w in trx_w:
#         text += '➖`{}`  *{} TRX*\n'.format(reduction_addr(w),
#                                            await trx.get_balance(w))
#
#     text += '\n*Ethereum:*\n' if eth_w else ''
#     for w in eth_w:
#         text += '➖`{}`  *{} ETH*\n'.format(reduction_addr(w),
#                                            await eth.get_balance(w))
#
#     if len(text.split('\n')) == 3:
#         text += _('У вас нет добавленных кошельков 😞')
#         return text, no_full_wallets_inl()
#     return text, full_wallets_inl()


async def my_wallets_msg(msg):
    return _('*Выберите блокчейн*'), select_bch_inl()


async def my_bch_wallets(msg: CallbackQuery, bch):
    if isinstance(msg, CallbackQuery):
        user_id = msg.message.chat.id
    else:
        user_id = msg.chat.id
    text = _('*Мои {bch}-кошельки*\n\n').format(bch=bch.capitalize())
    wallets = await db.get_user_wallets(user_id, bch)
    btn = list_wallet_inl(wallets, bch)
    if len(btn.inline_keyboard) <= 2:
        text += _('У вас нет добавленных кошельков 😞')
    return text, btn


def select_bch_check(call: CallbackQuery):
    if call.data.endswith('view'):
        return {'bch': call.data.split('_')[0]}  # (ethereum/tron)_select_bch


# def cancel_check(call):
#    print(call.data)
#    if call.data.startswith('cancel'):
#        maybe_msg_id = call.data.split('_')[-1]
#        if maybe_msg_id.isdigit():
#            return {'msg_id': int(maybe_msg_id)}
#        return {'msg_id': None}


# отмена любого действия
@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def on_cancel(call: CallbackQuery):
    await call.message.delete()
    text, btn = main_menu()
    await bot.send_message(call.message.chat.id, text, reply_markup=btn)
    await storage.reset_state(user=call.message.chat.id)


# список языков, доступных к выбору
@dp.callback_query_handler(lambda c: c.data in ['ru', 'en'])  # выбор языка
async def on_select_lang(call: CallbackQuery):
    await db.set_user_locale(call.from_user.id, call.data)
    # устанавливаем локаль явно
    i18n.ctx_locale.set(call.data)
    await call.message.delete()
    text, btn = main_menu()
    await bot.send_message(call.message.chat.id, text, reply_markup=btn)


# выбор блокчейна, кошельки которого хотим посмотреть
@dp.callback_query_handler(text='my_wallets')
async def on_wallets_inl(call: CallbackQuery):
    text, btn = await my_wallets_msg(call.message)
    await call.message.edit_text(text, reply_markup=btn)


# список добавленных кошельков
@dp.callback_query_handler(select_bch_check)
async def on_select_bch(call: CallbackQuery, bch):
    text, btn = await my_bch_wallets(call, bch)
    await call.message.edit_text(text, reply_markup=btn)


def find_address_in_callback_data(call):
    if call.data.endswith('address_info'):
        bch, wallet_id = call.data.split('_')[:2]
        module = bch_modules[bch]
        return {'bch': bch, 'module': module, 'wallet_id': int(wallet_id)}


# отображение информации о кошельке
@dp.callback_query_handler(find_address_in_callback_data)
async def on_view_address(call, bch, module, wallet_id):
    address = await db.get_address_by_id(call.message.chat.id, wallet_id)
    balance = await module.get_balance(address)
    text = _('*Кошелек {}*').format(bch.capitalize()) + '\n'
    text += '`{}`'.format(address) + '\n\n'
    text += _('*Баланс: *') + '`{}` *{}*'.format(balance, bch_token_names[bch])
    await call.message.edit_text(text, reply_markup=wallet_menu_inl(bch, wallet_id))


async def remove_addr_check(call):
    if call.data.endswith('remove_address'):
        bch, wallet_id = call.data.split('_')[:2]
        addr = await db.get_address_by_id(call.message.chat.id, int(wallet_id))
        return {'bch': bch, 'address': addr}


# удаление кошелька
@dp.callback_query_handler(remove_addr_check)
async def on_address_remove(call, bch, address):
    await db.remove_wallet(call.message.chat.id, bch, address)
    text, btn = await my_bch_wallets(call, bch)
    await call.message.edit_text(text, reply_markup=btn)


async def set_wallet_name_check(call):
    if call.data.endswith('set_address_name'):
        bch, wallet_id = call.data.split('_')[:2]
        addr = await db.get_address_by_id(call.message.chat.id, int(wallet_id))
        return {'bch': bch, 'address': addr}


# предложение задать имя кошельку
@dp.callback_query_handler(set_wallet_name_check)
async def on_set_wallet_name(call: CallbackQuery, bch, address):
    await call.message.delete()
    text = _('*Задайте имя кошельку*') + '\n\n'
    await bot.send_message(call.message.chat.id, text,
                           reply_markup=remove_btn())

    text = _('Введите имя ниже (не более 20 символов)')
    await bot.send_message(call.message.chat.id, text, reply_markup=cancel_inl())

    await storage.set_state(user=call.message.chat.id, state='input_address_name')
    await storage.set_data(user=call.message.chat.id,
                           data={'bch': bch, 'address': address})


def select_bch_check(call: CallbackQuery):
    if call.data.endswith('add_bch_wallet'):
        return {'bch': call.data.split('_')[0]}


def choice_method_check(call: CallbackQuery):
    if call.data.endswith('choice_method_add_wallet'):
        return {'bch': call.data.split('_')[0]}


# выбор способа добавления кошелька
@dp.callback_query_handler(choice_method_check)
async def on_choice_method(call, bch):
    text = _('*Добавление кошелька*') + f'* {bch.capitalize()}*' + '\n\n'
    text += _('Выберите способ добавления кошелька')
    btn = choice_method_add_wallet_inl(bch)
    await call.message.edit_text(text, reply_markup=btn)


# предложение ввести в поле ввода адрес кошелька
@dp.callback_query_handler(select_bch_check)
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
    bch = (await state.get_state()).split('_')[0]
    if bch == 'ethereum' and not eth.is_address(msg.text) or \
            bch == 'tron' and not trx.is_address(msg.text):
        await bot.send_message(msg.chat.id, _('*Неправильный адрес*'))
        return
    await db.add_bch_address(msg.chat.id, bch, msg.text)
    await bot.send_message(msg.chat.id, _('*Кошелек добавлен*'))
    await state.reset_state()
    text, btn = main_menu()
    await bot.send_message(call.message.chat.id, text, reply_markup=btn)


async def input_address_name_check(msg):
    data = await storage.get_data(user=msg.chat.id)
    return {'bch': data['bch'], 'address': data['address']}


# проверка корректности имени кошелька
@dp.message_handler(input_address_name_check, state='input_address_name')
async def on_input_addres_name(msg, bch, address):
    if len(msg.text) > 20:
        await bot.send_message(msg.chat.id, _('*Неверный формат*'))
        return
    await db.set_wallet_name(msg.chat.id, bch, address, msg.text)
    await bot.send_message(msg.chat.id, _('Имя `{name}` задано').format(name=msg.text),
                           reply_markup=main_menu_btn())
    await storage.reset_state(user=msg.chat.id)
    text, btn = await my_bch_wallets(msg, bch)
    await bot.send_message(msg.chat.id, text, reply_markup=btn)


def private_key_check(call):
    if call.data.endswith('import_private_key'):
        return {'bch': call.data.split('_')[0]}


# импортирование приватного ключа
@dp.callback_query_handler(private_key_check)
async def on_private_key(call: CallbackQuery, bch):
    await call.message.delete()
    text = _('Импорт приватного ключа {bch}').format(bch=bch.capitalize()) + '\n\n'
    text += _('Вставьте приватный ключ')
    await bot.send_message(call.from_user.id, text, reply_markup=remove_btn())
    await storage.set_state(user=call.from_user.id, state='import_private_key')
    await storage.set_data(user=call.message.chat.id,
                           data={'bch': bch})


def generate_wallet_check(call):
    if call.data.endswith('generate_wallet'):
        return {'bch': call.data.split('_')[0]}


@dp.callback_query_handler(generate_wallet_check)
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
    bch_module = bch_modules[bch]
    try:
        address = await bch_module.get_addr_from_pkey(msg.text)
    except ValueError:
        await bot.send_message(msg.chat.id, _('*Неверный формат приватного ключа*'))
    else:
        await db.add_bch_address_with_pkey(msg.chat.id, bch, address, msg.text)
        text = _('*Кошелек добавлен*') + '\n\n'
        text += _('_Рекомендуется удалить сообщение с приватным ключом')
        await bot.send_message(msg.chat.id, text)
        await storage.reset_state(user=msg.chat.id)
        btn, text = main_menu()
        await bot.send_message(msg.chat.id, text, reply_markup=btn)


executor.start_polling(dp)
