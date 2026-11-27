"""
Anh Minh Translate — Lớp xử lý logic, bảo mật, đồng bộ Supabase/SQLite, dịch thuật & TTS
Tác giả: Mai Văn Minh — Sinh viên năm 4, Chuyên ngành Đóng tàu, СПбГМТУ (Xanh-Petecbua)
"""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import base64
import csv
import hashlib
import hmac
import html
import io
import json
import os
import random
import re
import secrets
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    import docx as python_docx
except Exception:
    python_docx = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:
    Fernet = None
    InvalidToken = Exception

from data import (
    AUTHOR_NOTIFICATION_EMAIL,
    DIRECTION_OPTIONS,
    ENC_API_KEY_PREFIX,
    MAX_AI_CACHE_SIZE,
    MAX_HISTORY_ITEMS,
    MAX_MEM_CACHE_SIZE,
    PREFERRED_GEMINI_MODELS,
    PREFERRED_GEMINI_MODELS_FAST,
    PREFERRED_GEMINI_MODELS_QUALITY,
    RUSSIAN_SLANG_DICT,
    SESSION_TOKEN_TTL_DAYS,
    SQLITE_DB_PATH,
)


def _get_secret_or_env(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            val = str(st.secrets[key]).strip()
            if val:
                return val
    except Exception:
        pass
    return os.environ.get(key, default).strip()


DEFAULT_AUTHOR_PASSWORD = _get_secret_or_env("AUTHOR_ADMIN_PASSWORD", "")
DATA_ENCRYPTION_KEY = _get_secret_or_env("DATA_ENCRYPTION_KEY", "")
SESSION_SIGNING_SECRET = _get_secret_or_env(
    "SESSION_SIGNING_SECRET",
    f"am_session_{DEFAULT_AUTHOR_PASSWORD or DATA_ENCRYPTION_KEY or 'local_dev'}_v12",
)
SUPABASE_URL = _get_secret_or_env("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = _get_secret_or_env("SUPABASE_KEY", "")
FORMSPREE_ENDPOINT = _get_secret_or_env("FORMSPREE_ENDPOINT", "")
SHARED_DEMO_GEMINI_KEY = re.sub(r'[\s"\'\`]+', "", _get_secret_or_env("SHARED_DEMO_GEMINI_KEY", ""))
try:
    DAILY_DEMO_LIMIT = max(0, int(_get_secret_or_env("DAILY_DEMO_LIMIT", "12") or "12"))
except Exception:
    DAILY_DEMO_LIMIT = 12

SESSION_TOKEN_TTL_DAYS = 30
ENC_API_KEY_PREFIX = "enc::"


def clean_api_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    return re.sub(r'[\s"\'\`]+', "", raw_key.strip())


def verify_author_password(input_pwd: str) -> bool:
    if not input_pwd or not DEFAULT_AUTHOR_PASSWORD:
        return False
    return hmac.compare_digest(input_pwd.strip(), DEFAULT_AUTHOR_PASSWORD)


def get_demo_usage_today() -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")
    raw = st.session_state.get("demo_usage")
    if isinstance(raw, dict) and str(raw.get("date", "")) == today:
        try:
            cnt = max(0, int(raw.get("count", 0)))
        except Exception:
            cnt = 0
        normalized = {"date": today, "count": cnt}
    else:
        normalized = {"date": today, "count": 0}
        st.session_state["demo_usage"] = normalized
    return normalized


def get_remaining_demo_quota() -> int:
    if not SHARED_DEMO_GEMINI_KEY or DAILY_DEMO_LIMIT <= 0:
        return 0
    usage = get_demo_usage_today()
    return max(0, DAILY_DEMO_LIMIT - int(usage.get("count", 0)))


def consume_demo_quota() -> None:
    usage = get_demo_usage_today()
    usage["count"] = int(usage.get("count", 0)) + 1
    st.session_state["demo_usage"] = usage
    sync_current_account_to_db()


def _normalize_username(raw: str) -> str:
    return re.sub(r"[^a-z0-9_.@-]", "", raw.strip().lower())


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt_val = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_val.encode("utf-8"), 120000)
    return f"{salt_val}${dk.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_val, hex_hash = stored_hash.split("$", 1)
        expected = _hash_password(password, salt_val).split("$", 1)[1]
        return hmac.compare_digest(hex_hash, expected)
    except Exception:
        return False


def _get_fernet() -> Optional[Any]:
    if Fernet is None or not DATA_ENCRYPTION_KEY:
        return None
    try:
        return Fernet(DATA_ENCRYPTION_KEY.encode("utf-8"))
    except Exception:
        return None


def encrypt_api_key(raw_key: str) -> str:
    """Mã hóa Gemini API Key bằng Fernet (gắn tiền tố enc::) trước khi lưu DB."""
    if not raw_key:
        return ""
    val = str(raw_key).strip()
    if val.startswith(ENC_API_KEY_PREFIX):
        return val
    cleaned = clean_api_key(val)
    if not cleaned:
        return ""
    fernet = _get_fernet()
    if fernet is None:
        return cleaned
    try:
        token = fernet.encrypt(cleaned.encode("utf-8")).decode("utf-8")
        return f"{ENC_API_KEY_PREFIX}{token}"
    except Exception:
        return cleaned


def decrypt_api_key(stored_key: str) -> str:
    """Giải mã Gemini API Key đã mã hóa (tương thích ngược với khóa cũ dạng văn bản thuần)."""
    if not stored_key:
        return ""
    val = str(stored_key).strip()
    if not val.startswith(ENC_API_KEY_PREFIX):
        return clean_api_key(val)
    fernet = _get_fernet()
    if fernet is None:
        return ""
    try:
        decrypted = fernet.decrypt(val[len(ENC_API_KEY_PREFIX):].encode("utf-8")).decode("utf-8")
        return clean_api_key(decrypted)
    except (InvalidToken, Exception):
        return ""


def _set_supabase_error(msg: str) -> None:
    try:
        st.session_state["last_supabase_error"] = msg
    except Exception:
        pass


def _format_supabase_error(op: str, exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="ignore").strip()
        except Exception:
            pass
        detail = f" — {body[:200]}" if body else ""
        return f"Supabase ({op}) HTTP {exc.code}: {exc.reason}{detail}"
    return f"Supabase ({op}) lỗi kết nối: {exc}"


def _get_browser_cookie(name: str) -> str:
    try:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            return urllib.parse.unquote(str(st.context.cookies.get(name, "")).strip())
    except Exception:
        pass
    return ""


def create_session_token(username: str, token_version: int = 1, ttl_days: int = SESSION_TOKEN_TTL_DAYS) -> str:
    """Tạo token phiên đã ký HMAC-SHA256 kèm hạn dùng (exp) và phiên bản (tv) để giữ đăng nhập an toàn."""
    token_obj = {
        "u": username,
        "exp": int(time.time()) + int(ttl_days) * 86400,
        "tv": int(token_version),
    }
    raw_json = json.dumps(token_obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    p_b64 = base64.urlsafe_b64encode(raw_json).decode("ascii").rstrip("=")
    sig = hmac.new(SESSION_SIGNING_SECRET.encode("utf-8"), p_b64.encode("ascii"), hashlib.sha256).hexdigest()[:32]
    return f"{p_b64}.{sig}"


def verify_session_token(token: str) -> Optional[Tuple[str, int]]:
    """Xác thực chữ ký HMAC-SHA256 và hạn dùng (exp); trả về (username, token_version) hoặc None."""
    if not token or "." not in token:
        return None
    try:
        p_b64, sig = token.split(".", 1)
        expected = hmac.new(SESSION_SIGNING_SECRET.encode("utf-8"), p_b64.encode("ascii"), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        pad = "=" * (-len(p_b64) % 4)
        data = json.loads(base64.urlsafe_b64decode((p_b64 + pad).encode("ascii")).decode("utf-8"))
        if not isinstance(data, dict):
            return None
        uname = str(data.get("u", "")).strip()
        exp = int(data.get("exp", 0))
        tv = int(data.get("tv", 1))
        if not uname or exp < int(time.time()):
            return None
        return uname, tv
    except Exception:
        return None


def _is_cloud_sync_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


@st.cache_resource
def _init_sqlite_db() -> bool:
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS am_users (
                    username TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        return True
    except Exception:
        return False


def _supabase_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    if SUPABASE_KEY.startswith("eyJ"):
        h["Authorization"] = f"Bearer {SUPABASE_KEY}"
    if extra:
        h.update(extra)
    return h


def db_get_user(username: str) -> Optional[Dict[str, Any]]:
    uname = _normalize_username(username)
    if not uname:
        return None

    # 1. Ưu tiên đọc từ Supabase Cloud (đồng bộ đa thiết bị)
    if _is_cloud_sync_enabled():
        try:
            url = f"{SUPABASE_URL}/rest/v1/am_users?username=eq.{urllib.parse.quote(uname)}&select=payload"
            req = urllib.request.Request(url, headers=_supabase_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                rows = json.loads(resp.read().decode("utf-8"))
                _set_supabase_error("")
                if isinstance(rows, list) and rows:
                    payload = rows[0].get("payload")
                    if isinstance(payload, str):
                        return json.loads(payload)
                    if isinstance(payload, dict):
                        return payload
        except Exception as exc:
            _set_supabase_error(_format_supabase_error("db_get_user", exc))

    # 2. Đọc từ SQLite cục bộ
    _init_sqlite_db()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            row = conn.execute("SELECT payload FROM am_users WHERE username = ?", (uname,)).fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return None


def db_save_user(username: str, payload: Dict[str, Any]) -> bool:
    uname = _normalize_username(username)
    if not uname:
        return False

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload_to_save = dict(payload)
    payload_to_save["updated_at"] = now_iso
    if payload_to_save.get("api_key"):
        payload_to_save["api_key"] = encrypt_api_key(str(payload_to_save["api_key"]))
    payload_str = json.dumps(payload_to_save, ensure_ascii=False)

    # 1. Luôn lưu SQLite cục bộ trước (nhanh, an toàn)
    _init_sqlite_db()
    local_ok = False
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.execute(
                "INSERT INTO am_users (username, payload, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(username) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                (uname, payload_str, now_iso),
            )
            conn.commit()
            local_ok = True
    except Exception:
        pass

    # 2. Đồng bộ lên Supabase Cloud (nếu đã cấu hình Secrets)
    cloud_ok = False
    if _is_cloud_sync_enabled():
        try:
            url = f"{SUPABASE_URL}/rest/v1/am_users?on_conflict=username"
            body = json.dumps({"username": uname, "payload": payload_to_save, "updated_at": now_iso}, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers=_supabase_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201, 204):
                    cloud_ok = True
                    _set_supabase_error("")
                else:
                    _set_supabase_error(f"Supabase (db_save_user) HTTP {resp.status}")
        except Exception as exc:
            _set_supabase_error(_format_supabase_error("db_save_user", exc))

    return cloud_ok or local_ok


def _extract_user_summary(uname: str, payload: Dict[str, Any], updated_at: str) -> Dict[str, str]:
    prof = payload.get("profile") or {}
    raw_api_key = str(payload.get("api_key", "")).strip()
    has_key = bool(raw_api_key and (raw_api_key.startswith(ENC_API_KEY_PREFIX) or clean_api_key(raw_api_key)))
    return {
        "username": uname,
        "full_name": str(prof.get("full_name", "") or "—"),
        "student_year": str(prof.get("student_year", "") or "—"),
        "university": str(prof.get("university", "") or "—"),
        "has_api_key": "Có" if has_key else "Chưa",
        "vocab_count": str(len(payload.get("vocab_notebook") or [])),
        "history_count": str(len(payload.get("translation_history") or [])),
        "login_count": str(payload.get("login_count", 1)),
        "last_login": str(payload.get("last_login_at") or updated_at)[:19],
        "created_at": str(payload.get("created_at") or updated_at)[:19],
    }


def db_list_all_users() -> List[Dict[str, str]]:
    """Dành cho Chế độ Tác giả xem thông tin tài khoản và hoạt động đăng nhập (bảo vệ mật khẩu & API Key)."""
    users: List[Dict[str, str]] = []
    if _is_cloud_sync_enabled():
        try:
            url = f"{SUPABASE_URL}/rest/v1/am_users?select=username,payload,updated_at&order=updated_at.desc&limit=200"
            req = urllib.request.Request(url, headers=_supabase_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                rows = json.loads(resp.read().decode("utf-8"))
                _set_supabase_error("")
                for r in rows:
                    uname = str(r.get("username", ""))
                    if not uname:
                        continue
                    payload = r.get("payload")
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    if isinstance(payload, dict) and payload.get("password_hash"):
                        users.append(_extract_user_summary(uname, payload, str(r.get("updated_at", ""))))
                return users
        except Exception as exc:
            _set_supabase_error(_format_supabase_error("db_list_all_users", exc))

    _init_sqlite_db()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            rows = conn.execute("SELECT username, payload, updated_at FROM am_users ORDER BY updated_at DESC LIMIT 200").fetchall()
            for uname, raw_p, upd in rows:
                if not uname:
                    continue
                payload = json.loads(raw_p) if raw_p else {}
                if isinstance(payload, dict) and payload.get("password_hash"):
                    users.append(_extract_user_summary(str(uname), payload, str(upd)))
    except Exception:
        pass
    return users


def export_users_to_csv(users: List[Dict[str, str]]) -> bytes:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Username", "Ho_va_Ten", "Nam_hoc", "Truong", "So_lan_dang_nhap", "Lan_cuoi_dang_nhap", "So_tu_vung", "So_luot_dich", "Da_cai_API_Key"])
    for u in users:
        w.writerow([u["username"], u["full_name"], u["student_year"], u["university"], u["login_count"], u["last_login"], u["vocab_count"], u["history_count"], u["has_api_key"]])
    return ("\ufeff" + out.getvalue()).encode("utf-8")


def sync_current_account_to_db() -> None:
    """Lưu đồng bộ tức thì toàn bộ trạng thái tài khoản hiện tại mà không cần gọi db_get_user() thừa."""
    uname = st.session_state.get("auth_username", "")
    if not uname:
        return
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "password_hash": st.session_state.get("auth_password_hash", ""),
        "created_at": st.session_state.get("auth_created_at") or now_str,
        "last_login_at": st.session_state.get("auth_last_login_at") or now_str,
        "login_count": int(st.session_state.get("auth_login_count", 1)),
        "token_version": int(st.session_state.get("auth_token_version", 1)),
        "profile": {
            "full_name": st.session_state.get("confirmed_user_name", ""),
            "student_year": st.session_state.get("confirmed_user_year", "Sinh viên Năm 4"),
            "university": st.session_state.get("confirmed_user_uni", ""),
        },
        "api_key": clean_api_key(st.session_state.get("saved_gemini_api_key", "")),
        "theme_mode": st.session_state.get("theme_mode", "light"),
        "is_author_admin": bool(st.session_state.get("is_author_admin", False)),
        "demo_usage": get_demo_usage_today(),
        "vocab_notebook": st.session_state.get("saved_vocab_notebook", [])[:500],
        "translation_history": st.session_state.get("translation_history", [])[:MAX_HISTORY_ITEMS],
    }
    db_save_user(uname, payload)


def apply_user_payload_to_session(username: str, payload: Dict[str, Any]) -> None:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tv = int(payload.get("token_version", 1))
    st.session_state["auth_username"] = username
    st.session_state["auth_password_hash"] = payload.get("password_hash", "")
    st.session_state["auth_created_at"] = str(payload.get("created_at") or now_str)
    st.session_state["auth_last_login_at"] = str(payload.get("last_login_at") or now_str)
    st.session_state["auth_login_count"] = int(payload.get("login_count", 1))
    st.session_state["auth_token_version"] = tv
    prof = payload.get("profile") or {}
    st.session_state["confirmed_user_name"] = prof.get("full_name", "")
    st.session_state["confirmed_user_year"] = prof.get("student_year", "Sinh viên Năm 4")
    st.session_state["confirmed_user_uni"] = prof.get("university", "")
    st.session_state["saved_gemini_api_key"] = decrypt_api_key(str(payload.get("api_key", "")))
    today = datetime.now().strftime("%Y-%m-%d")
    raw_demo = payload.get("demo_usage")
    if isinstance(raw_demo, dict) and str(raw_demo.get("date", "")) == today:
        try:
            demo_cnt = max(0, int(raw_demo.get("count", 0)))
        except Exception:
            demo_cnt = 0
        st.session_state["demo_usage"] = {"date": today, "count": demo_cnt}
    else:
        st.session_state["demo_usage"] = {"date": today, "count": 0}
    st.session_state["theme_mode"] = payload.get("theme_mode", "light") if payload.get("theme_mode") in ("light", "dark") else "light"
    if payload.get("is_author_admin") and DEFAULT_AUTHOR_PASSWORD:
        st.session_state["is_author_admin"] = True
        try:
            if verify_admin_token(_get_browser_cookie("am_atok")):
                if "a" in st.query_params:
                    del st.query_params["a"]
            else:
                st.query_params["a"] = create_admin_token()
        except Exception:
            pass
    st.session_state["saved_vocab_notebook"] = payload.get("vocab_notebook") if isinstance(payload.get("vocab_notebook"), list) else []
    st.session_state["translation_history"] = payload.get("translation_history") if isinstance(payload.get("translation_history"), list) else []
    try:
        cookie_verified = verify_session_token(_get_browser_cookie("am_rtok"))
        if cookie_verified == (username, tv):
            if "s" in st.query_params:
                del st.query_params["s"]
        else:
            st.query_params["s"] = create_session_token(username, tv)
    except Exception:
        pass


def create_admin_token() -> str:
    """Tạo token tác giả đã ký HMAC (không chứa mật khẩu rõ)."""
    return hmac.new(SESSION_SIGNING_SECRET.encode("utf-8"), b"author_admin_persistent_v1", hashlib.sha256).hexdigest()[:32]


def verify_admin_token(tok: str) -> bool:
    if not tok or not DEFAULT_AUTHOR_PASSWORD:
        return False
    return hmac.compare_digest(tok.strip(), create_admin_token())


def send_user_notification_email(full_name: str, student_year: str, university: str) -> Tuple[bool, str]:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    gmail_app_pwd = _get_secret_or_env("GMAIL_APP_PASSWORD", "")
    if gmail_app_pwd:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Anh Minh Translate] Sinh viên mới: {full_name} ({university})"
            msg["From"] = AUTHOR_NOTIFICATION_EMAIL
            msg["To"] = AUTHOR_NOTIFICATION_EMAIL
            html_body = (
                f"<div style='font-family:sans-serif;padding:16px;'>"
                f"<h3>Thông báo sinh viên đăng ký Anh Minh Translate</h3>"
                f"<p><b>Họ và tên:</b> {html.escape(str(full_name), quote=True)}</p>"
                f"<p><b>Năm học:</b> {html.escape(str(student_year), quote=True)}</p>"
                f"<p><b>Trường:</b> {html.escape(str(university), quote=True)}</p>"
                f"<p><b>Thời gian:</b> {now_str}</p></div>"
            )
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8) as server:
                server.login(AUTHOR_NOTIFICATION_EMAIL, gmail_app_pwd)
                server.sendmail(AUTHOR_NOTIFICATION_EMAIL, [AUTHOR_NOTIFICATION_EMAIL], msg.as_string())
            return True, "Gmail SMTP"
        except Exception:
            pass

    headers_json = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 Chrome/126.0.0.0 Safari/537.36",
    }
    if FORMSPREE_ENDPOINT:
        try:
            req = urllib.request.Request(
                FORMSPREE_ENDPOINT,
                data=json.dumps({"Họ và tên": full_name, "Năm học": student_year, "Trường": university, "Thời gian": now_str}).encode("utf-8"),
                headers=headers_json, method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True, "Formspree"
        except Exception:
            pass
    return False, "DB Saved"


def resolve_effective_direction(source_text: str, selected_direction: str) -> str:
    """
    Xác định chính xác chiều dịch thực tế để KHÔNG BAO GIỜ bị lỗi nhập tiếng Việt lại ra tiếng Việt
    hay nhập tiếng Nga lại ra tiếng Nga.
    """
    if selected_direction == DIRECTION_OPTIONS[3]:  # Đối chiếu 3 ngôn ngữ
        return selected_direction

    has_cyr = bool(re.search(r"[а-яА-ЯёЁ]", source_text))
    has_latin = bool(re.search(r"[a-zA-ZăâđêôơưĂÂĐÊÔƠƯàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", source_text))

    if selected_direction == DIRECTION_OPTIONS[0]:  # Tự động (Nga ↔ Việt)
        return DIRECTION_OPTIONS[1] if has_cyr else DIRECTION_OPTIONS[2]

    if selected_direction == DIRECTION_OPTIONS[1]:  # Tiếng Nga → Tiếng Việt
        if not has_cyr and has_latin:
            return DIRECTION_OPTIONS[2]  # Người dùng gõ tiếng Việt (có dấu hoặc không dấu) -> dịch sang Nga
        return DIRECTION_OPTIONS[1]

    if selected_direction == DIRECTION_OPTIONS[2]:  # Tiếng Việt → Tiếng Nga
        if has_cyr and not has_latin:
            return DIRECTION_OPTIONS[1]  # Người dùng dán thuần tiếng Nga -> dịch sang Việt
        return DIRECTION_OPTIONS[2]

    return selected_direction


def classify_input_type(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return "word"
    lines = [ln for ln in cleaned.splitlines() if ln.strip()]
    words = cleaned.split()
    sentence_ends = len(re.findall(r"[.!?…]+", cleaned))
    has_cyr = bool(re.search(r"[а-яА-ЯёЁ]", cleaned))
    word_limit = 3 if has_cyr else 4

    if len(lines) == 1 and len(words) <= word_limit and sentence_ends == 0:
        return "word"
    if len(lines) <= 2 and len(words) <= 25 and sentence_ends <= 1:
        return "sentence"
    return "paragraph"


def detect_slang_in_text(text: str) -> List[Dict[str, str]]:
    if not text:
        return []
    text_lower = text.lower()
    detected = []
    seen = set()
    for item in RUSSIAN_SLANG_DICT:
        w = item["word"]
        base_stem = w[:-1] if (len(w) >= 4 and w[-1] in "аяоеыи") or len(w) > 4 else w
        if re.search(rf"\b{re.escape(base_stem)}[а-яё]*\b", text_lower) and w not in seen:
            detected.append(item)
            seen.add(w)
    return detected


def chunk_text_smart(text: str, max_chars: int = 1100) -> List[str]:
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return [cleaned] if cleaned else []

    chunks: List[str] = []
    current = ""
    for para in cleaned.split("\n"):
        para_s = para.strip()
        if not para_s:
            if current:
                current += "\n"
            continue
        if len(current) + len(para_s) + 1 <= max_chars:
            current = f"{current}\n{para_s}" if current else para_s
        else:
            if current:
                chunks.append(current.strip())
                current = ""
            if len(para_s) <= max_chars:
                current = para_s
            else:
                for sent in re.split(r"(?<=[.!?…])\s+", para_s):
                    if len(current) + len(sent) + 1 <= max_chars:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current.strip())
                        if len(sent) <= max_chars:
                            current = sent
                        else:
                            for idx in range(0, len(sent), max_chars):
                                chunks.append(sent[idx : idx + max_chars])
                            current = ""
    if current.strip():
        chunks.append(current.strip())
    return chunks


@st.cache_data(ttl=3600, show_spinner=False)
def generate_tts_audio(text: str, lang_code: str, slow: bool = False) -> Optional[bytes]:
    cleaned_text = text.strip()
    if not cleaned_text or gTTS is None:
        return None
    try:
        tts = gTTS(text=cleaned_text[:650], lang=lang_code, slow=slow)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def discover_working_gemini_models(api_key: str) -> Tuple[List[str], Optional[str]]:
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return [], "Chưa có API Key."

    discovered: List[str] = []
    for api_ver in ("v1beta", "v1"):
        try:
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={urllib.parse.quote(clean_k)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        short = m.get("name", "").replace("models/", "")
                        if "gemini" in short and "embedding" not in short and "tts" not in short and "image" not in short:
                            if short not in discovered:
                                discovered.append(short)
                if discovered:
                    break
        except urllib.error.HTTPError as http_err:
            err_body = ""
            try:
                err_body = http_err.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            if "API_KEY_INVALID" in err_body or http_err.code == 400:
                return [], "Gemini API Key không hợp lệ hoặc đã bị thu hồi."
            if "location is not supported" in err_body.lower():
                return [], "Vị trí máy chủ hiện tại không được Gemini API hỗ trợ."
        except Exception:
            pass

    if discovered:
        ordered = [p for p in PREFERRED_GEMINI_MODELS if p in discovered]
        flash_others = [d for d in discovered if "flash" in d and d not in ordered]
        rest = [d for d in discovered if d not in ordered and d not in flash_others]
        return ordered + flash_others + rest, None

    return list(PREFERRED_GEMINI_MODELS), None


def _try_multi_endpoint_translate(cleaned: str, src: str, tgt: str) -> Optional[str]:
    headers_form = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    }
    post_body = urllib.parse.urlencode({"sl": src, "tl": tgt, "q": cleaned}).encode("utf-8")

    for url in (
        "https://translate.googleapis.com/translate_a/single?client=gtx&dt=t",
        "https://translate.google.com/translate_a/single?client=at&dt=t&dj=1",
    ):
        try:
            req = urllib.request.Request(url, data=post_body, headers=headers_form, method="POST")
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and data and isinstance(data[0], list):
                    chunks = [c[0] for c in data[0] if c and c[0]]
                    if chunks:
                        return "".join(chunks)
                if isinstance(data, dict) and data.get("sentences"):
                    chunks = [s.get("trans", "") for s in data["sentences"] if s.get("trans")]
                    if chunks:
                        return "".join(chunks)
        except Exception:
            pass

    if GoogleTranslator is not None:
        try:
            res = GoogleTranslator(source=src, target=tgt).translate(cleaned)
            if res and "too many requests" not in res.lower():
                return res
        except Exception:
            pass
    return None


def _get_lru_cache(name: str) -> OrderedDict:
    if name not in st.session_state or not isinstance(st.session_state[name], OrderedDict):
        st.session_state[name] = OrderedDict()
    return st.session_state[name]


def fast_free_translate(text: str, src: str, tgt: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if src == tgt:
        return cleaned

    cache = _get_lru_cache("translation_mem_cache")
    cache_key = f"{src}::{tgt}::{hashlib.sha256(cleaned.encode('utf-8')).hexdigest()}"
    if cache_key in cache:
        cache.move_to_end(cache_key)
        return cache[cache_key]

    chunks = chunk_text_smart(cleaned, max_chars=1100)
    if len(chunks) == 1:
        translated = _try_multi_endpoint_translate(chunks[0], src, tgt)
    else:
        with ThreadPoolExecutor(max_workers=min(4, len(chunks))) as ex:
            results = list(ex.map(lambda c: _try_multi_endpoint_translate(c, src, tgt) or c, chunks))
        translated = "\n".join(results) if any(results) else None

    if translated:
        cache[cache_key] = translated
        while len(cache) > MAX_MEM_CACHE_SIZE:
            cache.popitem(last=False)
        return translated
    return "Máy chủ dịch miễn phí đang tạm bận. Vui lòng thử lại sau vài giây."


def call_gemini_fast_rest(
    api_key: str,
    prompt_text: str,
    temperature: float = 0.1,
    timeout_sec: int = 22,
) -> Tuple[Optional[str], Optional[str], str]:
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return None, "Chưa nhập API Key.", ""

    discovered, key_err = discover_working_gemini_models(clean_k)
    if key_err:
        return None, key_err, ""

    ai_speed_mode = st.session_state.get("ai_speed_mode", "fast")
    pref_list = PREFERRED_GEMINI_MODELS_QUALITY if ai_speed_mode == "quality" else PREFERRED_GEMINI_MODELS_FAST
    ordered_discovered = [m for m in pref_list if m in discovered] + [m for m in discovered if m not in pref_list]
    pinned = st.session_state.get("pinned_gemini_model", "")
    models = ([pinned] + [m for m in ordered_discovered if m != pinned]) if (pinned and pinned in ordered_discovered) else ordered_discovered
    last_error = ""

    for model_name in models[:5]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
        gen_cfg: Dict[str, Any] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }
        if "gemini-3" in model_name:
            gen_cfg["thinkingConfig"] = {"thinkingLevel": "LOW" if ai_speed_mode == "quality" else "MINIMAL"}
        elif "2.5" in model_name:
            gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}

        payload = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": gen_cfg}
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}, method="POST",
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    candidates = resp_data.get("candidates", [])
                    if candidates:
                        resp_parts = candidates[0].get("content", {}).get("parts", [])
                        if resp_parts and "text" in resp_parts[0]:
                            st.session_state["pinned_gemini_model"] = model_name
                            return resp_parts[0]["text"], None, model_name
            except urllib.error.HTTPError as http_err:
                err_body = ""
                try:
                    err_body = http_err.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                last_error = f"HTTP {http_err.code}: {err_body[:160]}"
                if "API_KEY_INVALID" in err_body:
                    return None, "Gemini API Key không chính xác.", ""
                if "location is not supported" in err_body.lower():
                    return None, "Gemini API chặn khu vực IP hiện tại.", ""
                if http_err.code == 400 and ("thinkingConfig" in err_body or "responseMimeType" in err_body):
                    payload["generationConfig"] = {"temperature": temperature}
                    continue
                if http_err.code in (429, 503) and attempt == 0:
                    time.sleep(0.6)
                    continue
                break
            except Exception as exc:
                last_error = str(exc)
                break
    return None, last_error or "Không nhận được phản hồi từ Gemini API.", ""


def _parse_json_response(raw_text: str) -> Optional[Dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.IGNORECASE)
    json_match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    return json.loads(cleaned)


def validate_and_clean_ai_result(
    parsed: Dict[str, Any], input_kind: str, effective_dir: str, source_text: str = ""
) -> Dict[str, Any]:
    """Kiểm soát tuyệt đối ngôn ngữ đích & lọc dữ liệu rác."""
    if not isinstance(parsed, dict):
        return {}

    def _valid_str(v: Any) -> str:
        s = str(v or "").strip()
        if s.lower() in ("", "...", "n/a", "none", "null", "không có"):
            return ""
        return s

    main_t = _valid_str(parsed.get("main_translation"))
    ru_v = _valid_str(parsed.get("ru_version"))
    vi_v = _valid_str(parsed.get("vi_version"))
    en_v = _valid_str(parsed.get("en_version"))

    # KIỂM SOÁT TUYỆT ĐỐI CHIỀU VIỆT → NGA: main_translation PHẢI là tiếng Nga (Cyrillic)
    if effective_dir == DIRECTION_OPTIONS[2]:
        has_vi_in_main = bool(re.search(r"[ăâđêôơưàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]", main_t.lower()))
        if not re.search(r"[а-яА-ЯёЁ]", main_t) or has_vi_in_main:
            if re.search(r"[а-яА-ЯёЁ]", ru_v):
                main_t = ru_v
            elif source_text.strip():
                main_t = fast_free_translate(source_text, "vi", "ru")
                ru_v = main_t
        if not re.search(r"[а-яА-ЯёЁ]", ru_v):
            ru_v = main_t
        if not vi_v:
            vi_v = source_text.strip()

    # KIỂM SOÁT TUYỆT ĐỐI CHIỀU NGA → VIỆT: main_translation PHẢI là tiếng Việt
    elif effective_dir == DIRECTION_OPTIONS[1]:
        if re.search(r"[а-яА-ЯёЁ]", main_t):
            if vi_v and not re.search(r"[а-яА-ЯёЁ]", vi_v):
                main_t = vi_v
            elif source_text.strip():
                main_t = fast_free_translate(source_text, "ru", "vi")
                vi_v = main_t

    out: Dict[str, Any] = {
        "input_kind": input_kind,
        "effective_dir": effective_dir,
        "main_translation": main_t,
        "pronunciation_hint": _valid_str(parsed.get("pronunciation_hint")),
        "ru_version": ru_v,
        "vi_version": vi_v,
        "en_version": en_v,
        "context_note": _valid_str(parsed.get("context_note")),
        "morphology": {},
        "synonyms": [],
        "antonyms": [],
        "sentence_grammar": [],
        "context_examples": [],
        "slang_explanations": [],
        "vocabulary_table": [],
    }

    if input_kind == "word" and isinstance(parsed.get("morphology"), dict):
        m = parsed["morphology"]
        clean_m: Dict[str, Any] = {
            "word_type": _valid_str(m.get("word_type")),
            "lemma": _valid_str(m.get("lemma")),
            "aspect_or_gender": _valid_str(m.get("aspect_or_gender")),
            "usage_note": _valid_str(m.get("usage_note")),
        }

        raw_cases = m.get("cases_table")
        if isinstance(raw_cases, list) and len(raw_cases) == 6:
            valid_cases = []
            for r in raw_cases:
                if isinstance(r, dict) and _valid_str(r.get("case")):
                    sg = str(r.get("singular") or "—").strip() or "—"
                    pl = str(r.get("plural") or "—").strip() or "—"
                    if sg != "—" or pl != "—":
                        valid_cases.append({"case": _valid_str(r.get("case")), "singular": sg, "plural": pl})
            if len(valid_cases) == 6:
                clean_m["cases_table"] = valid_cases

        raw_conj = m.get("verb_conjugation")
        if isinstance(raw_conj, dict):
            valid_conj = {str(k).strip(): _valid_str(v) for k, v in raw_conj.items() if _valid_str(v) and _valid_str(v) != "—"}
            if len(valid_conj) >= 4:
                clean_m["verb_conjugation"] = valid_conj

        if clean_m.get("cases_table") or clean_m.get("verb_conjugation") or clean_m.get("usage_note"):
            out["morphology"] = clean_m

    for field_name in ("synonyms", "antonyms"):
        raw_list = parsed.get(field_name)
        if isinstance(raw_list, list):
            out[field_name] = [
                {"ru": _valid_str(it.get("ru")), "vi": _valid_str(it.get("vi"))}
                for it in raw_list
                if isinstance(it, dict) and _valid_str(it.get("ru")) and _valid_str(it.get("vi"))
            ][:5]

    if input_kind in ("sentence", "paragraph") and isinstance(parsed.get("sentence_grammar"), list):
        out["sentence_grammar"] = [
            {
                "segment": _valid_str(g.get("segment")),
                "grammar_tag": _valid_str(g.get("grammar_tag")),
                "explanation": _valid_str(g.get("explanation")),
            }
            for g in parsed["sentence_grammar"]
            if isinstance(g, dict) and _valid_str(g.get("segment")) and _valid_str(g.get("explanation"))
        ][:8]

    if isinstance(parsed.get("context_examples"), list):
        out["context_examples"] = [
            {
                "context": _valid_str(ex.get("context")) or "Ví dụ áp dụng",
                "ru": _valid_str(ex.get("ru")),
                "vi": _valid_str(ex.get("vi")),
            }
            for ex in parsed["context_examples"]
            if isinstance(ex, dict) and _valid_str(ex.get("ru")) and _valid_str(ex.get("vi"))
        ][:4]

    if isinstance(parsed.get("slang_explanations"), list):
        out["slang_explanations"] = [
            {
                "term": _valid_str(s.get("term")),
                "full_form": _valid_str(s.get("full_form")),
                "meaning_vi": _valid_str(s.get("meaning_vi")),
            }
            for s in parsed["slang_explanations"]
            if isinstance(s, dict) and _valid_str(s.get("term")) and _valid_str(s.get("meaning_vi"))
        ]

    if isinstance(parsed.get("vocabulary_table"), list):
        out["vocabulary_table"] = [
            {
                "ru_accent": _valid_str(v.get("ru_accent")),
                "vi": _valid_str(v.get("vi")),
                "en": _valid_str(v.get("en")),
            }
            for v in parsed["vocabulary_table"]
            if isinstance(v, dict) and _valid_str(v.get("ru_accent")) and _valid_str(v.get("vi"))
        ][:10]

    return out


def call_gemini_smart_translate(
    api_key: str, source_text: str, effective_dir: str, learner_level: str = "beginner"
) -> Tuple[Optional[Dict], Optional[str], float, str]:
    t0 = time.perf_counter()
    input_kind = classify_input_type(source_text)
    level_key = "beginner" if learner_level != "advanced" else "advanced"

    ai_cache = _get_lru_cache("gemini_result_cache")
    cache_key = hashlib.sha256(
        f"{effective_dir}::{input_kind}::{level_key}::{source_text.strip()}".encode("utf-8")
    ).hexdigest()
    if cache_key in ai_cache:
        ai_cache.move_to_end(cache_key)
        return ai_cache[cache_key], None, 0.01, "Cache"

    if effective_dir == DIRECTION_OPTIONS[2]:
        dir_rule = (
            "CHIỀU DỊCH BẮT BUỘC: TIẾNG VIỆT → TIẾNG NGA.\n"
            "- `main_translation` BẮT BUỘC CHỈ CHỨA TIẾNG NGA (chữ Cyrillic, có dấu trọng âm \\u0301 nếu là từ đơn). TUYỆT ĐỐI KHÔNG viết tiếng Việt vào `main_translation`!\n"
            "- `ru_version` là tiếng Nga; `vi_version` là tiếng Việt gốc; `en_version` là tiếng Anh."
        )
    elif effective_dir == DIRECTION_OPTIONS[1]:
        dir_rule = (
            "CHIỀU DỊCH BẮT BUỘC: TIẾNG NGA → TIẾNG VIỆT.\n"
            "- `main_translation` BẮT BUỘC CHỈ CHỨA TIẾNG VIỆT chuẩn xác, tự nhiên.\n"
            "- `ru_version` là tiếng Nga gốc; `vi_version` là tiếng Việt; `en_version` là tiếng Anh."
        )
    else:
        dir_rule = "CHIỀU DỊCH: ĐỐI CHIẾU 3 NGÔN NGỮ (NGA · VIỆT · ANH). Điền đầy đủ `ru_version`, `vi_version`, `en_version`."

    if input_kind == "word":
        task_instruction = """
Đầu vào là TỪ ĐƠN hoặc CỤM TỪ NGẮN (luôn phân tích hình thái của TỪ TIẾNG NGA tương ứng!):
1. Xác định đúng từ loại tiếng Nga (Danh từ / Tính từ / Đại từ / Động từ / Trạng từ).
2. Nếu là ĐỘNG TỪ: BẮT BUỘC điền đủ `verb_conjugation` (я, ты, он / она / оно, мы, вы, они, Quá khứ, Mệnh lệnh) và ghi rõ cặp thể НСВ / СВ vào `aspect_or_gender`. Đặt `cases_table` = [].
3. Nếu là DANH TỪ / TÍNH TỪ / ĐẠI TỪ / CỤM DANH TỪ: BẮT BUỘC điền ĐỦ 6 CÁCH vào `cases_table` (1. Именительный -> 6. Предложный, có dấu trọng âm \\u0301, cả `singular` và `plural`; nếu không có số nhiều ghi "—"). Đặt `verb_conjugation` = {}.
4. Nếu là TRẠNG TỪ / TỪ KHÔNG BIẾN CÁCH: đặt `cases_table` = [], `verb_conjugation` = {}, giải thích cách dùng & cấp so sánh vào `usage_note`.
5. BẮT BUỘC điền `synonyms` (2–4 từ đồng nghĩa tiếng Nga có trọng âm \\u0301 + nghĩa Việt) và `antonyms` (1–3 từ trái nghĩa tiếng Nga có trọng âm \\u0301 + nghĩa Việt nếu có).
6. BẮT BUỘC tạo 3 ví dụ áp dụng thực tế (`context_examples`) chứa CHÍNH từ tiếng Nga này, có dấu trọng âm \\u0301 và dịch tiếng Việt.
7. Đặt `sentence_grammar` = [].
"""
    elif input_kind == "sentence":
        task_instruction = """
Đầu vào là MỘT CÂU HOÀN CHỈNH:
1. Đặt `morphology` = {}.
2. BẮT BUỘC điền `sentence_grammar` (3–6 mục) phân tích ngữ pháp tiếng Nga (cách mấy, tại sao, thể động từ НСВ/СВ).
3. BẮT BUỘC tạo 2–3 ví dụ áp dụng (`context_examples`) dùng lại cấu trúc hoặc từ khóa chính của câu.
4. Điền `synonyms` / `antonyms` (1–3 cặp) cho từ khóa quan trọng nhất trong câu nếu phù hợp.
5. Điền `vocabulary_table` 3–6 từ khóa quan trọng (có dấu trọng âm \\u0301).
"""
    else:
        task_instruction = """
Đầu vào là ĐOẠN VĂN DÀI:
1. Dịch toàn bộ đoạn văn chuẩn xác, giữ đúng bố cục xuống dòng.
2. Đặt `morphology` = {}.
3. Điền `sentence_grammar` 3–5 điểm ngữ pháp nổi bật trong đoạn.
4. Điền `vocabulary_table` 5–8 thuật ngữ trọng tâm (có dấu trọng âm \\u0301).
5. BẮT BUỘC tạo 2 ví dụ áp dụng (`context_examples`) cho thuật ngữ/cấu trúc hay nhất trong đoạn.
"""

    if level_key == "beginner":
        level_instruction = (
            "CHẾ ĐỘ NGƯỜI MỚI BẮT ĐẦU (A0–A1):\n"
            "- Nếu đầu vào là từ đơn hoặc cụm từ ngắn, BẮT BUỘC điền `pronunciation_hint` là cách đọc gần đúng bằng âm tiếng Việt "
            "(tuân thủ quy tắc giảm âm `о → а` khi không có trọng âm và vô thanh hóa phụ âm cuối, ví dụ `хорошо́` → `kha-ra-shô`). "
            "Nếu là câu dài/đoạn văn có thể để chuỗi rỗng.\n"
            "- Giải thích ngữ pháp (`usage_note`, `sentence_grammar`, `context_note`) thật ngắn gọn, dễ hiểu cho người mới, "
            "chỉ rõ đuôi từ nào biến đổi; lấy ví dụ (`context_examples`) gắn với đời sống sinh viên (ký túc xá, siêu thị, lớp dự bị)."
        )
    else:
        level_instruction = (
            "CHẾ ĐỘ CHUYÊN SÂU:\n"
            "- Để `pronunciation_hint` = \"\" (hoặc chỉ ghi nếu là từ đơn khó đọc).\n"
            "- Phân tích ngữ pháp, sắc thái học thuật và biến cách/chia động từ đầy đủ, chuẩn xác."
        )

    system_prompt = f"""
Bạn là giáo sư ngôn ngữ học Nga – Việt chuyên sâu dịch thuật và thuật ngữ đại học.
{dir_rule}
{level_instruction}
{task_instruction}
CHỈ TRẢ VỀ đúng 1 JSON hợp lệ:
{{
  "main_translation": "",
  "pronunciation_hint": "",
  "ru_version": "",
  "vi_version": "",
  "en_version": "",
  "morphology": {{
    "word_type": "",
    "lemma": "",
    "aspect_or_gender": "",
    "cases_table": [{{"case": "1. Именительный (Cách 1)", "singular": "", "plural": ""}}],
    "verb_conjugation": {{"я": "", "ты": "", "он / она / оно": "", "мы": "", "вы": "", "они": "", "Quá khứ": "", "Mệnh lệnh": ""}},
    "usage_note": ""
  }},
  "synonyms": [{{"ru": "Từ đồng nghĩa tiếng Nga có trọng âm \\u0301", "vi": "Nghĩa tiếng Việt"}}],
  "antonyms": [{{"ru": "Từ trái nghĩa tiếng Nga có trọng âm \\u0301", "vi": "Nghĩa tiếng Việt"}}],
  "sentence_grammar": [{{"segment": "", "grammar_tag": "", "explanation": ""}}],
  "context_examples": [{{"context": "Ngữ cảnh ngắn", "ru": "Câu tiếng Nga có dấu trọng âm \\u0301", "vi": "Nghĩa tiếng Việt"}}],
  "slang_explanations": [{{"term": "", "full_form": "", "meaning_vi": ""}}],
  "vocabulary_table": [{{"ru_accent": "", "vi": "", "en": ""}}],
  "context_note": "1-2 câu lưu ý ngữ pháp/ngữ cảnh ngắn gọn."
}}
"""
    raw_text, err, model_used = call_gemini_fast_rest(
        api_key=api_key,
        prompt_text=f"{system_prompt}\n\nVăn bản cần xử lý:\n{source_text.strip()}",
        temperature=0.1,
        timeout_sec=22,
    )
    elapsed = time.perf_counter() - t0
    if not raw_text:
        return None, err, elapsed, ""

    try:
        parsed = _parse_json_response(raw_text)
        cleaned = validate_and_clean_ai_result(parsed or {}, input_kind, effective_dir=effective_dir, source_text=source_text)
        if not cleaned.get("main_translation"):
            return None, "Gemini trả về JSON không có bản dịch.", elapsed, model_used
        ai_cache[cache_key] = cleaned
        while len(ai_cache) > MAX_AI_CACHE_SIZE:
            ai_cache.popitem(last=False)
        return cleaned, None, elapsed, model_used
    except Exception as exc:
        return None, f"Lỗi đọc JSON từ Gemini: {exc}", elapsed, model_used


def extract_text_from_uploaded_doc(uploaded_file) -> Tuple[Optional[str], Optional[str]]:
    name = uploaded_file.name.lower()
    raw_bytes = uploaded_file.getvalue()
    if name.endswith((".txt", ".md")):
        for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
            try:
                return raw_bytes.decode(enc).strip(), None
            except Exception:
                continue
        return None, "Không thể đọc mã hóa của tệp văn bản này."

    if name.endswith(".docx"):
        if python_docx is None:
            return None, "Thiếu thư viện python-docx trong requirements.txt."
        try:
            doc = python_docx.Document(io.BytesIO(raw_bytes))
            return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip()), None
        except Exception as exc:
            return None, f"Lỗi đọc tệp .docx: {exc}"

    if name.endswith(".pdf"):
        if PdfReader is None:
            return None, "Thiếu thư viện pypdf trong requirements.txt."
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages[:15]]
            text = "\n\n".join(p.strip() for p in pages if p.strip())
            return (text, None) if text else (None, "Tệp PDF này không có lớp văn bản để trích xuất.")
        except Exception as exc:
            return None, f"Lỗi đọc tệp .pdf: {exc}"
    return None, "Định dạng tệp chưa được hỗ trợ."


def fallback_fast_translate(source_text: str, effective_dir: str) -> Dict[str, Any]:
    input_kind = classify_input_type(source_text)
    text_for_trans = source_text.strip()
    detected_slang = detect_slang_in_text(text_for_trans)
    expanded_ru = text_for_trans

    slang_inflections = {
        "препод": "преподаватель", "курсач": "курсовую работу", "лабу": "лабораторную работу",
        "лаба": "лабораторная работа", "лабы": "лабораторные работы",
        "хвосты": "академические задолженности", "хвост": "академическую задолженность",
        "общаге": "общежитии", "общага": "общежитие", "стипуха": "стипендия",
        "зачетку": "зачётную книжку", "зачетка": "зачётная книжка",
        "инфу": "информацию", "инфа": "информация", "презу": "презентацию",
        "преза": "презентация", "студак": "студенческий билет", "столовку": "столовую",
    }
    for s_form, full_rep in slang_inflections.items():
        expanded_ru = re.sub(rf"\b{re.escape(s_form)}\b", full_rep, expanded_ru, flags=re.IGNORECASE)

    with ThreadPoolExecutor(max_workers=3) as executor:
        if effective_dir == DIRECTION_OPTIONS[1]:  # Nga → Việt
            f_vi = executor.submit(fast_free_translate, expanded_ru, "ru", "vi")
            f_en = executor.submit(fast_free_translate, expanded_ru, "ru", "en")
            vi_ver, en_ver, ru_ver = f_vi.result(), f_en.result(), source_text
            main_trans = vi_ver
        elif effective_dir == DIRECTION_OPTIONS[2]:  # Việt → Nga
            f_ru = executor.submit(fast_free_translate, text_for_trans, "vi", "ru")
            f_en = executor.submit(fast_free_translate, text_for_trans, "vi", "en")
            ru_ver, en_ver, vi_ver = f_ru.result(), f_en.result(), source_text
            main_trans = ru_ver
        else:
            has_cyr = bool(re.search(r"[а-яА-ЯёЁ]", text_for_trans))
            src_g = "ru" if has_cyr else "auto"
            f_vi = executor.submit(fast_free_translate, expanded_ru, src_g, "vi")
            f_en = executor.submit(fast_free_translate, expanded_ru, src_g, "en")
            ru_ver = source_text if has_cyr else executor.submit(fast_free_translate, text_for_trans, "auto", "ru").result()
            vi_ver, en_ver = f_vi.result(), f_en.result()
            main_trans = f"Tiếng Việt:\n{vi_ver}\n\nTiếng Nga:\n{ru_ver}\n\nTiếng Anh:\n{en_ver}"

    vocab_list = [
        {"ru_accent": f"{s['accent']} ({s['full']})", "en": s["en"], "vi": s["vi"]}
        for s in detected_slang
    ]
    slang_explanations = [
        {"term": s["word"], "full_form": s["full"], "meaning_vi": f"{s['vi']} — VD: «{s['example']}»"}
        for s in detected_slang
    ]
    examples = [
        {"context": "Tiếng lóng đại học", "ru": s["example"], "vi": s["vi"]}
        for s in detected_slang[:2]
    ]

    return {
        "input_kind": input_kind,
        "effective_dir": effective_dir,
        "main_translation": main_trans,
        "ru_version": ru_ver,
        "vi_version": vi_ver,
        "en_version": en_ver,
        "morphology": {},
        "synonyms": [],
        "antonyms": [],
        "sentence_grammar": [],
        "context_examples": examples,
        "slang_explanations": slang_explanations,
        "vocabulary_table": vocab_list,
        "context_note": "Nhập Gemini API Key (miễn phí) ở thanh bên trái để bật chia 6 cách, chia động từ, từ đồng nghĩa/trái nghĩa, phân tích ngữ pháp câu dài và ví dụ áp dụng.",
    }


def is_vocab_due_today(item: Dict[str, Any], today_str: Optional[str] = None) -> bool:
    today = today_str or datetime.now().strftime("%Y-%m-%d")
    next_rev = str(item.get("next_review", "") or "").strip()
    if next_rev:
        return next_rev <= today
    return not bool(item.get("mastered", False))


def apply_vocab_review_rating(ru_accent: str, rating: int) -> None:
    """Cập nhật lịch nhắc ôn 3 mức độ nhớ: 0=Chưa nhớ (hôm nay), 1=Nhớ mang máng (+1 ngày), 2=Thuộc kỹ (+5 ngày)."""
    saved_list = st.session_state.get("saved_vocab_notebook")
    if not isinstance(saved_list, list):
        return
    now_dt = datetime.now()
    today = now_dt.strftime("%Y-%m-%d")
    target_idx = None
    for idx, item in enumerate(saved_list):
        if item.get("ru_accent") == ru_accent:
            target_idx = idx
            break
    if target_idx is None:
        return

    item = saved_list[target_idx]
    if rating <= 0:
        item["level"] = 0
        item["mastered"] = False
        item["next_review"] = today
        saved_list.append(saved_list.pop(target_idx))
    elif rating == 1:
        item["level"] = 1
        item["mastered"] = False
        item["next_review"] = (now_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        item["level"] = 2
        item["mastered"] = True
        item["next_review"] = (now_dt + timedelta(days=5)).strftime("%Y-%m-%d")

    sync_current_account_to_db()


def add_vocab_items_to_notebook(items: List[Dict[str, str]]) -> int:
    if "saved_vocab_notebook" not in st.session_state:
        st.session_state["saved_vocab_notebook"] = []
    today = datetime.now().strftime("%Y-%m-%d")
    existing = {v["ru_accent"].lower() for v in st.session_state["saved_vocab_notebook"] if v.get("ru_accent")}
    added = 0
    for it in items:
        ru_k = str(it.get("ru_accent", "")).strip()
        if ru_k and ru_k.lower() not in existing:
            pron = str(it.get("pronunciation") or it.get("pronunciation_hint") or "").strip()
            st.session_state["saved_vocab_notebook"].insert(
                0,
                {
                    "ru_accent": ru_k,
                    "en": str(it.get("en", "")).strip(),
                    "vi": str(it.get("vi", "")).strip(),
                    "pronunciation": pron,
                    "pronunciation_hint": pron,
                    "example": str(it.get("example", "")).strip(),
                    "level": 0,
                    "next_review": today,
                    "mastered": False,
                },
            )
            existing.add(ru_k.lower())
            added += 1
    if added > 0:
        sync_current_account_to_db()
    return added


def export_vocab_to_anki_csv(vocab_list: List[Dict[str, str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tieng_Nga", "Phien_am", "Tieng_Viet", "Tieng_Anh"])
    for item in vocab_list:
        pron = item.get("pronunciation") or item.get("pronunciation_hint") or ""
        writer.writerow([item.get("ru_accent", ""), pron, item.get("vi", ""), item.get("en", "")])
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _generate_quiz_question(pool: List[Dict[str, Any]], quiz_dir: str = "ru_to_vi") -> Optional[Dict[str, Any]]:
    valid_pool = [x for x in pool if str(x.get("ru_accent", "")).strip() and str(x.get("vi", "")).strip()]
    if len(valid_pool) < 4:
        return None
    target = random.choice(valid_pool)
    others = [x for x in valid_pool if x["ru_accent"] != target["ru_accent"]]
    if len(others) < 3:
        return None
    distractors = random.sample(others, 3)

    if quiz_dir == "vi_to_ru":
        options = [target["ru_accent"]] + [d["ru_accent"] for d in distractors]
        random.shuffle(options)
        return {
            "mode": "vi_to_ru",
            "prompt": target["vi"],
            "correct": target["ru_accent"],
            "sub_hint": "Chọn từ tiếng Nga tương ứng:",
            "options": options,
            "answered": None,
        }

    if quiz_dir == "audio_to_vi":
        options = [target["vi"]] + [d["vi"] for d in distractors]
        random.shuffle(options)
        ru_plain = target["ru_accent"].split("(")[0].replace("\u0301", "").strip()
        pron = str(target.get("pronunciation") or target.get("pronunciation_hint") or "").strip()
        return {
            "mode": "audio_to_vi",
            "prompt": "",
            "audio_text": ru_plain,
            "reveal_ru": target["ru_accent"],
            "reveal_pron": pron,
            "correct": target["vi"],
            "sub_hint": "Bấm nghe phát âm tiếng Nga và chọn nghĩa tiếng Việt đúng:",
            "options": options,
            "answered": None,
        }

    options = [target["vi"]] + [d["vi"] for d in distractors]
    random.shuffle(options)
    return {
        "mode": "ru_to_vi",
        "prompt": target["ru_accent"],
        "correct": target["vi"],
        "sub_hint": "Chọn nghĩa tiếng Việt đúng:",
        "options": options,
        "answered": None,
    }