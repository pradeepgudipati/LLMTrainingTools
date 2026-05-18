import io
import os


def test_validate_dataset_api_returns_report(tmp_path):
    os.environ["LLMTOOLS_DB_PATH"] = str(tmp_path / "app.db")
    os.environ["FLASK_SECRET_KEY"] = "test-secret"

    from src.app import app, create_app

    create_app()
    client = app.test_client()

    response = client.post(
        "/api/validate_dataset",
        data={
            "file": (
                io.BytesIO(b'{"messages":[{"role":"user","content":"Hi"},{"role":"assistant","content":""}]}\n'),
                "bad.jsonl",
            )
        },
        content_type="multipart/form-data",
    )

    payload = response.get_json()
    assert response.status_code == 422
    assert payload["status"] == "invalid"
    assert payload["report"]["error_count"] == 1
    assert payload["report"]["issues"][0]["message"] == "messages[1].content is empty."
