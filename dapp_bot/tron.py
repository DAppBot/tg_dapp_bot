import aiohttp
import asyncio

from trx_utils import is_address
from tronapi import Tron

import dapp_bot.utils as utils





class TronApi:
    def __init__(self):
        self.tron = Tron()
        self.api = 'https://api.trongrid.io/'
        self.session = aiohttp.ClientSession(conn_timeout=3600)
        self.block_q = asyncio.Queue()

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

    async def get_token_info(self, token_id):
        print(token_id)
        token_info = await self._request('POST', 'wallet/getassetissuebyid', value=token_id)
        return token_info

    async def _get_block(self, number=None):
        if not number:
            return await self._request('POST', 'wallet/getnowblock')
        return await self._request('POST', 'wallet/getblockbynum', num=number)

    async def create_wallet(self):
        account = tron.create_account
        return account.address.base58, account.private_key