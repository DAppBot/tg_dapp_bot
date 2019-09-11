import aiohttp
import functools
from copy import deepcopy

from eth_account import Account
from eth_utils import from_wei
from eth_utils.address import is_address



class EthereumApi:
    def __init__(self, project_id: str):
        self.api = 'https://mainnet.infura.io/v3/' + project_id
        self.template = {"jsonrpc": "2.0",
                         "id": 1,
                         "method": "",
                         "params": []}
        self.session = aiohttp.ClientSession(conn_timeout=3600)

    async def _post(self, method, *args, **params):
        data = deepcopy(self.template)

        data['method'] = method
        if params:
            data['params'].append(params)
        data['params'].extend([*args])

        async with self.session.post(self.api, json=data) as r:
            return (await r.json())['result']

    def __getattr__(self, item):
        return functools.partial(self._post, item)

    def is_address(self, addr):
        return is_address(addr)

    async def get_balance(self, addr):
        balance = await self.eth_getBalance(addr, 'latest')
        return float(round(from_wei(int(balance, 0), 'ether'), 7))

    async def get_addr_from_pkey(self, pkey):
        account = Account.privateKeyToAccount(pkey)
        return account.address

    async def create_wallet(self):
        account = Account.create()
        return account.address, account.privateKey.hex()

