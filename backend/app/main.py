from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
import secrets
import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.ai import (
    DEFAULT_CONNECTIVITY_PROMPT,
    DEFAULT_OPENAI_MODEL,
    OpenAIConfigurationError,
    OpenAIRequestError,
    OpenAIService,
)
from app.database import (
    get_board_for_user,
    initialize_database,
    save_board_for_user,
)

APP_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = APP_ROOT / "frontend_dist"
LOCAL_FRONTEND_OUT_DIR = APP_ROOT.parent / "frontend" / "out"
FALLBACK_STATIC_DIR = APP_ROOT / "static"
DEFAULT_DB_PATH = APP_ROOT / "data" / "pm.db"
SESSION_COOKIE_NAME = "pm_session"
SESSION_TTL_SECONDS = 60 * 60 * 12
MVP_USERNAME = "user"
MVP_PASSWORD = "password"


@dataclass
class SessionRecord:
    username: str
    expires_at: float


class LoginRequest(BaseModel):
    username: str
    password: str


class CardPayload(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    details: str = ""


class ColumnPayload(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cardIds: list[str] = Field(default_factory=list)


class BoardPayload(BaseModel):
    version: int = Field(default=1, ge=1)
    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]


class AIConnectivityPayload(BaseModel):
    prompt: str = Field(default=DEFAULT_CONNECTIVITY_PROMPT, min_length=1)


SESSION_STORE: dict[str, SessionRecord] = {}


def resolve_frontend_dir() -> Path:
    for candidate in (FRONTEND_DIST_DIR, LOCAL_FRONTEND_OUT_DIR, FALLBACK_STATIC_DIR):
        if (candidate / "index.html").exists():
            return candidate
    return FALLBACK_STATIC_DIR


def clear_sessions() -> None:
    SESSION_STORE.clear()


def _create_session(username: str) -> str:
    session_id = secrets.token_urlsafe(32)
    SESSION_STORE[session_id] = SessionRecord(
        username=username,
        expires_at=time.time() + SESSION_TTL_SECONDS,
    )
    return session_id


def _get_authenticated_user(request: Request) -> str | None:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None

    session = SESSION_STORE.get(session_id)
    if not session:
        return None

    if session.expires_at <= time.time():
        SESSION_STORE.pop(session_id, None)
        return None

    return session.username


def require_authenticated_user(request: Request) -> str:
    username = _get_authenticated_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return username


def get_openai_service() -> OpenAIService:
    return OpenAIService(model=DEFAULT_OPENAI_MODEL)


def _validate_board_payload(board: BoardPayload) -> dict:
    column_ids = [column.id for column in board.columns]
    if len(set(column_ids)) != len(column_ids):
        raise HTTPException(status_code=400, detail="Column ids must be unique.")

    card_keys = set(board.cards.keys())
    for key, card in board.cards.items():
        if key != card.id:
            raise HTTPException(
                status_code=400,
                detail=f"Card key '{key}' does not match card.id '{card.id}'.",
            )

    assigned_card_ids: list[str] = []
    for column in board.columns:
        assigned_card_ids.extend(column.cardIds)

    unknown_ids = sorted({card_id for card_id in assigned_card_ids if card_id not in card_keys})
    if unknown_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown card ids in columns: {', '.join(unknown_ids)}",
        )

    if len(set(assigned_card_ids)) != len(assigned_card_ids):
        raise HTTPException(
            status_code=400,
            detail="A card can only appear in one column once.",
        )

    missing_ids = sorted(card_keys.difference(assigned_card_ids))
    if missing_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Cards missing from columns: {', '.join(missing_ids)}",
        )

    return board.model_dump()


def create_app(frontend_dir: Path | None = None, db_path: Path | None = None) -> FastAPI:
    resolved_db_path = db_path or DEFAULT_DB_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(resolved_db_path, seed_username=MVP_USERNAME)
        yield

    app = FastAPI(title="Project Management MVP", lifespan=lifespan)
    app.state.db_path = resolved_db_path

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/auth/session")
    def get_session(request: Request) -> dict[str, str | bool | None]:
        username = _get_authenticated_user(request)
        return {
            "authenticated": username is not None,
            "username": username,
        }

    @app.post("/api/auth/login")
    def login(payload: LoginRequest) -> JSONResponse:
        if payload.username != MVP_USERNAME or payload.password != MVP_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        session_id = _create_session(payload.username)
        response = JSONResponse({"username": payload.username})
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            samesite="lax",
            max_age=SESSION_TTL_SECONDS,
            secure=False,
            path="/",
        )
        return response

    @app.post("/api/auth/logout")
    def logout(request: Request) -> JSONResponse:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id:
            SESSION_STORE.pop(session_id, None)

        response = JSONResponse({"ok": True})
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")
        return response

    @app.get("/api/auth/me")
    def me(username: str = Depends(require_authenticated_user)) -> dict[str, str]:
        return {"username": username}

    @app.get("/api/board")
    def get_board(username: str = Depends(require_authenticated_user)) -> dict:
        return get_board_for_user(app.state.db_path, username)

    @app.put("/api/board")
    def save_board(
        payload: BoardPayload,
        username: str = Depends(require_authenticated_user),
    ) -> dict:
        board = _validate_board_payload(payload)
        return save_board_for_user(app.state.db_path, username, board)

    @app.post("/api/ai/connectivity")
    def ai_connectivity(
        payload: AIConnectivityPayload,
        _username: str = Depends(require_authenticated_user),
    ) -> dict[str, str]:
        try:
            service = get_openai_service()
        except OpenAIConfigurationError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        try:
            output = service.connectivity_check(payload.prompt)
        except OpenAIRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return {"model": service.model, "output": output}

    app.mount(
        "/",
        StaticFiles(directory=frontend_dir or resolve_frontend_dir(), html=True),
        name="frontend",
    )
    return app


app = create_app()
