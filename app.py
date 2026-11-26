"""
Anh Minh Translate v8.0 Pro — Hệ sinh thái Dịch thuật & Học thuật cho Sinh viên Việt tại Nga
Tác giả: Mai Văn Minh — Sinh viên năm 4, Chuyên ngành Đóng tàu, СПбГМТУ (Xanh-Petecbua)
"""

from array import array
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
import math
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.parse
import urllib.request
import wave

import streamlit as st
import streamlit.components.v1 as components

try:
    import speech_recognition as sr
except Exception:
    sr = None

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
# 1. CẤU HÌNH TRANG, HẰNG SỐ & BẢO MẬT TÁC GIẢ
# ==============================================================================
st.set_page_config(
    page_title="Anh Minh Translate v8.0 | Mai Văn Minh - СПбГМТУ",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_VERSION = "v8.0 Pro"
GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"
AUTHOR_NOTIFICATION_EMAIL = "anhminh11062003@gmail.com"
MAX_MEM_CACHE_SIZE = 250
MAX_HISTORY_ITEMS = 30


def _get_secret_or_env(key: str, default: str = "") -> str:
    """Đọc cấu hình ưu tiên từ st.secrets rồi đến biến môi trường."""
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

# File log cục bộ (chỉ lưu log đăng ký cho tác giả; KHÔNG lưu chung API Key giữa các user!)
USER_LOGS_FILE = Path(".user_access_logs.json")
FIXED_AUTHOR_AVATAR_BASE64_OR_URL = ""

STUDENT_YEAR_OPTIONS = [
    "Dự bị tiếng Nga (Подфак)",
    "Sinh viên Năm 1",
    "Sinh viên Năm 2",
    "Sinh viên Năm 3",
    "Sinh viên Năm 4",
    "Sinh viên Năm 5 (Специалитет)",
    "Cao học / Thạc sĩ (Магистратура)",
    "Nghiên cứu sinh (Аспирантура)",
    "Khác / Đã tốt nghiệp",
]

DOMAIN_OPTIONS = [
    "Kỹ thuật & Đóng tàu",
    "Giao tiếp / Tin nhắn đời thường",
    "CNTT & Khoa học máy tính",
    "Kinh tế & Quản trị",
    "Học thuật tổng hợp",
]

DIRECTION_OPTIONS = [
    "🇷🇺 Tiếng Nga ➔ 🇻🇳 Tiếng Việt",
    "🇻🇳 Tiếng Việt ➔ 🇷🇺 Tiếng Nga",
    "🌐 Đa chiều: Nga ↔ Anh ↔ Việt (Đối chiếu 3 ngôn ngữ)",
]

QUICK_SAMPLE_PRESETS: List[Dict[str, str]] = [
    {
        "label": "💬 Slang KTX / Telegram",
        "direction": "🇷🇺 Tiếng Nga ➔ 🇻🇳 Tiếng Việt",
        "domain": "Giao tiếp / Tin nhắn đời thường",
        "text": "Ребята, препод сказал, что завтра первая пара отменяется, но нужно срочно сдать курсач и закрыть все хвосты до начала сессии!",
    },
    {
        "label": "⚓ Kỹ thuật Đóng tàu",
        "direction": "🇷🇺 Tiếng Nga ➔ 🇻🇳 Tiếng Việt",
        "domain": "Kỹ thuật & Đóng tàu",
        "text": "Расчёт остойчивости и непотопляемости корпуса судна выполняется с учётом водоизмещения, осадки и прочности шпангоутов.",
    },
    {
        "label": "🛂 Hỏi Phòng Visa (VI➔RU)",
        "direction": "🇻🇳 Tiếng Việt ➔ 🇷🇺 Tiếng Nga",
        "domain": "Giao tiếp / Tin nhắn đời thường",
        "text": "Thưa cô, em là sinh viên năm 4, em muốn hỏi hồ sơ cần chuẩn bị để gia hạn thị thực và đăng ký tạm trú tại ký túc xá ạ.",
    },
    {
        "label": "🎓 Xin giảng viên duyệt đồ án",
        "direction": "🇻🇳 Tiếng Việt ➔ 🇷🇺 Tiếng Nga",
        "domain": "Học thuật tổng hợp",
        "text": "Em chào thầy ạ, em đã hoàn thành phần bản vẽ kỹ thuật và tính toán sức bền vật liệu của đồ án môn học. Khi nào em có thể gặp thầy để nhận xét ạ?",
    },
]


def esc(text: Any) -> str:
    """Chống XSS và tránh vỡ HTML khi văn bản chứa ký tự <, >, &, dấu nháy."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def render_html(html_str: str) -> None:
    cleaned_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(cleaned_lines), unsafe_allow_html=True)


def clean_api_key(raw_key: str) -> str:
    """Làm sạch mọi ký tự thừa, khoảng trắng, dấu nháy khi người dùng dán API Key."""
    if not raw_key:
        return ""
    return re.sub(r'[\s"\'\`]+', "", raw_key.strip())


def verify_author_password(input_pwd: str) -> bool:
    """So sánh mật khẩu an toàn chống timing attack."""
    if not input_pwd or not DEFAULT_AUTHOR_PASSWORD:
        return False
    return hmac.compare_digest(input_pwd.strip(), DEFAULT_AUTHOR_PASSWORD)


def render_copy_button(text_to_copy: str, label: str = "📋 Sao chép", key_suffix: str = "") -> None:
    """Nút sao chép 1 chạm vào Clipboard hoạt động mượt trên cả Máy tính và Điện thoại."""
    if not text_to_copy:
        return
    safe_js_text = json.dumps(text_to_copy, ensure_ascii=False)
    safe_label = esc(label)
    btn_id = f"copy_btn_{hashlib.md5((key_suffix + text_to_copy[:30]).encode('utf-8')).hexdigest()[:10]}"
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:transparent;overflow:hidden;">
            <button id="{btn_id}" onclick="copyNow()" style="
                font-family: 'Be Vietnam Pro', -apple-system, sans-serif;
                background: #FFFFFF;
                color: #0369A1;
                border: 1.5px solid #38BDF8;
                border-radius: 10px;
                padding: 5px 12px;
                font-size: 0.82rem;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.18s ease;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            ">{safe_label}</button>
            <script>
            function copyNow() {{
                const text = {safe_js_text};
                const btn = document.getElementById("{btn_id}");
                const markDone = () => {{
                    btn.innerText = "✅ Đã sao chép!";
                    btn.style.background = "#DCFCE7";
                    btn.style.color = "#166534";
                    btn.style.borderColor = "#4ADE80";
                    setTimeout(() => {{
                        btn.innerText = {json.dumps(label, ensure_ascii=False)};
                        btn.style.background = "#FFFFFF";
                        btn.style.color = "#0369A1";
                        btn.style.borderColor = "#38BDF8";
                    }}, 1800);
                }};
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).then(markDone).catch(() => fallbackCopy(text, markDone));
                }} else {{
                    fallbackCopy(text, markDone);
                }}
            }}
            function fallbackCopy(text, cb) {{
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
        height=36,
    )


# ==============================================================================
# 1B. ĐỒNG BỘ CLIENT-SIDE LOCALSTORAGE AN TOÀN (CÁCH LY TUYỆT ĐỐI GIỮA CÁC USER)
# ==============================================================================
def consume_bootstrap_query_params() -> Tuple[str, Dict[str, str]]:
    """
    Đọc dữ liệu đồng bộ từ localStorage (nếu vừa bootstrap) rồi XÓA NGAY khỏi URL/query_params
    để API Key không bao giờ bị lộ trên thanh địa chỉ trình duyệt hoặc khi chia sẻ link.
    """
    recovered_key = ""
    recovered_profile: Dict[str, str] = {}
    had_sensitive_qp = False

    try:
        qp_key = st.query_params.get("_am_k", "")
        if qp_key:
            recovered_key = clean_api_key(qp_key)
            del st.query_params["_am_k"]
            had_sensitive_qp = True

        qp_name = st.query_params.get("_am_n", "").strip()
        qp_year = st.query_params.get("_am_y", "").strip()
        qp_uni = st.query_params.get("_am_u", "").strip()
        if qp_name and qp_uni:
            recovered_profile = {
                "full_name": qp_name,
                "student_year": qp_year if qp_year in STUDENT_YEAR_OPTIONS else "Sinh viên Năm 4",
                "university": qp_uni,
            }
        for k in ("_am_n", "_am_y", "_am_u", "saved_gkey", "sv_name", "sv_year", "sv_uni"):
            if k in st.query_params:
                del st.query_params[k]
                had_sensitive_qp = True
    except Exception:
        pass

    if had_sensitive_qp:
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

    return recovered_key, recovered_profile


def inject_localstorage_sync(
    action: str = "load_all",
    key_to_save: str = "",
    student_profile: Optional[Dict[str, str]] = None,
) -> None:
    """
    Lưu API Key và Hồ sơ Sinh viên CHỈ trên localStorage trình duyệt của chính người dùng đó.
    Tuyệt đối không ghi chung lên ổ đĩa server (tránh rò rỉ dữ liệu giữa nhiều người dùng).
    """
    safe_key = json.dumps(clean_api_key(key_to_save))
    safe_profile = json.dumps(student_profile or {}, ensure_ascii=False)

    if action == "save_key":
        components.html(
            f"""
            <script>
            try {{
                localStorage.setItem("anhminh_saved_gemini_key", {safe_key});
                localStorage.setItem("anhminh_key_decision", "saved");
            }} catch (e) {{}}
            </script>
            """,
            height=0,
        )
    elif action == "delete_key":
        components.html(
            """
            <script>
            try {
                localStorage.removeItem("anhminh_saved_gemini_key");
                localStorage.removeItem("anhminh_key_decision");
            } catch (e) {}
            </script>
            """,
            height=0,
        )
    elif action == "save_profile":
        components.html(
            f"""
            <script>
            try {{
                localStorage.setItem("anhminh_saved_student_profile", JSON.stringify({safe_profile}));
            }} catch (e) {{}}
            </script>
            """,
            height=0,
        )
    elif action == "delete_profile":
        components.html(
            """
            <script>
            try {
                localStorage.removeItem("anhminh_saved_student_profile");
            } catch (e) {}
            </script>
            """,
            height=0,
        )
    else:
        components.html(
            """
            <script>
            try {
                if (!sessionStorage.getItem("anhminh_bootstrapped_v8")) {
                    sessionStorage.setItem("anhminh_bootstrapped_v8", "1");
                    const url = new URL(window.parent.location.href);
                    let changed = false;

                    const savedKey = localStorage.getItem("anhminh_saved_gemini_key");
                    if (savedKey && savedKey.trim().length > 10) {
                        url.searchParams.set("_am_k", savedKey.trim());
                        changed = true;
                    }

                    const rawProf = localStorage.getItem("anhminh_saved_student_profile");
                    if (rawProf) {
                        const prof = JSON.parse(rawProf);
                        if (prof && prof.full_name && prof.university) {
                            url.searchParams.set("_am_n", prof.full_name);
                            url.searchParams.set("_am_y", prof.student_year || "Sinh viên Năm 4");
                            url.searchParams.set("_am_u", prof.university);
                            changed = true;
                        }
                    }

                    if (changed) {
                        window.parent.location.replace(url.toString());
                    }
                }
            } catch (e) {}
            </script>
            """,
            height=0,
        )


def log_user_locally(full_name: str, student_year: str, university: str) -> None:
    """Lưu danh sách người dùng đăng ký vào file log cục bộ để tác giả theo dõi."""
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
    """
    Gửi thông báo người dùng mới về email tác giả.
    Hỗ trợ 4 kênh: Gmail SMTP -> Formspree -> EmailJS -> FormSubmit.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log_user_locally(full_name, student_year, university)

    gmail_app_pwd = _get_secret_or_env("GMAIL_APP_PASSWORD", "")
    if gmail_app_pwd:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚢 [Anh Minh Translate] Sinh viên mới: {full_name} ({university})"
            msg["From"] = AUTHOR_NOTIFICATION_EMAIL
            msg["To"] = AUTHOR_NOTIFICATION_EMAIL
            html_body = f"""
            <div style="font-family:Arial,sans-serif;padding:16px;border:2px solid #0284C7;border-radius:12px;">
                <h3 style="color:#0369A1;margin-top:0;">🚢 Thông báo Sinh viên sử dụng Anh Minh Translate</h3>
                <p><b>👤 Họ và tên:</b> {esc(full_name)}</p>
                <p><b>🎓 Sinh viên năm:</b> {esc(student_year)}</p>
                <p><b>🏫 Trường đại học:</b> {esc(university)}</p>
                <p><b>🕒 Thời gian:</b> {now_str}</p>
            </div>
            """
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
        "Origin": "https://dich-thuat-anhminh.streamlit.app",
        "Referer": "https://dich-thuat-anhminh.streamlit.app/",
    }

    if FORMSPREE_ENDPOINT:
        try:
            fs_data = {
                "email": AUTHOR_NOTIFICATION_EMAIL,
                "Họ và tên": full_name,
                "Sinh viên năm": student_year,
                "Trường đại học": university,
                "Thời gian": now_str,
            }
            req_fsp = urllib.request.Request(
                FORMSPREE_ENDPOINT,
                data=json.dumps(fs_data).encode("utf-8"),
                headers=headers_json,
                method="POST",
            )
            with urllib.request.urlopen(req_fsp, timeout=8) as resp:
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

    payload_fs = {
        "_subject": f"🚢 [Anh Minh Translate] Người dùng mới: {full_name} ({university})",
        "_template": "table",
        "_captcha": "false",
        "Ho_va_Ten": full_name,
        "Sinh_vien_nam": student_year,
        "Truong_theo_hoc": university,
        "Thoi_gian": now_str,
        "Ung_dung": f"Anh Minh Translate {APP_VERSION} (СПбГМТУ)",
    }
    try:
        req_fs = urllib.request.Request(
            f"https://formsubmit.co/ajax/{AUTHOR_NOTIFICATION_EMAIL}",
            data=json.dumps(payload_fs).encode("utf-8"),
            headers=headers_json,
            method="POST",
        )
        with urllib.request.urlopen(req_fs, timeout=8) as resp:
            resp_body = resp.read().decode("utf-8", errors="ignore")
            if resp.status in (200, 201) and '"success":false' not in resp_body.lower():
                return True, "FormSubmit AJAX"
    except Exception:
        pass

    return False, "Client Browser Relay"


def trigger_client_side_email_relay(full_name: str, student_year: str, university: str) -> None:
    """Thực thi gửi thông báo dự phòng từ trình duyệt sau khi trang ổn định."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    safe_payload = json.dumps(
        {
            "_subject": f"🚢 [Anh Minh Translate] Sinh viên sử dụng: {full_name} ({university})",
            "_template": "table",
            "_captcha": "false",
            "Họ và tên": full_name,
            "Sinh viên năm": student_year,
            "Trường đại học": university,
            "Thời gian": now_str,
        },
        ensure_ascii=False,
    )
    safe_formspree = json.dumps(FORMSPREE_ENDPOINT)
    safe_name_html = esc(full_name)
    safe_year_html = esc(student_year)
    safe_uni_html = esc(university)

    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;overflow:hidden;">
            <iframe name="hidden_fs_iframe" style="display:none;"></iframe>
            <form id="fsAutoForm" action="https://formsubmit.co/{AUTHOR_NOTIFICATION_EMAIL}" method="POST" target="hidden_fs_iframe" style="display:none;">
                <input type="hidden" name="_subject" value="🚢 [Anh Minh Translate] Sinh viên mới: {safe_name_html} ({safe_uni_html})" />
                <input type="hidden" name="_template" value="table" />
                <input type="hidden" name="_captcha" value="false" />
                <input type="hidden" name="Họ và tên" value="{safe_name_html}" />
                <input type="hidden" name="Sinh viên năm" value="{safe_year_html}" />
                <input type="hidden" name="Trường đại học" value="{safe_uni_html}" />
                <input type="hidden" name="Thời gian" value="{now_str}" />
            </form>
            <script>
            (function() {{
                const payload = {safe_payload};
                const formspreeUrl = {safe_formspree};
                if (formspreeUrl) {{
                    fetch(formspreeUrl, {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json", "Accept": "application/json" }},
                        body: JSON.stringify(payload)
                    }}).catch(() => {{}});
                }}
                fetch("https://formsubmit.co/ajax/{AUTHOR_NOTIFICATION_EMAIL}", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json", "Accept": "application/json" }},
                    body: JSON.stringify(payload)
                }}).then(r => r.json()).then(data => {{
                    if (!data || data.success === "false" || data.success === false) {{
                        const f = document.getElementById("fsAutoForm");
                        if (f) f.submit();
                    }}
                }}).catch(() => {{
                    const f = document.getElementById("fsAutoForm");
                    if (f) f.submit();
                }});
            }})();
            </script>
        </body>
        </html>
        """,
        height=0,
    )


def get_fixed_author_portrait_svg_uri() -> str:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240">
      <defs>
        <linearGradient id="studioBg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#F5F6F8"/>
          <stop offset="100%" stop-color="#EAECEF"/>
        </linearGradient>
        <linearGradient id="skinTone" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#FCE5D8"/>
          <stop offset="100%" stop-color="#F3D1BE"/>
        </linearGradient>
        <linearGradient id="hairGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#2B211E"/>
          <stop offset="50%" stop-color="#1F1715"/>
          <stop offset="100%" stop-color="#332622"/>
        </linearGradient>
      </defs>
      <rect width="240" height="240" fill="url(#studioBg)"/>
      <path d="M18 240 C24 185, 65 172, 120 172 C175 172, 216 185, 222 240 Z" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.8"/>
      <rect x="97" y="138" width="46" height="42" rx="14" fill="#F1CEBC"/>
      <path d="M88 168 Q120 188 152 168" fill="none" stroke="#E5E7EB" stroke-width="6" stroke-linecap="round"/>
      <ellipse cx="69" cy="106" rx="8" ry="15" fill="#F3D1BE"/>
      <ellipse cx="171" cy="106" rx="8" ry="15" fill="#F3D1BE"/>
      <path d="M72 72 C72 40, 168 40, 168 72 C168 118, 149 152, 120 152 C91 152, 72 118, 72 72 Z" fill="url(#skinTone)"/>
      <path d="M84 85 Q98 80 110 85" stroke="#2A201D" stroke-width="3.6" fill="none" stroke-linecap="round"/>
      <path d="M130 85 Q142 80 156 85" stroke="#2A201D" stroke-width="3.6" fill="none" stroke-linecap="round"/>
      <ellipse cx="97" cy="96" rx="7.5" ry="4.8" fill="#FFFFFF"/>
      <ellipse cx="143" cy="96" rx="7.5" ry="4.8" fill="#FFFFFF"/>
      <circle cx="97" cy="96" r="4.3" fill="#2A1B17"/>
      <circle cx="143" cy="96" r="4.3" fill="#2A1B17"/>
      <circle cx="95.5" cy="94.5" r="1.4" fill="#FFFFFF"/>
      <circle cx="141.5" cy="94.5" r="1.4" fill="#FFFFFF"/>
      <rect x="78" y="86" width="38" height="24" rx="8" fill="rgba(255,255,255,0.12)" stroke="#3A302C" stroke-width="1.8"/>
      <rect x="124" y="86" width="38" height="24" rx="8" fill="rgba(255,255,255,0.12)" stroke="#3A302C" stroke-width="1.8"/>
      <path d="M78 90 Q97 85 116 90" stroke="#221C1A" stroke-width="3.4" fill="none" stroke-linecap="round"/>
      <path d="M124 90 Q143 85 162 90" stroke="#221C1A" stroke-width="3.4" fill="none" stroke-linecap="round"/>
      <path d="M116 93 Q120 90 124 93" stroke="#3A302C" stroke-width="2.2" fill="none"/>
      <line x1="71" y1="92" x2="78" y2="91" stroke="#221C1A" stroke-width="2.6"/>
      <line x1="162" y1="91" x2="169" y2="92" stroke="#221C1A" stroke-width="2.6"/>
      <path d="M120 95 L118 114 Q120 117 124 115" stroke="#DFB39E" stroke-width="2.4" fill="none" stroke-linecap="round"/>
      <path d="M106 128 Q120 133 134 128" stroke="#D97F76" stroke-width="3.8" fill="none" stroke-linecap="round"/>
      <path d="M108 128 Q120 125 132 128" stroke="#C86D65" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path d="M67 92 C60 48, 84 23, 120 23 C156 23, 180 48, 173 92 C169 66, 152 50, 130 47 C124 58, 115 67, 104 72 C109 58, 113 50, 115 43 C94 48, 75 66, 67 92 Z" fill="url(#hairGrad)"/>
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
    return get_fixed_author_portrait_svg_uri()


@st.cache_data(ttl=3600, show_spinner=False)
def shorten_share_url(long_url: str) -> str:
    clean_url = long_url.strip()
    if not clean_url.startswith(("http://", "https://")):
        return clean_url
    try:
        api_url = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(clean_url)}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            short = resp.read().decode("utf-8").strip()
            if short.startswith("http"):
                return short
    except Exception:
        pass
    return clean_url


# ==============================================================================
# 2. TỪ ĐIỂN TIẾNG LÓNG SINH VIÊN NGA (30 TỪ) & THUẬT NGỮ CHUYÊN NGÀNH MỞ RỘNG
# ==============================================================================
RUSSIAN_SLANG_DICT: List[Dict[str, str]] = [
    {"word": "препод", "accent": "пре́под", "full": "преподаватель", "en": "lecturer / professor", "vi": "Giảng viên, thầy/cô giáo đại học", "example": "Препод сегодня добрый, всех отпустил пораньше."},
    {"word": "курсач", "accent": "курса́ч", "full": "курсовая работа", "en": "term paper / course project", "vi": "Đồ án môn học / Tiểu luận học kỳ", "example": "Мне нужно сдать курсач до пятницы."},
    {"word": "лаба", "accent": "ла́ба", "full": "лабораторная работа", "en": "lab work / laboratory session", "vi": "Bài thí nghiệm / Giờ thực hành phòng Lab", "example": "У нас сегодня две лабы по физике."},
    {"word": "хвост", "accent": "хвост", "full": "академическая задолженность", "en": "academic debt / failed exam", "vi": "Nợ môn (chưa qua môn/thi trượt cần thi lại)", "example": "Нужно закрыть все хвосты до начала сессии."},
    {"word": "зачетка", "accent": "зачётка", "full": "зачётная книжка", "en": "student record book", "vi": "Sổ điểm sinh viên (dùng để giảng viên ký khi thi)", "example": "Не забудь взять зачётку на экзамен!"},
    {"word": "автомат", "accent": "автома́т", "full": "зачёт/экзамен автоматом", "en": "automatic pass (without final exam)", "vi": "Được miễn thi (qua môn/điểm tối đa nhờ tích cực)", "example": "Я ходил на все лекции и получил автомат!"},
    {"word": "пара", "accent": "па́ра", "full": "учебная пара (90 минут)", "en": "90-minute university class", "vi": "Ca học đại học (90 phút = 2 tiết)", "example": "Во сколько завтра первая пара?"},
    {"word": "общага", "accent": "обща́га", "full": "общежитие", "en": "dormitory / student hostel", "vi": "Ký túc xá (KTX) sinh viên", "example": "Вечером собираемся в общаге готовиться к сессии."},
    {"word": "стипуха", "accent": "стипу́ха", "full": "стипендия", "en": "stipend / scholarship", "vi": "Tiền học bổng hàng tháng", "example": "Ура, сегодня пришла стипуха!"},
    {"word": "окно", "accent": "окно́", "full": "свободное время между парами", "en": "free period between classes", "vi": "Ca trống giữa các tiết học trong ngày", "example": "У нас окно между второй и четвёртой парой, пойдём в столовку."},
    {"word": "сессия", "accent": "се́ссия", "full": "экзаменационная сессия", "en": "exam period / finals", "vi": "Kỳ thi học kỳ (mùa thi)", "example": "Зимняя сессия начинается в январе."},
    {"word": "пересдача", "accent": "пересда́ча", "full": "повторная сдача экзамена", "en": "retake / resit exam", "vi": "Thi lại", "example": "Комиссия назначила пересдачу на следующую неделю."},
    {"word": "деканат", "accent": "декана́т", "full": "администрация факультета", "en": "dean's office", "vi": "Văn phòng khoa / Phòng giáo vụ khoa", "example": "Возьми справку об обучении в деканате."},
    {"word": "шпора", "accent": "шпо́ра", "full": "шпаргалка", "en": "cheat sheet / crib note", "vi": "Phao thi / Tờ ghi chú nhỏ", "example": "Писать шпоры полезно для памяти, но доставать опасно."},
    {"word": "домашка", "accent": "дома́шка", "full": "домашнее задание (ДЗ)", "en": "homework / assignment", "vi": "Bài tập về nhà", "example": "Скинь домашку по матану, пожалуйста!"},
    {"word": "матан", "accent": "мата́н", "full": "математический анализ", "en": "calculus / mathematical analysis", "vi": "Môn Giải tích toán học", "example": "Завтра коллоквиум по матану."},
    {"word": "сопромат", "accent": "сопрома́т", "full": "сопротивление материалов", "en": "strength of materials", "vi": "Môn Sức bền vật liệu (kỹ thuật/đóng tàu/cơ khí)", "example": "Сдал сопромат — можно жениться!"},
    {"word": "научник", "accent": "нау́чник", "full": "научный руководитель", "en": "thesis supervisor", "vi": "Giảng viên hướng dẫn khoa học / đồ án", "example": "Мой научник одобрил тему диплома."},
    {"word": "инфа", "accent": "инфа́", "full": "информация", "en": "information / info", "vi": "Thông tin (hay dùng trong nhóm chat Telegram/VK)", "example": "Спасибо за инфу, передам группе!"},
    {"word": "преза", "accent": "пре́за", "full": "презентация", "en": "presentation / slide deck", "vi": "Bài thuyết trình PowerPoint / Slide", "example": "Ты уже сделал презу к завтрашнему семинару?"},
    {"word": "коллок", "accent": "колло́к", "full": "коллоквиум", "en": "colloquium / oral quiz", "vi": "Bài kiểm tra vấn đáp giữa kỳ", "example": "В среду будет коллок по гидромеханике."},
    {"word": "госы", "accent": "го́сы", "full": "государственные экзамены", "en": "state final exams", "vi": "Kỳ thi tốt nghiệp quốc gia", "example": "В июне сдаём госы и защищаем диплом."},
    {"word": "прогул", "accent": "прогу́л", "full": "пропуск занятия без причины", "en": "unexcused absence / skipping class", "vi": "Nghỉ học không phép / Cúp tiết", "example": "За прогулы без справки могут не поставить зачёт."},
    {"word": "отработка", "accent": "отрабо́тка", "full": "отработка пропущенного занятия", "en": "make-up class / lab", "vi": "Học bù / Làm bù bài thí nghiệm đã nghỉ", "example": "Мне нужно прийти на отработку лабы в пятницу."},
    {"word": "студак", "accent": "студа́к", "full": "студенческий билет", "en": "student ID card", "vi": "Thẻ sinh viên (dùng giảm giá vé tàu/bảo tàng)", "example": "Покажи студак на входе в корпус."},
    {"word": "пропуск", "accent": "про́пуск", "full": "электронный пропуск", "en": "access pass / entry badge", "vi": "Thẻ từ ra vào trường hoặc ký túc xá", "example": "Я забыл пропуск в комнате, не могу пройти через турникет."},
    {"word": "столовка", "accent": "столо́вка", "full": "студенческая столовая", "en": "university cafeteria / canteen", "vi": "Căng-tin / Nhà ăn sinh viên", "example": "Пойдём в столовку на большой перемене."},
    {"word": "академ", "accent": "акаде́м", "full": "академический отпуск", "en": "academic leave of absence", "vi": "Bảo lưu kết quả học tập", "example": "Он взял академ на один год по состоянию здоровья."},
    {"word": "староста", "accent": "ста́роста", "full": "староста учебной группы", "en": "class monitor / group leader", "vi": "Lớp trưởng", "example": "Староста отметила всех в журнале посещаемости."},
    {"word": "медосмотр", "accent": "медосмо́тр", "full": "медицинский осмотр", "en": "mandatory medical check-up", "vi": "Khám sức khỏe định kỳ (bắt buộc cho sinh viên quốc tế tại Nga)", "example": "Всем иностранным студентам нужно пройти медосмотр до конца месяца."},
]

DOMAIN_GLOSSARY: Dict[str, List[Dict[str, str]]] = {
    "Kỹ thuật & Đóng tàu": [
        {"ru": "судострое́ние", "en": "shipbuilding / naval architecture", "vi": "Kỹ thuật đóng tàu"},
        {"ru": "ко́рпус су́дна", "en": "ship hull", "vi": "Thân tàu / Kết cấu vỏ tàu"},
        {"ru": "водоизмеще́ние", "en": "displacement", "vi": "Lượng giãn nước"},
        {"ru": "чертёж", "en": "technical drawing / blueprint", "vi": "Bản vẽ kỹ thuật"},
        {"ru": "сопротивле́ние материа́лов", "en": "strength of materials", "vi": "Sức bền vật liệu"},
        {"ru": "гребно́й винт", "en": "propeller", "vi": "Chân vịt tàu thủy"},
        {"ru": "силова́я устано́вка", "en": "marine propulsion plant", "vi": "Hệ động lực tàu thủy"},
        {"ru": "осто́йчивость су́дна", "en": "vessel stability", "vi": "Tính ổn định của tàu"},
        {"ru": "плаву́честь", "en": "buoyancy", "vi": "Tính nổi"},
        {"ru": "непотопля́емость", "en": "unsinkability / damage stability", "vi": "Tính chống chìm"},
        {"ru": "шпанго́ут", "en": "hull frame / rib", "vi": "Sườn tàu"},
        {"ru": "киль", "en": "keel", "vi": "Sống chính (Ky tàu)"},
        {"ru": "па́луба", "en": "deck", "vi": "Boong tàu"},
        {"ru": "оса́дка су́дна", "en": "vessel draft / draught", "vi": "Mớn nước của tàu"},
        {"ru": "валопрово́д", "en": "shafting system", "vi": "Hệ trục chân vịt"},
        {"ru": "судострои́тельная верфь", "en": "shipyard", "vi": "Nhà máy đóng tàu"},
    ],
    "CNTT & Khoa học máy tính": [
        {"ru": "ба́за да́нных", "en": "database", "vi": "Cơ sở dữ liệu"},
        {"ru": "алгори́тм", "en": "algorithm", "vi": "Thuật toán"},
        {"ru": "иску́сственный интелле́кт", "en": "artificial intelligence", "vi": "Trí tuệ nhân tạo (AI)"},
        {"ru": "исхо́дный код", "en": "source code", "vi": "Mã nguồn"},
        {"ru": "нейро́нная сеть", "en": "neural network", "vi": "Mạng nơ-ron"},
        {"ru": "вычисли́тельная се́ть", "en": "computer network", "vi": "Mạng máy tính"},
        {"ru": "отла́дка", "en": "debugging", "vi": "Gỡ lỗi (Debug)"},
        {"ru": "архитекту́ра ПО", "en": "software architecture", "vi": "Kiến trúc phần mềm"},
    ],
    "Kinh tế & Quản trị": [
        {"ru": "себесто́имость", "en": "cost price / production cost", "vi": "Giá thành sản xuất"},
        {"ru": "бухга́лтерский учё́т", "en": "accounting", "vi": "Kế toán"},
        {"ru": "рента́бельность", "en": "profitability", "vi": "Khả năng sinh lời / Tỷ suất lợi nhuận"},
        {"ru": "инвести́ции", "en": "investments", "vi": "Đầu tư"},
        {"ru": "спрос и предложе́ние", "en": "supply and demand", "vi": "Cung và cầu"},
        {"ru": "валово́й вну́тренний проду́кт", "en": "gross domestic product (GDP)", "vi": "Tổng sản phẩm quốc nội (GDP)"},
    ],
    "Giao tiếp / Tin nhắn đời thường": [
        {"ru": "преподава́тель", "en": "lecturer / professor", "vi": "Giảng viên"},
        {"ru": "расписа́ние заня́тий", "en": "class schedule / timetable", "vi": "Thời khóa biểu"},
        {"ru": "консульта́ция", "en": "office hours / consultation", "vi": "Buổi giải đáp thắc mắc với giảng viên"},
        {"ru": "ста́роста гру́ппы", "en": "class monitor / group leader", "vi": "Lớp trưởng"},
        {"ru": "общежи́тие (обща́га)", "en": "student dormitory", "vi": "Ký túc xá sinh viên"},
        {"ru": "продле́ние ви́зы", "en": "visa extension", "vi": "Gia hạn thị thực (Visa)"},
        {"ru": "миграцио́нный учё́т", "en": "migration registration", "vi": "Đăng ký tạm trú (Регистрация)"},
    ],
    "Học thuật tổng hợp": [
        {"ru": "дипло́мная рабо́та", "en": "graduation thesis", "vi": "Khóa luận / Đồ án tốt nghiệp"},
        {"ru": "аннота́ция", "en": "abstract", "vi": "Tóm tắt bài báo/luận văn"},
        {"ru": "актуа́льность те́мы", "en": "relevance of the topic", "vi": "Tính cấp thiết của đề tài"},
        {"ru": "методоло́гия", "en": "methodology", "vi": "Phương pháp luận"},
        {"ru": "защи́та дипло́ма", "en": "thesis defense", "vi": "Bảo vệ đồ án tốt nghiệp"},
        {"ru": "спи́сок литерату́ры", "en": "references / bibliography", "vi": "Danh mục tài liệu tham khảo"},
    ],
}


# ==============================================================================
# 3. ĐỒ HỌA SVG HÀNG HẢI (СПбГМТУ OCEAN THEME)
# ==============================================================================
SVG_3D_SHIP_ILLUSTRATION = """
<svg width="155" height="115" viewBox="0 0 220 165" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 10px 14px rgba(3, 105, 161, 0.35));">
  <defs>
    <linearGradient id="hullGrad" x1="30" y1="95" x2="190" y2="135" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#0284C7"/>
      <stop offset="55%" stop-color="#0369A1"/>
      <stop offset="100%" stop-color="#082F49"/>
    </linearGradient>
    <linearGradient id="cabinGrad" x1="60" y1="45" x2="150" y2="95" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#E0F2FE"/>
    </linearGradient>
    <linearGradient id="sailAccent" x1="95" y1="15" x2="140" y2="60" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="100%" stop-color="#06B6D4"/>
    </linearGradient>
    <linearGradient id="waveGrad1" x1="0" y1="130" x2="220" y2="155" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="50%" stop-color="#06B6D4"/>
      <stop offset="100%" stop-color="#0284C7"/>
    </linearGradient>
  </defs>
  <circle cx="165" cy="42" r="24" fill="#FDE047" fill-opacity="0.28"/>
  <circle cx="165" cy="42" r="15" fill="#FEF08A" fill-opacity="0.55"/>
  <path d="M82 32H104L99 62H77L82 32Z" fill="url(#sailAccent)" stroke="#FFFFFF" stroke-width="1.5"/>
  <rect x="81" y="36" width="21" height="5" fill="#F43F5E"/>
  <path d="M122 22V60M112 32H132M116 42H128" stroke="#E0F2FE" stroke-width="2.5" stroke-linecap="round"/>
  <circle cx="122" cy="19" r="3.5" fill="#38BDF8"/>
  <path d="M58 62H152L162 88H48L58 62Z" fill="url(#cabinGrad)" stroke="#BAE6FD" stroke-width="1.5"/>
  <rect x="68" y="69" width="12" height="8" rx="2" fill="#0284C7"/>
  <rect x="86" y="69" width="12" height="8" rx="2" fill="#0284C7"/>
  <rect x="104" y="69" width="12" height="8" rx="2" fill="#0284C7"/>
  <rect x="122" y="69" width="18" height="8" rx="2" fill="#0369A1"/>
  <path d="M26 86L194 82L172 126H46L26 86Z" fill="url(#hullGrad)" stroke="#7DD3FC" stroke-width="1.8"/>
  <path d="M40 114L178 112L172 125H46L40 114Z" fill="#E11D48"/>
  <circle cx="162" cy="96" r="3" stroke="#FFFFFF" stroke-width="1.8"/>
  <path d="M162 99V109M156 105C156 109 168 109 168 105" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round"/>
  <circle cx="65" cy="99" r="3.5" fill="#E0F2FE"/>
  <circle cx="82" cy="99" r="3.5" fill="#E0F2FE"/>
  <circle cx="99" cy="99" r="3.5" fill="#E0F2FE"/>
  <circle cx="116" cy="99" r="3.5" fill="#E0F2FE"/>
  <path d="M10 126C28 118 44 118 62 126C80 134 98 134 116 126C134 118 152 118 170 126C188 134 202 130 212 124L216 144H6L10 126Z" fill="url(#waveGrad1)"/>
  <path d="M18 138C36 131 54 131 72 138C90 145 108 145 126 138C144 131 162 131 180 138C194 143 204 140 212 136" stroke="#E0F2FE" stroke-width="3" stroke-linecap="round"/>
</svg>
""".strip()

STICKER_SAILBOAT_MINI = """
<svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
  <path d="M24 6L38 30H24V6Z" fill="#06B6D4"/>
  <path d="M22 10L10 30H22V10Z" fill="#0284C7"/>
  <path d="M6 33H42L36 41H12L6 33Z" fill="#0369A1"/>
  <path d="M4 43C10 40 16 40 22 43C28 46 34 46 40 43" stroke="#38BDF8" stroke-width="3" stroke-linecap="round"/>
</svg>
""".strip()

STICKER_HELM_WHEEL = """
<svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
  <circle cx="24" cy="24" r="14" stroke="#0284C7" stroke-width="4" fill="#E0F2FE"/>
  <circle cx="24" cy="24" r="5" fill="#0369A1"/>
  <path d="M24 4V44M4 24H44M9.8 9.8L38.2 38.2M38.2 9.8L9.8 38.2" stroke="#0369A1" stroke-width="3.5" stroke-linecap="round"/>
</svg>
""".strip()

STICKER_COMPASS_3D = """
<svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
  <circle cx="24" cy="24" r="19" fill="#F0F9FF" stroke="#0284C7" stroke-width="3.5"/>
  <polygon points="24,7 29,24 24,21 19,24" fill="#EF4444"/>
  <polygon points="24,41 29,24 24,27 19,24" fill="#0369A1"/>
  <circle cx="24" cy="24" r="3" fill="#0F172A"/>
</svg>
""".strip()

STICKER_ANCHOR_3D = """
<svg width="24" height="24" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
  <circle cx="24" cy="10" r="4.5" stroke="#0284C7" stroke-width="3.5" fill="#E0F2FE"/>
  <path d="M24 15V40M15 21H33" stroke="#0369A1" stroke-width="4" stroke-linecap="round"/>
  <path d="M10 29C10 37 17 41 24 41C31 41 38 37 38 29" stroke="#0284C7" stroke-width="4" stroke-linecap="round"/>
</svg>
""".strip()


# ==============================================================================
# 4. CUSTOM CSS CHUYÊN NGHIỆP (OCEAN BLUE + MOBILE RESPONSIVE)
# ==============================================================================
def inject_ocean_blue_css(is_author_admin: bool = False) -> None:
    hide_github_and_edit_css = ""
    if not is_author_admin:
        hide_github_and_edit_css = """
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
        button[title="View app source on GitHub"],
        footer {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        """

    render_html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

        {hide_github_and_edit_css}

        :root {{
            --ocean-primary: #0284C7;
            --ocean-secondary: #0369A1;
            --ocean-accent: #06B6D4;
            --ocean-bg: #F0F9FF;
            --ocean-card: #FFFFFF;
            --ocean-text: #0F172A;
            --ocean-muted: #334155;
            --ocean-border: #BAE6FD;
            color-scheme: light !important;
        }}

        html, body, .stApp, div, p, label, h1, h2, h3, h4, h5, h6, button, input, textarea, table,
        span:not([data-testid="stIconMaterial"]):not(.material-icons) {{
            font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }}

        span[data-testid="stIconMaterial"], .material-icons {{
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
        }}

        .stApp {{
            background-color: #F0F9FF !important;
            background-image:
                radial-gradient(at 12% 15%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 88% 80%, rgba(2, 132, 199, 0.12) 0px, transparent 50%),
                linear-gradient(to right, rgba(186, 230, 253, 0.3) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(186, 230, 253, 0.3) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
            color: #0F172A !important;
        }}

        .main .block-container {{
            padding-top: 1.4rem !important;
        }}

        .main .block-container label,
        .main .block-container p,
        .main .block-container h1,
        .main .block-container h2,
        .main .block-container h3,
        .main .block-container h4,
        div[data-testid="stWidgetLabel"] p {{
            color: #0C4A6E !important;
            font-weight: 600 !important;
        }}

        div[data-testid="stTextArea"] textarea,
        .main input[type="text"] {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            caret-color: #0284C7 !important;
            border: 2px solid #7DD3FC !important;
            border-radius: 14px !important;
            font-size: 1.03rem !important;
            line-height: 1.65 !important;
            font-weight: 500 !important;
            padding: 14px 16px !important;
            box-shadow: inset 0 2px 6px rgba(2, 132, 199, 0.05), 0 4px 12px rgba(2, 132, 199, 0.06) !important;
        }}
        div[data-testid="stTextArea"] textarea:focus {{
            border-color: #0284C7 !important;
            box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.18) !important;
        }}

        .main div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #7DD3FC !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
        }}

        div[data-testid="stTabs"] div[role="tablist"] {{
            gap: 10px;
            border-bottom: 2px solid #BAE6FD !important;
            padding-bottom: 6px;
            flex-wrap: wrap;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] {{
            background-color: #FFFFFF !important;
            border-radius: 14px 14px 4px 4px !important;
            padding: 11px 18px !important;
            border: 2px solid #7DD3FC !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.07) !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] p {{
            color: #0369A1 !important;
            font-weight: 700 !important;
            font-size: 0.94rem !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            border-color: #0369A1 !important;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.28) !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {{
            color: #FFFFFF !important;
        }}

        /* SIDEBAR */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #061E33 0%, #0C4A6E 55%, #0369A1 100%) !important;
            border-right: 2px solid #38BDF8 !important;
        }}
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] li,
        section[data-testid="stSidebar"] small {{
            color: #F0F9FF !important;
        }}
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="input"],
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="base-input"] {{
            background-color: #FFFFFF !important;
            border: 2px solid #38BDF8 !important;
            border-radius: 10px !important;
        }}
        section[data-testid="stSidebar"] .stTextInput input {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            border: none !important;
            font-weight: 600 !important;
        }}
        section[data-testid="stSidebar"] .stTextInput button {{
            background-color: #FFFFFF !important;
            color: #0369A1 !important;
        }}
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border: 2px solid #38BDF8 !important;
            border-radius: 10px !important;
        }}
        section[data-testid="stSidebar"] div[data-baseweb="select"] span,
        section[data-testid="stSidebar"] div[data-baseweb="select"] div {{
            color: #0F172A !important;
            font-weight: 700 !important;
        }}
        section[data-testid="stSidebar"] details {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(186, 230, 253, 0.35) !important;
            border-radius: 10px !important;
            margin-bottom: 6px !important;
        }}

        .gemini-key-link-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            background: linear-gradient(135deg, #38BDF8 0%, #0284C7 100%);
            color: #FFFFFF !important;
            text-decoration: none !important;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 10px 14px;
            border-radius: 11px;
            border: 1.5px solid #BAE6FD;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
            margin-top: 4px;
            margin-bottom: 10px;
            text-align: center;
        }}
        .author-sidebar-card {{
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.16) 0%, rgba(14, 116, 144, 0.35) 100%);
            border: 1.5px solid rgba(125, 211, 252, 0.6);
            border-radius: 18px;
            padding: 14px;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 13px;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
        }}
        .author-avatar-img {{
            width: 66px;
            height: 66px;
            border-radius: 50%;
            object-fit: cover;
            border: 2.5px solid #38BDF8;
            background: #FFFFFF;
            flex-shrink: 0;
        }}
        .author-info-name {{
            font-size: 1.04rem;
            font-weight: 800;
            color: #FFFFFF !important;
            line-height: 1.25;
        }}
        .author-info-role {{
            font-size: 0.77rem;
            font-weight: 600;
            color: #BAE6FD !important;
            line-height: 1.38;
        }}
        .author-uni-badge {{
            display: inline-block;
            margin-top: 5px;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.25);
            border: 1px solid rgba(125, 211, 252, 0.5);
            font-size: 0.72rem;
            font-weight: 700;
            color: #E0F2FE !important;
        }}
        .user-checkin-card {{
            background: linear-gradient(145deg, rgba(14, 116, 144, 0.4) 0%, rgba(8, 47, 73, 0.65) 100%);
            border: 1.5px solid #38BDF8;
            border-radius: 16px;
            padding: 12px 14px;
            margin-bottom: 12px;
        }}
        .saved-student-badge-box {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.22) 0%, rgba(3, 105, 161, 0.45) 100%);
            border: 1.5px solid #6EE7B7;
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }}

        .am-hero-banner {{
            background: linear-gradient(130deg, #082F49 0%, #0369A1 45%, #0284C7 80%, #06B6D4 100%);
            border-radius: 24px;
            padding: 22px 28px;
            color: #FFFFFF !important;
            box-shadow: 0 18px 38px rgba(3, 105, 161, 0.25);
            margin-bottom: 20px;
            border: 2px solid rgba(125, 211, 252, 0.45);
        }}
        .am-brand-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .am-brand-left {{
            display: flex;
            align-items: center;
            gap: 22px;
            flex: 1;
            flex-wrap: wrap;
            min-width: 280px;
        }}
        .author-hero-box {{
            display: flex;
            align-items: center;
            gap: 14px;
            background: rgba(8, 47, 73, 0.55);
            border: 1.5px solid rgba(125, 211, 252, 0.65);
            border-radius: 18px;
            padding: 12px 16px;
            max-width: 390px;
        }}
        .author-hero-avatar {{
            width: 72px;
            height: 72px;
            border-radius: 16px;
            object-fit: cover;
            border: 2.5px solid #7DD3FC;
            background: #FFFFFF;
            flex-shrink: 0;
        }}
        .am-title {{
            font-size: 1.92rem !important;
            font-weight: 800 !important;
            margin: 0 !important;
            color: #FFFFFF !important;
        }}
        .am-title span.highlight {{
            color: #7DD3FC !important;
        }}
        .am-subtitle {{
            font-size: 0.95rem !important;
            color: #E0F2FE !important;
            margin-top: 5px !important;
            font-weight: 500 !important;
        }}
        .am-badges {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .am-badge {{
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.38);
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.79rem;
            font-weight: 600;
            color: #FFFFFF !important;
        }}

        .ocean-card {{
            background: rgba(255, 255, 255, 0.97);
            border-radius: 20px;
            padding: 20px 24px;
            border: 1.5px solid #BAE6FD;
            box-shadow: 0 10px 28px rgba(2, 132, 199, 0.08);
            margin-bottom: 18px;
        }}
        .ocean-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid #E0F2FE;
            padding-bottom: 10px;
            margin-bottom: 14px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .ocean-card-title {{
            font-size: 1.08rem !important;
            font-weight: 800 !important;
            color: #0369A1 !important;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .ocean-pill {{
            background: linear-gradient(135deg, #E0F2FE 0%, #CFFAFE 100%);
            color: #0369A1 !important;
            font-size: 0.77rem;
            font-weight: 700;
            padding: 5px 13px;
            border-radius: 999px;
            border: 1px solid #7DD3FC;
        }}
        .translation-main-text {{
            font-size: 1.12rem !important;
            line-height: 1.72 !important;
            color: #0F172A !important;
            font-weight: 600 !important;
            background: #F8FAFC;
            padding: 16px 20px;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
            border-left: 6px solid #0284C7;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .lang-card-header {{
            font-size: 0.94rem !important;
            font-weight: 800 !important;
            color: #0C4A6E !important;
            margin-bottom: 8px;
        }}
        .lang-compare-box-ru, .lang-compare-box-vi, .lang-compare-box-en {{
            background: #FFFFFF;
            border-radius: 14px;
            padding: 14px 16px;
            font-size: 1.0rem;
            font-weight: 600;
            line-height: 1.6;
            margin-bottom: 8px;
            min-height: 86px;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .lang-compare-box-ru {{ border: 1.5px solid #93C5FD; border-top: 5px solid #0284C7; color: #0F172A !important; }}
        .lang-compare-box-vi {{ border: 1.5px solid #6EE7B7; border-top: 5px solid #059669; color: #064E3B !important; }}
        .lang-compare-box-en {{ border: 1.5px solid #FCD34D; border-top: 5px solid #D97706; color: #78350F !important; }}

        .tone-box-formal {{
            background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
            border: 1.5px solid #7DD3FC;
            border-left: 6px solid #0369A1;
            border-radius: 14px;
            padding: 15px 18px;
            margin-bottom: 8px;
        }}
        .tone-box-casual {{
            background: linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%);
            border: 1.5px solid #67E8F9;
            border-left: 6px solid #06B6D4;
            border-radius: 14px;
            padding: 15px 18px;
            margin-bottom: 8px;
        }}
        .tone-title {{ font-weight: 800; font-size: 0.94rem; color: #0C4A6E !important; margin-bottom: 6px; }}
        .tone-ru {{ font-size: 1.08rem; font-weight: 700; color: #0F172A !important; margin-bottom: 8px; line-height: 1.55; }}
        .tone-note {{ font-size: 0.87rem; color: #334155 !important; line-height: 1.5; }}

        .vocab-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 0.95rem;
            border-radius: 12px;
            overflow: hidden;
        }}
        .vocab-table th {{
            background: linear-gradient(90deg, #0369A1 0%, #0284C7 100%);
            color: #FFFFFF !important;
            text-align: left;
            padding: 11px 14px;
            font-weight: 700;
        }}
        .vocab-table td {{
            padding: 11px 14px;
            border-bottom: 1px solid #E2E8F0;
            color: #0F172A !important;
            font-weight: 500;
        }}
        .vocab-table tr:nth-child(even) {{ background-color: #F0F9FF; }}

        .flashcard-box {{
            background: linear-gradient(145deg, #FFFFFF 0%, #E0F2FE 100%);
            border: 2.5px solid #0284C7;
            border-radius: 22px;
            padding: 34px 28px;
            text-align: center;
            box-shadow: 0 14px 32px rgba(2, 132, 199, 0.14);
            margin: 12px 0;
        }}
        .flashcard-ru {{
            font-size: 2.0rem;
            font-weight: 800;
            color: #0369A1;
            margin-bottom: 10px;
        }}
        .flashcard-meaning {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #065F46;
            margin-top: 12px;
            padding-top: 12px;
            border-top: 2px dashed #7DD3FC;
        }}

        div.stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.62rem 1.3rem !important;
            font-weight: 700 !important;
            box-shadow: 0 6px 16px rgba(2, 132, 199, 0.28) !important;
        }}
        div.stButton > button[kind="primary"] p {{ color: #FFFFFF !important; }}
        div.stButton > button[kind="secondary"] {{
            border-radius: 12px !important;
            border: 2px solid #38BDF8 !important;
            background-color: #FFFFFF !important;
            color: #0369A1 !important;
            font-weight: 700 !important;
        }}
        div.stButton > button[kind="secondary"] p {{ color: #0369A1 !important; }}

        .slang-item {{
            background: #F0F9FF;
            border: 1.5px solid #BAE6FD;
            border-radius: 12px;
            padding: 11px 15px;
            margin-bottom: 10px;
            color: #0F172A !important;
        }}
        .slang-word {{ font-weight: 800; color: #0284C7 !important; font-size: 1.03rem; }}

        .nautical-divider {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin: 18px 0;
            color: #0284C7;
            font-weight: 700;
            font-size: 0.84rem;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            text-align: center;
        }}
        .nautical-divider::before, .nautical-divider::after {{
            content: "";
            flex: 1;
            height: 1.5px;
            background: linear-gradient(90deg, transparent, #7DD3FC, transparent);
        }}

        @media (max-width: 768px) {{
            .main .block-container {{ padding: 0.8rem 0.7rem !important; }}
            .am-hero-banner {{ padding: 15px 14px !important; border-radius: 18px !important; }}
            .am-title {{ font-size: 1.42rem !important; }}
            .am-ship-art {{ display: none !important; }}
            .ocean-card {{ padding: 14px 13px !important; }}
            .flashcard-ru {{ font-size: 1.5rem !important; }}
        }}
        </style>
        """
    )


def render_brand_header(avatar_uri: str) -> None:
    render_html(
        f"""
        <div class="am-hero-banner">
            <div class="am-brand-row">
                <div class="am-brand-left">
                    <div class="author-hero-box">
                        <img src="{avatar_uri}" class="author-hero-avatar" alt="Mai Văn Minh" />
                        <div>
                            <div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:#7DD3FC; font-weight:700;">⚓ Tác giả & Phát triển</div>
                            <div style="font-size:1.12rem; font-weight:800; color:#FFFFFF; margin:2px 0;">Mai Văn Minh</div>
                            <div style="font-size:0.81rem; color:#E0F2FE; line-height:1.35; font-weight:500;">
                                Sinh viên năm 4 — Chuyên ngành Đóng tàu<br/>
                                <b>Trường Kỹ thuật Hàng hải Xanh-Petecbua (СПбГМТУ)</b>
                            </div>
                        </div>
                    </div>
                    <div style="flex:1; min-width:240px;">
                        <h1 class="am-title">🚢 <span class="highlight">Anh Minh</span> Translate <span style="font-size:0.95rem;background:rgba(255,255,255,0.2);padding:3px 10px;border-radius:999px;vertical-align:middle;">{APP_VERSION}</span></h1>
                        <div class="am-subtitle">Hệ sinh thái Dịch thuật, OCR Slide, Thu âm Giảng đường & Flashcard cho Sinh viên Việt tại Nga</div>
                        <div class="am-badges">
                            <span class="am-badge">⚓ Kỹ thuật & Đóng tàu</span>
                            <span class="am-badge">📸 OCR Dịch Ảnh Slide / Tài liệu</span>
                            <span class="am-badge">🎙️ Hybrid Voice AI & Audio Đa định dạng</span>
                            <span class="am-badge">🎴 Flashcards & Xuất Anki CSV</span>
                        </div>
                    </div>
                </div>
                <div class="am-ship-art" title="Con tàu tri thức vượt đại dương">
                    {SVG_3D_SHIP_ILLUSTRATION}
                </div>
            </div>
        </div>
        """
    )


# ==============================================================================
# 5. ĐỘNG CƠ DỊCH ĐA LUỒNG CHIA ĐOẠN THÔNG MINH + GEMINI AI + OCR VISION
# ==============================================================================
def detect_slang_in_text(text: str) -> List[Dict[str, str]]:
    if not text:
        return []
    text_lower = text.lower()
    detected = []
    seen_words = set()
    for item in RUSSIAN_SLANG_DICT:
        w = item["word"]
        base_stem = w[:-1] if (len(w) >= 4 and w[-1] in "аяоеыи") or len(w) > 4 else w
        pattern = rf"\b{re.escape(base_stem)}[а-яё]*\b"
        if re.search(pattern, text_lower) and item["word"] not in seen_words:
            detected.append(item)
            seen_words.add(item["word"])
    return detected


def chunk_text_smart(text: str, max_chars: int = 1200) -> List[str]:
    """
    Chia văn bản dài thành các đoạn hợp lý theo dòng/câu (tối đa max_chars)
    để không bao giờ bị cắt cụt khi dịch qua API miễn phí.
    """
    cleaned = text.strip()
    if len(cleaned) <= max_chars:
        return [cleaned] if cleaned else []

    paragraphs = cleaned.split("\n")
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
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
                sentences = re.split(r"(?<=[.!?…])\s+", para_s)
                for sent in sentences:
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
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp.read()
    except Exception:
        return None


def _try_multi_endpoint_translate(cleaned: str, src: str, tgt: str) -> Optional[str]:
    headers_form = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    }
    post_body = urllib.parse.urlencode({"sl": src, "tl": tgt, "q": cleaned}).encode("utf-8")

    # Cổng 1: Google Translate GTX POST
    try:
        req1 = urllib.request.Request(
            "https://translate.googleapis.com/translate_a/single?client=gtx&dt=t",
            data=post_body,
            headers=headers_form,
            method="POST",
        )
        with urllib.request.urlopen(req1, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], list):
                chunks = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
                if chunks:
                    return "".join(chunks)
    except Exception:
        pass

    # Cổng 2: Google Translate Android Endpoint
    try:
        req2 = urllib.request.Request(
            "https://translate.google.com/translate_a/single?client=at&dt=t&dj=1",
            data=post_body,
            headers=headers_form,
            method="POST",
        )
        with urllib.request.urlopen(req2, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sentences = data.get("sentences", [])
            if sentences:
                chunks = [s.get("trans", "") for s in sentences if s.get("trans")]
                if chunks:
                    return "".join(chunks)
    except Exception:
        pass

    # Cổng 3: Chrome Extension Endpoint
    try:
        req3 = urllib.request.Request(
            "https://clients5.google.com/translate_a/t?client=dict-chrome-ex",
            data=post_body,
            headers=headers_form,
            method="POST",
        )
        with urllib.request.urlopen(req3, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data:
                if isinstance(data[0], str):
                    return data[0]
                if isinstance(data[0], list):
                    return "".join(str(x[0]) for x in data if isinstance(x, list) and x)
            elif isinstance(data, dict) and "sentences" in data:
                return "".join(s.get("trans", "") for s in data["sentences"] if s.get("trans"))
    except Exception:
        pass

    # Cổng 4: MyMemory API (dự phòng đoạn ngắn <= 480 ký tự)
    if len(cleaned) <= 480:
        try:
            src_mm = "ru" if src == "auto" else src
            mm_url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(cleaned)}&langpair={src_mm}|{tgt}"
            req4 = urllib.request.Request(mm_url, headers={"User-Agent": headers_form["User-Agent"]})
            with urllib.request.urlopen(req4, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                trans_text = data.get("responseData", {}).get("translatedText", "")
                if trans_text and "MYMEMORY WARNING" not in trans_text.upper():
                    return trans_text
        except Exception:
            pass

    # Cổng 5: deep-translator fallback
    if GoogleTranslator is not None:
        try:
            res = GoogleTranslator(source=src, target=tgt).translate(cleaned)
            if res and "too many requests" not in res.lower():
                return res
        except Exception:
            pass

    return None


def _get_lru_cache() -> OrderedDict:
    if "translation_mem_cache" not in st.session_state or not isinstance(
        st.session_state["translation_mem_cache"], OrderedDict
    ):
        st.session_state["translation_mem_cache"] = OrderedDict()
    return st.session_state["translation_mem_cache"]


def fast_free_translate(text: str, src: str, tgt: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if src == tgt:
        return cleaned

    cache = _get_lru_cache()
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

    return "⚠️ Máy chủ dịch miễn phí đang bận. Bạn hãy bấm lại nút «🚀 Dịch & Phân Tích Ngay» hoặc dán Gemini API Key ở thanh bên trái nhé!"


def discover_available_gemini_models(api_key: str) -> List[str]:
    clean_k = clean_api_key(api_key)
    preferred_order = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]
    if not clean_k:
        return preferred_order

    cache_name = f"gemini_models_{hashlib.sha256(clean_k.encode('utf-8')).hexdigest()[:12]}"
    if cache_name in st.session_state:
        return st.session_state[cache_name]

    discovered: List[str] = []
    for api_ver in ("v1beta", "v1"):
        try:
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={urllib.parse.quote(clean_k)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        short_name = m.get("name", "").replace("models/", "")
                        if "gemini" in short_name and "embedding" not in short_name:
                            if short_name not in discovered:
                                discovered.append(short_name)
                if discovered:
                    break
        except Exception:
            pass

    if discovered:
        ordered = [p for p in preferred_order if p in discovered]
        for d in discovered:
            if d not in ordered:
                ordered.append(d)
        st.session_state[cache_name] = ordered
        return ordered

    return preferred_order


def call_gemini_multimodal_rest(
    api_key: str,
    parts: List[Dict[str, Any]],
    expect_json: bool = True,
    temperature: float = 0.2,
    timeout_sec: int = 25,
) -> Tuple[Optional[str], Optional[str]]:
    """Gọi Gemini REST API hỗ trợ cả văn bản, hình ảnh (OCR) và âm thanh với retry thông minh."""
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return None, "Empty API Key"

    models_to_try = discover_available_gemini_models(clean_k)
    last_error = ""

    for model_name in models_to_try[:5]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
        gen_cfg: Dict[str, Any] = {"temperature": temperature}
        if expect_json:
            gen_cfg["responseMimeType"] = "application/json"

        payload = {"contents": [{"parts": parts}], "generationConfig": gen_cfg}
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    candidates = resp_data.get("candidates", [])
                    if candidates:
                        resp_parts = candidates[0].get("content", {}).get("parts", [])
                        if resp_parts and "text" in resp_parts[0]:
                            return resp_parts[0]["text"], None
            except urllib.error.HTTPError as http_err:
                err_body = ""
                try:
                    err_body = http_err.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                last_error = f"HTTP {http_err.code}: {err_body[:180]}"
                if "API_KEY_INVALID" in err_body:
                    return None, "Mã Gemini API Key không chính xác. Vui lòng kiểm tra lại!"
                if http_err.code in (429, 503) and attempt == 0:
                    time.sleep(0.9)
                    continue
                if http_err.code == 400 and expect_json:
                    payload["generationConfig"] = {"temperature": temperature}
                    continue
                break
            except Exception as exc:
                last_error = str(exc)
                break

    return None, last_error


def _parse_json_response(raw_text: str) -> Optional[Dict]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.IGNORECASE)
    json_match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    return json.loads(cleaned)


def call_gemini_smart_translate(
    api_key: str,
    source_text: str,
    direction: str,
    domain: str,
) -> Tuple[Optional[Dict], Optional[str]]:
    system_prompt = f"""
Bạn là chuyên gia dịch thuật cao cấp Nga - Việt - Anh (RU - VI - EN) và cố vấn học thuật cho sinh viên Việt Nam tại Nga.
Chuyên ngành ưu tiên: "{domain}". Chiều dịch: "{direction}".
CHỈ TRẢ VỀ đúng 1 đối tượng JSON hợp lệ (không thêm markdown) theo cấu trúc sau:
{{
  "main_translation": "Bản dịch tự nhiên, chuẩn thuật ngữ nhất theo chiều dịch đã chọn",
  "ru_version": "Bản tiếng Nga tương ứng",
  "vi_version": "Bản tiếng Việt chuẩn thuật ngữ đại học",
  "en_version": "Bản tiếng Anh đối chiếu",
  "slang_explanations": [
    {{"term": "Từ lóng/viết tắt", "full_form": "Dạng đầy đủ tiếng Nga", "meaning_vi": "Giải nghĩa tiếng Việt"}}
  ],
  "vocabulary_table": [
    {{"ru_accent": "Từ tiếng Nga có dấu trọng âm \\u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu tiếng Nga lịch sự ngôi «Вы»",
    "formal_vy_vi_note": "Giải thích & dịch nghĩa câu trang trọng",
    "casual_ty": "Câu tiếng Nga thân mật ngôi «Ты»",
    "casual_ty_vi_note": "Giải thích & dịch nghĩa câu thân mật"
  }},
  "grammar_notes": "1-2 ghi chú ngữ pháp tiếng Nga quan trọng xuất hiện trong câu (cách/giống/động từ/cấu trúc).",
  "study_tip": "1 mẹo ngắn gọn về giao tiếp hoặc thuật ngữ đại học tại Nga."
}}
"""
    raw_text, err = call_gemini_multimodal_rest(
        api_key=api_key,
        parts=[{"text": f"{system_prompt}\n\n---\nVăn bản cần xử lý:\n{source_text}"}],
        expect_json=True,
        temperature=0.2,
    )
    if not raw_text:
        return None, err
    try:
        return _parse_json_response(raw_text), None
    except Exception as exc:
        return None, str(exc)


def call_gemini_ocr_and_translate_image(
    api_key: str,
    image_bytes: bytes,
    mime_type: str,
    direction: str,
    domain: str,
) -> Tuple[Optional[Dict], Optional[str]]:
    """OCR ảnh chụp slide giảng đường, bảng viết hoặc tin nhắn rồi dịch thuật học thuật."""
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    prompt = f"""
Bạn là trợ lý học thuật Nga - Việt - Anh chuyên ngành "{domain}".
Hãy đọc chính xác toàn bộ chữ trong ảnh đính kèm (slide bài giảng, bảng viết tay, tài liệu hoặc ảnh chụp tin nhắn), sau đó dịch theo chiều "{direction}".
CHỈ TRẢ VỀ đúng 1 đối tượng JSON hợp lệ:
{{
  "extracted_text": "Toàn bộ văn bản gốc đọc được từ ảnh (giữ xuống dòng hợp lý)",
  "main_translation": "Bản dịch tự nhiên, chuẩn chuyên ngành",
  "ru_version": "Bản tiếng Nga",
  "vi_version": "Bản tiếng Việt",
  "en_version": "Bản tiếng Anh đối chiếu",
  "slang_explanations": [],
  "vocabulary_table": [
    {{"ru_accent": "Từ khóa tiếng Nga có dấu trọng âm \\u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu hỏi/phản hồi lịch sự ngôi «Вы» liên quan đến nội dung ảnh",
    "formal_vy_vi_note": "Giải thích tiếng Việt",
    "casual_ty": "Câu trao đổi thân mật ngôi «Ты» với bạn học",
    "casual_ty_vi_note": "Giải thích tiếng Việt"
  }},
  "grammar_notes": "Ghi chú thuật ngữ/ngữ pháp nổi bật trong ảnh.",
  "study_tip": "Tóm tắt 1-2 ý cốt lõi cần nhớ từ ảnh này để ôn thi."
}}
"""
    raw_text, err = call_gemini_multimodal_rest(
        api_key=api_key,
        parts=[
            {"text": prompt},
            {"inlineData": {"mimeType": mime_type, "data": b64_img}},
        ],
        expect_json=True,
        temperature=0.15,
        timeout_sec=30,
    )
    if not raw_text:
        return None, err
    try:
        return _parse_json_response(raw_text), None
    except Exception as exc:
        return None, str(exc)


def extract_text_from_uploaded_doc(uploaded_file) -> Tuple[Optional[str], Optional[str]]:
    """Trích xuất văn bản từ file .txt, .docx hoặc .pdf tải lên."""
    name = uploaded_file.name.lower()
    raw_bytes = uploaded_file.getvalue()
    if name.endswith(".txt") or name.endswith(".md"):
        for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
            try:
                return raw_bytes.decode(enc).strip(), None
            except Exception:
                continue
        return None, "Không thể giải mã file văn bản này."

    if name.endswith(".docx"):
        if python_docx is None:
            return None, "Thiếu thư viện `python-docx`. Hãy thêm `python-docx` vào `requirements.txt`."
        try:
            doc = python_docx.Document(io.BytesIO(raw_bytes))
            text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
            return text, None
        except Exception as exc:
            return None, f"Lỗi đọc file .docx: {exc}"

    if name.endswith(".pdf"):
        if PdfReader is None:
            return None, "Thiếu thư viện `pypdf`. Hãy thêm `pypdf` vào `requirements.txt`."
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages = [page.extract_text() or "" for page in reader.pages[:15]]
            text = "\n\n".join(p.strip() for p in pages if p.strip())
            if not text:
                return None, "File PDF này là dạng ảnh scan (không có lớp chữ). Hãy chụp ảnh trang cần dịch và dùng mục **Dịch ảnh Slide/Tài liệu**!"
            return text, None
        except Exception as exc:
            return None, f"Lỗi đọc file .pdf: {exc}"

    return None, "Định dạng file chưa được hỗ trợ."


def fallback_smart_translate(source_text: str, direction: str, domain: str) -> Dict:
    text_for_translation = source_text.strip()
    detected_slang = detect_slang_in_text(text_for_translation)
    expanded_ru_text = text_for_translation

    slang_inflections = {
        "препод": "преподаватель",
        "курсач": "курсовую работу",
        "лабу": "лабораторную работу",
        "лаба": "лабораторная работа",
        "лабы": "лабораторные работы",
        "хвосты": "академические задолженности",
        "хвост": "академическую задолженность",
        "общаге": "общежитии",
        "общага": "общежитие",
        "стипуха": "стипендия",
        "зачетку": "зачётную книжку",
        "зачетка": "зачётная книжка",
        "инфу": "информацию",
        "инфа": "информация",
        "презу": "презентацию",
        "преза": "презентация",
        "студак": "студенческий билет",
        "столовку": "столовую",
    }
    for slang_form, full_replacement in slang_inflections.items():
        expanded_ru_text = re.sub(
            rf"\b{re.escape(slang_form)}\b",
            full_replacement,
            expanded_ru_text,
            flags=re.IGNORECASE,
        )

    with ThreadPoolExecutor(max_workers=3) as executor:
        if direction == DIRECTION_OPTIONS[0]:
            fut_vi = executor.submit(fast_free_translate, expanded_ru_text, "ru", "vi")
            fut_en = executor.submit(fast_free_translate, expanded_ru_text, "ru", "en")
            vi_ver = fut_vi.result()
            en_ver = fut_en.result()
            ru_ver = source_text
            main_trans = vi_ver
        elif direction == DIRECTION_OPTIONS[1]:
            fut_ru = executor.submit(fast_free_translate, text_for_translation, "vi", "ru")
            fut_en = executor.submit(fast_free_translate, text_for_translation, "vi", "en")
            ru_ver = fut_ru.result()
            en_ver = fut_en.result()
            vi_ver = source_text
            main_trans = ru_ver
        else:
            has_cyrillic = bool(re.search(r"[а-яА-ЯёЁ]", text_for_translation))
            src_guess = "ru" if has_cyrillic else "auto"
            fut_vi = executor.submit(fast_free_translate, expanded_ru_text, src_guess, "vi")
            fut_en = executor.submit(fast_free_translate, expanded_ru_text, src_guess, "en")
            if has_cyrillic:
                ru_ver = source_text
            else:
                fut_ru = executor.submit(fast_free_translate, text_for_translation, "auto", "ru")
                ru_ver = fut_ru.result()
            vi_ver = fut_vi.result()
            en_ver = fut_en.result()
            main_trans = f"🇻🇳 Tiếng Việt:\n{vi_ver}\n\n🇷🇺 Tiếng Nga:\n{ru_ver}\n\n🇬🇧 Tiếng Anh:\n{en_ver}"

    if direction == DIRECTION_OPTIONS[0]:
        formal_vy_full = "Здравствуйте! Спасибо за важную информацию, мы обязательно примем это к сведению и всё выполним по правилам."
        formal_note = "Mẫu câu trả lời lễ phép (Ngôi «Вы» — Gửi Giảng viên / Phòng Visa / Деканат)."
        casual_ty_full = "Привет! Понял, спасибо за инфу! Обязательно передам ребятам, всё сделаем как надо."
        casual_note = "Mẫu câu trả lời thân mật (Ngôi «Ты» — Nhắn bạn học / nhóm chat Telegram)."
    else:
        base_ru = ru_ver.strip()
        formal_vy = re.sub(r"\bты\b", "Вы", base_ru, flags=re.IGNORECASE)
        formal_vy = re.sub(r"\bтебя\b", "Вас", formal_vy, flags=re.IGNORECASE)
        formal_vy = re.sub(r"\bтебе\b", "Вам", formal_vy, flags=re.IGNORECASE)
        formal_vy = re.sub(r"\bпривет\b", "Здравствуйте", formal_vy, flags=re.IGNORECASE)
        if not formal_vy.lower().startswith(("здравствуйте", "добрый день", "уважаем")):
            formal_vy_full = f"Здравствуйте! {formal_vy} С уважением."
        else:
            formal_vy_full = formal_vy
        formal_note = "Dùng khi nhắn email/Telegram cho Giáo sư, Giảng viên (Преподаватель) hoặc Văn phòng khoa (Деканат)."

        casual_ty = re.sub(r"\bВы\b", "ты", base_ru)
        casual_ty = re.sub(r"\bВас\b", "тебя", casual_ty)
        casual_ty = re.sub(r"\bВам\b", "тебе", casual_ty)
        casual_ty = re.sub(r"\bЗдравствуйте\b", "Привет", casual_ty, flags=re.IGNORECASE)
        casual_ty_full = casual_ty if casual_ty.lower().startswith(("привет", "слушай", "салют")) else f"Привет! {casual_ty}"
        casual_note = "Dùng khi nhắn nhanh cho bạn cùng lớp (Одногруппники) hoặc bạn cùng KTX (Общага)."

    vocab_list = [
        {"ru_accent": f"{s['accent']} ({s['full']})", "en": s["en"], "vi": s["vi"]}
        for s in detected_slang
    ]
    for term in DOMAIN_GLOSSARY.get(domain, DOMAIN_GLOSSARY["Học thuật tổng hợp"])[:5]:
        vocab_list.append({"ru_accent": term["ru"], "en": term["en"], "vi": term["vi"]})

    slang_explanations = [
        {"term": s["word"], "full_form": s["full"], "meaning_vi": f"{s['vi']} — Ví dụ: «{s['example']}»"}
        for s in detected_slang
    ]

    return {
        "main_translation": main_trans,
        "ru_version": ru_ver,
        "vi_version": vi_ver,
        "en_version": en_ver,
        "slang_explanations": slang_explanations,
        "vocabulary_table": vocab_list,
        "russian_reply_variants": {
            "formal_vy": formal_vy_full,
            "formal_vy_vi_note": formal_note,
            "casual_ty": casual_ty_full,
            "casual_ty_vi_note": casual_note,
        },
        "grammar_notes": "Dán Gemini API Key (miễn phí) vào thanh bên trái để bật phân tích ngữ pháp chuyên sâu, chia cách và dịch chuẩn ngữ cảnh 100%.",
        "study_tip": "Khi liên hệ Phòng Quốc tế (Международный отдел) về gia hạn thị thực (продление визы), luôn dùng ngôi «Вы» và nộp hồ sơ trước 30–45 ngày.",
        "is_fallback": True,
    }


# ==============================================================================
# 6. GIẢNG ĐƯỜNG REAL-TIME HYBRID VOICE AI + TÓM TẮT AI + CHỐNG XSS
# ==============================================================================
def build_realtime_lecture_component(gemini_api_key: str = "", selected_domain: str = "") -> str:
    safe_domain = json.dumps(selected_domain, ensure_ascii=False)
    safe_gemini_key = json.dumps(clean_api_key(gemini_api_key))

    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
            * {{ box-sizing: border-box; font-family: 'Be Vietnam Pro', -apple-system, sans-serif; }}
            body {{ margin: 0; padding: 4px; background: transparent; color: #0F172A; }}
            .rt-container {{
                background: linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 100%);
                border: 2px solid #7DD3FC;
                border-radius: 20px;
                padding: 16px 18px;
                box-shadow: 0 12px 30px rgba(2, 132, 199, 0.12);
            }}
            .rt-top-bar {{
                display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
                gap: 10px; padding-bottom: 10px; border-bottom: 2px solid #E0F2FE;
            }}
            .rt-controls {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }}
            .rt-select {{
                padding: 8px 11px; border-radius: 12px; border: 1.5px solid #38BDF8;
                background: #FFFFFF; color: #0369A1; font-weight: 700; font-size: 0.84rem; cursor: pointer;
            }}
            .rt-btn {{
                display: inline-flex; align-items: center; gap: 6px; padding: 8px 13px;
                border-radius: 12px; font-weight: 700; font-size: 0.83rem; border: none; cursor: pointer;
                transition: all 0.18s ease;
            }}
            .btn-start {{ background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%); color: #FFFFFF; }}
            .btn-flush {{ background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%); color: #FFFFFF; }}
            .btn-pause {{ background: #FEF3C7; color: #B45309; border: 1px solid #F59E0B; }}
            .btn-clear {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }}
            .btn-download {{ background: linear-gradient(135deg, #06B6D4 0%, #0284C7 100%); color: #FFFFFF; }}
            .btn-summary {{ background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%); color: #FFFFFF; }}
            .btn-copyall {{ background: #FFFFFF; color: #0369A1; border: 1.5px solid #38BDF8; }}
            .rt-btn:disabled {{ opacity: 0.45; cursor: not-allowed; }}
            .sensitivity-bar {{
                display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
                gap: 12px; background: #F0F9FF; border: 1.5px solid #BAE6FD;
                border-radius: 14px; padding: 9px 14px; margin-top: 10px;
                font-size: 0.82rem; color: #0C4A6E; font-weight: 600;
            }}
            .sens-group {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
            .sens-slider {{ width: 115px; accent-color: #0284C7; cursor: pointer; }}
            .sens-pill {{ background: #0284C7; color: #FFFFFF; font-weight: 800; padding: 3px 9px; border-radius: 999px; font-size: 0.75rem; }}
            .level-meter-wrap {{ display: flex; align-items: center; gap: 8px; min-width: 180px; }}
            .level-bar-bg {{ flex: 1; height: 10px; background: #CBD5E1; border-radius: 999px; overflow: hidden; }}
            .level-bar-fill {{ height: 100%; width: 0%; background: linear-gradient(90deg, #22C55E 0%, #06B6D4 60%, #F59E0B 90%, #EF4444 100%); transition: width 0.08s ease; }}
            .rt-visualizer-row {{
                display: flex; align-items: center; justify-content: space-between; gap: 12px;
                background: #082F49; border-radius: 16px; padding: 10px 15px; margin-top: 10px;
                color: #E0F2FE; border: 1px solid #0284C7; flex-wrap: wrap;
            }}
            .status-indicator {{ display: flex; align-items: center; gap: 10px; font-size: 0.85rem; font-weight: 600; flex: 1; min-width: 220px; }}
            .dsp-badge {{ background: rgba(34, 197, 94, 0.2); border: 1px solid #4ADE80; color: #86EFAC; font-size: 0.73rem; font-weight: 700; padding: 4px 10px; border-radius: 999px; }}
            .pulse-dot {{ width: 12px; height: 12px; border-radius: 50%; background: #94A3B8; flex-shrink: 0; }}
            .pulse-dot.active {{ background: #22C55E; animation: pulseGreen 1.2s infinite; }}
            .pulse-dot.speaking {{ background: #38BDF8; animation: pulseBlue 0.7s infinite; }}
            @keyframes pulseGreen {{ 0% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0.7); }} 70% {{ box-shadow: 0 0 0 10px rgba(34,197,94,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(34,197,94,0); }} }}
            @keyframes pulseBlue {{ 0% {{ box-shadow: 0 0 0 0 rgba(56,189,248,0.85); }} 70% {{ box-shadow: 0 0 0 12px rgba(56,189,248,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(56,189,248,0); }} }}
            #waveCanvas {{ width: 180px; height: 34px; border-radius: 8px; background: rgba(255,255,255,0.06); }}
            .interim-box {{
                margin-top: 10px; background: #E0F2FE; border: 2px solid #0284C7;
                border-radius: 14px; padding: 11px 15px; display: flex; flex-direction: column; gap: 8px;
            }}
            .interim-box.voice-detected {{ background: #ECFEFF; border-color: #06B6D4; box-shadow: 0 0 0 3px rgba(6,182,212,0.2); }}
            .interim-left {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
            .interim-label {{ background: #0284C7; color: #FFFFFF; font-size: 0.72rem; font-weight: 800; padding: 4px 10px; border-radius: 999px; }}
            .vad-live-pill {{ font-size: 0.72rem; font-weight: 700; padding: 3px 9px; border-radius: 999px; background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; display: none; }}
            .interim-text {{ color: #0C4A6E; font-size: 1.02rem; font-weight: 700; line-height: 1.45; }}
            .manual-input {{ width: 100%; padding: 8px 12px; border-radius: 10px; border: 1.5px solid #7DD3FC; font-size: 0.87rem; color: #0F172A; background: #FFFFFF; outline: none; font-weight: 600; }}
            .stream-wrapper {{ position: relative; margin-top: 10px; }}
            .scroll-status-bar {{
                display: flex; align-items: center; justify-content: space-between; padding: 6px 12px;
                background: #F1F5F9; border: 1px solid #CBD5E1; border-bottom: none;
                border-radius: 14px 14px 0 0; font-size: 0.77rem; font-weight: 700; color: #334155;
            }}
            .scroll-lock-badge {{ padding: 2px 10px; border-radius: 999px; font-size: 0.73rem; font-weight: 700; }}
            .scroll-lock-badge.auto {{ background: #DCFCE7; color: #166534; }}
            .scroll-lock-badge.locked {{ background: #FEF3C7; color: #92400E; }}
            .subtitle-stream {{
                height: 300px; overflow-y: auto; background: #FFFFFF; border: 1.5px solid #BAE6FD;
                border-radius: 0 0 16px 16px; padding: 13px; scroll-behavior: smooth;
            }}
            .jump-bottom-btn {{
                position: absolute; bottom: 14px; right: 20px; background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                color: #FFFFFF; border: 2px solid #BAE6FD; border-radius: 999px; padding: 7px 14px;
                font-size: 0.8rem; font-weight: 800; cursor: pointer; display: none; z-index: 20;
            }}
            .sub-item {{
                background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 5px solid #0284C7;
                border-radius: 12px; padding: 11px 14px; margin-bottom: 10px;
            }}
            .sub-meta {{ display: flex; justify-content: space-between; font-size: 0.73rem; color: #475569; margin-bottom: 4px; font-weight: 600; }}
            .sub-source {{ font-size: 1.0rem; font-weight: 600; color: #0F172A; margin-bottom: 6px; line-height: 1.5; }}
            .sub-target {{ font-size: 1.02rem; font-weight: 700; color: #0369A1; background: #E0F2FE; padding: 8px 12px; border-radius: 10px; line-height: 1.52; }}
            .ai-summary-panel {{
                display: none; margin-top: 10px; background: linear-gradient(135deg, #F5F3FF 0%, #EEF2FF 100%);
                border: 2px solid #8B5CF6; border-radius: 14px; padding: 13px 16px; color: #1E1B4B;
                font-size: 0.9rem; line-height: 1.6; white-space: pre-wrap; max-height: 210px; overflow-y: auto;
            }}
            .empty-hint {{ text-align: center; color: #475569; padding: 48px 16px; font-size: 0.9rem; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="rt-container">
            <div class="rt-top-bar">
                <div class="rt-controls">
                    <label style="font-weight:700; color:#0369A1; font-size:0.84rem;">Nghe:</label>
                    <select id="sourceLang" class="rt-select">
                        <option value="ru-RU" selected>🇷🇺 Tiếng Nga (Giảng đường)</option>
                        <option value="vi-VN">🇻🇳 Tiếng Việt (Thử mic)</option>
                        <option value="en-US">🇬🇧 Tiếng Anh</option>
                    </select>
                    <label style="font-weight:700; color:#0369A1; font-size:0.84rem;">➔ Dịch sang:</label>
                    <select id="targetLang" class="rt-select">
                        <option value="vi" selected>🇻🇳 Tiếng Việt</option>
                        <option value="ru">🇷🇺 Tiếng Nga</option>
                        <option value="en">🇬🇧 Tiếng Anh</option>
                    </select>
                </div>

                <div class="rt-controls">
                    <button id="btnStart" class="rt-btn btn-start" onclick="startRecognition()">🎙️ Bắt đầu thu</button>
                    <button id="btnFlush" class="rt-btn btn-flush" onclick="forceCommitInterim()">➕ Ngắt & Dịch</button>
                    <button id="btnPause" class="rt-btn btn-pause" onclick="stopRecognition()" disabled>⏸️ Dừng</button>
                    <button id="btnSummary" class="rt-btn btn-summary" onclick="summarizeLectureAI()">🧠 Tóm tắt AI</button>
                    <button id="btnCopyAll" class="rt-btn btn-copyall" onclick="copyFullTranscript()">📋 Copy</button>
                    <button id="btnDownload" class="rt-btn btn-download" onclick="downloadTranscript()">📥 Tải .txt</button>
                    <button id="btnClear" class="rt-btn btn-clear" onclick="clearTranscript()">🗑️</button>
                </div>
            </div>

            <div class="sensitivity-bar">
                <div class="sens-group">
                    <span>🎙️ <b>Chế độ:</b></span>
                    <select id="captureModeSelect" class="rt-select" style="padding:5px 9px; font-size:0.79rem;" onchange="onCaptureModeChange()">
                        <option value="webspeech" selected>⚡ Trực tiếp (Hiện chữ tức thì)</option>
                        <option value="aidsp">🧠 AI Audio DSP (Gemini/Whisper 16kHz)</option>
                    </select>
                </div>
                <div class="sens-group">
                    <span>🎚️ <b>Độ nhạy:</b></span>
                    <input type="range" id="micGainSlider" class="sens-slider" min="1" max="12" step="0.5" value="7.5" oninput="updateMicSensitivity(this.value)" />
                    <span id="gainValueBadge" class="sens-pill">x7.5</span>
                </div>
                <div class="level-meter-wrap">
                    <span>🔊 Tín hiệu:</span>
                    <div class="level-bar-bg"><div id="levelBarFill" class="level-bar-fill"></div></div>
                    <span id="levelPctText" style="min-width:34px; text-align:right; font-weight:800; color:#0284C7;">0%</span>
                </div>
            </div>

            <div class="rt-visualizer-row">
                <div class="status-indicator">
                    <div id="statusDot" class="pulse-dot"></div>
                    <span id="statusText">Sẵn sàng — Chọn đúng ngôn ngữ mục «Nghe» rồi bấm «🎙️ Bắt đầu thu».</span>
                </div>
                <span id="engineBadge" class="dsp-badge">🔥 Live Speech Stream</span>
                <canvas id="waveCanvas" width="180" height="34"></canvas>
            </div>

            <div id="interimBox" class="interim-box">
                <div class="interim-left">
                    <span class="interim-label">🎙️ CÂU ĐANG THU</span>
                    <span id="vadLivePill" class="vad-live-pill">🟢 Đang thu...</span>
                    <span id="interimText" class="interim-text">Nhấn "🎙️ Bắt đầu thu" rồi nói vào Mic — Chữ sẽ hiện trực tiếp tại đây...</span>
                </div>
                <input type="text" id="manualSentenceInput" class="manual-input"
                    placeholder="✍️ Sửa nhanh câu đang thu hoặc gõ trực tiếp rồi bấm Enter..."
                    onkeydown="if(event.key === 'Enter') {{ event.preventDefault(); forceCommitInterim(); }}" />
            </div>

            <div id="aiSummaryPanel" class="ai-summary-panel"></div>

            <div class="stream-wrapper">
                <div class="scroll-status-bar">
                    <span>📜 Lịch sử Bài giảng (Liên kết ngữ cảnh 3 câu gần nhất)</span>
                    <span id="scrollBadge" class="scroll-lock-badge auto">🟢 Tự động cuộn</span>
                </div>
                <div id="subtitleStream" class="subtitle-stream">
                    <div id="emptyHint" class="empty-hint">
                        🚢 <b>Lịch sử Thu âm & Dịch thuật theo Ngữ cảnh</b><br/>
                        • Lướt lên đọc lại lịch sử sẽ tự động khóa cuộn để không bị nhảy trang.<br/>
                        • Bấm <b>🧠 Tóm tắt AI</b> sau buổi học để tổng hợp nhanh ý chính & thuật ngữ ôn thi!
                    </div>
                </div>
                <button id="jumpBottomBtn" class="jump-bottom-btn" onclick="resumeAutoScroll()">
                    ⬇️ Xem câu mới nhất <span id="unreadCountBadge"></span>
                </button>
            </div>
        </div>

        <script>
            try {{
                if (window.frameElement) {{
                    window.frameElement.setAttribute("allow", "microphone *; autoplay *; clipboard-write *");
                }}
            }} catch (e) {{}}

            const SELECTED_DOMAIN = {safe_domain};
            const GEMINI_API_KEY = {safe_gemini_key};
            const SLANG_MAP = {{
                "препод": "преподаватель", "курсач": "курсовая работа", "лаба": "лабораторная работа",
                "хвост": "академическая задолженность", "зачетка": "зачётная книжка",
                "зачётка": "зачётная книжка", "автомат": "экзамен автоматом",
                "общага": "общежитие", "стипуха": "стипендия", "сопромат": "сопротивление материалов",
                "матан": "математический анализ", "инфа": "информация", "преза": "презентация"
            }};

            function escapeHtml(str) {{
                return String(str || "")
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#39;");
            }}

            let recognition = null, isListening = false, lectureHistory = [];
            let currentMicGain = 7.5, committedResultIndex = 0, currentActiveSentence = "", latestResultsLength = 0;
            let lastCommittedNormalized = "", lastCommitTimestamp = 0, sentenceSilenceTimer = null;
            let lastSpeechActivity = 0, waveAnimId = null;
            let audioCtx = null, micStream = null, analyserNode = null, gainNode = null, scriptProcessor = null;
            let pcmRingBuffer = [], vadSpeechActive = false, vadSpeechStartTime = 0, vadLastVoiceTime = 0;
            let isTranscribingChunk = false, currentRmsLevel = 0, noiseFloorRms = 0.008;
            let userScrolledUp = false, unreadNewCount = 0;

            const statusDot = document.getElementById("statusDot");
            const statusText = document.getElementById("statusText");
            const interimBox = document.getElementById("interimBox");
            const interimText = document.getElementById("interimText");
            const vadLivePill = document.getElementById("vadLivePill");
            const manualSentenceInput = document.getElementById("manualSentenceInput");
            const subtitleStream = document.getElementById("subtitleStream");
            const scrollBadge = document.getElementById("scrollBadge");
            const jumpBottomBtn = document.getElementById("jumpBottomBtn");
            const unreadCountBadge = document.getElementById("unreadCountBadge");
            const btnStart = document.getElementById("btnStart");
            const btnPause = document.getElementById("btnPause");
            const sourceLangSelect = document.getElementById("sourceLang");
            const targetLangSelect = document.getElementById("targetLang");
            const captureModeSelect = document.getElementById("captureModeSelect");
            const levelBarFill = document.getElementById("levelBarFill");
            const levelPctText = document.getElementById("levelPctText");
            const gainValueBadge = document.getElementById("gainValueBadge");
            const engineBadge = document.getElementById("engineBadge");
            const aiSummaryPanel = document.getElementById("aiSummaryPanel");

            function updateMicSensitivity(val) {{
                currentMicGain = parseFloat(val) || 7.5;
                gainValueBadge.innerText = `x${{currentMicGain.toFixed(1)}}`;
                if (gainNode && audioCtx) {{
                    gainNode.gain.setTargetAtTime(Math.min(4.0, currentMicGain * 0.45), audioCtx.currentTime, 0.03);
                }}
            }}

            function onCaptureModeChange() {{
                const mode = captureModeSelect.value;
                engineBadge.innerText = mode === "webspeech" ? "🔥 Live Speech Stream" : "🧠 AI Audio DSP (16kHz)";
                if (isListening) {{ stopRecognition(); setTimeout(startRecognition, 180); }}
            }}

            manualSentenceInput.addEventListener("input", () => {{
                currentActiveSentence = manualSentenceInput.value;
                if (currentActiveSentence.trim()) interimText.innerText = currentActiveSentence;
            }});

            subtitleStream.addEventListener("scroll", () => {{
                const dist = subtitleStream.scrollHeight - subtitleStream.scrollTop - subtitleStream.clientHeight;
                if (dist > 55) {{
                    userScrolledUp = true;
                    scrollBadge.className = "scroll-lock-badge locked";
                    scrollBadge.innerText = "🔒 Khóa cuộn";
                    jumpBottomBtn.style.display = "inline-flex";
                }} else {{
                    userScrolledUp = false; unreadNewCount = 0; unreadCountBadge.innerText = "";
                    scrollBadge.className = "scroll-lock-badge auto";
                    scrollBadge.innerText = "🟢 Tự động cuộn";
                    jumpBottomBtn.style.display = "none";
                }}
            }});

            function resumeAutoScroll() {{
                userScrolledUp = false; unreadNewCount = 0; unreadCountBadge.innerText = "";
                subtitleStream.scrollTop = subtitleStream.scrollHeight;
                scrollBadge.className = "scroll-lock-badge auto";
                scrollBadge.innerText = "🟢 Tự động cuộn";
                jumpBottomBtn.style.display = "none";
            }}

            function normalizeText(s) {{
                return (s || "").toLowerCase().replace(/[.,?!…;:"'«»()\\-]/g, " ").replace(/\\s+/g, " ").trim();
            }}

            function formatSentence(raw) {{
                let s = (raw || "").replace(/\\s+/g, " ").trim();
                if (!s) return "";
                s = s.charAt(0).toUpperCase() + s.slice(1);
                return /[.?!…]$/.test(s) ? s : (s + ".");
            }}

            function expandRussianSlang(text, srcShort) {{
                if (srcShort !== "ru") return text;
                let out = text;
                Object.keys(SLANG_MAP).forEach(slang => {{
                    out = out.replace(new RegExp("\\\\b" + slang + "\\\\b", "gi"), SLANG_MAP[slang]);
                }});
                return out;
            }}

            async function translateSentenceWithContext(currentSentence, srcLangCode, tgtLang) {{
                const srcShort = srcLangCode.split("-")[0];
                if (srcShort === tgtLang) return currentSentence;
                const cleanCurrent = expandRussianSlang(currentSentence.trim(), srcShort);
                const recentContext = lectureHistory.slice(-3);

                if (GEMINI_API_KEY && GEMINI_API_KEY.length > 10) {{
                    try {{
                        const ctx = recentContext.length
                            ? recentContext.map((it, i) => `[Câu ${{i+1}}]: ${{it.source}} -> ${{it.translated}}`).join("\\n")
                            : "Câu mở đầu.";
                        const prompt = `Bạn là trợ lý dịch bài giảng chuyên ngành ${{SELECTED_DOMAIN}}.\\nNgữ cảnh trước:\\n${{ctx}}\\nDịch câu sau từ ${{srcShort}} sang ${{tgtLang}} mượt mà, chuẩn thuật ngữ. CHỈ TRẢ VỀ câu dịch:\\n${{cleanCurrent}}`;
                        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`, {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({{ contents: [{{ parts: [{{ text: prompt }}] }}], generationConfig: {{ temperature: 0.15 }} }})
                        }});
                        if (res.ok) {{
                            const data = await res.json();
                            const out = data?.candidates?.[0]?.content?.parts?.[0]?.text;
                            if (out && out.trim()) return out.trim();
                        }}
                    }} catch (e) {{}}
                }}

                try {{
                    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${{srcShort}}&tl=${{tgtLang}}&dt=t&q=${{encodeURIComponent(cleanCurrent)}}`;
                    const res = await fetch(url);
                    const data = await res.json();
                    if (Array.isArray(data) && Array.isArray(data[0])) {{
                        return data[0].map(it => it[0]).join("");
                    }}
                }} catch (e) {{}}
                return "[Đang chờ kết nối dịch...]";
            }}

            function appendSubtitleCard(originalText, srcLangCode, tgtLang) {{
                const cleanOrig = formatSentence(originalText);
                const normOrig = normalizeText(cleanOrig);
                if (!normOrig) return;
                const nowMs = Date.now();
                if (normOrig === lastCommittedNormalized && (nowMs - lastCommitTimestamp) < 7000) return;
                lastCommittedNormalized = normOrig;
                lastCommitTimestamp = nowMs;

                const hintEl = document.getElementById("emptyHint");
                if (hintEl) hintEl.style.display = "none";

                const timeStr = new Date().toLocaleTimeString("vi-VN", {{ hour: "2-digit", minute: "2-digit", second: "2-digit" }});
                const idx = lectureHistory.length + 1;
                const itemId = "sub-" + Date.now() + "-" + Math.floor(Math.random() * 1000);

                const card = document.createElement("div");
                card.className = "sub-item";
                card.innerHTML = `
                    <div class="sub-meta">
                        <span>#${{idx}} • 🕒 ${{escapeHtml(timeStr)}} (${{escapeHtml(srcLangCode)}})</span>
                        <span>${{escapeHtml(SELECTED_DOMAIN)}}</span>
                    </div>
                    <div class="sub-source">🗣️ ${{escapeHtml(cleanOrig)}}</div>
                    <div id="${{itemId}}" class="sub-target">⏳ Đang dịch...</div>
                `;
                subtitleStream.appendChild(card);
                if (!userScrolledUp) subtitleStream.scrollTop = subtitleStream.scrollHeight;
                else {{ unreadNewCount++; unreadCountBadge.innerText = `(${{unreadNewCount}})`; jumpBottomBtn.style.display = "inline-flex"; }}

                translateSentenceWithContext(cleanOrig, srcLangCode, tgtLang).then(translated => {{
                    const el = document.getElementById(itemId);
                    if (el) el.innerText = "🌊 " + translated;
                    lectureHistory.push({{ time: timeStr, source: cleanOrig, translated: translated }});
                    if (!userScrolledUp) subtitleStream.scrollTop = subtitleStream.scrollHeight;
                }});
            }}

            function forceCommitInterim() {{
                if (sentenceSilenceTimer) {{ clearTimeout(sentenceSilenceTimer); sentenceSilenceTimer = null; }}
                let candidate = (manualSentenceInput.value || "").trim() || currentActiveSentence.trim();
                if (candidate) {{
                    committedResultIndex = latestResultsLength;
                    currentActiveSentence = "";
                    manualSentenceInput.value = "";
                    interimText.innerText = "✅ Đã chốt câu! Đang nghe câu tiếp theo...";
                    appendSubtitleCard(candidate, sourceLangSelect.value, targetLangSelect.value);
                }} else {{
                    manualSentenceInput.focus();
                }}
            }}

            async function summarizeLectureAI() {{
                if (lectureHistory.length === 0) {{
                    alert("Chưa có câu nào trong lịch sử bài giảng để tóm tắt!");
                    return;
                }}
                aiSummaryPanel.style.display = "block";
                if (!GEMINI_API_KEY || GEMINI_API_KEY.length < 10) {{
                    aiSummaryPanel.innerText = "💡 Tính năng Tóm tắt Bài giảng AI cần Gemini API Key ở thanh bên trái (miễn phí). Hiện bạn đã ghi được " + lectureHistory.length + " câu và có thể tải file .txt về ôn tập!";
                    return;
                }}
                aiSummaryPanel.innerText = "🧠 Đang dùng Gemini AI tóm tắt bài giảng (" + lectureHistory.length + " câu) và rút trích thuật ngữ ôn thi...";
                const joined = lectureHistory.map((it, i) => `${{i+1}}. ${{it.source}} (${{it.translated}})`).join("\\n");
                const prompt = `Hãy tóm tắt ngắn gọn bài giảng chuyên ngành ${{SELECTED_DOMAIN}} sau đây thành:\\n1. 3-5 ý chính cốt lõi bằng tiếng Việt.\\n2. Danh sách 5 thuật ngữ Nga-Việt quan trọng nhất cần nhớ.\\nNội dung:\\n${{joined.slice(0, 12000)}}`;
                try {{
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`, {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ contents: [{{ parts: [{{ text: prompt }}] }}], generationConfig: {{ temperature: 0.25 }} }})
                    }});
                    if (res.ok) {{
                        const data = await res.json();
                        const summary = data?.candidates?.[0]?.content?.parts?.[0]?.text || "Không tạo được bản tóm tắt.";
                        aiSummaryPanel.innerText = "✨ TÓM TẮT BÀI GIẢNG AI:\\n\\n" + summary.trim();
                        return;
                    }}
                }} catch (e) {{}}
                aiSummaryPanel.innerText = "⚠️ Không thể kết nối Gemini AI để tóm tắt lúc này. Hãy kiểm tra lại Gemini API Key.";
            }}

            function copyFullTranscript() {{
                if (lectureHistory.length === 0) {{ alert("Chưa có nội dung để sao chép!"); return; }}
                const text = lectureHistory.map((it, i) => `[${{i+1}} - ${{it.time}}]\\nGốc: ${{it.source}}\\nDịch: ${{it.translated}}`).join("\\n\\n");
                navigator.clipboard?.writeText(text).then(() => {{
                    const b = document.getElementById("btnCopyAll");
                    b.innerText = "✅ Đã Copy";
                    setTimeout(() => b.innerText = "📋 Copy", 1600);
                }});
            }}

            function encodeWavBase64(floatSamples, inputRate) {{
                const targetRate = 16000, ratio = inputRate / targetRate;
                const outLen = Math.max(1, Math.floor(floatSamples.length / ratio));
                const resampled = new Float32Array(outLen);
                let sumSq = 0;
                for (let i = 0; i < outLen; i++) {{
                    const s = floatSamples[Math.min(floatSamples.length - 1, Math.floor(i * ratio))];
                    resampled[i] = s; sumSq += s * s;
                }}
                const rms = Math.sqrt(sumSq / outLen);
                const gain = rms > 0.0005 ? Math.min(8.0, Math.max(1.0, 0.20 / rms)) : 2.0;
                const buf = new ArrayBuffer(44 + outLen * 2);
                const view = new DataView(buf);
                const ws = (off, str) => {{ for (let i = 0; i < str.length; i++) view.setUint8(off + i, str.charCodeAt(i)); }};
                ws(0, "RIFF"); view.setUint32(4, 36 + outLen * 2, true); ws(8, "WAVE"); ws(12, "fmt ");
                view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
                view.setUint32(24, targetRate, true); view.setUint32(28, targetRate * 2, true);
                view.setUint16(32, 2, true); view.setUint16(34, 16, true); ws(36, "data"); view.setUint32(40, outLen * 2, true);
                let off = 44;
                for (let i = 0; i < outLen; i++) {{
                    let s = Math.tanh(resampled[i] * gain);
                    view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true); off += 2;
                }}
                const bytes = new Uint8Array(buf);
                let bin = "";
                for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
                return btoa(bin);
            }}

            async function handleAudioChunkAI(chunks, sampleRate) {{
                if (!GEMINI_API_KEY || GEMINI_API_KEY.length < 10) {{
                    interimText.innerText = "💡 Chế độ AI Audio DSP cần Gemini API Key ở thanh bên trái.";
                    return;
                }}
                let total = chunks.reduce((acc, c) => acc + c.length, 0);
                const merged = new Float32Array(total);
                let off = 0; chunks.forEach(c => {{ merged.set(c, off); off += c.length; }});
                isTranscribingChunk = true;
                interimText.innerText = "🧠 Đang giải mã đoạn âm thanh bằng AI Audio...";
                try {{
                    const wavB64 = encodeWavBase64(merged, sampleRate);
                    const prompt = `Chép lại chính xác lời nói trong đoạn âm thanh (${{sourceLangSelect.value}}, chuyên ngành ${{SELECTED_DOMAIN}}). Nếu chỉ có im lặng/nhiễu, trả về chuỗi rỗng.`;
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`, {{
                        method: "POST", headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ contents: [{{ parts: [{{ text: prompt }}, {{ inlineData: {{ mimeType: "audio/wav", data: wavB64 }} }}] }}], generationConfig: {{ temperature: 0.1 }} }})
                    }});
                    if (res.ok) {{
                        const data = await res.json();
                        const text = (data?.candidates?.[0]?.content?.parts?.[0]?.text || "").trim().replace(/^["'«]|["'»]$/g, "");
                        if (text.length >= 2) {{
                            appendSubtitleCard(text, sourceLangSelect.value, targetLangSelect.value);
                            interimText.innerText = "✅ Đã chốt câu! Đang nghe câu tiếp theo...";
                        }}
                    }}
                }} catch (e) {{}}
                isTranscribingChunk = false;
            }}

            async function initUltraAudioDSP() {{
                try {{
                    if (!navigator.mediaDevices?.getUserMedia || micStream) return;
                    micStream = await navigator.mediaDevices.getUserMedia({{ audio: {{ echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 }} }});
                    const AC = window.AudioContext || window.webkitAudioContext;
                    audioCtx = new AC();
                    if (audioCtx.state === "suspended") await audioCtx.resume();
                    const src = audioCtx.createMediaStreamSource(micStream);
                    gainNode = audioCtx.createGain();
                    gainNode.gain.value = Math.min(3.5, currentMicGain * 0.4);
                    analyserNode = audioCtx.createAnalyser(); analyserNode.fftSize = 256;
                    scriptProcessor = audioCtx.createScriptProcessor(2048, 1, 1);
                    const sink = audioCtx.createGain(); sink.gain.value = 0.0;
                    src.connect(gainNode); gainNode.connect(analyserNode); gainNode.connect(scriptProcessor);
                    scriptProcessor.connect(sink); sink.connect(audioCtx.destination);
                    scriptProcessor.onaudioprocess = (ev) => {{
                        if (!isListening) return;
                        const buf = ev.inputBuffer.getChannelData(0);
                        let sumSq = 0; for (let i = 0; i < buf.length; i++) sumSq += buf[i] * buf[i];
                        const rms = Math.sqrt(sumSq / buf.length);
                        currentRmsLevel = rms;
                        noiseFloorRms = rms < noiseFloorRms ? noiseFloorRms * 0.94 + rms * 0.06 : noiseFloorRms * 0.995 + rms * 0.005;
                        const thresh = Math.max(0.018, Math.min(0.12, noiseFloorRms * 2.4));
                        const now = Date.now();
                        if (rms > thresh) {{
                            lastSpeechActivity = now; vadLastVoiceTime = now;
                            if (!vadSpeechActive) {{ vadSpeechActive = true; vadSpeechStartTime = now; }}
                        }}
                        if (vadSpeechActive) {{
                            pcmRingBuffer.push(new Float32Array(buf));
                            if ((now - vadLastVoiceTime > 950 && now - vadSpeechStartTime >= 600) || (now - vadSpeechStartTime >= 4200)) {{
                                vadSpeechActive = false;
                                const cap = pcmRingBuffer.slice(); pcmRingBuffer = [];
                                if (!isTranscribingChunk && cap.length > 4) handleAudioChunkAI(cap, audioCtx.sampleRate);
                            }}
                        }}
                    }};
                }} catch (e) {{}}
            }}

            function stopUltraAudioDSP() {{
                try {{
                    scriptProcessor?.disconnect(); scriptProcessor = null;
                    micStream?.getTracks().forEach(t => t.stop()); micStream = null;
                    audioCtx?.close(); audioCtx = null; analyserNode = null; gainNode = null;
                    pcmRingBuffer = []; vadSpeechActive = false; currentRmsLevel = 0;
                }} catch (e) {{}}
            }}

            function startReactiveWave() {{
                const canvas = document.getElementById("waveCanvas");
                const ctx = canvas.getContext("2d");
                if (waveAnimId) cancelAnimationFrame(waveAnimId);
                function render() {{
                    if (!isListening) {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        levelBarFill.style.width = "0%"; levelPctText.innerText = "0%";
                        vadLivePill.style.display = "none"; interimBox.classList.remove("voice-detected");
                        return;
                    }}
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    const now = Date.now(), active = (now - lastSpeechActivity) < 550;
                    const pct = analyserNode
                        ? Math.min(98, Math.round(Math.min(1, currentRmsLevel * 3.2) * 100))
                        : (active ? Math.min(92, Math.round(58 + Math.sin(now / 90) * 22)) : 5);
                    levelBarFill.style.width = pct + "%"; levelPctText.innerText = pct + "%";
                    statusDot.classList.toggle("speaking", active);
                    interimBox.classList.toggle("voice-detected", active);
                    vadLivePill.style.display = active ? "inline-block" : "none";
                    for (let i = 0; i < 22; i++) {{
                        const h = Math.max(4, (active ? (Math.sin(now / 75 + i * 0.6) * 0.4 + 0.55) : 0.14) * canvas.height);
                        ctx.fillStyle = active ? "#38BDF8" : "#4ADE80";
                        ctx.fillRect(i * (canvas.width / 22) + 1, canvas.height - h, (canvas.width / 22) - 3, h);
                    }}
                    waveAnimId = requestAnimationFrame(render);
                }}
                render();
            }}

            function startRecognition() {{
                if (isListening) return;
                const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                isListening = true; committedResultIndex = 0; latestResultsLength = 0; currentActiveSentence = "";
                statusDot.classList.add("active"); btnStart.disabled = true; btnPause.disabled = false;
                startReactiveWave();

                if (captureModeSelect.value === "aidsp" || !SR) {{
                    statusText.innerText = "🧠 Đang thu bằng AI Audio DSP — Cứ nói hết câu (~4s) AI sẽ tự động chép & dịch...";
                    initUltraAudioDSP(); return;
                }}

                stopUltraAudioDSP();
                recognition = new SR();
                recognition.lang = sourceLangSelect.value;
                recognition.continuous = true; recognition.interimResults = true;
                recognition.onstart = () => {{ statusText.innerText = "🟢 Đang thu trực tiếp (" + sourceLangSelect.options[sourceLangSelect.selectedIndex].text + ")..."; }};
                recognition.onresult = (ev) => {{
                    lastSpeechActivity = Date.now(); latestResultsLength = ev.results.length;
                    let rebuilt = "";
                    for (let i = committedResultIndex; i < ev.results.length; i++) {{
                        const piece = (ev.results[i][0]?.transcript || "").trim();
                        if (piece) rebuilt = (rebuilt + " " + piece).trim();
                    }}
                    currentActiveSentence = rebuilt;
                    if (rebuilt) {{
                        interimText.innerText = rebuilt; manualSentenceInput.value = rebuilt;
                        if (sentenceSilenceTimer) clearTimeout(sentenceSilenceTimer);
                        sentenceSilenceTimer = setTimeout(() => {{ if (currentActiveSentence.trim()) forceCommitInterim(); }}, 1550);
                    }}
                }};
                recognition.onerror = (ev) => {{
                    if (ev.error === "not-allowed") {{ statusText.innerText = "❌ Trình duyệt chặn quyền Microphone!"; stopRecognition(); }}
                    else if (ev.error === "network") {{ captureModeSelect.value = "aidsp"; initUltraAudioDSP(); }}
                }};
                recognition.onend = () => {{
                    if (currentActiveSentence.trim()) forceCommitInterim();
                    committedResultIndex = 0; latestResultsLength = 0;
                    if (isListening && captureModeSelect.value === "webspeech") {{
                        setTimeout(() => {{ try {{ recognition.lang = sourceLangSelect.value; recognition.start(); }} catch (e) {{}} }}, 100);
                    }}
                }};
                recognition.start();
            }}

            function stopRecognition() {{
                isListening = false;
                if (sentenceSilenceTimer) clearTimeout(sentenceSilenceTimer);
                if (currentActiveSentence.trim()) forceCommitInterim();
                try {{ recognition?.stop(); }} catch (e) {{}}
                stopUltraAudioDSP();
                if (waveAnimId) cancelAnimationFrame(waveAnimId);
                statusDot.classList.remove("active", "speaking");
                statusText.innerText = "⏸️ Đã tạm dừng thu âm.";
                btnStart.disabled = false; btnPause.disabled = true;
            }}

            function clearTranscript() {{
                lectureHistory = []; currentActiveSentence = ""; manualSentenceInput.value = "";
                aiSummaryPanel.style.display = "none"; aiSummaryPanel.innerText = "";
                subtitleStream.innerHTML = '<div id="emptyHint" class="empty-hint">🚢 Đã xóa lịch sử. Nhấn <b>🎙️ Bắt đầu thu</b> để ghi bài giảng mới.</div>';
                interimText.innerText = "...";
            }}

            function downloadTranscript() {{
                if (lectureHistory.length === 0) {{ alert("Chưa có nội dung bài giảng!"); return; }}
                let content = "BẢN GHI BÀI GIẢNG — ANH MINH TRANSLATE ({APP_VERSION})\\nChuyên ngành: " + SELECTED_DOMAIN + "\\n====================================\\n\\n";
                lectureHistory.forEach((it, i) => {{ content += `[Câu ${{i+1}} | ${{it.time}}]\\nGốc : ${{it.source}}\\nDịch: ${{it.translated}}\\n------------------------------------\\n`; }});
                const blob = new Blob([content], {{ type: "text/plain;charset=utf-8" }});
                const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
                a.download = `Bai_Giang_AnhMinhTranslate_${{new Date().toISOString().slice(0,10)}}.txt`;
                a.click();
            }}
        </script>
    </body>
    </html>
    """


# ==============================================================================
# 7. XỬ LÝ ÂM THANH PYTHON DSP (RMS AUTO-GAIN X12) & MULTIMODAL AUDIO ĐA ĐỊNH DẠNG
# ==============================================================================
AUDIO_MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}


def boost_wav_audio_bytes(audio_bytes: bytes, max_gain_factor: float = 12.0) -> bytes:
    """Bộ xử lý DSP chuẩn Whisper cho file WAV: DC offset + Pre-emphasis + RMS Auto-Gain + Soft Limiter."""
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            params = wf.getparams()
            frames = wf.readframes(params.nframes)
            if params.sampwidth != 2:
                return audio_bytes

            samples = array("h")
            samples.frombytes(frames)
            n = len(samples)
            if n == 0:
                return audio_bytes

            mean_val = sum(samples) / float(n)
            skip = min(int(params.framerate * 0.08), n // 6)
            core_slice = samples[skip : n - skip] if (n - 2 * skip) > 200 else samples

            sum_sq = sum((x - mean_val) ** 2 for x in core_slice)
            rms = math.sqrt(sum_sq / max(1, len(core_slice)))
            auto_gain = min(max_gain_factor, max(1.8, 6500.0 / rms)) if rms > 1.0 else max_gain_factor

            prev_sample = 0.0
            for i in range(n):
                cur = float(samples[i]) - mean_val
                emphasized = cur - 0.22 * prev_sample
                prev_sample = cur
                boosted = emphasized * auto_gain
                if boosted > 29000.0:
                    boosted = 29000.0 + 3767.0 * math.tanh((boosted - 29000.0) / 8000.0)
                elif boosted < -29000.0:
                    boosted = -29000.0 + 3767.0 * math.tanh((boosted + 29000.0) / 8000.0)
                samples[i] = int(max(-32768, min(32767, boosted)))

        out_io = io.BytesIO()
        with wave.open(out_io, "wb") as out_wf:
            out_wf.setparams(params)
            out_wf.writeframes(samples.tobytes())
        return out_io.getvalue()
    except Exception:
        return audio_bytes


def transcribe_audio_with_gemini_multimodal(
    api_key: str,
    audio_bytes: bytes,
    mime_type: str,
    source_lang_speech: str,
    target_lang_trans: str,
    domain: str = "Kỹ thuật & Đóng tàu",
) -> Tuple[Optional[str], Optional[str]]:
    """Nhận diện & dịch âm thanh đa định dạng (.wav, .mp3, .m4a, .ogg, .webm) qua Gemini Multimodal."""
    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    prompt = f"""
Bạn là chuyên gia nhận diện giọng nói (ASR) và dịch thuật học thuật chuyên ngành "{domain}".
Hãy nghe file âm thanh đính kèm (ngôn ngữ gốc: {source_lang_speech}) và:
1. Chép lại chính xác toàn bộ lời nói (kể cả giọng nói nhỏ).
2. Dịch chuẩn xác sang ngôn ngữ "{target_lang_trans}".
CHỈ TRẢ VỀ JSON:
{{"transcript": "Lời nói gốc", "translation": "Bản dịch hoàn chỉnh"}}
"""
    raw_text, _ = call_gemini_multimodal_rest(
        api_key=api_key,
        parts=[
            {"text": prompt},
            {"inlineData": {"mimeType": mime_type, "data": b64_audio}},
        ],
        expect_json=True,
        temperature=0.1,
        timeout_sec=30,
    )
    if not raw_text:
        return None, None
    try:
        parsed = _parse_json_response(raw_text)
        if parsed:
            return str(parsed.get("transcript", "")).strip(), str(parsed.get("translation", "")).strip()
    except Exception:
        pass
    return None, None


def transcribe_and_translate_audio_bytes(
    audio_bytes: bytes,
    source_lang_speech: str,
    target_lang_trans: str,
    gemini_api_key: str = "",
    selected_domain: str = "Kỹ thuật & Đóng tàu",
    max_gain_factor: float = 12.0,
    file_ext: str = ".wav",
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    ext = file_ext.lower()
    mime_type = AUDIO_MIME_MAP.get(ext, "audio/wav")
    processed_bytes = boost_wav_audio_bytes(audio_bytes, max_gain_factor=max_gain_factor) if ext == ".wav" else audio_bytes

    if clean_api_key(gemini_api_key):
        ai_tr, ai_tl = transcribe_audio_with_gemini_multimodal(
            api_key=gemini_api_key,
            audio_bytes=processed_bytes,
            mime_type=mime_type,
            source_lang_speech=source_lang_speech,
            target_lang_trans=target_lang_trans,
            domain=selected_domain,
        )
        if ai_tr:
            if not ai_tl:
                ai_tl = fast_free_translate(ai_tr, source_lang_speech.split("-")[0], target_lang_trans)
            return ai_tr, ai_tl, None

    if ext != ".wav":
        return (
            None,
            None,
            f"Định dạng `{ext}` (ghi âm điện thoại / Telegram Voice) cần dán **Gemini API Key** ở thanh bên trái để bật bộ giải mã AI đa phương thức, hoặc bạn hãy tải file `.wav` / thu âm trực tiếp bằng nút Mic phía trên!",
        )

    if sr is None:
        return None, None, "Thư viện SpeechRecognition chưa được cài đặt trong requirements.txt."

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 20
    recognizer.dynamic_energy_threshold = False
    last_err = None

    for candidate_wav in (processed_bytes, audio_bytes):
        try:
            with sr.AudioFile(io.BytesIO(candidate_wav)) as source:
                audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data, language=source_lang_speech)
            if transcript and transcript.strip():
                translated = fast_free_translate(transcript, source_lang_speech.split("-")[0], target_lang_trans)
                return transcript, translated, None
        except sr.UnknownValueError:
            last_err = "Không nhận diện được lời nói. Hãy nói gần Mic hơn hoặc dán Gemini API Key để bật AI Audio siêu nhạy!"
        except sr.RequestError as exc:
            last_err = f"Lỗi kết nối dịch vụ nhận diện giọng nói: {exc}"
        except Exception as exc:
            last_err = f"Lỗi đọc file âm thanh: {exc}"

    return None, None, last_err


# ==============================================================================
# 8. SỔ TỪ VỰNG CÁ NHÂN, LỊCH SỬ & XUẤT FILE ANKI CSV
# ==============================================================================
def add_vocab_items_to_notebook(items: List[Dict[str, str]]) -> int:
    """Thêm từ vựng vào sổ cá nhân trong session_state (chống trùng lặp)."""
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
                    "added_at": datetime.now().strftime("%H:%M %d/%m"),
                },
            )
            existing.add(ru_k.lower())
            added += 1
    return added


def export_vocab_to_anki_csv(vocab_list: List[Dict[str, str]]) -> bytes:
    """Xuất danh sách từ vựng thành CSV chuẩn UTF-8 BOM để nạp thẳng vào Anki / Quizlet / Excel."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tieng_Nga_Trong_Am", "Nghia_Tieng_Viet", "Tieng_Anh_Doi_Chieu"])
    for item in vocab_list:
        writer.writerow([item.get("ru_accent", ""), item.get("vi", ""), item.get("en", "")])
    return ("\ufeff" + output.getvalue()).encode("utf-8")


# ==============================================================================
# 9. GIAO DIỆN CHÍNH (SIDEBAR + 3 TAB HỆ SINH THÁI HỌC THUẬT)
# ==============================================================================
def init_session_state() -> None:
    defaults: Dict[str, Any] = {
        "input_text_area": "",
        "selected_direction": DIRECTION_OPTIONS[0],
        "is_author_admin": False,
        "saved_gemini_api_key": "",
        "declined_keys": set(),
        "editing_student_profile": False,
        "translation_history": [],
        "saved_vocab_notebook": [],
        "flashcard_index": 0,
        "flashcard_show_back": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Nhận lại dữ liệu từ localStorage bootstrap (rồi xóa ngay khỏi URL)
    recovered_key, recovered_profile = consume_bootstrap_query_params()
    if recovered_key and not st.session_state["saved_gemini_api_key"]:
        st.session_state["saved_gemini_api_key"] = recovered_key
    if recovered_profile:
        st.session_state["confirmed_user_name"] = recovered_profile["full_name"]
        st.session_state["confirmed_user_year"] = recovered_profile["student_year"]
        st.session_state["confirmed_user_uni"] = recovered_profile["university"]

    if not st.session_state.get("ls_sync_checked"):
        st.session_state["ls_sync_checked"] = True
        if not st.session_state.get("saved_gemini_api_key") or not st.session_state.get("confirmed_user_name"):
            inject_localstorage_sync(action="load_all")


def render_translation_result(res: Dict, selected_domain: str, used_ai: bool) -> None:
    used_ai_badge = (
        "✨ Gemini AI Smart Mode" if used_ai else "⚡ Đa Luồng Siêu Tốc (Parallel GTX)"
    )

    render_html(
        f'<div class="nautical-divider">{STICKER_SAILBOAT_MINI} KẾT QUẢ DỊCH THUẬT & PHÂN TÍCH HỌC THUẬT {STICKER_SAILBOAT_MINI}</div>'
    )

    main_trans = res.get("main_translation", "")
    render_html(
        f"""
        <div class="ocean-card">
            <div class="ocean-card-header">
                <div class="ocean-card-title">{STICKER_COMPASS_3D} 1. Bản dịch tự nhiên nhất ({esc(selected_domain)})</div>
                <span class="ocean-pill">{esc(used_ai_badge)}</span>
            </div>
            <div class="translation-main-text">{esc(main_trans)}</div>
        </div>
        """
    )
    render_copy_button(main_trans, "📋 Sao chép bản dịch chính", "main_trans")

    tri_col1, tri_col2, tri_col3 = st.columns(3)
    for col, title, css_cls, text_val, lang_code, btn_key in (
        (tri_col1, "🇷🇺 Bản Tiếng Nga (RU)", "lang-compare-box-ru", res.get("ru_version", ""), "ru", "ru"),
        (tri_col2, "🇻🇳 Bản Tiếng Việt (VI)", "lang-compare-box-vi", res.get("vi_version", ""), "vi", "vi"),
        (tri_col3, "🇬🇧 Đối chiếu Tiếng Anh (EN)", "lang-compare-box-en", res.get("en_version", ""), "en", "en"),
    ):
        with col:
            render_html(
                f"""
                <div class="lang-card-header">{title}</div>
                <div class="{css_cls}">{esc(text_val) if text_val else "—"}</div>
                """
            )
            if text_val:
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button(f"🔊 Nghe {btn_key.upper()}", key=f"tts_{btn_key}_btn", use_container_width=True):
                        audio_b = generate_tts_audio(text_val, lang_code)
                        if audio_b:
                            st.audio(audio_b, format="audio/mp3")
                with c_btn2:
                    render_copy_button(text_val, "📋 Copy", f"tri_{btn_key}")

    reply_variants = res.get("russian_reply_variants", {})
    if reply_variants:
        render_html(
            f"""
            <div class="ocean-card" style="margin-top:12px; margin-bottom:10px;">
                <div class="ocean-card-header" style="margin-bottom:0; border-bottom:none; padding-bottom:0;">
                    <div class="ocean-card-title">{STICKER_HELM_WHEEL} 2. Hai phiên bản giao tiếp Tiếng Nga (Chuẩn văn phong bản xứ)</div>
                    <span class="ocean-pill">Ngôi «Вы» & Ngôi «Ты»</span>
                </div>
            </div>
            """
        )
        tone_c1, tone_c2 = st.columns(2)
        with tone_c1:
            formal_vy = reply_variants.get("formal_vy", "")
            formal_note = reply_variants.get("formal_vy_vi_note", "")
            render_html(
                f"""
                <div class="tone-box-formal">
                    <div class="tone-title">🎩 Trang trọng (Ngôi «Вы» — Gửi Giáo sư, Giảng viên, Деканат)</div>
                    <div class="tone-ru">{esc(formal_vy)}</div>
                    <div class="tone-note">💡 {esc(formal_note)}</div>
                </div>
                """
            )
            if formal_vy:
                fc1, fc2 = st.columns(2)
                with fc1:
                    if st.button("🔊 Nghe câu «Вы»", key="tts_vy_btn", use_container_width=True):
                        vy_audio = generate_tts_audio(formal_vy, "ru")
                        if vy_audio:
                            st.audio(vy_audio, format="audio/mp3")
                with fc2:
                    render_copy_button(formal_vy, "📋 Copy «Вы»", "copy_vy")

        with tone_c2:
            casual_ty = reply_variants.get("casual_ty", "")
            casual_note = reply_variants.get("casual_ty_vi_note", "")
            render_html(
                f"""
                <div class="tone-box-casual">
                    <div class="tone-title">🤝 Thân mật (Ngôi «Ты» — Nhắn bạn học trên Telegram/VK)</div>
                    <div class="tone-ru">{esc(casual_ty)}</div>
                    <div class="tone-note">💡 {esc(casual_note)}</div>
                </div>
                """
            )
            if casual_ty:
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("🔊 Nghe câu «Ты»", key="tts_ty_btn", use_container_width=True):
                        ty_audio = generate_tts_audio(casual_ty, "ru")
                        if ty_audio:
                            st.audio(ty_audio, format="audio/mp3")
                with cc2:
                    render_copy_button(casual_ty, "📋 Copy «Ты»", "copy_ty")

    slang_list = res.get("slang_explanations", [])
    if slang_list:
        slang_items_html = "".join(
            f"""
            <div class="slang-item">
                <span class="slang-word">⚓ {esc(s_item.get("term", ""))}</span>
                <span> (Dạng đầy đủ: <b>{esc(s_item.get("full_form", ""))}</b>)</span><br/>
                <span style="color:#334155;">➔ {esc(s_item.get("meaning_vi", ""))}</span>
            </div>
            """
            for s_item in slang_list
        )
    else:
        slang_items_html = (
            '<div style="color:#475569; font-size:0.93rem;">'
            "✅ Văn bản hiện tại dùng từ vựng tiêu chuẩn. Các từ lóng sinh viên (như <b>препод, курсач, лаба, хвост, инфа, преза...</b>) sẽ tự động được bóc tách tại đây."
            "</div>"
        )
    render_html(
        f"""
        <div class="ocean-card" style="margin-top:12px;">
            <div class="ocean-card-header">
                <div class="ocean-card-title">{STICKER_SAILBOAT_MINI} 3. Giải thích Từ lóng & Viết tắt Sinh viên Nga</div>
                <span class="ocean-pill">Telegram / VK / Общага</span>
            </div>
            {slang_items_html}
        </div>
        """
    )

    vocab_table = res.get("vocabulary_table", [])
    if vocab_table:
        rows_html = "".join(
            f"""
            <tr>
                <td><b>{esc(row.get("ru_accent", ""))}</b></td>
                <td>{esc(row.get("en", ""))}</td>
                <td>{esc(row.get("vi", ""))}</td>
            </tr>
            """
            for row in vocab_table
        )
        render_html(
            f"""
            <div class="ocean-card">
                <div class="ocean-card-header">
                    <div class="ocean-card-title">{STICKER_ANCHOR_3D} 4. Bảng từ vựng Chuyên ngành 3 ngôn ngữ (Kèm dấu trọng âm)</div>
                    <span class="ocean-pill">RU (Ударение) • EN • VI</span>
                </div>
                <table class="vocab-table">
                    <thead>
                        <tr>
                            <th>🇷🇺 Tiếng Nga (Trọng âm)</th>
                            <th>🇬🇧 Tiếng Anh</th>
                            <th>🇻🇳 Tiếng Việt</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            """
        )
        if st.button("⭐ Lưu toàn bộ bảng từ này vào Sổ Từ Vựng & Flashcards (Tab 3)", key="btn_save_vocab_table"):
            added_cnt = add_vocab_items_to_notebook(vocab_table)
            if added_cnt > 0:
                st.toast(f"⭐ Đã lưu {added_cnt} từ mới vào Sổ Từ Vựng (Tab 3)!")
            else:
                st.toast("📌 Các từ này đã có sẵn trong Sổ Từ Vựng của bạn.")

    grammar_note = res.get("grammar_notes", "")
    study_tip = res.get("study_tip", "")
    if grammar_note or study_tip:
        notes_html = ""
        if grammar_note:
            notes_html += f"<div style='margin-bottom:8px;'><b>📐 Ghi chú Ngữ pháp:</b> {esc(grammar_note)}</div>"
        if study_tip:
            notes_html += f"<div><b>🎓 Góc Cố vấn Học tập tại Nga:</b> {esc(study_tip)}</div>"
        render_html(
            f"""
            <div class="ocean-card" style="background: linear-gradient(135deg, #E0F2FE 0%, #F0F9FF 100%); border-left: 6px solid #0284C7;">
                {notes_html}
            </div>
            """
        )


def main() -> None:
    init_session_state()
    inject_ocean_blue_css(is_author_admin=st.session_state["is_author_admin"])
    avatar_uri = get_author_avatar_data_uri()

    with st.sidebar:
        render_html(
            f"""
            <div class="author-sidebar-card">
                <img src="{avatar_uri}" class="author-avatar-img" alt="Mai Văn Minh" />
                <div>
                    <div class="author-info-name">Mai Văn Minh</div>
                    <div class="author-info-role">
                        Sinh viên năm 4<br/>
                        Chuyên ngành Đóng tàu<br/>
                        Trường Kỹ thuật Hàng hải Xanh-Petecbua
                    </div>
                    <span class="author-uni-badge">⚓ СПбГМТУ (Корабелка)</span>
                </div>
            </div>
            """
        )

        # THÔNG TIN SINH VIÊN SỬ DỤNG (CHỈ LƯU CỤC BỘ TRÊN TRÌNH DUYỆT USER)
        render_html(
            """
            <div class="user-checkin-card">
                <div style="font-size:0.94rem; font-weight:800; color:#7DD3FC; margin-bottom:2px;">
                    👤 Thông tin Sinh viên sử dụng
                </div>
                <div style="font-size:0.75rem; color:#E0F2FE; line-height:1.35;">
                    Chỉ cần nhập 1 lần — Lưu riêng trên trình duyệt của bạn:
                </div>
            </div>
            """
        )

        if st.session_state.get("pending_email_relay"):
            relay_info = st.session_state.pop("pending_email_relay")
            inject_localstorage_sync(action="save_profile", student_profile=relay_info)
            trigger_client_side_email_relay(
                full_name=relay_info["full_name"],
                student_year=relay_info["student_year"],
                university=relay_info["university"],
            )

        has_confirmed_profile = bool(
            st.session_state.get("confirmed_user_name") and st.session_state.get("confirmed_user_uni")
        )

        if has_confirmed_profile and not st.session_state["editing_student_profile"]:
            sv_name = st.session_state["confirmed_user_name"]
            sv_year = st.session_state.get("confirmed_user_year", "Sinh viên Năm 4")
            sv_uni = st.session_state["confirmed_user_uni"]

            render_html(
                f"""
                <div class="saved-student-badge-box">
                    <div style="font-size:0.75rem; color:#A7F3D0; font-weight:700; margin-bottom:3px;">
                        ✅ ĐÃ LƯU THÔNG TIN RIÊNG TƯ
                    </div>
                    <div style="font-size:0.97rem; font-weight:800; color:#FFFFFF;">🎓 {esc(sv_name)}</div>
                    <div style="font-size:0.81rem; color:#E0F2FE; margin-top:2px;">
                        • {esc(sv_year)}<br/>• Trường: <b>{esc(sv_uni)}</b>
                    </div>
                </div>
                """
            )
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                if st.button("✏️ Đổi thông tin", key="btn_edit_sv", use_container_width=True):
                    st.session_state["editing_student_profile"] = True
                    st.rerun()
            with c_p2:
                if st.button("📨 Gửi lại", key="btn_resend_sv", use_container_width=True):
                    _, ch = send_user_notification_email(sv_name, sv_year, sv_uni)
                    trigger_client_side_email_relay(sv_name, sv_year, sv_uni)
                    st.toast(f"📨 Đã gửi thông báo ({ch})!")
        else:
            cur_year = st.session_state.get("confirmed_user_year", "Sinh viên Năm 4")
            default_year_idx = STUDENT_YEAR_OPTIONS.index(cur_year) if cur_year in STUDENT_YEAR_OPTIONS else 3
            with st.form("student_user_checkin_form", clear_on_submit=False):
                u_name = st.text_input("✍️ Họ và tên của bạn:", value=st.session_state.get("confirmed_user_name", ""), placeholder="VD: Nguyễn Văn A")
                u_year = st.selectbox("🎓 Sinh viên năm mấy:", options=STUDENT_YEAR_OPTIONS, index=default_year_idx)
                u_uni = st.text_input("🏫 Học ở trường nào:", value=st.session_state.get("confirmed_user_uni", ""), placeholder="VD: СПбГМТУ, ИТМО, СПбГУ...")
                submit_sv = st.form_submit_button("✅ Xác nhận & Lưu", use_container_width=True, type="primary")

            if submit_sv:
                if not u_name.strip() or not u_uni.strip():
                    st.warning("⚠️ Vui lòng nhập đầy đủ Họ và tên và Tên trường!")
                else:
                    st.session_state["confirmed_user_name"] = u_name.strip()
                    st.session_state["confirmed_user_year"] = u_year
                    st.session_state["confirmed_user_uni"] = u_uni.strip()
                    st.session_state["editing_student_profile"] = False
                    send_user_notification_email(u_name.strip(), u_year, u_uni.strip())
                    st.session_state["pending_email_relay"] = {
                        "full_name": u_name.strip(),
                        "student_year": u_year,
                        "university": u_uni.strip(),
                    }
                    st.toast(f"✅ Đã lưu thông tin của {u_name.strip()}!")
                    st.rerun()

            if has_confirmed_profile and st.session_state["editing_student_profile"]:
                if st.button("↩️ Hủy chỉnh sửa", use_container_width=True):
                    st.session_state["editing_student_profile"] = False
                    st.rerun()

        st.markdown("---")

        # BUỒNG LÁI HỆ THỐNG & API KEY RIÊNG TƯ
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:9px; margin-bottom:8px;">
                {STICKER_HELM_WHEEL}
                <span style="font-size:1.08rem; font-weight:800; color:#FFFFFF;">Buồng Lái Hệ Thống</span>
            </div>
            """
        )

        saved_key_val = clean_api_key(st.session_state.get("saved_gemini_api_key", ""))
        gemini_api_key = st.text_input(
            "🔑 Gemini API Key (Lưu riêng trên trình duyệt):",
            value=saved_key_val,
            type="password",
            placeholder="Dán Gemini API Key (hoặc để trống)",
            help="Key chỉ được lưu trên trình duyệt cá nhân của bạn, hoàn toàn cách ly với người dùng khác.",
        )

        render_html(
            f'<a href="{GEMINI_API_KEY_URL}" target="_blank" rel="noopener noreferrer" class="gemini-key-link-btn">🔗 Lấy Gemini API Key miễn phí ↗</a>'
        )

        clean_key_input = clean_api_key(gemini_api_key)
        if clean_key_input and clean_key_input != saved_key_val and clean_key_input not in st.session_state["declined_keys"]:
            st.warning("💾 **Lưu Gemini API Key trên trình duyệt cá nhân cho các lần sau?**")
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("✅ Lưu Key", key="btn_save_k", type="primary", use_container_width=True):
                    st.session_state["saved_gemini_api_key"] = clean_key_input
                    inject_localstorage_sync(action="save_key", key_to_save=clean_key_input)
                    st.toast("✅ Đã lưu Key an toàn trên trình duyệt của bạn!")
                    st.rerun()
            with sc2:
                if st.button("❌ Phiên này thôi", key="btn_no_k", use_container_width=True):
                    st.session_state["declined_keys"].add(clean_key_input)
                    st.rerun()

        if clean_key_input:
            avail_models = discover_available_gemini_models(clean_key_input)
            top_model = avail_models[0] if avail_models else "gemini-2.0-flash"
            st.success(f"✨ AI Ready (`{top_model}`) — Bật OCR Ảnh, Audio Đa định dạng & Tóm tắt AI!")
            if clean_key_input == saved_key_val:
                if st.button("🗑️ Xóa Key đã lưu", key="btn_del_k", use_container_width=True):
                    st.session_state["saved_gemini_api_key"] = ""
                    inject_localstorage_sync(action="delete_key")
                    st.rerun()
        else:
            st.info("⚡ Chế độ Miễn phí: **Dịch Đa Luồng GTX (Chia đoạn thông minh)**.")

        st.markdown("---")
        st.markdown("### 🎓 Chuyên ngành Ưu tiên")
        selected_domain = st.selectbox("Chọn lĩnh vực:", options=DOMAIN_OPTIONS, index=0)

        st.markdown("---")
        st.markdown("### 📲 Chia sẻ Link & QR Điện thoại")
        app_public_url = st.text_input("🌐 Link ứng dụng:", value="https://dich-thuat-anhminh.streamlit.app", key="share_url_input")
        if app_public_url.strip():
            short_link = shorten_share_url(app_public_url.strip())
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(short_link)}"
            render_html(
                f"""
                <div style="background:rgba(255,255,255,0.12); border:1.5px solid #38BDF8; border-radius:14px; padding:10px; text-align:center;">
                    <a href="{esc(short_link)}" target="_blank" style="color:#7DD3FC !important; font-weight:800; font-size:0.88rem; word-break:break-all;">{esc(short_link)}</a>
                    <div style="margin-top:8px;"><img src="{qr_api_url}" alt="QR Code" style="width:118px; height:118px; border-radius:10px; border:3px solid #FFFFFF; background:#FFFFFF;" /></div>
                </div>
                """
            )

        st.markdown("---")
        st.markdown("### 📚 Tra nhanh Lóng Sinh viên Nga (30 từ)")
        slang_search = st.text_input("🔍 Tìm từ lóng:", placeholder="VD: препод, инфа, преза, хвост...")
        filtered_slang = [
            it for it in RUSSIAN_SLANG_DICT
            if not slang_search.strip()
            or slang_search.lower() in it["word"].lower()
            or slang_search.lower() in it["vi"].lower()
            or slang_search.lower() in it["full"].lower()
        ]
        with st.container(height=230):
            for it in filtered_slang:
                with st.expander(f"⚓ {it['accent']} — {it['vi']}"):
                    st.markdown(f"- **Đầy đủ:** `{it['full']}`\n- **EN:** *{it['en']}*\n- **VD:** _{it['example']}_")
                    if st.button(f"Đưa «{it['word']}» vào ô dịch", key=f"use_sl_{it['word']}"):
                        st.session_state["input_text_area"] = it["example"]
                        st.rerun()

        st.markdown("---")
        with st.expander("🔐 Chế độ Tác giả (Mai Văn Minh)"):
            if not st.session_state["is_author_admin"]:
                admin_pwd = st.text_input("Mật khẩu tác giả:", type="password", key="author_pwd_input")
                if st.button("🔓 Mở khóa", use_container_width=True):
                    if verify_author_password(admin_pwd):
                        st.session_state["is_author_admin"] = True
                        st.rerun()
                    else:
                        st.error("❌ Mật khẩu không đúng!")
            else:
                st.success("👑 Đang ở Chế độ Tác giả")
                if USER_LOGS_FILE.exists():
                    try:
                        logs_data = json.loads(USER_LOGS_FILE.read_text(encoding="utf-8"))
                        st.markdown(f"**📋 Sinh viên đã đăng ký ({len(logs_data)}):**")
                        for entry in logs_data[:15]:
                            st.caption(f"• **{entry.get('full_name')}** — {entry.get('student_year')} ({entry.get('university')}) `{entry.get('time')}`")
                    except Exception:
                        pass
                if st.button("🔒 Khóa lại", use_container_width=True):
                    st.session_state["is_author_admin"] = False
                    st.rerun()

        render_html(
            f"""
            <div style="text-align:center; font-size:0.8rem; padding: 8px; margin-top:6px; background: rgba(255,255,255,0.08); border-radius: 12px;">
                {STICKER_SAILBOAT_MINI}<br/>
                <b>Anh Minh Translate {APP_VERSION}</b><br/>
                Tác giả: <b>Mai Văn Minh</b> — <i>СПбГМТУ</i>
            </div>
            """
        )

    render_brand_header(avatar_uri)

    tab1, tab2, tab3 = st.tabs(
        [
            "📝 TAB 1: DỊCH VĂN BẢN, ẢNH SLIDE & TÀI LIỆU",
            "🎙️ TAB 2: GIẢNG ĐƯỜNG — THU ÂM & TÓM TẮT AI",
            "🎴 TAB 3: SỔ TỪ VỰNG, FLASHCARDS & CHUYÊN NGÀNH",
        ]
    )

    # ==========================================================================
    # TAB 1: DỊCH VĂN BẢN + OCR ẢNH SLIDE + TẢI TÀI LIỆU + LỊCH SỬ
    # ==========================================================================
    with tab1:
        top_c1, top_c2, top_c3 = st.columns([2.4, 0.7, 2.9])
        with top_c1:
            direction = st.selectbox(
                "🧭 Chiều dịch thuật:",
                options=DIRECTION_OPTIONS,
                index=DIRECTION_OPTIONS.index(st.session_state["selected_direction"]),
            )
            st.session_state["selected_direction"] = direction
        with top_c2:
            st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
            if st.button("⇄ Đổi", use_container_width=True, help="Hoán đổi nhanh chiều Nga ➔ Việt và Việt ➔ Nga"):
                if st.session_state["selected_direction"] == DIRECTION_OPTIONS[0]:
                    st.session_state["selected_direction"] = DIRECTION_OPTIONS[1]
                else:
                    st.session_state["selected_direction"] = DIRECTION_OPTIONS[0]
                st.rerun()
        with top_c3:
            render_html(
                f"""
                <div style="background:#FFFFFF; border:1.5px solid #BAE6FD; border-radius:14px; padding:11px 16px; margin-top:4px; display:flex; align-items:center; justify-content:space-between;">
                    <div style="display:flex; align-items:center; gap:9px;">
                        {STICKER_COMPASS_3D}
                        <div>
                            <div style="font-weight:800; color:#0369A1; font-size:0.9rem;">Chuyên ngành: {esc(selected_domain)}</div>
                            <div style="font-size:0.78rem; color:#475569;">Hỗ trợ văn bản dài (auto-chunk), ảnh chụp Slide & tài liệu .docx/.pdf/.txt</div>
                        </div>
                    </div>
                </div>
                """
            )

        # CÁC CÂU MẪU THỬ NHANH
        preset_cols = st.columns(len(QUICK_SAMPLE_PRESETS))
        for idx, preset in enumerate(QUICK_SAMPLE_PRESETS):
            with preset_cols[idx]:
                if st.button(preset["label"], key=f"preset_{idx}", use_container_width=True):
                    st.session_state["input_text_area"] = preset["text"]
                    st.session_state["selected_direction"] = preset["direction"]
                    st.rerun()

        source_text = st.text_area(
            "✍️ Nhập văn bản, đoạn bài giảng dài hoặc tin nhắn Telegram/VK cần dịch:",
            key="input_text_area",
            height=145,
            placeholder="Dán tin nhắn tiếng Nga của giảng viên / phòng Visa / bạn học, hoặc đoạn tiếng Việt muốn dịch sang tiếng Nga...",
        )

        word_cnt = len(source_text.split()) if source_text.strip() else 0
        st.caption(f"📊 Độ dài: **{len(source_text)}** ký tự • **{word_cnt}** từ (Tự động chia đoạn nếu dài >1.100 ký tự)")

        # CÔNG CỤ MỞ RỘNG: OCR ẢNH SLIDE & TẢI FILE TÀI LIỆU
        with st.expander("📸 Dịch Ảnh chụp Slide / Bảng viết (OCR) hoặc Tải File tài liệu (.txt, .docx, .pdf)"):
            ext_c1, ext_c2 = st.columns(2)
            with ext_c1:
                uploaded_img = st.file_uploader(
                    "📷 Tải ảnh chụp Slide / Bảng / Tin nhắn:",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="ocr_img_uploader",
                )
                if uploaded_img is not None:
                    st.image(uploaded_img, width=260, caption="Ảnh cần OCR & Dịch")
                    if st.button("🔍 Quét chữ (OCR) & Dịch ảnh bằng Gemini AI", type="primary", use_container_width=True):
                        if not clean_key_input:
                            st.warning("⚠️ Tính năng OCR & Dịch ảnh cần dán **Gemini API Key** (miễn phí) ở thanh bên trái!")
                        else:
                            mime_img = uploaded_img.type or "image/jpeg"
                            with st.spinner("🧠 Đang quét chữ và dịch học thuật từ ảnh..."):
                                ocr_res, ocr_err = call_gemini_ocr_and_translate_image(
                                    api_key=clean_key_input,
                                    image_bytes=uploaded_img.getvalue(),
                                    mime_type=mime_img,
                                    direction=direction,
                                    domain=selected_domain,
                                )
                                if ocr_res:
                                    extracted = ocr_res.get("extracted_text", "")
                                    if extracted:
                                        st.session_state["input_text_area"] = extracted
                                    st.session_state["last_translation_result"] = ocr_res
                                    st.session_state["last_used_ai"] = True
                                    st.toast("✅ Đã OCR và dịch xong ảnh!")
                                    st.rerun()
                                else:
                                    st.error(f"⚠️ Không thể xử lý ảnh: {ocr_err}")

            with ext_c2:
                uploaded_doc = st.file_uploader(
                    "📄 Hoặc tải file tài liệu (.txt, .docx, .pdf):",
                    type=["txt", "md", "docx", "pdf"],
                    key="doc_file_uploader",
                )
                if uploaded_doc is not None:
                    if st.button("📥 Trích xuất chữ đưa vào ô dịch", use_container_width=True):
                        doc_txt, doc_err = extract_text_from_uploaded_doc(uploaded_doc)
                        if doc_err:
                            st.warning(f"⚠️ {doc_err}")
                        elif doc_txt:
                            st.session_state["input_text_area"] = doc_txt[:8000]
                            st.toast(f"✅ Đã nạp {len(doc_txt[:8000])} ký tự từ {uploaded_doc.name}!")
                            st.rerun()

        act_c1, act_c2, act_c3 = st.columns([2.2, 1.8, 1.0])
        with act_c1:
            translate_clicked = st.button("🚀 Dịch & Phân Tích Ngay", type="primary", use_container_width=True)
        with act_c2:
            tts_quick_clicked = st.button("🔊 Phát âm văn bản gốc", type="secondary", use_container_width=True)
        with act_c3:
            if st.button("🧹 Xóa ô", use_container_width=True):
                st.session_state["input_text_area"] = ""
                st.rerun()

        if tts_quick_clicked and source_text.strip():
            has_cyrillic = bool(re.search(r"[а-яА-ЯёЁ]", source_text))
            lang_tts = "ru" if has_cyrillic else ("vi" if "Tiếng Việt ➔" in direction else "en")
            with st.spinner("Đang tạo giọng đọc..."):
                audio_bytes = generate_tts_audio(source_text, lang_tts)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

        if translate_clicked:
            if not source_text.strip():
                st.warning("⚠️ Vui lòng nhập văn bản cần dịch!")
            else:
                result_data: Optional[Dict] = None
                used_ai = False
                if clean_key_input:
                    with st.spinner("🧠 Đang dịch & phân tích chuyên sâu bằng Gemini AI..."):
                        result_data, gemini_err = call_gemini_smart_translate(
                            api_key=clean_key_input,
                            source_text=source_text,
                            direction=direction,
                            domain=selected_domain,
                        )
                        if result_data:
                            used_ai = True
                        elif gemini_err and "không chính xác" in gemini_err.lower():
                            st.warning(f"⚠️ {gemini_err} Đang tự động chuyển sang chế độ Đa Luồng GTX!")

                if not result_data:
                    with st.spinner("⚡ Đang dịch đa luồng siêu tốc (Auto-Chunking GTX)..."):
                        result_data = fallback_smart_translate(source_text, direction, selected_domain)

                st.session_state["last_translation_result"] = result_data
                st.session_state["last_used_ai"] = used_ai
                st.session_state["translation_history"].insert(
                    0,
                    {
                        "time": datetime.now().strftime("%H:%M"),
                        "source": source_text.strip()[:160],
                        "full_source": source_text.strip(),
                        "direction": direction,
                        "result": result_data,
                        "used_ai": used_ai,
                    },
                )
                st.session_state["translation_history"] = st.session_state["translation_history"][:MAX_HISTORY_ITEMS]

        if st.session_state.get("last_translation_result"):
            render_translation_result(
                st.session_state["last_translation_result"],
                selected_domain,
                st.session_state.get("last_used_ai", False),
            )

        # LỊCH SỬ DỊCH TRONG PHIÊN
        if st.session_state["translation_history"]:
            with st.expander(f"🕒 Lịch sử dịch gần đây ({len(st.session_state['translation_history'])} mục)"):
                for h_idx, h_item in enumerate(st.session_state["translation_history"][:10]):
                    hc1, hc2 = st.columns([5, 1])
                    with hc1:
                        st.markdown(f"**`{h_item['time']}`** — {h_item['source']}")
                    with hc2:
                        if st.button("↩️ Xem", key=f"hist_load_{h_idx}", use_container_width=True):
                            st.session_state["input_text_area"] = h_item["full_source"]
                            st.session_state["last_translation_result"] = h_item["result"]
                            st.session_state["last_used_ai"] = h_item["used_ai"]
                            st.rerun()

    # ==========================================================================
    # TAB 2: GIẢNG ĐƯỜNG REAL-TIME & NHẬN DIỆN AUDIO ĐA ĐỊNH DẠNG
    # ==========================================================================
    with tab2:
        realtime_html = build_realtime_lecture_component(
            gemini_api_key=clean_key_input,
            selected_domain=selected_domain,
        )
        components.html(realtime_html, height=740, scrolling=False)

        render_html(
            f'<div class="nautical-divider">{STICKER_ANCHOR_3D} THU ÂM TRỰC TIẾP / TẢI FILE GHI ÂM ĐA ĐỊNH DẠNG (.WAV, .MP3, .M4A, .OGG) {STICKER_ANCHOR_3D}</div>'
        )

        up_col1, up_col2 = st.columns(2)
        with up_col1:
            file_speech_lang = st.selectbox(
                "🗣️ Ngôn ngữ nói / file ghi âm:",
                options=[("ru-RU", "🇷🇺 Tiếng Nga (ru-RU)"), ("vi-VN", "🇻🇳 Tiếng Việt (vi-VN)"), ("en-US", "🇬🇧 Tiếng Anh (en-US)")],
                format_func=lambda x: x[1],
                index=0,
            )[0]
            file_target_lang = st.selectbox(
                "🎯 Dịch nội dung âm thanh sang:",
                options=[("vi", "🇻🇳 Tiếng Việt"), ("ru", "🇷🇺 Tiếng Nga"), ("en", "🇬🇧 Tiếng Anh")],
                format_func=lambda x: x[1],
                index=0,
            )[0]
            python_dsp_gain = st.slider(
                "🎚️ Khuếch đại RMS Auto-Gain cho file WAV / Thu trực tiếp:",
                min_value=2.0, max_value=15.0, value=12.0, step=0.5,
            )

        with up_col2:
            recorded_mic = st.audio_input("🎙️ Thu âm trực tiếp trên Điện thoại / Máy tính:") if hasattr(st, "audio_input") else None
            uploaded_audio = st.file_uploader(
                "📤 Hoặc tải file ghi âm bài giảng / Telegram Voice (.wav, .mp3, .m4a, .ogg, .webm):",
                type=["wav", "mp3", "m4a", "ogg", "webm"],
            )

        audio_source_bytes: Optional[bytes] = None
        audio_ext = ".wav"
        if recorded_mic is not None:
            audio_source_bytes = recorded_mic.getvalue()
            audio_ext = ".wav"
        elif uploaded_audio is not None:
            audio_source_bytes = uploaded_audio.getvalue()
            audio_ext = Path(uploaded_audio.name).suffix.lower() or ".wav"

        if audio_source_bytes:
            with st.spinner(f"⏳ Đang xử lý âm thanh ({audio_ext}) & dịch thuật..."):
                tr_text, tl_text, err = transcribe_and_translate_audio_bytes(
                    audio_bytes=audio_source_bytes,
                    source_lang_speech=file_speech_lang,
                    target_lang_trans=file_target_lang,
                    gemini_api_key=clean_key_input,
                    selected_domain=selected_domain,
                    max_gain_factor=python_dsp_gain,
                    file_ext=audio_ext,
                )
                if err:
                    st.error(f"⚠️ {err}")
                else:
                    render_html(
                        f"""
                        <div class="ocean-card">
                            <div class="ocean-card-header">
                                <div class="ocean-card-title">✅ Kết quả Nhận diện Giọng nói & Dịch thuật</div>
                                <span class="ocean-pill">{esc(file_speech_lang)} ➔ {esc(file_target_lang.upper())}</span>
                            </div>
                            <p style="color:#0369A1; font-weight:700;">🗣️ Lời nói nhận diện được:</p>
                            <div class="translation-main-text" style="margin-bottom:14px;">{esc(tr_text)}</div>
                            <p style="color:#0369A1; font-weight:700;">🌊 Bản dịch hoàn chỉnh:</p>
                            <div class="translation-main-text" style="border-left-color:#06B6D4; background:#F0F9FF; color:#0369A1 !important;">{esc(tl_text)}</div>
                        </div>
                        """
                    )
                    txt_report = (
                        f"BẢN DỊCH GHI ÂM — ANH MINH TRANSLATE ({APP_VERSION})\n"
                        f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"----------------------------------------\n"
                        f"Lời gốc ({file_speech_lang}):\n{tr_text}\n\n"
                        f"Bản dịch ({file_target_lang}):\n{tl_text}\n"
                    )
                    st.download_button(
                        label="📥 Tải bản dịch ghi âm (.txt)",
                        data=txt_report.encode("utf-8"),
                        file_name="Ket_Qua_Ghi_Am_AnhMinhTranslate.txt",
                        mime="text/plain",
                    )

    # ==========================================================================
    # TAB 3: SỔ TỪ VỰNG CÁ NHÂN, FLASHCARDS ÔN THI & TỪ ĐIỂN CHUYÊN NGÀNH
    # ==========================================================================
    with tab3:
        nb_col1, nb_col2 = st.columns([1.15, 1.0])

        with nb_col1:
            st.markdown("### 🎴 Thẻ Ghi Nhớ Ôn Thi (Interactive Flashcards)")
            deck_choice = st.radio(
                "Chọn bộ thẻ ôn tập:",
                options=["⭐ Sổ Từ Vựng Đã Lưu", f"⚓ Chuyên ngành: {selected_domain}", "💬 Tiếng Lóng Sinh Viên Nga"],
                horizontal=True,
            )

            if deck_choice == "⭐ Sổ Từ Vựng Đã Lưu":
                active_deck = st.session_state["saved_vocab_notebook"]
            elif deck_choice.startswith("⚓"):
                active_deck = [
                    {"ru_accent": x["ru"], "en": x["en"], "vi": x["vi"]}
                    for x in DOMAIN_GLOSSARY.get(selected_domain, [])
                ]
            else:
                active_deck = [
                    {"ru_accent": f"{x['accent']} ({x['full']})", "en": x["en"], "vi": x["vi"]}
                    for x in RUSSIAN_SLANG_DICT
                ]

            if not active_deck:
                st.info("📌 Sổ từ vựng của bạn đang trống. Hãy dịch ở Tab 1 rồi bấm **⭐ Lưu vào Sổ Từ Vựng**, hoặc chọn bộ thẻ Chuyên ngành / Tiếng lóng ở trên để ôn ngay!")
            else:
                idx = st.session_state["flashcard_index"] % len(active_deck)
                card = active_deck[idx]
                meaning_html = (
                    f'<div class="flashcard-meaning">🇻🇳 {esc(card["vi"])}<br/><span style="font-size:0.95rem;color:#475569;">🇬🇧 {esc(card["en"])}</span></div>'
                    if st.session_state["flashcard_show_back"]
                    else '<div style="color:#64748B;margin-top:12px;font-size:0.9rem;">👆 Bấm nút «🔄 Lật thẻ» để xem nghĩa Tiếng Việt & Tiếng Anh</div>'
                )
                render_html(
                    f"""
                    <div class="flashcard-box">
                        <div style="font-size:0.8rem;font-weight:700;color:#0284C7;margin-bottom:8px;">THẺ {idx + 1} / {len(active_deck)}</div>
                        <div class="flashcard-ru">{esc(card["ru_accent"])}</div>
                        {meaning_html}
                    </div>
                    """
                )
                fc_b1, fc_b2, fc_b3, fc_b4 = st.columns(4)
                with fc_b1:
                    if st.button("⬅️ Trước", use_container_width=True):
                        st.session_state["flashcard_index"] = (idx - 1) % len(active_deck)
                        st.session_state["flashcard_show_back"] = False
                        st.rerun()
                with fc_b2:
                    if st.button("🔄 Lật thẻ", type="primary", use_container_width=True):
                        st.session_state["flashcard_show_back"] = not st.session_state["flashcard_show_back"]
                        st.rerun()
                with fc_b3:
                    if st.button("🔊 Phát âm", use_container_width=True):
                        clean_ru_word = card["ru_accent"].split("(")[0].replace("\u0301", "").strip()
                        fc_audio = generate_tts_audio(clean_ru_word, "ru")
                        if fc_audio:
                            st.audio(fc_audio, format="audio/mp3")
                with fc_b4:
                    if st.button("Tiếp ➡️", use_container_width=True):
                        st.session_state["flashcard_index"] = (idx + 1) % len(active_deck)
                        st.session_state["flashcard_show_back"] = False
                        st.rerun()

        with nb_col2:
            st.markdown("### 📥 Sổ Từ Vựng & Xuất Anki / Quizlet (.CSV)")
            notebook_items = st.session_state["saved_vocab_notebook"]
            export_source = notebook_items if notebook_items else [
                {"ru_accent": x["ru"], "en": x["en"], "vi": x["vi"]}
                for x in DOMAIN_GLOSSARY.get(selected_domain, [])
            ]
            csv_label = (
                f"📥 Tải Sổ Từ Vựng của bạn ({len(notebook_items)} từ) — Chuẩn Anki/Excel"
                if notebook_items
                else f"📥 Tải bộ thuật ngữ {selected_domain} ({len(export_source)} từ) — Chuẩn Anki/Excel"
            )
            st.download_button(
                label=csv_label,
                data=export_vocab_to_anki_csv(export_source),
                file_name="Anki_Vocab_AnhMinhTranslate.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

            if notebook_items:
                nb_rows = "".join(
                    f"<tr><td><b>{esc(v['ru_accent'])}</b></td><td>{esc(v['vi'])}</td><td>{esc(v['en'])}</td></tr>"
                    for v in notebook_items[:25]
                )
                render_html(
                    f"""
                    <table class="vocab-table">
                        <thead><tr><th>🇷🇺 Tiếng Nga</th><th>🇻🇳 Tiếng Việt</th><th>🇬🇧 EN</th></tr></thead>
                        <tbody>{nb_rows}</tbody>
                    </table>
                    """
                )
                if st.button("🗑️ Xóa toàn bộ Sổ Từ Vựng", use_container_width=True):
                    st.session_state["saved_vocab_notebook"] = []
                    st.rerun()
            else:
                st.caption(f"Bảng thuật ngữ chuẩn chuyên ngành **{selected_domain}**:")
                dom_rows = "".join(
                    f"<tr><td><b>{esc(v['ru'])}</b></td><td>{esc(v['vi'])}</td><td>{esc(v['en'])}</td></tr>"
                    for v in DOMAIN_GLOSSARY.get(selected_domain, [])
                )
                render_html(
                    f"""
                    <table class="vocab-table">
                        <thead><tr><th>🇷🇺 Tiếng Nga</th><th>🇻🇳 Tiếng Việt</th><th>🇬🇧 EN</th></tr></thead>
                        <tbody>{dom_rows}</tbody>
                    </table>
                    """
                )


if __name__ == "__main__":
    main()
