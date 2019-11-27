from dapp_bot import utils
from dapp_bot.exceptions import *
from dapp_bot.buttons import *
from main import

async def my_bch_wallets(_, db, msg, bch):
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




async def reg_handlers(_, __, bot, dp, db, storage, **kwargs):
    pass