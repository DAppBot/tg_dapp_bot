import aiohttp
import asyncio
import base58
import base64
import codecs

from trx_utils import is_address
from trx_utils import to_hex, encode_hex
from tronapi import Tron
from tronapi.trx import Trx
import dapp_bot.utils as utils


class TronApi:
    def __init__(self):
        self.tron = Tron()
        self.api = 'https://api.trongrid.io/'
        self.session = aiohttp.ClientSession(conn_timeout=3600)

    async def _request(self, method, endpoint, **params):
        async with self.session.request(method, self.api + endpoint, json=params) as r:
            return await r.json(content_type='')

    def is_address(self, addr):
        try:
            return is_address(addr)
        except:
            return False

    async def get_balance(self, addr):
        account = await self._request('POST', 'wallet/getaccount',
                                      address=str(self.tron.address.to_hex(addr)))
        if 'balance' not in account:
            return 0
        return self.tron.fromSun(account['balance'])

    async def get_token_info(self, token_id):
        token_info = await self._request('POST', 'wallet/getassetissuebyid',
                                         value=token_id)
        return token_info

    async def _get_block(self, number=None):
        if not number:
            return await self._request('POST', 'wallet/getnowblock')
        return await self._request('POST', 'wallet/getblockbynum', num=number)

    async def create_wallet(self):
        account = self.tron.create_account
        return account.address.base58, account.private_key

    def from_hex(self, text):
        return base58.b58encode_check(bytes.fromhex(text))

    def to_hex(self, text):
        return codecs.encode(base58.b58decode_check(text), 'hex').decode()

    async def send_trx(self, from_address, private_key, to_address, amount):
        account = Tron(private_key=private_key, default_address=from_address)
        account_api = Trx(account)
        amount_sun = amount * 1e6
        tx = await self._request('POST', '/wallet/createtransaction',
                                 owner_address=self.to_hex(from_address.encode()),
                                 to_address=self.to_hex(to_address.encode()),
                                 amount=int(amount_sun))

        signed_tx = account_api.sign(tx)

        return await self._request('POST', '/wallet/broadcasttransaction', **signed_tx)

    async def send_token(self, from_address, private_key, to_address, token_id, amount):
        account = Tron(private_key=private_key, default_address=from_address)
        account_api = Trx(account)
        amount_sun = amount * 1e6

        tx = await self._request('POST', '/wallet/transferasset',
                                 owner_address=self.to_hex(from_address.encode()),
                                 to_address=self.to_hex(to_address.encode()),
                                 amount=int(amount_sun),
                                 asset_name=codecs.encode(str(token_id).encode(), 'hex').decode())

        signed_tx = account_api.sign(tx)

        return await self._request('POST', '/wallet/broadcasttransaction', **signed_tx)



