import sys
import asyncio
from copy import copy
from json import dumps
from traceback import print_exc
from argparse import ArgumentParser

from todoist import models
from todoist.api import json_default as _json_default
from aiotodoist import AsyncTodoistAPI

model_cls = {
    "collaborators": models.Collaborator,
    "collaborator_states": models.CollaboratorState,
    "filters": models.Filter,
    "items": models.Item,
    "labels": models.Label,
    "live_notifications": models.LiveNotification,
    "notes": models.Note,
    "project_notes": models.ProjectNote,
    "projects": models.Project,
    "reminders": models.Reminder,
    "sections": models.Section,
}


def json_default(obj):
    if isinstance(obj, models.Model):
        return {type(obj).__name__: dict(obj.data)}
    return _json_default(obj)


class Handler:

    __slots__ = ("api", )

    def __init__(self, api):
        self.api = api

    def on_error(self, exception):
        """
        :type exception: Exception
        """
        raise NotImplementedError

    def on_data(self, news, updates, deletes, others):
        """
        :type news: dict[str, list]
        :type updates: dict[str, list]
        :type deletes: dict[str, list]
        :type others: dict[str, str|int|bool|dict]
        """
        raise NotImplementedError


class Cli(Handler):

    indent = 2

    def on_error(self, exception):
        print_exc(file=sys.stderr)

    def on_data(self, news, updates, deletes, others):

        print(dumps([news, updates, deletes, others],
                    indent=self.indent, separators=",:", default=json_default))


def _process_data(api, data):
    news, updates, deletes = {}, {}, {}
    for dtype, m_cls in model_cls.items():
        for rdata in data.get(dtype, []):
            local_obj = api._find_object(dtype, rdata)
            if local_obj:
                if rdata.get("is_deleted"):
                    deletes.setdefault(dtype, []).append(m_cls(rdata, api))
                else:
                    updates.setdefault(dtype, []).append(m_cls(rdata, api))
            else:
                if not rdata.get("is_deleted"):
                    news.setdefault(dtype, []).append(m_cls(rdata, api))
    others = {k: copy(v) for k, v in data.items() if k not in model_cls.keys()}
    return news, updates, deletes, others


async def subscribe(api, handler, error_handler, delay=5, relax=1):
    while True:
        data = dict()
        try:
            fut = api.sync()
            cb, ctx = fut._callbacks[0]
            fut.remove_done_callback(cb)

            data = await fut
            if data:
                infos = _process_data(api, data)

            fut._loop.call_soon(cb, fut, context=ctx)
        except Exception as e:
            error_handler(e)
            await asyncio.sleep(relax)
            continue
        try:
            coro = handler(*infos)
            if asyncio.iscoroutine(coro):
                await coro
        except Exception as e:
            error_handler(e)

        await asyncio.sleep(delay)


async def main(args):
    api = AsyncTodoistAPI(args.token, cache=args.cache)
    hdlr = Cli(api)
    hdlr.indent = args.indent if args.indent > 0 else None

    try:
        if not api.sync_token:
            # first time, pull all states.
            await api.sync()
        await subscribe(api, hdlr.on_data, hdlr.on_error, args.delay, args.relax)
    finally:
        await api.session.close()


if __name__ == '__main__':
    arg = ArgumentParser(prog="subtodo", description=__doc__)
    arg.add_argument("token", metavar="API_TOKEN", help="user token")
    arg.add_argument("-d", "--dir", default="./.todoist-sync/",
                     dest="cache", metavar="CacheFolder",
                     help=r"The temp folder to store api state."
                          r"  Default: `./todoist-sync/`")
    arg.add_argument("-t", "--tick", default=5, type=int, dest="delay",
                     help=r"The frequecy to do sync().  Default: 5 (seconds)")
    arg.add_argument("-i", "--idle", default=1, type=int, dest="relax",
                     help=r"The frequency to do nothing when error occurred."
                          r"  Default: 1 (seconds)")
    arg.add_argument("-s", "--spaces", default=2, type=int, dest="indent",
                     help=r"The spaces for json.dumps, set 0 to compact output."
                          r"  Default: 2")

    def _(*args):
        raise KeyboardInterrupt

    import signal
    signal.signal(signal.SIGTSTP, _)

    try:
        asyncio.run(main(arg.parse_args()))
    except KeyboardInterrupt:
        print("\nExiting...\n", file=sys.stderr)
