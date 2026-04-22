from __future__ import annotations

import datetime
import pathlib
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from open_workshop_access import manager_client
from open_workshop_access.app import app
from open_workshop_access.contracts.state import (
    ACCESS_PUBLIC_CONTEXT_FIELDS,
    AccessModEntry,
    AccessState,
)


def make_context(**overrides) -> AccessState:
    payload = {
        "authenticated": True,
        "owner_id": 7,
        "login_method": "password",
        "admin": False,
        "write_comments": False,
        "set_reactions": False,
        "create_reactions": False,
        "mute_users": False,
        "publish_mods": False,
        "change_authorship_mods": False,
        "change_self_mods": False,
        "change_mods": False,
        "delete_self_mods": False,
        "delete_mods": False,
        "create_forums": False,
        "change_authorship_forums": False,
        "change_self_forums": False,
        "change_forums": False,
        "delete_self_forums": False,
        "delete_forums": False,
        "change_username": False,
        "change_about": False,
        "change_avatar": False,
        "vote_for_reputation": False,
        "mods": None,
    }
    payload.update(overrides)
    return AccessState(**payload)


def make_mod(
    mod_id: int,
    *,
    public: int = 0,
    owner: bool = False,
    member: bool = False,
) -> AccessModEntry:
    return AccessModEntry(
        mod_id=mod_id,
        public=public,
        owner=owner,
        member=member,
    )


INTERNAL_STATE_FIELDS = (
    "owner_id",
    "admin",
    "create_reactions",
    "mute_users",
    "publish_mods",
    "change_authorship_mods",
    "change_self_mods",
    "change_mods",
    "delete_self_mods",
    "delete_mods",
    "create_forums",
    "change_authorship_forums",
    "change_self_forums",
    "change_forums",
    "delete_self_forums",
    "delete_forums",
    "change_username",
    "change_about",
    "change_avatar",
    "mods",
)

PROFILE_EXPLICIT_RIGHT_FIELDS = (
    "write_comments",
    "set_reactions",
    "vote_for_reputation",
)


class AccessEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()

    def request(self, method: str, path: str, *, json: dict | None = None):
        return self.client.request(method, path, json=json)

    def test_context_returns_manager_context(self) -> None:
        context = make_context(owner_id=11, publish_mods=True)
        fetch_mock = AsyncMock(return_value=context)

        with patch.object(manager_client, "fetch_manager_context", fetch_mock):
            response = self.request("POST", "/context")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["login_method"], "password")
        for leaked_field in INTERNAL_STATE_FIELDS + PROFILE_EXPLICIT_RIGHT_FIELDS:
            self.assertNotIn(leaked_field, body)
        self.assertEqual(fetch_mock.await_args.kwargs, {})

    def test_public_context_projection_is_whitelist_only(self) -> None:
        now = datetime.datetime.now()
        context = make_context(
            owner_id=11,
            admin=True,
            write_comments=True,
            set_reactions=True,
            publish_mods=True,
            change_self_mods=True,
            change_username=True,
            change_about=True,
            change_avatar=True,
            vote_for_reputation=True,
            mute_until=now,
            last_username_reset=now,
            last_password_reset=now,
            password_change_available_at=now,
            username_change_available_at=now,
            mods=[make_mod(1, owner=True)],
        )

        public_body = context.to_public_context().model_dump(exclude_none=True)

        self.assertTrue(
            set(public_body).issubset(set(ACCESS_PUBLIC_CONTEXT_FIELDS)),
        )
        for leaked_field in INTERNAL_STATE_FIELDS + PROFILE_EXPLICIT_RIGHT_FIELDS:
            self.assertNotIn(leaked_field, public_body)
        self.assertIn("authenticated", public_body)
        self.assertIn("login_method", public_body)

    def test_openapi_responses_do_not_expose_mods(self) -> None:
        response = self.client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        schemas = response.json()["components"]["schemas"]

        for schema_name in (
            "AccessContext",
            "SimpleCrudResponse",
            "ModAddResponse",
            "GameAddResponse",
            "GameResponse",
            "ModResponse",
        ):
            with self.subTest(schema=schema_name):
                for leaked_field in (
                    INTERNAL_STATE_FIELDS + PROFILE_EXPLICIT_RIGHT_FIELDS
                ):
                    self.assertNotIn(
                        leaked_field,
                        schemas[schema_name].get("properties", {}),
                    )

        profile_properties = schemas["ProfileResponse"].get("properties", {})
        for leaked_field in INTERNAL_STATE_FIELDS:
            self.assertNotIn(leaked_field, profile_properties)
        for exposed_field in PROFILE_EXPLICIT_RIGHT_FIELDS:
            self.assertIn(exposed_field, profile_properties)

    def test_mod_add_returns_anonymous_add_right(self) -> None:
        context = make_context(publish_mods=True)

        with patch.object(manager_client, "fetch_manager_context", AsyncMock(return_value=context)):
            response = self.request("PUT", "/mod")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["add"]["value"])
        self.assertFalse(body["anonymous_add"]["value"])
        self.assertEqual(body["add"]["reason_code"], "allowed")
        self.assertEqual(body["anonymous_add"]["reason_code"], "admin_required")

    def test_mod_add_allows_anonymous_add_for_admin(self) -> None:
        context = make_context(admin=True)

        with patch.object(manager_client, "fetch_manager_context", AsyncMock(return_value=context)):
            response = self.request("PUT", "/mod")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["add"]["value"])
        self.assertTrue(body["anonymous_add"]["value"])
        self.assertEqual(body["anonymous_add"]["reason_code"], "admin")

    def test_mod_access_returns_owner_and_author_rules(self) -> None:
        context = make_context(
            change_self_mods=True,
            delete_self_mods=True,
            mods=[make_mod(10, owner=True)],
        )

        with patch.object(manager_client, "fetch_manager_context", AsyncMock(return_value=context)):
            response = self.request("POST", "/mod/10", json={"author_id": 7, "mode": False})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["info"]["value"])
        self.assertTrue(body["edit"]["title"]["value"])
        self.assertFalse(body["edit"]["authors"]["value"])
        self.assertTrue(body["delete"]["value"])
        self.assertTrue(body["download"]["value"])

    def test_mods_batch_uses_static_user_context(self) -> None:
        context = make_context(
            authenticated=False,
            owner_id=12,
            change_self_mods=True,
            delete_self_mods=True,
            mods=[
                make_mod(1, owner=True),
                make_mod(2, public=0),
                make_mod(3, member=True),
            ],
        )
        fetch_mock = AsyncMock(return_value=context)

        with patch.object(manager_client, "fetch_manager_context", fetch_mock):
            response = self.request(
                "POST",
                "/mods",
                json={"mods_ids": [1, 2, 3]},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(list(body.keys()), ["1", "2", "3"])
        self.assertTrue(body["1"]["info"]["value"])
        self.assertTrue(body["1"]["edit"]["title"]["value"])
        self.assertTrue(body["1"]["delete"]["value"])
        self.assertTrue(body["2"]["info"]["value"])
        self.assertFalse(body["2"]["edit"]["title"]["value"])
        self.assertFalse(body["2"]["delete"]["value"])
        for mod_body in body.values():
            for leaked_field in INTERNAL_STATE_FIELDS + PROFILE_EXPLICIT_RIGHT_FIELDS:
                self.assertNotIn(leaked_field, mod_body)
        self.assertEqual(fetch_mock.await_args.kwargs, {"mod_ids": [1, 2, 3]})

    def test_tags_and_genres_return_admin_crud_rights(self) -> None:
        context = make_context(admin=True)

        for path in ("/tags", "/genres"):
            with self.subTest(path=path):
                with patch.object(
                    manager_client,
                    "fetch_manager_context",
                    AsyncMock(return_value=context),
                ):
                    response = self.request("PATCH", path, json={})

                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertTrue(body["add"]["value"])
                self.assertTrue(body["edit"]["value"])
                self.assertTrue(body["delete"]["value"])
                self.assertEqual(body["add"]["reason_code"], "admin")

    def test_game_routes_return_admin_template(self) -> None:
        context = make_context(admin=False)

        for method, path in (("PUT", "/game"), ("POST", "/game/5")):
            with self.subTest(path=path):
                with patch.object(
                    manager_client,
                    "fetch_manager_context",
                    AsyncMock(return_value=context),
                ):
                    response = self.request(method, path, json={})

                self.assertEqual(response.status_code, 200)
                body = response.json()
                if path == "/game":
                    self.assertFalse(body["add"]["value"])
                    self.assertEqual(body["add"]["reason_code"], "forbidden")
                else:
                    self.assertFalse(body["edit"]["title"]["value"])
                    self.assertFalse(body["delete"]["value"])

    def test_profile_self_returns_cooldown_reason(self) -> None:
        now = datetime.datetime.now()
        context = make_context(
            owner_id=7,
            change_username=True,
            username_change_available_at=now + datetime.timedelta(days=10),
        )

        with patch.object(manager_client, "fetch_manager_context", AsyncMock(return_value=context)):
            response = self.request("POST", "/profile/7", json={})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["edit"]["nickname"]["reason_code"], "cooldown")
        self.assertEqual(body["delete"]["reason_code"], "self")

    def test_profile_self_returns_mute_reasons(self) -> None:
        now = datetime.datetime.now()
        context = make_context(
            owner_id=7,
            change_about=True,
            change_avatar=True,
            vote_for_reputation=True,
            write_comments=True,
            set_reactions=True,
            mute_until=now + datetime.timedelta(hours=1),
        )

        with patch.object(manager_client, "fetch_manager_context", AsyncMock(return_value=context)):
            response = self.request("POST", "/profile/7", json={})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["edit"]["description"]["reason_code"], "muted")
        self.assertEqual(body["edit"]["avatar"]["reason_code"], "muted")
        self.assertEqual(body["vote_for_reputation"]["reason_code"], "muted")
        self.assertEqual(body["write_comments"]["reason_code"], "muted")
        self.assertEqual(body["set_reactions"]["reason_code"], "muted")
        self.assertTrue(body["delete"]["value"])

    def test_profile_admin_can_manage_other_user(self) -> None:
        context = make_context(
            owner_id=1,
            admin=True,
            authenticated=True,
        )

        with patch.object(manager_client, "fetch_manager_context", AsyncMock(return_value=context)):
            response = self.request("POST", "/profile/7", json={})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["info"]["meta"]["reason_code"], "admin")
        self.assertTrue(body["edit"]["grade"]["value"])
        self.assertTrue(body["edit"]["mute"]["value"])
        self.assertTrue(body["edit"]["rights"]["value"])
        self.assertFalse(body["delete"]["value"])

    def test_context_accepts_anonymous_requests(self) -> None:
        with patch.object(
            manager_client,
            "fetch_manager_context",
            AsyncMock(return_value=make_context()),
        ):
            response = self.client.post("/context")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])


if __name__ == "__main__":
    unittest.main()
