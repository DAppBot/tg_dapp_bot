import asyncio
import asyncpg
from aiohttp import ClientSession

import utils

from config import db_params
from exceptions import *


class DB:

    @classmethod
    def create_tables(cls, *args, **kwargs):
        db = CacheDB()
        db.create_connection(*args, **kwargs)
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(db._execute("DROP TABLE users; DROP TABLE wallets;"))
        finally:
            loop.run_until_complete(db._execute("""CREATE TABLE users (
                                               "user_id" integer NOT NULL UNIQUE,
                                               "first_name" text,
                                               "username" text,
                                               "locale" varchar(2) DEFAULT NULL
                                               )"""))
            loop.run_until_complete(db._execute("""CREATE TABLE wallets (
                                                "id" serial NOT NULL,
                                                "user_id" integer NOT NULL,
                                                "blockchain" text NOT NULL,
                                                "address" varchar(42) NOT NULL,
                                                "private_key" text DEFAULT NULL,
                                                "custom_name" text DEFAULT NULL
                                                )"""))
            print('ok')
            loop.run_until_complete(db.close_connect())

    async def _execute(self, *args, **kwargs):
        return await self.connect.execute(*args, **kwargs)

    async def _fetch(self, *args, **kwargs):
        return await self.connect.fetch(*args, **kwargs)

    async def _fetchrow(self, *args, **kwargs):
        return await self.connect.fetchrow(*args, **kwargs)

    async def _fetchval(self, *args, **kwargs):
        return await self.connect.fetchrow(*args, **kwargs)

    async def get_user_wallets(self, user_id, bch):
        wallets = await self._fetch(
            'SELECT id, address FROM wallets '
            'WHERE user_id = $1 AND blockchain = $2', user_id, bch)
        return wallets  # [id, address]

    async def get_user_locale(self, user_id):
        try:
            locale = await self._fetchrow('SELECT locale FROM users WHERE user_id = $1',
                                          user_id)
            if not locale:
                raise LocaleNotFound
            return locale[0]
        except asyncpg.UndefinedColumnError:
            raise LocaleNotFound

    async def set_user_locale(self, user_id, locale):
        await self._execute('UPDATE users SET locale = $1 WHERE user_id = $2',
                            locale, user_id)

    async def add_bch_address(self, user_id, bch, addr):
        await self._execute(
            'INSERT INTO wallets(user_id, blockchain, address) VALUES ($1, $2, $3)',
            user_id, bch, addr.lower())

    async def add_bch_address_with_pkey(self, user_id, bch, addr, pkey):
        await self._execute(
            'INSERT INTO wallets(user_id, blockchain, address, private_key) VALUES ($1, '
            '$2, $3, $4)', user_id, bch, addr.lower(), pkey)

    async def save_new_user(self, user_id, f_name, username):
        try:
            await self._execute('INSERT INTO users VALUES ($1, $2, $3)',
                                user_id, f_name, username)
        except asyncpg.UniqueViolationError:
            raise ExistingUser

    async def remove_wallet(self, user_id, bch, address):
        await self._execute(
            'DELETE FROM wallets WHERE user_id = $1 AND blockchain = $2 AND address = $3',
            user_id, bch, address)

    async def set_wallet_name(self, user_id, bch, address, name):
        await self._execute(
            'UPDATE wallets SET custom_name = $1'
            'WHERE user_id = $2 AND blockchain = $3 AND address = $4',
            name, user_id, bch, address)

    async def get_address_by_id(self, user_id, wallet_id):
        address = await self._fetchval(
            'SELECT address FROM wallets WHERE user_id = $1 AND id = $2',
            user_id, wallet_id)
        address = address.get('address')
        return address


class CacheDB(DB):
    cache = {}

    async def _create_connection(self, *args, **kwargs):
        self.connect = await asyncpg.connect(*args, **kwargs)

    def create_connection(self, *args, **kwargs):
        asyncio.get_event_loop().run_until_complete(
            self._create_connection(*args, **kwargs)
            )

    async def close_connect(self):
        await self.connect.close()

    def _get_user_cache(self, user_id):
        return self.cache.setdefault(user_id, {})

    async def get_user_locale(self, user_id):
        user = self._get_user_cache(user_id)
        if user.get('locale'):
            return user['locale']

        user_locale = await super().get_user_locale(user_id)
        user['locale'] = user_locale
        return user_locale

    async def set_user_locale(self, user_id, locale):
        await super().set_user_locale(user_id, locale)
        user = self._get_user_cache(user_id)
        user['locale'] = locale


if __name__ == '__main__':
    DB.create_tables(**db_params)
    pass
