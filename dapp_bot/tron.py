import aiohttp

from trx_utils import is_address
from tronapi.common.account import Account
from tronapi import Tron

tron = Tron()




class TronApi:
    def __init__(self):
        self.api = 'https://api.trongrid.io/'
        self.session = aiohttp.ClientSession(conn_timeout=3600)

    async def _request(self, method, endpoint, **params):
        async with self.session.request(method, self.api + endpoint, json=params) as r:
            return await r.json(content_type='')

    def is_address(self, addr):
        return is_address(addr)

    async def get_balance(self, addr):
        account = await self._request('POST', 'wallet/getaccount',
                                      address=str(tron.address.to_hex(addr)))
        if 'balance' not in account:
            return 0
        return tron.fromSun(account['balance'])

    async def create_wallet(self):
        account = tron.create_account
        return account.address.base58, account.private_key

