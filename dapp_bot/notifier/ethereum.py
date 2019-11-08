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
        logging.basicConfig(filename='log.txt', format=log_format)
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
                    await self.send_notification(user_id, wallet_id, transaction)

    def prepare_loop_to_start(self, loop):
        loop.create_task(self._block_getter())
        loop.create_task(self._process_block_hash())


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    notifier = EthereumNotifier()
    notifier.prepare_loop_to_start(loop)
    loop.run_forever()
