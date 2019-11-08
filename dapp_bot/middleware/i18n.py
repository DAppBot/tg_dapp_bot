from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.dispatcher import Dispatcher as dp
from babel.support import LazyProxy
from eth_utils import from_wei
from aiogram.types import User

from exceptions import *
from dapp_bot.config import get_root_path




class CustomI18n(I18nMiddleware):
    async def get_user_locale(self, action, args) -> str:
        user = User.get_current()
        db = dp.get_current()['db']
        try:  # пробуем достать локаль из базы
            return await db.get_user_locale(user.id)
        except LocaleNotFound:  # возвращаем локаль, которую вернул телеграм
            if user.locale:
                return user.locale.language
            return 'ru'

    def lazy_gettext(self, *args):
        return LazyProxy(self.gettext, *args, enable_cache=False)

i18n = CustomI18n('bot', path=get_root_path())

