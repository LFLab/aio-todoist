from asyncio import iscoroutine, isfuture, ensure_future

from aiohttp import ClientSession
from todoist.api import TodoistAPI, json_dumps, SyncError

from .managers import (AsyncUserManager,
                       AsyncFiltersManager,
                       AsyncItemsManager,
                       AsyncLabelsManager,
                       AsyncNotesManager,
                       AsyncProjectsManager,
                       AsyncProjectNotesManager,
                       AsyncRemindersManager,
                       AsyncSectionsManager,
                       AsyncItemsArchiveManagerMaker,
                       AsyncSectionsArchiveManagerMaker,
                       )


class AsyncTodoistAPI(TodoistAPI):

    #: we dont expact that you will change the endpoint and version,
    #: so let it be class attributes.
    API_ENDPOINT = "https://api.todoist.com"
    API_VERSION = "v8"

    def __init__(self, token="", session=None, cache="~/.todoist-sync/"):
        session = session or ClientSession()
        super().__init__(token, session=session, cache=cache)

        self.user = AsyncUserManager(self)
        self.filters = AsyncFiltersManager(self)
        self.items = AsyncItemsManager(self)
        self.labels = AsyncLabelsManager(self)
        self.notes = AsyncNotesManager(self)
        self.projects = AsyncProjectsManager(self)
        self.project_notes = AsyncProjectNotesManager(self)
        self.reminders = AsyncRemindersManager(self)
        self.sections = AsyncSectionsManager(self)
        self.items_archive = AsyncItemsArchiveManagerMaker(self)
        self.sections_archive = AsyncSectionsArchiveManagerMaker(self)

    def _get(self, call, url=None, **kwargs):
        url = url or self.get_api_url()

        resp = self.session.get(url + call, **kwargs)
        if iscoroutine(resp):
            resp.close()
            return self._get_async(call, url, **kwargs)

        try:
            return resp.json()
        except ValueError:
            return resp.text

    def _post(self, call, url=None, **kwargs):
        url = url or self.get_api_url()

        try:
            resp = self.session.post(url + call, **kwargs)
        except TypeError:  # keyword `files` is not available in aiohttp.
            return self._post_async(call, url, **kwargs)

        if iscoroutine(resp):
            resp.close()
            return self._post_async(call, url, **kwargs)

        try:
            return resp.json()
        except ValueError:
            return resp.text

    async def _get_async(self, call, url=None, **kwargs):
        url = url or self.get_api_url()

        resp = await self.session.get(url + call, **kwargs)

        try:
            return await resp.json()
        except ValueError:
            return await resp.text()

    async def _post_async(self, call, url=None, *, data=None, files=None, **kwargs):
        url = url or self.get_api_url()

        data = {**(data or {}), **(files or {})}
        resp = await self.session.post(url + call, data=data, **kwargs)

        try:
            return await resp.json()
        except ValueError:
            return await resp.text()

    def sync(self, commands=None):
        def _callback(fut=None, response=None):
            response = response or fut.result()
            if "temp_id_mapping" in response:
                for temp_id, new_id in response["temp_id_mapping"].items():
                    self.temp_ids[temp_id] = new_id
                    self._replace_temp_id(temp_id, new_id)
            self._update_state(response)
            self._write_cache()

        post_data = {
            "token": self.token,
            "sync_token": self.sync_token,
            "day_orders_timestamp": self.state["day_orders_timestamp"],
            "include_notification_settings": 1,
            "resource_types": json_dumps(["all"]),
            "commands": json_dumps(commands or []),
        }
        response = self._post("sync", data=post_data)
        if iscoroutine(response):
            response = ensure_future(response)
            response.add_done_callback(_callback)
        else:
            _callback(response=response)
        return response

    def commit(self, raise_on_error=True):
        async def _helper(fut):
            try:
                ret = await fut
            except Exception as e:
                self.queue[:] = queue + self.queue[:]
                raise e
            _callback(ret)
            return ret

        def _check_cancel(dest_fut):
            if dest_fut.cancelled():
                src_fut.cancel()
                self.queue[:] = queue + self.queue[:]

        def _callback(ret):
            if raise_on_error and "sync_status" in ret:
                for k, v in ret["sync_status"].items():
                    if v != "ok":
                        raise SyncError(k, v)

        if self.queue:
            queue = self.queue[:]
            ret = self.sync(commands=queue)
            self.queue[:] = []
            if isfuture(ret):
                src_fut = ret
                ret = ensure_future(_helper(src_fut))
                ret.add_done_callback(_check_cancel)
            else:
                _callback(ret)

            return ret
