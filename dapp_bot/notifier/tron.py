import asyncio
import base58
import logging

from dapp_bot.notifier import utils
from dapp_bot.tron import TronApi
from dapp_bot.db import CacheDB

from dapp_bot.middleware.i18n import i18n

_ = i18n.gettext

db = CacheDB()
db.create_connection()

class TronNotifier:
    def __init__(self):
        log_format = '%(levelname)s:%(name)s:%(asctime)s  %(message)s'
        logging.basicConfig(filename='log.txt', format=log_format)
        self.logger = logging.getLogger('tron_notifier')
        self.logger.setLevel(logging.INFO)

        self.blocks = asyncio.Queue()
        self.tron_api = TronApi()

        self.db = db

    async def _block_getter(self):
        latest_block = await self.tron_api._get_block()
        num_latest_block = latest_block['block_header']['raw_data']['number']
        num_future_block = num_latest_block + 2
        while True:
            try:
                block = await self.tron_api._get_block(num_future_block)
            except Exception:
                continue
            else:
                if block:
                    num_future_block += 1
                    await self.blocks.put(block)
            finally:
                await asyncio.sleep(0.2)

    async def _process_block(self):
        while True:
            block = await self.blocks.get()

            subscribers = await self.db.get_subscribes_wallets('tron')
            subscribed_wallets = utils.build_structure_subscribers(subscribers)

            for transaction in block.get("transactions", []):
                trans = transaction['raw_data']['contract'][0]

                if trans['type'] in ['TransferContract', 'TransferAssetContract']:
                    hex_address = trans['parameter']['value']['to_address']
                    address = base58.b58encode_check(bytes.fromhex(hex_address))
                else:
                    continue


                current_subs = subscribed_wallets.get(address, {})
                for user_id in current_subs.keys():
                    wallet_id = current_subs[user_id]  # для получения имени кошелька
                    locale, wallet_name = await self.collect_user_data(user_id, wallet_id)
                    msg_text = self._prepare_msg_text(locale, wallet_name, trans)
                    await utils.send_notify(user_id, msg_text)
                    self.logger.info('{} notify message to {}'.format(trans['type'],
                                                                      user_id))

    def _prepare_msg_text(self, locale, wallet_name, transaction):
        text = _('*Входящая транзакция {bch}* `{wallet_name}`\n\n',
                 locale=locale).format(bch='Tron',
                                       wallet_name=wallet_name)

        if (transaction['type'] == 'TransferAssetContract' and
                values['asset_name'] == 1002000):
            # token_id_b16 = values['asset_name']
            # token_id = bytes.fromhex(token_id_b16).decode()
            # token_info = await self.get_token_info(token_id)
            # token_name = bytes.fromhex(token_info['name']).decode()
            # text += _('*Токен: *', locale=locale) + f'*{token_name}*\n'
            text += _('*Токен: *', locale=locale) + f'*BTT*\n'

        to_addr = base58.b58encode_check(bytes.fromhex(values["to_address"]))
        from_addr = base58.b58encode_check(bytes.fromhex(values["owner_address"]))
        amount = tron.fromSun(values["amount"])

        text += _('*Сумма: *', locale=locale) + f'`{amount}`\n'
        text += _('*Кому: *', locale=locale) + f'`{to_addr}`\n'
        text += _('*От кого: *', locale=locale) + f'`{from_addr}`\n'

        return text

    def prepare_loop_to_start(self, loop):
        loop.create_task(self._block_getter())
        loop.create_task(self._process_block())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    notifier = TronNotifier()
    notifier.prepare_loop_to_start(loop)
    loop.run_forever()