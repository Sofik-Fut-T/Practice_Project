"""
data/storage.py — авторизація та збереження історії (JSON)
"""
import json
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "users.json"


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load() -> dict:
    if not DB_PATH.exists():
        DB_PATH.write_text("{}", encoding="utf-8")
    try:
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict):
    DB_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _new_user(pw_hash: str) -> dict:
    return {
        "password": pw_hash,
        "history": {
            "files":     [],   # останні 3 файли
            "modes":     [],   # останні 3 режими
            "embedded":  [],   # останні 3 вкладені повідомлення
            "extracted": [],   # останні 3 витягнуті повідомлення
        },
        "last_session": None,
    }


# ── Авторизація ───────────────────────────────────────────

def register(username: str, password: str) -> bool:
    """False якщо користувач вже існує."""
    data = _load()
    if username in data:
        return False
    data[username] = _new_user(_hash(password))
    _save(data)
    return True


def login(username: str, password: str) -> bool:
    data = _load()
    u = data.get(username)
    return bool(u and u["password"] == _hash(password))


# ── Збереження历toriї ──────────────────────────────────────

def _push(lst: list, val, n: int = 3) -> list:
    lst = [x for x in lst if x != val]
    lst.insert(0, val)
    return lst[:n]


def save_file(username: str, path: str):
    data = _load()
    data[username]["history"]["files"] = _push(
        data[username]["history"]["files"], path)
    _save(data)


def save_mode(username: str, mode: dict):
    data = _load()
    modes = [m for m in data[username]["history"]["modes"] if m != mode]
    modes.insert(0, mode)
    data[username]["history"]["modes"] = modes[:3]
    _save(data)


def save_embedded(username: str, msg: str):
    data = _load()
    data[username]["history"]["embedded"] = _push(
        data[username]["history"]["embedded"], msg)
    _save(data)


def save_extracted(username: str, msg: str):
    data = _load()
    data[username]["history"]["extracted"] = _push(
        data[username]["history"]["extracted"], msg)
    _save(data)


def save_session(username: str, session: dict):
    data = _load()
    data[username]["last_session"] = session
    _save(data)


def get_history(username: str) -> dict:
    data = _load()
    return data.get(username, {}).get(
        "history",
        {"files": [], "modes": [], "embedded": [], "extracted": []}
    )


def get_session(username: str) -> dict | None:
    data = _load()
    return data.get(username, {}).get("last_session")
