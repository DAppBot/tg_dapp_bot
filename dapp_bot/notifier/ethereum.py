import asyncio
import aiohttp
import logging

from dapp_bot.notifier import utils
from dapp_bot.ethereum import EthereumApi
from dapp_bot.db import CacheDB

from dapp_bot.middleware.i18n import i18n

_ = i18n.gettext

db = CacheDB()
db.create_connection()


class EthereumNotifier:
    def __init__(self):
        log_format = '%(levelname)s:%(name)s:%(asctime)s  %(message)s'
        # logging.basicConfig(filename='log.txt', format=log_format)
        self.logger = logging.getLogger('ethereum_notifier')
        self.logger.setLevel(logging.INFO)

        self.db = db

        self.eth_api = EthereumApi()
        self.ws_api = 'ws://104.248.84.124:8546'

        self.session = aiohttp.ClientSession(conn_timeout=3600)

        self.block_hash_q = asyncio.Queue()

    async def _connect_ws(self):
        return await self.session.ws_connect(self.ws_api)

    async def _get_block_hashes(self, ws_sock, filter_id):
        data = self.eth_api._create_req('eth_getFilterChanges', filter_id)
        await ws_sock.send_json(data)
        try:
            result = await ws_sock.receive_json()
        except TypeError:
            return []
        else:
            return result.get('result', [])

    async def _get_filter_id(self, ws_sock):
        data = self.eth_api._create_req('eth_newBlockFilter')
        await ws_sock.send_json(data)
        return (await ws_sock.receive_json())['result']

    async def _block_getter(self):
        ws_sock = await self._connect_ws()

        filter_id = await self._get_filter_id(ws_sock)
        self.logger.info('starting the notifier')
        while True:
            block_hashes = await self._get_block_hashes(ws_sock, filter_id)

            for block_hash in block_hashes:
                await self.block_hash_q.put(block_hash)

            await asyncio.sleep(0.2)

    async def _process_block_hash(self):
        while True:
            block_hash = await self.block_hash_q.get()
            block = await self.eth_api.eth_getBlockByHash(block_hash, True)
            subscribers = await self.db.get_subscribes_wallets('ethereum')
            subscribed_wallets = utils.build_structure_subscribers(subscribers, True)

            for transaction in block['transactions']:
                address = transaction['to']
                current_subs = subscribed_wallets.get(address, {})
                for user_id in current_subs.keys():
                    wallet_id = current_subs[user_id]  # для получения имени кошелька
                    locale, wallet_name = await self._collect_user_data(user_id,
                                                                        wallet_id)
                    msg_text = await self._prepare_msg_text(locale,
                                                            wallet_name,
                                                            transaction)
                    await utils.send_notify(user_id, msg_text)
                    self.logger.info(
                        'Ethereum: notify message to {}'.format(user_id))
                    await db.add_transaction(user_id, 'ethereum')

    async def _collect_user_data(self, user_id, wallet_id):
        locale = await db.get_user_locale(user_id)
        wallet_name = await db.get_wallet_name_by_id(wallet_id)
        return locale, wallet_name or ''

    async def _prepare_msg_text(self, locale, wallet_name, transaction):

        text = _('*Входящая транзакция {bch}* `{wallet_name}`\n\n', locale=locale).format(
            bch='Ethereum', wallet_name=wallet_name)
        text += _('*Сумма: *', locale=locale) + '`{:.8f}`\n'.format(
                        self.eth_api._from_wei(transaction["value"])).rstrip('0').rstrip('.')
        text += _('*Кому: *', locale=locale) + f'`{transaction["to"]}`\n'
        text += _('*От кого: *', locale=locale) + f'`{transaction["from"]}`\n'
        print(text)
        return text

    def prepare_loop_to_start(self, loop):
        loop.create_task(self._block_getter())
        loop.create_task(self._process_block_hash())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    notifier = EthereumNotifier()
    notifier.prepare_loop_to_start(loop)
    loop.run_forever()
