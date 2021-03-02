from asyncio import iscoroutine, ensure_future

from todoist.models import Item, Section
from todoist.managers.user import UserManager
from todoist.managers.items import ItemsManager
from todoist.managers.notes import NotesManager, ProjectNotesManager
from todoist.managers.labels import LabelsManager
from todoist.managers.filters import FiltersManager
from todoist.managers.projects import ProjectsManager
from todoist.managers.reminders import RemindersManager
from todoist.managers.sections import SectionsManager
from todoist.managers.archive import (ArchiveManager,
                              SectionsArchiveManager,
                              ItemsArchiveManager)


class AsyncUserManager(UserManager):
    def login(self, email, password):
        def _callback(fut=None, data=None):
            data = data or fut.result()
            if "token" in data:
                self.api.token = data["token"]

        data = self.api._post("user/login", data=dict(email=email, password=password))
        if iscoroutine(data):
            data = ensure_future(data)
            data.add_done_callback(_callback)
        else:
            _callback(data=data)
        return data

    def login_with_google(self, email, oauth2_token, **kwargs):
        def _callback(fut=None, resp=None):
            data = resp or fut.result()
            if "token" in data:
                self.api.token = data["token"]

        data = dict(email=email, oauth2_token=oauth2_token, **kwargs)
        resp = self.api._post("user/login_with_google", data=data)
        if iscoroutine(resp):
            resp = ensure_future(resp)
            resp.add_done_callback(_callback)
        else:
            _callback(resp=resp)
        return resp

    def register(self, email, full_name, password, **kwargs):
        def _callback(fut=None, resp=None):
            data = resp or fut.result()
            if "token" in data:
                self.api.token = data["token"]

        data = dict(email=email, full_name=full_name, password=password, **kwargs)
        resp = self.api._post("user/register", data=data)
        if iscoroutine(resp):
            resp = ensure_future(resp)
            resp.add_done_callback(_callback)
        else:
            _callback(resp=resp)
        return resp


class AsyncFiltersManager(FiltersManager):

    def get(self, filter_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            data = dict(filters=[])
            if obj.get("filter"):
                data["filters"].append(obj.get("filter"))
            self.api._update_state(data)

        params = dict(token=self.token, filter_id=filter_id)
        obj = self.api._get("filters/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncItemsManager(ItemsManager):

    def get(self, item_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                # ???: the origin behavior return `None` when error occurred,
                # which actually made return type inconsitent, so we change
                # it to return the same type but with empty content.
                obj.clear()
            else:
                data = dict(projects=[], items=[], notes=[])
                if obj.get("project"):
                    data["projects"].append(obj.get("project"))
                if obj.get("item"):
                    data["items"].append(obj.get("item"))
                if obj.get("notes"):
                    data["notes"].extend(obj.get("notes"))
                self.api._update_state(data)

        params = dict(token=self.token, item_id=item_id)
        obj = self.api._get("items/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncLabelsManager(LabelsManager):

    def get(self, label_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                obj.empty()
            else:
                data = dict(labels=[])
                if obj.get("label"):
                    data["labels"].append(obj.get("label"))
                self.api._update_state(data)

        params = dict(token=self.token, label_id=label_id)
        obj = self.api._get("labels/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncNotesManager(NotesManager):

    def get(self, note_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                obj.empty()
            else:
                data = dict(notes=[])
                if obj.get("note"):
                    data["notes"].append(obj.get("note"))
                    self.api._update_state(data)

        params = dict(token=self.token, note_id=note_id)
        obj = self.api._get("notes/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncProjectNotesManager(ProjectNotesManager):

    def get(self, note_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                obj.empty()
            else:
                data = dict(project_notes=[])
                if obj.get("note"):
                    data["project_notes"].append(obj.get("note"))
                    self.api._update_state(data)

        params = dict(token=self.token, note_id=note_id)
        obj = self.api._get("notes/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncProjectsManager(ProjectsManager):

    def get(self, project_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                obj.empty()
            else:
                data = dict(projects=[], project_notes=[])
                if obj.get("project"):
                    data["projects"].append(obj.get("project"))
                if obj.get("notes"):
                    data["project_notes"].extend(obj.get("notes"))
                self.api._update_state(data)

        params = dict(token=self.token, project_id=project_id)
        obj = self.api._get("projects/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncRemindersManager(RemindersManager):

    def get(self, reminder_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                obj.empty()
            else:
                data = dict(reminders=[])
                if obj.get("reminder"):
                    data["reminders"].append(obj.get("reminder"))
                self.api._update_state(data)

        params = dict(token=self.token, reminder_id=reminder_id)
        obj = self.api._get("reminders/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class AsyncSectionsManager(SectionsManager):

    def get(self, section_id):
        def _callback(fut=None, obj=None):
            obj = obj or fut.result()
            if obj and "error" in obj:
                obj.empty()
            else:
                data = dict(sections=[])
                if obj.get("section"):
                    data["sections"].append(obj.get("section"))
                self.api._update_state(data)

        params = dict(token=self.token, section_id=section_id)
        obj = self.api._get("sections/get", params=params)
        if iscoroutine(obj):
            obj = ensure_future(obj)
            obj.add_done_callback(_callback)
        else:
            _callback(obj=obj)
        return obj


class _AsyncArchiveManager(ArchiveManager):

    def next_page(self, cursor):
        resp = self.api.session.get(
            self._next_url(),
            params=self._next_query_params(cursor),
            headers=self._request_headers(),
        )
        if iscoroutine(resp):
            resp.close()
            return self._next_page_async(cursor)
        resp.raise_for_status()
        return resp.json()

    async def _next_page_async(self, cursor):
        resp = await self.api.session.get(
            self._next_url(),
            params=self._next_query_params(cursor),
            headers=self._request_headers(),
        )
        resp.raise_for_status()
        return await resp.json()

    async def __aiter__(self):
        has_more, cursor = True, None
        while has_more:
            resp = await self.next_page(cursor)
            has_more, cursor = resp["has_more"], resp.get("next_cursor")
            elms = (self._make_element(data) for data in resp[self.element_type])
            for el in elms:
                yield el


class AsyncSectionsArchiveManager(_AsyncArchiveManager):

    object_model = Section

    def __init__(self, api, project_id):
        super().__init__(api, "sections")
        self.project_id = project_id

    def __repr__(self):
        return f'{__class__.__name__}("project_id"={project_id})'

    def sections(self):
        if iscoroutine(self.next_page(None)):
            return self.__aiter__()
        else:
            return self._iterate()

    def _next_query_params(self, cursor):
        rv = super()._next_query_params(cursor)
        rv["project_id"] = self.project_id
        return rv


class AsyncItemsArchiveManager(_AsyncArchiveManager):

    object_model = Item
    _locations = ("project", "section", "parent")

    def __init__(self, api, located, uid):
        assert located in self._locations
        super().__init__(api, "items")
        self._locate_info = (f"{located}_id", uid)
        setattr(self, *self._locate_info)  # for convenience

    def __repr__(self):
        name, uid = self._locate_info
        return f"ItemsArchiveManager({name}={uid})"

    def _next_query_params(self, cursor):
        rv = super()._next_query_params(cursor)
        rv.update([self._locate_info])
        return rv

    def items(self):
        data = self.next_page(None)
        if iscoroutine(data):
            data.close()
            return self.__aiter__()
        else:
            return self._iterate()


class AsyncSectionsArchiveManagerMaker:

    __slots__ = "api",

    def __init__(self, api):
        self.api = api

    def __repr__(self):
        return f"{__class__.__name__}({self.api})"

    def for_project(self, project_id):
        return AsyncSectionsArchiveManager(self.api, project_id)


class AsyncItemsArchiveManagerMaker:

    __slots__ = ("api", )

    def __init__(self, api):
        self.api = api

    def __repr__(self):
        return f"{__class__.__name__}({self.api})"

    def for_project(self, project_id):
        return AsyncItemsArchiveManager(self.api, "project", project_id)

    def for_section(self, section_id):
        return AsyncItemsArchiveManager(self.api, "section", section_id)

    def for_parent(self, parent_id):
        return AsyncItemsArchiveManager(self.api, "parent", parent_id)
