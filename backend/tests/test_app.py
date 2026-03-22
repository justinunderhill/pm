from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import create_app, resolve_frontend_dir


def test_root_serves_kanban_frontend(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Kanban Studio" in response.text


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_serves_frontend_export_assets(tmp_path: Path, db_path: Path) -> None:
    (tmp_path / "_next" / "static").mkdir(parents=True)
    (tmp_path / "_next" / "static" / "app.js").write_text(
        "console.log('ok')",
        encoding="utf-8",
    )
    (tmp_path / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )

    with TestClient(create_app(frontend_dir=tmp_path, db_path=db_path)) as test_client:
        root = test_client.get("/")
        asset = test_client.get("/_next/static/app.js")

    assert root.status_code == 200
    assert "Kanban Studio" in root.text
    assert asset.status_code == 200
    assert "console.log('ok')" in asset.text


def test_resolve_frontend_dir_priority(tmp_path: Path, monkeypatch) -> None:
    frontend_dist = tmp_path / "frontend_dist"
    local_frontend_out = tmp_path / "frontend_out"
    fallback_static = tmp_path / "fallback_static"

    frontend_dist.mkdir()
    local_frontend_out.mkdir()
    fallback_static.mkdir()

    (local_frontend_out / "index.html").write_text("local", encoding="utf-8")
    (fallback_static / "index.html").write_text("fallback", encoding="utf-8")

    monkeypatch.setattr(main_module, "FRONTEND_DIST_DIR", frontend_dist)
    monkeypatch.setattr(main_module, "LOCAL_FRONTEND_OUT_DIR", local_frontend_out)
    monkeypatch.setattr(main_module, "FALLBACK_STATIC_DIR", fallback_static)

    assert resolve_frontend_dir() == local_frontend_out

    (frontend_dist / "index.html").write_text("dist", encoding="utf-8")
    assert resolve_frontend_dir() == frontend_dist
