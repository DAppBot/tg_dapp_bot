from aiohttp import web

from .storage import pkey_storage
from exceptions import *

app = web.Application()
routes = web.RouteTableDef()


@routes.get('/pkey/{path:[a-zA-Z0-9]+}')
def pkey_handler(request: web.Request):
    path = request.match_info['path']
    try:
        pkey = pkey_storage.get_pkey_by_path(path)
    except PKeyNotFound:
        return web.HTTPNotFound()
    else:
        pkey_storage.remove_pkey_path(path)
        return web.Response(text=pkey)

app.add_routes(routes)

app_coro = web._run_app(app)

