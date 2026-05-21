import time

from fastapi.testclient import TestClient

from app.main import app


def test_upload_text_document():
    client = TestClient(app)
    response = client.post(
        "/api/v1/documents",
        files={"file": ("demo.txt", b"first paragraph\nsecond paragraph", "text/plain")},
        data={"parser_mode": "plain"},
    )
    assert response.status_code == 200
    payload = response.json()

    task = None
    for _ in range(30):
        task_response = client.get(f"/api/v1/tasks/{payload['task_id']}")
        assert task_response.status_code == 200
        task = task_response.json()
        if task["status"] in {"done", "failed"}:
            break
        time.sleep(0.1)

    assert task is not None
    assert task["status"] == "done", task

    result_response = client.get(f"/api/v1/documents/{payload['doc_id']}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["doc_id"] == payload["doc_id"]
    assert "first paragraph" in result["text"]
    assert "second paragraph" in result["markdown"]
    assert result["sections"]

    markdown_response = client.get(f"/api/v1/documents/{payload['doc_id']}/markdown")
    assert markdown_response.status_code == 200
    assert "first paragraph" in markdown_response.text
