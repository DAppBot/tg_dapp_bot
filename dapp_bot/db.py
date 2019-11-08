import asyncio
import asyncpg


from dapp_bot.config import db_params
from exceptions import *


class DB:

    async def _create_connection(self, *args, **kwargs):
        self.connect_poll = await asyncpg.create_pool(*args, **kwargs)
        self._is_connect = True


    def create_connection(self, *args, **kwargs):
        kwargs = db_params
        asyncio.get_event_loop().run_until_complete(
            self._create_connection(*args, **kwargs)
            )

    async def close_connect(self):
        await self.connect_poll.close()

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
                                               "locale" varchar(2) DEFAULT NULL,
                                                "bonus_is_paid" boolean DEFAULT false,
                                                "ref_link" text UNIQUE,
                                                "inviter_id" integer
                                               )"""))
            loop.run_until_complete(db._execute("""CREATE TABLE wallets (
                                                "id" serial NOT NULL,
                                                "user_id" integer NOT NULL,
                                                "blockchain" text NOT NULL,
                                                "address" varchar(42) NOT NULL,
                                                "private_key" text DEFAULT NULL,
                                                "custom_name" text DEFAULT NULL,
                                                "is_subscribe" boolean DEFAULT false
                                                )"""))
            print('ok')
            loop.run_until_complete(db.close_connect())

    async def _execute(self, *args, **kwargs):
        return await self.connect_poll.execute(*args, **kwargs)

    async def _fetch(self, *args, **kwargs):
        return await self.connect_poll.fetch(*args, **kwargs)

    async def _fetchrow(self, *args, **kwargs):
        return await self.connect_poll.fetchrow(*args, **kwargs)

    async def _fetchval(self, *args, **kwargs):
        return await self.connect_poll.fetchrow(*args, **kwargs)

    async def is_bonus(self, user_id):
        result = await self._fetchval(
            'SELECT bonus_is_paid = false and '
            '(SELECT COUNT(DISTINCT(blockchain)) >= 2 FROM wallets WHERE user_id = $1) '
            'FROM users WHERE user_id = $1', user_id)
        return result[0] if result else False

    async def get_ref_link(self, user_id):
        return (await self._fetchval('SELECT ref_link FROM users WHERE user_id = $1',
                                    user_id))[0]

    async def bonus_paid(self, user_id):
        return await self._execute("""UPDATE users
                                      SET bonus_is_paid = true 
                                      WHERE user_id = $1""", user_id)

    async def get_user_inviter(self, user_id):
        inviter_id = await self._fetchval("""SELECT inviter_id
                                             FROM users
                                             WHERE user_id = $1""", user_id)
        return inviter_id[0] if inviter_id else None


    async def save_bonus(self, user_id):
        await self._execute('UPDATE users SET bonus_is_paid = true WHERe user_id = $1',
                            user_id)

    async def get_user_wallets(self, user_id, bch):
        wallets = await self._fetch(
            'SELECT id, COALESCE(custom_name, LOWER(address)) '
            'FROM wallets WHERE user_id = $1 AND blockchain = $2', user_id, bch)
        return wallets  # [id, name/wallet]

    async def get_user_locale(self, user_id):
        try:
            locale = await self._fetchrow('SELECT locale FROM users WHERE user_id = $1',
                                          user_id)
        except asyncpg.UndefinedColumnError:
            raise LocaleNotFound
        else:
            if not locale:
                raise LocaleNotFound
            return locale[0]

    async def set_user_locale(self, user_id, locale):
        await self._execute('UPDATE users SET locale = $1 WHERE user_id = $2',
                            locale, user_id)

    async def add_bch_address(self, user_id, bch, addr):
        await self._execute(
            'INSERT INTO wallets(user_id, blockchain, address) VALUES ($1, $2, $3)',
            user_id, bch, addr)

    async def add_bch_address_with_pkey(self, user_id, bch, addr, pkey):
        await self._execute(
            'INSERT INTO wallets(user_id, blockchain, address, private_key) VALUES ($1, '
            '$2, $3, $4)', user_id, bch, addr, pkey)

    async def save_new_user(self, user_id, f_name, username, ref_link, inv_link=None):
        try:
            await self._execute(
                'INSERT INTO users(user_id, first_name, username, ref_link, inviter_id) '
                'VALUES ($1, $2, $3, $4, (SELECT user_id FROM users WHERE ref_link = '
                '$5))',
                user_id, f_name, username, ref_link, inv_link)
        except asyncpg.UniqueViolationError:
            raise ExistingUser

    async def get_number_of_invited(self, user_id):
        return (await self._fetchval("""SELECT COUNT(user_id)
                                       FROM users
                                       WHERE inviter_id = $1""",
                                       user_id
                                    ))[0]


    async def get_number_of_invited_with_bonus(self, user_id):
        return (await self._fetchval("""SELECT COUNT(user_id)
                                       FROM users
                                       WHERE inviter_id = $1 AND bonus_is_paid = true""",
                                       user_id
                                    ))[0]

    async def remove_wallet(self, wallet_id):
        await self._execute('DELETE FROM wallets WHERE id = $1', int(wallet_id))

    async def set_wallet_name(self, wallet_id, name):
        await self._execute(
            'UPDATE wallets SET custom_name = $1 WHERE id=$2', name, int(wallet_id))

    async def get_wallet_by_id(self, wallet_id):
        address = await self._fetchval(
            'SELECT address,'
            ' custom_name, is_subscribe FROM wallets WHERE id = $1',
            wallet_id)
        return address

    async def get_wallet_name_by_id(self, wallet_id):
        name = await self._fetchval(
            'SELECT custom_name FROM wallets WHERE id = $1', wallet_id)
        if name:
            return name[0]

    async def get_private_key(self, wallet_id):
        pkey = await self._fetchval(
            'SELECT private_key FROM wallets WHERE id = $1', wallet_id)
        if not pkey[0]:
            raise PKeyNotFound
        return pkey[0]

    async def get_subscribes_wallets(self, bch):
        wallets = await self._fetch(
            'SELECT id, address, user_id  FROM wallets WHERE is_subscribe = true AND '
            'blockchain = $1',
            bch)
        return wallets

    async def subscribe_addr_to_updates(self, wallet_id):
        await self._execute(
            'UPDATE wallets SET is_subscribe = CASE WHEN is_subscribe IS NOT NULL'
            ' THEN not is_subscribe ELSE true END WHERE id = $1', wallet_id)


class CacheDB(DB):
    cache = {}

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

    async def get_subscribes_wallets(self, bch):
        return await super().get_subscribes_wallets(bch)


if __name__ == '__main__':
    #DB.create_tables(**db_params)
    # print(asyncio.get_event_loop().run_until_complete(db.is_bonus(425439946)))
    pass