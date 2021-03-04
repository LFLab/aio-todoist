from asyncio import isfuture, iscoroutine, ensure_future, sleep, CancelledError
from unittest.mock import patch, MagicMock

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

import aiotodoist
from tests.stubs import create_app

try:
    from unittest.mock import AsyncMock  # type: ignore[attr-defined]
except ImportError:
    from asynctest import CoroutineMock as AsyncMock


class TestAsyncTodoistAPI(AioHTTPTestCase):

    async def get_application(self):
        return create_app()

    async def setUpAsync(self):
        await super().setUpAsync()
        self.api = aiotodoist.AsyncTodoistAPI("DUMMY_TOKEN",
                                              session=self.client,
                                              cache=None)
        self.api.get_api_url = lambda: "/"
        # API endpoint and version does not matter.

    def test__get(self):
        with patch.object(self.api.session, "get") as m_get:
            resp = MagicMock()
            m_get.return_value = resp
            self.api._get("get_null")
        m_get.assert_called_once_with("/get_null")
        resp.close.assert_not_called()

    def test__post(self):
        with patch.object(self.api.session, "post") as m_post:
            resp = MagicMock()
            m_post.return_value = resp
            self.api._post("post_null")
        m_post.assert_called_once_with("/post_null")
        resp.close.assert_not_called()

    @unittest_run_loop
    async def test__get_async(self):
        resp = await self.api._get_async("get_null")
        self.assertEqual(resp, {})

        resp = await self.api._get_async("get_null_text")
        self.assertIsNone(resp)

    @unittest_run_loop
    async def test__post_async(self):
        resp = await self.api._post_async("post_null")
        self.assertEqual(resp, {})

        resp = await self.api._post_async("post_null_text")
        self.assertIsNone(resp)

    @unittest_run_loop
    async def test__post_async_multipart(self):
        data = dict(task="wtf")
        file_data = dict(file="123")

        resp = await self.api._post_async("post_null", data=data)
        self.assertEqual(resp.get("req_data"), data)

        resp = await self.api._post_async("post_null", files=file_data)
        self.assertEqual(resp.get("req_data"), file_data)

        resp = await self.api._post_async("post_null", data=data, files=file_data)
        self.assertEqual(resp.get("req_data"), {**data, **file_data})

    @unittest_run_loop
    async def test__get_redirect(self):
        with patch.object(self.api.session, "get", new=AsyncMock()) as m_get, \
                patch.object(self.api, "_get_async", new=AsyncMock()) as m_aget:
            await self.api._get("get_null")

        m_get.assert_called()
        m_get.assert_not_awaited()

        m_aget.assert_called_with("get_null", self.api.get_api_url())
        m_aget.assert_awaited()

    @unittest_run_loop
    async def test__post_redirect(self):
        with patch.object(self.api.session, "post", new=AsyncMock()) as m_post, \
                patch.object(self.api, "_post_async", new=AsyncMock()) as m_apost:
            await self.api._post("post_null")

            m_post.assert_called()
            m_post.assert_not_awaited()
            m_apost.assert_called_with("post_null", self.api.get_api_url())
            m_apost.assert_awaited()

            m_post.reset_mock(), m_apost.reset_mock()
            file_data = dict(file="dummy")
            await self.api._post("post_null", files=file_data)
            m_apost.assert_called_with("post_null", self.api.get_api_url(),
                                       files=file_data)

    def test_sync(self):
        m = MagicMock()
        dummy_in = dict(dummy=True, temp_id_mapping=m)
        with patch.object(self.api, "_post", return_value=dummy_in):
            resp = self.api.sync()
            self.assertEqual(resp, dummy_in)
            m.items.assert_called()

    def test_sync_future_callback(self):
        with patch("aiotodoist.api.ensure_future") as ensure_future:
            resp = self.api.sync()

            ensure_future.assert_called_once()

        coro = ensure_future.call_args[0][0]
        self.assertTrue(iscoroutine(coro))
        coro.close()

        self.assertEqual(resp, ensure_future.return_value)
        resp.add_done_callback.assert_called_once()

    @unittest_run_loop
    async def test_sync_awaitable(self):
        fut = self.api.sync()
        self.assertTrue(isfuture(fut))
        fut.cancel()

        resp = await self.api.sync()
        self.assertIn("token", resp.get("req_data"))
        self.assertEqual(self.api.token, resp["req_data"]["token"])
        self.assertEqual("[]", resp["req_data"].get("commands"))

    def test_commit(self):
        with patch.object(self.api, "sync") as m_sync:
            self.api.commit()

            m_sync.assert_not_called()

        commands = ["a", "b", "c"]
        self.api.queue.extend(commands)
        with patch.object(self.api, "sync") as m_sync:
            resp = self.api.commit()

            m_sync.assert_called_with(commands=commands)
            self.assertEqual([], self.api.queue)
            self.assertEqual(resp, m_sync.return_value)

    @unittest_run_loop
    async def test_commit_when_connection_fail(self):
        commands = ["a", "b", "c"]
        self.api.queue.extend(commands)

        # sync scenario
        with patch.object(self.api, "sync", side_effect=TimeoutError),\
                self.assertRaises(TimeoutError):
            self.api.commit()
            self.assertEqual(self.api.queue, commands)

        # Future scenario 1
        fut = self.api.commit()
        fut.cancel()

        self.assertEqual(self.api.queue, [])
        with self.assertRaises(CancelledError):
            await fut
        self.assertEqual(self.api.queue, commands)

        # Future scenario 2: commit without await
        fut2 = self.api.commit()
        fut2.cancel()

        self.assertEqual(self.api.queue, [])
        await sleep(0.1)  # let done_callback spawn
        self.assertEqual(self.api.queue, commands)
        with self.assertRaises(CancelledError):
            fut2.result()

    @unittest_run_loop
    async def test_commit_when_return_not_ok(self):
        rv = dict(sync_status=dict(task="not_ok"))
        commands = ["a", "b", "c"]

        # sync scenario
        self.api.queue.extend(commands)
        with patch.object(self.api, "sync", return_value=rv):
            self.api.commit(raise_on_error=False)
            self.assertEqual(self.api.queue, [])

        self.api.queue.extend(commands)
        with patch.object(self.api, "sync", return_value=rv), \
                self.assertRaises(aiotodoist.api.SyncError):
            self.api.commit(raise_on_error=True)
            self.assertEqual(self.api.queue, [])

        def _helper(**kw):
            async def n():
                return rv
            return ensure_future(n())
        # async scenario
        self.api.queue.extend(commands)
        with patch.object(self.api, "sync", side_effect=_helper):
            ret = await self.api.commit(raise_on_error=False)
        self.assertEqual(ret, rv)
        self.assertEqual(self.api.queue, [])

        self.api.queue.extend(commands)
        with patch.object(self.api, "sync", side_effect=_helper),\
                self.assertRaises(aiotodoist.api.SyncError):
            ret = await self.api.commit(raise_on_error=True)
            self.assertEqual(ret, rv)
            self.assertEqual(self.api.queue, [])
