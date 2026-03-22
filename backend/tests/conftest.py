from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import clear_sessions, create_app


@pytest.fixture(autouse=True)
def reset_sessions() -> None:
    clear_sessions()


@pytest.fixture
def frontend_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "frontend"
    directory.mkdir()
    (directory / "index.html").write_text(
        "<!doctype html><html><body><h1>Kanban Studio</h1></body></html>",
        encoding="utf-8",
    )
    return directory


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "data" / "pm.db"


@pytest.fixture
def client(frontend_dir: Path, db_path: Path):
    app = create_app(frontend_dir=frontend_dir, db_path=db_path)
    with TestClient(app) as test_client:
        yield test_client
