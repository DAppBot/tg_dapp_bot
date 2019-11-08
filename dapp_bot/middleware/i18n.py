from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.dispatcher import Dispatcher as dp
from babel.support import LazyProxy
from aiogram.types import User
from exceptions import *



class CustomI18n(I18nMiddleware):
    async def get_user_locale(self, action, args) -> str:
        db = dp.get_current()['db']
        user = User.get_current()
        try:  # пробуем достать локаль из базы
            return await db.get_user_locale(user.id)
        except LocaleNotFound:  # возвращаем локаль, которую вернул телеграм
            return user.locale.language

    def lazy_gettext(self, *args):
        return LazyProxy(self.gettext, *args, enable_cache=False)

i18n = CustomI18n('bot')
_ = i18n.gettext
