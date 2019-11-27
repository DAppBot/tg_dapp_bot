import aiogram
import logging

from dapp_bot.config import token

bot = aiogram.Bot(token)


def build_structure_subscribers(subscribers, addr_to_lower=False):
    subscribed_wallets = {}
    for ids, address, user_id in subscribers:
        if addr_to_lower:
            address = address.lower()
        current_addr = subscribed_wallets.setdefault(address, {})
        current_addr[user_id] = ids
    return subscribed_wallets


async def send_notify(user_id, msg_text):
    await bot.send_message(user_id, msg_text, parse_mode='Markdown')
