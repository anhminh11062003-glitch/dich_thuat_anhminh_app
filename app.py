"""
Anh Minh Translate — Dịch thuật siêu tốc, ngữ pháp 6 cách & ôn tập tiếng Nga cho sinh viên tại Nga
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
MAX_HISTORY_ITEMS = 30

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
FORMSPREE_ENDPOINT = _get_secret_or_env("FORMSPREE_ENDPOINT", "")
EMAILJS_SERVICE_ID = _get_secret_or_env("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = _get_secret_or_env("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = _get_secret_or_env("EMAILJS_PUBLIC_KEY", "")

USER_LOGS_FILE = Path(".user_access_logs.json")
CLIENT_STATE_FILE = Path(".client_private_vault.json")

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


def render_copy_button(text_to_copy: str, label: str = "Sao chép", key_suffix: str = "") -> None:
    if not text_to_copy:
        return
    safe_js_text = json.dumps(text_to_copy, ensure_ascii=False)
    safe_label = esc(label)
    btn_id = f"cp_{hashlib.md5((key_suffix + text_to_copy[:30]).encode('utf-8')).hexdigest()[:10]}"
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:transparent;overflow:hidden;">
            <button id="{btn_id}" onclick="copyNow()" style="
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: #FFFFFF;
                color: #18181B;
                border: 1px solid #D4D4D8;
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
                    btn.style.background = "#18181B";
                    btn.style.color = "#FFFFFF";
                    btn.style.borderColor = "#18181B";
                    setTimeout(() => {{
                        btn.innerText = {json.dumps(label, ensure_ascii=False)};
                        btn.style.background = "#FFFFFF";
                        btn.style.color = "#18181B";
                        btn.style.borderColor = "#D4D4D8";
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
# 2. LƯU CỐ ĐỊNH KEY & HỒ SƠ SINH VIÊN BỀN VỮNG QUA MỌI LẦN F5 / RESET WEB
#    (KẾT HỢP 3 LỚP: BROWSER COOKIE + LOCALSTORAGE + VAULT CÁCH LY THEO CLIENT ID)
# ==============================================================================
def _get_client_vault_id() -> str:
    """
    Tạo mã định danh riêng của từng người dùng dựa trên Cookie `am_uid` (nếu có)
    hoặc hash từ IP + User-Agent + Accept-Language. Tuyệt đối KHÔNG dùng khóa 'default' chung.
    """
    try:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            uid = str(st.context.cookies.get("am_uid", "")).strip()
            if len(uid) >= 8:
                return f"uid_{uid[:24]}"
    except Exception:
        pass

    try:
        headers = st.context.headers if hasattr(st, "context") and hasattr(st.context, "headers") else {}
        ua = str(headers.get("User-Agent", ""))
        lang = str(headers.get("Accept-Language", ""))
        xff = str(headers.get("X-Forwarded-For", headers.get("X-Real-Ip", "")))
        ip_part = xff.split(",")[0].strip() if xff else ""
        if ua or ip_part:
            raw = f"{ip_part}::{ua}::{lang}"
            return "fp_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    except Exception:
        pass
    return ""


def _read_vault_all() -> Dict[str, Any]:
    if CLIENT_STATE_FILE.exists():
        try:
            data = json.loads(CLIENT_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _write_vault_entry(client_id: str, updates: Dict[str, Any]) -> None:
    if not client_id:
        return
    data = _read_vault_all()
    entry = data.get(client_id) if isinstance(data.get(client_id), dict) else {}
    entry.update(updates)
    entry["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data[client_id] = entry
    try:
        CLIENT_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_persisted_user_data() -> Tuple[str, Dict[str, str]]:
    """
    Đọc API Key và Hồ sơ sinh viên bền vững sau khi F5 / đóng mở lại trình duyệt:
    Ưu tiên 1: Query params vừa đồng bộ từ localStorage (đọc xong xóa ngay khỏi URL)
    Ưu tiên 2: Cookie HTTP của chính trình duyệt người dùng (st.context.cookies)
    Ưu tiên 3: Vault cục bộ cách ly theo client_id riêng
    """
    api_key = ""
    profile: Dict[str, str] = {}
    had_qp = False

    # 1. Đọc từ query params vừa bootstrap (nếu có) rồi xóa ngay khỏi URL
    try:
        qp_k = st.query_params.get("_am_k", "")
        if qp_k:
            api_key = clean_api_key(qp_k)
            del st.query_params["_am_k"]
            had_qp = True

        qp_n = st.query_params.get("_am_n", "").strip()
        qp_y = st.query_params.get("_am_y", "").strip()
        qp_u = st.query_params.get("_am_u", "").strip()
        if qp_n and qp_u:
            profile = {
                "full_name": qp_n,
                "student_year": qp_y if qp_y in STUDENT_YEAR_OPTIONS else "Sinh viên Năm 4",
                "university": qp_u,
            }
        for k in ("_am_n", "_am_y", "_am_u", "saved_gkey", "sv_name", "sv_year", "sv_uni"):
            if k in st.query_params:
                del st.query_params[k]
                had_qp = True
    except Exception:
        pass

    if had_qp:
        components.html(
            """
            <script>
            try {
                const url = new URL(window.parent.location.href);
                ["_am_k", "_am_n", "_am_y", "_am_u", "saved_gkey", "sv_name", "sv_year", "sv_uni"]
                    .forEach(p => url.searchParams.delete(p));
                window.parent.history.replaceState({}, "", url.toString());
            } catch (e) {}
            </script>
            """,
            height=0,
        )

    # 2. Đọc trực tiếp từ Cookie trình duyệt (bền vững qua mọi lần F5, không cần reload)
    try:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            cookies = st.context.cookies
            if not api_key and cookies.get("am_gkey"):
                api_key = clean_api_key(urllib.parse.unquote(str(cookies.get("am_gkey"))))
            if not profile and cookies.get("am_prof"):
                raw_p = urllib.parse.unquote(str(cookies.get("am_prof")))
                parsed_p = json.loads(raw_p)
                if isinstance(parsed_p, dict) and parsed_p.get("full_name") and parsed_p.get("university"):
                    profile = {
                        "full_name": str(parsed_p["full_name"]).strip(),
                        "student_year": str(parsed_p.get("student_year", "Sinh viên Năm 4")).strip(),
                        "university": str(parsed_p["university"]).strip(),
                    }
    except Exception:
        pass

    # 3. Dự phòng từ Vault riêng theo client_id (không chia sẻ giữa các máy khác nhau)
    cid = _get_client_vault_id()
    if cid and (not api_key or not profile):
        entry = _read_vault_all().get(cid)
        if isinstance(entry, dict):
            if not api_key and entry.get("api_key"):
                api_key = clean_api_key(str(entry["api_key"]))
            if not profile and isinstance(entry.get("profile"), dict):
                p = entry["profile"]
                if p.get("full_name") and p.get("university"):
                    profile = {
                        "full_name": str(p["full_name"]).strip(),
                        "student_year": str(p.get("student_year", "Sinh viên Năm 4")).strip(),
                        "university": str(p["university"]).strip(),
                    }

    return api_key, profile


def persist_browser_state(
    action: str,
    api_key: str = "",
    student_profile: Optional[Dict[str, str]] = None,
) -> None:
    """
    Ghi đồng thời vào Cookie (max-age 1 năm), localStorage và Vault riêng của client_id.
    """
    cid = _get_client_vault_id()
    safe_key = json.dumps(clean_api_key(api_key))
    safe_prof = json.dumps(student_profile or {}, ensure_ascii=False)

    if action == "save_key":
        _write_vault_entry(cid, {"api_key": clean_api_key(api_key)})
        components.html(
            f"""
            <script>
            try {{
                const k = {safe_key};
                localStorage.setItem("anhminh_saved_gemini_key", k);
                const cookieStr = "am_gkey=" + encodeURIComponent(k) + "; path=/; max-age=31536000; SameSite=Lax";
                try {{ window.parent.document.cookie = cookieStr; }} catch (e) {{}}
                document.cookie = cookieStr;
            }} catch (e) {{}}
            </script>
            """,
            height=0,
        )
    elif action == "delete_key":
        _write_vault_entry(cid, {"api_key": ""})
        components.html(
            """
            <script>
            try {
                localStorage.removeItem("anhminh_saved_gemini_key");
                const delCookie = "am_gkey=; path=/; max-age=0; SameSite=Lax";
                try { window.parent.document.cookie = delCookie; } catch (e) {}
                document.cookie = delCookie;
            } catch (e) {}
            </script>
            """,
            height=0,
        )
    elif action == "save_profile":
        _write_vault_entry(cid, {"profile": student_profile or {}})
        components.html(
            f"""
            <script>
            try {{
                const pStr = JSON.stringify({safe_prof});
                localStorage.setItem("anhminh_saved_student_profile", pStr);
                const cookieStr = "am_prof=" + encodeURIComponent(pStr) + "; path=/; max-age=31536000; SameSite=Lax";
                try {{ window.parent.document.cookie = cookieStr; }} catch (e) {{}}
                document.cookie = cookieStr;
            }} catch (e) {{}}
            </script>
            """,
            height=0,
        )
    elif action == "bootstrap_from_localstorage":
        # Chạy mỗi khi server session còn trống (kể cả sau F5!) — KHÔNG bị chặn bởi sessionStorage cũ
        components.html(
            """
            <script>
            try {
                // Đảm bảo luôn có cookie định danh am_uid riêng cho trình duyệt này
                let hasUid = (document.cookie || "").includes("am_uid=");
                if (!hasUid) {
                    const randUid = (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(36).slice(2)).replace(/-/g, "");
                    const uidCookie = "am_uid=" + randUid + "; path=/; max-age=31536000; SameSite=Lax";
                    try { window.parent.document.cookie = uidCookie; } catch (e) {}
                    document.cookie = uidCookie;
                }

                const url = new URL(window.parent.location.href);
                let changed = false;

                const savedKey = localStorage.getItem("anhminh_saved_gemini_key");
                if (savedKey && savedKey.trim().length > 10) {
                    const ck = "am_gkey=" + encodeURIComponent(savedKey.trim()) + "; path=/; max-age=31536000; SameSite=Lax";
                    try { window.parent.document.cookie = ck; } catch (e) {}
                    url.searchParams.set("_am_k", savedKey.trim());
                    changed = true;
                }

                const rawProf = localStorage.getItem("anhminh_saved_student_profile");
                if (rawProf) {
                    const prof = JSON.parse(rawProf);
                    if (prof && prof.full_name && prof.university) {
                        const cp = "am_prof=" + encodeURIComponent(rawProf) + "; path=/; max-age=31536000; SameSite=Lax";
                        try { window.parent.document.cookie = cp; } catch (e) {}
                        url.searchParams.set("_am_n", prof.full_name);
                        url.searchParams.set("_am_y", prof.student_year || "Sinh viên Năm 4");
                        url.searchParams.set("_am_u", prof.university);
                        changed = true;
                    }
                }

                // Chống vòng lặp reload bằng mốc thời gian 4 giây
                const lastSync = parseInt(sessionStorage.getItem("am_last_sync_ts") || "0", 10);
                if (changed && (Date.now() - lastSync > 4000)) {
                    sessionStorage.setItem("am_last_sync_ts", String(Date.now()));
                    window.parent.location.replace(url.toString());
                }
            } catch (e) {}
            </script>
            """,
            height=0,
        )


def log_user_locally(full_name: str, student_year: str, university: str) -> None:
    logs: List[Dict[str, str]] = []
    if USER_LOGS_FILE.exists():
        try:
            loaded = json.loads(USER_LOGS_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                logs = loaded
        except Exception:
            logs = []
    logs.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "full_name": full_name,
            "student_year": student_year,
            "university": university,
        },
    )
    try:
        USER_LOGS_FILE.write_text(json.dumps(logs[:300], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def send_user_notification_email(full_name: str, student_year: str, university: str) -> Tuple[bool, str]:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log_user_locally(full_name, student_year, university)

    gmail_app_pwd = _get_secret_or_env("GMAIL_APP_PASSWORD", "")
    if gmail_app_pwd:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Anh Minh Translate] Sinh viên mới: {full_name} ({university})"
            msg["From"] = AUTHOR_NOTIFICATION_EMAIL
            msg["To"] = AUTHOR_NOTIFICATION_EMAIL
            html_body = (
                f"<div style='font-family:sans-serif;padding:16px;'>"
                f"<h3>Thông báo sinh viên sử dụng Anh Minh Translate</h3>"
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
        "Origin": "https://dich-thuat-anhminh.streamlit.app",
        "Referer": "https://dich-thuat-anhminh.streamlit.app/",
    }

    if FORMSPREE_ENDPOINT:
        try:
            req = urllib.request.Request(
                FORMSPREE_ENDPOINT,
                data=json.dumps(
                    {"Họ và tên": full_name, "Năm học": student_year, "Trường": university, "Thời gian": now_str}
                ).encode("utf-8"),
                headers=headers_json,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True, "Formspree"
        except Exception:
            pass

    if EMAILJS_SERVICE_ID and EMAILJS_TEMPLATE_ID and EMAILJS_PUBLIC_KEY:
        try:
            ejs_payload = {
                "service_id": EMAILJS_SERVICE_ID,
                "template_id": EMAILJS_TEMPLATE_ID,
                "user_id": EMAILJS_PUBLIC_KEY,
                "template_params": {
                    "to_email": AUTHOR_NOTIFICATION_EMAIL,
                    "user_name": full_name,
                    "student_year": student_year,
                    "university": university,
                    "access_time": now_str,
                },
            }
            req = urllib.request.Request(
                "https://api.emailjs.com/api/v1.0/email/send",
                data=json.dumps(ejs_payload).encode("utf-8"),
                headers=headers_json,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True, "EmailJS"
        except Exception:
            pass

    try:
        payload_fs = {
            "_subject": f"[Anh Minh Translate] Người dùng mới: {full_name} ({university})",
            "_template": "table",
            "_captcha": "false",
            "Ho_va_Ten": full_name,
            "Sinh_vien_nam": student_year,
            "Truong_theo_hoc": university,
            "Thoi_gian": now_str,
        }
        req_fs = urllib.request.Request(
            f"https://formsubmit.co/ajax/{AUTHOR_NOTIFICATION_EMAIL}",
            data=json.dumps(payload_fs).encode("utf-8"),
            headers=headers_json,
            method="POST",
        )
        with urllib.request.urlopen(req_fs, timeout=8) as resp:
            if resp.status in (200, 201):
                return True, "FormSubmit"
    except Exception:
        pass

    return False, "Local Log"


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
# 4. CSS TỐI GIẢN CHUẨN EDITORIAL (PHONG CÁCH NHATANH.AI · TƯƠNG PHẢN CAO)
# ==============================================================================
def inject_editorial_minimal_css(is_author_admin: bool = False) -> None:
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

    render_html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        {hide_admin_chrome}

        :root {{
            color-scheme: light !important;
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: #FAF9F6 !important;
            color: #18181B !important;
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
            padding-top: 1.8rem !important;
            padding-bottom: 3rem !important;
        }}

        .main p, .main label, .main h1, .main h2, .main h3, .main h4,
        .main div[data-testid="stWidgetLabel"] p,
        .main div[data-testid="stMarkdownContainer"] p,
        .main div[data-testid="stMarkdownContainer"] li {{
            color: #18181B !important;
        }}

        .main div[data-testid="stCaptionContainer"] p {{
            color: #52525B !important;
            font-size: 0.85rem !important;
        }}

        section[data-testid="stSidebar"] {{
            background-color: #F4F3EE !important;
            border-right: 1px solid #E5E4DF !important;
        }}
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] li {{
            color: #18181B !important;
        }}
        section[data-testid="stSidebar"] a {{
            color: #1D4ED8 !important;
        }}

        textarea, input[type="text"], input[type="password"] {{
            background-color: #FFFFFF !important;
            color: #18181B !important;
            -webkit-text-fill-color: #18181B !important;
            caret-color: #18181B !important;
            border: 1px solid #D4D4D8 !important;
            border-radius: 10px !important;
            font-size: 0.98rem !important;
            line-height: 1.6 !important;
        }}
        textarea:focus, input[type="text"]:focus, input[type="password"]:focus {{
            border-color: #18181B !important;
            box-shadow: 0 0 0 1px #18181B !important;
        }}
        textarea::placeholder, input::placeholder {{
            color: #71717A !important;
            -webkit-text-fill-color: #71717A !important;
            opacity: 1 !important;
        }}

        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {{
            background-color: #FFFFFF !important;
            border-color: #D4D4D8 !important;
            border-radius: 10px !important;
        }}

        div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border: 1px solid #D4D4D8 !important;
            border-radius: 10px !important;
            color: #18181B !important;
        }}
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] svg {{
            color: #18181B !important;
            fill: #18181B !important;
        }}
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"],
        ul[data-testid="stSelectboxVirtualDropdown"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #D4D4D8 !important;
            border-radius: 10px !important;
        }}
        div[data-baseweb="popover"] li,
        div[data-baseweb="menu"] li {{
            background-color: #FFFFFF !important;
            color: #18181B !important;
        }}
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="menu"] li:hover {{
            background-color: #F4F3EE !important;
        }}

        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"],
        div.stDownloadButton > button[kind="primary"] {{
            background-color: #18181B !important;
            color: #FFFFFF !important;
            border: 1px solid #18181B !important;
            border-radius: 9px !important;
            padding: 0.52rem 1.15rem !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            box-shadow: none !important;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] *,
        div.stDownloadButton > button[kind="primary"] * {{
            color: #FFFFFF !important;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: #27272A !important;
        }}

        div.stButton > button[kind="secondary"],
        div.stDownloadButton > button[kind="secondary"],
        div.stFormSubmitButton > button[kind="secondary"] {{
            background-color: #FFFFFF !important;
            color: #18181B !important;
            border: 1px solid #D4D4D8 !important;
            border-radius: 9px !important;
            padding: 0.5rem 1.05rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            box-shadow: none !important;
        }}
        div.stButton > button[kind="secondary"] *,
        div.stDownloadButton > button[kind="secondary"] * {{
            color: #18181B !important;
        }}
        div.stButton > button[kind="secondary"]:hover,
        div.stDownloadButton > button[kind="secondary"]:hover {{
            background-color: #F4F3EE !important;
        }}

        div[data-testid="stTabs"] div[role="tablist"] {{
            gap: 6px;
            border-bottom: 1px solid #E5E4DF !important;
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
            color: #52525B !important;
            font-weight: 500 !important;
            font-size: 0.92rem !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {{
            background-color: #F4F3EE !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: #18181B !important;
            border-color: #18181B !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}

        div[data-testid="stExpander"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #E5E4DF !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary svg {{
            color: #18181B !important;
            fill: #18181B !important;
            font-weight: 500 !important;
        }}
        div[data-testid="stFileUploader"] section {{
            background-color: #FFFFFF !important;
            border: 1px dashed #D4D4D8 !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stFileUploader"] section *,
        div[data-testid="stFileUploader"] small {{
            color: #18181B !important;
        }}
        div[data-testid="stFileUploader"] button {{
            background-color: #F4F3EE !important;
            color: #18181B !important;
            border: 1px solid #D4D4D8 !important;
        }}

        /* HEADER + TÁC GIẢ */
        .minimal-header {{
            padding-bottom: 18px;
            margin-bottom: 20px;
            border-bottom: 1px solid #E5E4DF;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 14px;
        }}
        .minimal-title {{
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: #18181B;
            margin: 0;
            line-height: 1.2;
        }}
        .minimal-sub {{ font-size: 0.88rem; color: #52525B; margin-top: 3px; }}
        .author-chip {{
            display: flex;
            align-items: center;
            gap: 11px;
            background: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 999px;
            padding: 6px 14px 6px 6px;
        }}
        .author-chip-img {{
            width: 40px; height: 40px; border-radius: 50%; object-fit: cover;
            border: 1px solid #D4D4D8; flex-shrink: 0;
        }}
        .author-chip-name {{ font-size: 0.86rem; font-weight: 600; color: #18181B; line-height: 1.25; }}
        .author-chip-role {{ font-size: 0.76rem; color: #52525B; line-height: 1.25; }}

        .sidebar-author-box {{
            display: flex; align-items: center; gap: 12px;
            background: #FFFFFF; border: 1px solid #E5E4DF; border-radius: 12px;
            padding: 12px; margin-bottom: 14px;
        }}
        .sidebar-author-img {{
            width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
            border: 1px solid #D4D4D8; flex-shrink: 0;
        }}

        .clean-card {{
            background-color: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 12px;
            padding: 18px 20px;
            margin-top: 14px;
            margin-bottom: 14px;
        }}
        .clean-label {{
            font-size: 0.82rem; font-weight: 600; color: #52525B; margin-bottom: 8px;
            display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;
        }}
        .clean-result-text {{
            font-size: 1.07rem; line-height: 1.72; color: #18181B; font-weight: 500;
            white-space: pre-wrap; word-break: break-word;
        }}
        .example-row {{ padding: 11px 0; border-bottom: 1px solid #E5E4DF; }}
        .example-row:last-child {{ border-bottom: none; padding-bottom: 2px; }}
        .example-ru {{ font-size: 1.0rem; font-weight: 600; color: #18181B; line-height: 1.5; }}
        .example-vi {{ font-size: 0.91rem; color: #52525B; margin-top: 3px; line-height: 1.5; }}
        .example-tag {{
            display: inline-block; font-size: 0.75rem; font-weight: 500; color: #52525B;
            background: #F4F3EE; padding: 2px 8px; border-radius: 6px; margin-bottom: 4px;
        }}

        .clean-table {{ width: 100%; border-collapse: collapse; font-size: 0.91rem; margin-top: 6px; }}
        .clean-table th {{
            text-align: left; padding: 9px 12px; border-bottom: 1px solid #D4D4D8;
            color: #52525B; font-weight: 600; background-color: #FAF9F6;
        }}
        .clean-table td {{
            padding: 9px 12px; border-bottom: 1px solid #E5E4DF; color: #18181B;
            vertical-align: top; line-height: 1.5;
        }}

        .note-callout {{
            background-color: #F4F3EE; border-left: 3px solid #18181B; border-radius: 0 8px 8px 0;
            padding: 12px 16px; margin-top: 12px; font-size: 0.91rem; color: #18181B; line-height: 1.62;
        }}

        .flashcard-minimal {{
            background-color: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 14px;
            padding: 36px 24px; text-align: center; margin: 12px 0;
        }}
        .flashcard-word {{ font-size: 1.72rem; font-weight: 700; color: #18181B; letter-spacing: -0.02em; }}
        .flashcard-back {{
            margin-top: 16px; padding-top: 16px; border-top: 1px solid #E5E4DF;
            font-size: 1.1rem; font-weight: 600; color: #18181B;
        }}

        @media (max-width: 768px) {{
            .main .block-container {{ padding: 1rem 0.85rem 2.5rem 0.85rem !important; }}
            .minimal-title {{ font-size: 1.32rem; }}
            .clean-card {{ padding: 14px 15px; }}
        }}
        </style>
        """
    )


# ==============================================================================
# 5. PHÂN LOẠI ĐẦU VÀO, DÒ MODEL TỰ ĐỘNG (CACHE 1H) & KIỂM SOÁT CHẤT LƯỢNG
# ==============================================================================
def classify_input_type(text: str) -> str:
    """
    Phân loại chính xác đầu vào:
    - 'word': từ đơn hoặc cụm từ/thuật ngữ ngắn (1-3 từ tiếng Nga hoặc 1-4 từ tiếng Việt, 1 dòng, không dấu kết câu)
    - 'sentence': 1 câu hoàn chỉnh (<= 25 từ, <= 1 dấu kết câu)
    - 'paragraph': đoạn văn nhiều câu / nhiều dòng
    """
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
    """
    Dò đúng danh sách model mà API Key này được cấp phép (cache 1 tiếng nên chỉ tốn 1 lần duy nhất).
    Trả về (danh_sách_model, thông_báo_lỗi_nếu_key_sai).
    """
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


def validate_and_clean_ai_result(parsed: Dict[str, Any], input_kind: str) -> Dict[str, Any]:
    """Kiểm soát chất lượng đầu ra: lọc rác nhưng KHÔNG xóa nhầm dữ liệu ngữ pháp hợp lệ."""
    if not isinstance(parsed, dict):
        return {}

    def _valid_str(v: Any) -> str:
        s = str(v or "").strip()
        if s.lower() in ("", "...", "n/a", "none", "null", "không có"):
            return ""
        return s

    out: Dict[str, Any] = {
        "input_kind": input_kind,
        "main_translation": _valid_str(parsed.get("main_translation")),
        "ru_version": _valid_str(parsed.get("ru_version")),
        "vi_version": _valid_str(parsed.get("vi_version")),
        "en_version": _valid_str(parsed.get("en_version")),
        "context_note": _valid_str(parsed.get("context_note")),
        "morphology": {},
        "sentence_grammar": [],
        "context_examples": [],
        "slang_explanations": [],
        "vocabulary_table": [],
    }

    # 1. Hình thái học (6 cách / chia động từ) khi tra từ đơn hoặc cụm từ ngắn
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

    # 2. Giải thích ngữ pháp câu / đoạn
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

    # 3. Ví dụ áp dụng theo ngữ cảnh
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

    # 4. Tiếng lóng
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

    # 5. Bảng từ vựng
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
    api_key: str, source_text: str, direction: str
) -> Tuple[Optional[Dict], Optional[str], float, str]:
    t0 = time.perf_counter()
    input_kind = classify_input_type(source_text)

    ai_cache = _get_lru_cache("gemini_result_cache")
    cache_key = hashlib.sha256(f"{direction}::{input_kind}::{source_text.strip()}".encode("utf-8")).hexdigest()
    if cache_key in ai_cache:
        ai_cache.move_to_end(cache_key)
        return ai_cache[cache_key], None, 0.01, "Cache"

    if input_kind == "word":
        task_instruction = """
Đầu vào là TỪ ĐƠN hoặc CỤM TỪ NGẮN (dù người dùng nhập tiếng Nga hay tiếng Việt, luôn phân tích hình thái của TỪ TIẾNG NGA tương ứng!).
BẮT BUỘC thực hiện chính xác:
1. Xác định đúng từ loại tiếng Nga (Danh từ / Tính từ / Đại từ / Động từ / Trạng từ).
2. Nếu là ĐỘNG TỪ: BẮT BUỘC điền đủ bảng `verb_conjugation` (я, ты, он / она / оно, мы, вы, они, Quá khứ, Mệnh lệnh) và ghi rõ cặp thể НСВ / СВ vào `aspect_or_gender`. Để `cases_table` = [].
3. Nếu là DANH TỪ / TÍNH TỪ / ĐẠI TỪ / CỤM DANH TỪ: BẮT BUỘC điền CHÍNH XÁC ĐỦ 6 CÁCH vào `cases_table`:
   1. Именительный (Cách 1), 2. Родительный (Cách 2), 3. Дательный (Cách 3), 4. Винительный (Cách 4), 5. Творительный (Cách 5), 6. Предложный (Cách 6) — có dấu trọng âm \\u0301, đủ số ít `singular` và số nhiều `plural` (nếu từ không có số nhiều thì ghi "—"). Để `verb_conjugation` = {}.
4. Nếu là TRẠNG TỪ / TỪ KHÔNG BIẾN CÁCH: để `cases_table` = [], `verb_conjugation` = {}, giải thích chi tiết cách dùng & cấp so sánh vào `usage_note`.
5. BẮT BUỘC tạo đúng 3 ví dụ áp dụng thực tế (`context_examples`) chứa CHÍNH từ tiếng Nga này trong ngữ cảnh tự nhiên (đại học, đời sống hoặc chuyên ngành), có dấu trọng âm \\u0301 và nghĩa tiếng Việt.
6. Đặt `sentence_grammar` = [].
"""
    elif input_kind == "sentence":
        task_instruction = """
Đầu vào là MỘT CÂU HOÀN CHỈNH. BẮT BUỘC thực hiện chính xác:
1. Đặt `morphology` = {}.
2. BẮT BUỘC điền `sentence_grammar` (3–6 mục) phân tích chính xác ngữ pháp của câu tiếng Nga: từ/cụm nào chia Cách mấy, tại sao, động từ thể НСВ/СВ nào & thì gì.
3. BẮT BUỘC tạo 2–3 ví dụ áp dụng (`context_examples`) dùng lại cấu trúc hoặc từ khóa chính của câu vào tình huống thực tế.
4. Điền `vocabulary_table` 3–6 từ khóa quan trọng (có dấu trọng âm \\u0301).
"""
    else:
        task_instruction = """
Đầu vào là ĐOẠN VĂN DÀI. BẮT BUỘC thực hiện chính xác:
1. Dịch toàn bộ đoạn văn chuẩn xác, giữ nguyên bố cục xuống dòng.
2. Đặt `morphology` = {}.
3. Điền `sentence_grammar` 3–5 điểm ngữ pháp / cấu trúc đáng chú ý nhất trong đoạn.
4. Điền `vocabulary_table` 5–8 thuật ngữ trọng tâm (có dấu trọng âm \\u0301).
5. BẮT BUỘC tạo 2 ví dụ áp dụng (`context_examples`) cho các thuật ngữ/cấu trúc nổi bật nhất trong đoạn.
"""

    system_prompt = f"""
Bạn là giáo sư ngôn ngữ học Nga – Việt chuyên sâu về thuật ngữ đại học và dịch thuật song ngữ Nga-Việt. Chiều dịch: "{direction}".
{task_instruction}
CHỈ TRẢ VỀ đúng 1 JSON hợp lệ:
{{
  "main_translation": "Bản dịch chuẩn xác nhất",
  "ru_version": "Bản tiếng Nga tương ứng",
  "vi_version": "Bản tiếng Việt tương ứng",
  "en_version": "Bản tiếng Anh đối chiếu",
  "morphology": {{
    "word_type": "",
    "lemma": "",
    "aspect_or_gender": "",
    "cases_table": [{{"case": "1. Именительный (Cách 1)", "singular": "", "plural": ""}}],
    "verb_conjugation": {{"я": "", "ты": "", "он / она / оно": "", "мы": "", "вы": "", "они": "", "Quá khứ": "", "Mệnh lệnh": ""}},
    "usage_note": ""
  }},
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
        cleaned = validate_and_clean_ai_result(parsed or {}, input_kind)
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


def fallback_fast_translate(source_text: str, direction: str) -> Dict[str, Any]:
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
        if direction == DIRECTION_OPTIONS[0]:
            f_vi = executor.submit(fast_free_translate, expanded_ru, "ru", "vi")
            f_en = executor.submit(fast_free_translate, expanded_ru, "ru", "en")
            vi_ver, en_ver, ru_ver = f_vi.result(), f_en.result(), source_text
            main_trans = vi_ver
        elif direction == DIRECTION_OPTIONS[1]:
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
        "main_translation": main_trans,
        "ru_version": ru_ver,
        "vi_version": vi_ver,
        "en_version": en_ver,
        "morphology": {},
        "sentence_grammar": [],
        "context_examples": examples,
        "slang_explanations": slang_explanations,
        "vocabulary_table": vocab_list,
        "context_note": "Nhập Gemini API Key (miễn phí) ở thanh bên trái để bật chia 6 cách, chia động từ theo ngôi, phân tích ngữ pháp câu dài và ví dụ áp dụng.",
    }


# ==============================================================================
# 6. CẨM NANG KIẾN THỨC TIẾNG NGA CHI TIẾT & KHOA HỌC (TAB 3)
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
                    <thead>
                        <tr><th>Cách</th><th>Câu hỏi</th><th>Chức năng chính</th><th>Giới từ hay gặp</th><th>Ví dụ</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><b>1. Именительный</b><br/>Nguyên cách</td><td>Кто? Что?</td><td>Chủ ngữ, định nghĩa, dạng gốc trong từ điển</td><td>Không có</td><td><b>Студе́нт</b> у́чится. <b>Кни́га</b> на столе́.</td></tr>
                        <tr><td><b>2. Родительный</b><br/>Sở hữu cách</td><td>Кого́? Чего́?</td><td>Sở hữu (của ai), phủ định (нет), số lượng (2–4 số ít; ≥5 số nhiều), nơi xuất phát</td><td>у, без, до, из, с, от, о́коло, по́сле, для, кро́ме, во вре́мя</td><td>Нет <b>вре́мени</b>. Два <b>студе́нта</b>. Из <b>Росси́и</b>.</td></tr>
                        <tr><td><b>3. Дательный</b><br/>Tặng cách</td><td>Кому́? Чему́?</td><td>Người nhận (cho ai), tuổi tác, trạng thái/cảm xúc (мне ну́жно), đối tượng hướng tới</td><td>к, по, благодаря́, вопреки́</td><td>Помога́ю <b>дру́гу</b>. <b>Мне</b> 21 год. По <b>пла́ну</b>.</td></tr>
                        <tr><td><b>4. Винительный</b><br/>Đối cách</td><td>Кого́? Что?</td><td>Tân ngữ trực tiếp (đọc gì, gặp ai), hướng chuyển động (куда́?), thứ trong tuần, thời lượng</td><td>в, на (hướng đi), че́рез, за, про</td><td>Чита́ю <b>кни́гу</b>. Иду́ в <b>университе́т</b>. В <b>сре́ду</b>.</td></tr>
                        <tr><td><b>5. Творительный</b><br/>Công cụ cách</td><td>Кем? Чем?</td><td>Công cụ (bằng gì), đi cùng ai (с кем?), nghề nghiệp (стать/рабо́тать), bị động</td><td>с, над, под, пе́ред, за, ме́жду</td><td>Пишу́ <b>ру́чкой</b>. Ко́фе с <b>молоко́м</b>. Ста́ну <b>инжене́ром</b>.</td></tr>
                        <tr><td><b>6. Предложный</b><br/>Giới cách</td><td>О ком? О чём? Где?</td><td>Vị trí tĩnh (ở đâu?), chủ đề (nói/nghĩ về gì), tháng/năm, phương tiện (на метро́)</td><td>в, на (vị trí), о (об), при</td><td>Живу́ в <b>Петербу́рге</b>. Ду́маю об <b>экза́мене</b>.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Bảng đuôi Danh từ Số ít (Единственное число)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Giống đực (ø / -й / -ь)</th><th>Giống cái (-а / -я / -ь)</th><th>Giống trung (-о / -е / -ие)</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>ø / -й / -ь</td><td>-а / -я / -ь</td><td>-о / -е / -ие</td></tr>
                        <tr><td><b>2</b></td><td>-а / -я / -я</td><td>-ы (-и) / -и / -и</td><td>-а / -я / -ия</td></tr>
                        <tr><td><b>3</b></td><td>-у / -ю / -ю</td><td>-е / -е (-и với -ия) / -и</td><td>-у / -ю / -ию</td></tr>
                        <tr><td><b>4</b></td><td>Vật = C1 · Người = C2</td><td>-у / -ю / -ь</td><td>Giống Cách 1 (-о / -е / -ие)</td></tr>
                        <tr><td><b>5</b></td><td>-ом / -ем / -ем</td><td>-ой / -ей / -ью</td><td>-ом / -ем / -ием</td></tr>
                        <tr><td><b>6</b></td><td>-е (-ии với -ий)</td><td>-е (-ии với -ия; -и với -ь)</td><td>-е (-ии với -ие)</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Bảng đuôi Danh từ Số nhiều (Множественное число)</span><span>Chú ý Cách 2 số nhiều</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Đuôi số nhiều phổ biến</th><th>Ví dụ (студе́нты · кни́ги · общежи́тия)</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>-ы / -и (Đực, Cái) · -а / -я (Trung)</td><td>студе́нты, кни́ги, окна́, общежи́тия</td></tr>
                        <tr><td><b>2</b></td><td><b>-ов / -ев</b> (Đực cứng/-й) · <b>-ей</b> (đuôi -ь, ж/ш/ч/щ) · <b>ø</b> (bỏ đuôi -а/-о) · <b>-ий</b> (từ -ия/-ие)</td><td>студе́нт<b>ов</b>, враче́<b>й</b>, книг<b>ø</b>, окон<b>ø</b>, общежи́т<b>ий</b></td></tr>
                        <tr><td><b>3</b></td><td>-ам / -ям</td><td>студе́нтам, кни́гам, общежи́тиям</td></tr>
                        <tr><td><b>4</b></td><td>Vật = Cách 1 số nhiều · Người = Cách 2 số nhiều</td><td>чита́ю кни́ги · ви́жу студе́нтов</td></tr>
                        <tr><td><b>5</b></td><td>-ами / -ями</td><td>студе́нтами, кни́гами, общежи́тиями</td></tr>
                        <tr><td><b>6</b></td><td>-ах / -ях</td><td>о студе́нтах, в кни́гах, в общежи́тиях</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>2 quy tắc chính tả bắt buộc nhớ:</b><br/>
                    • <b>Quy tắc 7 chữ cái (г, к, х, ж, ч, ш, щ):</b> Sau 7 âm này không viết <b>«ы»</b>, luôn viết <b>«и»</b> (кни́га → кни́ги).<br/>
                    • <b>Quy tắc 5 chữ cái (ж, ч, ш, щ, ц):</b> Nếu không có trọng âm thì viết <b>«е»</b> thay vì <b>«о»</b> (това́рищем, хоро́шего).
                </div>
            </div>
            """
        )

    elif topic == "2. Tính từ & Đại từ":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Biến cách Tính từ theo 6 cách (Прилагательные)</span><span>VD: но́вый (cứng) / си́ний (mềm)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cách</th><th>Giống đực</th><th>Giống trung</th><th>Giống cái</th><th>Số nhiều (cả 3 giống)</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b></td><td>-ый / -ой / -ий</td><td>-ое / -ее</td><td>-ая / -яя</td><td>-ые / -ие</td></tr>
                        <tr><td><b>2</b></td><td>-ого / -его</td><td>-ого / -его</td><td>-ой / -ей</td><td>-ых / -их</td></tr>
                        <tr><td><b>3</b></td><td>-ому / -ему</td><td>-ому / -ему</td><td>-ой / -ей</td><td>-ым / -им</td></tr>
                        <tr><td><b>4</b></td><td>Vật = C1 · Người = C2</td><td>-ое / -ее</td><td>-ую / -юю</td><td>Vật = C1 · Người = C2</td></tr>
                        <tr><td><b>5</b></td><td>-ым / -им</td><td>-ым / -им</td><td>-ой / -ей</td><td>-ыми / -ими</td></tr>
                        <tr><td><b>6</b></td><td>-ом / -ем</td><td>-ом / -ем</td><td>-ой / -ей</td><td>-ых / -их</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>6 Cách của Đại từ nhân xưng (Личные местоимения)</span><span>Dùng hàng ngày</span></div>
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
                <div class="note-callout">
                    <b>Lưu ý thêm chữ «н-»:</b> Với đại từ ngôi 3 (<b>он, она́, оно́, они́</b>), khi đứng ngay sau giới từ luôn thêm <b>н-</b> phía trước (VD: у <b>него́</b>, к <b>ней</b>, с <b>ни́ми</b>).
                </div>
            </div>
            """
        )

    elif topic == "3. Động từ & Thể (НСВ/СВ)":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Quy tắc chia động từ Hiện tại / Tương lai đơn</span></div>
                <table class="clean-table">
                    <thead><tr><th>Ngôi</th><th>Nhóm I (đa số -ать, -ять, -еть · чита́ть)</th><th>Nhóm II (đa số -ить · говори́ть)</th></tr></thead>
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
                    <b>Biến âm phụ âm hay gặp ở ngôi «я» (Nhóm II):</b> <b>д → ж</b> (ви́деть → ви́жу), <b>т → ч</b> (плати́ть → плачу́), <b>с → ш</b> (писа́ть → пишу́), <b>б/п/в/м → бл/пл/вл/мл</b> (люби́ть → люблю́, гото́вить → гото́влю).<br/>
                    <b>Thì quá khứ:</b> Bỏ <b>-ть</b>, thêm <b>-л / -ла / -ло / -ли</b> theo giống/số của chủ ngữ.
                </div>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Phân biệt Thể Chưa Hoàn Thành (НСВ) & Thể Hoàn Thành (СВ)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Tiêu chí</th><th>НСВ (Несовершенный вид)</th><th>СВ (Совершенный вид)</th></tr></thead>
                    <tbody>
                        <tr><td><b>Bản chất</b></td><td>Quá trình, hành động lặp lại, thói quen, nêu sự thật chung</td><td>Kết quả đã hoàn tất, hành động xảy ra 1 lần dứt điểm</td></tr>
                        <tr><td><b>Từ dấu hiệu</b></td><td>ка́ждый день, ча́сто, обы́чно, до́лго, всегда́</td><td>уже́, наконе́ц, вдруг, сра́зу, за (2 часа́)</td></tr>
                        <tr><td><b>Các thì</b></td><td>Quá khứ · Hiện tại · Tương lai (бу́ду + nguyên thể)</td><td>Quá khứ · Tương lai đơn (chia trực tiếp, <b>không có Hiện tại</b>)</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>12 cặp động từ НСВ / СВ sinh viên dùng nhiều nhất</span></div>
                <table class="clean-table">
                    <thead><tr><th>НСВ (Quá trình)</th><th>СВ (Kết quả)</th><th>Nghĩa tiếng Việt</th></tr></thead>
                    <tbody>
                        <tr><td>сдава́ть</td><td>сдать</td><td>Nộp bài / thi (сдал экза́мен = đã qua môn)</td></tr>
                        <tr><td>писа́ть</td><td>написа́ть</td><td>Viết</td></tr>
                        <tr><td>учи́ть</td><td>вы́учить</td><td>Học / học thuộc</td></tr>
                        <tr><td>реша́ть</td><td>реши́ть</td><td>Giải bài / quyết định</td></tr>
                        <tr><td>понима́ть</td><td>поня́ть</td><td>Hiểu</td></tr>
                        <tr><td>отправля́ть</td><td>отпра́вить</td><td>Gửi (email, tài liệu)</td></tr>
                        <tr><td>получа́ть</td><td>получи́ть</td><td>Nhận (học bổng, giấy tờ)</td></tr>
                        <tr><td>переводи́ть</td><td>перевести́</td><td>Dịch thuật</td></tr>
                        <tr><td>проверя́ть</td><td>прове́рить</td><td>Kiểm tra / chấm bài</td></tr>
                        <tr><td>объясня́ть</td><td>объясни́ть</td><td>Giải thích</td></tr>
                        <tr><td>забыва́ть</td><td>забы́ть</td><td>Quên</td></tr>
                        <tr><td>продлева́ть</td><td>продли́ть</td><td>Gia hạn (visa, tạm trú)</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "4. Động từ chuyển động":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Bảng Động từ chuyển động cơ bản (không tiền tố)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Nghĩa</th><th>1 hướng / Đang diễn ra</th><th>Khứ hồi / Lặp lại / Thói quen</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>Đi bộ</b></td><td>идти́ (иду́, идёшь)</td><td>ходи́ть (хожу́, хо́дишь)</td><td>Сейча́с иду́ в корпус. Ка́ждый день хожу́ на па́ры.</td></tr>
                        <tr><td><b>Đi bằng phương tiện</b></td><td>е́хать (е́ду, е́дешь)</td><td>е́здить (е́зжу, е́здишь)</td><td>Е́ду на метро́. Ча́сто е́зжу в центр.</td></tr>
                        <tr><td><b>Chạy</b></td><td>бежа́ть</td><td>бе́гать</td><td>Бегу́ на пе́рвую па́ру!</td></tr>
                        <tr><td><b>Mang (đi bộ)</b></td><td>нести́</td><td>носи́ть</td><td>Несу́ чертёж преподава́телю.</td></tr>
                        <tr><td><b>Chở (bằng xe)</b></td><td>везти́</td><td>вози́ть</td><td>Авто́бус везёт студе́нтов.</td></tr>
                        <tr><td><b>Dẫn / lái</b></td><td>вести́</td><td>води́ть</td><td>Он во́дит маши́ну.</td></tr>
                        <tr><td><b>Bay</b></td><td>лете́ть</td><td>лета́ть</td><td>Лечу́ во Вьетна́м ле́том.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>10 Tiền tố không gian thường gặp nhất</span></div>
                <table class="clean-table">
                    <thead><tr><th>Tiền tố</th><th>Nghĩa</th><th>Giới từ + Cách đi kèm</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>при-</b></td><td>Đến nơi</td><td>в/на + C4 · к + C3</td><td>прийти́ в декана́т (đến văn phòng khoa)</td></tr>
                        <tr><td><b>у-</b></td><td>Rời đi hẳn</td><td>из/с/от + C2</td><td>уе́хать из го́рода (rời khỏi thành phố)</td></tr>
                        <tr><td><b>в- / во-</b></td><td>Đi vào trong</td><td>в + C4</td><td>войти́ в аудито́рию (vào giảng đường)</td></tr>
                        <tr><td><b>вы-</b></td><td>Đi ra ngoài</td><td>из + C2</td><td>вы́йти из общежи́тия (ra khỏi KTX)</td></tr>
                        <tr><td><b>под-</b></td><td>Tiến lại gần</td><td>к + C3</td><td>подойти́ к преподава́телю (lại gần thầy)</td></tr>
                        <tr><td><b>от-</b></td><td>Lùi ra xa</td><td>от + C2</td><td>отойти́ от окна́ (rời khỏi cửa sổ)</td></tr>
                        <tr><td><b>пере-</b></td><td>Đi ngang qua</td><td>че́рез + C4 (hoặc C4 trực tiếp)</td><td>перейти́ у́лицу (sang đường)</td></tr>
                        <tr><td><b>про-</b></td><td>Đi xuyên qua / đi qua</td><td>ми́мо + C2 · че́рез + C4</td><td>пройти́ ми́мо ко́рпуса (đi ngang qua tòa nhà)</td></tr>
                        <tr><td><b>за-</b></td><td>Ghé qua / tạt vào</td><td>в/на + C4 · к + C3</td><td>зайти́ в магази́н (ghé qua cửa hàng)</td></tr>
                        <tr><td><b>до-</b></td><td>Đi tới đích</td><td>до + C2</td><td>дое́хать до метро́ (đi tới ga metro)</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "5. Giới từ & Thời gian":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Cặp giới từ địa điểm & các từ BẮT BUỘC dùng «НА»</span></div>
                <table class="clean-table">
                    <thead><tr><th>Ở đâu? (Где? · C6)</th><th>Đi đâu? (Куда́? · C4)</th><th>Từ đâu? (Отку́да? · C2)</th><th>Dùng cho</th></tr></thead>
                    <tbody>
                        <tr><td><b>в</b> + Cách 6</td><td><b>в</b> + Cách 4</td><td><b>из</b> + Cách 2</td><td>Không gian kín, tòa nhà, thành phố, quốc gia (в Росси́и, в ко́мнате, в униве́ре)</td></tr>
                        <tr><td><b>на</b> + Cách 6</td><td><b>на</b> + Cách 4</td><td><b>с</b> + Cách 2</td><td>Sự kiện, buổi học, khoa, không gian mở, phương hướng</td></tr>
                        <tr><td><b>у</b> + Cách 2</td><td><b>к</b> + Cách 3</td><td><b>от</b> + Cách 2</td><td>Người (у вра́ча, к дека́ну, от преподава́теля)</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Danh sách bắt buộc dùng «НА» (rất hay thi & dễ nhầm):</b><br/>
                    на факульте́те, на ка́федре, на ку́рсе, на ле́кции, на семина́ре, на экза́мене, на пра́ктике, на рабо́те, на заво́де, на по́чте, на вокза́ле, на стадио́не, на пло́щади, на у́лице, на се́вере/ю́ге, на Ро́дине.
                </div>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Cấu trúc nói Thời gian (Thứ · Ngày · Tháng · Giờ)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Hỏi</th><th>Cấu trúc</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>Vào thứ mấy?</b></td><td>в + Cách 4</td><td>в понеде́льник, во вто́рник, в сре́ду, в четве́рг, в пя́тницу, в суббо́ту, в воскресе́нье</td></tr>
                        <tr><td><b>Vào tháng mấy?</b></td><td>в + Cách 6</td><td>в январе́, в феврале́, в ма́рте, в сентябре́, в ноябре́, в декабре́</td></tr>
                        <tr><td><b>Vào ngày mấy?</b></td><td>Số thứ tự (trung) + Tháng (đều <b>Cách 2</b>)</td><td>пе́рвого сентября́ (1/9), два́дцать шесто́го ноября́ (26/11)</td></tr>
                        <tr><td><b>Lúc mấy giờ?</b></td><td>в + số giờ (Cách 4)</td><td>в час (1h), в два часа́ (2h), в пять часо́в (5h), без де́сяти два (2h kém 10)</td></tr>
                        <tr><td><b>Bao lâu nữa?</b></td><td>че́рез + Cách 4</td><td>че́рез неде́лю (1 tuần nữa), че́рез два дня (2 ngày nữa)</td></tr>
                        <tr><td><b>Cách đây bao lâu?</b></td><td>Cách 4 + наза́д</td><td>три дня наза́д (3 ngày trước), год наза́д (1 năm trước)</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "6. Số từ & Lượng từ":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Quy tắc sống còn khi ghép Số đếm với Danh từ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Số tận cùng bằng</th><th>Cách của Danh từ</th><th>Ví dụ: рубль (rúp)</th><th>Ví dụ: год (năm)</th><th>Ví dụ: час (giờ)</th></tr></thead>
                    <tbody>
                        <tr><td><b>1</b> (1, 21, 31... trừ 11)</td><td><b>Cách 1 số ít</b></td><td>оди́н рубль</td><td>оди́н год</td><td>оди́н час</td></tr>
                        <tr><td><b>2, 3, 4</b> (2–4, 22–24... trừ 12–14)</td><td><b>Cách 2 số ít</b></td><td>два рубля́</td><td>три го́да</td><td>четы́ре часа́</td></tr>
                        <tr><td><b>5–20, 0</b> và <b>мно́го / ма́ло / ско́лько / не́сколько</b></td><td><b>Cách 2 số nhiều</b></td><td>пять рубле́й</td><td>пять <b>лет</b></td><td>пять часо́в</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Lưu ý về Tính từ đi cùng số 2, 3, 4:</b><br/>
                    • Với danh từ giống đực/trung: Tính từ chia <b>Cách 2 số nhiều</b> (два <b>но́вых</b> студе́нта).<br/>
                    • Với danh từ giống cái: Tính từ thường chia <b>Cách 1 số nhiều</b> (две <b>но́вые</b> кни́ги).
                </div>
            </div>
            """
        )

    else:
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Cấu trúc câu ghép & Từ nối học thuật (Dùng viết tiểu luận / đồ án)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Từ nối / Cấu trúc</th><th>Quy tắc ngữ pháp</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>что́бы</b> (để mà)</td><td>Cùng chủ ngữ: <b>что́бы + nguyên thể</b><br/>Khác chủ ngữ: <b>что́бы + thì Quá khứ</b></td><td>Я учу́сь, что́бы <b>получи́ть</b> дипло́м.<br/>Преподава́тель хо́чет, что́бы мы <b>сда́ли</b> рабо́ту.</td></tr>
                        <tr><td><b>кото́рый</b> (mà / cái mà)</td><td>Giống & số theo danh từ đứng trước; <b>Cách</b> theo vai trò trong mệnh đề sau</td><td>Кни́га, <b>кото́рую</b> я чита́ю (C4).<br/>Университе́т, в <b>кото́ром</b> я учу́сь (C6).</td></tr>
                        <tr><td><b>потому́ что / поэ́тому</b></td><td>потому́ что (bởi vì) · поэ́тому (vì vậy)</td><td>Я уста́л, <b>потому́ что</b> мно́го рабо́тал.</td></tr>
                        <tr><td><b>благодаря́ + C3 / из-за + C2</b></td><td>благодаря́ (nhờ vào · tích cực)<br/>из-за (tại vì · tiêu cực)</td><td><b>Благодаря́</b> по́мощи дру́га (C3).<br/><b>Из-за</b> плохо́й пого́ды (C2).</td></tr>
                        <tr><td><b>несмотря́ на + C4 / хотя́</b></td><td>Mặc dù</td><td><b>Несмотря́ на</b> сло́жность зада́чи, мы реши́ли её.</td></tr>
                        <tr><td><b>е́сли ..., то ...</b></td><td>Nếu ... thì ... (Điều kiện giả định dùng <b>е́сли бы + quá khứ</b>)</td><td><b>Е́сли</b> у тебя́ есть вопро́сы, <b>то</b> напиши́ мне.</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )


# ==============================================================================
# 7. QUẢN LÝ SỔ TỪ VỰNG, FLASHCARDS & TRẮC NGHIỆM ÔN TẬP (TAB 2)
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
    return added


def export_vocab_to_anki_csv(vocab_list: List[Dict[str, str]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tieng_Nga", "Tieng_Viet", "Tieng_Anh"])
    for item in vocab_list:
        writer.writerow([item.get("ru_accent", ""), item.get("vi", ""), item.get("en", "")])
    return ("\ufeff" + output.getvalue()).encode("utf-8")


def _generate_quiz_question(pool: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if len(pool) < 4:
        return None
    target = random.choice(pool)
    distractors = random.sample([x for x in pool if x["ru_accent"] != target["ru_accent"]], 3)
    options = [target["vi"]] + [d["vi"] for d in distractors]
    random.shuffle(options)
    return {
        "prompt_ru": target["ru_accent"],
        "correct_vi": target["vi"],
        "en": target.get("en", ""),
        "options": options,
        "answered": None,
    }


def render_vocab_and_practice_tab() -> None:
    mode = st.radio(
        "Chế độ học từ vựng",
        options=["Thẻ ghi nhớ (Flashcards)", "Trắc nghiệm nhanh (Quiz)", "Sổ từ vựng & Tiếng lóng"],
        horizontal=True,
        label_visibility="collapsed",
    )

    saved_list = st.session_state["saved_vocab_notebook"]
    slang_deck = [
        {"ru_accent": f"{x['accent']} ({x['full']})", "vi": x["vi"], "en": x["en"], "mastered": False}
        for x in RUSSIAN_SLANG_DICT
    ]

    if mode == "Thẻ ghi nhớ (Flashcards)":
        fc_top1, fc_top2 = st.columns([2, 1.5])
        with fc_top1:
            deck_choice = st.selectbox(
                "Bộ thẻ ôn tập",
                options=["Sổ từ vựng đã lưu", "Từ chưa thuộc trong sổ", "30 từ lóng sinh viên Nga"],
                label_visibility="collapsed",
            )
        if deck_choice == "Sổ từ vựng đã lưu":
            active_deck = saved_list
        elif deck_choice == "Từ chưa thuộc trong sổ":
            active_deck = [v for v in saved_list if not v.get("mastered")]
        else:
            active_deck = slang_deck

        with fc_top2:
            if saved_list:
                mastered_cnt = sum(1 for v in saved_list if v.get("mastered"))
                st.caption(f"Tiến độ sổ cá nhân: Đã thuộc **{mastered_cnt} / {len(saved_list)}** từ")

        if not active_deck:
            st.info("Chưa có từ trong bộ thẻ này. Bạn có thể lưu từ sau khi dịch ở Tab 1, hoặc chọn bộ «30 từ lóng sinh viên Nga» để ôn ngay.")
            return

        idx = st.session_state["flashcard_index"] % len(active_deck)
        card = active_deck[idx]
        status_tag = " · Đã thuộc" if card.get("mastered") else ""

        back_html = (
            f'<div class="flashcard-back">{esc(card["vi"])}<div style="font-size:0.9rem;color:#52525B;font-weight:400;margin-top:4px;">{esc(card.get("en",""))}</div></div>'
            if st.session_state["flashcard_show_back"]
            else '<div style="margin-top:12px;font-size:0.86rem;color:#71717A;">Bấm «Lật thẻ» để kiểm tra nghĩa</div>'
        )
        render_html(
            f"""
            <div class="flashcard-minimal">
                <div style="font-size:0.8rem;color:#71717A;margin-bottom:8px;">Thẻ {idx + 1} / {len(active_deck)}{status_tag}</div>
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
                lbl = "Bỏ đã thuộc" if card.get("mastered") else "Đã thuộc ✓"
                if st.button(lbl, use_container_width=True):
                    for item in saved_list:
                        if item["ru_accent"] == card["ru_accent"]:
                            item["mastered"] = not item.get("mastered", False)
                            break
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

    elif mode == "Trắc nghiệm nhanh (Quiz)":
        pool = saved_list if len(saved_list) >= 4 else slang_deck
        source_note = (
            f"Đang luyện từ Sổ cá nhân ({len(saved_list)} từ)"
            if len(saved_list) >= 4
            else "Đang luyện từ bộ 30 từ lóng sinh viên Nga (lưu từ 4 từ trở lên ở Tab 1 để luyện sổ cá nhân)"
        )
        st.caption(f"{source_note} · Điểm phiên này: **{st.session_state['quiz_score']} / {st.session_state['quiz_total']}**")

        if st.session_state.get("current_quiz") is None:
            st.session_state["current_quiz"] = _generate_quiz_question(pool)

        q = st.session_state["current_quiz"]
        if q:
            render_html(
                f"""
                <div class="clean-card" style="text-align:center;padding:24px;">
                    <div style="font-size:0.82rem;color:#71717A;margin-bottom:6px;">Chọn nghĩa tiếng Việt đúng của từ sau:</div>
                    <div style="font-size:1.6rem;font-weight:700;color:#18181B;">{esc(q['prompt_ru'])}</div>
                </div>
                """
            )
            for opt_i, opt in enumerate(q["options"]):
                if st.button(opt, key=f"quiz_opt_{opt_i}", use_container_width=True, disabled=q["answered"] is not None):
                    q["answered"] = opt
                    st.session_state["quiz_total"] += 1
                    if opt == q["correct_vi"]:
                        st.session_state["quiz_score"] += 1
                    st.rerun()

            if q["answered"] is not None:
                if q["answered"] == q["correct_vi"]:
                    st.success(f"Chính xác: {q['prompt_ru']} = {q['correct_vi']}")
                else:
                    st.error(f"Chưa đúng. Đáp án đúng là: {q['correct_vi']}")
                if st.button("Câu tiếp theo", type="primary"):
                    st.session_state["current_quiz"] = _generate_quiz_question(pool)
                    st.rerun()

    else:
        col_left, col_right = st.columns([1.05, 1.0])
        with col_left:
            st.markdown("#### Sổ từ vựng cá nhân")
            with st.expander("Thêm từ mới thủ công"):
                with st.form("add_manual_vocab", clear_on_submit=True):
                    m_ru = st.text_input("Tiếng Nga (có thể kèm trọng âm)", placeholder="VD: осто́йчивость")
                    m_vi = st.text_input("Nghĩa tiếng Việt", placeholder="VD: Tính ổn định (của tàu)")
                    m_en = st.text_input("Tiếng Anh (tùy chọn)", placeholder="VD: stability")
                    if st.form_submit_button("Thêm vào sổ", type="primary", use_container_width=True):
                        if m_ru.strip() and m_vi.strip():
                            add_vocab_items_to_notebook([{"ru_accent": m_ru.strip(), "vi": m_vi.strip(), "en": m_en.strip()}])
                            st.toast("Đã thêm từ mới.")
                            st.rerun()

            if saved_list:
                st.download_button(
                    f"Xuất {len(saved_list)} từ ra CSV (Anki / Excel)",
                    data=export_vocab_to_anki_csv(saved_list),
                    file_name="tu_vung_anki.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                rows = "".join(
                    f"<tr><td><b>{esc(v['ru_accent'])}</b></td><td>{esc(v['vi'])}</td><td>{'Đã thuộc' if v.get('mastered') else 'Chưa thuộc'}</td></tr>"
                    for v in saved_list
                )
                render_html(
                    f"""
                    <div style="max-height:360px;overflow-y:auto;border:1px solid #E5E4DF;border-radius:10px;background:#FFFFFF;margin-top:8px;">
                        <table class="clean-table" style="margin-top:0;">
                            <thead><tr><th>Tiếng Nga</th><th>Nghĩa tiếng Việt</th><th>Trạng thái</th></tr></thead>
                            <tbody>{rows}</tbody>
                        </table>
                    </div>
                    """
                )
                if st.button("Xóa toàn bộ sổ từ vựng", use_container_width=True):
                    st.session_state["saved_vocab_notebook"] = []
                    st.rerun()
            else:
                st.caption("Sổ từ vựng đang trống. Dịch ở Tab 1 rồi bấm «Lưu từ vựng vào sổ ôn tập» hoặc thêm thủ công ở trên.")

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
                f"<tr><td><b>{esc(x['accent'])}</b><br/><span style='font-size:0.8rem;color:#71717A;'>{esc(x['full'])}</span></td><td>{esc(x['vi'])}</td></tr>"
                for x in filtered
            )
            render_html(
                f"""
                <div style="max-height:420px;overflow-y:auto;border:1px solid #E5E4DF;border-radius:10px;background:#FFFFFF;">
                    <table class="clean-table" style="margin-top:0;">
                        <thead><tr><th>Tiếng Nga</th><th>Nghĩa tiếng Việt</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
                """
            )


# ==============================================================================
# 8. HIỂN THỊ KẾT QUẢ DỊCH & KHỞI TẠO SESSION BỀN VỮNG
# ==============================================================================
def init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "input_text_area": "",
        "selected_direction": DIRECTION_OPTIONS[0],
        "is_author_admin": False,
        "saved_gemini_api_key": "",
        "declined_keys": set(),
        "translation_history": [],
        "saved_vocab_notebook": [],
        "flashcard_index": 0,
        "flashcard_show_back": False,
        "current_quiz": None,
        "quiz_score": 0,
        "quiz_total": 0,
        "last_meta_badge": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Nạp bền vững từ Query Bootstrap -> Browser Cookie -> Client Vault
    rec_key, rec_prof = load_persisted_user_data()
    if rec_key and not st.session_state["saved_gemini_api_key"]:
        st.session_state["saved_gemini_api_key"] = rec_key
    if rec_prof and not st.session_state.get("confirmed_user_name"):
        st.session_state["confirmed_user_name"] = rec_prof["full_name"]
        st.session_state["confirmed_user_year"] = rec_prof["student_year"]
        st.session_state["confirmed_user_uni"] = rec_prof["university"]

    # Nếu vẫn thiếu key hoặc profile sau khi F5 -> đồng bộ từ localStorage của trình duyệt (chỉ 1 lần / session mới)
    if not st.session_state.get("ls_bootstrapped_this_session"):
        st.session_state["ls_bootstrapped_this_session"] = True
        if not st.session_state.get("saved_gemini_api_key") or not st.session_state.get("confirmed_user_name"):
            persist_browser_state("bootstrap_from_localstorage")


def render_translation_result(res: Dict[str, Any], meta_badge: str) -> None:
    kind_labels = {"word": "Tra từ", "sentence": "Phân tích câu", "paragraph": "Dịch đoạn văn"}
    kind_text = kind_labels.get(res.get("input_kind", ""), "Bản dịch")
    main_trans = res.get("main_translation", "")

    render_html(
        f"""
        <div class="clean-card">
            <div class="clean-label">
                <span>{esc(kind_text)}</span>
                <span>{esc(meta_badge)}</span>
            </div>
            <div class="clean-result-text">{esc(main_trans)}</div>
        </div>
        """
    )

    c_act1, c_act2, _ = st.columns([1.2, 1.3, 4.5])
    with c_act1:
        render_copy_button(main_trans, "Sao chép", "main_cp")
    with c_act2:
        tts_lang = "ru" if re.search(r"[а-яА-ЯёЁ]", main_trans) else "vi"
        if st.button("Nghe bản dịch", key="tts_main_btn", use_container_width=True):
            audio_b = generate_tts_audio(main_trans, tts_lang)
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
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Ví dụ áp dụng theo ngữ cảnh</span></div>
                {ex_html}
            </div>
            """
        )
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
                <div class="clean-label"><span>Tiếng lóng &amp; viết tắt trong văn bản</span></div>
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
            st.toast(f"Đã lưu {added} từ mới." if added else "Các từ này đã có trong sổ.")

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
# 9. GIAO DIỆN CHÍNH (SIDEBAR + HEADER TÁC GIẢ + 3 TAB TINH GỌN)
# ==============================================================================
def main() -> None:
    init_session_state()
    inject_editorial_minimal_css(is_author_admin=st.session_state["is_author_admin"])
    avatar_uri = get_author_avatar_data_uri()

    with st.sidebar:
        render_html(
            f"""
            <div class="sidebar-author-box">
                <img src="{avatar_uri}" class="sidebar-author-img" alt="Mai Văn Minh" />
                <div>
                    <div style="font-size:0.95rem;font-weight:700;color:#18181B;">Mai Văn Minh</div>
                    <div style="font-size:0.79rem;color:#52525B;line-height:1.35;">
                        Sinh viên năm 4 · Đóng tàu<br/>
                        СПбГМТУ (Xanh-Petecbua)
                    </div>
                </div>
            </div>
            """
        )

        # Thực thi ghi cookie/localStorage sau khi rerun ổn định
        if st.session_state.get("pending_key_save"):
            k_save = st.session_state.pop("pending_key_save")
            persist_browser_state("save_key", api_key=k_save)
        if st.session_state.get("pending_key_delete"):
            st.session_state.pop("pending_key_delete")
            persist_browser_state("delete_key")
        if st.session_state.get("pending_profile_save"):
            prof = st.session_state.pop("pending_profile_save")
            persist_browser_state("save_profile", student_profile=prof)

        st.markdown("#### Cài đặt API")
        saved_key_val = clean_api_key(st.session_state.get("saved_gemini_api_key", ""))
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=saved_key_val,
            type="password",
            placeholder="Dán key để bật dịch AI, 6 cách & ví dụ",
        )
        st.markdown(f"[Lấy Gemini API Key miễn phí →]({GEMINI_API_KEY_URL})")

        clean_key_input = clean_api_key(gemini_api_key)
        # Tự động lưu ngay khi người dùng dán Key hợp lệ mới (chỉ cần nhập 1 lần duy nhất!)
        if clean_key_input and clean_key_input != saved_key_val and len(clean_key_input) >= 20:
            st.session_state["saved_gemini_api_key"] = clean_key_input
            st.session_state["pending_key_save"] = clean_key_input
            st.session_state.pop("pinned_gemini_model", None)
            st.toast("Đã tự động lưu API Key cho các lần truy cập sau.")
            st.rerun()

        if clean_key_input:
            models_avail, key_err = discover_working_gemini_models(clean_key_input)
            if key_err:
                st.error(key_err)
            else:
                top_m = st.session_state.get("pinned_gemini_model") or (models_avail[0] if models_avail else "gemini-flash")
                st.caption(f"Đã lưu Key vĩnh viễn · Model: `{top_m}`")
            if st.button("Xóa / Đổi API Key", use_container_width=True):
                st.session_state["saved_gemini_api_key"] = ""
                st.session_state["pending_key_delete"] = True
                st.session_state.pop("pinned_gemini_model", None)
                st.rerun()
        else:
            st.caption("Chưa nhập Key — đang dùng chế độ dịch nhanh cơ bản.")

        st.markdown("---")

        has_prof = bool(st.session_state.get("confirmed_user_name") and st.session_state.get("confirmed_user_uni"))
        with st.expander("Thông tin sinh viên" + (f" · {st.session_state['confirmed_user_name']}" if has_prof else ""), expanded=not has_prof):
            cur_y = st.session_state.get("confirmed_user_year", "Sinh viên Năm 4")
            y_idx = STUDENT_YEAR_OPTIONS.index(cur_y) if cur_y in STUDENT_YEAR_OPTIONS else 3
            with st.form("sv_profile_form"):
                u_name = st.text_input("Họ và tên", value=st.session_state.get("confirmed_user_name", ""), placeholder="Nguyễn Văn A")
                u_year = st.selectbox("Năm học", options=STUDENT_YEAR_OPTIONS, index=y_idx)
                u_uni = st.text_input("Trường theo học", value=st.session_state.get("confirmed_user_uni", ""), placeholder="СПбГМТУ, ИТМО, СПбГУ...")
                if st.form_submit_button("Lưu thông tin", type="primary", use_container_width=True):
                    if u_name.strip() and u_uni.strip():
                        prof_obj = {"full_name": u_name.strip(), "student_year": u_year, "university": u_uni.strip()}
                        st.session_state["confirmed_user_name"] = prof_obj["full_name"]
                        st.session_state["confirmed_user_year"] = prof_obj["student_year"]
                        st.session_state["confirmed_user_uni"] = prof_obj["university"]
                        send_user_notification_email(prof_obj["full_name"], prof_obj["student_year"], prof_obj["university"])
                        st.session_state["pending_profile_save"] = prof_obj
                        st.toast("Đã lưu thông tin sinh viên cho các lần sau.")
                        st.rerun()
                    else:
                        st.warning("Vui lòng nhập họ tên và tên trường.")

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
                st.caption("Đã mở khóa chế độ tác giả.")
                if USER_LOGS_FILE.exists():
                    try:
                        logs = json.loads(USER_LOGS_FILE.read_text(encoding="utf-8"))
                        st.caption(f"Danh sách đã đăng ký ({len(logs)}):")
                        for item in logs[:15]:
                            st.caption(f"• {item.get('full_name')} · {item.get('university')} ({item.get('time')})")
                    except Exception:
                        pass
                if st.button("Khóa lại", use_container_width=True):
                    st.session_state["is_author_admin"] = False
                    st.rerun()

    render_html(
        f"""
        <div class="minimal-header">
            <div>
                <h1 class="minimal-title">Anh Minh Translate</h1>
                <div class="minimal-sub">Dịch nhanh Nga – Việt, chia 6 cách, ngữ pháp &amp; ôn tập từ vựng cho sinh viên tại Nga</div>
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

    tab1, tab2, tab3 = st.tabs(["Dịch & Ngữ pháp", "Từ vựng & Ôn tập", "Kiến thức tiếng Nga"])

    # ==========================================================================
    # TAB 1: DỊCH SIÊU TỐC, 6 CÁCH, CHIA ĐỘNG TỪ & VÍ DỤ ÁP DỤNG (ĐÃ BỎ ẢNH SLIDE)
    # ==========================================================================
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
                st.session_state["selected_direction"] = (
                    DIRECTION_OPTIONS[1] if st.session_state["selected_direction"] == DIRECTION_OPTIONS[0] else DIRECTION_OPTIONS[0]
                )
                st.rerun()

        source_text = st.text_area(
            "Nội dung cần dịch",
            key="input_text_area",
            height=145,
            label_visibility="collapsed",
            placeholder="Nhập 1 từ tiếng Nga (hoặc tiếng Việt) để chia 6 cách / chia động từ, hoặc dán câu / đoạn văn để dịch, giải thích ngữ pháp và xem ví dụ áp dụng...",
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
                detected_k = k_map[classify_input_type(source_text)]
                st.caption(f"{detected_k} · {len(source_text)} ký tự · {len(source_text.split())} từ")

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
            lang_tts = "ru" if has_cyr else ("vi" if "Tiếng Việt →" in direction else "en")
            audio_b = generate_tts_audio(source_text, lang_tts)
            if audio_b:
                st.audio(audio_b, format="audio/mp3")

        if translate_clicked:
            if not source_text.strip():
                st.warning("Vui lòng nhập từ, câu hoặc đoạn văn cần dịch.")
            else:
                result_data: Optional[Dict] = None
                meta_badge = "Dịch nhanh"
                if clean_key_input:
                    with st.spinner("Đang dịch và phân tích ngữ pháp bằng Gemini AI..."):
                        result_data, g_err, elapsed, model_used = call_gemini_smart_translate(
                            clean_key_input, source_text, direction
                        )
                        if result_data:
                            meta_badge = f"{model_used} · {elapsed:.2f}s"
                        elif g_err:
                            # Báo rõ lý do lỗi API để người dùng biết, KHÔNG âm thầm bỏ qua!
                            st.warning(f"Gemini API chưa phản hồi ({g_err}). Tạm thời hiển thị kết quả dịch nhanh cơ bản.")

                if not result_data:
                    t_free = time.perf_counter()
                    with st.spinner("Đang dịch..."):
                        result_data = fallback_fast_translate(source_text, direction)
                    meta_badge = f"Dịch nhanh · {time.perf_counter() - t_free:.2f}s"

                st.session_state["last_translation_result"] = result_data
                st.session_state["last_meta_badge"] = meta_badge
                st.session_state["translation_history"].insert(
                    0,
                    {
                        "time": datetime.now().strftime("%H:%M"),
                        "preview": source_text.strip()[:120],
                        "full_source": source_text.strip(),
                        "result": result_data,
                        "meta_badge": meta_badge,
                    },
                )
                st.session_state["translation_history"] = st.session_state["translation_history"][:MAX_HISTORY_ITEMS]

        if st.session_state.get("last_translation_result"):
            render_translation_result(
                st.session_state["last_translation_result"],
                st.session_state.get("last_meta_badge", "Dịch nhanh"),
            )

        if st.session_state["translation_history"]:
            with st.expander(f"Lịch sử dịch gần đây ({len(st.session_state['translation_history'])})"):
                for idx, h in enumerate(st.session_state["translation_history"][:10]):
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
