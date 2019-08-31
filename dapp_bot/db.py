import asyncio
import asyncpg

import utils

from config import db_params
from exceptions import *


class DB(object):

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
                                                        "user_id" integer NOT NULL,
                                                        "blockchain" text NOT NULL,
                                                        "address" varchar(32) NOT NULL,
                                                        "private_key" text DEFAULT NULL
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

    async def get_user_wallets(self, user_id):
        wallets = await self._fetch('SELECT address FROM wallets WHERE user_id = $1',
                                       user_id)
        return utils.compose_wallets(wallets)

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

    async def save_new_user(self, user_id, f_name, username):
        try:
            await self._execute('INSERT INTO users VALUES ($1, $2, $3)',
                                user_id, f_name, username)
        except asyncpg.UniqueViolationError:
            raise ExistingUser


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

    async def get_user_locale(self, user_id):
        user = self.cache.get(user_id)

        if not user:
            self.cache[user_id] = {}
        elif user.get('locale'):
            return user['locale']

        user_locale = await super().get_user_locale(user_id)
        self.cache[user_id]['locale'] = user_locale
        return user_locale


if __name__ == '__main__':
    DB.create_tables(**db_params)
