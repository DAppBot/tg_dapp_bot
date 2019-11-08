import aiohttp
import asyncio
import functools

from copy import deepcopy
from eth_account import Account
from eth_utils import from_wei
from eth_utils.address import is_address
from middleware.i18n import i18n

import utils

class EthereumApi:

    def __init__(self):
        self.api = 'http://104.248.84.124:8545'
        self.ws_api = 'ws://104.248.84.124:8546'
        self.template = {"jsonrpc": "2.0",
                         "id": 1,
                         "method": "",
                         "params": []}

        self.session = aiohttp.ClientSession(conn_timeout=3600)


    def _create_req(self, method, *args, **params):
        data = deepcopy(self.template)

        data['method'] = method
        data['params'].extend([*args])
        if params:
            data['params'].append(params)

        return data

    async def _post(self, method, *args, **params):
        data = self._create_req(method, *args, **params)

        async with self.session.post(self.api, json=data) as r:
            return (await r.json())['result']
            # return (await r.json())

    def __getattr__(self, item):
        return functools.partial(self._post, item)

    def _from_wei(self, wei):
        if isinstance(wei, str):
            wei = int(wei, 16)
        return float(round(from_wei(wei, 'ether'), 7))

    def is_address(self, addr):
        return is_address(addr)

    async def get_balance(self, addr):
        balance = await self.eth_getBalance(addr, 'latest')
        return self._from_wei(balance)

    async def get_addr_from_pkey(self, pkey):
        account = Account.privateKeyToAccount(pkey)
        return account.address

    async def create_wallet(self):
        account = Account.create()
        return account.address, account.privateKey.hex()

    async def connect_ws(self):
        self.ws_sock = await self.ws_session.ws_connect(self.ws_api)

    async def subcribe_to_updates(self):
        asyncio.get_running_loop().create_task(self._process_block_hash())
        await self.connect_ws()
        data = self._create_req('eth_newBlockFilter')
        await self.ws_sock.send_json(data)

        filter = (await self.ws_sock.receive_json())['result']

        while True:
            data = self._create_req('eth_getFilterChanges', filter)
            await self.ws_sock.send_json(data)
            try:
                result = await self.ws_sock.receive_json()
            except TypeError:
                continue
            if result.get('result'):
                for block_hash in result['result']:
                    await self.block_hash_q.put(block_hash)

            await asyncio.sleep(0.2)

    async def _process_block_hash(self):
        while True:
            block_hash = await self.block_hash_q.get()
            block = await self.eth_getBlockByHash(block_hash, True)

            subscribers = await self.db.get_subscribes_wallets('ethereum')
            subscribed_wallets = utils.build_structure_subscribers(subscribers, True)

            for transaction in block['transactions']:
                address = transaction['to']
                current_subs = subscribed_wallets.get(address, {})
                for user_id in current_subs.keys():
                    wallet_id = current_subs[user_id]  # для получения имени кошелька
                    await self.send_notification(user_id, wallet_id, transaction)

    async def send_notification(self, user_id, wallet_id, trans):
        locale = await self.db.get_user_locale(user_id)
        wallet_name = await self.db.get_wallet_name_by_id(wallet_id) or ''

        text = _('*Входящая транзакция {bch}* `{wallet_name}`\n\n', locale=locale).format(
            bch='Ethereum', wallet_name=wallet_name)
        text += _('*Сумма: *', locale=locale) + f'`{self._from_wei(trans["value"])}`\n'
        text += _('*Кому: *', locale=locale) + f'`{trans["to"]}`\n'
        text += _('*От кого: *', locale=locale) + f'`{trans["from"]}`\n'

        await self.bot.send_message(user_id, text)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    eth = EthereumApi('9d968cd7361a4c64acf5dedbec1ec48f')

    loop.run_until_complete(eth.connect_ws())
    loop.create_task(eth._process_block_hash())
    print(loop.run_until_complete(eth.subcribe_to_updates()))
