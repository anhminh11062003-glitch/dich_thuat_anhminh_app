"""
Anh Minh Translate — Dịch thuật siêu tốc, ngữ pháp 6 cách & ôn tập tiếng Nga đồng bộ đa thiết bị
Tác giả: Mai Văn Minh — Sinh viên năm 4, Chuyên ngành Đóng tàu, СПбГМТУ (Xanh-Petecbua)
"""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import base64
import csv
import hashlib
import hmac
import html
import io
import json
import os
from pathlib import Path
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
import streamlit.components.v1 as components

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


# ==============================================================================
# 1. CẤU HÌNH TRANG, TÁC GIẢ & HẰNG SỐ
# ==============================================================================
st.set_page_config(
    page_title="Anh Minh Translate · Mai Văn Minh (СПбГМТУ)",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"
AUTHOR_NOTIFICATION_EMAIL = "anhminh11062003@gmail.com"
FIXED_AUTHOR_AVATAR_BASE64_OR_URL = ""
MAX_MEM_CACHE_SIZE = 300
MAX_AI_CACHE_SIZE = 150
MAX_HISTORY_ITEMS = 50

PREFERRED_GEMINI_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def _get_secret_or_env(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            val = str(st.secrets[key]).strip()
            if val:
                return val
    except Exception:
        pass
    return os.environ.get(key, default).strip()


DEFAULT_AUTHOR_PASSWORD = _get_secret_or_env("AUTHOR_ADMIN_PASSWORD", "minh1106")
SESSION_SIGNING_SECRET = _get_secret_or_env("SESSION_SIGNING_SECRET", f"am_session_{DEFAULT_AUTHOR_PASSWORD}_v12")
SUPABASE_URL = _get_secret_or_env("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = _get_secret_or_env("SUPABASE_KEY", "")
FORMSPREE_ENDPOINT = _get_secret_or_env("FORMSPREE_ENDPOINT", "")
EMAILJS_SERVICE_ID = _get_secret_or_env("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = _get_secret_or_env("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = _get_secret_or_env("EMAILJS_PUBLIC_KEY", "")

SQLITE_DB_PATH = Path("anhminh_users.db")
USER_LOGS_FILE = Path(".user_access_logs.json")

STUDENT_YEAR_OPTIONS = [
    "Dự bị tiếng Nga (Подфак)",
    "Sinh viên Năm 1",
    "Sinh viên Năm 2",
    "Sinh viên Năm 3",
    "Sinh viên Năm 4",
    "Sinh viên Năm 5 (Специалитет)",
    "Cao học / Thạc sĩ",
    "Nghiên cứu sinh",
    "Khác",
]

DIRECTION_OPTIONS = [
    "Tự động (Nga ↔ Việt)",
    "Tiếng Nga → Tiếng Việt",
    "Tiếng Việt → Tiếng Nga",
    "Đối chiếu 3 ngôn ngữ (Nga · Việt · Anh)",
]


def esc(text: Any) -> str:
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def render_html(html_str: str) -> None:
    cleaned_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(cleaned_lines), unsafe_allow_html=True)


def clean_api_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    return re.sub(r'[\s"\'\`]+', "", raw_key.strip())


def verify_author_password(input_pwd: str) -> bool:
    if not input_pwd or not DEFAULT_AUTHOR_PASSWORD:
        return False
    return hmac.compare_digest(input_pwd.strip(), DEFAULT_AUTHOR_PASSWORD)


def get_author_monogram_svg_uri() -> str:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
      <rect width="120" height="120" rx="60" fill="#18181B"/>
      <text x="60" y="72" text-anchor="middle" font-family="Inter, -apple-system, sans-serif" font-size="42" font-weight="600" fill="#FAF9F6" letter-spacing="-1">MM</text>
    </svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


@st.cache_data(show_spinner=False)
def get_author_avatar_data_uri() -> str:
    if FIXED_AUTHOR_AVATAR_BASE64_OR_URL.strip():
        val = FIXED_AUTHOR_AVATAR_BASE64_OR_URL.strip()
        if val.startswith(("http://", "https://", "data:image/")):
            return val
        return f"data:image/jpeg;base64,{val}"

    candidate_names = [
        "avatar.png", "avatar.jpg", "avatar.jpeg", "avatar.webp",
        "minh.png", "minh.jpg", "minh.jpeg", "author.png", "author.jpg",
    ]
    base_dir = Path(__file__).parent if "__file__" in globals() else Path(".")
    for name in candidate_names:
        for folder in (base_dir, Path(".")):
            p = folder / name
            if p.exists() and p.is_file():
                try:
                    raw = p.read_bytes()
                    ext = p.suffix.lower().replace(".", "")
                    mime = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
                    b64 = base64.b64encode(raw).decode("utf-8")
                    return f"data:{mime};base64,{b64}"
                except Exception:
                    pass
    return get_author_monogram_svg_uri()


def render_copy_button(text_to_copy: str, label: str = "Sao chép", key_suffix: str = "", is_dark: bool = False) -> None:
    if not text_to_copy:
        return
    safe_js_text = json.dumps(text_to_copy, ensure_ascii=False)
    safe_label = esc(label)
    btn_id = f"cp_{hashlib.md5((key_suffix + text_to_copy[:30]).encode('utf-8')).hexdigest()[:10]}"
    bg = "#18181B" if is_dark else "#FFFFFF"
    fg = "#FAFAFA" if is_dark else "#18181B"
    bd = "#3F3F46" if is_dark else "#D4D4D8"
    done_bg = "#FAFAFA" if is_dark else "#18181B"
    done_fg = "#0B0B0D" if is_dark else "#FFFFFF"
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:transparent;overflow:hidden;">
            <button id="{btn_id}" onclick="copyNow()" style="
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: {bg};
                color: {fg};
                border: 1px solid {bd};
                border-radius: 8px;
                padding: 5px 12px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
            ">{safe_label}</button>
            <script>
            function copyNow() {{
                const text = {safe_js_text};
                const btn = document.getElementById("{btn_id}");
                const done = () => {{
                    btn.innerText = "Đã sao chép";
                    btn.style.background = "{done_bg}";
                    btn.style.color = "{done_fg}";
                    btn.style.borderColor = "{done_bg}";
                    setTimeout(() => {{
                        btn.innerText = {json.dumps(label, ensure_ascii=False)};
                        btn.style.background = "{bg}";
                        btn.style.color = "{fg}";
                        btn.style.borderColor = "{bd}";
                    }}, 1500);
                }};
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).then(done).catch(() => fallback(text, done));
                }} else {{
                    fallback(text, done);
                }}
            }}
            function fallback(text, cb) {{
                const ta = document.createElement("textarea");
                ta.value = text;
                ta.style.position = "fixed";
                ta.style.opacity = "0";
                document.body.appendChild(ta);
                ta.select();
                try {{ document.execCommand("copy"); cb(); }} catch (e) {{}}
                document.body.removeChild(ta);
            }}
            </script>
        </body>
        </html>
        """,
        height=34,
    )


# ==============================================================================
# 2. HỆ THỐNG TÀI KHOẢN & ĐỒNG BỘ ĐA THIẾT BỊ (SUPABASE CLOUD + SQLITE LOCAL)
#    GIỮ PHIÊN BỀN VỮNG QUA MỌI LẦN F5 BẰNG HMAC TOKEN TRÊN st.query_params["s"]
# ==============================================================================
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


def create_session_token(username: str) -> str:
    """Tạo token phiên đã ký HMAC (không chứa mật khẩu hay API key) để giữ đăng nhập qua F5."""
    u_b64 = base64.urlsafe_b64encode(username.encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(SESSION_SIGNING_SECRET.encode("utf-8"), u_b64.encode("ascii"), hashlib.sha256).hexdigest()[:24]
    return f"{u_b64}.{sig}"


def verify_session_token(token: str) -> Optional[str]:
    if not token or "." not in token:
        return None
    try:
        u_b64, sig = token.split(".", 1)
        expected = hmac.new(SESSION_SIGNING_SECRET.encode("utf-8"), u_b64.encode("ascii"), hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected):
            return None
        pad = "=" * (-len(u_b64) % 4)
        return base64.urlsafe_b64decode((u_b64 + pad).encode("ascii")).decode("utf-8")
    except Exception:
        return None


def _is_cloud_sync_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _init_sqlite_db() -> None:
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
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
    except Exception:
        pass


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
                if isinstance(rows, list) and rows:
                    payload = rows[0].get("payload")
                    if isinstance(payload, str):
                        return json.loads(payload)
                    if isinstance(payload, dict):
                        return payload
        except Exception:
            pass

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
    payload["updated_at"] = now_iso
    payload_str = json.dumps(payload, ensure_ascii=False)

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
            body = json.dumps({"username": uname, "payload": payload, "updated_at": now_iso}, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers=_supabase_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201, 204):
                    cloud_ok = True
        except Exception:
            pass

    return cloud_ok or local_ok


def db_list_all_users() -> List[Dict[str, str]]:
    """Dành cho Chế độ Tác giả xem danh sách sinh viên đã đăng ký."""
    users: List[Dict[str, str]] = []
    if _is_cloud_sync_enabled():
        try:
            url = f"{SUPABASE_URL}/rest/v1/am_users?select=username,payload,updated_at&order=updated_at.desc&limit=50"
            req = urllib.request.Request(url, headers=_supabase_headers(), method="GET")
            with urllib.request.urlopen(req, timeout=8) as resp:
                rows = json.loads(resp.read().decode("utf-8"))
                for r in rows:
                    p = r.get("payload") if isinstance(r.get("payload"), dict) else {}
                    prof = p.get("profile") or {}
                    users.append({
                        "username": r.get("username", ""),
                        "full_name": prof.get("full_name", ""),
                        "student_year": prof.get("student_year", ""),
                        "university": prof.get("university", ""),
                        "vocab_count": str(len(p.get("vocab_notebook") or [])),
                        "time": str(r.get("updated_at", ""))[:19],
                    })
                return users
        except Exception:
            pass

    _init_sqlite_db()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            rows = conn.execute("SELECT username, payload, updated_at FROM am_users ORDER BY updated_at DESC LIMIT 50").fetchall()
            for uname, raw_p, upd in rows:
                p = json.loads(raw_p) if raw_p else {}
                prof = p.get("profile") or {}
                users.append({
                    "username": uname,
                    "full_name": prof.get("full_name", ""),
                    "student_year": prof.get("student_year", ""),
                    "university": prof.get("university", ""),
                    "vocab_count": str(len(p.get("vocab_notebook") or [])),
                    "time": str(upd)[:19],
                })
    except Exception:
        pass
    return users


def sync_current_account_to_db() -> None:
    """Lưu đồng bộ tức thì toàn bộ trạng thái tài khoản hiện tại (API Key, Hồ sơ, Sổ từ vựng, Lịch sử, Nền sáng/tối)."""
    uname = st.session_state.get("auth_username", "")
    if not uname:
        return
    existing = db_get_user(uname) or {}
    payload = {
        "password_hash": existing.get("password_hash", st.session_state.get("auth_password_hash", "")),
        "profile": {
            "full_name": st.session_state.get("confirmed_user_name", ""),
            "student_year": st.session_state.get("confirmed_user_year", "Sinh viên Năm 4"),
            "university": st.session_state.get("confirmed_user_uni", ""),
        },
        "api_key": clean_api_key(st.session_state.get("saved_gemini_api_key", "")),
        "theme_mode": st.session_state.get("theme_mode", "light"),
        "vocab_notebook": st.session_state.get("saved_vocab_notebook", [])[:500],
        "translation_history": st.session_state.get("translation_history", [])[:MAX_HISTORY_ITEMS],
    }
    db_save_user(uname, payload)


def apply_user_payload_to_session(username: str, payload: Dict[str, Any]) -> None:
    st.session_state["auth_username"] = username
    st.session_state["auth_password_hash"] = payload.get("password_hash", "")
    prof = payload.get("profile") or {}
    st.session_state["confirmed_user_name"] = prof.get("full_name", "")
    st.session_state["confirmed_user_year"] = prof.get("student_year", "Sinh viên Năm 4")
    st.session_state["confirmed_user_uni"] = prof.get("university", "")
    st.session_state["saved_gemini_api_key"] = clean_api_key(payload.get("api_key", ""))
    st.session_state["theme_mode"] = payload.get("theme_mode", "light") if payload.get("theme_mode") in ("light", "dark") else "light"
    st.session_state["saved_vocab_notebook"] = payload.get("vocab_notebook") if isinstance(payload.get("vocab_notebook"), list) else []
    st.session_state["translation_history"] = payload.get("translation_history") if isinstance(payload.get("translation_history"), list) else []
    try:
        st.query_params["s"] = create_session_token(username)
    except Exception:
        pass


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
                f"<p><b>Họ và tên:</b> {esc(full_name)}</p>"
                f"<p><b>Năm học:</b> {esc(student_year)}</p>"
                f"<p><b>Trường:</b> {esc(university)}</p>"
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


# ==============================================================================
# 3. TỪ ĐIỂN TIẾNG LÓNG SINH VIÊN NGA (30 TỪ THỰC CHIẾN)
# ==============================================================================
RUSSIAN_SLANG_DICT: List[Dict[str, str]] = [
    {"word": "препод", "accent": "пре́под", "full": "преподаватель", "en": "lecturer", "vi": "Giảng viên, thầy/cô đại học", "example": "Препод сегодня добрый, всех отпустил пораньше."},
    {"word": "курсач", "accent": "курса́ч", "full": "курсовая работа", "en": "course project", "vi": "Đồ án môn học / Tiểu luận", "example": "Мне нужно сдать курсач до пятницы."},
    {"word": "лаба", "accent": "ла́ба", "full": "лабораторная работа", "en": "lab work", "vi": "Bài thí nghiệm / Thực hành Lab", "example": "У нас сегодня две лабы по физике."},
    {"word": "хвост", "accent": "хвост", "full": "академическая задолженность", "en": "failed exam", "vi": "Nợ môn (cần thi lại)", "example": "Нужно закрыть все хвосты до начала сессии."},
    {"word": "зачетка", "accent": "зачётка", "full": "зачётная книжка", "en": "record book", "vi": "Sổ điểm sinh viên", "example": "Не забудь взять зачётку на экзамен!"},
    {"word": "автомат", "accent": "автома́т", "full": "зачёт/экзамен автоматом", "en": "automatic pass", "vi": "Được miễn thi (qua môn tự động)", "example": "Я ходил на все лекции и получил автомат!"},
    {"word": "пара", "accent": "па́ра", "full": "учебная пара (90 минут)", "en": "90-min class", "vi": "Ca học đại học (90 phút)", "example": "Во сколько завтра первая пара?"},
    {"word": "общага", "accent": "обща́га", "full": "общежитие", "en": "dormitory", "vi": "Ký túc xá sinh viên", "example": "Вечером собираемся в общаге готовиться к сессии."},
    {"word": "стипуха", "accent": "стипу́ха", "full": "стипендия", "en": "scholarship", "vi": "Tiền học bổng hàng tháng", "example": "Сегодня пришла стипуха!"},
    {"word": "окно", "accent": "окно́", "full": "перерыв между парами", "en": "free period", "vi": "Ca trống giữa các tiết học", "example": "У нас окно между второй и четвёртой парой."},
    {"word": "сессия", "accent": "се́ссия", "full": "экзаменационная сессия", "en": "exam period", "vi": "Kỳ thi học kỳ", "example": "Зимняя сессия начинается в январе."},
    {"word": "пересдача", "accent": "пересда́ча", "full": "повторная сдача", "en": "retake exam", "vi": "Thi lại", "example": "Комиссия назначила пересдачу на следующую неделю."},
    {"word": "деканат", "accent": "декана́т", "full": "администрация факультета", "en": "dean's office", "vi": "Văn phòng khoa / Giáo vụ khoa", "example": "Возьми справку об обучении в деканате."},
    {"word": "шпора", "accent": "шпо́ра", "full": "шпаргалка", "en": "cheat sheet", "vi": "Phao thi / Tờ ghi chú nhỏ", "example": "Писать шпоры полезно для памяти."},
    {"word": "домашка", "accent": "дома́шка", "full": "домашнее задание", "en": "homework", "vi": "Bài tập về nhà", "example": "Скинь домашку по матану, пожалуйста!"},
    {"word": "матан", "accent": "мата́н", "full": "математический анализ", "en": "calculus", "vi": "Môn Giải tích toán học", "example": "Завтра коллоквиум по матану."},
    {"word": "сопромат", "accent": "сопрома́т", "full": "сопротивление материалов", "en": "strength of materials", "vi": "Môn Sức bền vật liệu", "example": "Сдал сопромат — можно жениться!"},
    {"word": "научник", "accent": "нау́чник", "full": "научный руководитель", "en": "advisor", "vi": "Giảng viên hướng dẫn đồ án", "example": "Мой научник одобрил тему диплома."},
    {"word": "инфа", "accent": "инфа́", "full": "информация", "en": "info", "vi": "Thông tin (nhóm chat Telegram/VK)", "example": "Спасибо за инфу, передам группе!"},
    {"word": "преза", "accent": "пре́за", "full": "презентация", "en": "presentation", "vi": "Bài thuyết trình / Slide", "example": "Ты уже сделал презу к завтрашнему семинару?"},
    {"word": "коллок", "accent": "колло́к", "full": "коллоквиум", "en": "colloquium", "vi": "Kiểm tra vấn đáp giữa kỳ", "example": "В среду будет коллок по гидромеханике."},
    {"word": "госы", "accent": "го́сы", "full": "государственные экзамены", "en": "state exams", "vi": "Kỳ thi tốt nghiệp quốc gia", "example": "В июне сдаём госы и защищаем диплом."},
    {"word": "прогул", "accent": "прогу́л", "full": "пропуск без причины", "en": "skipping class", "vi": "Nghỉ học không phép", "example": "За прогулы без справки могут не поставить зачёт."},
    {"word": "отработка", "accent": "отрабо́тка", "full": "отработка занятия", "en": "make-up lab", "vi": "Học bù / Làm bù bài thí nghiệm", "example": "Мне нужно прийти на отработку лабы в пятницу."},
    {"word": "студак", "accent": "студа́к", "full": "студенческий билет", "en": "student ID", "vi": "Thẻ sinh viên", "example": "Покажи студак на входе в корпус."},
    {"word": "пропуск", "accent": "про́пуск", "full": "электронный пропуск", "en": "access pass", "vi": "Thẻ từ ra vào trường / KTX", "example": "Я забыл пропуск в комнате."},
    {"word": "столовка", "accent": "столо́вка", "full": "студенческая столовая", "en": "cafeteria", "vi": "Căng-tin / Nhà ăn sinh viên", "example": "Пойдём в столовку на большой перемене."},
    {"word": "академ", "accent": "акаде́м", "full": "академический отпуск", "en": "academic leave", "vi": "Bảo lưu kết quả học tập", "example": "Он взял академ на один год."},
    {"word": "староста", "accent": "ста́роста", "full": "староста группы", "en": "class monitor", "vi": "Lớp trưởng", "example": "Староста отметила всех в журнале."},
    {"word": "медосмотр", "accent": "медосмо́тр", "full": "медицинский осмотр", "en": "medical check-up", "vi": "Khám sức khỏe định kỳ (bắt buộc)", "example": "Нужно пройти медосмотр до конца месяца."},
]


# ==============================================================================
# 4. CSS SÁNG / TỐI TƯƠNG PHẢN TUYỆT ĐỐI (TRẮNG CHỮ ĐEN · ĐEN CHỮ TRẮNG)
# ==============================================================================
def inject_theme_css(is_author_admin: bool = False, theme_mode: str = "light") -> None:
    hide_admin_chrome = ""
    if not is_author_admin:
        hide_admin_chrome = """
        [data-testid="stToolbarActions"],
        [data-testid="stAppDeployButton"],
        .stAppDeployButton,
        [data-testid="stMainMenu"],
        #MainMenu,
        [data-testid="manage-app-button"],
        .viewerBadge_container__r5tak,
        .viewerBadge_link__qRIco,
        .styles_viewerBadge__CvC9N,
        a[href*="github.com"],
        footer {
            display: none !important;
            visibility: hidden !important;
        }
        """

    if theme_mode == "dark":
        c_scheme = "dark"
        bg_page = "#0B0B0D"
        bg_surface = "#141417"
        bg_subtle = "#1C1C21"
        bg_sidebar = "#111114"
        text_main = "#FAFAFA"
        text_sub = "#A1A1AA"
        text_muted = "#71717A"
        border_light = "#27272A"
        border_strong = "#3F3F46"
        btn_pri_bg = "#FAFAFA"
        btn_pri_fg = "#0B0B0D"
        btn_pri_hover = "#E4E4E7"
        btn_sec_bg = "#18181B"
        btn_sec_fg = "#FAFAFA"
        btn_sec_hover = "#27272A"
        link_color = "#60A5FA"
    else:
        c_scheme = "light"
        bg_page = "#FAF9F6"
        bg_surface = "#FFFFFF"
        bg_subtle = "#F4F3EE"
        bg_sidebar = "#F4F3EE"
        text_main = "#18181B"
        text_sub = "#52525B"
        text_muted = "#71717A"
        border_light = "#E5E4DF"
        border_strong = "#D4D4D8"
        btn_pri_bg = "#18181B"
        btn_pri_fg = "#FFFFFF"
        btn_pri_hover = "#27272A"
        btn_sec_bg = "#FFFFFF"
        btn_sec_fg = "#18181B"
        btn_sec_hover = "#F4F3EE"
        link_color = "#1D4ED8"

    render_html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        {hide_admin_chrome}

        :root {{ color-scheme: {c_scheme} !important; }}

        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: {bg_page} !important;
            color: {text_main} !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }}

        span:not([data-testid="stIconMaterial"]):not(.material-icons),
        p, div, label, li, td, th, h1, h2, h3, h4, h5, h6 {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }}

        span[data-testid="stIconMaterial"], .material-icons {{
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        }}

        .main .block-container {{
            max-width: 960px !important;
            padding-top: 1.6rem !important;
            padding-bottom: 3rem !important;
        }}

        .main p, .main label, .main h1, .main h2, .main h3, .main h4,
        .main div[data-testid="stWidgetLabel"] p,
        .main div[data-testid="stMarkdownContainer"] p,
        .main div[data-testid="stMarkdownContainer"] li {{
            color: {text_main} !important;
        }}

        .main div[data-testid="stCaptionContainer"] p {{
            color: {text_sub} !important;
            font-size: 0.85rem !important;
        }}

        section[data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {border_light} !important;
        }}
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] li {{
            color: {text_main} !important;
        }}
        section[data-testid="stSidebar"] a {{ color: {link_color} !important; }}

        textarea, input[type="text"], input[type="password"] {{
            background-color: {bg_surface} !important;
            color: {text_main} !important;
            -webkit-text-fill-color: {text_main} !important;
            caret-color: {text_main} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            font-size: 0.98rem !important;
            line-height: 1.6 !important;
        }}
        textarea:focus, input[type="text"]:focus, input[type="password"]:focus {{
            border-color: {text_main} !important;
            box-shadow: 0 0 0 1px {text_main} !important;
        }}
        textarea::placeholder, input::placeholder {{
            color: {text_muted} !important;
            -webkit-text-fill-color: {text_muted} !important;
            opacity: 1 !important;
        }}

        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {{
            background-color: {bg_surface} !important;
            border-color: {border_strong} !important;
            border-radius: 10px !important;
        }}

        div[data-baseweb="select"] > div {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            color: {text_main} !important;
        }}
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] svg {{
            color: {text_main} !important;
            fill: {text_main} !important;
        }}
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"],
        ul[data-testid="stSelectboxVirtualDropdown"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
        }}
        div[data-baseweb="popover"] li,
        div[data-baseweb="menu"] li {{
            background-color: {bg_surface} !important;
            color: {text_main} !important;
        }}
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="menu"] li:hover {{
            background-color: {bg_subtle} !important;
        }}

        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"],
        div.stDownloadButton > button[kind="primary"] {{
            background-color: {btn_pri_bg} !important;
            color: {btn_pri_fg} !important;
            border: 1px solid {btn_pri_bg} !important;
            border-radius: 9px !important;
            padding: 0.52rem 1.15rem !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            box-shadow: none !important;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] *,
        div.stDownloadButton > button[kind="primary"] * {{
            color: {btn_pri_fg} !important;
        }}
        div.stButton > button[kind="primary"]:hover {{ background-color: {btn_pri_hover} !important; }}

        div.stButton > button[kind="secondary"],
        div.stDownloadButton > button[kind="secondary"],
        div.stFormSubmitButton > button[kind="secondary"] {{
            background-color: {btn_sec_bg} !important;
            color: {btn_sec_fg} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 9px !important;
            padding: 0.5rem 1.05rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            box-shadow: none !important;
        }}
        div.stButton > button[kind="secondary"] *,
        div.stDownloadButton > button[kind="secondary"] * {{
            color: {btn_sec_fg} !important;
        }}
        div.stButton > button[kind="secondary"]:hover,
        div.stDownloadButton > button[kind="secondary"]:hover {{ background-color: {btn_sec_hover} !important; }}

        div[data-testid="stTabs"] div[role="tablist"] {{
            gap: 6px;
            border-bottom: 1px solid {border_light} !important;
            padding-bottom: 8px;
            flex-wrap: wrap;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] {{
            background-color: transparent !important;
            border: 1px solid transparent !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            box-shadow: none !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] p {{
            color: {text_sub} !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {{ background-color: {bg_subtle} !important; }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: {btn_pri_bg} !important;
            border-color: {btn_pri_bg} !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {{
            color: {btn_pri_fg} !important;
            font-weight: 600 !important;
        }}

        div[data-testid="stExpander"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_light} !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary svg {{
            color: {text_main} !important;
            fill: {text_main} !important;
            font-weight: 500 !important;
        }}
        div[data-testid="stFileUploader"] section {{
            background-color: {bg_surface} !important;
            border: 1px dashed {border_strong} !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stFileUploader"] section *,
        div[data-testid="stFileUploader"] small {{ color: {text_main} !important; }}
        div[data-testid="stFileUploader"] button {{
            background-color: {bg_subtle} !important;
            color: {text_main} !important;
            border: 1px solid {border_strong} !important;
        }}

        .minimal-header {{
            padding-bottom: 16px;
            margin-bottom: 18px;
            border-bottom: 1px solid {border_light};
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 14px;
        }}
        .minimal-title {{
            font-size: 1.55rem; font-weight: 700; letter-spacing: -0.025em;
            color: {text_main}; margin: 0; line-height: 1.2;
        }}
        .minimal-sub {{ font-size: 0.88rem; color: {text_sub}; margin-top: 3px; }}
        .author-chip {{
            display: flex; align-items: center; gap: 11px;
            background: {bg_surface}; border: 1px solid {border_light};
            border-radius: 999px; padding: 6px 14px 6px 6px;
        }}
        .author-chip-img {{
            width: 40px; height: 40px; border-radius: 50%; object-fit: cover;
            border: 1px solid {border_strong}; flex-shrink: 0;
        }}
        .author-chip-name {{ font-size: 0.86rem; font-weight: 600; color: {text_main}; line-height: 1.25; }}
        .author-chip-role {{ font-size: 0.76rem; color: {text_sub}; line-height: 1.25; }}

        .sidebar-author-box {{
            display: flex; align-items: center; gap: 12px;
            background: {bg_surface}; border: 1px solid {border_light}; border-radius: 12px;
            padding: 12px; margin-bottom: 14px;
        }}
        .sidebar-author-img {{
            width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
            border: 1px solid {border_strong}; flex-shrink: 0;
        }}

        .clean-card {{
            background-color: {bg_surface};
            border: 1px solid {border_light};
            border-radius: 12px;
            padding: 18px 20px;
            margin-top: 14px;
            margin-bottom: 14px;
        }}
        .clean-label {{
            font-size: 0.82rem; font-weight: 600; color: {text_sub}; margin-bottom: 8px;
            display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;
        }}
        .clean-result-text {{
            font-size: 1.07rem; line-height: 1.72; color: {text_main}; font-weight: 500;
            white-space: pre-wrap; word-break: break-word;
        }}
        .example-row {{ padding: 11px 0; border-bottom: 1px solid {border_light}; }}
        .example-row:last-child {{ border-bottom: none; padding-bottom: 2px; }}
        .example-ru {{ font-size: 1.0rem; font-weight: 600; color: {text_main}; line-height: 1.5; }}
        .example-vi {{ font-size: 0.91rem; color: {text_sub}; margin-top: 3px; line-height: 1.5; }}
        .example-tag {{
            display: inline-block; font-size: 0.75rem; font-weight: 500; color: {text_sub};
            background: {bg_subtle}; padding: 2px 8px; border-radius: 6px; margin-bottom: 4px;
        }}

        .syn-ant-item {{
            padding: 7px 0; border-bottom: 1px solid {border_light};
            font-size: 0.92rem; color: {text_main}; line-height: 1.45;
        }}
        .syn-ant-item:last-child {{ border-bottom: none; }}

        .clean-table {{ width: 100%; border-collapse: collapse; font-size: 0.91rem; margin-top: 6px; }}
        .clean-table th {{
            text-align: left; padding: 9px 12px; border-bottom: 1px solid {border_strong};
            color: {text_sub}; font-weight: 600; background-color: {bg_subtle};
        }}
        .clean-table td {{
            padding: 9px 12px; border-bottom: 1px solid {border_light}; color: {text_main};
            vertical-align: top; line-height: 1.5;
        }}

        .note-callout {{
            background-color: {bg_subtle}; border-left: 3px solid {text_main}; border-radius: 0 8px 8px 0;
            padding: 12px 16px; margin-top: 12px; font-size: 0.91rem; color: {text_main}; line-height: 1.62;
        }}

        .flashcard-minimal {{
            background-color: {bg_surface}; border: 1px solid {border_strong}; border-radius: 14px;
            padding: 36px 24px; text-align: center; margin: 12px 0;
        }}
        .flashcard-word {{ font-size: 1.72rem; font-weight: 700; color: {text_main}; letter-spacing: -0.02em; }}
        .flashcard-back {{
            margin-top: 16px; padding-top: 16px; border-top: 1px solid {border_light};
            font-size: 1.1rem; font-weight: 600; color: {text_main};
        }}

        .stat-grid {{
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 10px 0 14px 0;
        }}
        .stat-box {{
            background: {bg_surface}; border: 1px solid {border_light}; border-radius: 10px;
            padding: 12px 14px; text-align: center;
        }}
        .stat-num {{ font-size: 1.35rem; font-weight: 700; color: {text_main}; }}
        .stat-lbl {{ font-size: 0.78rem; color: {text_sub}; margin-top: 2px; }}

        @media (max-width: 768px) {{
            .main .block-container {{ padding: 1rem 0.85rem 2.5rem 0.85rem !important; }}
            .minimal-title {{ font-size: 1.32rem; }}
            .clean-card {{ padding: 14px 15px; }}
        }}
        </style>
        """
    )


# ==============================================================================
# 5. PHÂN LOẠI ĐẦU VÀO, NHẬN DIỆN CHIỀU DỊCH CHUẨN & ĐỘNG CƠ DỊCH API SIÊU TỐC
# ==============================================================================
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
def generate_tts_audio(text: str, lang_code: str) -> Optional[bytes]:
    cleaned_text = text.strip()
    if not cleaned_text or gTTS is None:
        return None
    try:
        tts = gTTS(text=cleaned_text[:650], lang=lang_code, slow=False)
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

    pinned = st.session_state.get("pinned_gemini_model", "")
    models = ([pinned] + [m for m in discovered if m != pinned]) if (pinned and pinned in discovered) else discovered
    last_error = ""

    for model_name in models[:5]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
        gen_cfg: Dict[str, Any] = {
            "temperature": temperature,
            "responseMimeType": "application/json",
        }
        if "2.5" in model_name:
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
    api_key: str, source_text: str, effective_dir: str
) -> Tuple[Optional[Dict], Optional[str], float, str]:
    t0 = time.perf_counter()
    input_kind = classify_input_type(source_text)

    ai_cache = _get_lru_cache("gemini_result_cache")
    cache_key = hashlib.sha256(f"{effective_dir}::{input_kind}::{source_text.strip()}".encode("utf-8")).hexdigest()
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

    system_prompt = f"""
Bạn là giáo sư ngôn ngữ học Nga – Việt chuyên sâu dịch thuật và thuật ngữ đại học.
{dir_rule}
{task_instruction}
CHỈ TRẢ VỀ đúng 1 JSON hợp lệ:
{{
  "main_translation": "",
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


# ==============================================================================
# 6. CẨM NANG KIẾN THỨC TIẾNG NGA CHI TIẾT (7 CHUYÊN ĐỀ · TAB 3)
# ==============================================================================
def render_russian_knowledge_hub() -> None:
    topic = st.radio(
        "Chọn chuyên đề",
        options=[
            "1. 6 Cách · Danh từ",
            "2. Tính từ & Đại từ",
            "3. Động từ & Thể (НСВ/СВ)",
            "4. Động từ chuyển động",
            "5. Giới từ & Thời gian",
            "6. Số từ & Lượng từ",
            "7. Câu ghép & Từ nối",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    if topic == "1. 6 Cách · Danh từ":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Tổng quan 6 cách trong tiếng Nga (Падежи)</span><span>Nền tảng cốt lõi</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Câu hỏi</th><th>Chức năng chính</th><th>Giới từ hay gặp</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>1. Именительный</b><br/>Nguyên cách</td><td>Кто? Что?</td><td>Chủ ngữ, định nghĩa, dạng gốc trong từ điển</td><td>Không có</td><td><b>Студе́нт</b> у́чится. <b>Кни́га</b> на столе́.</td></tr>
                        <tr><td><b>2. Родительный</b><br/>Sở hữu cách</td><td>Кого́? Чего́?</td><td>Sở hữu (của ai), phủ định (нет), số lượng (2–4 số ít; ≥5 số nhiều), xuất phát</td><td>у, без, до, из, с, от, о́коло, по́сле, для, кро́ме</td><td>Нет <b>вре́мени</b>. Два <b>студе́нта</b>. Из <b>Росси́и</b>.</td></tr>
                        <tr><td><b>3. Дательный</b><br/>Tặng cách</td><td>Кому́? Чему́?</td><td>Người nhận (cho ai), tuổi tác, trạng thái/cảm xúc (мне ну́жно), đối tượng hướng tới</td><td>к, по, благодаря́, вопреки́</td><td>Помога́ю <b>дру́гу</b>. <b>Мне</b> 21 год. По <b>пла́ну</b>.</td></tr>
                        <tr><td><b>4. Винительный</b><br/>Đối cách</td><td>Кого́? Что?</td><td>Tân ngữ trực tiếp (đọc gì, gặp ai), hướng chuyển động (куда́?), thứ trong tuần</td><td>в, на (hướng đi), че́рез, за, про</td><td>Чита́ю <b>кни́гу</b>. Иду́ в <b>университе́т</b>. В <b>сре́ду</b>.</td></tr>
                        <tr><td><b>5. Творительный</b><br/>Công cụ cách</td><td>Кем? Чем?</td><td>Công cụ (bằng gì), đi cùng ai (с кем?), nghề nghiệp (стать/рабо́тать), bị động</td><td>с, над, под, пе́ред, за, ме́жду</td><td>Пишу́ <b>ру́чкой</b>. Ко́фе с <b>молоко́м</b>. Ста́ну <b>инжене́ром</b>.</td></tr>
                        <tr><td><b>6. Предложный</b><br/>Giới cách</td><td>О ком? О чём? Где?</td><td>Vị trí tĩnh (ở đâu?), chủ đề (nói/nghĩ về gì), tháng/năm, phương tiện (на метро́)</td><td>в, на (vị trí), о (об), при</td><td>Живу́ в <b>Петербу́рге</b>. Ду́маю об <b>экза́мене</b>.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Bảng đuôi Danh từ Số ít &amp; Số nhiều</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Đực (ø/-й/-ь)</th><th>Cái (-а/-я/-ь)</th><th>Trung (-о/-е/-ие)</th><th>Số nhiều (Мн. ч.)</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>ø / -й / -ь</td><td>-а / -я / -ь</td><td>-о / -е / -ие</td><td>-ы / -и · -а / -я</td></tr>
                        <tr><td><b>2</b></td><td>-а / -я / -я</td><td>-ы(-и) / -и / -и</td><td>-а / -я / -ия</td><td><b>-ов/-ев · -ей · ø · -ий</b></td></tr>
                        <tr><td><b>3</b></td><td>-у / -ю / -ю</td><td>-е (-и) / -и</td><td>-у / -ю / -ию</td><td>-ам / -ям</td></tr>
                        <tr><td><b>4</b></td><td>Vật=C1 · Người=C2</td><td>-у / -ю / -ь</td><td>Giống C1</td><td>Vật=C1 · Người=C2</td></tr>
                        <tr><td><b>5</b></td><td>-ом / -ем / -ем</td><td>-ой / -ей / -ью</td><td>-ом / -ем / -ием</td><td>-ами / -ями</td></tr>
                        <tr><td><b>6</b></td><td>-е (-ии)</td><td>-е (-ии/-и)</td><td>-е (-ии)</td><td>-ах / -ях</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Quy tắc 7 chữ cái (г, к, х, ж, ч, ш, щ):</b> Không bao giờ viết «ы», luôn đổi thành «и» (кни́га → кни́ги).<br/>
                    <b>Quy tắc 5 chữ cái (ж, ч, ш, щ, ц):</b> Không có trọng âm thì viết «е» thay cho «о» (това́рищем, хоро́шего).
                </div>
            </div>
            """
        )

    elif topic == "2. Tính từ & Đại từ":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Biến cách Tính từ theo 6 cách</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Giống đực</th><th>Giống trung</th><th>Giống cái</th><th>Số nhiều</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>-ый / -ой / -ий</td><td>-ое / -ее</td><td>-ая / -яя</td><td>-ые / -ие</td></tr>
                        <tr><td><b>2</b></td><td>-ого / -его</td><td>-ого / -его</td><td>-ой / -ей</td><td>-ых / -их</td></tr>
                        <tr><td><b>3</b></td><td>-ому / -ему</td><td>-ому / -ему</td><td>-ой / -ей</td><td>-ым / -им</td></tr>
                        <tr><td><b>4</b></td><td>Vật=C1 · Người=C2</td><td>-ое / -ее</td><td>-ую / -юю</td><td>Vật=C1 · Người=C2</td></tr>
                        <tr><td><b>5</b></td><td>-ым / -им</td><td>-ым / -им</td><td>-ой / -ей</td><td>-ыми / -ими</td></tr>
                        <tr><td><b>6</b></td><td>-ом / -ем</td><td>-ом / -ем</td><td>-ой / -ей</td><td>-ых / -их</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>6 Cách của Đại từ nhân xưng</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>я</th><th>ты</th><th>он / оно́</th><th>она́</th><th>мы</th><th>вы</th><th>они́</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>я</td><td>ты</td><td>он / оно́</td><td>она́</td><td>мы</td><td>вы</td><td>они́</td></tr>
                        <tr><td><b>2</b></td><td>меня́</td><td>тебя́</td><td>его́ (него́)</td><td>её (неё)</td><td>нас</td><td>вас</td><td>их (них)</td></tr>
                        <tr><td><b>3</b></td><td>мне</td><td>тебе́</td><td>ему́ (нему́)</td><td>ей (ней)</td><td>нам</td><td>вам</td><td>им (ним)</td></tr>
                        <tr><td><b>4</b></td><td>меня́</td><td>тебя́</td><td>его́ (него́)</td><td>её (неё)</td><td>нас</td><td>вас</td><td>их (них)</td></tr>
                        <tr><td><b>5</b></td><td>мной</td><td>тобо́й</td><td>им (ним)</td><td>ей (ней)</td><td>на́ми</td><td>ва́ми</td><td>и́ми (ни́ми)</td></tr>
                        <tr><td><b>6</b></td><td>обо мне</td><td>о тебе́</td><td>о нём</td><td>о ней</td><td>о нас</td><td>о вас</td><td>о них</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "3. Động từ & Thể (НСВ/СВ)":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Chia động từ Nhóm I &amp; Nhóm II · Biến âm · Thể НСВ / СВ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Ngôi</th><th>Nhóm I (-ать, -ять, -еть · чита́ть)</th><th>Nhóm II (-ить · говори́ть)</th></tr></thead>
                    <tbody>
                        <tr><td><b>я</b></td><td>-у / -ю (чита́ю)</td><td>-у / -ю (говорю́)</td></tr>
                        <tr><td><b>ты</b></td><td>-ешь / -ёшь (чита́ешь)</td><td>-ишь (говори́шь)</td></tr>
                        <tr><td><b>он / она́ / оно́</b></td><td>-ет / -ёт (чита́ет)</td><td>-ит (говори́т)</td></tr>
                        <tr><td><b>мы</b></td><td>-ем / -ём (чита́ем)</td><td>-им (говори́м)</td></tr>
                        <tr><td><b>вы</b></td><td>-ете / -ёте (чита́ете)</td><td>-ите (говори́те)</td></tr>
                        <tr><td><b>они́</b></td><td>-ут / -ют (чита́ют)</td><td>-ат / -ят (говоря́т)</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Biến âm ở ngôi «я»:</b> д→ж (ви́жу), т→ч (плачу́), с→ш (пишу́), б/п/в/м→бл/пл/вл/мл (люблю́, гото́влю).<br/>
                    <b>НСВ</b> = quá trình, lặp lại (ка́ждый день, до́лго) · <b>СВ</b> = kết quả dứt điểm 1 lần (уже́, наконе́ц; không có thì hiện tại).
                </div>
            </div>
            """
        )

    elif topic == "4. Động từ chuyển động":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Động từ chuyển động (1 chiều vs Đa chiều) &amp; Tiền tố</span></div>
                <table class="clean-table">
                    <thead><tr><th>Nghĩa</th><th>1 hướng / Đang đi</th><th>Khứ hồi / Thói quen</th><th>Tiền tố hay gặp</th></tr></thead>
                    <tbody>
                        <tr><td><b>Đi bộ</b></td><td>идти́ (иду́, идёшь)</td><td>ходи́ть (хожу́, хо́дишь)</td><td>при- (đến), у- (đi khỏi)</td></tr>
                        <tr><td><b>Đi xe / tàu</b></td><td>е́хать (е́ду, е́дешь)</td><td>е́здить (е́зжу, е́здишь)</td><td>в-/во- (vào), вы- (ra)</td></tr>
                        <tr><td><b>Mang (đi bộ)</b></td><td>нести́</td><td>носи́ть</td><td>под- (lại gần), от- (rời xa)</td></tr>
                        <tr><td><b>Chở (xe)</b></td><td>везти́</td><td>вози́ть</td><td>пере- (sang ngang), за- (ghé qua)</td></tr>
                        <tr><td><b>Bay</b></td><td>лете́ть</td><td>лета́ть</td><td>до- (tới đích), про- (đi qua)</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "5. Giới từ & Thời gian":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Giới từ địa điểm (В/НА · ИЗ/С · У/К/ОТ) &amp; Thời gian</span></div>
                <table class="clean-table">
                    <thead><tr><th>Где? (C6)</th><th>Куда́? (C4)</th><th>Отку́да? (C2)</th><th>Bắt buộc dùng «НА»</th></tr></thead>
                    <tbody>
                        <tr><td><b>в</b> + C6</td><td><b>в</b> + C4</td><td><b>из</b> + C2</td><td rowspan="3">на факульте́те, на ка́федре, на ку́рсе, на ле́кции, на экза́мене, на пра́ктике, на рабо́те, на по́чте, на вокза́ле, на заво́де</td></tr>
                        <tr><td><b>на</b> + C6</td><td><b>на</b> + C4</td><td><b>с</b> + C2</td></tr>
                        <tr><td><b>у</b> + C2</td><td><b>к</b> + C3</td><td><b>от</b> + C2</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Thời gian:</b> Thứ (<b>в</b> + C4: в сре́ду) · Tháng (<b>в</b> + C6: в ноябре́) · Ngày (Số thứ tự + Tháng đều <b>C2</b>: пе́рвого сентября́) · Bao lâu nữa (<b>че́рез</b> + C4) · Trước đây (C4 + <b>наза́д</b>).
                </div>
            </div>
            """
        )

    elif topic == "6. Số từ & Lượng từ":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Quy tắc ghép Số đếm với Danh từ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Số tận cùng</th><th>Cách của Danh từ</th><th>рубль</th><th>год</th><th>час</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b> (trừ 11)</td><td>Cách 1 số ít</td><td>оди́н рубль</td><td>оди́н год</td><td>оди́н час</td></tr>
                        <tr><td><b>2, 3, 4</b> (trừ 12–14)</td><td>Cách 2 số ít</td><td>два рубля́</td><td>три го́да</td><td>четы́ре часа́</td></tr>
                        <tr><td><b>5–20, 0, мно́го, ма́ло</b></td><td>Cách 2 số nhiều</td><td>пять рубле́й</td><td>пять <b>лет</b></td><td>пять часо́в</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    else:
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Cấu trúc câu ghép &amp; Từ nối học thuật</span></div>
                <table class="clean-table">
                    <thead><tr><th>Từ nối</th><th>Quy tắc</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>что́бы</b></td><td>Cùng chủ ngữ: nguyên thể · Khác chủ ngữ: <b>Quá khứ</b></td><td>Я хочу́, что́бы ты <b>пришёл</b>.</td></tr>
                        <tr><td><b>кото́рый</b></td><td>Giống &amp; số theo danh từ trước; Cách theo mệnh đề sau</td><td>Кни́га, <b>кото́рую</b> я чита́ю (C4).</td></tr>
                        <tr><td><b>благодаря́ / из-за</b></td><td>благодаря́ + C3 (nhờ vào) · из-за + C2 (tại vì)</td><td>Благодаря́ по́мощи · Из-за дождя́.</td></tr>
                        <tr><td><b>несмотря́ на</b></td><td>+ Cách 4 (mặc dù)</td><td>Несмотря́ на сло́жность зада́чи...</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )


# ==============================================================================
# 7. TỪ VỰNG & ÔN TẬP ĐỒNG BỘ TÀI KHOẢN (FLASHCARDS + QUIZ 2 CHIỀU + CSV IMPORT/EXPORT)
# ==============================================================================
def add_vocab_items_to_notebook(items: List[Dict[str, str]]) -> int:
    if "saved_vocab_notebook" not in st.session_state:
        st.session_state["saved_vocab_notebook"] = []
    existing = {v["ru_accent"].lower() for v in st.session_state["saved_vocab_notebook"]}
    added = 0
    for it in items:
        ru_k = str(it.get("ru_accent", "")).strip()
        if ru_k and ru_k.lower() not in existing:
            st.session_state["saved_vocab_notebook"].insert(
                0,
                {
                    "ru_accent": ru_k,
                    "en": str(it.get("en", "")).strip(),
                    "vi": str(it.get("vi", "")).strip(),
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
    writer.writerow(["Tieng_Nga", "Tieng_Viet", "Tieng_Anh"])
    for item in vocab_list:
        writer.writerow([item.get("ru_accent", ""), item.get("vi", ""), item.get("en", "")])
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _generate_quiz_question(pool: List[Dict[str, Any]], quiz_dir: str = "ru_to_vi") -> Optional[Dict[str, Any]]:
    if len(pool) < 4:
        return None
    target = random.choice(pool)
    distractors = random.sample([x for x in pool if x["ru_accent"] != target["ru_accent"]], 3)
    if quiz_dir == "vi_to_ru":
        options = [target["ru_accent"]] + [d["ru_accent"] for d in distractors]
        random.shuffle(options)
        return {
            "prompt": target["vi"],
            "correct": target["ru_accent"],
            "sub_hint": "Chọn từ tiếng Nga tương ứng:",
            "options": options,
            "answered": None,
        }
    options = [target["vi"]] + [d["vi"] for d in distractors]
    random.shuffle(options)
    return {
        "prompt": target["ru_accent"],
        "correct": target["vi"],
        "sub_hint": "Chọn nghĩa tiếng Việt đúng:",
        "options": options,
        "answered": None,
    }


def render_vocab_and_practice_tab() -> None:
    saved_list = st.session_state["saved_vocab_notebook"]
    mastered_cnt = sum(1 for v in saved_list if v.get("mastered"))
    unmastered_cnt = len(saved_list) - mastered_cnt
    pct = int(round((mastered_cnt / len(saved_list)) * 100)) if saved_list else 0

    if not st.session_state.get("auth_username"):
        st.info("Đăng nhập hoặc tạo tài khoản ở thanh bên trái để lưu vĩnh viễn và đồng bộ Sổ từ vựng + Lịch sử trên mọi thiết bị.")

    render_html(
        f"""
        <div class="stat-grid">
            <div class="stat-box"><div class="stat-num">{len(saved_list)}</div><div class="stat-lbl">Tổng từ trong sổ</div></div>
            <div class="stat-box"><div class="stat-num">{mastered_cnt}</div><div class="stat-lbl">Đã thuộc ({pct}%)</div></div>
            <div class="stat-box"><div class="stat-num">{unmastered_cnt}</div><div class="stat-lbl">Cần ôn lại</div></div>
        </div>
        """
    )

    mode = st.radio(
        "Chế độ học từ vựng",
        options=["Thẻ ghi nhớ (Flashcards)", "Trắc nghiệm (Quiz)", "Quản lý sổ & Tiếng lóng"],
        horizontal=True,
        label_visibility="collapsed",
    )

    slang_deck = [
        {"ru_accent": f"{x['accent']} ({x['full']})", "vi": x["vi"], "en": x["en"], "mastered": False}
        for x in RUSSIAN_SLANG_DICT
    ]

    if mode == "Thẻ ghi nhớ (Flashcards)":
        fc1, fc2 = st.columns([2.2, 1])
        with fc1:
            deck_choice = st.selectbox(
                "Bộ thẻ",
                options=["Từ chưa thuộc trong sổ", "Tất cả từ trong sổ", "30 từ lóng sinh viên Nga"],
                label_visibility="collapsed",
            )
        with fc2:
            if st.button("Xáo trộn thẻ", use_container_width=True):
                if saved_list:
                    random.shuffle(saved_list)
                st.session_state["flashcard_index"] = 0
                st.session_state["flashcard_show_back"] = False
                st.rerun()

        if deck_choice == "Từ chưa thuộc trong sổ":
            active_deck = [v for v in saved_list if not v.get("mastered")]
        elif deck_choice == "Tất cả từ trong sổ":
            active_deck = saved_list
        else:
            active_deck = slang_deck

        if not active_deck:
            st.info("Không có thẻ nào trong bộ này. Hãy lưu từ ở Tab 1, hoặc chọn bộ «30 từ lóng sinh viên Nga».")
            return

        idx = st.session_state["flashcard_index"] % len(active_deck)
        card = active_deck[idx]
        status_tag = " · Đã thuộc" if card.get("mastered") else ""

        back_html = (
            f'<div class="flashcard-back">{esc(card["vi"])}<div style="font-size:0.9rem;opacity:0.75;font-weight:400;margin-top:4px;">{esc(card.get("en",""))}</div></div>'
            if st.session_state["flashcard_show_back"]
            else '<div style="margin-top:12px;font-size:0.86rem;opacity:0.7;">Bấm «Lật thẻ» để xem nghĩa</div>'
        )
        render_html(
            f"""
            <div class="flashcard-minimal">
                <div style="font-size:0.8rem;opacity:0.7;margin-bottom:8px;">Thẻ {idx + 1} / {len(active_deck)}{status_tag}</div>
                <div class="flashcard-word">{esc(card["ru_accent"])}</div>
                {back_html}
            </div>
            """
        )

        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            if st.button("Trước", use_container_width=True):
                st.session_state["flashcard_index"] = (idx - 1) % len(active_deck)
                st.session_state["flashcard_show_back"] = False
                st.rerun()
        with b2:
            if st.button("Lật thẻ", type="primary", use_container_width=True):
                st.session_state["flashcard_show_back"] = not st.session_state["flashcard_show_back"]
                st.rerun()
        with b3:
            if st.button("Phát âm", use_container_width=True):
                ru_clean = card["ru_accent"].split("(")[0].replace("\u0301", "").strip()
                ab = generate_tts_audio(ru_clean, "ru")
                if ab:
                    st.audio(ab, format="audio/mp3")
        with b4:
            if deck_choice != "30 từ lóng sinh viên Nga":
                lbl = "Ôn lại" if card.get("mastered") else "Đã thuộc ✓"
                if st.button(lbl, use_container_width=True):
                    for item in saved_list:
                        if item["ru_accent"] == card["ru_accent"]:
                            item["mastered"] = not item.get("mastered", False)
                            break
                    sync_current_account_to_db()
                    st.session_state["flashcard_show_back"] = False
                    st.rerun()
            else:
                if st.button("Lưu vào sổ", use_container_width=True):
                    add_vocab_items_to_notebook([card])
                    st.toast("Đã lưu vào sổ từ vựng.")
        with b5:
            if st.button("Tiếp", use_container_width=True):
                st.session_state["flashcard_index"] = (idx + 1) % len(active_deck)
                st.session_state["flashcard_show_back"] = False
                st.rerun()

    elif mode == "Trắc nghiệm (Quiz)":
        qc1, qc2 = st.columns([2, 1.5])
        with qc1:
            quiz_dir_label = st.radio(
                "Chiều kiểm tra",
                options=["Nga → Việt", "Việt → Nga"],
                horizontal=True,
                label_visibility="collapsed",
            )
            q_dir = "vi_to_ru" if quiz_dir_label == "Việt → Nga" else "ru_to_vi"
        with qc2:
            st.caption(f"Điểm: **{st.session_state['quiz_score']} / {st.session_state['quiz_total']}**")

        unmastered_pool = [v for v in saved_list if not v.get("mastered")]
        pool = unmastered_pool if len(unmastered_pool) >= 4 else (saved_list if len(saved_list) >= 4 else slang_deck)

        if st.session_state.get("current_quiz") is None or st.session_state.get("last_quiz_dir") != q_dir:
            st.session_state["last_quiz_dir"] = q_dir
            st.session_state["current_quiz"] = _generate_quiz_question(pool, q_dir)

        q = st.session_state["current_quiz"]
        if q:
            render_html(
                f"""
                <div class="clean-card" style="text-align:center;padding:24px;">
                    <div style="font-size:0.82rem;opacity:0.7;margin-bottom:6px;">{esc(q['sub_hint'])}</div>
                    <div style="font-size:1.55rem;font-weight:700;">{esc(q['prompt'])}</div>
                </div>
                """
            )
            for opt_i, opt in enumerate(q["options"]):
                if st.button(opt, key=f"quiz_opt_{opt_i}", use_container_width=True, disabled=q["answered"] is not None):
                    q["answered"] = opt
                    st.session_state["quiz_total"] += 1
                    if opt == q["correct"]:
                        st.session_state["quiz_score"] += 1
                    st.rerun()

            if q["answered"] is not None:
                if q["answered"] == q["correct"]:
                    st.success(f"Chính xác: {q['prompt']} = {q['correct']}")
                else:
                    st.error(f"Chưa đúng. Đáp án đúng là: {q['correct']}")
                if st.button("Câu tiếp theo", type="primary"):
                    st.session_state["current_quiz"] = _generate_quiz_question(pool, q_dir)
                    st.rerun()

    else:
        col_left, col_right = st.columns([1.1, 1.0])
        with col_left:
            st.markdown("#### Sổ từ vựng cá nhân")
            with st.expander("Thêm từ thủ công hoặc nhập từ file CSV"):
                with st.form("add_manual_vocab", clear_on_submit=True):
                    m_ru = st.text_input("Tiếng Nga (kèm trọng âm)", placeholder="VD: осто́йчивость")
                    m_vi = st.text_input("Nghĩa tiếng Việt", placeholder="VD: Tính ổn định (của tàu)")
                    m_en = st.text_input("Tiếng Anh (tùy chọn)", placeholder="VD: stability")
                    if st.form_submit_button("Thêm vào sổ", type="primary", use_container_width=True):
                        if m_ru.strip() and m_vi.strip():
                            add_vocab_items_to_notebook([{"ru_accent": m_ru.strip(), "vi": m_vi.strip(), "en": m_en.strip()}])
                            st.toast("Đã thêm và đồng bộ từ mới.")
                            st.rerun()
                csv_up = st.file_uploader("Nhập danh sách từ file CSV (cột: Tiếng Nga, Tiếng Việt)", type=["csv"])
                if csv_up is not None and st.button("Nhập từ CSV vào sổ", use_container_width=True):
                    try:
                        decoded = csv_up.getvalue().decode("utf-8-sig")
                        reader = csv.reader(io.StringIO(decoded))
                        new_items = []
                        for r_idx, row in enumerate(reader):
                            if len(row) >= 2 and not (r_idx == 0 and "tieng_nga" in row[0].lower()):
                                new_items.append({"ru_accent": row[0].strip(), "vi": row[1].strip(), "en": row[2].strip() if len(row) > 2 else ""})
                        cnt = add_vocab_items_to_notebook(new_items)
                        st.toast(f"Đã nhập {cnt} từ mới từ CSV.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Lỗi đọc CSV: {exc}")

            if saved_list:
                q_my = st.text_input("Tìm trong sổ của bạn", placeholder="Gõ tiếng Nga hoặc tiếng Việt...", label_visibility="collapsed")
                filtered_my = [
                    (i, v) for i, v in enumerate(saved_list)
                    if not q_my.strip() or q_my.lower() in v["ru_accent"].lower() or q_my.lower() in v["vi"].lower()
                ]
                st.download_button(
                    f"Xuất {len(saved_list)} từ ra CSV (Anki / Excel)",
                    data=export_vocab_to_anki_csv(saved_list),
                    file_name="tu_vung_anki.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                for orig_i, v in filtered_my[:25]:
                    rc1, rc2, rc3 = st.columns([3.6, 1.2, 0.7])
                    with rc1:
                        st.markdown(f"**{v['ru_accent']}** — {v['vi']}")
                    with rc2:
                        st_lbl = "Đã thuộc" if v.get("mastered") else "Chưa thuộc"
                        if st.button(st_lbl, key=f"tog_v_{orig_i}", use_container_width=True):
                            saved_list[orig_i]["mastered"] = not v.get("mastered", False)
                            sync_current_account_to_db()
                            st.rerun()
                    with rc3:
                        if st.button("×", key=f"del_v_{orig_i}", use_container_width=True):
                            saved_list.pop(orig_i)
                            sync_current_account_to_db()
                            st.rerun()
            else:
                st.caption("Sổ từ vựng đang trống. Hãy lưu từ sau khi tra ở Tab 1 hoặc thêm thủ công.")

        with col_right:
            st.markdown("#### Tra nhanh 30 từ lóng sinh viên Nga")
            q_slang = st.text_input("Tìm từ lóng", placeholder="препод, курсач, хвост, инфа...", label_visibility="collapsed")
            filtered = [
                x for x in RUSSIAN_SLANG_DICT
                if not q_slang.strip()
                or q_slang.lower() in x["word"].lower()
                or q_slang.lower() in x["vi"].lower()
                or q_slang.lower() in x["full"].lower()
            ]
            rows = "".join(
                f"<tr><td><b>{esc(x['accent'])}</b><br/><span style='font-size:0.8rem;opacity:0.7;'>{esc(x['full'])}</span></td><td>{esc(x['vi'])}</td></tr>"
                for x in filtered
            )
            render_html(
                f"""
                <div class="clean-card" style="padding:0;max-height:420px;overflow-y:auto;">
                    <table class="clean-table" style="margin-top:0;">
                        <thead><tr><th>Tiếng Nga</th><th>Nghĩa tiếng Việt</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """
            )


# ==============================================================================
# 8. HIỂN THỊ KẾT QUẢ DỊCH & KHỞI TẠO PHIÊN ĐĂNG NHẬP BỀN VỮNG
# ==============================================================================
def init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "auth_username": "",
        "auth_password_hash": "",
        "input_text_area": "",
        "selected_direction": DIRECTION_OPTIONS[0],
        "is_author_admin": False,
        "saved_gemini_api_key": "",
        "theme_mode": "light",
        "translation_history": [],
        "saved_vocab_notebook": [],
        "flashcard_index": 0,
        "flashcard_show_back": False,
        "current_quiz": None,
        "last_quiz_dir": "ru_to_vi",
        "quiz_score": 0,
        "quiz_total": 0,
        "last_meta_badge": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # TỰ ĐỘNG KHÔI PHỤC TÀI KHOẢN QUA MỌI LẦN F5 BẰNG TOKEN ĐÃ KÝ HMAC TRÊN ?s=...
    if not st.session_state["auth_username"]:
        try:
            tok = str(st.query_params.get("s", "")).strip()
            if tok:
                uname = verify_session_token(tok)
                if uname:
                    user_payload = db_get_user(uname)
                    if user_payload:
                        apply_user_payload_to_session(uname, user_payload)
        except Exception:
            pass


def render_translation_result(res: Dict[str, Any], meta_badge: str, is_dark: bool = False) -> None:
    kind_labels = {"word": "Tra từ", "sentence": "Phân tích câu", "paragraph": "Dịch đoạn văn"}
    kind_text = kind_labels.get(res.get("input_kind", ""), "Bản dịch")
    eff_dir = res.get("effective_dir", "")
    header_left = f"{kind_text} · {eff_dir}" if eff_dir else kind_text
    main_trans = res.get("main_translation", "")

    render_html(
        f"""
        <div class="clean-card">
            <div class="clean-label">
                <span>{esc(header_left)}</span>
                <span>{esc(meta_badge)}</span>
            </div>
            <div class="clean-result-text">{esc(main_trans)}</div>
        </div>
        """
    )

    c_act1, c_act2, _ = st.columns([1.2, 1.3, 4.5])
    with c_act1:
        render_copy_button(main_trans, "Sao chép", "main_cp", is_dark=is_dark)
    with c_act2:
        tts_lang = "ru" if re.search(r"[а-яА-ЯёЁ]", main_trans) else "vi"
        if st.button("Nghe bản dịch", key="tts_main_btn", use_container_width=True):
            audio_b = generate_tts_audio(main_trans.replace("\u0301", ""), tts_lang)
            if audio_b:
                st.audio(audio_b, format="audio/mp3")

    morph = res.get("morphology") or {}
    cases_table = morph.get("cases_table") or []
    verb_conj = morph.get("verb_conjugation") or {}
    usage_note = morph.get("usage_note", "")

    if cases_table or verb_conj or usage_note:
        meta_parts = [p for p in (morph.get("word_type"), morph.get("lemma"), morph.get("aspect_or_gender")) if p]
        meta_line = " · ".join(meta_parts)

        if verb_conj:
            v_rows = "".join(
                f"<tr><td style='width:34%;'><b>{esc(k)}</b></td><td>{esc(v)}</td></tr>"
                for k, v in verb_conj.items() if v
            )
            render_html(
                f"""
                <div class="clean-card">
                    <div class="clean-label">
                        <span>Chia động từ theo các ngôi</span>
                        <span>{esc(meta_line)}</span>
                    </div>
                    <table class="clean-table">
                        <thead><tr><th>Ngôi / Thì</th><th>Dạng chia</th></tr></thead>
                        <tbody>{v_rows}</tbody>
                    </table>
                </div>
                """
            )
        elif cases_table:
            c_rows = "".join(
                f"<tr><td><b>{esc(row.get('case',''))}</b></td><td>{esc(row.get('singular','—'))}</td><td>{esc(row.get('plural','—'))}</td></tr>"
                for row in cases_table
            )
            render_html(
                f"""
                <div class="clean-card">
                    <div class="clean-label">
                        <span>Biến cách theo 6 cách tiếng Nga</span>
                        <span>{esc(meta_line)}</span>
                    </div>
                    <table class="clean-table">
                        <thead><tr><th>6 Cách (Падежи)</th><th>Số ít (Ед. ч.)</th><th>Số nhiều (Мн. ч.)</th></tr></thead>
                        <tbody>{c_rows}</tbody>
                    </table>
                </div>
                """
            )
        if usage_note:
            render_html(f'<div class="note-callout"><b>Cách dùng ({esc(meta_line)}):</b> {esc(usage_note)}</div>')

    synonyms = res.get("synonyms") or []
    antonyms = res.get("antonyms") or []
    if synonyms or antonyms:
        sa_c1, sa_c2 = st.columns(2)
        with sa_c1:
            if synonyms:
                s_items = "".join(f"<div class='syn-ant-item'><b>{esc(s['ru'])}</b> — {esc(s['vi'])}</div>" for s in synonyms)
                render_html(f'<div class="clean-card" style="margin-top:8px;"><div class="clean-label"><span>Từ đồng nghĩa (Синонимы)</span></div>{s_items}</div>')
        with sa_c2:
            if antonyms:
                a_items = "".join(f"<div class='syn-ant-item'><b>{esc(a['ru'])}</b> — {esc(a['vi'])}</div>" for a in antonyms)
                render_html(f'<div class="clean-card" style="margin-top:8px;"><div class="clean-label"><span>Từ trái nghĩa (Антонимы)</span></div>{a_items}</div>')

    sent_grammar = res.get("sentence_grammar") or []
    if sent_grammar:
        g_rows = "".join(
            f"<tr><td><b>{esc(g.get('segment',''))}</b></td><td>{esc(g.get('grammar_tag',''))}</td><td>{esc(g.get('explanation',''))}</td></tr>"
            for g in sent_grammar
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Giải thích ngữ pháp</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cụm từ / Từ</th><th>Ngữ pháp (Cách / Thể)</th><th>Giải thích</th></tr></thead>
                    <tbody>{g_rows}</tbody>
                </table>
            </div>
            """
        )

    examples = res.get("context_examples") or []
    if examples:
        ex_html = "".join(
            f"""
            <div class="example-row">
                <span class="example-tag">{esc(ex.get('context','Ví dụ'))}</span>
                <div class="example-ru">{esc(ex.get('ru',''))}</div>
                <div class="example-vi">{esc(ex.get('vi',''))}</div>
            </div>
            """
            for ex in examples
        )
        render_html(f'<div class="clean-card"><div class="clean-label"><span>Ví dụ áp dụng theo ngữ cảnh</span></div>{ex_html}</div>')
        ex_btn_cols = st.columns(min(3, len(examples)))
        for idx, ex in enumerate(examples[:3]):
            with ex_btn_cols[idx]:
                if st.button(f"Nghe ví dụ {idx + 1}", key=f"tts_ex_{idx}", use_container_width=True):
                    ab = generate_tts_audio(ex["ru"].replace("\u0301", ""), "ru")
                    if ab:
                        st.audio(ab, format="audio/mp3")

    slang_list = res.get("slang_explanations") or []
    if slang_list:
        slang_rows = "".join(
            f"<tr><td><b>{esc(s.get('term',''))}</b></td><td>{esc(s.get('full_form',''))}</td><td>{esc(s.get('meaning_vi',''))}</td></tr>"
            for s in slang_list
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Tiếng lóng &amp; viết tắt</span></div>
                <table class="clean-table">
                    <thead><tr><th>Từ lóng</th><th>Dạng đầy đủ</th><th>Giải nghĩa</th></tr></thead>
                    <tbody>{slang_rows}</tbody>
                </table>
            </div>
            """
        )

    vocab_table = res.get("vocabulary_table") or []
    if vocab_table:
        v_rows = "".join(
            f"<tr><td><b>{esc(r.get('ru_accent',''))}</b></td><td>{esc(r.get('vi',''))}</td><td>{esc(r.get('en',''))}</td></tr>"
            for r in vocab_table
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Từ vựng đáng chú ý (có dấu trọng âm)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Tiếng Nga</th><th>Tiếng Việt</th><th>Tiếng Anh</th></tr></thead>
                    <tbody>{v_rows}</tbody>
                </table>
            </div>
            """
        )
        if st.button("Lưu từ vựng vào sổ ôn tập", key="btn_save_vocab"):
            added = add_vocab_items_to_notebook(vocab_table)
            st.toast(f"Đã lưu {added} từ mới vào sổ." if added else "Các từ này đã có trong sổ.")

    if res.get("context_note"):
        render_html(f'<div class="note-callout">{esc(res["context_note"])}</div>')

    with st.expander("Đối chiếu 3 ngôn ngữ (Nga · Việt · Anh)"):
        e1, e2, e3 = st.columns(3)
        with e1:
            st.caption("Tiếng Nga")
            st.write(res.get("ru_version") or "—")
        with e2:
            st.caption("Tiếng Việt")
            st.write(res.get("vi_version") or "—")
        with e3:
            st.caption("Tiếng Anh")
            st.write(res.get("en_version") or "—")


# ==============================================================================
# 9. GIAO DIỆN CHÍNH (ĐĂNG NHẬP ĐỒNG BỘ + HEADER TÁC GIẢ + SÁNG/TỐI + 3 TAB)
# ==============================================================================
def main() -> None:
    init_session_state()
    is_dark = st.session_state["theme_mode"] == "dark"
    inject_theme_css(is_author_admin=st.session_state["is_author_admin"], theme_mode=st.session_state["theme_mode"])
    avatar_uri = get_author_avatar_data_uri()

    with st.sidebar:
        render_html(
            f"""
            <div class="sidebar-author-box">
                <img src="{avatar_uri}" class="sidebar-author-img" alt="Mai Văn Minh" />
                <div>
                    <div style="font-size:0.95rem;font-weight:700;">Mai Văn Minh</div>
                    <div style="font-size:0.79rem;opacity:0.75;line-height:1.35;">
                        Sinh viên năm 4 · Đóng tàu<br/>
                        СПбГМТУ (Xanh-Petecbua)
                    </div>
                </div>
            </div>
            """
        )

        # 1. TÀI KHOẢN ĐĂNG NHẬP & ĐỒNG BỘ ĐA THIẾT BỊ
        st.markdown("#### Tài khoản & Đồng bộ")
        sync_badge = "Cloud Supabase (Đa thiết bị)" if _is_cloud_sync_enabled() else "SQLite cục bộ"
        if st.session_state["auth_username"]:
            uname = st.session_state["auth_username"]
            sv_name = st.session_state.get("confirmed_user_name") or uname
            sv_uni = st.session_state.get("confirmed_user_uni") or ""
            st.success(f"Đang đăng nhập: **{sv_name}** (`@{uname}`)" + (f" · {sv_uni}" if sv_uni else ""))
            st.caption(f"Đồng bộ: {sync_badge} · Tự giữ phiên khi F5")
            if st.button("Đăng xuất", use_container_width=True):
                st.session_state["auth_username"] = ""
                st.session_state["auth_password_hash"] = ""
                st.session_state["saved_gemini_api_key"] = ""
                st.session_state["saved_vocab_notebook"] = []
                st.session_state["translation_history"] = []
                try:
                    if "s" in st.query_params:
                        del st.query_params["s"]
                except Exception:
                    pass
                st.rerun()
        else:
            auth_mode = st.radio("Chế độ tài khoản", ["Đăng nhập", "Đăng ký mới"], horizontal=True, label_visibility="collapsed")
            if auth_mode == "Đăng nhập":
                with st.form("login_form"):
                    l_user = st.text_input("Tên đăng nhập / Email", placeholder="vd: minh2003")
                    l_pass = st.text_input("Mật khẩu", type="password")
                    if st.form_submit_button("Đăng nhập & Đồng bộ", type="primary", use_container_width=True):
                        u_clean = _normalize_username(l_user)
                        record = db_get_user(u_clean)
                        if record and _verify_password(l_pass, record.get("password_hash", "")):
                            apply_user_payload_to_session(u_clean, record)
                            st.toast("Đăng nhập thành công! Đã đồng bộ Key, Sổ từ vựng & Lịch sử.")
                            st.rerun()
                        else:
                            st.error("Sai tên đăng nhập hoặc mật khẩu.")
            else:
                with st.form("register_form"):
                    r_user = st.text_input("Tên đăng nhập (không dấu)", placeholder="vd: minh_spb")
                    r_pass = st.text_input("Mật khẩu (tối thiểu 4 ký tự)", type="password")
                    r_name = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
                    r_year = st.selectbox("Năm học", options=STUDENT_YEAR_OPTIONS, index=3)
                    r_uni = st.text_input("Trường theo học", placeholder="СПбГМТУ, ИТМО, СПбГУ...")
                    if st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True):
                        u_clean = _normalize_username(r_user)
                        if len(u_clean) < 3 or len(r_pass) < 4 or not r_name.strip() or not r_uni.strip():
                            st.warning("Nhập đủ tên đăng nhập (≥3 ký tự), mật khẩu (≥4 ký tự), họ tên và tên trường.")
                        elif db_get_user(u_clean) is not None:
                            st.error("Tên đăng nhập này đã tồn tại. Hãy chọn tên khác hoặc chuyển sang Đăng nhập.")
                        else:
                            new_payload = {
                                "password_hash": _hash_password(r_pass),
                                "profile": {
                                    "full_name": r_name.strip(),
                                    "student_year": r_year,
                                    "university": r_uni.strip(),
                                },
                                "api_key": clean_api_key(st.session_state.get("saved_gemini_api_key", "")),
                                "theme_mode": st.session_state.get("theme_mode", "light"),
                                "vocab_notebook": st.session_state.get("saved_vocab_notebook", []),
                                "translation_history": st.session_state.get("translation_history", []),
                            }
                            db_save_user(u_clean, new_payload)
                            send_user_notification_email(r_name.strip(), r_year, r_uni.strip())
                            apply_user_payload_to_session(u_clean, new_payload)
                            st.toast("Tạo tài khoản thành công! Dữ liệu của bạn sẽ tự động lưu.")
                            st.rerun()
            st.caption(f"Lưu trữ: {sync_badge}")

        st.markdown("---")

        # 2. CÀI ĐẶT GEMINI API KEY (TỰ ĐỘNG LƯU VÀO TÀI KHOẢN)
        st.markdown("#### Gemini API Key")
        saved_key_val = clean_api_key(st.session_state.get("saved_gemini_api_key", ""))
        gemini_api_key = st.text_input(
            "API Key cá nhân",
            value=saved_key_val,
            type="password",
            placeholder="Dán Gemini API Key vào đây",
            label_visibility="collapsed",
        )
        st.markdown(f"[Lấy Gemini API Key miễn phí →]({GEMINI_API_KEY_URL})")

        clean_key_input = clean_api_key(gemini_api_key)
        if clean_key_input != saved_key_val and (len(clean_key_input) >= 20 or clean_key_input == ""):
            st.session_state["saved_gemini_api_key"] = clean_key_input
            st.session_state.pop("pinned_gemini_model", None)
            if st.session_state["auth_username"]:
                sync_current_account_to_db()
                st.toast("Đã lưu API Key vào tài khoản của bạn.")
            st.rerun()

        if clean_key_input:
            models_avail, key_err = discover_working_gemini_models(clean_key_input)
            if key_err:
                st.error(key_err)
            else:
                top_m = st.session_state.get("pinned_gemini_model") or (models_avail[0] if models_avail else "gemini-flash")
                st.caption(f"Sẵn sàng · Model: `{top_m}`")
        else:
            st.caption("Chưa có Key — đang dùng dịch cơ bản.")

        st.markdown("---")
        with st.expander("Dành cho tác giả"):
            if not st.session_state["is_author_admin"]:
                pwd = st.text_input("Mật khẩu", type="password", key="author_pwd_in")
                if st.button("Mở khóa", use_container_width=True):
                    if verify_author_password(pwd):
                        st.session_state["is_author_admin"] = True
                        st.rerun()
                    else:
                        st.error("Mật khẩu không đúng.")
            else:
                st.caption(f"Trạng thái đồng bộ Cloud: {'Đang bật Supabase' if _is_cloud_sync_enabled() else 'Chưa cấu hình SUPABASE_URL/SUPABASE_KEY trong Secrets'}")
                all_users = db_list_all_users()
                st.caption(f"Tài khoản sinh viên đã đăng ký ({len(all_users)}):")
                for u in all_users[:15]:
                    st.caption(f"• **{u['full_name']}** (`@{u['username']}`) · {u['university']} · {u['vocab_count']} từ")
                if st.button("Khóa lại", use_container_width=True):
                    st.session_state["is_author_admin"] = False
                    st.rerun()

    # HEADER + NÚT BẬT/TẮT NỀN SÁNG/TỐI
    hdr_c1, hdr_c2 = st.columns([5.2, 1.1])
    with hdr_c1:
        render_html(
            f"""
            <div class="minimal-header" style="margin-bottom:8px;">
                <div>
                    <h1 class="minimal-title">Anh Minh Translate</h1>
                    <div class="minimal-sub">Dịch nhanh Nga – Việt, chia 6 cách, đồng nghĩa/trái nghĩa &amp; ôn tập từ vựng đồng bộ</div>
                </div>
                <div class="author-chip">
                    <img src="{avatar_uri}" class="author-chip-img" alt="Mai Văn Minh" />
                    <div>
                        <div class="author-chip-name">Mai Văn Minh</div>
                        <div class="author-chip-role">SV năm 4 · Đóng tàu · СПбГМТУ</div>
                    </div>
                </div>
            </div>
            """
        )
    with hdr_c2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        toggle_txt = "☀ Nền sáng" if is_dark else "☾ Nền tối"
        if st.button(toggle_txt, key="top_theme_toggle", use_container_width=True):
            st.session_state["theme_mode"] = "light" if is_dark else "dark"
            sync_current_account_to_db()
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["Dịch & Ngữ pháp", "Từ vựng & Ôn tập", "Kiến thức tiếng Nga"])

    with tab1:
        dir_c1, dir_c2 = st.columns([5, 1])
        with dir_c1:
            direction = st.selectbox(
                "Chiều dịch",
                options=DIRECTION_OPTIONS,
                index=DIRECTION_OPTIONS.index(st.session_state["selected_direction"]),
                label_visibility="collapsed",
            )
            st.session_state["selected_direction"] = direction
        with dir_c2:
            if st.button("⇄ Đổi chiều", use_container_width=True):
                if st.session_state["selected_direction"] == DIRECTION_OPTIONS[1]:
                    st.session_state["selected_direction"] = DIRECTION_OPTIONS[2]
                else:
                    st.session_state["selected_direction"] = DIRECTION_OPTIONS[1]
                st.rerun()

        source_text = st.text_area(
            "Nội dung cần dịch",
            key="input_text_area",
            height=145,
            label_visibility="collapsed",
            placeholder="Nhập từ, câu hoặc đoạn văn (tiếng Nga hay tiếng Việt đều tự nhận diện chuẩn) để dịch, chia 6 cách, chia động từ và xem ví dụ...",
        )

        b1, b2, b3, b4 = st.columns([1.8, 1.4, 1.0, 2.8])
        with b1:
            translate_clicked = st.button("Dịch & Phân tích", type="primary", use_container_width=True)
        with b2:
            tts_clicked = st.button("Nghe văn bản", type="secondary", use_container_width=True)
        with b3:
            if st.button("Xóa", type="secondary", use_container_width=True):
                st.session_state["input_text_area"] = ""
                st.rerun()
        with b4:
            if source_text.strip():
                k_map = {"word": "Từ / Cụm ngắn", "sentence": "Câu", "paragraph": "Đoạn văn"}
                eff_preview = resolve_effective_direction(source_text, direction)
                st.caption(f"{k_map[classify_input_type(source_text)]} · {eff_preview} · {len(source_text.split())} từ")

        with st.expander("Tải tệp văn bản (.txt, .docx, .pdf)"):
            uploaded_doc = st.file_uploader("Chọn tệp tài liệu", type=["txt", "md", "docx", "pdf"], label_visibility="collapsed")
            if uploaded_doc is not None:
                if st.button("Đưa nội dung tệp vào ô dịch", use_container_width=True):
                    txt, err = extract_text_from_uploaded_doc(uploaded_doc)
                    if err:
                        st.warning(err)
                    elif txt:
                        st.session_state["input_text_area"] = txt[:8000]
                        st.rerun()

        if tts_clicked and source_text.strip():
            has_cyr = bool(re.search(r"[а-яА-ЯёЁ]", source_text))
            lang_tts = "ru" if has_cyr else "vi"
            audio_b = generate_tts_audio(source_text, lang_tts)
            if audio_b:
                st.audio(audio_b, format="audio/mp3")

        if translate_clicked:
            if not source_text.strip():
                st.warning("Vui lòng nhập từ, câu hoặc đoạn văn cần dịch.")
            else:
                effective_dir = resolve_effective_direction(source_text, direction)
                result_data: Optional[Dict] = None
                meta_badge = "Dịch nhanh"
                if clean_key_input:
                    with st.spinner("Đang dịch và phân tích ngữ pháp bằng Gemini AI..."):
                        result_data, g_err, elapsed, model_used = call_gemini_smart_translate(
                            clean_key_input, source_text, effective_dir
                        )
                        if result_data:
                            meta_badge = f"{model_used} · {elapsed:.2f}s"
                        elif g_err:
                            st.warning(f"Gemini API chưa phản hồi ({g_err}). Tạm thời hiển thị kết quả dịch nhanh cơ bản.")

                if not result_data:
                    t_free = time.perf_counter()
                    with st.spinner("Đang dịch..."):
                        result_data = fallback_fast_translate(source_text, effective_dir)
                    meta_badge = f"Dịch nhanh · {time.perf_counter() - t_free:.2f}s"

                st.session_state["last_translation_result"] = result_data
                st.session_state["last_meta_badge"] = meta_badge
                st.session_state["translation_history"].insert(
                    0,
                    {
                        "time": datetime.now().strftime("%H:%M %d/%m"),
                        "preview": source_text.strip()[:120],
                        "full_source": source_text.strip(),
                        "result": result_data,
                        "meta_badge": meta_badge,
                    },
                )
                st.session_state["translation_history"] = st.session_state["translation_history"][:MAX_HISTORY_ITEMS]
                sync_current_account_to_db()

        if st.session_state.get("last_translation_result"):
            render_translation_result(
                st.session_state["last_translation_result"],
                st.session_state.get("last_meta_badge", "Dịch nhanh"),
                is_dark=is_dark,
            )

        if st.session_state["translation_history"]:
            with st.expander(f"Lịch sử dịch đã đồng bộ ({len(st.session_state['translation_history'])})"):
                for idx, h in enumerate(st.session_state["translation_history"][:15]):
                    hc1, hc2 = st.columns([5, 1])
                    with hc1:
                        st.markdown(f"`{h['time']}` · {h['preview']}")
                    with hc2:
                        if st.button("Mở lại", key=f"h_{idx}", use_container_width=True):
                            st.session_state["input_text_area"] = h["full_source"]
                            st.session_state["last_translation_result"] = h["result"]
                            st.session_state["last_meta_badge"] = h["meta_badge"]
                            st.rerun()

    with tab2:
        render_vocab_and_practice_tab()

    with tab3:
        render_russian_knowledge_hub()


if __name__ == "__main__":
    main()
