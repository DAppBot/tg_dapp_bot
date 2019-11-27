import aiohttp
import asyncio
import functools

from copy import deepcopy
from eth_account import Account
from eth_utils import from_wei
from eth_utils.address import is_address


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

    async def call_contract(self, address, ):



if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    eth = EthereumApi('9d968cd7361a4c64acf5dedbec1ec48f')

