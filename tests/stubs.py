from aiohttp import web


def _return_json(data):
    async def wrap(req):
        if req.method == "POST":
            req_data = dict(await req.post())
            if req_data:
                rv = dict(req_data=req_data, **data)
                return web.json_response(rv)
        return web.json_response(data)
    return wrap


def _return_text(string, **kwargs):
    async def wrap(req):
        return web.Response(text=string, **kwargs)
    return wrap


def create_app():
    app = web.Application()
    app.router.add_get("/get_null", _return_json({}))
    app.router.add_get("/get_null_text", _return_text("", content_type="application/json"))

    app.router.add_post("/post_null", _return_json({}))
    app.router.add_post("/post_null_text", _return_text("", content_type="application/json"))
    app.router.add_post("/sync", _return_json({}))

    return app
