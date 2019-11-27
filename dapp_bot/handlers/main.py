from dapp_bot import utils
from dapp_bot.exceptions import *
from dapp_bot.buttons import *


def main_menu(_):
    return _('Главное меню'), main_menu_btn()


def my_wallets_msg(_, msg):
    return _('*Выберите блокчейн*'), select_bch_inl()


async def select_language(bot, _, msg):
    await bot.send_message(msg.chat.id, _('Выберите язык'),
                           reply_markup=lang_select_inl())


async def on_start_msg(bot, db, _, msg):
    new_ref_link = utils.encode_to_base64(msg.chat.id).lower()

    try:
        await db.save_new_user(msg.from_user.id,
                               msg.from_user.first_name,
                               msg.from_user.username,
                               new_ref_link, inv_link=msg.get_args() or None)
    except ExistingUser:
        text, btn = main_menu(_)
        await bot.send_message(msg.chat.id, text, reply_markup=btn)
    else:
        await select_language(bot, _, msg)


async def on_cancel(bot, storage, call):
    await call.message.delete()
    text, btn = main_menu(_)
    await bot.send_message(call.message.chat.id, text, reply_markup=btn)
    await storage.reset_state(user=call.message.chat.id)


async def on_wallets_btn(bot, _, msg):
    text, btn = my_wallets_msg(_, msg)
    await bot.send_message(msg.chat.id, text, reply_markup=btn)


async def on_settings_btn(bot, _, msg):
    await bot.send_message(msg.chat.id, _('Настройки'), reply_markup=settings_btn())


async def on_partner_btn(bot, _, db, msg):
    ref_link = await db.get_ref_link(msg.chat.id)
    inv_count = await db.get_number_of_invited(msg.chat.id)
    inv_count_with_bonus = await db.get_number_of_invited_with_bonus(msg.chat.id)

    text = _('*Партнерская программа*') + '\n\n'
    text += _('*Ваша ссылка для приглашений:*') + '\n'
    text += f't.me/dapppp\_bot?start={ref_link}' + '\n\n'
    text += _('*Приглашено:* ') + f'`{inv_count}`' + '\n'
    text += _('*Из них выплачено:* ') + f'`{inv_count_with_bonus}`'

    await bot.send_message(msg.chat.id, text, reply_markup=main_menu_btn())


# список языков, доступных к выбору
async def on_select_lang(bot, _, db, call):
    await db.set_user_locale(call.from_user.id, call.data)
    # устанавливаем локаль явно
    i18n.ctx_locale.set(call.data)
    await call.message.delete()
    text, btn = main_menu(_)
    await bot.send_message(call.message.chat.id, text, reply_markup=btn)


async def reg_handlers(_, __, bot, dp, db, storage, **kwargs):
    dp.register_message_handler(on_start_msg, [bot, db],
                                ChatType.is_private, commands=['start'])
    dp.register_message_handler(on_wallets_btn, [bot, _],
                                text=__('Мои кошельки'))
    dp.register_message_handler(on_settings_btn, [bot, _],
                                text=__('Настройки'))
    dp.register_message_handler(select_language, [bot, _, db],
                                text=__('Сменить язык'))
    dp.register_message_handler(on_partner_btn, [bot, _, db],
                                text=__('Партнеры'))

    dp.register_callback_query_handler(on_cancel, [bot, _, storage],
                                       lambda c: c.data == 'cancel', state='*')
    dp.register_callback_query_handler(on_select_lang, [bot, _, db],
                                       lambda c: c.data in ['ru', 'en'])
