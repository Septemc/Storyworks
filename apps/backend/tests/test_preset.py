from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_preset_crud_test_and_export_flow() -> None:
    with TestClient(app) as client:
        project_response = client.post(
            "/api/projects",
            json={
                "title": f"Preset Test Project {uuid4()}",
                "summary": "Project for preset module testing.",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        generate_response = client.post(
            "/api/presets/generate",
            json={
                "title": "黑暗悬疑基调",
                "preset_type": "文风预设",
                "style_goal": "黑暗悬疑、压抑、伏笔密集",
                "reference_text": "",
                "target_use": "剧本与正文生成",
                "status": "draft",
            },
        )
        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert generated["title"] == "黑暗悬疑基调"

        create_response = client.post(f"/api/projects/{project_id}/presets", json=generated)
        assert create_response.status_code == 201
        preset_id = create_response.json()["id"]

        list_response = client.get(f"/api/projects/{project_id}/presets")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

        test_response = client.post(
            "/api/presets/test",
            json={
                "title": generated["title"],
                "preset_type": generated["preset_type"],
                "style_description": generated["style_description"],
                "wording_tendency": generated["wording_tendency"],
                "sentence_tendency": generated["sentence_tendency"],
                "description_density": generated["description_density"],
                "dialogue_ratio": generated["dialogue_ratio"],
                "rhythm_tendency": generated["rhythm_tendency"],
                "emotion_intensity": generated["emotion_intensity"],
                "plot_preferences": generated["plot_preferences"],
                "character_preferences": generated["character_preferences"],
                "forbidden_expressions": generated["forbidden_expressions"],
                "output_requirements": generated["output_requirements"],
                "sample_target": "剧本草稿",
                "sample_input": "主角进入被封锁的档案馆调查真相。",
            },
        )
        assert test_response.status_code == 200
        assert "剧本草稿" in test_response.json()["preview_summary"]

        update_response = client.patch(
            f"/api/presets/{preset_id}",
            json={"status": "ready", "notes": "更新后的备注。"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "ready"

        export_json_response = client.get(f"/api/presets/{preset_id}/export?format=json")
        assert export_json_response.status_code == 200
        assert export_json_response.json()["title"] == "黑暗悬疑基调"

        export_markdown_response = client.get(f"/api/presets/{preset_id}/export?format=markdown")
        assert export_markdown_response.status_code == 200
        assert "# 黑暗悬疑基调" in export_markdown_response.text

        delete_response = client.delete(f"/api/presets/{preset_id}")
        assert delete_response.status_code == 204
