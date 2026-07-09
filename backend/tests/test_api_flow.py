from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fastapi.testclient import TestClient


def test_core_flow(tmp_path: Path) -> None:
    os.environ["LOCAL_STORE_PATH"] = str(tmp_path / "modeltrace-test.json")
    os.environ["MONGODB_URL"] = ""

    from app.main import app

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

        register = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Diego Xavier",
                "email": "diegohenrique.mail@gmail.com",
                "password": "D1eg0X@vi3rHUB",
                "organization_name": "UF NoSQL",
                "job_title": "Cientista de Dados",
                "department": "Governança Analítica",
                "company": "UFU",
                "phone": "+55 34 99999-0000",
            },
        )
        assert register.status_code == 201, register.text
        token = register.json()["access_token"]
        assert register.json()["user"]["email_verified"] is False
        assert register.json()["user"]["job_title"] == "Cientista de Dados"
        assert "password_hash" not in register.json()["user"]
        assert "email_hash" not in register.json()["user"]
        headers = {"Authorization": f"Bearer {token}"}
        cookie_me = client.get("/api/v1/auth/me")
        assert cookie_me.status_code == 200, cookie_me.text

        outbox = tmp_path / "email_outbox.jsonl"
        verification_message = json.loads(outbox.read_text(encoding="utf-8").strip().splitlines()[-1])
        verification_token = re.search(r"verify_email_token=([A-Za-z0-9_\\-]+)", verification_message["text"]).group(1)
        verification = client.post("/api/v1/auth/verify-email", json={"token": verification_token})
        assert verification.status_code == 200, verification.text
        assert verification.json()["user"]["email_verified"] is True

        profile = client.patch(
            "/api/v1/auth/me",
            headers=headers,
            json={"job_title": "Lead Data Scientist", "bio": "Responsável por monitoramento e governança de modelos."},
        )
        assert profile.status_code == 200, profile.text
        assert profile.json()["user"]["job_title"] == "Lead Data Scientist"

        avatar = client.post(
            "/api/v1/auth/me/avatar",
            headers=headers,
            json={
                "file_name": "avatar.png",
                "content_type": "image/png",
                "data_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            },
        )
        assert avatar.status_code == 200, avatar.text
        assert avatar.json()["user"]["avatar_url"].endswith("/auth/me/avatar?v=" + avatar.json()["user"]["avatar_url"].split("v=")[-1])
        avatar_download = client.get("/api/v1/auth/me/avatar", headers=headers)
        assert avatar_download.status_code == 200, avatar_download.text

        reset_request = client.post("/api/v1/auth/password-reset/request", json={"email": "diegohenrique.mail@gmail.com"})
        assert reset_request.status_code == 200, reset_request.text
        reset_message = json.loads(outbox.read_text(encoding="utf-8").strip().splitlines()[-1])
        reset_token = re.search(r"reset_token=([A-Za-z0-9_\\-]+)", reset_message["text"]).group(1)
        reset_confirm = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "N0v@SenhaForte2026"},
        )
        assert reset_confirm.status_code == 200, reset_confirm.text
        relogin = client.post(
            "/api/v1/auth/login",
            json={"email": "diegohenrique.mail@gmail.com", "password": "N0v@SenhaForte2026"},
        )
        assert relogin.status_code == 200, relogin.text

        weak_register = client.post(
            "/api/v1/auth/register",
            json={
                "name": "Weak User",
                "email": "weak@example.com",
                "password": "secret123",
                "organization_name": "UF NoSQL",
            },
        )
        assert weak_register.status_code == 422

        project = client.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Academic Dropout Risk", "bias_sensitive_features": ["scholarship", "night_shift"]},
        )
        assert project.status_code == 201, project.text
        project_id = project.json()["_id"]

        model = client.post(
            f"/api/v1/projects/{project_id}/models",
            headers=headers,
            json={
                "name": "Dropout Risk Classifier",
                "target_name": "dropout",
                "expected_features": [{"name": "attendance_rate", "type": "float"}],
            },
        )
        assert model.status_code == 201, model.text
        model_id = model.json()["_id"]

        older_version = client.post(
            f"/api/v1/models/{model_id}/versions",
            headers=headers,
            json={"version": "v1.1.0", "status": "deprecated", "features": ["attendance_rate"]},
        )
        assert older_version.status_code == 201, older_version.text

        version = client.post(
            f"/api/v1/models/{model_id}/versions",
            headers=headers,
            json={"version": "v1.2.0", "status": "production", "features": ["attendance_rate"]},
        )
        assert version.status_code == 201, version.text

        contract = client.patch(
            f"/api/v1/projects/{project_id}/data-contract",
            headers=headers,
            json={"mode": "block", "expected_features": [{"name": "attendance_rate", "type": "numeric", "required": True}]},
        )
        assert contract.status_code == 200, contract.text
        assert contract.json()["mode"] == "block"

        api_key_response = client.post(
            f"/api/v1/projects/{project_id}/api-keys",
            headers=headers,
            json={"name": "Seed pipeline", "scopes": ["predictions:write", "feedback:write"]},
        )
        assert api_key_response.status_code == 201, api_key_response.text
        api_key = api_key_response.json()["api_key"]

        contract_violation = client.post(
            "/api/v1/predictions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "project_id": project_id,
                "model_id": model_id,
                "model_version": "v1.2.0",
                "entity_id": "student_contract_error",
                "features": {"other": 1},
                "prediction": {"label": "high_risk", "score": 0.82, "threshold": 0.70},
                "metadata": {"request_id": "req_contract_error"},
            },
        )
        assert contract_violation.status_code == 422

        prediction = client.post(
            "/api/v1/predictions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "project_id": project_id,
                "model_id": model_id,
                "model_version": "v1.2.0",
                "entity_id": "student_001",
                "features": {"attendance_rate": 0.61, "failed_subjects": 3, "avg_grade": 58.0},
                "prediction": {"label": "high_risk", "score": 0.82, "threshold": 0.70},
                "metadata": {"request_id": "req_test_001"},
            },
        )
        assert prediction.status_code == 201, prediction.text
        prediction_id = prediction.json()["prediction_id"]
        assert prediction.json()["prediction"]["entity"]["id"] == "student_001"

        timeline = client.get(f"/api/v1/projects/{project_id}/entity-timeline?q=student_001", headers=headers)
        assert timeline.status_code == 200, timeline.text
        assert len(timeline.json()["predictions"]) == 1

        note = client.post(
            f"/api/v1/projects/{project_id}/entity-notes",
            headers=headers,
            json={"entity_id": "student_001", "content": "Priorizar acompanhamento.", "tags": ["priority"]},
        )
        assert note.status_code == 201, note.text

        saved_view = client.post(
            "/api/v1/saved-views",
            headers=headers,
            json={"view": "predictions", "name": "High risk view", "filters": {"label": "high_risk"}, "columns": ["entity", "score"]},
        )
        assert saved_view.status_code == 201, saved_view.text
        assert client.get("/api/v1/saved-views", headers=headers).json()["items"]

        duplicated = client.post(
            "/api/v1/predictions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "project_id": project_id,
                "model_id": model_id,
                "model_version": "v1.2.0",
                "entity_id": "student_001",
                "features": {"attendance_rate": 0.61, "failed_subjects": 3, "avg_grade": 58.0},
                "prediction": {"label": "high_risk", "score": 0.82, "threshold": 0.70},
                "metadata": {"request_id": "req_test_001"},
            },
        )
        assert duplicated.status_code == 409

        feedback = client.post(
            f"/api/v1/predictions/{prediction_id}/feedback",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"observed_value": 1, "source": "academic_records"},
        )
        assert feedback.status_code == 200, feedback.text
        assert feedback.json()["feedback"]["classification_result"] == "tp"

        dashboard = client.get(f"/api/v1/projects/{project_id}/dashboard", headers=headers)
        assert dashboard.status_code == 200, dashboard.text
        assert dashboard.json()["kpis"]["total_predictions"] == 1

        posture = client.get("/api/v1/security/posture", headers=headers)
        assert posture.status_code == 200, posture.text
        assert any(item["id"] == "field_encryption" for item in posture.json()["checks"])

        annotation = client.post(
            f"/api/v1/predictions/{prediction_id}/annotations",
            headers=headers,
            json={"type": "analyst_note", "content": "Student contacted.", "tags": ["contacted"]},
        )
        assert annotation.status_code == 201, annotation.text

        whatif = client.post(
            f"/api/v1/predictions/{prediction_id}/whatif",
            headers=headers,
            json={"hypothetical_features": {"attendance_rate": 0.91, "failed_subjects": 0}},
        )
        assert whatif.status_code == 200, whatif.text
        assert "estimated_score" in whatif.json()

        replay = client.post(
            f"/api/v1/predictions/{prediction_id}/replay",
            headers=headers,
            json={"target_version": "v1.3.0", "replay_score": 0.42},
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["replay"]["target_version"] == "v1.3.0"

        compare = client.get(
            f"/api/v1/models/{model_id}/versions/compare?a=v1.1.0&b=v1.2.0",
            headers=headers,
        )
        assert compare.status_code == 200, compare.text
        assert "delta" in compare.json()

        bias = client.get(f"/api/v1/models/{model_id}/bias-analysis?feature=attendance_rate", headers=headers)
        assert bias.status_code == 200, bias.text
        assert "methodological_warning" in bias.json()

        drift = client.post(f"/api/v1/models/{model_id}/drift/run", headers=headers)
        assert drift.status_code == 200, drift.text

        alert_rule = client.post(
            "/api/v1/alert-rules",
            headers=headers,
            json={
                "project_id": project_id,
                "model_id": model_id,
                "name": "Recall too high demo check",
                "type": "performance_threshold",
                "metric": "recall",
                "operator": "greater_than",
                "threshold": 0.1,
                "severity": "medium",
            },
        )
        assert alert_rule.status_code == 201, alert_rule.text
        alerts = client.post(f"/api/v1/alerts/run-checks?project_id={project_id}", headers=headers)
        assert alerts.status_code == 200, alerts.text
        assert len(alerts.json()["created"]) == 1
        notifications = client.get("/api/v1/notifications", headers=headers)
        assert notifications.status_code == 200, notifications.text
        assert notifications.json()["unread"] >= 1
        alert_id = alerts.json()["created"][0]["_id"]
        assert client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=headers).status_code == 200
        assert client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=headers).status_code == 200

        job = client.post(
            "/api/v1/jobs",
            headers=headers,
            json={"type": "alerts", "project_id": project_id, "params": {"include_defaults": True}},
        )
        assert job.status_code == 202, job.text
        jobs = client.get(f"/api/v1/jobs?project_id={project_id}", headers=headers)
        assert jobs.status_code == 200, jobs.text
        assert jobs.json()["items"][0]["status"] in {"queued", "running", "completed", "failed"}

        export = client.post(
            "/api/v1/exports",
            headers=headers,
            json={"filters": {"project_id": project_id}, "format": "csv"},
        )
        assert export.status_code == 201, export.text
        assert export.json()["record_count"] == 1
        assert export.json()["redact_pii"] is True
        download = client.get(f"/api/v1/exports/{export.json()['_id']}/download", headers=headers)
        assert download.status_code == 200, download.text
        assert "prediction_id" in download.text
        assert "student_001" not in download.text

        migration = client.post("/api/v1/security/migrate-sensitive-data", headers=headers)
        assert migration.status_code == 200, migration.text
        assert migration.json()["status"] == "completed"
