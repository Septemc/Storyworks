from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_character_template_and_crud_flow() -> None:
    with TestClient(app) as client:
        project_response = client.post(
            "/api/projects",
            json={
                "title": f"Character Test Project {uuid4()}",
                "summary": "Project for character module testing.",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        templates_response = client.get("/api/character/templates")
        assert templates_response.status_code == 200
        templates = templates_response.json()
        assert len(templates) >= 1
        template_id = templates[0]["template_id"]

        generate_response = client.post(
            "/api/characters/generate",
            json={
                "template_id": template_id,
                "name_hint": "林青溪",
                "concept": "北境巡夜人，外冷内热，追查旧案多年。",
                "project_context": "寒地联邦背景，政治与边境危机并存。",
                "status": "draft",
            },
        )
        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert generated["name"] == "林青溪"
        assert generated["player_mode"]["tab_secrets"]["f_trauma"] == "未知"

        create_response = client.post(
            f"/api/projects/{project_id}/characters",
            json={
                "template_id": generated["template_id"],
                "developer_mode": generated["developer_mode"],
                "player_mode": generated["player_mode"],
                "meta": generated["meta"],
                "notes": generated["notes"],
                "status": "draft",
            },
        )
        assert create_response.status_code == 201
        character_id = create_response.json()["id"]

        list_response = client.get(f"/api/projects/{project_id}/characters")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

        updated_payload = {
            "developer_mode": generated["developer_mode"],
            "player_mode": generated["player_mode"],
            "meta": {"source": "test"},
            "notes": "更新后的备注。",
            "status": "ready",
        }
        update_response = client.patch(f"/api/characters/{character_id}", json=updated_payload)
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "ready"

        export_json_response = client.get(f"/api/characters/{character_id}/export?format=json")
        assert export_json_response.status_code == 200
        assert export_json_response.json()["name"] == "林青溪"

        export_markdown_response = client.get(f"/api/characters/{character_id}/export?format=markdown")
        assert export_markdown_response.status_code == 200
        assert "# 林青溪" in export_markdown_response.text

        delete_response = client.delete(f"/api/characters/{character_id}")
        assert delete_response.status_code == 204
