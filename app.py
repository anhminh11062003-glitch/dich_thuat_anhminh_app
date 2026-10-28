from array import array
import base64
import hashlib
import io
import json
import math
import os
import re
import urllib.parse
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


# ==============================================================================
# 1. CẤU HÌNH TRANG, BẢO MẬT TÁC GIẢ & EMAIL THÔNG BỌ
# ==============================================================================
st.set_page_config(
    page_title="Anh Minh Translate | Mai Văn Minh - СПбГМТУ",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Link lấy Gemini API Key chính thức từ Google AI Studio
GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"

# Email nhận thông báo của tác giả
AUTHOR_NOTIFICATION_EMAIL = "anhminh11062003@gmail.com"

# Mật khẩu mở khóa giao diện Tác giả (sửa app / xem Github / xem danh sách người dùng)
DEFAULT_AUTHOR_PASSWORD = os.environ.get("AUTHOR_ADMIN_PASSWORD", "minh1106")

# Tùy chọn cấu hình thêm Formspree Endpoint hoặc EmailJS
FORMSPREE_ENDPOINT = os.environ.get("FORMSPREE_ENDPOINT", "")
EMAILJS_SERVICE_ID = os.environ.get("EMAILJS_SERVICE_ID", "")
EMAILJS_TEMPLATE_ID = os.environ.get("EMAILJS_TEMPLATE_ID", "")
EMAILJS_PUBLIC_KEY = os.environ.get("EMAILJS_PUBLIC_KEY", "")

# File lưu cố định API Key, Hồ sơ Sinh viên và Lịch sử người dùng trên ổ đĩa
SAVED_KEYS_FILE = Path(".saved_gemini_keys.json")
SAVED_PROFILES_FILE = Path(".saved_student_profiles.json")
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


def render_html(html_str: str) -> None:
    cleaned_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(cleaned_lines), unsafe_allow_html=True)


def clean_api_key(raw_key: str) -> str:
    """Làm sạch mọi ký tự thừa, khoảng trắng, dấu nháy khi người dùng dán API Key."""
    if not raw_key:
        return ""
    return re.sub(r'[\s"\'\`]+', "", raw_key.strip())


# ==============================================================================
# 1B. QUẢN LÝ LƯU CỐ ĐỊNH GEMINI API KEY, THÔNG TIN SINH VIÊN & GỬI EMAIL
# ==============================================================================
def get_client_fingerprint() -> str:
    """Tạo mã định danh trình duyệt/phiên kết nối để lưu Key & Thông tin sinh viên cố định."""
    try:
        headers = st.context.headers if hasattr(st, "context") and hasattr(st.context, "headers") else {}
        ua = headers.get("User-Agent", "default_ua")
        lang = headers.get("Accept-Language", "vi")
        raw_id = f"{ua}::{lang}"
        return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:20]
    except Exception:
        return "default_device"


def load_saved_api_key_from_store() -> str:
    """Đọc API Key đã được người dùng đồng ý lưu cố định trước đó."""
    try:
        qp_key = st.query_params.get("saved_gkey", "")
        if qp_key:
            return clean_api_key(qp_key)
    except Exception:
        pass

    fp = get_client_fingerprint()
    if SAVED_KEYS_FILE.exists():
        try:
            data = json.loads(SAVED_KEYS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return clean_api_key(data.get(fp, data.get("default", "")))
        except Exception:
            pass
    return ""


def save_api_key_permanently(api_key: str) -> None:
    """Lưu cố định API Key vào ổ đĩa."""
    clean_k = clean_api_key(api_key)
    fp = get_client_fingerprint()
    data = {}
    if SAVED_KEYS_FILE.exists():
        try:
            data = json.loads(SAVED_KEYS_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    data[fp] = clean_k
    data["default"] = clean_k
    try:
        SAVED_KEYS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def delete_saved_api_key() -> None:
    """Xóa API Key đã lưu cố định khi người dùng muốn đổi hoặc gỡ Key."""
    fp = get_client_fingerprint()
    if SAVED_KEYS_FILE.exists():
        try:
            data = json.loads(SAVED_KEYS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.pop(fp, None)
                data.pop("default", None)
                SAVED_KEYS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    try:
        if "saved_gkey" in st.query_params:
            del st.query_params["saved_gkey"]
    except Exception:
        pass


def load_saved_student_profile() -> Dict[str, str]:
    """Đọc thông tin sinh viên đã lưu cố định từ query params (localStorage đồng bộ) hoặc file ổ đĩa."""
    try:
        qp_name = st.query_params.get("sv_name", "").strip()
        qp_year = st.query_params.get("sv_year", "").strip()
        qp_uni = st.query_params.get("sv_uni", "").strip()
        if qp_name and qp_uni:
            profile = {
                "full_name": qp_name,
                "student_year": qp_year if qp_year in STUDENT_YEAR_OPTIONS else "Sinh viên Năm 4",
                "university": qp_uni,
            }
            save_student_profile_permanently(
                profile["full_name"], profile["student_year"], profile["university"]
            )
            return profile
    except Exception:
        pass

    fp = get_client_fingerprint()
    if SAVED_PROFILES_FILE.exists():
        try:
            data = json.loads(SAVED_PROFILES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                prof = data.get(fp) or data.get("default")
                if isinstance(prof, dict) and prof.get("full_name") and prof.get("university"):
                    return {
                        "full_name": str(prof["full_name"]).strip(),
                        "student_year": str(prof.get("student_year", "Sinh viên Năm 4")).strip(),
                        "university": str(prof["university"]).strip(),
                    }
        except Exception:
            pass
    return {}


def save_student_profile_permanently(full_name: str, student_year: str, university: str) -> None:
    """Lưu cố định thông tin sinh viên vào ổ đĩa để các lần truy cập sau không cần nhập lại."""
    fp = get_client_fingerprint()
    data = {}
    if SAVED_PROFILES_FILE.exists():
        try:
            data = json.loads(SAVED_PROFILES_FILE.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}
    profile_obj = {
        "full_name": full_name.strip(),
        "student_year": student_year.strip(),
        "university": university.strip(),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    data[fp] = profile_obj
    data["default"] = profile_obj
    try:
        SAVED_PROFILES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def delete_saved_student_profile() -> None:
    """Xóa thông tin sinh viên đã lưu khi người dùng muốn chỉnh sửa/đổi thông tin."""
    fp = get_client_fingerprint()
    if SAVED_PROFILES_FILE.exists():
        try:
            data = json.loads(SAVED_PROFILES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.pop(fp, None)
                data.pop("default", None)
                SAVED_PROFILES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    try:
        for k in ("sv_name", "sv_year", "sv_uni"):
            if k in st.query_params:
                del st.query_params[k]
    except Exception:
        pass


def inject_localstorage_sync(
    action: str = "load_all",
    key_to_save: str = "",
    student_profile: Optional[Dict[str, str]] = None,
) -> None:
    """
    Đồng bộ cả Gemini API Key và Thông tin Sinh viên với localStorage trên trình duyệt
    để tự động nạp lại cho mọi lần mở web sau.
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
                const url = new URL(window.parent.location.href);
                if (url.searchParams.has("saved_gkey")) {
                    url.searchParams.delete("saved_gkey");
                    window.parent.history.replaceState({}, "", url.toString());
                }
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
                const prof = {safe_profile};
                localStorage.setItem("anhminh_saved_student_profile", JSON.stringify(prof));
                const url = new URL(window.parent.location.href);
                if (prof.full_name) url.searchParams.set("sv_name", prof.full_name);
                if (prof.student_year) url.searchParams.set("sv_year", prof.student_year);
                if (prof.university) url.searchParams.set("sv_uni", prof.university);
                window.parent.history.replaceState({{}}, "", url.toString());
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
                const url = new URL(window.parent.location.href);
                ["sv_name", "sv_year", "sv_uni"].forEach(k => url.searchParams.delete(k));
                window.parent.history.replaceState({}, "", url.toString());
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
                const url = new URL(window.parent.location.href);
                let changed = false;

                const savedKey = localStorage.getItem("anhminh_saved_gemini_key");
                if (savedKey && savedKey.trim().length > 10) {
                    if (url.searchParams.get("saved_gkey") !== savedKey.trim()) {
                        url.searchParams.set("saved_gkey", savedKey.trim());
                        changed = true;
                    }
                }

                const rawProf = localStorage.getItem("anhminh_saved_student_profile");
                if (rawProf) {
                    const prof = JSON.parse(rawProf);
                    if (prof && prof.full_name && prof.university) {
                        if (url.searchParams.get("sv_name") !== prof.full_name) {
                            url.searchParams.set("sv_name", prof.full_name);
                            url.searchParams.set("sv_year", prof.student_year || "Sinh viên Năm 4");
                            url.searchParams.set("sv_uni", prof.university);
                            changed = true;
                        }
                    }
                }

                if (changed) {
                    window.parent.location.replace(url.toString());
                }
            } catch (e) {}
            </script>
            """,
            height=0,
        )


def log_user_locally(full_name: str, student_year: str, university: str) -> None:
    """Lưu danh sách người dùng vào file log để tác giả có thể kiểm tra bất cứ lúc nào."""
    logs = []
    if USER_LOGS_FILE.exists():
        try:
            logs = json.loads(USER_LOGS_FILE.read_text(encoding="utf-8"))
            if not isinstance(logs, list):
                logs = []
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
        USER_LOGS_FILE.write_text(json.dumps(logs[:200], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def send_user_notification_email(full_name: str, student_year: str, university: str) -> Tuple[bool, str]:
    """
    Gửi thông báo người dùng mới về email tác giả (anhminh11062003@gmail.com).
    Hỗ trợ 4 kênh: Gmail SMTP trực tiếp -> Formspree -> EmailJS -> FormSubmit (kèm Origin/Referer).
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log_user_locally(full_name, student_year, university)

    # 1. Kênh SMTP Gmail trực tiếp (nếu tác giả cấu hình GMAIL_APP_PASSWORD trong Secrets/Env)
    gmail_app_pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    try:
        if not gmail_app_pwd and "GMAIL_APP_PASSWORD" in st.secrets:
            gmail_app_pwd = str(st.secrets["GMAIL_APP_PASSWORD"]).strip()
    except Exception:
        pass

    if gmail_app_pwd:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚢 [Anh Minh Translate] Sinh viên mới: {full_name} ({university})"
            msg["From"] = AUTHOR_NOTIFICATION_EMAIL
            msg["To"] = AUTHOR_NOTIFICATION_EMAIL
            html_body = f"""
            <div style="font-family:Arial,sans-serif;padding:16px;border:2px solid #0284C7;border-radius:12px;">
                <h3 style="color:#0369A1;margin-top:0;">🚢 Thông báo Sinh viên sử dụng Anh Minh Translate</h3>
                <p><b>👤 Họ và tên:</b> {full_name}</p>
                <p><b>🎓 Sinh viên năm:</b> {student_year}</p>
                <p><b>🏫 Trường đại học:</b> {university}</p>
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Origin": "https://dich-thuat-anhminh.streamlit.app",
        "Referer": "https://dich-thuat-anhminh.streamlit.app/",
    }

    # 2. Kênh Formspree (nếu có FORMSPREE_ENDPOINT)
    formspree_url = FORMSPREE_ENDPOINT.strip()
    if formspree_url:
        try:
            fs_data = {
                "email": AUTHOR_NOTIFICATION_EMAIL,
                "Họ và tên": full_name,
                "Sinh viên năm": student_year,
                "Trường đại học": university,
                "Thời gian": now_str,
            }
            req_fsp = urllib.request.Request(
                formspree_url,
                data=json.dumps(fs_data).encode("utf-8"),
                headers=headers_json,
                method="POST",
            )
            with urllib.request.urlopen(req_fsp, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True, "Formspree"
        except Exception:
            pass

    # 3. Kênh EmailJS (nếu có cấu hình)
    ejs_service = EMAILJS_SERVICE_ID.strip()
    ejs_template = EMAILJS_TEMPLATE_ID.strip()
    ejs_pubkey = EMAILJS_PUBLIC_KEY.strip()
    if ejs_service and ejs_template and ejs_pubkey:
        try:
            ejs_payload = {
                "service_id": ejs_service,
                "template_id": ejs_template,
                "user_id": ejs_pubkey,
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

    # 4. Kênh FormSubmit AJAX + Form POST (Có đầy đủ Origin & Referer header)
    payload_fs = {
        "_subject": f"🚢 [Anh Minh Translate] Người dùng mới: {full_name} ({university})",
        "_template": "table",
        "_captcha": "false",
        "Ho_va_Ten": full_name,
        "Sinh_vien_nam": student_year,
        "Truong_theo_hoc": university,
        "Thoi_gian": now_str,
        "Ung_dung": "Anh Minh Translate (СПбГМТУ)",
    }
    try:
        formsubmit_ajax_url = f"https://formsubmit.co/ajax/{AUTHOR_NOTIFICATION_EMAIL}"
        req_fs = urllib.request.Request(
            formsubmit_ajax_url,
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

    try:
        formsubmit_post_url = f"https://formsubmit.co/{AUTHOR_NOTIFICATION_EMAIL}"
        form_encoded = urllib.parse.urlencode(payload_fs).encode("utf-8")
        headers_form = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": headers_json["User-Agent"],
            "Origin": "https://dich-thuat-anhminh.streamlit.app",
            "Referer": "https://dich-thuat-anhminh.streamlit.app/",
        }
        req_form = urllib.request.Request(
            formsubmit_post_url,
            data=form_encoded,
            headers=headers_form,
            method="POST",
        )
        with urllib.request.urlopen(req_form, timeout=8) as resp:
            if resp.status in (200, 201, 302):
                return True, "FormSubmit Form"
    except Exception:
        pass

    return False, "Client Browser Relay"


def trigger_client_side_email_relay(full_name: str, student_year: str, university: str) -> None:
    """
    Thực thi gửi thông báo từ trình duyệt người dùng (sau khi trang đã rerun ổn định)
    bằng cả Fetch AJAX lẫn Hidden HTML Form POST tới FormSubmit.co để đảm bảo 100% gửi đi.
    """
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
    safe_formspree = json.dumps(FORMSPREE_ENDPOINT.strip())
    safe_name_html = full_name.replace('"', "&quot;")
    safe_year_html = student_year.replace('"', "&quot;")
    safe_uni_html = university.replace('"', "&quot;")

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
        "avatar.png",
        "avatar.jpg",
        "avatar.jpeg",
        "avatar.webp",
        "minh.png",
        "minh.jpg",
        "minh.jpeg",
        "author.png",
        "author.jpg",
    ]
    base_dir = Path(__file__).parent if "__file__" in globals() else Path(".")
    for name in candidate_names:
        for folder in [base_dir, Path(".")]:
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
# 2. DỮ LIỆU TỪ ĐIỂN TIẾNG LÓNG & CHUYÊN NGÀNH CHO SINH VIÊN TẠI NGA
# ==============================================================================
RUSSIAN_SLANG_DICT: List[Dict[str, str]] = [
    {
        "word": "препод",
        "accent": "пре́под",
        "full": "преподаватель",
        "en": "lecturer / professor",
        "vi": "Giảng viên, thầy/cô giáo đại học",
        "example": "Препод сегодня добрый, всех отпустил пораньше.",
    },
    {
        "word": "курсач",
        "accent": "курса́ч",
        "full": "курсовая работа",
        "en": "term paper / course project",
        "vi": "Đồ án môn học / Tiểu luận học kỳ",
        "example": "Мне нужно сдать курсач до пятницы.",
    },
    {
        "word": "лаба",
        "accent": "ла́ба",
        "full": "лабораторная работа",
        "en": "lab work / laboratory session",
        "vi": "Bài thí nghiệm / Giờ thực hành phòng Lab",
        "example": "У нас сегодня две лабы по физике.",
    },
    {
        "word": "хвост",
        "accent": "хвост",
        "full": "академическая задолженность",
        "en": "academic debt / failed exam",
        "vi": "Nợ môn (chưa qua môn/thi trượt cần thi lại)",
        "example": "Нужно закрыть все хвосты до начала сессии.",
    },
    {
        "word": "зачетка",
        "accent": "зачётка",
        "full": "зачётная книжка",
        "en": "student record book",
        "vi": "Sổ điểm sinh viên (dùng để giảng viên ký khi thi)",
        "example": "Не забудь взять зачётку на экзамен!",
    },
    {
        "word": "автомат",
        "accent": "автома́т",
        "full": "зачёт/экзамен автоматом",
        "en": "automatic pass (without final exam)",
        "vi": "Được miễn thi (qua môn/điểm tối đa nhờ tích cực trên lớp)",
        "example": "Я ходил на все лекции и получил автомат!",
    },
    {
        "word": "пара",
        "accent": "па́ра",
        "full": "учебная пара (2 академических часа)",
        "en": "double period / 90-minute university class",
        "vi": "Ca học đại học (thường kéo dài 90 phút = 2 tiết)",
        "example": "Во сколько завтра первая пара?",
    },
    {
        "word": "общага",
        "accent": "обща́га",
        "full": "общежитие",
        "en": "dormitory / student hostel",
        "vi": "Ký túc xá (KTX) sinh viên",
        "example": "Вечером собираемся в общаге готовиться к сессии.",
    },
    {
        "word": "стипуха",
        "accent": "стипу́ха",
        "full": "стипендия",
        "en": "stipend / scholarship allowance",
        "vi": "Tiền học bổng hàng tháng",
        "example": "Ура, сегодня пришла стипуха!",
    },
    {
        "word": "окно",
        "accent": "окно́",
        "full": "свободное время между парами",
        "en": "free period / gap between classes",
        "vi": "Ca trống giữa các tiết học trong ngày",
        "example": "У нас окно между второй и четвёртой парой, пойдём в столовую.",
    },
    {
        "word": "сессия",
        "accent": "се́ссия",
        "full": "экзаменационная сессия",
        "en": "exam period / finals week",
        "vi": "Kỳ thi học kỳ (mùa thi)",
        "example": "Зимняя сессия начинается в январе.",
    },
    {
        "word": "пересдача",
        "accent": "пересда́ча",
        "full": "повторная сдача экзамена",
        "en": "retake / resit exam",
        "vi": "Thi lại",
        "example": "Комиссия назначила пересдачу на следующую неделю.",
    },
    {
        "word": "деканат",
        "accent": "декана́т",
        "full": "администрация факультета",
        "en": "dean's office",
        "vi": "Văn phòng khoa / Phòng giáo vụ khoa",
        "example": "Возьми справку в деканате.",
    },
    {
        "word": "шпора",
        "accent": "шпо́ра",
        "full": "шпаргалка",
        "en": "cheat sheet / crib note",
        "vi": "Phao thi / Tờ ghi chú nhỏ",
        "example": "Писать шпоры полезно для памяти, но доставать на экзамене опасно.",
    },
    {
        "word": "домашка",
        "accent": "дома́шка",
        "full": "домашнее задание (ДЗ)",
        "en": "homework / assignment",
        "vi": "Bài tập về nhà",
        "example": "Скинь домашку по матану, пожалуйста!",
    },
    {
        "word": "матан",
        "accent": "мата́н",
        "full": "математический анализ",
        "en": "calculus / mathematical analysis",
        "vi": "Môn Giải tích toán học",
        "example": "Завтра коллоквиум по матану.",
    },
    {
        "word": "сопромат",
        "accent": "сопрома́т",
        "full": "сопротивление материалов",
        "en": "strength of materials (mechanics)",
        "vi": "Môn Sức bền vật liệu (kỹ thuật/đóng tàu/cơ khí)",
        "example": "Сдал сопромат — можно жениться!",
    },
    {
        "word": "научник",
        "accent": "нау́чник",
        "full": "научный руководитель",
        "en": "academic advisor / thesis supervisor",
        "vi": "Giảng viên hướng dẫn khoa học / hướng dẫn đồ án",
        "example": "Мой научник одобрил тему диплома.",
    },
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
        {"ru": "шпанго́ут", "en": "hull frame / rib", "vi": "Sườn tàu"},
    ],
    "CNTT & Khoa học máy tính": [
        {"ru": "ба́за да́нных", "en": "database", "vi": "Cơ sở dữ liệu"},
        {"ru": "алгори́тм", "en": "algorithm", "vi": "Thuật toán"},
        {"ru": "иску́сственный интелле́кт", "en": "artificial intelligence", "vi": "Trí tuệ nhân tạo (AI)"},
        {"ru": "исхо́дный код", "en": "source code", "vi": "Mã nguồn"},
        {"ru": "нейро́нная сеть", "en": "neural network", "vi": "Mạng nơ-ron"},
        {"ru": "вычисли́тельная се́ть", "en": "computer network", "vi": "Mạng máy tính"},
        {"ru": "отла́дка", "en": "debugging", "vi": "Gỡ lỗi (Debug)"},
    ],
    "Kinh tế & Quản trị": [
        {"ru": "себесто́имость", "en": "cost price / production cost", "vi": "Giá thành sản xuất"},
        {"ru": "бухга́лтерский учё́т", "en": "accounting", "vi": "Kế toán"},
        {"ru": "рента́бельность", "en": "profitability", "vi": "Khả năng sinh lời / Tỷ suất lợi nhuận"},
        {"ru": "инвести́ции", "en": "investments", "vi": "Đầu tư"},
        {"ru": "спрос и предложе́ние", "en": "supply and demand", "vi": "Cung và cầu"},
    ],
    "Giao tiếp / Tin nhắn đời thường": [
        {"ru": "преподава́тель", "en": "lecturer / professor", "vi": "Giảng viên"},
        {"ru": "расписа́ние заня́тий", "en": "class schedule / timetable", "vi": "Thời khóa biểu"},
        {"ru": "консульта́ция", "en": "office hours / consultation", "vi": "Buổi giải đáp thắc mắc với giảng viên"},
        {"ru": "ста́роста гру́ппы", "en": "class monitor / group leader", "vi": "Lớp trưởng"},
        {"ru": "общежи́тие (обща́га)", "en": "student dormitory", "vi": "Ký túc xá sinh viên"},
    ],
    "Học thuật tổng hợp": [
        {"ru": "дипло́мная рабо́та", "en": "graduation thesis", "vi": "Khóa luận / Đồ án tốt nghiệp"},
        {"ru": "аннота́ция", "en": "abstract", "vi": "Tóm tắt bài báo/luận văn"},
        {"ru": "актуа́льность те́мы", "en": "relevance of the topic", "vi": "Tính cấp thiết của đề tài"},
        {"ru": "методоло́гия", "en": "methodology", "vi": "Phương pháp luận"},
        {"ru": "защи́та дипло́ма", "en": "thesis defense", "vi": "Bảo vệ đồ án tốt nghiệp"},
    ],
}


# ==============================================================================
# 3. BỘ STICKER & MINH HỌA THUYỀN 2D/3D NGHỆ THUẬT (SVG GRAPHICS)
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
<svg width="26" height="26" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; filter: drop-shadow(0 2px 4px rgba(2,132,199,0.25));">
  <path d="M24 6L38 30H24V6Z" fill="#06B6D4"/>
  <path d="M22 10L10 30H22V10Z" fill="#0284C7"/>
  <path d="M6 33H42L36 41H12L6 33Z" fill="#0369A1"/>
  <path d="M4 43C10 40 16 40 22 43C28 46 34 46 40 43" stroke="#38BDF8" stroke-width="3" stroke-linecap="round"/>
</svg>
""".strip()

STICKER_HELM_WHEEL = """
<svg width="26" height="26" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; filter: drop-shadow(0 2px 4px rgba(2,132,199,0.25));">
  <circle cx="24" cy="24" r="14" stroke="#0284C7" stroke-width="4" fill="#E0F2FE"/>
  <circle cx="24" cy="24" r="5" fill="#0369A1"/>
  <path d="M24 4V44M4 24H44M9.8 9.8L38.2 38.2M38.2 9.8L9.8 38.2" stroke="#0369A1" stroke-width="3.5" stroke-linecap="round"/>
</svg>
""".strip()

STICKER_COMPASS_3D = """
<svg width="26" height="26" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; filter: drop-shadow(0 2px 4px rgba(2,132,199,0.25));">
  <circle cx="24" cy="24" r="19" fill="#F0F9FF" stroke="#0284C7" stroke-width="3.5"/>
  <polygon points="24,7 29,24 24,21 19,24" fill="#EF4444"/>
  <polygon points="24,41 29,24 24,27 19,24" fill="#0369A1"/>
  <circle cx="24" cy="24" r="3" fill="#0F172A"/>
</svg>
""".strip()

STICKER_ANCHOR_3D = """
<svg width="26" height="26" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle; filter: drop-shadow(0 2px 4px rgba(2,132,199,0.25));">
  <circle cx="24" cy="10" r="4.5" stroke="#0284C7" stroke-width="3.5" fill="#E0F2FE"/>
  <path d="M24 15V40M15 21H33" stroke="#0369A1" stroke-width="4" stroke-linecap="round"/>
  <path d="M10 29C10 37 17 41 24 41C31 41 38 37 38 29" stroke="#0284C7" stroke-width="4" stroke-linecap="round"/>
</svg>
""".strip()


# ==============================================================================
# 4. CUSTOM CSS CHUYÊN NGHIỆP + ẨN NÚT SỬA APP/GITHUB ĐỐI VỚI NGƯỜI DÙNG THƯỜNG
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
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@500;600&display=swap');

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
                linear-gradient(to right, rgba(186, 230, 253, 0.35) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(186, 230, 253, 0.35) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
            color: #0F172A !important;
        }}

        .main .block-container {{
            padding-top: 1.5rem !important;
        }}

        .main .block-container label,
        .main .block-container p,
        .main .block-container h1,
        .main .block-container h2,
        .main .block-container h3,
        .main .block-container h4,
        .main .block-container h5,
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMarkdownContainer"] p {{
            color: #0C4A6E !important;
            font-weight: 600 !important;
        }}

        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="textarea"] textarea,
        div[data-baseweb="base-input"] textarea,
        .main input[type="text"] {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            caret-color: #0284C7 !important;
            border: 2px solid #7DD3FC !important;
            border-radius: 14px !important;
            font-size: 1.04rem !important;
            line-height: 1.65 !important;
            font-weight: 500 !important;
            padding: 14px 16px !important;
            box-shadow: inset 0 2px 6px rgba(2, 132, 199, 0.06), 0 4px 12px rgba(2, 132, 199, 0.06) !important;
        }}
        div[data-testid="stTextArea"] textarea:focus,
        div[data-baseweb="textarea"] textarea:focus {{
            border-color: #0284C7 !important;
            box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.2) !important;
            background-color: #FFFFFF !important;
        }}
        div[data-testid="stTextArea"] textarea::placeholder {{
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
            opacity: 1 !important;
        }}

        .main div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #7DD3FC !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.06) !important;
        }}
        .main div[data-baseweb="select"] span,
        .main div[data-baseweb="select"] div {{
            color: #0C4A6E !important;
        }}
        ul[data-testid="stSelectboxVirtualDropdown"],
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"] {{
            background-color: #FFFFFF !important;
            border: 1px solid #7DD3FC !important;
            border-radius: 12px !important;
        }}
        div[data-baseweb="popover"] li,
        div[data-baseweb="menu"] li {{
            color: #0F172A !important;
            font-weight: 500 !important;
        }}
        div[data-baseweb="popover"] li:hover {{
            background-color: #E0F2FE !important;
            color: #0284C7 !important;
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
            padding: 12px 20px !important;
            border: 2px solid #7DD3FC !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.07) !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] p,
        div[data-testid="stTabs"] button[data-baseweb="tab"] span,
        div[data-testid="stTabs"] button[data-baseweb="tab"] div {{
            color: #0369A1 !important;
            font-weight: 700 !important;
            font-size: 0.96rem !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            border-color: #0369A1 !important;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.28) !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p,
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] span,
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] div {{
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
            border: none !important;
        }}
        section[data-testid="stSidebar"] .stTextInput button span,
        section[data-testid="stSidebar"] .stTextInput button svg {{
            color: #0369A1 !important;
            fill: #0369A1 !important;
        }}
        section[data-testid="stSidebar"] .stTextInput input::placeholder {{
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
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
            transition: all 0.2s ease;
            text-align: center;
        }}
        .gemini-key-link-btn:hover {{
            background: linear-gradient(135deg, #06B6D4 0%, #0369A1 100%);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(6, 182, 212, 0.45);
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
            backdrop-filter: blur(8px);
        }}
        .author-avatar-img {{
            width: 68px;
            height: 68px;
            border-radius: 50%;
            object-fit: cover;
            border: 2.5px solid #38BDF8;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.45);
            background: #FFFFFF;
            flex-shrink: 0;
        }}
        .author-info-name {{
            font-size: 1.05rem;
            font-weight: 800;
            color: #FFFFFF !important;
            line-height: 1.25;
            margin-bottom: 3px;
        }}
        .author-info-role {{
            font-size: 0.78rem;
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
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.18);
        }}

        .saved-student-badge-box {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.22) 0%, rgba(3, 105, 161, 0.45) 100%);
            border: 1.5px solid #6EE7B7;
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }}

        .author-hero-box {{
            display: flex;
            align-items: center;
            gap: 14px;
            background: rgba(8, 47, 73, 0.55);
            border: 1.5px solid rgba(125, 211, 252, 0.65);
            border-radius: 18px;
            padding: 12px 16px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
            max-width: 390px;
        }}
        .author-hero-avatar {{
            width: 74px;
            height: 74px;
            border-radius: 16px;
            object-fit: cover;
            border: 2.5px solid #7DD3FC;
            background: #FFFFFF;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}

        .am-hero-banner {{
            background: linear-gradient(130deg, #082F49 0%, #0369A1 45%, #0284C7 80%, #06B6D4 100%);
            border-radius: 24px;
            padding: 22px 28px;
            color: #FFFFFF !important;
            box-shadow: 0 18px 38px rgba(3, 105, 161, 0.25);
            margin-bottom: 22px;
            position: relative;
            overflow: hidden;
            border: 2px solid rgba(125, 211, 252, 0.45);
        }}
        .am-brand-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
            position: relative;
            z-index: 2;
        }}
        .am-brand-left {{
            display: flex;
            align-items: center;
            gap: 22px;
            flex: 1;
            flex-wrap: wrap;
            min-width: 280px;
        }}
        .am-title {{
            font-size: 1.95rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            margin: 0 !important;
            line-height: 1.2 !important;
            color: #FFFFFF !important;
        }}
        .am-title span.highlight {{
            color: #7DD3FC !important;
            text-shadow: 0 2px 10px rgba(6, 182, 212, 0.4);
        }}
        .am-subtitle {{
            font-size: 0.96rem !important;
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
            font-size: 0.8rem;
            font-weight: 600;
            color: #FFFFFF !important;
            backdrop-filter: blur(4px);
        }}
        .am-ship-art {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .ocean-card {{
            background: rgba(255, 255, 255, 0.96);
            border-radius: 20px;
            padding: 22px 26px;
            border: 1.5px solid #BAE6FD;
            box-shadow: 0 10px 28px rgba(2, 132, 199, 0.09);
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }}
        .ocean-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid #E0F2FE;
            padding-bottom: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .ocean-card-title {{
            font-size: 1.12rem !important;
            font-weight: 800 !important;
            color: #0369A1 !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .ocean-pill {{
            background: linear-gradient(135deg, #E0F2FE 0%, #CFFAFE 100%);
            color: #0369A1 !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 5px 14px;
            border-radius: 999px;
            border: 1px solid #7DD3FC;
        }}
        .translation-main-text {{
            font-size: 1.14rem !important;
            line-height: 1.72 !important;
            color: #0F172A !important;
            font-weight: 600 !important;
            background: #F8FAFC;
            padding: 18px 22px;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
            border-left: 6px solid #0284C7;
            white-space: pre-wrap;
        }}

        .lang-card-header {{
            font-size: 0.96rem !important;
            font-weight: 800 !important;
            color: #0C4A6E !important;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .lang-compare-box-ru {{
            background: #FFFFFF;
            border: 1.5px solid #93C5FD;
            border-top: 5px solid #0284C7;
            border-radius: 14px;
            padding: 15px 18px;
            color: #0F172A !important;
            font-size: 1.02rem;
            font-weight: 600;
            line-height: 1.62;
            margin-bottom: 10px;
            min-height: 90px;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.06);
            white-space: pre-wrap;
        }}
        .lang-compare-box-vi {{
            background: #FFFFFF;
            border: 1.5px solid #6EE7B7;
            border-top: 5px solid #059669;
            border-radius: 14px;
            padding: 15px 18px;
            color: #064E3B !important;
            font-size: 1.02rem;
            font-weight: 600;
            line-height: 1.62;
            margin-bottom: 10px;
            min-height: 90px;
            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.06);
            white-space: pre-wrap;
        }}
        .lang-compare-box-en {{
            background: #FFFFFF;
            border: 1.5px solid #FCD34D;
            border-top: 5px solid #D97706;
            border-radius: 14px;
            padding: 15px 18px;
            color: #78350F !important;
            font-size: 1.02rem;
            font-weight: 600;
            line-height: 1.62;
            margin-bottom: 10px;
            min-height: 90px;
            box-shadow: 0 4px 12px rgba(217, 119, 6, 0.06);
            white-space: pre-wrap;
        }}

        .tone-box-formal {{
            background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
            border: 1.5px solid #7DD3FC;
            border-left: 6px solid #0369A1;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 8px;
        }}
        .tone-box-casual {{
            background: linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%);
            border: 1.5px solid #67E8F9;
            border-left: 6px solid #06B6D4;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 8px;
        }}
        .tone-title {{
            font-weight: 800;
            font-size: 0.96rem;
            color: #0C4A6E !important;
            margin-bottom: 8px;
        }}
        .tone-ru {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #0F172A !important;
            margin-bottom: 8px;
            line-height: 1.55;
        }}
        .tone-note {{
            font-size: 0.88rem;
            color: #334155 !important;
            line-height: 1.5;
        }}

        .vocab-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 0.96rem;
            border-radius: 12px;
            overflow: hidden;
        }}
        .vocab-table th {{
            background: linear-gradient(90deg, #0369A1 0%, #0284C7 100%);
            color: #FFFFFF !important;
            text-align: left;
            padding: 12px 16px;
            font-weight: 700;
        }}
        .vocab-table td {{
            padding: 12px 16px;
            border-bottom: 1px solid #E2E8F0;
            color: #0F172A !important;
            font-weight: 500;
        }}
        .vocab-table tr:nth-child(even) {{
            background-color: #F0F9FF;
        }}
        .vocab-table tr:hover {{
            background-color: #E0F2FE;
        }}

        div.stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.68rem 1.4rem !important;
            font-weight: 700 !important;
            font-size: 0.98rem !important;
            box-shadow: 0 8px 18px rgba(2, 132, 199, 0.28) !important;
        }}
        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span {{
            color: #FFFFFF !important;
        }}
        div.stButton > button[kind="secondary"] {{
            border-radius: 12px !important;
            border: 2px solid #38BDF8 !important;
            background-color: #FFFFFF !important;
            color: #0369A1 !important;
            padding: 0.55rem 1.1rem !important;
            font-weight: 700 !important;
        }}
        div.stButton > button[kind="secondary"] p,
        div.stButton > button[kind="secondary"] span {{
            color: #0369A1 !important;
        }}

        .slang-item {{
            background: #F0F9FF;
            border: 1.5px solid #BAE6FD;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 10px;
            color: #0F172A !important;
        }}
        .slang-word {{
            font-weight: 800;
            color: #0284C7 !important;
            font-size: 1.04rem;
        }}

        .nautical-divider {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 14px;
            margin: 18px 0;
            color: #0284C7;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-align: center;
        }}
        .nautical-divider::before,
        .nautical-divider::after {{
            content: "";
            flex: 1;
            height: 1.5px;
            background: linear-gradient(90deg, transparent, #7DD3FC, transparent);
        }}

        @media (max-width: 768px) {{
            .main .block-container {{
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
                padding-top: 1rem !important;
            }}
            .am-hero-banner {{
                padding: 16px 14px !important;
                border-radius: 18px !important;
            }}
            .am-title {{
                font-size: 1.45rem !important;
            }}
            .author-hero-box {{
                max-width: 100% !important;
                width: 100% !important;
                padding: 10px 12px !important;
            }}
            .am-ship-art {{
                display: none !important;
            }}
            .ocean-card {{
                padding: 15px 14px !important;
                border-radius: 16px !important;
            }}
            div[data-testid="stTabs"] button[data-baseweb="tab"] {{
                padding: 10px 12px !important;
                flex: 1 1 auto !important;
            }}
            div[data-testid="stTabs"] button[data-baseweb="tab"] p {{
                font-size: 0.84rem !important;
            }}
            .vocab-table th, .vocab-table td {{
                padding: 8px 10px !important;
                font-size: 0.85rem !important;
            }}
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
                        <h1 class="am-title">🚢 <span class="highlight">Anh Minh</span> Translate</h1>
                        <div class="am-subtitle">Hệ sinh thái Dịch thuật & Học thuật Siêu tốc cho Sinh viên Việt tại Nga</div>
                        <div class="am-badges">
                            <span class="am-badge">⚓ Kỹ thuật & Đóng tàu</span>
                            <span class="am-badge">💬 Slang Sinh viên Telegram/VK</span>
                            <span class="am-badge">🎙️ Hybrid Voice AI (Claude/ChatGPT VAD + DSP x12)</span>
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
# 5. HỆ THỐNG DỊCH ĐA LUỒNG 5 CỔNG (CHỐNG CHẶN IP STREAMLIT CLOUD + MỌI GEMINI KEY)
# ==============================================================================
def detect_slang_in_text(text: str) -> List[Dict[str, str]]:
    if not text:
        return []
    text_lower = text.lower()
    detected = []
    for item in RUSSIAN_SLANG_DICT:
        base_stem = item["word"][:-1] if len(item["word"]) > 4 else item["word"]
        pattern = rf"\b{re.escape(base_stem)}[а-яё]*\b"
        if re.search(pattern, text_lower):
            detected.append(item)
    return detected


@st.cache_data(ttl=3600, show_spinner=False)
def generate_tts_audio(text: str, lang_code: str) -> Optional[bytes]:
    cleaned_text = text.strip()
    if not cleaned_text or gTTS is None:
        return None
    try:
        tts = gTTS(text=cleaned_text[:600], lang=lang_code, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp.read()
    except Exception:
        return None


def _try_multi_endpoint_translate(cleaned: str, src: str, tgt: str) -> Optional[str]:
    headers_form = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    post_body = urllib.parse.urlencode({"sl": src, "tl": tgt, "q": cleaned}).encode("utf-8")

    # Cổng 1: Google Translate GTX POST
    try:
        url1 = "https://translate.googleapis.com/translate_a/single?client=gtx&dt=t"
        req1 = urllib.request.Request(url1, data=post_body, headers=headers_form, method="POST")
        with urllib.request.urlopen(req1, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                chunks = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
                if chunks:
                    return "".join(chunks)
    except Exception:
        pass

    # Cổng 2: Google Translate Android App Endpoint
    try:
        url2 = "https://translate.google.com/translate_a/single?client=at&dt=t&dj=1"
        req2 = urllib.request.Request(url2, data=post_body, headers=headers_form, method="POST")
        with urllib.request.urlopen(req2, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sentences = data.get("sentences", [])
            if sentences:
                chunks = [s.get("trans", "") for s in sentences if s.get("trans")]
                if chunks:
                    return "".join(chunks)
    except Exception:
        pass

    # Cổng 3: Chrome Extension Dictionary Endpoint
    try:
        url3 = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex"
        req3 = urllib.request.Request(url3, data=post_body, headers=headers_form, method="POST")
        with urllib.request.urlopen(req3, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], str):
                    return data[0]
                if isinstance(data[0], list):
                    return "".join(str(x[0]) for x in data if isinstance(x, list) and x)
            elif isinstance(data, dict) and "sentences" in data:
                return "".join(s.get("trans", "") for s in data["sentences"] if s.get("trans"))
    except Exception:
        pass

    # Cổng 4: Google Translate GET
    try:
        encoded_q = urllib.parse.quote(cleaned)
        url4 = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={tgt}&dt=t&q={encoded_q}"
        req4 = urllib.request.Request(url4, headers={"User-Agent": headers_form["User-Agent"]})
        with urllib.request.urlopen(req4, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                chunks = [chunk[0] for chunk in data[0] if chunk and chunk[0]]
                if chunks:
                    return "".join(chunks)
    except Exception:
        pass

    # Cổng 5: MyMemory API dự phòng
    try:
        src_mm = "ru" if src == "auto" else src
        mm_url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(cleaned[:480])}&langpair={src_mm}|{tgt}"
        req5 = urllib.request.Request(mm_url, headers={"User-Agent": headers_form["User-Agent"]})
        with urllib.request.urlopen(req5, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            trans_text = data.get("responseData", {}).get("translatedText", "")
            if trans_text and "MYMEMORY WARNING" not in trans_text.upper():
                return trans_text
    except Exception:
        pass

    # Cổng 6: deep-translator
    if GoogleTranslator is not None:
        try:
            res = GoogleTranslator(source=src, target=tgt).translate(cleaned)
            if res and "too many requests" not in res.lower():
                return res
        except Exception:
            pass

    return None


def fast_free_translate(text: str, src: str, tgt: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if src == tgt:
        return cleaned

    if "translation_mem_cache" not in st.session_state:
        st.session_state["translation_mem_cache"] = {}

    cache_key = f"{src}::{tgt}::{cleaned}"
    cached_val = st.session_state["translation_mem_cache"].get(cache_key)
    if cached_val:
        return cached_val

    translated = _try_multi_endpoint_translate(cleaned, src, tgt)
    if translated:
        st.session_state["translation_mem_cache"][cache_key] = translated
        return translated

    return "⚠️ Máy chủ dịch miễn phí đang bận trong giây lát. Bạn hãy bấm lại nút «🚀 Dịch & Phân Tích Ngay» hoặc dán bất kỳ Gemini API Key nào vào cột trái nhé!"


def discover_available_gemini_models(api_key: str) -> List[str]:
    clean_k = clean_api_key(api_key)
    preferred_order = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-pro",
    ]
    if not clean_k:
        return preferred_order

    cache_name = f"gemini_models_{clean_k[:8]}_{len(clean_k)}"
    if cache_name in st.session_state:
        return st.session_state[cache_name]

    discovered: List[str] = []
    for api_ver in ["v1beta", "v1"]:
        try:
            url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={urllib.parse.quote(clean_k)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        short_name = m.get("name", "").replace("models/", "")
                        if "gemini" in short_name and "vision" not in short_name and "embedding" not in short_name:
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


def call_gemini_rest_api(api_key: str, system_prompt: str, user_text: str) -> Tuple[Optional[str], Optional[str]]:
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return None, "Empty API Key"

    models_to_try = discover_available_gemini_models(clean_k)
    last_error = ""

    combined_prompt = f"{system_prompt}\n\n---\nVăn bản cần xử lý:\n{user_text}"

    for model_name in models_to_try[:6]:
        url_v1beta = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
        payload_json_mode = {
            "contents": [{"parts": [{"text": combined_prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }
        try:
            req = urllib.request.Request(
                url_v1beta,
                data=json.dumps(payload_json_mode).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"], None
        except urllib.error.HTTPError as http_err:
            err_body = ""
            try:
                err_body = http_err.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            last_error = f"HTTP {http_err.code}: {err_body[:200]}"
            if http_err.code == 400 and "API_KEY_INVALID" not in err_body:
                try:
                    payload_plain = {
                        "contents": [{"parts": [{"text": combined_prompt}]}],
                        "generationConfig": {"temperature": 0.2},
                    }
                    req2 = urllib.request.Request(
                        url_v1beta,
                        data=json.dumps(payload_plain).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req2, timeout=12) as resp2:
                        resp_data2 = json.loads(resp2.read().decode("utf-8"))
                        candidates2 = resp_data2.get("candidates", [])
                        if candidates2:
                            parts2 = candidates2[0].get("content", {}).get("parts", [])
                            if parts2 and "text" in parts2[0]:
                                return parts2[0]["text"], None
                except Exception:
                    pass
            if "API_KEY_INVALID" in err_body:
                return None, "Mã Gemini API Key không chính xác. Vui lòng kiểm tra lại!"
        except Exception as exc:
            last_error = str(exc)

    return None, last_error


def call_gemini_smart_translate(
    api_key: str,
    source_text: str,
    direction: str,
    domain: str,
) -> Tuple[Optional[Dict], Optional[str]]:
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return None, "Empty Key"

    system_prompt = f"""
Bạn là chuyên gia dịch thuật cao cấp Nga - Việt - Anh (RU - VI - EN) và cố vấn học thuật cho sinh viên Việt Nam tại Nga.
Chuyên ngành ưu tiên: "{domain}". Chiều dịch: "{direction}".
CHỈ TRẢ VỀ đúng 1 đối tượng JSON hợp lệ (không thêm markdown) theo cấu trúc sau:
{{
  "main_translation": "Bản dịch tự nhiên nhất theo chiều dịch đã chọn",
  "ru_version": "Bản tiếng Nga tương ứng",
  "vi_version": "Bản tiếng Việt chuẩn thuật ngữ đại học",
  "en_version": "Bản tiếng Anh đối chiếu",
  "slang_explanations": [
    {{"term": "Từ lóng/viết tắt", "full_form": "Dạng đầy đủ tiếng Nga", "meaning_vi": "Giải nghĩa tiếng Việt"}}
  ],
  "vocabulary_table": [
    {{"ru_accent": "Từ tiếng Nga có dấu trọng âm u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu tiếng Nga lịch sự ngôi «Вы»",
    "formal_vy_vi_note": "Giải thích câu trang trọng",
    "casual_ty": "Câu tiếng Nga thân mật ngôi «Ты»",
    "casual_ty_vi_note": "Giải thích câu thân mật"
  }},
  "study_tip": "1 mẹo ngắn gọn về ngữ pháp/thuật ngữ liên quan."
}}
"""

    raw_text, err = call_gemini_rest_api(clean_k, system_prompt, source_text)
    if not raw_text:
        return None, err

    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.IGNORECASE)
        json_match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)
        parsed = json.loads(cleaned)
        return parsed, None
    except Exception as exc:
        return None, str(exc)


def fallback_smart_translate(
    source_text: str,
    direction: str,
    domain: str,
) -> Dict:
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
    }
    for slang_form, full_replacement in slang_inflections.items():
        expanded_ru_text = re.sub(
            rf"\b{re.escape(slang_form)}\b",
            full_replacement,
            expanded_ru_text,
            flags=re.IGNORECASE,
        )

    with ThreadPoolExecutor(max_workers=3) as executor:
        if direction == "🇷🇺 Tiếng Nga ➔ 🇻🇳 Tiếng Việt":
            fut_vi = executor.submit(fast_free_translate, expanded_ru_text, "ru", "vi")
            fut_en = executor.submit(fast_free_translate, expanded_ru_text, "ru", "en")
            vi_ver = fut_vi.result()
            en_ver = fut_en.result()
            ru_ver = source_text
            main_trans = vi_ver
        elif direction == "🇻🇳 Tiếng Việt ➔ 🇷🇺 Tiếng Nga":
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

    if direction == "🇷🇺 Tiếng Nga ➔ 🇻🇳 Tiếng Việt":
        formal_vy_full = "Здравствуйте! Спасибо за важную информацию, мы обязательно примем это к сведению и всё выполним по правилам."
        formal_note = "Mẫu câu trả lời lễ phép (Ngôi «Вы» — Gửi Giảng viên / Phòng Visa / Деканат): «Xin chào! Cảm ơn vì thông tin quan trọng, chúng em nhất định sẽ lưu ý và thực hiện đúng quy định ạ.»"
        casual_ty_full = "Привет! Понял, спасибо за инфу! Обязательно передам ребятам, всё сделаем как надо."
        casual_note = "Mẫu câu trả lời thân mật (Ngôi «Ты» — Nhắn bạn học / nhóm chat Telegram): «Chào cậu! Mình hiểu rồi, cảm ơn vì thông tin nhé! Mình sẽ nhắn lại với mọi người, tụi mình sẽ làm đầy đủ.»"
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
        if not casual_ty.lower().startswith(("привет", "слушай", "салют")):
            casual_ty_full = f"Привет! {casual_ty}"
        else:
            casual_ty_full = casual_ty
        casual_note = "Dùng khi nhắn nhanh cho bạn cùng lớp (Одногруппники) hoặc bạn cùng KTX (Общага)."

    vocab_list = []
    for s in detected_slang:
        vocab_list.append(
            {
                "ru_accent": f"{s['accent']} ({s['full']})",
                "en": s["en"],
                "vi": s["vi"],
            }
        )

    domain_terms = DOMAIN_GLOSSARY.get(domain, DOMAIN_GLOSSARY["Học thuật tổng hợp"])
    for term in domain_terms[:5]:
        vocab_list.append(
            {
                "ru_accent": term["ru"],
                "en": term["en"],
                "vi": term["vi"],
            }
        )

    slang_explanations = [
        {
            "term": s["word"],
            "full_form": s["full"],
            "meaning_vi": f"{s['vi']} — Ví dụ: «{s['example']}»",
        }
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
        "study_tip": (
            "Khi làm việc với Phòng Quốc tế (Международный отдел) về gia hạn thị thực (продление визы) hoặc thực tập (практика), "
            "luôn sử dụng ngôi «Вы» trang trọng và chuẩn bị hồ sơ trước ít nhất 30–45 ngày làm việc."
        ),
        "is_fallback": True,
    }


# ==============================================================================
# 6. CÔNG NGHỆ THU ÂM GIẢNG ĐƯỜNG HYBRID VOICE AI (MÔ HÌNH CLAUDE & CHATGPT WHISPER)
# ==============================================================================
def build_realtime_lecture_component(gemini_api_key: str = "", selected_domain: str = "") -> str:
    safe_domain = json.dumps(selected_domain)
    safe_gemini_key = json.dumps(clean_api_key(gemini_api_key))

    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
            * {{
                box-sizing: border-box;
                font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, sans-serif;
            }}
            body {{
                margin: 0;
                padding: 4px;
                background: transparent;
                color: #0F172A;
            }}
            .rt-container {{
                background: linear-gradient(180deg, #FFFFFF 0%, #F0F9FF 100%);
                border: 2px solid #7DD3FC;
                border-radius: 20px;
                padding: 16px 18px;
                box-shadow: 0 12px 30px rgba(2, 132, 199, 0.12);
                position: relative;
            }}
            .rt-top-bar {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                padding-bottom: 10px;
                border-bottom: 2px solid #E0F2FE;
            }}
            .rt-controls {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                gap: 8px;
            }}
            .rt-select {{
                padding: 8px 11px;
                border-radius: 12px;
                border: 1.5px solid #38BDF8;
                background: #FFFFFF;
                color: #0369A1;
                font-weight: 700;
                font-size: 0.84rem;
                outline: none;
                cursor: pointer;
            }}
            .rt-btn {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 9px 14px;
                border-radius: 12px;
                font-weight: 700;
                font-size: 0.85rem;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            .btn-start {{
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                color: #FFFFFF;
                box-shadow: 0 6px 16px rgba(2, 132, 199, 0.3);
            }}
            .btn-start:hover:not(:disabled) {{
                transform: translateY(-1px);
                background: linear-gradient(135deg, #0369A1 0%, #075985 100%);
            }}
            .btn-flush {{
                background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%);
                color: #FFFFFF;
                border: 1.5px solid #38BDF8;
                box-shadow: 0 4px 12px rgba(2, 132, 199, 0.25);
            }}
            .btn-flush:hover:not(:disabled) {{
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                transform: translateY(-1px);
            }}
            .btn-pause {{
                background: #FEF3C7;
                color: #B45309;
                border: 1px solid #F59E0B;
            }}
            .btn-clear {{
                background: #FEE2E2;
                color: #B91C1C;
                border: 1px solid #FCA5A5;
            }}
            .btn-download {{
                background: linear-gradient(135deg, #06B6D4 0%, #0284C7 100%);
                color: #FFFFFF;
                box-shadow: 0 4px 12px rgba(6, 182, 212, 0.28);
            }}
            .rt-btn:disabled {{
                opacity: 0.45;
                cursor: not-allowed;
            }}
            .sensitivity-bar {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                background: #F0F9FF;
                border: 1.5px solid #BAE6FD;
                border-radius: 14px;
                padding: 9px 14px;
                margin-top: 10px;
                font-size: 0.82rem;
                color: #0C4A6E;
                font-weight: 600;
            }}
            .sens-group {{
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
            }}
            .sens-slider {{
                width: 120px;
                accent-color: #0284C7;
                cursor: pointer;
            }}
            .sens-pill {{
                background: #0284C7;
                color: #FFFFFF;
                font-weight: 800;
                padding: 3px 9px;
                border-radius: 999px;
                font-size: 0.76rem;
            }}
            .level-meter-wrap {{
                display: flex;
                align-items: center;
                gap: 8px;
                min-width: 185px;
            }}
            .level-bar-bg {{
                flex: 1;
                height: 10px;
                background: #CBD5E1;
                border-radius: 999px;
                overflow: hidden;
                position: relative;
            }}
            .level-bar-fill {{
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #22C55E 0%, #06B6D4 60%, #F59E0B 90%, #EF4444 100%);
                border-radius: 999px;
                transition: width 0.08s ease;
            }}
            .rt-visualizer-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                background: #082F49;
                border-radius: 16px;
                padding: 11px 16px;
                margin-top: 10px;
                color: #E0F2FE;
                border: 1px solid #0284C7;
                flex-wrap: wrap;
            }}
            .status-indicator {{
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.86rem;
                font-weight: 600;
                flex: 1;
                min-width: 220px;
            }}
            .dsp-badge {{
                background: rgba(34, 197, 94, 0.2);
                border: 1px solid #4ADE80;
                color: #86EFAC;
                font-size: 0.74rem;
                font-weight: 700;
                padding: 4px 10px;
                border-radius: 999px;
                white-space: nowrap;
            }}
            .pulse-dot {{
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #94A3B8;
                flex-shrink: 0;
            }}
            .pulse-dot.active {{
                background: #22C55E;
                box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7);
                animation: pulseGreen 1.2s infinite;
            }}
            .pulse-dot.speaking {{
                background: #38BDF8;
                box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.85);
                animation: pulseBlue 0.7s infinite;
            }}
            @keyframes pulseGreen {{
                0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }}
                70% {{ box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
            }}
            @keyframes pulseBlue {{
                0% {{ box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.85); transform: scale(1.08); }}
                70% {{ box-shadow: 0 0 0 12px rgba(56, 189, 248, 0); transform: scale(1); }}
                100% {{ box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }}
            }}
            #waveCanvas {{
                width: 185px;
                height: 36px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.06);
                flex-shrink: 0;
            }}
            .interim-box {{
                margin-top: 10px;
                background: #E0F2FE;
                border: 2px solid #0284C7;
                border-radius: 14px;
                padding: 12px 16px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                transition: all 0.2s ease;
            }}
            .interim-box.voice-detected {{
                background: #ECFEFF;
                border-color: #06B6D4;
                box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.22);
            }}
            .interim-top {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .interim-left {{
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
                min-width: 220px;
            }}
            .interim-label {{
                background: #0284C7;
                color: #FFFFFF;
                font-size: 0.72rem;
                font-weight: 800;
                padding: 4px 10px;
                border-radius: 999px;
                white-space: nowrap;
            }}
            .vad-live-pill {{
                font-size: 0.73rem;
                font-weight: 700;
                padding: 3px 9px;
                border-radius: 999px;
                background: #DCFCE7;
                color: #166534;
                border: 1px solid #86EFAC;
                display: none;
                white-space: nowrap;
            }}
            .interim-text {{
                color: #0C4A6E;
                font-size: 1.06rem;
                font-weight: 700;
                word-break: break-word;
                line-height: 1.48;
            }}
            .manual-commit-row {{
                display: flex;
                gap: 8px;
                margin-top: 2px;
            }}
            .manual-input {{
                flex: 1;
                padding: 8px 12px;
                border-radius: 10px;
                border: 1.5px solid #7DD3FC;
                font-size: 0.88rem;
                color: #0F172A;
                background: #FFFFFF;
                outline: none;
                font-weight: 600;
            }}
            .manual-input:focus {{
                border-color: #0284C7;
            }}
            .stream-wrapper {{
                position: relative;
                margin-top: 10px;
            }}
            .scroll-status-bar {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 6px 12px;
                background: #F1F5F9;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-radius: 14px 14px 0 0;
                font-size: 0.78rem;
                font-weight: 700;
                color: #334155;
            }}
            .scroll-lock-badge {{
                padding: 2px 10px;
                border-radius: 999px;
                font-size: 0.74rem;
                font-weight: 700;
            }}
            .scroll-lock-badge.auto {{
                background: #DCFCE7;
                color: #166534;
                border: 1px solid #86EFAC;
            }}
            .scroll-lock-badge.locked {{
                background: #FEF3C7;
                color: #92400E;
                border: 1px solid #FDE68A;
            }}
            .subtitle-stream {{
                height: 330px;
                overflow-y: auto;
                background: #FFFFFF;
                border: 1.5px solid #BAE6FD;
                border-radius: 0 0 16px 16px;
                padding: 14px;
                scroll-behavior: smooth;
            }}
            .jump-bottom-btn {{
                position: absolute;
                bottom: 16px;
                right: 24px;
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                color: #FFFFFF;
                border: 2px solid #BAE6FD;
                border-radius: 999px;
                padding: 8px 16px;
                font-size: 0.82rem;
                font-weight: 800;
                cursor: pointer;
                box-shadow: 0 8px 20px rgba(2, 132, 199, 0.4);
                display: none;
                align-items: center;
                gap: 6px;
                z-index: 20;
                transition: transform 0.2s ease;
            }}
            .jump-bottom-btn:hover {{
                transform: translateY(-2px);
            }}
            .sub-item {{
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-left: 5px solid #0284C7;
                border-radius: 12px;
                padding: 12px 15px;
                margin-bottom: 12px;
                animation: fadeInCard 0.22s ease-out;
            }}
            @keyframes fadeInCard {{
                from {{ opacity: 0; transform: translateY(4px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .sub-meta {{
                display: flex;
                justify-content: space-between;
                font-size: 0.74rem;
                color: #475569;
                margin-bottom: 5px;
                font-weight: 600;
                flex-wrap: wrap;
                gap: 4px;
            }}
            .sub-source {{
                font-size: 1.02rem;
                font-weight: 600;
                color: #0F172A;
                margin-bottom: 7px;
                line-height: 1.52;
            }}
            .sub-target {{
                font-size: 1.04rem;
                font-weight: 700;
                color: #0369A1;
                background: #E0F2FE;
                padding: 9px 13px;
                border-radius: 10px;
                line-height: 1.55;
                border: 1px solid #BAE6FD;
            }}
            .empty-hint {{
                text-align: center;
                color: #475569;
                padding: 55px 16px;
                font-size: 0.92rem;
                line-height: 1.65;
            }}
        </style>
    </head>
    <body>
        <div class="rt-container">
            <div class="rt-top-bar">
                <div class="rt-controls">
                    <label style="font-weight:700; color:#0369A1; font-size:0.85rem;">Nghe:</label>
                    <select id="sourceLang" class="rt-select">
                        <option value="ru-RU" selected>🇷🇺 Tiếng Nga (Giảng đường)</option>
                        <option value="vi-VN">🇻🇳 Tiếng Việt (Giao tiếp / Thử mic)</option>
                        <option value="en-US">🇬🇧 Tiếng Anh (Bài giảng Quốc tế)</option>
                    </select>

                    <label style="font-weight:700; color:#0369A1; font-size:0.85rem;">➔ Dịch sang:</label>
                    <select id="targetLang" class="rt-select">
                        <option value="vi" selected>🇻🇳 Tiếng Việt</option>
                        <option value="ru">🇷🇺 Tiếng Nga</option>
                        <option value="en">🇬🇧 Tiếng Anh</option>
                    </select>
                </div>

                <div class="rt-controls">
                    <button id="btnStart" class="rt-btn btn-start" onclick="startRecognition()">
                        🎙️ Bắt đầu thu âm
                    </button>
                    <button id="btnFlush" class="rt-btn btn-flush" onclick="forceCommitInterim()" title="Ngắt câu và dịch ngay lập tức (Phím tắt: Enter)">
                        ➕ Ngắt câu & Dịch ngay
                    </button>
                    <button id="btnPause" class="rt-btn btn-pause" onclick="stopRecognition()" disabled>
                        ⏸️ Tạm dừng
                    </button>
                    <button id="btnClear" class="rt-btn btn-clear" onclick="clearTranscript()">
                        🗑️ Xóa lịch sử
                    </button>
                    <button id="btnDownload" class="rt-btn btn-download" onclick="downloadTranscript()">
                        📥 Tải bản ghi (.txt)
                    </button>
                </div>
            </div>

            <!-- THANH ĐỘ NHẠY MIC & CHẾ ĐỘ THU ÂM KHÔNG XUNG ĐỘT -->
            <div class="sensitivity-bar">
                <div class="sens-group">
                    <span>🎙️ <b>Chế độ thu:</b></span>
                    <select id="captureModeSelect" class="rt-select" style="padding:5px 9px; font-size:0.8rem;" onchange="onCaptureModeChange()">
                        <option value="webspeech" selected>⚡ Trực tiếp (Hiện chữ tức thì từng từ)</option>
                        <option value="aidsp">🧠 AI Audio DSP (Cắt câu 4s bằng Gemini/Whisper)</option>
                    </select>
                </div>

                <div class="sens-group">
                    <span>🎚️ <b>Độ nhạy Mic:</b></span>
                    <input
                        type="range"
                        id="micGainSlider"
                        class="sens-slider"
                        min="1"
                        max="12"
                        step="0.5"
                        value="7.5"
                        oninput="updateMicSensitivity(this.value)"
                    />
                    <span id="gainValueBadge" class="sens-pill">x7.5 (Siêu nhạy)</span>
                </div>

                <div class="level-meter-wrap">
                    <span>🔊 Tín hiệu:</span>
                    <div class="level-bar-bg">
                        <div id="levelBarFill" class="level-bar-fill"></div>
                    </div>
                    <span id="levelPctText" style="min-width:36px; text-align:right; font-weight:800; color:#0284C7;">0%</span>
                </div>
            </div>

            <div class="rt-visualizer-row">
                <div class="status-indicator">
                    <div id="statusDot" class="pulse-dot"></div>
                    <span id="statusText">Sẵn sàng — Hãy kiểm tra ngôn ngữ mục «Nghe» (🇷🇺 Tiếng Nga hoặc 🇻🇳 Tiếng Việt) rồi nhấn «🎙️ Bắt đầu thu âm».</span>
                </div>
                <span id="engineBadge" class="dsp-badge">🔥 Live Speech Stream (Không xung đột Mic)</span>
                <canvas id="waveCanvas" width="185" height="36"></canvas>
            </div>

            <div id="interimBox" class="interim-box">
                <div class="interim-top">
                    <div class="interim-left">
                        <span class="interim-label">🎙️ CÂU ĐANG THU</span>
                        <span id="vadLivePill" class="vad-live-pill">🟢 Đang thu giọng nói...</span>
                        <span id="interimText" class="interim-text">Nhấn "🎙️ Bắt đầu thu âm" rồi nói vào Mic — Chữ đang nói sẽ hiện trực tiếp tại đây theo thời gian thực...</span>
                    </div>
                </div>
                <div class="manual-commit-row">
                    <input
                        type="text"
                        id="manualSentenceInput"
                        class="manual-input"
                        placeholder="✍️ Câu đang thu sẽ đồng bộ trực tiếp vào đây (hoặc gõ/chỉnh sửa rồi nhấn Enter / «➕ Ngắt câu & Dịch ngay»)..."
                        onkeydown="if(event.key === 'Enter') {{ event.preventDefault(); forceCommitInterim(); }}"
                    />
                </div>
            </div>

            <div class="stream-wrapper">
                <div class="scroll-status-bar">
                    <span>📜 Lịch sử Bài giảng (Tự động liên kết ngữ cảnh các câu trước để dịch chuẩn xác)</span>
                    <span id="scrollBadge" class="scroll-lock-badge auto">🟢 Tự động cuộn theo câu mới</span>
                </div>
                <div id="subtitleStream" class="subtitle-stream">
                    <div id="emptyHint" class="empty-hint">
                        🚢 <b>Lịch sử Thu âm & Dịch thuật theo Ngữ cảnh (Mô hình Claude & ChatGPT Voice)</b><br/>
                        • <b>Lưu ý quan trọng khi thử Mic:</b> Nếu bạn nói <b>Tiếng Việt</b> để thử mic, hãy chọn mục <b>Nghe: 🇻🇳 Tiếng Việt</b> ở góc trái phía trên.<br/>
                        • <b>Không bị nhảy trang:</b> Khi bạn lướt lên để đọc lại các câu phía trên, màn hình sẽ <b>tự động khóa vị trí</b> để bạn đọc thoải mái!
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
                    window.frameElement.setAttribute("allow", "microphone *; autoplay *; clipboard-write *; display-capture *");
                }}
            }} catch (e) {{}}

            const SELECTED_DOMAIN = {safe_domain};
            const GEMINI_API_KEY = {safe_gemini_key};

            const SLANG_MAP = {{
                "препод": "преподаватель",
                "курсач": "курсовая работа",
                "лаба": "лабораторная работа",
                "хвост": "академическая задолженность",
                "зачетка": "зачётная книжка",
                "зачётка": "зачётная книжка",
                "автомат": "экзамен автоматом",
                "общага": "общежитие",
                "стипуха": "стипендия",
                "сопромат": "сопротивление материалов",
                "матан": "математический анализ"
            }};

            const DEFAULT_PLACEHOLDERS = [
                "Nhấn \\"🎙️ Bắt đầu thu âm\\" rồi nói vào Mic — Chữ đang nói sẽ hiện trực tiếp tại đây theo thời gian thực...",
                "🎙️ Mic đã bật — Hãy nói bình thường, từng từ sẽ hiện trực tiếp tại đây...",
                "...",
                "Đã chốt câu! Đang lắng nghe câu tiếp theo..."
            ];

            let recognition = null;
            let isListening = false;
            let lectureHistory = [];
            let currentMicGain = 7.5;

            let committedResultIndex = 0;
            let currentActiveSentence = "";
            let latestResultsLength = 0;
            let lastCommittedNormalized = "";
            let lastCommitTimestamp = 0;
            let sentenceSilenceTimer = null;
            let noResultWatchdogTimer = null;
            let lastSpeechActivity = 0;
            let lastWebSpeechResultAt = 0;
            let waveAnimId = null;

            let audioCtx = null;
            let micStream = null;
            let analyserNode = null;
            let gainNode = null;
            let scriptProcessor = null;
            let pcmRingBuffer = [];
            let vadSpeechActive = false;
            let vadSpeechStartTime = 0;
            let vadLastVoiceTime = 0;
            let isTranscribingChunk = false;
            let currentRmsLevel = 0;
            let noiseFloorRms = 0.008;

            let userScrolledUp = false;
            let unreadNewCount = 0;

            const SENTENCE_PAUSE_MS = 1650;
            const PUNCTUATION_PAUSE_MS = 550;

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

            function updateMicSensitivity(val) {{
                currentMicGain = parseFloat(val) || 7.5;
                let label = "Chuẩn";
                if (currentMicGain >= 9.0) label = "Cực đại (Cuối phòng)";
                else if (currentMicGain >= 6.0) label = "Siêu nhạy";
                else if (currentMicGain >= 3.5) label = "Giảng đường";
                gainValueBadge.innerText = `x${{currentMicGain.toFixed(1)}} (${{label}})`;
                if (gainNode && audioCtx) {{
                    gainNode.gain.setTargetAtTime(Math.min(4.0, currentMicGain * 0.45), audioCtx.currentTime, 0.03);
                }}
            }}

            function onCaptureModeChange() {{
                const mode = captureModeSelect ? captureModeSelect.value : "webspeech";
                if (mode === "webspeech") {{
                    engineBadge.innerText = "🔥 Live Speech Stream (Không xung đột Mic)";
                }} else {{
                    engineBadge.innerText = "🧠 AI Audio DSP (Gemini/Whisper 16kHz)";
                }}
                if (isListening) {{
                    stopRecognition();
                    setTimeout(() => startRecognition(), 180);
                }}
            }}

            manualSentenceInput.addEventListener("input", () => {{
                const val = manualSentenceInput.value;
                currentActiveSentence = val;
                if (val.trim().length > 0) {{
                    interimText.innerText = val;
                }}
            }});

            subtitleStream.addEventListener("scroll", () => {{
                const distanceFromBottom = subtitleStream.scrollHeight - subtitleStream.scrollTop - subtitleStream.clientHeight;
                if (distanceFromBottom > 55) {{
                    if (!userScrolledUp) {{
                        userScrolledUp = true;
                        scrollBadge.className = "scroll-lock-badge locked";
                        scrollBadge.innerText = "🔒 Đang xem lịch sử (Đã khóa tự động nhảy dòng)";
                        jumpBottomBtn.style.display = "inline-flex";
                    }}
                }} else {{
                    if (userScrolledUp) {{
                        userScrolledUp = false;
                        unreadNewCount = 0;
                        unreadCountBadge.innerText = "";
                        scrollBadge.className = "scroll-lock-badge auto";
                        scrollBadge.innerText = "🟢 Tự động cuộn theo câu mới";
                        jumpBottomBtn.style.display = "none";
                    }}
                }}
            }});

            function resumeAutoScroll() {{
                userScrolledUp = false;
                unreadNewCount = 0;
                unreadCountBadge.innerText = "";
                subtitleStream.scrollTop = subtitleStream.scrollHeight;
                scrollBadge.className = "scroll-lock-badge auto";
                scrollBadge.innerText = "🟢 Tự động cuộn theo câu mới";
                jumpBottomBtn.style.display = "none";
            }}

            function smartScrollToBottomIfAllowed() {{
                if (!userScrolledUp) {{
                    subtitleStream.scrollTop = subtitleStream.scrollHeight;
                }} else {{
                    unreadNewCount += 1;
                    unreadCountBadge.innerText = `(${{unreadNewCount}} câu mới)`;
                    jumpBottomBtn.style.display = "inline-flex";
                }}
            }}

            function normalizeForComparison(str) {{
                return (str || "")
                    .toLowerCase()
                    .replace(/[.,?!…;:"'«»()\\-]/g, " ")
                    .replace(/\\s+/g, " ")
                    .trim();
            }}

            function smartMergeSegments(prevText, nextText) {{
                const a = (prevText || "").replace(/\\s+/g, " ").trim();
                const b = (nextText || "").replace(/\\s+/g, " ").trim();
                if (!a) return b;
                if (!b) return a;

                const normA = normalizeForComparison(a);
                const normB = normalizeForComparison(b);

                if (!normA) return b;
                if (!normB) return a;
                if (normA === normB) return b;
                if (normB.startsWith(normA)) return b;
                if (normA.endsWith(normB) || normA.includes(normB)) return a;

                const wordsA = a.split(" ");
                const wordsB = b.split(" ");
                const normWordsA = wordsA.map(w => normalizeForComparison(w));
                const normWordsB = wordsB.map(w => normalizeForComparison(w));

                const maxOverlap = Math.min(wordsA.length, wordsB.length);
                for (let k = maxOverlap; k >= 1; k--) {{
                    let match = true;
                    for (let j = 0; j < k; j++) {{
                        if (normWordsA[wordsA.length - k + j] !== normWordsB[j]) {{
                            match = false;
                            break;
                        }}
                    }}
                    if (match) {{
                        return wordsA.concat(wordsB.slice(k)).join(" ");
                    }}
                }}

                return a + " " + b;
            }}

            function collapseImmediateRepetitions(text) {{
                let cleaned = (text || "").replace(/\\s+/g, " ").trim();
                if (!cleaned) return "";

                const words = cleaned.split(" ");
                if (words.length < 2) return cleaned;

                let resultWords = [];
                let i = 0;
                while (i < words.length) {{
                    resultWords.push(words[i]);
                    i++;
                    const maxPhraseLen = Math.floor(resultWords.length / 2);
                    for (let len = maxPhraseLen; len >= 1; len--) {{
                        let isRepeat = true;
                        for (let m = 0; m < len; m++) {{
                            const w1 = normalizeForComparison(resultWords[resultWords.length - 2 * len + m]);
                            const w2 = normalizeForComparison(resultWords[resultWords.length - len + m]);
                            if (!w1 || w1 !== w2) {{
                                isRepeat = false;
                                break;
                            }}
                        }}
                        if (isRepeat && (len >= 2 || normalizeForComparison(resultWords[resultWords.length - 1]).length >= 4)) {{
                            resultWords.splice(resultWords.length - len, len);
                            break;
                        }}
                    }}
                }}
                return resultWords.join(" ");
            }}

            function encodeAmplifiedWavFromSamples(floatSamples, inputSampleRate) {{
                if (!floatSamples || floatSamples.length === 0) return null;
                const targetRate = 16000;
                const ratio = inputSampleRate / targetRate;
                const outLength = Math.max(1, Math.floor(floatSamples.length / ratio));
                const resampled = new Float32Array(outLength);

                for (let i = 0; i < outLength; i++) {{
                    const srcIdx = Math.min(floatSamples.length - 1, Math.floor(i * ratio));
                    resampled[i] = floatSamples[srcIdx];
                }}

                let sumSq = 0;
                for (let i = 0; i < resampled.length; i++) {{
                    const a = Math.abs(resampled[i]);
                    sumSq += a * a;
                }}
                const rms = Math.sqrt(sumSq / resampled.length);
                const extraNormGain = rms > 0.0005 ? Math.min(8.0, Math.max(1.0, 0.20 / rms)) : 2.0;

                const buffer = new ArrayBuffer(44 + resampled.length * 2);
                const view = new DataView(buffer);

                function writeString(offset, str) {{
                    for (let i = 0; i < str.length; i++) {{
                        view.setUint8(offset + i, str.charCodeAt(i));
                    }}
                }}

                writeString(0, "RIFF");
                view.setUint32(4, 36 + resampled.length * 2, true);
                writeString(8, "WAVE");
                writeString(12, "fmt ");
                view.setUint32(16, 16, true);
                view.setUint16(20, 1, true);
                view.setUint16(22, 1, true);
                view.setUint32(24, targetRate, true);
                view.setUint32(28, targetRate * 2, true);
                view.setUint16(32, 2, true);
                view.setUint16(34, 16, true);
                writeString(36, "data");
                view.setUint32(40, resampled.length * 2, true);

                let offset = 44;
                for (let i = 0; i < resampled.length; i++) {{
                    let s = Math.tanh(resampled[i] * extraNormGain);
                    let intSample = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    view.setInt16(offset, intSample, true);
                    offset += 2;
                }}

                const bytes = new Uint8Array(buffer);
                let binary = "";
                const chunkSize = 0x8000;
                for (let i = 0; i < bytes.length; i += chunkSize) {{
                    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
                }}
                return btoa(binary);
            }}

            async function transcribeBufferedAudioWithAI(wavBase64, srcLangCode) {{
                if (!GEMINI_API_KEY || GEMINI_API_KEY.length < 10 || !wavBase64) return null;
                const langName = srcLangCode.startsWith("ru")
                    ? "tiếng Nga (Russian)"
                    : (srcLangCode.startsWith("vi") ? "tiếng Việt (Vietnamese)" : "tiếng Anh (English)");

                const prompt = `Hãy nghe đoạn thu âm bài giảng/giao tiếp bằng ${{langName}} (chuyên ngành ${{SELECTED_DOMAIN}}) và chép lại CHÍNH XÁC từng từ người nói vừa phát âm.
Yêu cầu bắt buộc:
- Chỉ trả về đúng câu văn bản nghe được bằng ${{langName}}.
- Nếu chỉ có tiếng ồn hoặc im lặng không có tiếng người nói, chỉ trả về đúng chuỗi rỗng "".
- Không giải thích, không thêm dấu ngoặc kép.`;

                const models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"];
                for (const m of models) {{
                    try {{
                        const url = `https://generativelanguage.googleapis.com/v1beta/models/${{m}}:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`;
                        const res = await fetch(url, {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({{
                                contents: [{{
                                    parts: [
                                        {{ text: prompt }},
                                        {{
                                            inlineData: {{
                                                mimeType: "audio/wav",
                                                data: wavBase64
                                            }}
                                        }}
                                    ]
                                }}],
                                generationConfig: {{ temperature: 0.1 }}
                            }})
                        }});
                        if (res.ok) {{
                            const data = await res.json();
                            const transcript = (data?.candidates?.[0]?.content?.parts?.[0]?.text || "").trim();
                            if (transcript && transcript !== '""' && transcript !== "''" && transcript.length >= 2) {{
                                return transcript.replace(/^["'«]|["'»]$/g, "").trim();
                            }}
                            return "";
                        }}
                    }} catch (e) {{}}
                }}
                return null;
            }}

            async function initUltraAudioDSP() {{
                try {{
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
                    if (micStream) return;

                    micStream = await navigator.mediaDevices.getUserMedia({{
                        audio: {{
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true,
                            channelCount: 1
                        }}
                    }});

                    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                    audioCtx = new AudioContextClass();
                    if (audioCtx.state === "suspended") {{
                        await audioCtx.resume();
                    }}

                    const source = audioCtx.createMediaStreamSource(micStream);

                    const highpass = audioCtx.createBiquadFilter();
                    highpass.type = "highpass";
                    highpass.frequency.value = 85;

                    const lowpass = audioCtx.createBiquadFilter();
                    lowpass.type = "lowpass";
                    lowpass.frequency.value = 7200;

                    gainNode = audioCtx.createGain();
                    gainNode.gain.value = Math.min(3.5, currentMicGain * 0.4);

                    analyserNode = audioCtx.createAnalyser();
                    analyserNode.fftSize = 256;
                    analyserNode.smoothingTimeConstant = 0.55;

                    scriptProcessor = audioCtx.createScriptProcessor(2048, 1, 1);
                    const silentSink = audioCtx.createGain();
                    silentSink.gain.value = 0.0;

                    source.connect(highpass);
                    highpass.connect(lowpass);
                    lowpass.connect(gainNode);
                    gainNode.connect(analyserNode);
                    gainNode.connect(scriptProcessor);
                    scriptProcessor.connect(silentSink);
                    silentSink.connect(audioCtx.destination);

                    scriptProcessor.onaudioprocess = (audioEvent) => {{
                        if (!isListening) return;
                        const inputBuf = audioEvent.inputBuffer.getChannelData(0);
                        let sumSq = 0;
                        for (let i = 0; i < inputBuf.length; i++) {{
                            sumSq += inputBuf[i] * inputBuf[i];
                        }}
                        const rms = Math.sqrt(sumSq / inputBuf.length);
                        currentRmsLevel = rms;

                        if (rms < noiseFloorRms) {{
                            noiseFloorRms = noiseFloorRms * 0.94 + rms * 0.06;
                        }} else {{
                            noiseFloorRms = noiseFloorRms * 0.995 + rms * 0.005;
                        }}
                        const dynamicThreshold = Math.max(0.018, Math.min(0.12, noiseFloorRms * 2.4));
                        const now = Date.now();

                        if (rms > dynamicThreshold) {{
                            lastSpeechActivity = now;
                            vadLastVoiceTime = now;
                            if (!vadSpeechActive) {{
                                vadSpeechActive = true;
                                vadSpeechStartTime = now;
                            }}
                        }}

                        if (vadSpeechActive) {{
                            pcmRingBuffer.push(new Float32Array(inputBuf));
                            const maxChunks = Math.ceil((15 * audioCtx.sampleRate) / 2048);
                            if (pcmRingBuffer.length > maxChunks) {{
                                pcmRingBuffer.shift();
                            }}

                            const silenceDuration = now - vadLastVoiceTime;
                            const totalChunkDuration = now - vadSpeechStartTime;

                            if ((silenceDuration > 950 && totalChunkDuration >= 600) || totalChunkDuration >= 4200) {{
                                vadSpeechActive = false;
                                const capturedChunks = pcmRingBuffer.slice();
                                pcmRingBuffer = [];
                                if (!isTranscribingChunk && capturedChunks.length > 4) {{
                                    handleFallbackAudioChunk(capturedChunks, audioCtx.sampleRate);
                                }}
                            }}
                        }}
                    }};
                }} catch (e) {{
                    console.warn("DSP init warning:", e);
                }}
            }}

            async function handleFallbackAudioChunk(chunks, sampleRate) {{
                if (!chunks || chunks.length === 0) return;
                let totalLen = 0;
                for (const c of chunks) totalLen += c.length;
                const merged = new Float32Array(totalLen);
                let offset = 0;
                for (const c of chunks) {{
                    merged.set(c, offset);
                    offset += c.length;
                }}

                if (GEMINI_API_KEY && GEMINI_API_KEY.length > 10) {{
                    isTranscribingChunk = true;
                    interimText.innerText = "🧠 Đang giải mã đoạn âm thanh bằng AI Audio (Gemini/Whisper)...";
                    try {{
                        const wavB64 = encodeAmplifiedWavFromSamples(merged, sampleRate);
                        const aiTranscript = await transcribeBufferedAudioWithAI(wavB64, sourceLangSelect.value);
                        if (aiTranscript && aiTranscript.trim().length > 0) {{
                            interimText.innerText = aiTranscript;
                            if (manualSentenceInput) manualSentenceInput.value = aiTranscript;
                            appendSubtitleCard(aiTranscript, sourceLangSelect.value, targetLangSelect.value);
                            interimText.innerText = "✅ Đã chốt câu! Đang lắng nghe câu tiếp theo...";
                            if (manualSentenceInput) manualSentenceInput.value = "";
                        }} else if (!currentActiveSentence.trim()) {{
                            interimText.innerText = "🎙️ Đang lắng nghe (Hãy tiếp tục nói)...";
                        }}
                    }} catch (e) {{}}
                    isTranscribingChunk = false;
                }} else {{
                    interimText.innerText = "💡 Chế độ AI Audio DSP cần Gemini API Key ở thanh bên trái. Hãy chọn chế độ «⚡ Trực tiếp» hoặc dán Gemini API Key!";
                }}
            }}

            function stopUltraAudioDSP() {{
                try {{
                    if (scriptProcessor) {{
                        scriptProcessor.disconnect();
                        scriptProcessor = null;
                    }}
                    if (micStream) {{
                        micStream.getTracks().forEach(t => t.stop());
                        micStream = null;
                    }}
                    if (audioCtx) {{
                        audioCtx.close();
                        audioCtx = null;
                    }}
                    analyserNode = null;
                    gainNode = null;
                    pcmRingBuffer = [];
                    vadSpeechActive = false;
                    currentRmsLevel = 0;
                }} catch (e) {{}}
            }}

            function startReactiveWave() {{
                const canvas = document.getElementById("waveCanvas");
                const ctx = canvas.getContext("2d");
                const bars = 24;
                if (waveAnimId) cancelAnimationFrame(waveAnimId);

                function renderWave() {{
                    if (!isListening) {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        if (levelBarFill) levelBarFill.style.width = "0%";
                        if (levelPctText) levelPctText.innerText = "0%";
                        if (vadLivePill) vadLivePill.style.display = "none";
                        if (interimBox) interimBox.classList.remove("voice-detected");
                        return;
                    }}
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    const barW = canvas.width / bars;
                    const now = Date.now();
                    const isVoiceActiveNow = (now - lastSpeechActivity) < 550;

                    let pct = 0;
                    if (analyserNode) {{
                        pct = Math.min(98, Math.round(Math.min(1.0, currentRmsLevel * 3.2) * 100));
                    }} else {{
                        if (isVoiceActiveNow) {{
                            pct = Math.min(92, Math.max(38, Math.round(58 + Math.sin(now / 90) * 22 + (currentMicGain - 5) * 2)));
                        }} else {{
                            pct = Math.max(2, Math.round(4 + Math.sin(now / 300) * 2));
                        }}
                    }}
                    if (levelBarFill) levelBarFill.style.width = pct + "%";
                    if (levelPctText) levelPctText.innerText = pct + "%";

                    if (isVoiceActiveNow) {{
                        statusDot.classList.add("speaking");
                        if (interimBox) interimBox.classList.add("voice-detected");
                        if (vadLivePill) {{
                            vadLivePill.style.display = "inline-block";
                            vadLivePill.innerText = `🟢 Đang thu giọng nói (${{pct}}%)`;
                        }}
                    }} else {{
                        statusDot.classList.remove("speaking");
                        if (interimBox) interimBox.classList.remove("voice-detected");
                        if (vadLivePill) vadLivePill.style.display = "none";
                    }}

                    if (analyserNode) {{
                        const freqData = new Uint8Array(analyserNode.frequencyBinCount);
                        analyserNode.getByteFrequencyData(freqData);
                        for (let i = 0; i < bars; i++) {{
                            const val = freqData[i % freqData.length] || 0;
                            const h = Math.max(4, Math.min(canvas.height - 2, (val / 255) * canvas.height * 1.25));
                            const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
                            grad.addColorStop(0, "#0284C7");
                            grad.addColorStop(1, isVoiceActiveNow ? "#38BDF8" : "#4ADE80");
                            ctx.fillStyle = grad;
                            ctx.fillRect(i * barW + 1, canvas.height - h, barW - 3, h);
                        }}
                    }} else {{
                        for (let i = 0; i < bars; i++) {{
                            const base = isVoiceActiveNow ? (Math.sin(now / 75 + i * 0.65) * 0.4 + 0.5) : 0.14;
                            const jitter = isVoiceActiveNow ? Math.random() * 0.3 : Math.random() * 0.05;
                            const h = Math.max(4, Math.min(canvas.height - 2, (base + jitter) * canvas.height));
                            const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
                            grad.addColorStop(0, "#0284C7");
                            grad.addColorStop(1, isVoiceActiveNow ? "#38BDF8" : "#4ADE80");
                            ctx.fillStyle = grad;
                            ctx.fillRect(i * barW + 1, canvas.height - h, barW - 3, h);
                        }}
                    }}
                    waveAnimId = requestAnimationFrame(renderWave);
                }}
                renderWave();
            }}

            function expandRussianSlang(text, srcShort) {{
                if (srcShort !== "ru") return text;
                let out = text;
                Object.keys(SLANG_MAP).forEach(slang => {{
                    const regex = new RegExp("\\\\b" + slang + "\\\\b", "gi");
                    out = out.replace(regex, SLANG_MAP[slang]);
                }});
                return out;
            }}

            async function translateSentenceWithContext(currentSentence, srcLangCode, tgtLang) {{
                const srcShort = srcLangCode.split("-")[0];
                if (srcShort === tgtLang) return currentSentence;

                const cleanCurrent = expandRussianSlang(currentSentence.trim(), srcShort);
                const recentContextItems = lectureHistory.slice(-3);

                if (GEMINI_API_KEY && GEMINI_API_KEY.length > 10) {{
                    try {{
                        const contextBlock = recentContextItems.length > 0
                            ? recentContextItems.map((item, i) => `[Câu trước ${{i+1}}]: ${{item.source}} -> ${{item.translated}}`).join("\\n")
                            : "Chưa có câu trước (đây là câu mở đầu).";

                        const prompt = `Bạn là trợ lý dịch cabin bài giảng đại học chuyên ngành ${{SELECTED_DOMAIN}}.
Ngữ cảnh các câu ngay trước đó:
${{contextBlock}}

Hãy dịch câu tiếp theo sau đây từ tiếng ${{srcShort}} sang tiếng ${{tgtLang}} sao cho liền mạch, chuẩn xác theo ngữ cảnh các câu trước, KHÔNG lặp lại câu trước và đúng thuật ngữ chuyên ngành.
CHỈ TRẢ VỀ đúng nội dung câu dịch (không giải thích thêm, không ngoặc kép):
${{cleanCurrent}}`;

                        const gemUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`;
                        const gemRes = await fetch(gemUrl, {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({{
                                contents: [{{ parts: [{{ text: prompt }}] }}],
                                generationConfig: {{ temperature: 0.15 }}
                            }})
                        }});
                        if (gemRes.ok) {{
                            const gemData = await gemRes.json();
                            const textOut = gemData?.candidates?.[0]?.content?.parts?.[0]?.text;
                            if (textOut && textOut.trim().length > 0) {{
                                return textOut.trim();
                            }}
                        }}
                    }} catch (e) {{}}
                }}

                try {{
                    let queryPayload = cleanCurrent;
                    const hasContext = recentContextItems.length > 0;
                    if (hasContext) {{
                        const prevSources = recentContextItems.slice(-2).map(it => expandRussianSlang(it.source, srcShort)).join(". ");
                        queryPayload = prevSources + " ||| " + cleanCurrent;
                    }}

                    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${{srcShort}}&tl=${{tgtLang}}&dt=t&q=${{encodeURIComponent(queryPayload)}}`;
                    const res = await fetch(url);
                    const data = await res.json();
                    if (Array.isArray(data) && Array.isArray(data[0])) {{
                        const fullTranslated = data[0].map(item => item[0]).join("");
                        if (hasContext && fullTranslated.includes("|||")) {{
                            const parts = fullTranslated.split("|||");
                            const contextualResult = parts[parts.length - 1].trim();
                            if (contextualResult.length > 0) return contextualResult;
                        }} else if (!hasContext && fullTranslated.trim().length > 0) {{
                            return fullTranslated.trim();
                        }}
                    }}
                }} catch (err) {{}}

                try {{
                    const urlSingle = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${{srcShort}}&tl=${{tgtLang}}&dt=t&q=${{encodeURIComponent(cleanCurrent)}}`;
                    const resSingle = await fetch(urlSingle);
                    const dataSingle = await resSingle.json();
                    if (Array.isArray(dataSingle) && Array.isArray(dataSingle[0])) {{
                        return dataSingle[0].map(item => item[0]).join("");
                    }}
                }} catch (err2) {{}}

                try {{
                    const mmUrl = `https://api.mymemory.translated.net/get?q=${{encodeURIComponent(cleanCurrent.slice(0, 450))}}&langpair=${{srcShort}}|${{tgtLang}}`;
                    const res3 = await fetch(mmUrl);
                    const data3 = await res3.json();
                    if (data3 && data3.responseData && data3.responseData.translatedText) {{
                        return data3.responseData.translatedText;
                    }}
                }} catch (err3) {{}}

                return "[Đang chờ kết nối dịch tự động...]";
            }}

            function formatCompleteSentence(raw) {{
                let s = collapseImmediateRepetitions(raw);
                if (!s) return "";
                s = s.charAt(0).toUpperCase() + s.slice(1);
                if (!/[.?!…]$/.test(s)) {{
                    s += ".";
                }}
                return s;
            }}

            function appendSubtitleCard(originalText, srcLangCode, tgtLang) {{
                const cleanOrig = formatCompleteSentence(originalText);
                if (!cleanOrig || cleanOrig === ".") return;

                const normOrig = normalizeForComparison(cleanOrig);
                if (!normOrig) return;

                const nowMs = Date.now();
                if (normOrig === lastCommittedNormalized && (nowMs - lastCommitTimestamp) < 8000) {{
                    return;
                }}
                if (
                    lastCommittedNormalized &&
                    lastCommittedNormalized.endsWith(normOrig) &&
                    (nowMs - lastCommitTimestamp) < 4000
                ) {{
                    return;
                }}

                lastCommittedNormalized = normOrig;
                lastCommitTimestamp = nowMs;

                const hintEl = document.getElementById("emptyHint");
                if (hintEl) hintEl.style.display = "none";

                const now = new Date();
                const timeStr = now.toLocaleTimeString("vi-VN", {{ hour: "2-digit", minute: "2-digit", second: "2-digit" }});
                const sentenceIndex = lectureHistory.length + 1;
                const itemId = "sub-" + Date.now() + "-" + Math.floor(Math.random() * 1000);
                const contextCount = Math.min(3, lectureHistory.length);
                const contextNote = contextCount > 0 ? `🔗 Ngữ cảnh +${{contextCount}} câu trước` : `⚓ Câu mở đầu`;

                const card = document.createElement("div");
                card.className = "sub-item";
                card.innerHTML = `
                    <div class="sub-meta">
                        <span>#${{sentenceIndex}} • 🕒 ${{timeStr}} (${{srcLangCode}})</span>
                        <span>${{contextNote}} • ${{SELECTED_DOMAIN}}</span>
                    </div>
                    <div class="sub-source">🗣️ ${{cleanOrig}}</div>
                    <div id="${{itemId}}" class="sub-target">⏳ Đang dịch chuẩn ngữ cảnh...</div>
                `;
                subtitleStream.appendChild(card);

                smartScrollToBottomIfAllowed();

                translateSentenceWithContext(cleanOrig, srcLangCode, tgtLang).then(translated => {{
                    const targetEl = document.getElementById(itemId);
                    if (targetEl) {{
                        targetEl.innerHTML = `🌊 ${{translated}}`;
                    }}
                    lectureHistory.push({{
                        time: timeStr,
                        source: cleanOrig,
                        translated: translated
                    }});
                    if (!userScrolledUp) {{
                        subtitleStream.scrollTop = subtitleStream.scrollHeight;
                    }}
                }});
            }}

            function forceCommitInterim() {{
                if (sentenceSilenceTimer) {{
                    clearTimeout(sentenceSilenceTimer);
                    sentenceSilenceTimer = null;
                }}

                let candidate = "";
                if (manualSentenceInput && manualSentenceInput.value.trim().length > 0) {{
                    candidate = manualSentenceInput.value.trim();
                }} else if (currentActiveSentence.trim().length > 0) {{
                    candidate = currentActiveSentence.trim();
                }}

                if (!candidate && interimText) {{
                    const domText = (interimText.innerText || "").trim();
                    if (
                        domText &&
                        !DEFAULT_PLACEHOLDERS.includes(domText) &&
                        !domText.startsWith("Nhấn") &&
                        !domText.startsWith("🎙️") &&
                        !domText.startsWith("🧠") &&
                        !domText.startsWith("💡") &&
                        !domText.startsWith("✅")
                    ) {{
                        candidate = domText;
                    }}
                }}

                if (candidate && candidate.length > 0) {{
                    committedResultIndex = latestResultsLength;
                    currentActiveSentence = "";
                    pcmRingBuffer = [];
                    if (manualSentenceInput) manualSentenceInput.value = "";
                    interimText.innerText = "✅ Đã chốt câu! Đang lắng nghe câu tiếp theo...";

                    appendSubtitleCard(candidate, sourceLangSelect.value, targetLangSelect.value);
                }} else if (pcmRingBuffer.length > 3 && audioCtx && GEMINI_API_KEY && GEMINI_API_KEY.length > 10) {{
                    const captured = pcmRingBuffer.slice();
                    pcmRingBuffer = [];
                    vadSpeechActive = false;
                    handleFallbackAudioChunk(captured, audioCtx.sampleRate);
                }} else {{
                    const prevStatus = statusText.innerText;
                    statusText.innerText = "💡 Chưa có câu đang nói! Hãy nói vào Mic hoặc gõ câu vào ô bên dưới rồi nhấn Enter.";
                    if (manualSentenceInput) manualSentenceInput.focus();
                    setTimeout(() => {{
                        if (isListening) {{
                            statusText.innerText = `🟢 Đang thu âm (${{sourceLangSelect.options[sourceLangSelect.selectedIndex].text}}) — Hãy nói bình thường...`;
                        }} else {{
                            statusText.innerText = prevStatus;
                        }}
                    }}, 2500);
                }}
            }}

            function pickBestTranscript(resultItem) {{
                if (!resultItem || resultItem.length === 0) return "";
                let bestText = (resultItem[0].transcript || "").trim();
                let bestConf = typeof resultItem[0].confidence === "number" ? resultItem[0].confidence : 0;
                for (let a = 1; a < resultItem.length; a++) {{
                    const altText = (resultItem[a].transcript || "").trim();
                    const altConf = typeof resultItem[a].confidence === "number" ? resultItem[a].confidence : 0;
                    if (altText.length > bestText.length && altConf >= bestConf * 0.85) {{
                        bestText = altText;
                        bestConf = altConf;
                    }}
                }}
                return bestText;
            }}

            function startRecognition() {{
                if (isListening) return;

                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                const selectedMode = captureModeSelect ? captureModeSelect.value : "webspeech";

                isListening = true;
                committedResultIndex = 0;
                latestResultsLength = 0;
                currentActiveSentence = "";
                lastWebSpeechResultAt = 0;
                statusDot.classList.add("active");
                btnStart.disabled = true;
                btnPause.disabled = false;

                const langLabel = sourceLangSelect.options[sourceLangSelect.selectedIndex].text;
                interimText.innerText = `🎙️ Đang lắng nghe bằng ${{langLabel}} — Bạn hãy nói vào Mic, từng chữ sẽ hiện ngay tại đây...`;

                startReactiveWave();

                if (selectedMode === "aidsp" || !SpeechRecognition) {{
                    if (recognition) {{
                        try {{ recognition.stop(); }} catch (e) {{}}
                        recognition = null;
                    }}
                    statusText.innerText = `🧠 Đang thu âm bằng AI Audio DSP (${{langLabel}}) — Cứ nói hết câu (~4 giây) AI sẽ tự động chép lời & dịch...`;
                    initUltraAudioDSP();
                    return;
                }}

                // Tắt mọi luồng getUserMedia để SpeechRecognition độc quyền Microphone 100%
                stopUltraAudioDSP();

                try {{
                    recognition = new SpeechRecognition();
                    recognition.lang = sourceLangSelect.value;
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.maxAlternatives = 3;

                    recognition.onstart = () => {{
                        const curLangText = sourceLangSelect.options[sourceLangSelect.selectedIndex].text;
                        statusText.innerText = `🟢 Đang thu âm trực tiếp (${{curLangText}}) — Hãy nói bình thường, chữ sẽ chạy ngay bên dưới...`;
                    }};

                    recognition.onaudiostart = () => {{ lastSpeechActivity = Date.now(); }};
                    recognition.onsoundstart = () => {{ lastSpeechActivity = Date.now(); }};
                    recognition.onspeechstart = () => {{ lastSpeechActivity = Date.now(); }};

                    recognition.onresult = (event) => {{
                        const now = Date.now();
                        lastSpeechActivity = now;
                        lastWebSpeechResultAt = now;
                        latestResultsLength = event.results.length;

                        if (committedResultIndex > event.results.length) {{
                            committedResultIndex = 0;
                        }}

                        let rebuiltSentence = "";
                        let hasUnfinishedInterim = false;

                        for (let i = committedResultIndex; i < event.results.length; ++i) {{
                            const piece = pickBestTranscript(event.results[i]);
                            if (!piece) continue;

                            if (
                                i === committedResultIndex &&
                                lastCommittedNormalized &&
                                normalizeForComparison(piece) === lastCommittedNormalized
                            ) {{
                                committedResultIndex = i + 1;
                                continue;
                            }}

                            rebuiltSentence = smartMergeSegments(rebuiltSentence, piece);
                            if (!event.results[i].isFinal) {{
                                hasUnfinishedInterim = true;
                            }}
                        }}

                        rebuiltSentence = collapseImmediateRepetitions(rebuiltSentence);
                        currentActiveSentence = rebuiltSentence;

                        if (currentActiveSentence.length > 0) {{
                            interimText.innerText = currentActiveSentence;
                            if (manualSentenceInput) {{
                                manualSentenceInput.value = currentActiveSentence;
                            }}

                            if (sentenceSilenceTimer) clearTimeout(sentenceSilenceTimer);

                            const wordCount = currentActiveSentence.split(/\\s+/).length;
                            const hasEndPunctuation = /[.?!…]\\s*$/.test(currentActiveSentence);

                            if (hasEndPunctuation && !hasUnfinishedInterim && wordCount >= 2) {{
                                sentenceSilenceTimer = setTimeout(() => {{
                                    forceCommitInterim();
                                }}, PUNCTUATION_PAUSE_MS);
                            }} else if (!hasUnfinishedInterim && wordCount >= 11) {{
                                sentenceSilenceTimer = setTimeout(() => {{
                                    forceCommitInterim();
                                }}, PUNCTUATION_PAUSE_MS);
                            }} else {{
                                sentenceSilenceTimer = setTimeout(() => {{
                                    if (currentActiveSentence.trim().length > 0) {{
                                        forceCommitInterim();
                                    }}
                                }}, SENTENCE_PAUSE_MS);
                            }}
                        }}
                    }};

                    recognition.onerror = (event) => {{
                        if (event.error === "not-allowed" || event.error === "service-not-allowed") {{
                            statusText.innerText = "❌ Trình duyệt đang chặn quyền Microphone! Hãy bấm biểu tượng ổ khóa trên thanh địa chỉ web -> Cho phép Microphone.";
                            stopRecognition();
                        }} else if (event.error === "audio-capture") {{
                            statusText.innerText = "❌ Không tìm thấy thiết bị Microphone! Hãy kiểm tra kết nối Mic của bạn.";
                            stopRecognition();
                        }} else if (event.error === "network") {{
                            statusText.innerText = "🔄 Kết nối WebSpeech bị chặn trên trình duyệt này — Đang tự động chuyển sang chế độ AI Audio DSP...";
                            if (captureModeSelect) captureModeSelect.value = "aidsp";
                            try {{ recognition.stop(); }} catch (e) {{}}
                            recognition = null;
                            initUltraAudioDSP();
                        }} else if (event.error === "no-speech") {{
                            const curLang = sourceLangSelect.options[sourceLangSelect.selectedIndex].text;
                            statusText.innerText = `🟢 Đang lắng nghe (${{curLang}}) — Lưu ý: Nếu bạn nói Tiếng Việt hãy chọn mục «Nghe: 🇻🇳 Tiếng Việt» nhé!`;
                        }}
                    }};

                    recognition.onend = () => {{
                        if (currentActiveSentence.trim().length > 0) {{
                            const pending = currentActiveSentence.trim();
                            currentActiveSentence = "";
                            if (manualSentenceInput) manualSentenceInput.value = "";
                            appendSubtitleCard(pending, sourceLangSelect.value, targetLangSelect.value);
                        }}
                        committedResultIndex = 0;
                        latestResultsLength = 0;

                        const modeNow = captureModeSelect ? captureModeSelect.value : "webspeech";
                        if (isListening && modeNow === "webspeech" && recognition) {{
                            setTimeout(() => {{
                                if (isListening && recognition) {{
                                    try {{
                                        recognition.lang = sourceLangSelect.value;
                                        recognition.start();
                                    }} catch (e) {{}}
                                }}
                            }}, 80);
                        }}
                    }};

                    sourceLangSelect.onchange = () => {{
                        const newLangText = sourceLangSelect.options[sourceLangSelect.selectedIndex].text;
                        interimText.innerText = `🎙️ Đã chuyển sang nghe ${{newLangText}} — Hãy nói vào Mic...`;
                        if (isListening && recognition) {{
                            recognition.lang = sourceLangSelect.value;
                            try {{ recognition.stop(); }} catch (e) {{}}
                        }}
                    }};

                    recognition.start();

                    if (noResultWatchdogTimer) clearTimeout(noResultWatchdogTimer);
                    noResultWatchdogTimer = setTimeout(() => {{
                        if (isListening && lastWebSpeechResultAt === 0 && !currentActiveSentence.trim()) {{
                            const isRu = sourceLangSelect.value.startsWith("ru");
                            if (isRu) {{
                                interimText.innerText = "💡 Chưa thấy chữ hiện ra? Nếu bạn đang nói TIẾNG VIỆT để thử Mic, hãy đổi ô «Nghe» (góc trên bên trái) sang «🇻🇳 Tiếng Việt»! Hoặc đổi «Chế độ thu» sang «🧠 AI Audio DSP».";
                            }} else {{
                                interimText.innerText = "💡 Nếu trình duyệt của bạn chặn WebSpeech (như Brave/Firefox), hãy đổi «Chế độ thu» sang «🧠 AI Audio DSP» hoặc dùng nút Thu âm trực tiếp ngay bên dưới!";
                            }}
                        }}
                    }}, 6000);
                }} catch (err) {{
                    statusText.innerText = "⚠️ Đang chuyển sang chế độ thu âm AI Audio DSP dự phòng: " + err.message;
                    initUltraAudioDSP();
                }}
            }}

            function stopRecognition() {{
                isListening = false;
                if (sentenceSilenceTimer) clearTimeout(sentenceSilenceTimer);
                if (noResultWatchdogTimer) clearTimeout(noResultWatchdogTimer);
                if (currentActiveSentence.trim().length > 0) {{
                    const remaining = currentActiveSentence.trim();
                    currentActiveSentence = "";
                    if (manualSentenceInput) manualSentenceInput.value = "";
                    appendSubtitleCard(remaining, sourceLangSelect.value, targetLangSelect.value);
                }}
                committedResultIndex = 0;
                latestResultsLength = 0;
                if (recognition) {{
                    try {{ recognition.stop(); }} catch (e) {{}}
                }}
                stopUltraAudioDSP();
                if (waveAnimId) cancelAnimationFrame(waveAnimId);
                statusDot.classList.remove("active");
                statusDot.classList.remove("speaking");
                if (interimBox) interimBox.classList.remove("voice-detected");
                if (vadLivePill) vadLivePill.style.display = "none";
                statusText.innerText = "⏸️ Đã tạm dừng thu âm. Bạn có thể lướt xem lại toàn bộ lịch sử bài giảng hoặc tải file về máy.";
                btnStart.disabled = false;
                btnPause.disabled = true;
            }}

            function clearTranscript() {{
                lectureHistory = [];
                committedResultIndex = latestResultsLength;
                currentActiveSentence = "";
                lastCommittedNormalized = "";
                pcmRingBuffer = [];
                unreadNewCount = 0;
                userScrolledUp = false;
                if (manualSentenceInput) manualSentenceInput.value = "";
                jumpBottomBtn.style.display = "none";
                scrollBadge.className = "scroll-lock-badge auto";
                scrollBadge.innerText = "🟢 Tự động cuộn theo câu mới";
                subtitleStream.innerHTML = `
                    <div id="emptyHint" class="empty-hint">
                        🚢 Đã xóa lịch sử. Nhấn <b>🎙️ Bắt đầu thu âm</b> để ghi nhận bài giảng mới.
                    </div>
                `;
                interimText.innerText = "...";
            }}

            function downloadTranscript() {{
                if (lectureHistory.length === 0) {{
                    alert("Chưa có nội dung bài giảng nào được ghi lại!");
                    return;
                }}
                let content = "==========================================================\\n";
                content += "   BẢN GHI BÀI GIẢNG — ANH MINH TRANSLATE (RU - VI - EN)\\n";
                content += "   Tác giả: Mai Văn Minh — Đóng tàu, СПбГМТУ (Xanh-Petecbua)\\n";
                content += "   Chuyên ngành: " + SELECTED_DOMAIN + "\\n";
                content += "==========================================================\\n\\n";

                lectureHistory.forEach((item, idx) => {{
                    content += `[Câu ${{idx + 1}}] Thời gian: ${{item.time}}\\n`;
                    content += `🗣️ Câu gốc  : ${{item.source}}\\n`;
                    content += `🌊 Bản dịch : ${{item.translated}}\\n`;
                    content += "----------------------------------------------------------\\n";
                }});

                const blob = new Blob([content], {{ type: "text/plain;charset=utf-8" }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                const dateTag = new Date().toISOString().slice(0, 10);
                a.download = `Bai_Giang_AnhMinhTranslate_${{dateTag}}.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
        </script>
    </body>
    </html>
    """


# ==============================================================================
# 7. XỬ LÝ THU ÂM BẰNG PYTHON THUẦN (CHUẨN HÓA RMS + PRE-EMPHASIS NHƯ WHISPER X12.0)
# ==============================================================================
def boost_wav_audio_bytes(audio_bytes: bytes, max_gain_factor: float = 12.0) -> bytes:
    """
    Bộ xử lý DSP chuẩn Whisper/ChatGPT cho file WAV:
    1. Loại bỏ DC Offset (trung bình tĩnh).
    2. Lọc Pre-Emphasis nhẹ (+6dB tần số cao) giúp phụ âm tiếng Nga/Việt sắc nét.
    3. Chuẩn hóa theo RMS (Root Mean Square) (bỏ qua gai nhiễu khi bấm nút).
    4. Soft-knee Limiter chống vỡ tiếng (clipping).
    """
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

            # 1. Loại bỏ DC offset
            mean_val = sum(samples) / float(n)

            # 2. Bỏ qua 0.08 giây đầu và cuối khi tính RMS để không bị ảnh hưởng bởi tiếng "bụp" lúc bấm nút Mic
            skip = min(int(params.framerate * 0.08), n // 6)
            core_slice = samples[skip : n - skip] if (n - 2 * skip) > 200 else samples

            sum_sq = 0.0
            for x in core_slice:
                centered = x - mean_val
                sum_sq += centered * centered
            rms = math.sqrt(sum_sq / max(1, len(core_slice)))

            # Mục tiêu RMS chuẩn phòng thu cho nhận diện giọng nói là ~6500 (trên thang 32767)
            target_rms = 6500.0
            if rms > 1.0:
                auto_gain = min(max_gain_factor, max(1.8, target_rms / rms))
            else:
                auto_gain = max_gain_factor

            # 3. Áp dụng Pre-Emphasis nhẹ (0.22) + Khuếch đại Auto-Gain + Soft Limiter
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
    wav_bytes: bytes,
    source_lang_speech: str,
    target_lang_trans: str,
    domain: str = "Kỹ thuật & Đóng tàu",
) -> Tuple[Optional[str], Optional[str]]:
    """
    Nhận diện giọng nói & dịch thuật trực tiếp từ âm thanh bằng mô hình AI đa phương thức Gemini
    (Cơ chế tương đương Whisper / GPT-4o Audio của ChatGPT & Claude).
    """
    clean_k = clean_api_key(api_key)
    if not clean_k or not wav_bytes:
        return None, None

    b64_audio = base64.b64encode(wav_bytes).decode("utf-8")
    models_to_try = discover_available_gemini_models(clean_k)

    prompt = f"""
Bạn là chuyên gia nhận diện giọng nói (ASR) và dịch thuật học thuật chuyên ngành "{domain}".
Hãy nghe file âm thanh đính kèm (ngôn ngữ gốc: {source_lang_speech}) và thực hiện:
1. Chép lại chính xác tuyệt đối toàn bộ lời nói trong file âm thanh (kể cả khi người nói nói nhỏ).
2. Dịch câu đó sang ngôn ngữ "{target_lang_trans}" chuẩn xác theo ngữ cảnh đại học tại Nga.

CHỈ TRẢ VỀ đúng 1 đối tượng JSON hợp lệ:
{{
  "transcript": "Lời nói gốc nhận diện được",
  "translation": "Bản dịch hoàn chỉnh sang {target_lang_trans}"
}}
"""

    for model_name in models_to_try[:4]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "audio/wav",
                                "data": b64_audio,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", parts[0]["text"].strip())
                        parsed = json.loads(raw_json)
                        tr_text = str(parsed.get("transcript", "")).strip()
                        tl_text = str(parsed.get("translation", "")).strip()
                        if tr_text:
                            return tr_text, tl_text
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
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    # Bước 1: Khuếch đại RMS & lọc âm thanh bằng thuật toán DSP x12.0
    boosted_bytes = boost_wav_audio_bytes(audio_bytes, max_gain_factor=max_gain_factor)

    # Bước 2: Nếu có Gemini API Key, ưu tiên dùng AI Multimodal Audio (nhạy như Whisper/ChatGPT)
    if clean_api_key(gemini_api_key):
        ai_transcript, ai_translated = transcribe_audio_with_gemini_multimodal(
            api_key=gemini_api_key,
            wav_bytes=boosted_bytes,
            source_lang_speech=source_lang_speech,
            target_lang_trans=target_lang_trans,
            domain=selected_domain,
        )
        if ai_transcript:
            if not ai_translated:
                src_short = source_lang_speech.split("-")[0]
                ai_translated = fast_free_translate(ai_transcript, src_short, target_lang_trans)
            return ai_transcript, ai_translated, None

    # Bước 3: Sử dụng Google SpeechRecognition trên bản âm thanh đã kích RMS
    if sr is None:
        return None, None, "Thư viện SpeechRecognition chưa được cài đặt trong requirements.txt."

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 20
    recognizer.dynamic_energy_threshold = False

    last_err = None
    for candidate_wav in (boosted_bytes, audio_bytes):
        try:
            with sr.AudioFile(io.BytesIO(candidate_wav)) as source:
                audio_data = recognizer.record(source)

            transcript = recognizer.recognize_google(audio_data, language=source_lang_speech)
            if transcript and transcript.strip():
                src_short = source_lang_speech.split("-")[0]
                translated = fast_free_translate(transcript, src_short, target_lang_trans)
                return transcript, translated, None
        except sr.UnknownValueError:
            last_err = "Không nhận diện được lời nói trong đoạn thu âm. Bạn hãy nói gần Mic hơn hoặc dán Gemini API Key ở cột trái để bật AI Audio siêu nhạy nhé!"
        except sr.RequestError as e:
            last_err = f"Không thể kết nối tới dịch vụ nhận diện giọng nói: {e}"
        except Exception as e:
            last_err = f"Định dạng âm thanh chưa tương thích trực tiếp (ưu tiên thu âm trực tiếp hoặc tải file .WAV). Chi tiết: {e}"

    return None, None, last_err


# ==============================================================================
# 8. GIAO DIỆN CHÍNH (SIDEBAR + LƯU CỐ ĐỊNH THÔNG TIN SINH VIÊN & KEY + 2 TAB)
# ==============================================================================
def main() -> None:
    if "input_text_area" not in st.session_state:
        st.session_state["input_text_area"] = ""

    # Kiểm tra quyền Tác giả
    if "is_author_admin" not in st.session_state:
        st.session_state["is_author_admin"] = False
    try:
        if st.query_params.get("admin", "") == DEFAULT_AUTHOR_PASSWORD:
            st.session_state["is_author_admin"] = True
    except Exception:
        pass

    # 1. Nạp Gemini API Key đã lưu cố định (nếu có)
    persisted_key = load_saved_api_key_from_store()
    if "saved_gemini_api_key" not in st.session_state:
        st.session_state["saved_gemini_api_key"] = persisted_key
    elif persisted_key and not st.session_state["saved_gemini_api_key"]:
        st.session_state["saved_gemini_api_key"] = persisted_key

    if "declined_keys" not in st.session_state:
        st.session_state["declined_keys"] = set()

    # 2. Nạp Thông tin Sinh viên đã lưu cố định (nếu đã nhập từ các lần trước)
    saved_profile = load_saved_student_profile()
    if saved_profile:
        st.session_state["confirmed_user_name"] = saved_profile.get("full_name", "")
        st.session_state["confirmed_user_year"] = saved_profile.get("student_year", "Sinh viên Năm 4")
        st.session_state["confirmed_user_uni"] = saved_profile.get("university", "")

    if "editing_student_profile" not in st.session_state:
        st.session_state["editing_student_profile"] = False

    # Tự động đồng bộ localStorage (cả Key và Hồ sơ Sinh viên) ở lần tải đầu tiên
    if not st.session_state.get("ls_sync_checked"):
        st.session_state["ls_sync_checked"] = True
        if not st.session_state.get("saved_gemini_api_key") or not st.session_state.get("confirmed_user_name"):
            inject_localstorage_sync(action="load_all")

    inject_ocean_blue_css(is_author_admin=st.session_state["is_author_admin"])
    avatar_uri = get_author_avatar_data_uri()

    with st.sidebar:
        # 1. THẺ GIỚI THIỆU TÁC GIẢ
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

        # 2. THÔNG TIN SINH VIÊN SỬ DỤNG (TỰ ĐỘNG LƯU CỐ ĐỊNH CHO CÁC LẦN SAU)
        render_html(
            """
            <div class="user-checkin-card">
                <div style="font-size:0.95rem; font-weight:800; color:#7DD3FC; margin-bottom:2px;">
                    👤 Thông tin Sinh viên sử dụng
                </div>
                <div style="font-size:0.76rem; color:#E0F2FE; line-height:1.35;">
                    Chỉ cần nhập 1 lần — Hệ thống tự động lưu lại cho tất cả các lần sử dụng sau:
                </div>
            </div>
            """
        )

        has_confirmed_profile = bool(
            st.session_state.get("confirmed_user_name") and st.session_state.get("confirmed_user_uni")
        )

        # Thực thi gửi Email từ trình duyệt SAU KHI trang đã rerun ổn định (không bị st.rerun() cắt ngang!)
        if st.session_state.get("pending_email_relay"):
            relay_info = st.session_state.pop("pending_email_relay")
            inject_localstorage_sync(
                action="save_profile",
                student_profile=relay_info,
            )
            trigger_client_side_email_relay(
                full_name=relay_info["full_name"],
                student_year=relay_info["student_year"],
                university=relay_info["university"],
            )

        if has_confirmed_profile and not st.session_state["editing_student_profile"]:
            sv_name = st.session_state["confirmed_user_name"]
            sv_year = st.session_state.get("confirmed_user_year", "Sinh viên Năm 4")
            sv_uni = st.session_state["confirmed_user_uni"]

            render_html(
                f"""
                <div class="saved-student-badge-box">
                    <div style="font-size:0.76rem; color:#A7F3D0; font-weight:700; margin-bottom:3px;">
                        ✅ ĐÃ LƯU THÔNG TIN CỐ ĐỊNH
                    </div>
                    <div style="font-size:0.98rem; font-weight:800; color:#FFFFFF;">
                        🎓 {sv_name}
                    </div>
                    <div style="font-size:0.82rem; color:#E0F2FE; margin-top:2px;">
                        • {sv_year}<br/>
                        • Trường: <b>{sv_uni}</b>
                    </div>
                </div>
                """
            )
            col_prof1, col_prof2 = st.columns(2)
            with col_prof1:
                if st.button("✏️ Đổi thông tin", key="btn_edit_student_info", use_container_width=True):
                    st.session_state["editing_student_profile"] = True
                    st.rerun()
            with col_prof2:
                if st.button("📨 Gửi lại Email", key="btn_resend_email_notify", use_container_width=True):
                    ok_mail, channel_mail = send_user_notification_email(sv_name, sv_year, sv_uni)
                    trigger_client_side_email_relay(sv_name, sv_year, sv_uni)
                    st.toast(f"📨 Đã gửi thông báo về {AUTHOR_NOTIFICATION_EMAIL} ({channel_mail})!")
        else:
            default_year_idx = 3
            cur_year = st.session_state.get("confirmed_user_year", "Sinh viên Năm 4")
            if cur_year in STUDENT_YEAR_OPTIONS:
                default_year_idx = STUDENT_YEAR_OPTIONS.index(cur_year)

            with st.form("student_user_checkin_form", clear_on_submit=False):
                user_full_name = st.text_input(
                    "✍️ Họ và tên của bạn:",
                    value=st.session_state.get("confirmed_user_name", ""),
                    placeholder="VD: Nguyễn Văn A",
                )
                user_student_year = st.selectbox(
                    "🎓 Sinh viên năm mấy:",
                    options=STUDENT_YEAR_OPTIONS,
                    index=default_year_idx,
                )
                user_university = st.text_input(
                    "🏫 Học ở trường nào:",
                    value=st.session_state.get("confirmed_user_uni", ""),
                    placeholder="VD: СПбГМТУ, ИТМО, СПбГУ, МГТУ...",
                )
                confirm_user_btn = st.form_submit_button(
                    "✅ Xác nhận & Lưu cho các lần sau",
                    use_container_width=True,
                    type="primary",
                )

            if confirm_user_btn:
                if not user_full_name.strip() or not user_university.strip():
                    st.warning("⚠️ Bạn vui lòng nhập đầy đủ **Họ và tên** và **Tên trường đang theo học** nhé!")
                else:
                    clean_name = user_full_name.strip()
                    clean_uni = user_university.strip()
                    st.session_state["confirmed_user_name"] = clean_name
                    st.session_state["confirmed_user_year"] = user_student_year
                    st.session_state["confirmed_user_uni"] = clean_uni
                    st.session_state["editing_student_profile"] = False

                    save_student_profile_permanently(clean_name, user_student_year, clean_uni)

                    with st.spinner("📨 Đang lưu thông tin cố định & gửi thông báo tới tác giả..."):
                        send_user_notification_email(
                            full_name=clean_name,
                            student_year=user_student_year,
                            university=clean_uni,
                        )
                        # Lưu cờ để gửi tiếp từ trình duyệt ngay sau khi st.rerun() hoàn tất
                        st.session_state["pending_email_relay"] = {
                            "full_name": clean_name,
                            "student_year": user_student_year,
                            "university": clean_uni,
                        }
                    st.toast(f"✅ Đã lưu thông tin của {clean_name} và gửi thông báo tới tác giả!")
                    st.rerun()

            if has_confirmed_profile and st.session_state["editing_student_profile"]:
                if st.button("↩️ Hủy chỉnh sửa", key="btn_cancel_edit_student", use_container_width=True):
                    st.session_state["editing_student_profile"] = False
                    st.rerun()

        st.markdown("---")

        # 3. BUỒNG LÁI HỆ THỐNG & LƯU CỐ ĐỊNH GEMINI API KEY
        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:10px; margin-top:4px; margin-bottom:8px;">
                {STICKER_HELM_WHEEL}
                <span style="font-size:1.1rem; font-weight:800; color:#FFFFFF;">Buồng Lái Hệ Thống</span>
            </div>
            """
        )

        saved_key_val = clean_api_key(st.session_state.get("saved_gemini_api_key", ""))

        gemini_api_key = st.text_input(
            "🔑 Gemini API Key (Chấp nhận mọi Key):",
            value=saved_key_val,
            type="password",
            placeholder="Dán bất kỳ Gemini API Key nào (hoặc để trống)",
            help="Khi nhập Key lần đầu, bạn có thể chọn Lưu cố định để các lần sau vào web không cần dán lại!",
        )

        render_html(
            f"""
            <a href="{GEMINI_API_KEY_URL}" target="_blank" rel="noopener noreferrer" class="gemini-key-link-btn">
                🔗 Lấy Gemini API Key miễn phí (Mở tab mới) ↗
            </a>
            """
        )

        clean_key_input = clean_api_key(gemini_api_key)

        if (
            clean_key_input
            and clean_key_input != saved_key_val
            and clean_key_input not in st.session_state["declined_keys"]
        ):
            st.warning(
                "💾 **Bạn có muốn lưu cố định Gemini API Key này cho các lần sử dụng sau không?**\n\n"
                "Nếu đồng ý, từ các lần sau bạn mở lại hoặc tải lại trang sẽ chỉ việc dùng luôn mà không cần sao chép dán lại."
            )
            save_col1, save_col2 = st.columns(2)
            with save_col1:
                if st.button("✅ Đồng ý lưu", key="btn_agree_save_key", type="primary", use_container_width=True):
                    st.session_state["saved_gemini_api_key"] = clean_key_input
                    save_api_key_permanently(clean_key_input)
                    inject_localstorage_sync(action="save_key", key_to_save=clean_key_input)
                    st.toast("✅ Đã lưu cố định Gemini API Key cho các lần truy cập sau!")
                    st.rerun()
            with save_col2:
                if st.button("❌ Chỉ dùng lần này", key="btn_decline_save_key", use_container_width=True):
                    st.session_state["declined_keys"].add(clean_key_input)
                    st.info("👍 Key sẽ chỉ dùng trong phiên hiện tại.")
                    st.rerun()

        if clean_key_input:
            avail_models = discover_available_gemini_models(clean_key_input)
            top_model = avail_models[0] if avail_models else "gemini-flash"
            if clean_key_input == saved_key_val:
                st.success(
                    f"📌 **Đã lưu cố định Gemini API Key!** (Model ưu tiên: `{top_model}`)\n\n"
                    "Các lần sau vào web bạn chỉ việc sử dụng ngay."
                )
                if st.button("🗑️ Xóa / Đổi Key cố định đã lưu", key="btn_delete_saved_key", use_container_width=True):
                    st.session_state["saved_gemini_api_key"] = ""
                    delete_saved_api_key()
                    inject_localstorage_sync(action="delete_key")
                    st.rerun()
            else:
                st.success(f"✨ Đã nhận Gemini API Key! (Model ưu tiên: `{top_model}` + Tự động dự phòng GTX)")
        else:
            st.info("⚡ Chế độ hiện tại: **Dịch Đa Luồng GTX Siêu Tốc (5 Cổng POST)** — Không cần Key!")

        st.markdown("---")
        st.markdown("### 🎓 Chuyên ngành Ưu tiên")
        selected_domain = st.selectbox(
            "Chọn lĩnh vực học tập / giao tiếp:",
            options=[
                "Kỹ thuật & Đóng tàu",
                "Giao tiếp / Tin nhắn đời thường",
                "CNTT & Khoa học máy tính",
                "Kinh tế & Quản trị",
                "Học thuật tổng hợp",
            ],
            index=0,
        )

        st.markdown("---")
        st.markdown("### 📲 Chia sẻ 1 Link & Dùng trên Điện thoại")
        st.caption("Dán link web ứng dụng của bạn để rút gọn về 1 link duy nhất & tạo mã QR cho điện thoại:")
        app_public_url = st.text_input(
            "🌐 Link ứng dụng của bạn:",
            value="https://dich-thuat-anhminh.streamlit.app",
            key="share_url_input",
        )
        if app_public_url.strip():
            short_link = shorten_share_url(app_public_url.strip())
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={urllib.parse.quote(short_link)}"
            render_html(
                f"""
                <div style="background:rgba(255,255,255,0.12); border:1.5px solid #38BDF8; border-radius:14px; padding:12px; text-align:center; margin-top:6px;">
                    <div style="font-size:0.78rem; color:#BAE6FD; margin-bottom:4px;">🔗 Link rút gọn chia sẻ mọi nơi:</div>
                    <a href="{short_link}" target="_blank" style="color:#7DD3FC !important; font-weight:800; font-size:0.92rem; word-break:break-all; text-decoration:underline;">
                        {short_link}
                    </a>
                    <div style="margin-top:10px; display:flex; justify-content:center;">
                        <img src="{qr_api_url}" alt="QR Code" style="width:125px; height:125px; border-radius:10px; border:3px solid #FFFFFF; background:#FFFFFF;" />
                    </div>
                    <div style="font-size:0.74rem; color:#E0F2FE; margin-top:6px;">
                        📱 Mở Camera / Zalo / Telegram trên điện thoại quét mã để dùng ngay!
                    </div>
                </div>
                """
            )

        st.markdown("---")
        st.markdown("### 📚 Từ điển Lóng Sinh viên Nga")
        st.caption("Tra nhanh các từ viết tắt & tiếng lóng hay gặp trên Telegram / VK / Giảng đường:")

        slang_search = st.text_input(
            "🔍 Tìm nhanh từ lóng:",
            placeholder="VD: препод, курсач, лаба, хвост...",
        )

        filtered_slang = [
            item
            for item in RUSSIAN_SLANG_DICT
            if not slang_search.strip()
            or slang_search.lower() in item["word"].lower()
            or slang_search.lower() in item["vi"].lower()
            or slang_search.lower() in item["full"].lower()
        ]

        with st.container(height=260):
            for item in filtered_slang:
                with st.expander(f"⚓ {item['accent']} — {item['vi']}"):
                    st.markdown(
                        f"- **Dạng đầy đủ:** `{item['full']}`\n"
                        f"- **Tiếng Anh:** *{item['en']}*\n"
                        f"- **Ví dụ:** _{item['example']}_"
                    )
                    if st.button(f"Đưa «{item['word']}» vào ô dịch", key=f"use_slang_{item['word']}"):
                        st.session_state["input_text_area"] = item["example"]
                        st.rerun()

        st.markdown("---")
        # 4. CHẾ ĐỘ TÁC GIẢ
        with st.expander("🔐 Chế độ Tác giả (Mai Văn Minh)"):
            if not st.session_state["is_author_admin"]:
                admin_pwd = st.text_input(
                    "Nhập mật khẩu tác giả để hiện nút Sửa App & GitHub:",
                    type="password",
                    key="author_pwd_input",
                )
                if st.button("🔓 Mở khóa quyền Tác giả", use_container_width=True):
                    if admin_pwd == DEFAULT_AUTHOR_PASSWORD:
                        st.session_state["is_author_admin"] = True
                        st.success("✅ Đã mở khóa giao diện Tác giả! Các nút Sửa App & GitHub đã hiển thị trở lại.")
                        st.rerun()
                    else:
                        st.error("❌ Mật khẩu không đúng!")
            else:
                st.success("👑 Đang ở Chế độ Tác giả (Đã hiện thanh công cụ Sửa App & GitHub)")
                if USER_LOGS_FILE.exists():
                    try:
                        logs_data = json.loads(USER_LOGS_FILE.read_text(encoding="utf-8"))
                        st.markdown(f"**📋 Danh sách sinh viên đã xác nhận ({len(logs_data)}):**")
                        for entry in logs_data[:15]:
                            st.caption(
                                f"• **{entry.get('full_name')}** — {entry.get('student_year')} ({entry.get('university')}) lúc `{entry.get('time')}`"
                            )
                    except Exception:
                        pass
                if st.button("🔒 Khóa lại (Ẩn Sửa App & GitHub)", use_container_width=True):
                    st.session_state["is_author_admin"] = False
                    try:
                        if "admin" in st.query_params:
                            del st.query_params["admin"]
                    except Exception:
                        pass
                    st.rerun()

        render_html(
            f"""
            <div style="text-align:center; font-size:0.82rem; padding: 8px; margin-top:6px; background: rgba(255,255,255,0.08); border-radius: 12px;">
                {STICKER_SAILBOAT_MINI}<br/>
                <b>Anh Minh Translate v7.0 (Claude/ChatGPT Hybrid Voice DSP)</b><br/>
                Tác giả: <b>Mai Văn Minh</b><br/>
                <i>Đóng tàu — СПбГМТУ (Xanh-Petecbua)</i>
            </div>
            """
        )

    render_brand_header(avatar_uri)

    tab1, tab2 = st.tabs(
        [
            "📝 TAB 1: DỊCH VĂN BẢN & TIN NHẮN SIÊU TỐC",
            "🎙️ TAB 2: GIẢNG ĐƯỜNG — THU ÂM HYBRID DSP SIÊU NHẠY & DỊCH THEO NGỮ CẢNH",
        ]
    )

    with tab1:
        top_bar_col1, top_bar_col2 = st.columns([2, 3])
        with top_bar_col1:
            direction = st.selectbox(
                "🧭 Chọn chiều dịch thuật:",
                options=[
                    "🇷🇺 Tiếng Nga ➔ 🇻🇳 Tiếng Việt",
                    "🇻🇳 Tiếng Việt ➔ 🇷🇺 Tiếng Nga",
                    "🌐 Đa chiều: Nga ↔ Anh ↔ Việt (Đối chiếu 3 ngôn ngữ)",
                ],
                index=0,
            )
        with top_bar_col2:
            render_html(
                f"""
                <div style="background:#FFFFFF; border:1.5px solid #BAE6FD; border-radius:14px; padding:12px 18px; margin-top:6px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 4px 12px rgba(2,132,199,0.05);">
                    <div style="display:flex; align-items:center; gap:10px;">
                        {STICKER_COMPASS_3D}
                        <div>
                            <div style="font-weight:800; color:#0369A1; font-size:0.94rem;">Chuyên ngành đang chọn: {selected_domain}</div>
                            <div style="font-size:0.82rem; color:#475569;">Chống nghẽn mạng 5 cổng • Hỗ trợ mọi Gemini Key & Tự động chuyển sang Đa luồng GTX</div>
                        </div>
                    </div>
                    {STICKER_SAILBOAT_MINI}
                </div>
                """
            )

        source_text = st.text_area(
            "✍️ Nhập văn bản, tài liệu chuyên ngành Đóng tàu hoặc tin nhắn Telegram/VK cần dịch:",
            key="input_text_area",
            height=150,
            placeholder="Dán tin nhắn tiếng Nga của giảng viên / phòng Visa / bạn học, hoặc câu tiếng Việt bạn muốn dịch sang tiếng Nga vào đây...",
        )

        act_col1, act_col2, _ = st.columns([2, 2, 4])
        with act_col1:
            translate_clicked = st.button("🚀 Dịch & Phân Tích Ngay (Siêu tốc)", type="primary", use_container_width=True)
        with act_col2:
            tts_quick_clicked = st.button("🔊 Phát âm văn bản gốc", type="secondary", use_container_width=True)

        if tts_quick_clicked and source_text.strip():
            has_cyrillic = bool(re.search(r"[а-яА-ЯёЁ]", source_text))
            lang_tts = "ru" if has_cyrillic else ("vi" if "Tiếng Việt ➔" in direction else "en")
            with st.spinner("Đang tạo giọng đọc..."):
                audio_bytes = generate_tts_audio(source_text, lang_tts)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

        if translate_clicked:
            if not source_text.strip():
                st.warning("⚠️ Vui lòng nhập nội dung văn bản cần dịch vào ô phía trên!")
            else:
                result_data: Optional[Dict] = None
                used_ai = False

                if clean_key_input:
                    with st.spinner("🧠 Đang phân tích bằng Gemini AI..."):
                        result_data, gemini_err = call_gemini_smart_translate(
                            api_key=clean_key_input,
                            source_text=source_text,
                            direction=direction,
                            domain=selected_domain,
                        )
                        if result_data:
                            used_ai = True
                        elif gemini_err and "không chính xác" in gemini_err.lower():
                            st.warning(f"⚠️ {gemini_err} Hệ thống đã tự động chuyển sang Chế độ Dịch Đa Luồng GTX Siêu Tốc!")

                if not result_data:
                    with st.spinner("⚡ Đang dịch đa luồng siêu tốc (GTX 5-Port)..."):
                        result_data = fallback_smart_translate(
                            source_text=source_text,
                            direction=direction,
                            domain=selected_domain,
                        )

                st.session_state["last_translation_result"] = result_data
                st.session_state["last_used_ai"] = used_ai

        if "last_translation_result" in st.session_state and st.session_state["last_translation_result"]:
            res = st.session_state["last_translation_result"]
            used_ai_badge = (
                "✨ Gemini AI Smart Mode"
                if st.session_state.get("last_used_ai")
                else "⚡ Đa Luồng Siêu Tốc (Parallel GTX 5-Port)"
            )

            render_html(
                f'<div class="nautical-divider">{STICKER_SAILBOAT_MINI} KẾT QUẢ DỊCH THUẬT & PHÂN TÍCH HỌC THUẬT {STICKER_SAILBOAT_MINI}</div>'
            )

            render_html(
                f"""
                <div class="ocean-card">
                    <div class="ocean-card-header">
                        <div class="ocean-card-title">{STICKER_COMPASS_3D} 1. Bản dịch tự nhiên nhất ({selected_domain})</div>
                        <span class="ocean-pill">{used_ai_badge}</span>
                    </div>
                    <div class="translation-main-text">{res.get("main_translation", "")}</div>
                </div>
                """
            )

            tri_col1, tri_col2, tri_col3 = st.columns(3)
            with tri_col1:
                ru_text = res.get("ru_version", "")
                render_html(
                    f"""
                    <div class="lang-card-header">🇷🇺 Bản Tiếng Nga (RU)</div>
                    <div class="lang-compare-box-ru">{ru_text if ru_text else "—"}</div>
                    """
                )
                if ru_text and st.button("🔊 Nghe Tiếng Nga", key="tts_ru_btn"):
                    ru_audio = generate_tts_audio(ru_text, "ru")
                    if ru_audio:
                        st.audio(ru_audio, format="audio/mp3")

            with tri_col2:
                vi_text = res.get("vi_version", "")
                render_html(
                    f"""
                    <div class="lang-card-header">🇻🇳 Bản Tiếng Việt (VI)</div>
                    <div class="lang-compare-box-vi">{vi_text if vi_text else "—"}</div>
                    """
                )
                if vi_text and st.button("🔊 Nghe Tiếng Việt", key="tts_vi_btn"):
                    vi_audio = generate_tts_audio(vi_text, "vi")
                    if vi_audio:
                        st.audio(vi_audio, format="audio/mp3")

            with tri_col3:
                en_text = res.get("en_version", "")
                render_html(
                    f"""
                    <div class="lang-card-header">🇬🇧 Đối chiếu Tiếng Anh (EN)</div>
                    <div class="lang-compare-box-en">{en_text if en_text else "—"}</div>
                    """
                )
                if en_text and st.button("🔊 Nghe Tiếng Anh", key="tts_en_btn"):
                    en_audio = generate_tts_audio(en_text, "en")
                    if en_audio:
                        st.audio(en_audio, format="audio/mp3")

            reply_variants = res.get("russian_reply_variants", {})
            if reply_variants:
                render_html(
                    f"""
                    <div class="ocean-card" style="margin-top:14px; margin-bottom:12px;">
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
                            <div class="tone-title">🎩 Lịch sự / Trang trọng (Ngôi «Вы» — Gửi Giáo sư, Giảng viên, Деканат)</div>
                            <div class="tone-ru">{formal_vy}</div>
                            <div class="tone-note">💡 {formal_note}</div>
                        </div>
                        """
                    )
                    if formal_vy and st.button("🔊 Nghe câu «Вы»", key="tts_vy_btn"):
                        vy_audio = generate_tts_audio(formal_vy, "ru")
                        if vy_audio:
                            st.audio(vy_audio, format="audio/mp3")

                with tone_c2:
                    casual_ty = reply_variants.get("casual_ty", "")
                    casual_note = reply_variants.get("casual_ty_vi_note", "")
                    render_html(
                        f"""
                        <div class="tone-box-casual">
                            <div class="tone-title">🤝 Thân mật / Tự nhiên (Ngôi «Ты» — Nhắn bạn học trên Telegram/VK)</div>
                            <div class="tone-ru">{casual_ty}</div>
                            <div class="tone-note">💡 {casual_note}</div>
                        </div>
                        """
                    )
                    if casual_ty and st.button("🔊 Nghe câu «Ты»", key="tts_ty_btn"):
                        ty_audio = generate_tts_audio(casual_ty, "ru")
                        if ty_audio:
                            st.audio(ty_audio, format="audio/mp3")

            slang_list = res.get("slang_explanations", [])
            if slang_list:
                slang_items_html = "".join(
                    f"""
                    <div class="slang-item">
                        <span class="slang-word">⚓ {s_item.get("term", "")}</span>
                        <span> (Dạng đầy đủ: <b>{s_item.get("full_form", "")}</b>)</span><br/>
                        <span style="color:#334155;">➔ {s_item.get("meaning_vi", "")}</span>
                    </div>
                    """
                    for s_item in slang_list
                )
            else:
                slang_items_html = (
                    '<div style="color:#475569; font-size:0.95rem;">'
                    "✅ Văn bản hiện tại sử dụng từ vựng tiêu chuẩn. Nếu câu tiếng Nga có chứa các từ lóng sinh viên "
                    "(như <b>препод, курсач, лаба, хвост, общага, стипуха...</b>), hệ thống sẽ tự động bóc tách và giải nghĩa chi tiết tại đây."
                    "</div>"
                )

            render_html(
                f"""
                <div class="ocean-card" style="margin-top:14px;">
                    <div class="ocean-card-header">
                        <div class="ocean-card-title">{STICKER_SAILBOAT_MINI} 3. Giải thích Từ lóng & Viết tắt Sinh viên Nga (Slang & Abbreviations)</div>
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
                        <td><b>{row.get("ru_accent", "")}</b></td>
                        <td>{row.get("en", "")}</td>
                        <td>{row.get("vi", "")}</td>
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
                                    <th>🇷🇺 Tiếng Nga (Có dấu trọng âm)</th>
                                    <th>🇬🇧 Tiếng Anh (Đối chiếu)</th>
                                    <th>🇻🇳 Tiếng Việt (Chuyên ngành)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_html}
                            </tbody>
                        </table>
                    </div>
                    """
                )

            if res.get("study_tip"):
                render_html(
                    f"""
                    <div class="ocean-card" style="background: linear-gradient(135deg, #E0F2FE 0%, #F0F9FF 100%); border-left: 6px solid #0284C7;">
                        <div style="font-weight:800; color:#0369A1; margin-bottom:4px;">🎓 Góc Cố vấn Học tập tại Nga:</div>
                        <div style="color:#0F172A; font-weight:500;">{res.get("study_tip")}</div>
                    </div>
                    """
                )

    with tab2:
        realtime_html = build_realtime_lecture_component(
            gemini_api_key=clean_key_input,
            selected_domain=selected_domain,
        )
        components.html(realtime_html, height=725, scrolling=False)

        render_html(
            f'<div class="nautical-divider">{STICKER_ANCHOR_3D} THU ÂM TRỰC TIẾP / TẢI FILE GHI ÂM BÀI GIẢNG (WHISPER RMS AUTO-GAIN X12.0) {STICKER_ANCHOR_3D}</div>'
        )

        up_col1, up_col2 = st.columns([1, 1])
        with up_col1:
            file_speech_lang = st.selectbox(
                "🗣️ Ngôn ngữ nói / file ghi âm:",
                options=[
                    ("ru-RU", "🇷🇺 Tiếng Nga (ru-RU)"),
                    ("vi-VN", "🇻🇳 Tiếng Việt (vi-VN)"),
                    ("en-US", "🇬🇧 Tiếng Anh (en-US)"),
                ],
                format_func=lambda x: x[1],
                index=0,
            )[0]

            file_target_lang = st.selectbox(
                "🎯 Dịch nội dung âm thanh sang:",
                options=[
                    ("vi", "🇻🇳 Tiếng Việt"),
                    ("ru", "🇷🇺 Tiếng Nga"),
                    ("en", "🇬🇧 Tiếng Anh"),
                ],
                format_func=lambda x: x[1],
                index=0,
            )[0]

            python_dsp_gain = st.slider(
                "🎚️ Độ nhạy khuếch đại RMS cho File / Bản thu trực tiếp:",
                min_value=2.0,
                max_value=15.0,
                value=12.0,
                step=0.5,
                help="Tự động chuẩn hóa năng lượng RMS và kích tiếng nói nhỏ lên tới 12x–15x như tiền xử lý âm thanh của Whisper/ChatGPT.",
            )

        with up_col2:
            recorded_mic = None
            if hasattr(st, "audio_input"):
                recorded_mic = st.audio_input(
                    "🎙️ Thu âm trực tiếp trên Điện thoại / Máy tính (Tự động kích độ nhạy RMS x12 & dịch ngay):"
                )
            uploaded_audio = st.file_uploader(
                "📤 Hoặc tải file âm thanh bài giảng (.wav):",
                type=["wav"],
            )

        audio_source_bytes: Optional[bytes] = None
        if recorded_mic is not None:
            audio_source_bytes = recorded_mic.getvalue()
        elif uploaded_audio is not None:
            audio_source_bytes = uploaded_audio.getvalue()

        if audio_source_bytes:
            with st.spinner(f"⏳ Đang xử lý khuếch đại RMS Auto-Gain x{python_dsp_gain:.1f} & nhận diện giọng nói..."):
                transcript_text, translated_text, err = transcribe_and_translate_audio_bytes(
                    audio_bytes=audio_source_bytes,
                    source_lang_speech=file_speech_lang,
                    target_lang_trans=file_target_lang,
                    gemini_api_key=clean_key_input,
                    selected_domain=selected_domain,
                    max_gain_factor=python_dsp_gain,
                )
                if err:
                    st.error(f"⚠️ {err}")
                else:
                    render_html(
                        f"""
                        <div class="ocean-card">
                            <div class="ocean-card-header">
                                <div class="ocean-card-title">✅ Kết quả Nhận diện Giọng nói DSP & Dịch thuật</div>
                                <span class="ocean-pill">{file_speech_lang} ➔ {file_target_lang.upper()}</span>
                            </div>
                            <p style="color:#0369A1; font-weight:700;">🗣️ Lời nói nhận diện được (Transcript):</p>
                            <div class="translation-main-text" style="margin-bottom:14px;">{transcript_text}</div>
                            <p style="color:#0369A1; font-weight:700;">🌊 Bản dịch hoàn chỉnh:</p>
                            <div class="translation-main-text" style="border-left-color:#06B6D4; background:#F0F9FF; color:#0369A1 !important; font-weight:700;">
                                {translated_text}
                            </div>
                        </div>
                        """
                    )

                    txt_report = (
                        f"BẢN DỊCH GHI ÂM — ANH MINH TRANSLATE\n"
                        f"Tác giả: Mai Văn Minh — Đóng tàu, СПбГМТУ\n"
                        f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"----------------------------------------\n"
                        f"Lời gốc ({file_speech_lang}):\n{transcript_text}\n\n"
                        f"Bản dịch ({file_target_lang}):\n{translated_text}\n"
                    )
                    st.download_button(
                        label="📥 Tải kết quả dịch file ghi âm (.txt)",
                        data=txt_report.encode("utf-8"),
                        file_name="Ket_Qua_Ghi_Am_AnhMinhTranslate.txt",
                        mime="text/plain",
                    )


if __name__ == "__main__":
    main()
