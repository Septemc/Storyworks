from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_worldbook_crud_and_export() -> None:
    with TestClient(app) as client:
        project_payload = {
            "title": f"Worldbook Test Project {uuid4()}",
            "summary": "Project for worldbook module testing.",
        }
        project_response = client.post("/api/projects", json=project_payload)
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        create_payload = {
            "category": "政治",
            "title": "七城议会",
            "summary": "北境联邦的最高协商机构。",
            "keywords": ["联邦", "议会"],
            "content": {
                "definition": "七城议会是北境联邦的协商核心。",
                "origin": "战争后成立。",
                "structure": "每城一席。",
                "rules": "重大决议需五席通过。",
                "impact": "影响财政、军事与外交。",
            },
            "notes": "测试条目。",
            "status": "draft",
        }
        create_response = client.post(f"/api/projects/{project_id}/worldbook", json=create_payload)
        assert create_response.status_code == 201
        entry_id = create_response.json()["id"]

        list_response = client.get(f"/api/projects/{project_id}/worldbook")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 1

        update_response = client.patch(
            f"/api/worldbook/{entry_id}",
            json={"summary": "更新后的摘要。", "status": "ready"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["summary"] == "更新后的摘要。"
        assert update_response.json()["status"] == "ready"

        generate_response = client.post(
            "/api/worldbook/generate",
            json={
                "category": "制度",
                "title": "寒地征募令",
                "idea": "战后联邦征召边境居民补充常备军",
                "mode": "draft",
            },
        )
        assert generate_response.status_code == 200
        assert generate_response.json()["title"] == "寒地征募令"

        export_json_response = client.get(f"/api/worldbook/{entry_id}/export?format=json")
        assert export_json_response.status_code == 200
        assert export_json_response.json()["title"] == "七城议会"

        export_markdown_response = client.get(f"/api/worldbook/{entry_id}/export?format=markdown")
        assert export_markdown_response.status_code == 200
        assert "# 七城议会" in export_markdown_response.text

        delete_response = client.delete(f"/api/worldbook/{entry_id}")
        assert delete_response.status_code == 204
