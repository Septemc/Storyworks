from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_script_crud_and_export_flow() -> None:
    with TestClient(app) as client:
        project_response = client.post(
            "/api/projects",
            json={
                "title": f"Script Test Project {uuid4()}",
                "summary": "Project for script module testing.",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        generate_response = client.post(
            "/api/scripts/generate",
            json={
                "title": "北境风暴",
                "script_type": "主线",
                "concept": "主角被卷入联邦边境危机，并逐步揭开七城议会与旧王朝残党的关系。",
                "project_context": "寒地联邦，政治与军事 tension 持续上升。",
                "status": "draft",
            },
        )
        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert generated["title"] == "北境风暴"
        assert len(generated["scene_cards"]) >= 1

        create_response = client.post(f"/api/projects/{project_id}/scripts", json=generated)
        assert create_response.status_code == 201
        script_id = create_response.json()["id"]

        list_response = client.get(f"/api/projects/{project_id}/scripts")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

        update_response = client.patch(
            f"/api/scripts/{script_id}",
            json={
                "summary": "更新后的剧本摘要。",
                "status": "ready",
                "scene_cards": generated["scene_cards"],
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "ready"

        export_json_response = client.get(f"/api/scripts/{script_id}/export?format=json")
        assert export_json_response.status_code == 200
        assert export_json_response.json()["title"] == "北境风暴"

        export_markdown_response = client.get(f"/api/scripts/{script_id}/export?format=markdown")
        assert export_markdown_response.status_code == 200
        assert "# 北境风暴" in export_markdown_response.text

        delete_response = client.delete(f"/api/scripts/{script_id}")
        assert delete_response.status_code == 204
