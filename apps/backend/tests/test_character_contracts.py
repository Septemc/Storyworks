import importlib
import json
import sqlite3
import sys
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path):
    from apps.backend.app import database

    original_path = database.db.path
    database.db.path = tmp_path / "storyworks-test.db"
    sys.modules.pop("apps.backend.app.demo_data", None)
    sys.modules.pop("apps.backend.app.main", None)
    main = importlib.import_module("apps.backend.app.main")
    try:
        with TestClient(main.app) as test_client:
            yield test_client
    finally:
        database.db.path = original_path


def first_project_id(client):
    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()["data"]
    assert projects
    return next(project["id"] for project in projects if project["name"] == "修仙背景-demo")


def project_id_by_name(client, name):
    response = client.get("/api/projects")
    assert response.status_code == 200
    return next(project["id"] for project in response.json()["data"] if project["name"] == name)


@contextmanager
def mock_ai_provider():
    from shared.config import config

    original_ai = dict(config._config.get("ai", {}))
    config._config.setdefault("ai", {})["provider"] = "mock"
    try:
        yield
    finally:
        config._config["ai"] = original_ai


@contextmanager
def ai_provider_without_key():
    from shared.config import config

    original_ai = dict(config._config.get("ai", {}))
    config._config["ai"] = {
        "provider": "openai_compatible",
        "baseUrl": "http://127.0.0.1:9/v1",
        "apiKey": "",
        "model": "test-model",
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    try:
        yield
    finally:
        config._config["ai"] = original_ai


def test_strip_ai_markdown_preamble_only_removes_obvious_model_narration():
    from apps.backend.app.services.ai_service import strip_ai_markdown_preamble

    generated = "已按要求完成修改。\n\n---\n\n# 条目标题\n\n## 定义\n正文内容"
    assert strip_ai_markdown_preamble(generated).startswith("# 条目标题")

    plain = "这段正文本来就没有 Markdown 标题，但属于有效内容。"
    assert strip_ai_markdown_preamble(plain) == plain


def test_demo_characters_include_gender(client):
    project_id = first_project_id(client)
    response = client.get(f"/api/projects/{project_id}/characters")
    assert response.status_code == 200
    characters = response.json()["data"]
    assert characters
    assert all("gender" in item["developer_data"]["basic"] for item in characters)
    genders = {item["name"]: item["developer_data"]["basic"]["gender"] for item in characters}
    assert genders["林远"] == "男"
    assert genders["沈慕瑶"] == "女"
    assert genders["顾千秋"] == "男"
    assert genders["谢无烬"] == "男"
    assert genders["云怀素"] == "女"
    assert all("extras" in item["developer_data"] for item in characters)
    assert all(set(["basic", "knowledge", "secrets", "attributes", "relations", "inventory", "skills", "fortune", "extras"]).issubset(item["developer_data"]) for item in characters)


def test_demo_seed_does_not_rewrite_existing_character(client):
    from apps.backend.app.database import db, init_database

    project_id = first_project_id(client)
    detail = client.get(f"/api/projects/{project_id}/characters/detail/char_muyiao").json()["data"]
    developer = detail["developer_data"]
    developer["basic"]["summary"] = "用户已经保存的人物摘要必须保留"
    updated = client.put(
        f"/api/projects/{project_id}/characters/char_muyiao",
        json={
            "name": detail["name"],
            "character_type": detail["character_type"],
            "developer_data": developer,
            "field_visibility": detail["field_visibility"],
        },
    )
    assert updated.status_code == 200
    sentinel_updated_at = "2000-01-01T00:00:00"
    db.exec("UPDATE characters SET updated_at = ? WHERE project_id = ? AND id = ?", (sentinel_updated_at, project_id, "char_muyiao"))

    init_database()

    after = client.get(f"/api/projects/{project_id}/characters/detail/char_muyiao").json()["data"]
    assert after["developer_data"]["basic"]["summary"] == "用户已经保存的人物摘要必须保留"
    assert after["updated_at"] == sentinel_updated_at


def test_character_list_sections_normalize_to_fixed_item_fields(client):
    project_id = first_project_id(client)
    response = client.post(
        f"/api/projects/{project_id}/characters",
        json={
            "name": "结构归一化测试角色",
            "developer_data": {
                "basic": {"name": "结构归一化测试角色", "gender": "未定", "summary": "用于验证小字段固定。"},
                "relations": [{"target": "错误字段", "note": "关系补充"}],
                "inventory": ["破旧钥匙"],
                "skills": [{"name": "速记", "foo": "额外技能说明"}],
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]["developer_data"]
    assert set(["targetName", "relationType", "direction", "intimacy", "conflict", "history", "leverage", "currentStatus", "events"]).issubset(payload["relations"][0])
    assert "关系补充" in payload["relations"][0]["history"]
    assert set(["itemName", "type", "owner", "function", "origin", "limitations", "storyUse"]).issubset(payload["inventory"][0])
    assert "破旧钥匙" in payload["inventory"][0]["storyUse"]
    assert set(["name", "category", "level", "effect", "cost", "limitations", "trainingSource", "storyUse"]).issubset(payload["skills"][0])
    assert "额外技能说明" in payload["skills"][0]["storyUse"]


def test_character_markdown_export_uses_chinese_labels(client):
    project_id = first_project_id(client)
    response = client.get(f"/api/projects/{project_id}/characters/export?format=markdown&ids=char_linyuan")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["filename"] == "characters.md"
    content = payload["content"]
    assert "### 基础（BASIC）" in content
    assert "### 补充（EXTRAS）" in content
    assert "**姓名（name）**" in content
    assert "**性别（gender）**: 男" in content
    assert "### basic" not in content
    assert "**name**" not in content


def test_worldbook_export_markdown_and_json(client):
    project_id = first_project_id(client)
    markdown_response = client.get(f"/api/projects/{project_id}/worldbook/export?format=markdown&ids=world_sky_seal")
    assert markdown_response.status_code == 200
    markdown_payload = markdown_response.json()["data"]
    assert markdown_payload["filename"] == "worldbook.md"
    markdown = markdown_payload["content"]
    assert "# 世界书导出" in markdown
    assert "## 天阙封印" in markdown
    assert "- 分类:" in markdown
    assert "### 关联" in markdown

    json_response = client.get(f"/api/projects/{project_id}/worldbook/export?format=json&ids=world_sky_seal")
    assert json_response.status_code == 200
    json_payload = json_response.json()["data"]
    assert json_payload["filename"] == "worldbook.json"
    assert '"entries"' in json_payload["content"]
    assert '"天阙封印"' in json_payload["content"]
    assert '"relations"' in json_payload["content"]


def test_project_export_contains_all_core_modules(client):
    project_id = first_project_id(client)
    response = client.get(f"/api/projects/{project_id}/export")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["filename"].endswith(".storyworks.json")
    exported = json.loads(payload["content"])
    assert exported["format_version"] == 1
    assert exported["project"]["id"] == project_id
    assert exported["worldbook"]["entries"]
    assert exported["worldbook"]["categories"]
    assert exported["characters"]["entries"]
    assert exported["characters"]["relations"]
    assert exported["scripts"]["entries"]
    assert exported["scripts"]["tree"]
    assert exported["scripts"]["references"]
    assert exported["presets"]
    assert exported["versions"]
    linyuan = next(item for item in exported["characters"]["entries"] if item["id"] == "char_linyuan")
    assert linyuan["developer_data"]["basic"]["gender"] == "男"
    assert "extras" in linyuan["developer_data"]


def test_three_background_demo_projects_are_seeded_with_content(client):
    projects = client.get("/api/projects").json()["data"]
    names = {project["name"]: project for project in projects}
    assert {"修仙背景-demo", "都市背景-demo", "科幻背景-demo"}.issubset(names)
    for name in ["修仙背景-demo", "都市背景-demo", "科幻背景-demo"]:
        project_id = names[name]["id"]
        assert names[name]["counts"]["worldbook"] >= 4
        assert names[name]["counts"]["characters"] >= 3
        assert names[name]["counts"]["scripts"] >= 2
        assert names[name]["counts"]["presets"] >= 3
        characters = client.get(f"/api/projects/{project_id}/characters").json()["data"]
        assert characters
        assert all("extras" in item["developer_data"] for item in characters)


def test_project_import_preview_and_roundtrip_preserves_links(client):
    project_id = first_project_id(client)
    exported = client.get(f"/api/projects/{project_id}/export").json()["data"]["content"]

    preview = client.post("/api/projects/import/preview", json={"content": exported})
    assert preview.status_code == 200
    preview_payload = preview.json()["data"]
    assert preview_payload["valid"] is True
    assert preview_payload["project_name"] == "修仙背景-demo"
    assert preview_payload["name_available"] is False
    assert preview_payload["counts"]["worldbook_entries"] >= 10
    assert preview_payload["counts"]["characters"] >= 5
    assert preview_payload["counts"]["scripts"] >= 3
    assert preview_payload["counts"]["presets"] >= 10

    imported = client.post("/api/projects/import", json={"content": exported})
    assert imported.status_code == 200
    imported_payload = imported.json()["data"]
    imported_project_id = imported_payload["project_id"]
    assert imported_project_id != project_id
    assert imported_payload["project_name"].startswith("修仙背景-demo")

    consistency = client.get(f"/api/projects/{imported_project_id}/consistency/check").json()["data"]
    assert consistency["ok"] is True

    characters = client.get(f"/api/projects/{imported_project_id}/characters").json()["data"]
    linyuan = next(item for item in characters if item["name"] == "林远")
    assert linyuan["id"] != "char_linyuan"
    assert linyuan["developer_data"]["basic"]["gender"] == "男"
    assert linyuan["world_entry_ids"]

    scripts = client.get(f"/api/projects/{imported_project_id}/scripts/tree").json()["data"]
    assert scripts
    references = client.get(f"/api/projects/{imported_project_id}/references/character/{linyuan['id']}").json()["data"]
    assert references

    versions = client.get(f"/api/projects/{imported_project_id}/versions/preset/{imported_payload['id_maps']['presets']['preset_xianxia_epic']}").json()["data"]
    assert versions

    second_import = client.post("/api/projects/import", json={"content": exported})
    assert second_import.status_code == 200
    assert second_import.json()["data"]["project_id"] != imported_project_id
    assert second_import.json()["data"]["project_name"] != imported_payload["project_name"]


def test_project_import_rejects_invalid_package(client):
    invalid_json = client.post("/api/projects/import/preview", json={"content": "not-json"})
    assert invalid_json.status_code == 400

    invalid_package = client.post("/api/projects/import", json={"content": "{}"})
    assert invalid_package.status_code == 400


def test_project_lifecycle_archive_delete_and_demo_reset(client):
    created = client.post(
        "/api/projects",
        json={"name": "项目生命周期测试", "genre": "测试", "description": "用于验证编辑、归档和删除保护。"},
    )
    assert created.status_code == 200
    project = created.json()["data"]
    project_id = project["id"]
    assert project["status"] == "active"
    assert project["is_demo"] is False

    updated = client.put(f"/api/projects/{project_id}", json={"name": "项目生命周期测试-改名", "status": "active"})
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "项目生命周期测试-改名"

    archived = client.post(f"/api/projects/{project_id}/archive", json={"archived": True})
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "archived"
    active_projects = client.get("/api/projects").json()["data"]
    assert project_id not in {item["id"] for item in active_projects}
    all_projects = client.get("/api/projects?include_archived=true").json()["data"]
    assert next(item for item in all_projects if item["id"] == project_id)["status"] == "archived"

    restored = client.post(f"/api/projects/{project_id}/archive", json={"archived": False})
    assert restored.status_code == 200
    assert restored.json()["data"]["status"] == "active"

    unconfirmed_delete = client.request("DELETE", f"/api/projects/{project_id}", json={"confirm_name": "错误名称"})
    assert unconfirmed_delete.status_code == 400
    deleted = client.request("DELETE", f"/api/projects/{project_id}", json={"confirm_name": "项目生命周期测试-改名"})
    assert deleted.status_code == 200
    assert client.get(f"/api/projects/{project_id}").status_code == 404

    demo_id = first_project_id(client)
    demo_project = client.get(f"/api/projects/{demo_id}").json()["data"]
    assert demo_project["is_demo"] is True
    assert client.request("DELETE", f"/api/projects/{demo_id}", json={"confirm_name": demo_project["name"]}).status_code == 400

    before_entries = client.get(f"/api/projects/{demo_id}/worldbook/entries").json()["data"]
    created_entry = client.post(
        f"/api/projects/{demo_id}/worldbook/entries",
        json={"category_id": "cat_geography", "title": "Demo reset 临时条目", "content": "重置后应该消失。"},
    )
    assert created_entry.status_code == 200
    assert len(client.get(f"/api/projects/{demo_id}/worldbook/entries").json()["data"]) == len(before_entries) + 1

    reset = client.post(f"/api/projects/{demo_id}/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["data"]["name"] == "修仙背景-demo"
    after_entries = client.get(f"/api/projects/{demo_id}/worldbook/entries").json()["data"]
    assert len(after_entries) == len(before_entries)
    assert all(item["title"] != "Demo reset 临时条目" for item in after_entries)


def test_schema_migration_version_is_recorded(client):
    from apps.backend.app.database import db

    row = db.one("SELECT version, name FROM schema_migrations WHERE version = 1")
    assert row == {"version": 1, "name": "initial_unified_schema"}
    row = db.one("SELECT version, name FROM schema_migrations WHERE version = 2")
    assert row == {"version": 2, "name": "ensure_current_columns_and_indexes"}
    indexes = {item["name"] for item in db.all("PRAGMA index_list(worldbook_entries)")}
    assert "idx_worldbook_entries_category" in indexes
    assert "idx_worldbook_entries_status" in indexes


def test_init_database_upgrades_legacy_schema_without_dropping_data(tmp_path):
    from apps.backend.app import database

    legacy_path = tmp_path / "legacy-storyworks.db"
    with sqlite3.connect(legacy_path) as conn:
        conn.executescript(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                genre TEXT
            );
            INSERT INTO projects (id, name, description, genre)
            VALUES ('legacy_project', '旧库项目', '旧结构保留数据', '测试');

            CREATE TABLE characters (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL
            );
            INSERT INTO characters (id, project_id, name)
            VALUES ('legacy_character', 'legacy_project', '旧库角色');
            """
        )

    original_path = database.db.path
    database.db.path = legacy_path
    sys.modules.pop("apps.backend.app.demo_data", None)
    try:
        database.init_database()
        project = database.db.one("SELECT id, name, settings, updated_at FROM projects WHERE id = ?", ("legacy_project",))
        assert project["name"] == "旧库项目"
        assert project["settings"] == "{}"
        assert "updated_at" in project

        character = database.db.one(
            "SELECT name, developer_data, player_data, field_visibility, generation_history FROM characters WHERE id = ?",
            ("legacy_character",),
        )
        assert character["name"] == "旧库角色"
        assert character["developer_data"] == "{}"
        assert character["generation_history"] == "[]"

        migration = database.db.one("SELECT name FROM schema_migrations WHERE version = 2")
        assert migration == {"name": "ensure_current_columns_and_indexes"}
        indexes = {item["name"] for item in database.db.all("PRAGMA index_list(scripts)")}
        assert "idx_scripts_tree" in indexes
    finally:
        database.db.path = original_path


def test_health_reports_ai_settings_capability(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ok"
    assert payload["features"]["ai_settings"] is True
    assert payload["features"]["llm_config_persistence"] is True
    assert payload["features"]["schema_migrations"] is True


def test_project_settings_defaults_and_updates_are_normalized(client):
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}")
    assert before.status_code == 200
    settings = before.json()["data"]["settings"]
    assert settings["default_style"] == ""
    assert settings["ai"] == {"temperature": 0.7, "max_tokens": 4096}
    assert settings["modules"] == {"worldbook": True, "characters": True, "scripts": True, "presets": True}
    assert settings["defaults"] == {"worldbook_visibility": "public", "character_view_mode": "developer"}

    updated = client.put(
        f"/api/projects/{project_id}",
        json={
            "settings": {
                "default_style": "冷峻克制，强调因果代价",
                "ai": {"temperature": 2, "max_tokens": 300, "vendor_hint": "keep-me"},
                "modules": {"scripts": False},
                "defaults": {"worldbook_visibility": "secret", "character_view_mode": "player"},
                "custom_future_setting": {"enabled": True},
            }
        },
    )

    assert updated.status_code == 200
    payload = updated.json()["data"]["settings"]
    assert payload["default_style"] == "冷峻克制，强调因果代价"
    assert payload["ai"]["temperature"] == 1.4
    assert payload["ai"]["max_tokens"] == 1024
    assert payload["ai"]["vendor_hint"] == "keep-me"
    assert payload["modules"]["worldbook"] is True
    assert payload["modules"]["scripts"] is False
    assert payload["defaults"]["worldbook_visibility"] == "secret"
    assert payload["defaults"]["character_view_mode"] == "player"
    assert payload["custom_future_setting"] == {"enabled": True}

    listed = client.get("/api/projects").json()["data"]
    listed_project = next(item for item in listed if item["id"] == project_id)
    assert listed_project["settings"]["ai"]["temperature"] == 1.4
    assert listed_project["settings"]["modules"]["scripts"] is False


def test_project_ai_defaults_are_used_when_request_omits_temperature(client, monkeypatch):
    captured = {}

    async def fake_call_ai(prompt, system_prompt="", temperature=None, max_tokens=None, process_log=None):
        captured["temperature"] = temperature
        captured["max_tokens"] = max_tokens
        return "## 定义\n项目默认 AI 参数测试。"

    monkeypatch.setattr("apps.backend.app.services.ai_service.call_ai", fake_call_ai)
    project_id = first_project_id(client)
    updated = client.put(
        f"/api/projects/{project_id}",
        json={"settings": {"ai": {"temperature": 0.3, "max_tokens": 18000}}},
    )
    assert updated.status_code == 200

    response = client.post(
        f"/api/projects/{project_id}/worldbook/ai/generate",
        json={"prompt": "使用项目默认 AI 参数生成世界书。"},
    )

    assert response.status_code == 200
    assert captured["temperature"] == 0.3
    assert captured["max_tokens"] == 18000


def test_ai_settings_update_persists_key_without_exposing_secret(client, tmp_path):
    from shared.config import config

    original_config = json.loads(json.dumps(config._config))
    original_path = getattr(config, "_config_path", None)
    original_mtime = getattr(config, "_config_mtime_ns", None)
    config._config = {
        "ai": {
            "provider": "openai_compatible",
            "baseUrl": "https://example.com/v1",
            "apiKey": "",
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "projects_dir": "./projects",
    }
    config._config_path = tmp_path / "config.json"
    try:
        before = client.get("/api/settings/ai")
        assert before.status_code == 200
        before_payload = before.json()["data"]
        assert before_payload["apiKey"] == ""
        assert before_payload["has_api_key"] is False

        saved = client.put(
            "/api/settings/ai",
            json={
                "provider": "openai_compatible",
                "baseUrl": "https://api.example.test/v1",
                "apiKey": "secret-test-key",
                "model": "story-model",
                "temperature": 0.3,
                "max_tokens": 8192,
            },
        )
        assert saved.status_code == 200
        saved_payload = saved.json()["data"]
        assert saved_payload["has_api_key"] is True
        assert saved_payload["apiKey"] == ""
        assert "secret-test-key" not in json.dumps(saved_payload, ensure_ascii=False)

        stored = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert stored["ai"]["apiKey"] == "secret-test-key"
        assert stored["ai"]["baseUrl"] == "https://api.example.test/v1"

        cleared = client.put("/api/settings/ai", json={"provider": "mock", "clearApiKey": True})
        assert cleared.status_code == 200
        assert cleared.json()["data"]["provider"] == "mock"
        assert cleared.json()["data"]["has_api_key"] is False
    finally:
        config._config = original_config
        if original_path is not None:
            config._config_path = original_path
        config._config_mtime_ns = original_mtime


def test_ai_config_reloads_when_shared_config_file_changes(tmp_path):
    from shared.config import config

    original_config = json.loads(json.dumps(config._config))
    original_path = getattr(config, "_config_path", None)
    original_mtime = getattr(config, "_config_mtime_ns", None)
    config_path = tmp_path / "config.json"
    initial = {
        "ai": {
            "provider": "openai_compatible",
            "baseUrl": "https://example.invalid/v1",
            "apiKey": "",
            "model": "old-model",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "projects_dir": "./projects",
    }
    updated = {
        **initial,
        "ai": {
            **initial["ai"],
            "apiKey": "fresh-key",
            "model": "fresh-model",
        },
    }
    try:
        config_path.write_text(json.dumps(initial), encoding="utf-8")
        config._config = json.loads(json.dumps(initial))
        config._config_path = config_path
        config._config_mtime_ns = config_path.stat().st_mtime_ns

        config_path.write_text(json.dumps(updated), encoding="utf-8")
        config._config_mtime_ns = -1

        public = config.public_ai_config()
        assert public["has_api_key"] is True
        assert public["apiKey"] == ""
        assert public["model"] == "fresh-model"
    finally:
        config._config = original_config
        if original_path is not None:
            config._config_path = original_path
        config._config_mtime_ns = original_mtime


def test_saved_ai_settings_are_used_by_character_generation(client, tmp_path, monkeypatch):
    from shared.config import config

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "character_type": "supporting",
                                    "developer_data": {
                                        "basic": {"name": "陆谨", "gender": "男", "age": "34", "identity": "测试角色", "role": "同伴", "status": "可用", "summary": "通过已保存配置生成的角色。"},
                                        "knowledge": {"appearance": "测试外观", "personality": "谨慎", "background": "用于验证配置保存后立即参与 AI 调用。", "dailyLife": "测试日常", "motivation": "验证配置", "values": "可靠", "flaws": "过度谨慎", "currentConflict": "需要完成配置链路验证"},
                                        "secrets": {"publicMask": "普通测试角色", "privateTruth": "用于验证保存配置", "trauma": "无", "hiddenAgenda": "确认链路", "weakness": "配置缺失", "revealTrigger": "接口调用"},
                                        "attributes": {"physical": "普通", "mental": "稳定", "social": "测试影响力", "resources": "测试资源", "limitations": "仅用于测试", "special": "配置链路"},
                                        "relations": [{"targetName": "林远", "relationType": "ally", "direction": "bidirectional", "intimacy": 10, "conflict": "测试关系", "history": "用于验证配置链路", "leverage": "配置状态", "currentStatus": "可验证", "events": []}],
                                        "inventory": [{"itemName": "测试凭据", "type": "工具", "owner": "陆谨", "function": "验证 API 配置调用", "origin": "测试夹具", "limitations": "仅测试可用", "storyUse": "确认生成结果能进入固定字段"}],
                                        "skills": [{"name": "配置校验", "category": "测试", "level": "熟练", "effect": "确认请求使用保存后的 API Key", "cost": "无", "limitations": "依赖测试环境", "trainingSource": "自动化测试", "storyUse": "覆盖 LLM 保存与调用链"}],
                                        "fortune": {"desire": "完成验证", "fear": "配置失效", "destinyTags": ["测试"], "turningPoints": ["保存配置"], "choices": ["继续生成"], "causalHints": ["配置会影响 AI 调用"]},
                                        "extras": "配置调用链验证。",
                                    },
                                    "tags": ["fake-ai"],
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            assert url == "https://fake.example/v1/chat/completions"
            assert headers["Authorization"] == "Bearer saved-secret"
            assert json["model"] == "fake-model"
            return FakeResponse()

    original_config = json.loads(json.dumps(config._config))
    original_path = getattr(config, "_config_path", None)
    original_mtime = getattr(config, "_config_mtime_ns", None)
    config._config = {"ai": {"provider": "openai_compatible", "baseUrl": "", "apiKey": "", "model": "", "temperature": 0.7, "max_tokens": 4096}, "projects_dir": "./projects"}
    config._config_path = tmp_path / "config.json"
    monkeypatch.setattr("apps.backend.app.services.ai_service.httpx.AsyncClient", FakeClient)
    try:
        saved = client.put(
            "/api/settings/ai",
            json={"provider": "openai_compatible", "baseUrl": "https://fake.example/v1", "apiKey": "saved-secret", "model": "fake-model"},
        )
        assert saved.status_code == 200
        response = client.post(f"/api/projects/{first_project_id(client)}/characters/ai/generate", json={"concept": "测试配置调用链"})
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["developer_data"]["basic"]["name"] == "陆谨"
        assert payload["developer_data"]["extras"] == "配置调用链验证。"
    finally:
        config._config = original_config
        if original_path is not None:
            config._config_path = original_path
        config._config_mtime_ns = original_mtime


def test_ai_call_continues_when_provider_reports_length_limit(client, tmp_path, monkeypatch):
    from shared.config import config

    class FakeResponse:
        def __init__(self, content, finish_reason):
            self.content = content
            self.finish_reason = finish_reason

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": self.content}, "finish_reason": self.finish_reason}]}

    class FakeClient:
        calls = []

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            self.calls.append(json)
            if len(self.calls) == 1:
                return FakeResponse("## 定", "length")
            return FakeResponse("义\n自动续写正文。", "stop")

    original_config = json.loads(json.dumps(config._config))
    original_path = getattr(config, "_config_path", None)
    original_mtime = getattr(config, "_config_mtime_ns", None)
    config._config = {
        "ai": {
            "provider": "openai_compatible",
            "baseUrl": "https://fake.example/v1",
            "apiKey": "continue-secret",
            "model": "continue-model",
            "temperature": 0.7,
            "max_tokens": 4096,
            "continuation_max": 2,
        },
        "projects_dir": "./projects",
    }
    config._config_path = tmp_path / "config.json"
    monkeypatch.setattr("apps.backend.app.services.ai_service.httpx.AsyncClient", FakeClient)
    try:
        response = client.post(
            f"/api/projects/{first_project_id(client)}/worldbook/ai/generate",
            json={"title": "续写测试", "prompt": "生成一段会被截断的世界书正文"},
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["content"] == "## 定义\n自动续写正文。"
        assert len(FakeClient.calls) == 2
        assert FakeClient.calls[1]["messages"][-1]["content"].startswith("请从上一条回复的中断处继续输出")
        assert any("自动续写第 1 次" in item["message"] for item in payload["generation_log"])
    finally:
        FakeClient.calls.clear()
        config._config = original_config
        if original_path is not None:
            config._config_path = original_path
        config._config_mtime_ns = original_mtime


def test_character_generation_repairs_malformed_llm_output(client, tmp_path, monkeypatch):
    from shared.config import config

    repaired = {
        "character_type": "supporting",
        "developer_data": {
            "basic": {"name": "许南枝", "gender": "女", "age": "29", "identity": "城市调查记者", "role": "线索提供者", "status": "追查中", "summary": "她在自由提示词很混乱的情况下，仍被整理为严格人物卡结构。"},
            "knowledge": {"appearance": "短发、旧相机", "personality": "冷静敏锐", "background": "长期调查城市异常事件。", "dailyLife": "在新闻编辑部和事故现场之间奔走。", "motivation": "找出真相", "values": "证据优先", "flaws": "不善求助", "currentConflict": "证据链被关键人物截断"},
            "secrets": {"publicMask": "普通记者", "privateTruth": "掌握未公开录音", "trauma": "曾因报道失误伤害线人", "hiddenAgenda": "保护线人家属", "weakness": "对旧案有负罪感", "revealTrigger": "录音被公开"},
            "attributes": {"physical": "耐力稳定", "mental": "擅长交叉验证", "social": "媒体圈人脉", "resources": "资料库和线人", "limitations": "缺少执法权限", "special": "能快速识别证词矛盾"},
            "relations": [{"targetName": "林远", "relationType": "ally", "direction": "bidirectional", "intimacy": 20, "conflict": "是否公开线索", "history": "共享过一次调查", "leverage": "未公开录音", "currentStatus": "试探合作", "events": []}],
            "inventory": [{"itemName": "旧相机", "type": "工具", "owner": "许南枝", "function": "记录现场", "origin": "导师遗物", "limitations": "存储卡损坏风险", "storyUse": "保存关键证据"}],
            "skills": [{"name": "交叉采访", "category": "调查", "level": "熟练", "effect": "发现证词漏洞", "cost": "消耗人情", "limitations": "需要可靠对象", "trainingSource": "记者训练", "storyUse": "推动调查"}],
            "fortune": {"desire": "公开真相", "fear": "再次伤害线人", "destinyTags": ["记者", "旧案"], "turningPoints": ["公开录音"], "choices": ["保护线人", "追求曝光"], "causalHints": ["旧案会牵出新冲突"]},
            "extras": "自由提示词中的额外要求被收束到标准字段内容中。",
        },
        "tags": ["repair-test"],
    }

    class FakeResponse:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": self.content}}]}

    class FakeClient:
        calls = []

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            self.calls.append(json["messages"][-1]["content"])
            if len(self.calls) == 1:
                return FakeResponse('{"name": "这不是人物卡结构", "random": "字段漂移"}')
            return FakeResponse(json_module.dumps(repaired, ensure_ascii=False))

    import json as json_module

    original_config = json.loads(json.dumps(config._config))
    original_path = getattr(config, "_config_path", None)
    original_mtime = getattr(config, "_config_mtime_ns", None)
    config._config = {"ai": {"provider": "openai_compatible", "baseUrl": "https://fake.example/v1", "apiKey": "repair-secret", "model": "repair-model", "temperature": 0.7, "max_tokens": 4096}, "projects_dir": "./projects"}
    config._config_path = tmp_path / "config.json"
    monkeypatch.setattr("apps.backend.app.services.ai_service.httpx.AsyncClient", FakeClient)
    try:
        response = client.post(f"/api/projects/{first_project_id(client)}/characters/ai/generate", json={"concept": "随便写，但输出必须被系统收束"})
        assert response.status_code == 200
        payload = response.json()["data"]
        assert len(FakeClient.calls) == 2
        assert payload["developer_data"]["basic"]["name"] == "许南枝"
        assert set(["basic", "knowledge", "secrets", "attributes", "relations", "inventory", "skills", "fortune", "extras"]).issubset(payload["developer_data"])
        assert isinstance(payload["developer_data"]["extras"], str)
        assert payload["contract_issues"] == []
        assert any("结构修复" in item["message"] for item in payload["generation_log"])
    finally:
        config._config = original_config
        if original_path is not None:
            config._config_path = original_path
        config._config_mtime_ns = original_mtime


def test_ai_operation_logs_can_be_recorded_and_queried(client):
    from apps.backend.app.main import record_ai_operation

    project_id = first_project_id(client)
    record_ai_operation(
        project_id,
        "character",
        "iterate",
        "prompt text",
        {"result": "updated"},
        target_id="char_linyuan",
        section="basic",
        field="summary",
        instruction="补强摘要",
        request={"temperature": 0.7},
        process_log=[{"time": "now", "message": "done"}],
    )

    response = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character&target_id=char_linyuan")
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 1
    assert rows[0]["target_type"] == "character"
    assert rows[0]["operation"] == "iterate"
    assert rows[0]["section"] == "basic"
    assert rows[0]["field"] == "summary"
    assert rows[0]["request"] == {"temperature": 0.7}
    assert rows[0]["process_log"] == [{"time": "now", "message": "done"}]
    assert "updated" in rows[0]["response_preview"]
    assert rows[0]["response_data"] == {"result": "updated"}


def test_ai_log_apply_endpoint_updates_character_from_complete_history(client):
    from apps.backend.app.services.ai_service import record_ai_operation

    project_id = first_project_id(client)
    before_detail = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
    before_versions = client.get(f"/api/projects/{project_id}/versions/character/char_linyuan").json()["data"]
    result = {
        "developer_data": {
            "basic": {
                "name": "林远",
                "gender": "男",
                "summary": "从完整 AI 历史写回的人物描述。",
            },
            "secrets": {"privateTruth": "历史结果里不应写入的隐秘"},
        },
    }
    record_ai_operation(
        project_id,
        "character",
        "iterate",
        "prompt text",
        result,
        target_id="char_linyuan",
        section="basic",
        field="summary",
        instruction="从历史应用人物描述",
        request={"apply": False, "temperature": 0.2},
        process_log=[{"time": "now", "message": "done"}],
    )
    log = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character&target_id=char_linyuan").json()["data"][0]
    assert log["pending_apply"] is True

    applied = client.post(f"/api/projects/{project_id}/ai/logs/{log['id']}/apply")

    assert applied.status_code == 200
    entity = applied.json()["data"]["entity"]
    assert entity["developer_data"]["basic"]["summary"] == "从完整 AI 历史写回的人物描述。"
    detail = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
    assert detail["developer_data"]["basic"]["summary"] == "从完整 AI 历史写回的人物描述。"
    assert detail["developer_data"]["knowledge"]["background"] == before_detail["developer_data"]["knowledge"]["background"]
    assert detail["developer_data"]["secrets"]["privateTruth"] == before_detail["developer_data"]["secrets"]["privateTruth"]
    assert detail["field_visibility"]["basic"] == before_detail["field_visibility"]["basic"]
    assert detail["player_data"]["basic"]["summary"] == "从完整 AI 历史写回的人物描述。"
    after_versions = client.get(f"/api/projects/{project_id}/versions/character/char_linyuan").json()["data"]
    assert len(after_versions) == len(before_versions) + 1
    assert after_versions[0]["summary"] == "AI历史应用 basic / summary"
    logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character&target_id=char_linyuan").json()["data"]
    original_preview = next(item for item in logs if item["id"] == log["id"])
    assert original_preview["pending_apply"] is False
    assert original_preview["applied_preview"] is True
    assert any(item["operation"] == "apply" and item["instruction"] == "从历史应用人物描述" for item in logs)


def test_project_counts_pending_ai_drafts_until_preview_is_applied(client):
    from apps.backend.app.services.ai_service import record_ai_operation

    project_id = first_project_id(client)
    record_ai_operation(
        project_id,
        "worldbook",
        "iterate",
        "draft prompt",
        {"content": "## 定义\n待应用草稿。"},
        target_id="world_sky_seal",
        section="定义",
        instruction="形成待应用草稿",
        request={"apply": False},
        process_log=[{"time": "now", "message": "done"}],
    )

    projects = client.get("/api/projects").json()["data"]
    project = next(item for item in projects if item["id"] == project_id)
    assert project["counts"]["ai_drafts"] == 1
    overview = client.get(f"/api/projects/{project_id}/overview").json()["data"]
    assert overview["pending_ai_drafts"]["total"] == 1
    assert overview["pending_ai_drafts"]["by_target_type"]["worldbook"] == 1
    assert overview["pending_ai_drafts"]["recent"][0]["instruction"] == "形成待应用草稿"

    log = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook&target_id=world_sky_seal").json()["data"][0]
    assert log["pending_apply"] is True
    assert log["applied_preview"] is False
    applied = client.post(f"/api/projects/{project_id}/ai/logs/{log['id']}/apply")
    assert applied.status_code == 200
    applied_logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook&target_id=world_sky_seal").json()["data"]
    original_preview = next(item for item in applied_logs if item["id"] == log["id"])
    assert original_preview["pending_apply"] is False
    assert original_preview["applied_preview"] is True

    projects_after = client.get("/api/projects").json()["data"]
    project_after = next(item for item in projects_after if item["id"] == project_id)
    assert project_after["counts"]["ai_drafts"] == 0
    overview_after = client.get(f"/api/projects/{project_id}/overview").json()["data"]
    assert overview_after["pending_ai_drafts"]["total"] == 0


def test_project_overview_reports_recent_updates_for_core_modules(client):
    project_id = first_project_id(client)

    response = client.get(f"/api/projects/{project_id}/overview")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["recent"]["worldbook"]
    assert payload["recent"]["characters"]
    assert payload["recent"]["scripts"]
    assert payload["recent"]["presets"]
    assert {"id", "title", "updated_at"}.issubset(payload["recent"]["worldbook"][0])
    assert any(item["title"] == "天阙封印" for item in payload["recent"]["worldbook"])
    assert any(item["title"] == "林远" for item in payload["recent"]["characters"])
    assert payload["pending_ai_drafts"]["total"] >= 0


def test_ai_log_apply_endpoint_updates_worldbook_script_and_preset(client):
    from apps.backend.app.services.ai_service import record_ai_operation

    project_id = first_project_id(client)
    cases = [
        {
            "target_type": "worldbook",
            "target_id": "world_sky_seal",
            "entity_type": "worldbook_entry",
            "result": {"content": "## 定义\n从 AI 历史写回的世界书正文。"},
            "assert_path": ("content",),
            "expected": "从 AI 历史写回的世界书正文。",
            "section": "定义",
            "instruction": "应用世界书历史",
        },
        {
            "target_type": "script",
            "target_id": "scr_scene_starfall",
            "entity_type": "script",
            "result": "## 场景目标\n从 AI 历史写回的剧本正文。",
            "assert_path": ("content",),
            "expected": "从 AI 历史写回的剧本正文。",
            "section": "场景目标",
            "instruction": "应用剧本历史",
        },
        {
            "target_type": "preset",
            "target_id": "preset_scene_polish",
            "entity_type": "preset",
            "result": {
                "dimensions": [{"name": "历史维度", "value": "增强", "description": "从 AI 历史写回", "examples": [], "isCustom": True, "order": 0}],
                "custom_blocks": [{"title": "历史规则", "content": "应用历史结果时重新编译。", "position": "before", "order": 0}],
                "application_scenes": [{"sceneType": "script", "enabled": True, "adjustments": "强调版本审计"}],
            },
            "assert_path": ("dimensions", 0, "name"),
            "expected": "历史维度",
            "section": "维度",
            "instruction": "应用预设历史",
        },
    ]

    for case in cases:
        before_versions = client.get(f"/api/projects/{project_id}/versions/{case['entity_type']}/{case['target_id']}").json()["data"]
        record_ai_operation(
            project_id,
            case["target_type"],
            "iterate",
            f"{case['target_type']} prompt",
            case["result"],
            target_id=case["target_id"],
            section=case["section"],
            instruction=case["instruction"],
            request={"apply": False, "temperature": 0.2},
            process_log=[{"time": "now", "message": "done"}],
        )
        log = client.get(f"/api/projects/{project_id}/ai/logs?target_type={case['target_type']}&target_id={case['target_id']}").json()["data"][0]

        applied = client.post(f"/api/projects/{project_id}/ai/logs/{log['id']}/apply")

        assert applied.status_code == 200
        entity = applied.json()["data"]["entity"]
        value = entity
        for part in case["assert_path"]:
            value = value[part]
        assert case["expected"] in value
        after_versions = client.get(f"/api/projects/{project_id}/versions/{case['entity_type']}/{case['target_id']}").json()["data"]
        assert len(after_versions) == len(before_versions) + 1
        assert after_versions[0]["summary"] == f"AI历史应用 {case['section']}"
        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type={case['target_type']}&target_id={case['target_id']}").json()["data"]
        assert any(item["operation"] == "apply" and item["instruction"] == case["instruction"] for item in logs)


def test_ai_log_apply_endpoint_rejects_truncated_legacy_history(client):
    from apps.backend.app.database import db, new_id, now, to_json, to_json_array

    project_id = first_project_id(client)
    log_id = new_id("ailog")
    db.exec(
        """INSERT INTO ai_operation_logs
           (id, project_id, target_type, target_id, operation, status, section, field, instruction, prompt, request, response_preview, response_data, process_log, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            log_id,
            project_id,
            "character",
            "char_linyuan",
            "iterate",
            "success",
            "basic",
            "summary",
            "旧日志",
            "prompt",
            to_json({"apply": False}),
            "x" * 1600,
            None,
            to_json_array([]),
            now(),
        ),
    )

    response = client.post(f"/api/projects/{project_id}/ai/logs/{log_id}/apply")

    assert response.status_code == 409
    assert "截断预览" in response.json()["detail"]


def test_failed_ai_iteration_records_failed_log_and_preserves_request(client):
    with ai_provider_without_key():
        project_id = first_project_id(client)
        request_payload = {"instruction": "失败时保留这条用户输入", "section": "规则", "apply": False, "temperature": 0.2}
        response = client.post(
            f"/api/projects/{project_id}/worldbook/entries/world_sky_seal/ai/iterate",
            json=request_payload,
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "未配置 AI API Key"

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook&target_id=world_sky_seal").json()["data"]
        failed = next(item for item in logs if item["status"] == "failed" and item["operation"] == "iterate")
        assert failed["section"] == "规则"
        assert failed["instruction"] == "失败时保留这条用户输入"
        assert failed["request"] == request_payload
        assert "失败时保留这条用户输入" in failed["prompt"]
        assert "未配置 AI API Key" in failed["response_preview"]
        assert any("AI 调用失败" in item["message"] for item in failed["process_log"])


def test_ai_preview_apply_metadata_records_apply_log_and_version_summary(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        preview = client.post(
            f"/api/projects/{project_id}/worldbook/entries/world_sky_seal/ai/iterate",
            json={"instruction": "补强封印代价", "section": "规则", "apply": False, "temperature": 0.2},
        )
        assert preview.status_code == 200
        preview_payload = preview.json()["data"]

        applied = client.put(
            f"/api/projects/{project_id}/worldbook/entries/world_sky_seal",
            json={
                "content": preview_payload["content"],
                "ai_prompt": preview_payload["ai_prompt"],
                "summary": "AI迭代 规则",
                "ai_apply": {
                    "prompt": preview_payload["ai_prompt"],
                    "result": preview_payload["content"],
                    "section": "规则",
                    "instruction": "补强封印代价",
                    "request": {"section": "规则", "instruction": "补强封印代价", "temperature": 0.2},
                    "process_log": preview_payload["generation_log"],
                },
            },
        )
        assert applied.status_code == 200

        versions = client.get(f"/api/projects/{project_id}/versions/worldbook_entry/world_sky_seal").json()["data"]
        assert versions[0]["summary"] == "AI迭代 规则"
        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook&target_id=world_sky_seal").json()["data"]
        apply_log = next(item for item in logs if item["operation"] == "apply")
        assert apply_log["section"] == "规则"
        assert apply_log["instruction"] == "补强封印代价"
        assert apply_log["request"]["temperature"] == 0.2
        assert "补强封印代价" in apply_log["prompt"]


def test_ai_direct_apply_records_apply_log_and_version_summary_for_worldbook(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        before_versions = client.get(f"/api/projects/{project_id}/versions/worldbook_entry/world_sky_seal").json()["data"]

        response = client.post(
            f"/api/projects/{project_id}/worldbook/entries/world_sky_seal/ai/iterate",
            json={"instruction": "直接保存封印代价", "section": "规则", "apply": True, "temperature": 0.2},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["entry"]["version"] >= 2
        assert "直接保存封印代价" in payload["ai_prompt"]

        versions = client.get(f"/api/projects/{project_id}/versions/worldbook_entry/world_sky_seal").json()["data"]
        assert len(versions) == len(before_versions) + 1
        assert versions[0]["summary"] == "AI迭代 规则"

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook&target_id=world_sky_seal").json()["data"]
        assert any(item["operation"] == "iterate" and item["section"] == "规则" for item in logs)
        apply_log = next(item for item in logs if item["operation"] == "apply")
        assert apply_log["section"] == "规则"
        assert apply_log["instruction"] == "直接保存封印代价"
        assert apply_log["request"]["apply"] is True
        assert "直接保存封印代价" in apply_log["prompt"]


def test_worldbook_ai_generation_uses_category_template_for_structured_data(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        response = client.post(
            f"/api/projects/{project_id}/worldbook/ai/generate",
            json={"category_id": "cat_systems", "prompt": "生成一个可被角色和剧本引用的规则条目", "temperature": 0.2},
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["category_id"] == "cat_systems"
        assert payload["structured_data"]["definition"].startswith("mock 模式生成的世界书内容")
        assert "规则" in payload["structured_data"]["rules"]
        assert "后续可以被角色和剧本引用" in payload["structured_data"]["hooks"]
        assert payload["ai_metadata"]["category_template"][0]["id"] == "definition"

        created = client.post(
            f"/api/projects/{project_id}/worldbook/entries",
            json={
                "category_id": payload["category_id"],
                "title": payload["title"],
                "content": payload["content"],
                "structured_data": payload["structured_data"],
                "ai_generated": True,
                "ai_prompt": payload["ai_prompt"],
                "ai_metadata": payload["ai_metadata"],
                "tags": ["AI"],
            },
        )
        assert created.status_code == 200
        created_payload = created.json()["data"]
        assert created_payload["structured_data"]["definition"].startswith("mock 模式生成")

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook").json()["data"]
        generate_log = next(item for item in logs if item["operation"] == "generate")
        assert "分类模板和结构化字段约束" in generate_log["prompt"]
        assert '"definition"' in generate_log["prompt"]


def test_worldbook_entry_update_rejects_missing_category(client):
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}/worldbook/entries/world_sky_seal").json()["data"]

    response = client.put(
        f"/api/projects/{project_id}/worldbook/entries/world_sky_seal",
        json={"category_id": "missing_category"},
    )

    assert response.status_code == 404
    after = client.get(f"/api/projects/{project_id}/worldbook/entries/world_sky_seal").json()["data"]
    assert after["category_id"] == before["category_id"]


def test_mock_ai_character_generation_records_log(client):
    from shared.config import config

    original_ai = dict(config._config.get("ai", {}))
    config._config.setdefault("ai", {})["provider"] = "mock"
    try:
        project_id = first_project_id(client)
        response = client.post(
            f"/api/projects/{project_id}/characters/ai/generate",
            json={"concept": "离线生成一个阵法师", "temperature": 0.2},
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["developer_data"]["basic"]["gender"] == "未定"
        assert set(["basic", "knowledge", "secrets", "attributes", "relations", "inventory", "skills", "fortune", "extras"]).issubset(payload["developer_data"])
        assert isinstance(payload["developer_data"]["extras"], str)

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character").json()["data"]
        assert any(item["operation"] == "generate" and "云舟" in item["response_preview"] for item in logs)
    finally:
        config._config["ai"] = original_ai


def test_mock_ai_worldbook_iteration_records_log(client):
    from shared.config import config

    original_ai = dict(config._config.get("ai", {}))
    config._config.setdefault("ai", {})["provider"] = "mock"
    try:
        project_id = first_project_id(client)
        response = client.post(
            f"/api/projects/{project_id}/worldbook/entries/world_sky_seal/ai/iterate",
            json={"instruction": "补强规则", "section": "规则", "apply": False, "temperature": 0.2},
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert "## 规则" in payload["content"]
        assert payload["content"].count("## 规则") == 1

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=worldbook&target_id=world_sky_seal").json()["data"]
        assert any(item["operation"] == "iterate" and item["section"] == "规则" for item in logs)
    finally:
        config._config["ai"] = original_ai


def test_mock_ai_character_field_iteration_previews_then_applies_with_version(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        before = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
        before_background = before["developer_data"]["knowledge"]["background"]
        before_versions = client.get(f"/api/projects/{project_id}/versions/character/char_linyuan").json()["data"]

        preview = client.post(
            f"/api/projects/{project_id}/characters/char_linyuan/ai/iterate",
            json={"section": "knowledge", "field": "background", "instruction": "补强身世与灵灾后遗症", "apply": False, "temperature": 0.2},
        )
        assert preview.status_code == 200
        preview_payload = preview.json()["data"]
        assert "mock 模式迭代后的background内容" in preview_payload["developer_data"]["knowledge"]["background"]
        assert preview_payload["developer_data"]["basic"]["gender"] == "男"
        assert preview_payload["player_data"]["basic"]["gender"] == "男"

        unchanged = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
        assert unchanged["developer_data"]["knowledge"]["background"] == before_background

        logs_after_preview = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character&target_id=char_linyuan").json()["data"]
        preview_log = next(item for item in logs_after_preview if item["operation"] == "iterate" and item["section"] == "knowledge" and item["field"] == "background")
        assert preview_log["request"]["apply"] is False
        assert preview_log["pending_apply"] is True
        assert preview_log["response_data"]["knowledge"]["background"] == preview_payload["developer_data"]["knowledge"]["background"]

        applied = client.post(f"/api/projects/{project_id}/ai/logs/{preview_log['id']}/apply")
        assert applied.status_code == 200
        applied_character = applied.json()["data"]["entity"]
        assert "mock 模式迭代后的background内容" in applied_character["developer_data"]["knowledge"]["background"]
        assert applied_character["developer_data"]["basic"]["gender"] == "男"
        assert applied_character["player_data"]["basic"]["gender"] == "男"

        detail = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
        assert "mock 模式迭代后的background内容" in detail["developer_data"]["knowledge"]["background"]

        after_versions = client.get(f"/api/projects/{project_id}/versions/character/char_linyuan").json()["data"]
        assert len(after_versions) == len(before_versions) + 1
        assert after_versions[0]["entity_type"] == "character"
        assert "mock 模式迭代后的background内容" in after_versions[0]["data"]["developer_data"]["knowledge"]["background"]

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character&target_id=char_linyuan").json()["data"]
        applied_preview = next(item for item in logs if item["id"] == preview_log["id"])
        assert applied_preview["pending_apply"] is False
        assert applied_preview["applied_preview"] is True
        assert any(item["operation"] == "apply" and item["section"] == "knowledge" and item["field"] == "background" for item in logs)


def test_character_iteration_merges_wrapped_developer_data_for_selected_section(client, monkeypatch):
    async def fake_call_ai(*args, **kwargs):
        return json.dumps(
            {
                "developer_data": {
                    "attributes": {
                        "physical": "迭代后体能更强调旧伤与爆发代价。",
                        "mental": "能在高压局势下快速拆解线索。",
                    }
                }
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr("apps.backend.app.services.ai_service.call_ai", fake_call_ai)
    project_id = first_project_id(client)
    response = client.post(
        f"/api/projects/{project_id}/characters/char_linyuan/ai/iterate",
        json={"section": "attributes", "instruction": "补强属性，但模型返回完整包装", "apply": True, "temperature": 0.2},
    )
    assert response.status_code == 200
    character_payload = response.json()["data"]["character"]
    attributes = character_payload["developer_data"]["attributes"]
    assert attributes["physical"] == "迭代后体能更强调旧伤与爆发代价。"
    assert attributes["mental"] == "能在高压局势下快速拆解线索。"
    assert "developer_data" not in attributes

    detail = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
    assert detail["developer_data"]["attributes"]["physical"] == "迭代后体能更强调旧伤与爆发代价。"


def test_character_iteration_infers_description_field_and_applies_by_default(client, monkeypatch):
    async def fake_call_ai(*args, **kwargs):
        return json.dumps({"人物描述": "迭代后人物描述写入标准摘要字段。"}, ensure_ascii=False)

    monkeypatch.setattr("apps.backend.app.services.ai_service.call_ai", fake_call_ai)
    project_id = first_project_id(client)
    before_versions = client.get(f"/api/projects/{project_id}/versions/character/char_muyiao").json()["data"]

    response = client.post(
        f"/api/projects/{project_id}/characters/char_muyiao/ai/iterate",
        json={"section": "人物描述", "instruction": "更新人物描述", "temperature": 0.2},
    )
    assert response.status_code == 200
    payload = response.json()["data"]["character"]
    assert payload["developer_data"]["basic"]["summary"] == "迭代后人物描述写入标准摘要字段。"
    assert "人物描述" not in payload["developer_data"]["basic"]

    detail = client.get(f"/api/projects/{project_id}/characters/detail/char_muyiao").json()["data"]
    assert detail["developer_data"]["basic"]["summary"] == "迭代后人物描述写入标准摘要字段。"

    after_versions = client.get(f"/api/projects/{project_id}/versions/character/char_muyiao").json()["data"]
    assert len(after_versions) == len(before_versions) + 1
    logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=character&target_id=char_muyiao").json()["data"]
    assert any(item["operation"] == "apply" and item["section"] == "basic" and item["field"] == "summary" for item in logs)


def test_character_iteration_infers_target_from_instruction_text(client, monkeypatch):
    async def fake_call_ai(*args, **kwargs):
        return json.dumps({"privateTruth": "按自由提示词写入隐秘真相，不影响基础描述。"}, ensure_ascii=False)

    monkeypatch.setattr("apps.backend.app.services.ai_service.call_ai", fake_call_ai)
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}/characters/detail/char_muyiao").json()["data"]

    response = client.post(
        f"/api/projects/{project_id}/characters/char_muyiao/ai/iterate",
        json={"instruction": "以上内容可以写在隐秘字段里面", "temperature": 0.2},
    )

    assert response.status_code == 200
    developer = response.json()["data"]["character"]["developer_data"]
    assert developer["secrets"]["privateTruth"] == "按自由提示词写入隐秘真相，不影响基础描述。"
    assert developer["basic"]["summary"] == before["developer_data"]["basic"]["summary"]


def test_character_iteration_selected_field_ignores_unrequested_sections(client, monkeypatch):
    async def fake_call_ai(*args, **kwargs):
        return json.dumps(
            {
                "developer_data": {
                    "basic": {"description": "只应该更新人物描述。", "status": "不应更新的境界"},
                    "secrets": {"privateTruth": "不应被字段迭代写入"},
                }
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr("apps.backend.app.services.ai_service.call_ai", fake_call_ai)
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}/characters/detail/char_muyiao").json()["data"]

    response = client.post(
        f"/api/projects/{project_id}/characters/char_muyiao/ai/iterate",
        json={"section": "人物描述", "instruction": "更新人物描述", "temperature": 0.2},
    )

    assert response.status_code == 200
    developer = response.json()["data"]["character"]["developer_data"]
    assert developer["basic"]["summary"] == "只应该更新人物描述。"
    assert developer["basic"]["status"] == before["developer_data"]["basic"]["status"]
    assert developer["secrets"]["privateTruth"] == before["developer_data"]["secrets"]["privateTruth"]


def test_character_iteration_maps_ai_alias_fields_without_custom_schema_pollution(client, monkeypatch):
    async def fake_call_ai(*args, **kwargs):
        return json.dumps(
            {
                "developer_data": {
                    "basic": {"description": "别名描述应进入标准摘要。", "level": "筑基圆满"},
                    "attributes": {"health": "经脉旧伤会限制爆发次数。", "unknownPower": "不可识别字段进入补充。"},
                }
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr("apps.backend.app.services.ai_service.call_ai", fake_call_ai)
    project_id = first_project_id(client)
    response = client.post(
        f"/api/projects/{project_id}/characters/char_muyiao/ai/iterate",
        json={"instruction": "模型返回别名字段", "apply": True, "temperature": 0.2},
    )
    assert response.status_code == 200
    developer = response.json()["data"]["character"]["developer_data"]

    assert developer["basic"]["summary"] == "别名描述应进入标准摘要。"
    assert developer["basic"]["status"] == "筑基圆满"
    assert "description" not in developer["basic"]
    assert "level" not in developer["basic"]
    assert developer["attributes"]["limitations"] == "经脉旧伤会限制爆发次数。"
    assert "health" not in developer["attributes"]
    assert "unknownPower" not in developer["attributes"]
    assert "unknownPower" in developer["extras"]


def test_consistency_check_passes_for_seeded_demo(client):
    project_id = first_project_id(client)
    response = client.get(f"/api/projects/{project_id}/consistency/check")
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["ok"] is True
    assert report["issues"] == []


def test_consistency_check_reports_orphan_references(client):
    from apps.backend.app.database import db, now, to_json_array

    project_id = first_project_id(client)
    db.exec(
        """INSERT INTO script_references (id, project_id, script_id, ref_type, ref_id, ref_name, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("ref_broken_world", project_id, "scr_scene_starfall", "worldbook", "missing_world", "缺失世界书", "测试孤儿引用", now()),
    )
    db.exec(
        "UPDATE characters SET world_entry_ids = ? WHERE project_id = ? AND id = ?",
        (to_json_array(["missing_world"]), project_id, "char_linyuan"),
    )

    response = client.get(f"/api/projects/{project_id}/consistency/check")
    assert response.status_code == 200
    report = response.json()["data"]
    issue_types = {issue["type"] for issue in report["issues"]}
    assert report["ok"] is False
    assert "missing_worldbook_reference" in issue_types
    assert "missing_character_world_link" in issue_types


def test_consistency_repair_removes_safe_fixable_issues(client):
    from apps.backend.app.database import db, now, to_json_array

    project_id = first_project_id(client)
    db.exec(
        """INSERT INTO script_references (id, project_id, script_id, ref_type, ref_id, ref_name, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("ref_repair_missing_world", project_id, "scr_scene_starfall", "worldbook", "missing_world", "缺失世界书", "测试修复孤儿引用", now()),
    )
    db.exec(
        "UPDATE characters SET world_entry_ids = ? WHERE project_id = ? AND id = ?",
        (to_json_array(["world_sky_seal", "missing_world"]), project_id, "char_linyuan"),
    )
    db.exec(
        """INSERT INTO worldbook_relations (id, project_id, source_id, target_id, relation_type, label, strength, description, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("wrel_self_test", project_id, "world_sky_seal", "world_sky_seal", "related", "自环", 1, "测试自环", now()),
    )
    db.exec(
        """INSERT INTO character_relations (id, project_id, source_id, target_id, relation_type, direction, description, numeric_value, events, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("crel_self_test", project_id, "char_linyuan", "char_linyuan", "ally", "bidirectional", "测试自环", 1, "[]", now(), now()),
    )

    before = client.get(f"/api/projects/{project_id}/consistency/check").json()["data"]
    assert before["ok"] is False

    repaired = client.post(f"/api/projects/{project_id}/consistency/repair")
    assert repaired.status_code == 200
    payload = repaired.json()["data"]
    action_types = {action["type"] for action in payload["actions"]}
    assert "missing_worldbook_reference" in action_types
    assert "missing_character_world_link" in action_types
    assert "worldbook_relation_self_loop" in action_types
    assert "character_relation_self_loop" in action_types
    assert payload["after"]["ok"] is True

    character = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
    assert character["world_entry_ids"] == ["world_sky_seal"]


def test_consistency_check_and_repair_tree_parent_cycles(client):
    from apps.backend.app.database import db

    project_id = first_project_id(client)
    db.exec(
        "UPDATE worldbook_categories SET parent_id = ? WHERE project_id = ? AND id = ?",
        ("cat_geography", project_id, "cat_history"),
    )
    db.exec(
        "UPDATE worldbook_categories SET parent_id = ? WHERE project_id = ? AND id = ?",
        ("cat_history", project_id, "cat_geography"),
    )
    db.exec(
        "UPDATE scripts SET parent_id = ? WHERE project_id = ? AND id = ?",
        ("scr_scene_starfall", project_id, "scr_outline_skyseal"),
    )

    report = client.get(f"/api/projects/{project_id}/consistency/check").json()["data"]
    issue_types = {issue["type"] for issue in report["issues"]}
    assert report["ok"] is False
    assert "worldbook_category_parent_cycle" in issue_types
    assert "script_parent_cycle" in issue_types

    repaired = client.post(f"/api/projects/{project_id}/consistency/repair")
    assert repaired.status_code == 200
    payload = repaired.json()["data"]
    action_types = {action["type"] for action in payload["actions"]}
    assert "worldbook_category_parent_cycle" in action_types
    assert "script_parent_cycle" in action_types
    assert payload["after"]["ok"] is True

    history = db.one("SELECT parent_id FROM worldbook_categories WHERE project_id = ? AND id = ?", (project_id, "cat_history"))
    outline = db.one("SELECT parent_id FROM scripts WHERE project_id = ? AND id = ?", (project_id, "scr_outline_skyseal"))
    assert history["parent_id"] is None
    assert outline["parent_id"] is None


def test_version_diff_reports_changed_worldbook_content(client):
    project_id = first_project_id(client)
    created = client.post(
        f"/api/projects/{project_id}/worldbook/entries",
        json={"category_id": "cat_geography", "title": "差异测试条目", "content": "旧正文", "tags": ["test"]},
    )
    assert created.status_code == 200
    entry_id = created.json()["data"]["id"]

    updated = client.put(f"/api/projects/{project_id}/worldbook/entries/{entry_id}", json={"content": "新正文"})
    assert updated.status_code == 200

    versions = client.get(f"/api/projects/{project_id}/versions/worldbook_entry/{entry_id}").json()["data"]
    original_version = sorted(versions, key=lambda item: item["version"])[0]
    diff = client.get(f"/api/projects/{project_id}/version-diff/{original_version['id']}")
    assert diff.status_code == 200
    rows = diff.json()["data"]["diffs"]
    content_diff = next(item for item in rows if item["path"] == "content")
    assert content_diff["before"] == "旧正文"
    assert content_diff["after"] == "新正文"

    restored = client.post(f"/api/projects/{project_id}/versions/{original_version['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["data"]["entity_type"] == "worldbook_entry"
    detail = client.get(f"/api/projects/{project_id}/worldbook/entries/{entry_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["content"] == "旧正文"
    after_versions = client.get(f"/api/projects/{project_id}/versions/worldbook_entry/{entry_id}").json()["data"]
    assert after_versions[0]["summary"] == "恢复版本 1"


def test_version_routes_reject_missing_version(client):
    project_id = first_project_id(client)
    diff = client.get(f"/api/projects/{project_id}/version-diff/missing_version")
    assert diff.status_code == 404
    assert diff.json()["detail"] == "版本不存在"

    restored = client.post(f"/api/projects/{project_id}/versions/missing_version/restore")
    assert restored.status_code == 404
    assert restored.json()["detail"] == "版本不存在"


def test_create_character_backfills_basic_gender(client):
    project_id = first_project_id(client)
    response = client.post(
        f"/api/projects/{project_id}/characters",
        json={
            "name": "测试角色",
            "character_type": "npc",
            "developer_data": {"basic": {"name": "测试角色"}, "knowledge": {}},
            "tags": ["test"],
        },
    )
    assert response.status_code == 200
    character = response.json()["data"]
    assert character["developer_data"]["basic"]["gender"] == ""
    assert character["field_visibility"]["basic"]["gender"]["visible"] is True
    assert character["player_data"]["basic"]["gender"] == ""


def test_character_visibility_update_rebuilds_player_view_without_losing_developer_data(client):
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
    private_truth = before["developer_data"]["secrets"]["privateTruth"]
    visibility = before["field_visibility"]
    visibility["secrets"]["privateTruth"] = {"visible": True, "displayMode": "custom", "customDisplay": "玩家只知道他有不能公开的旧债"}
    visibility["fortune"]["desire"] = {"visible": False, "displayMode": "hidden", "customDisplay": ""}

    updated = client.put(f"/api/projects/{project_id}/characters/char_linyuan", json={"field_visibility": visibility})
    assert updated.status_code == 200
    payload = updated.json()["data"]
    assert payload["developer_data"]["secrets"]["privateTruth"] == private_truth
    assert payload["player_data"]["secrets"]["privateTruth"] == "玩家只知道他有不能公开的旧债"
    assert payload["player_data"]["secrets"]["privateTruth"] != private_truth
    assert payload["player_data"]["fortune"]["desire"] == "未知"


def test_ai_iteration_routes_are_registered(client):
    routes = {getattr(route, "path", "") for route in client.app.routes}
    assert "/api/projects/{project_id}/worldbook/entries/{entry_id}/ai/iterate" in routes
    assert "/api/projects/{project_id}/characters/{character_id}/ai/iterate" in routes
    assert "/api/projects/{project_id}/scripts/{script_id}/ai/iterate" in routes
    assert "/api/projects/{project_id}/presets/{preset_id}/ai/iterate" in routes


def test_delete_character_removes_script_references(client):
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}/references/character/char_linyuan")
    assert before.status_code == 200
    assert before.json()["data"]
    before_relations = client.get(f"/api/projects/{project_id}/characters/relations/all")
    assert before_relations.status_code == 200
    assert any(
        row["source_id"] == "char_linyuan" or row["target_id"] == "char_linyuan"
        for row in before_relations.json()["data"]
    )

    response = client.delete(f"/api/projects/{project_id}/characters/char_linyuan")
    assert response.status_code == 200

    after = client.get(f"/api/projects/{project_id}/references/character/char_linyuan")
    assert after.status_code == 200
    assert after.json()["data"] == []
    after_relations = client.get(f"/api/projects/{project_id}/characters/relations/all")
    assert after_relations.status_code == 200
    assert all(
        row["source_id"] != "char_linyuan" and row["target_id"] != "char_linyuan"
        for row in after_relations.json()["data"]
    )


def test_delete_worldbook_entry_cleans_references_and_character_links(client):
    project_id = first_project_id(client)
    before = client.get(f"/api/projects/{project_id}/references/worldbook/world_sky_seal")
    assert before.status_code == 200
    assert before.json()["data"]

    response = client.delete(f"/api/projects/{project_id}/worldbook/entries/world_sky_seal")
    assert response.status_code == 200

    after = client.get(f"/api/projects/{project_id}/references/worldbook/world_sky_seal")
    assert after.status_code == 200
    assert after.json()["data"] == []

    character = client.get(f"/api/projects/{project_id}/characters/detail/char_linyuan").json()["data"]
    assert "world_sky_seal" not in character["world_entry_ids"]


def test_delete_script_cascades_subtree_and_cleans_script_references(client):
    project_id = first_project_id(client)
    parent = client.post(
        f"/api/projects/{project_id}/scripts",
        json={"node_type": "chapter", "title": "删除测试父节点"},
    )
    assert parent.status_code == 200
    parent_id = parent.json()["data"]["id"]

    child = client.post(
        f"/api/projects/{project_id}/scripts",
        json={"node_type": "scene", "title": "删除测试子节点", "parent_id": parent_id},
    )
    assert child.status_code == 200
    child_id = child.json()["data"]["id"]

    reference = client.post(
        f"/api/projects/{project_id}/scripts/{child_id}/references",
        json={"ref_type": "character", "ref_id": "char_linyuan", "description": "删除子树时应清理"},
    )
    assert reference.status_code == 200
    before = client.get(f"/api/projects/{project_id}/references/character/char_linyuan").json()["data"]
    assert any(row["script_id"] == child_id for row in before)

    response = client.delete(f"/api/projects/{project_id}/scripts/{parent_id}")
    assert response.status_code == 200

    child_detail = client.get(f"/api/projects/{project_id}/scripts/detail/{child_id}")
    assert child_detail.status_code == 404
    after = client.get(f"/api/projects/{project_id}/references/character/char_linyuan").json()["data"]
    assert all(row["script_id"] != child_id for row in after)


def test_mock_ai_script_generate_iterate_and_check_record_logs(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        generated = client.post(
            f"/api/projects/{project_id}/scripts/ai/generate",
            json={"title": "离线场景", "prompt": "补一个带选择压力的秘境场景", "temperature": 0.2},
        )
        assert generated.status_code == 200
        generated_payload = generated.json()["data"]
        assert "## 场景目标" in generated_payload["content"]
        assert generated_payload["generation_log"]

        iterated = client.post(
            f"/api/projects/{project_id}/scripts/scr_scene_starfall/ai/iterate",
            json={"section": "冲突推进", "instruction": "增强角色选择代价", "apply": False, "temperature": 0.2},
        )
        assert iterated.status_code == 200
        iterated_payload = iterated.json()["data"]
        assert "## 冲突推进" in iterated_payload["content"]
        assert "增强角色选择代价" in iterated_payload["ai_prompt"]

        checked = client.post(
            f"/api/projects/{project_id}/scripts/ai/check",
            json={"id": "scr_scene_starfall", "content": iterated_payload["content"]},
        )
        assert checked.status_code == 200
        assert checked.json()["data"]["overall_score"] == 88

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=script").json()["data"]
        operations = {item["operation"] for item in logs}
        assert {"generate", "iterate", "check"}.issubset(operations)


def test_mock_ai_script_iteration_previews_then_applies_with_version(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        before = client.get(f"/api/projects/{project_id}/scripts/detail/scr_scene_starfall").json()["data"]
        before_versions = client.get(f"/api/projects/{project_id}/versions/script/scr_scene_starfall").json()["data"]

        preview = client.post(
            f"/api/projects/{project_id}/scripts/scr_scene_starfall/ai/iterate",
            json={"section": "冲突推进", "instruction": "增强角色选择代价", "apply": False, "temperature": 0.2},
        )
        assert preview.status_code == 200
        preview_payload = preview.json()["data"]
        assert "## 冲突推进" in preview_payload["content"]
        assert preview_payload["content"].count("## 冲突推进") == 1
        assert "角色在有限信息下做出选择" in preview_payload["content"]

        unchanged = client.get(f"/api/projects/{project_id}/scripts/detail/scr_scene_starfall").json()["data"]
        assert unchanged["content"] == before["content"]
        assert unchanged["version"] == before["version"]

        applied = client.post(
            f"/api/projects/{project_id}/scripts/scr_scene_starfall/ai/iterate",
            json={"section": "冲突推进", "instruction": "增强角色选择代价", "apply": True, "temperature": 0.2},
        )
        assert applied.status_code == 200
        applied_script = applied.json()["data"]["script"]
        assert applied_script["version"] == int(before["version"]) + 1
        assert "## 冲突推进" in applied_script["content"]
        assert "角色在有限信息下做出选择" in applied_script["content"]

        after_versions = client.get(f"/api/projects/{project_id}/versions/script/scr_scene_starfall").json()["data"]
        assert len(after_versions) == len(before_versions) + 1
        assert after_versions[0]["entity_type"] == "script"
        assert after_versions[0]["summary"] == "AI迭代 冲突推进"
        assert "角色在有限信息下做出选择" in after_versions[0]["data"]["content"]
        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=script&target_id=scr_scene_starfall").json()["data"]
        apply_log = next(item for item in logs if item["operation"] == "apply")
        assert apply_log["section"] == "冲突推进"
        assert apply_log["instruction"] == "增强角色选择代价"
        assert apply_log["request"]["apply"] is True


def test_mock_ai_preset_generate_iterate_and_organize_record_logs(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        generated = client.post(
            f"/api/projects/{project_id}/presets/ai/generate",
            json={"description": "用于离线验证的稳定修仙叙事预设", "temperature": 0.2},
        )
        assert generated.status_code == 200
        generated_payload = generated.json()["data"]
        assert generated_payload["name"] == "mock 写作预设"
        assert "文风基调" in generated_payload["compiled_prompt"]

        iterated = client.post(
            f"/api/projects/{project_id}/presets/preset_xianxia_epic/ai/iterate",
            json={"section": "dimensions", "instruction": "强调伏笔与因果代价", "apply": False, "temperature": 0.2},
        )
        assert iterated.status_code == 200
        iterated_payload = iterated.json()["data"]["generated"]
        assert iterated_payload["name"] == "mock 写作预设"
        assert "compiled_prompt" in iterated_payload

        organized = client.post(f"/api/projects/{project_id}/presets/preset_xianxia_epic/organize")
        assert organized.status_code == 200
        organized_payload = organized.json()["data"]
        assert organized_payload["issues"] == []
        assert organized_payload["fixed_preset"]["name"] == "mock 写作预设"

        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=preset").json()["data"]
        operations = {item["operation"] for item in logs}
        assert {"generate", "iterate", "organize"}.issubset(operations)


def test_mock_ai_preset_apply_records_version(client):
    with mock_ai_provider():
        project_id = first_project_id(client)
        before = client.get(f"/api/projects/{project_id}/versions/preset/preset_xianxia_epic").json()["data"]
        response = client.post(
            f"/api/projects/{project_id}/presets/preset_xianxia_epic/ai/iterate",
            json={"section": "dimensions", "instruction": "应用并记录版本", "apply": True, "temperature": 0.2},
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["preset"]["name"] == "mock 写作预设"

        after = client.get(f"/api/projects/{project_id}/versions/preset/preset_xianxia_epic").json()["data"]
        assert len(after) == len(before) + 1
        assert after[0]["entity_type"] == "preset"
        assert after[0]["summary"] == "AI迭代 dimensions"
        assert after[0]["data"]["name"] == "mock 写作预设"
        logs = client.get(f"/api/projects/{project_id}/ai/logs?target_type=preset&target_id=preset_xianxia_epic").json()["data"]
        apply_log = next(item for item in logs if item["operation"] == "apply")
        assert apply_log["section"] == "dimensions"
        assert apply_log["instruction"] == "应用并记录版本"
        assert apply_log["request"]["apply"] is True


def test_preset_apply_builds_scene_specific_prompt(client):
    project_id = first_project_id(client)
    response = client.post(
        f"/api/projects/{project_id}/presets/apply",
        json={
            "preset_id": "preset_xianxia_epic",
            "scene_type": "script",
            "scene_requirements": "用于坠星秘境场景，强调选择代价。",
        },
    )
    assert response.status_code == 200
    prompt = response.json()["data"]["prompt"]
    assert "[系统提示]" in prompt
    assert "[应用场景]" in prompt
    assert "[场景调整]" in prompt
    assert "用于坠星秘境场景，强调选择代价。" in prompt
    assert "输出可阅读场景，包含动作、对白、转折。" in prompt


def test_preset_combine_merges_override_and_base_into_readable_prompt(client):
    project_id = first_project_id(client)
    response = client.post(
        f"/api/projects/{project_id}/presets/combine",
        json={"base_id": "preset_xianxia_epic", "override_id": "preset_sword_duel"},
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["dimensions"]
    assert payload["custom_blocks"]
    assert payload["application_scenes"]
    assert "compiled_prompt" in payload
    assert "动作清晰，招式有代价" in payload["compiled_prompt"]
    assert "强调天地尺度、历史纵深和角色命运感" in payload["compiled_prompt"]


def test_preset_crud_and_export_routes(client):
    project_id = first_project_id(client)
    created = client.post(
        f"/api/projects/{project_id}/presets",
        json={
            "name": "路由拆分测试预设",
            "description": "验证预设非 AI 路由拆分后仍能完整闭环。",
            "category": "测试",
            "dimensions": [{"name": "叙事密度", "value": "高", "description": "每段都有信息增量", "examples": ["动机、冲突、代价"], "order": 0}],
            "custom_blocks": [{"title": "执行规则", "content": "输出可直接保存的内容。", "position": "before", "order": 0}],
            "application_scenes": [{"sceneType": "character", "enabled": True, "adjustments": "强调人物动机"}],
            "tags": ["router"],
        },
    )
    assert created.status_code == 200
    preset_id = created.json()["data"]["id"]
    assert "叙事密度" in created.json()["data"]["compiled_prompt"]

    listed = client.get(f"/api/projects/{project_id}/presets?category=测试")
    assert listed.status_code == 200
    assert any(item["id"] == preset_id for item in listed.json()["data"])

    updated = client.put(f"/api/projects/{project_id}/presets/{preset_id}", json={"description": "更新后的预设描述"})
    assert updated.status_code == 200
    assert updated.json()["data"]["description"] == "更新后的预设描述"

    exported = client.get(f"/api/projects/{project_id}/presets/export?format=markdown")
    assert exported.status_code == 200
    assert "路由拆分测试预设" in exported.json()["data"]["content"]

    deleted = client.delete(f"/api/projects/{project_id}/presets/{preset_id}")
    assert deleted.status_code == 200
    detail = client.get(f"/api/projects/{project_id}/presets/detail/{preset_id}")
    assert detail.status_code == 404


def test_preset_version_diff_and_restore(client):
    project_id = first_project_id(client)
    original = client.get(f"/api/projects/{project_id}/presets/detail/preset_xianxia_epic").json()["data"]
    updated = client.put(
        f"/api/projects/{project_id}/presets/preset_xianxia_epic",
        json={"description": "预设版本测试描述"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["description"] == "预设版本测试描述"

    versions = client.get(f"/api/projects/{project_id}/versions/preset/preset_xianxia_epic").json()["data"]
    original_version = sorted(versions, key=lambda item: item["version"])[0]
    diff = client.get(f"/api/projects/{project_id}/version-diff/{original_version['id']}")
    assert diff.status_code == 200
    rows = diff.json()["data"]["diffs"]
    description_diff = next(item for item in rows if item["path"] == "description")
    assert description_diff["before"] == original["description"]
    assert description_diff["after"] == "预设版本测试描述"

    restored = client.post(f"/api/projects/{project_id}/versions/{original_version['id']}/restore")
    assert restored.status_code == 200
    detail = client.get(f"/api/projects/{project_id}/presets/detail/preset_xianxia_epic")
    assert detail.status_code == 200
    assert detail.json()["data"]["description"] == original["description"]


def test_restore_version_restores_script_content(client):
    project_id = first_project_id(client)
    created = client.post(
        f"/api/projects/{project_id}/scripts",
        json={"node_type": "scene", "title": "恢复测试场景", "content": "初版内容", "summary": "初版摘要"},
    )
    assert created.status_code == 200
    script_id = created.json()["data"]["id"]

    updated = client.put(
        f"/api/projects/{project_id}/scripts/{script_id}",
        json={"content": "改写后的内容", "summary": "改写摘要"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["content"] == "改写后的内容"

    versions = client.get(f"/api/projects/{project_id}/versions/script/{script_id}").json()["data"]
    original_version = sorted(versions, key=lambda item: item["version"])[0]
    restored = client.post(f"/api/projects/{project_id}/versions/{original_version['id']}/restore")
    assert restored.status_code == 200

    detail = client.get(f"/api/projects/{project_id}/scripts/detail/{script_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["content"] == "初版内容"


def test_restore_version_restores_character_developer_data(client):
    project_id = first_project_id(client)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json={
            "name": "恢复测试角色",
            "developer_data": {
                "basic": {"name": "恢复测试角色", "gender": "女", "summary": "初版人物摘要"},
                "knowledge": {"background": "初版背景"},
            },
        },
    )
    assert created.status_code == 200
    character_id = created.json()["data"]["id"]

    developer = created.json()["data"]["developer_data"]
    developer["basic"]["summary"] = "改写后人物摘要"
    developer["knowledge"]["background"] = "改写后背景"
    updated = client.put(f"/api/projects/{project_id}/characters/{character_id}", json={"developer_data": developer})
    assert updated.status_code == 200
    assert updated.json()["data"]["developer_data"]["basic"]["summary"] == "改写后人物摘要"

    versions = client.get(f"/api/projects/{project_id}/versions/character/{character_id}").json()["data"]
    original_version = sorted(versions, key=lambda item: item["version"])[0]
    restored = client.post(f"/api/projects/{project_id}/versions/{original_version['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["data"]["entity_type"] == "character"

    detail = client.get(f"/api/projects/{project_id}/characters/detail/{character_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["developer_data"]["basic"]["summary"] == "初版人物摘要"
    assert detail.json()["data"]["developer_data"]["knowledge"]["background"] == "初版背景"
    after_versions = client.get(f"/api/projects/{project_id}/versions/character/{character_id}").json()["data"]
    assert after_versions[0]["summary"] == "恢复版本 1"


def test_script_parent_validation_rejects_cycles_and_cross_project_parent(client):
    project_id = first_project_id(client)
    parent = client.post(f"/api/projects/{project_id}/scripts", json={"node_type": "chapter", "title": "树校验父节点"}).json()["data"]
    child = client.post(f"/api/projects/{project_id}/scripts", json={"node_type": "scene", "title": "树校验子节点", "parent_id": parent["id"]}).json()["data"]

    self_parent = client.put(f"/api/projects/{project_id}/scripts/{child['id']}", json={"parent_id": child["id"]})
    assert self_parent.status_code == 400
    assert "自身" in self_parent.json()["detail"]

    descendant_parent = client.put(f"/api/projects/{project_id}/scripts/{parent['id']}", json={"parent_id": child["id"]})
    assert descendant_parent.status_code == 400
    assert "子级" in descendant_parent.json()["detail"]

    restored = client.put(f"/api/projects/{project_id}/scripts/{child['id']}", json={"parent_id": None})
    assert restored.status_code == 200
    assert restored.json()["data"]["parent_id"] is None

    other_project = client.post("/api/projects", json={"name": "树校验隔离项目"}).json()["data"]
    cross_project = client.post(f"/api/projects/{other_project['id']}/scripts", json={"node_type": "scene", "title": "跨项目父级", "parent_id": parent["id"]})
    assert cross_project.status_code == 400
    assert "当前项目" in cross_project.json()["detail"]


def test_worldbook_category_parent_validation_rejects_cycles_and_batch_cycle(client):
    project_id = first_project_id(client)
    parent = client.post(f"/api/projects/{project_id}/worldbook/categories", json={"name": "树校验分类父级"}).json()["data"]
    child = client.post(f"/api/projects/{project_id}/worldbook/categories", json={"name": "树校验分类子级", "parent_id": parent["id"]}).json()["data"]

    self_parent = client.put(f"/api/projects/{project_id}/worldbook/categories/{child['id']}", json={"parent_id": child["id"]})
    assert self_parent.status_code == 400
    assert "自身" in self_parent.json()["detail"]

    descendant_parent = client.put(f"/api/projects/{project_id}/worldbook/categories/{parent['id']}", json={"parent_id": child["id"]})
    assert descendant_parent.status_code == 400
    assert "子级" in descendant_parent.json()["detail"]

    batch_cycle = client.patch(
        f"/api/projects/{project_id}/worldbook/categories/sort",
        json=[
            {"id": parent["id"], "parent_id": child["id"], "sort_order": 0},
            {"id": child["id"], "parent_id": parent["id"], "sort_order": 1},
        ],
    )
    assert batch_cycle.status_code == 400

    restored = client.put(f"/api/projects/{project_id}/worldbook/categories/{child['id']}", json={"parent_id": None})
    assert restored.status_code == 200
    assert restored.json()["data"]["parent_id"] is None
