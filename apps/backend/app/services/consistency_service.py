from __future__ import annotations

from ..database import db, parse_json, to_json_array


def _exists(table: str, project_id: str, entity_id: str) -> bool:
    row = db.one(f"SELECT id FROM {table} WHERE project_id = ? AND id = ?", (project_id, entity_id))
    return row is not None


def _tree_parent_issues(project_id: str, table: str, entity: str, label: str, missing_type: str, self_type: str, cycle_type: str) -> list[dict]:
    rows = db.all(f"SELECT id, parent_id FROM {table} WHERE project_id = ?", (project_id,))
    parents = {row["id"]: row.get("parent_id") for row in rows}
    issues: list[dict] = []
    seen_issue_keys: set[tuple[str, str]] = set()

    def add_issue(issue_type: str, node_id: str, message: str):
        key = (issue_type, node_id)
        if key in seen_issue_keys:
            return
        seen_issue_keys.add(key)
        issues.append({"type": issue_type, "entity": entity, "id": node_id, "message": message})

    for node_id, parent_id in parents.items():
        if not parent_id:
            continue
        if parent_id == node_id:
            add_issue(self_type, node_id, f"{label}父级不能指向自身")
            continue
        if parent_id not in parents:
            add_issue(missing_type, node_id, f"{label}父级不存在：{parent_id}")
            continue

        visited = {node_id}
        cursor = parent_id
        while cursor:
            if cursor in visited:
                add_issue(cycle_type, node_id, f"{label}父级链存在循环")
                break
            visited.add(cursor)
            cursor = parents.get(cursor)
            if cursor and cursor not in parents:
                add_issue(missing_type, node_id, f"{label}父级不存在：{cursor}")
                break

    return issues


def project_consistency_report(project_id: str) -> dict:
    issues: list[dict] = []

    script_refs = db.all("SELECT * FROM script_references WHERE project_id = ?", (project_id,))
    for ref in script_refs:
        if not _exists("scripts", project_id, ref.get("script_id")):
            issues.append({"type": "missing_script", "entity": "script_reference", "id": ref["id"], "message": "脚本引用所属节点不存在"})
        if ref.get("ref_type") == "worldbook" and not _exists("worldbook_entries", project_id, ref.get("ref_id")):
            issues.append({"type": "missing_worldbook_reference", "entity": "script_reference", "id": ref["id"], "message": f"世界书引用目标不存在：{ref.get('ref_id')}"})
        elif ref.get("ref_type") == "character" and not _exists("characters", project_id, ref.get("ref_id")):
            issues.append({"type": "missing_character_reference", "entity": "script_reference", "id": ref["id"], "message": f"角色引用目标不存在：{ref.get('ref_id')}"})
        elif ref.get("ref_type") not in ("worldbook", "character"):
            issues.append({"type": "invalid_reference_type", "entity": "script_reference", "id": ref["id"], "message": f"未知引用类型：{ref.get('ref_type')}"})

    character_rows = db.all("SELECT id, name, world_entry_ids FROM characters WHERE project_id = ?", (project_id,))
    for char in character_rows:
        for entry_id in parse_json(char.get("world_entry_ids"), []):
            if not _exists("worldbook_entries", project_id, entry_id):
                issues.append({"type": "missing_character_world_link", "entity": "character", "id": char["id"], "message": f"角色 {char['name']} 关联的世界书不存在：{entry_id}"})

    for rel in db.all("SELECT id, source_id, target_id FROM worldbook_relations WHERE project_id = ?", (project_id,)):
        if rel["source_id"] == rel["target_id"]:
            issues.append({"type": "worldbook_relation_self_loop", "entity": "worldbook_relation", "id": rel["id"], "message": "世界书关系不能指向自身"})

    for rel in db.all("SELECT id, source_id, target_id FROM character_relations WHERE project_id = ?", (project_id,)):
        if rel["source_id"] == rel["target_id"]:
            issues.append({"type": "character_relation_self_loop", "entity": "character_relation", "id": rel["id"], "message": "人物关系不能指向自身"})

    issues.extend(
        _tree_parent_issues(
            project_id,
            "worldbook_categories",
            "worldbook_category",
            "世界书分类",
            "missing_worldbook_category_parent",
            "worldbook_category_parent_self_loop",
            "worldbook_category_parent_cycle",
        )
    )
    issues.extend(
        _tree_parent_issues(
            project_id,
            "scripts",
            "script",
            "剧本节点",
            "missing_script_parent",
            "script_parent_self_loop",
            "script_parent_cycle",
        )
    )

    worldbook_count = db.one("SELECT COUNT(*) c FROM worldbook_entries WHERE project_id = ?", (project_id,))["c"]
    summary = {
        "issues": len(issues),
        "script_references": len(script_refs),
        "characters": len(character_rows),
        "worldbook_entries": worldbook_count,
    }
    return {"ok": not issues, "summary": summary, "issues": issues}


def repair_project_consistency(project_id: str) -> dict:
    actions: list[dict] = []

    for ref in db.all("SELECT * FROM script_references WHERE project_id = ?", (project_id,)):
        reason = ""
        if not _exists("scripts", project_id, ref.get("script_id")):
            reason = "missing_script"
        elif ref.get("ref_type") == "worldbook" and not _exists("worldbook_entries", project_id, ref.get("ref_id")):
            reason = "missing_worldbook_reference"
        elif ref.get("ref_type") == "character" and not _exists("characters", project_id, ref.get("ref_id")):
            reason = "missing_character_reference"
        elif ref.get("ref_type") not in ("worldbook", "character"):
            reason = "invalid_reference_type"
        if reason:
            db.exec("DELETE FROM script_references WHERE project_id = ? AND id = ?", (project_id, ref["id"]))
            actions.append({"type": reason, "entity": "script_reference", "id": ref["id"], "action": "deleted"})

    for char in db.all("SELECT id, name, world_entry_ids FROM characters WHERE project_id = ?", (project_id,)):
        world_ids = parse_json(char.get("world_entry_ids"), [])
        repaired_ids = [entry_id for entry_id in world_ids if _exists("worldbook_entries", project_id, entry_id)]
        if repaired_ids != world_ids:
            db.exec("UPDATE characters SET world_entry_ids = ? WHERE project_id = ? AND id = ?", (to_json_array(repaired_ids), project_id, char["id"]))
            actions.append({"type": "missing_character_world_link", "entity": "character", "id": char["id"], "action": "filtered_world_entry_ids"})

    for rel in db.all("SELECT id, source_id, target_id FROM worldbook_relations WHERE project_id = ?", (project_id,)):
        if rel["source_id"] == rel["target_id"]:
            db.exec("DELETE FROM worldbook_relations WHERE project_id = ? AND id = ?", (project_id, rel["id"]))
            actions.append({"type": "worldbook_relation_self_loop", "entity": "worldbook_relation", "id": rel["id"], "action": "deleted"})

    for rel in db.all("SELECT id, source_id, target_id FROM character_relations WHERE project_id = ?", (project_id,)):
        if rel["source_id"] == rel["target_id"]:
            db.exec("DELETE FROM character_relations WHERE project_id = ? AND id = ?", (project_id, rel["id"]))
            actions.append({"type": "character_relation_self_loop", "entity": "character_relation", "id": rel["id"], "action": "deleted"})

    tree_issue_types = {
        "missing_worldbook_category_parent",
        "worldbook_category_parent_self_loop",
        "worldbook_category_parent_cycle",
        "missing_script_parent",
        "script_parent_self_loop",
        "script_parent_cycle",
    }
    for issue in project_consistency_report(project_id)["issues"]:
        if issue["type"] not in tree_issue_types:
            continue
        table = "worldbook_categories" if issue["entity"] == "worldbook_category" else "scripts"
        db.exec(f"UPDATE {table} SET parent_id = NULL WHERE project_id = ? AND id = ?", (project_id, issue["id"]))
        actions.append({"type": issue["type"], "entity": issue["entity"], "id": issue["id"], "action": "reset_parent"})

    return {"actions": actions, "after": project_consistency_report(project_id)}
