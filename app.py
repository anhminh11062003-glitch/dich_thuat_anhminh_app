"""
Anh Minh Translate — Công cụ dịch thuật & hỗ trợ học tập cho sinh viên Việt tại Nga
Tác giả: Mai Văn Minh — СПбГМТУ (Xanh-Petecbua)
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
# 1. CẤU HÌNH TRANG & HẰNG SỐ
# ==============================================================================
st.set_page_config(
    page_title="Anh Minh Translate",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"
AUTHOR_NOTIFICATION_EMAIL = "anhminh11062003@gmail.com"
MAX_MEM_CACHE_SIZE = 250
MAX_HISTORY_ITEMS = 25


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
                transition: background 0.15s ease, border-color 0.15s ease;
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
# 2. LƯU TRỮ RIÊNG TƯ TRÊN TRÌNH DUYỆT (LOCALSTORAGE) & THÔNG BÁO EMAIL
# ==============================================================================
def consume_bootstrap_query_params() -> Tuple[str, Dict[str, str]]:
    recovered_key = ""
    recovered_profile: Dict[str, str] = {}
    had_qp = False
    try:
        qp_key = st.query_params.get("_am_k", "")
        if qp_key:
            recovered_key = clean_api_key(qp_key)
            del st.query_params["_am_k"]
            had_qp = True

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
    return recovered_key, recovered_profile


def inject_localstorage_sync(
    action: str = "load_all",
    key_to_save: str = "",
    student_profile: Optional[Dict[str, str]] = None,
) -> None:
    safe_key = json.dumps(clean_api_key(key_to_save))
    safe_profile = json.dumps(student_profile or {}, ensure_ascii=False)

    if action == "save_key":
        components.html(
            f'<script>try{{localStorage.setItem("anhminh_saved_gemini_key",{safe_key});}}catch(e){{}}</script>',
            height=0,
        )
    elif action == "delete_key":
        components.html(
            '<script>try{localStorage.removeItem("anhminh_saved_gemini_key");}catch(e){}</script>',
            height=0,
        )
    elif action == "save_profile":
        components.html(
            f'<script>try{{localStorage.setItem("anhminh_saved_student_profile",JSON.stringify({safe_profile}));}}catch(e){{}}</script>',
            height=0,
        )
    else:
        components.html(
            """
            <script>
            try {
                if (!sessionStorage.getItem("anhminh_bootstrapped_v9")) {
                    sessionStorage.setItem("anhminh_bootstrapped_v9", "1");
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
                    if (changed) window.parent.location.replace(url.toString());
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
# 3. TỪ ĐIỂN TIẾNG LÓNG SINH VIÊN TẠI NGA (30 TỪ THỰC CHIẾN)
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
# 4. CSS TỐI GIẢN CHUẨN EDITORIAL (TƯƠNG PHẢN TUYỆT ĐỐI — PHONG CÁCH NHATANH.AI)
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
            --bg-page: #FAF9F6;
            --bg-surface: #FFFFFF;
            --bg-subtle: #F4F3EE;
            --text-primary: #18181B;
            --text-secondary: #52525B;
            --text-muted: #71717A;
            --border-light: #E5E4DF;
            --border-strong: #D4D4D8;
            --accent: #18181B;
            --link: #1D4ED8;
            color-scheme: light !important;
        }}

        /* ÉP NỀN SÁNG & CHỮ TỐI ĐỒNG NHẤT — CHỐNG LỖI CHỮ TRẮNG TRÊN NỀN TRẮNG */
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
            max-width: 940px !important;
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
        }}

        /* CHỮ CHUNG TRONG MAIN VÀ SIDEBAR */
        .main p, .main label, .main h1, .main h2, .main h3, .main h4,
        .main div[data-testid="stWidgetLabel"] p,
        .main div[data-testid="stMarkdownContainer"] p,
        .main div[data-testid="stMarkdownContainer"] li,
        .main div[data-testid="stCaptionContainer"] p {{
            color: #18181B !important;
        }}

        .main div[data-testid="stCaptionContainer"] p {{
            color: #52525B !important;
            font-size: 0.85rem !important;
        }}

        /* SIDEBAR SÁNG TINH TẾ — KHÔNG DÙNG NỀN TỐI GÂY LỖI MÀU CHỮ */
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

        /* INPUT, TEXTAREA, SELECTBOX: NỀN TRẮNG + CHỮ ĐEN RÕ NÉT */
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
            color: #18181B !important;
        }}

        /* NÚT BẤM TƯƠNG PHẢN CAO */
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
            border-color: #27272A !important;
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
            border-color: #A1A1AA !important;
        }}

        /* TABS TỐI GIẢN */
        div[data-testid="stTabs"] div[role="tablist"] {{
            gap: 6px;
            border-bottom: 1px solid #E5E4DF !important;
            padding-bottom: 8px;
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

        /* EXPANDER & FILE UPLOADER */
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

        /* HEADER TỐI GIẢN */
        .minimal-header {{
            padding-bottom: 18px;
            margin-bottom: 20px;
            border-bottom: 1px solid #E5E4DF;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .minimal-title {{
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: #18181B;
            margin: 0;
        }}
        .minimal-meta {{
            font-size: 0.88rem;
            color: #52525B;
            font-weight: 400;
        }}

        /* THẺ NỘI DUNG SẠCH SẼ */
        .clean-card {{
            background-color: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 12px;
            padding: 20px 22px;
            margin-top: 14px;
            margin-bottom: 14px;
        }}
        .clean-label {{
            font-size: 0.82rem;
            font-weight: 600;
            color: #52525B;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .clean-result-text {{
            font-size: 1.08rem;
            line-height: 1.72;
            color: #18181B;
            font-weight: 500;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .tone-card {{
            background-color: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 12px;
            padding: 16px 18px;
            height: 100%;
        }}
        .tone-heading {{
            font-size: 0.84rem;
            font-weight: 600;
            color: #52525B;
            margin-bottom: 8px;
        }}
        .tone-body {{
            font-size: 1.02rem;
            font-weight: 600;
            color: #18181B;
            line-height: 1.55;
            margin-bottom: 8px;
        }}
        .tone-sub {{
            font-size: 0.86rem;
            color: #52525B;
            line-height: 1.5;
        }}

        .clean-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
            margin-top: 6px;
        }}
        .clean-table th {{
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid #D4D4D8;
            color: #52525B;
            font-weight: 600;
            background-color: #FAF9F6;
        }}
        .clean-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #E5E4DF;
            color: #18181B;
            vertical-align: top;
        }}

        .note-callout {{
            background-color: #F4F3EE;
            border-left: 3px solid #18181B;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-top: 12px;
            font-size: 0.9rem;
            color: #18181B;
            line-height: 1.6;
        }}

        .flashcard-minimal {{
            background-color: #FFFFFF;
            border: 1px solid #D4D4D8;
            border-radius: 14px;
            padding: 36px 24px;
            text-align: center;
            margin: 12px 0;
        }}
        .flashcard-word {{
            font-size: 1.75rem;
            font-weight: 700;
            color: #18181B;
            letter-spacing: -0.02em;
        }}
        .flashcard-back {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #E5E4DF;
            font-size: 1.12rem;
            font-weight: 600;
            color: #18181B;
        }}

        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 1rem 0.85rem 2.5rem 0.85rem !important;
            }}
            .minimal-title {{ font-size: 1.32rem; }}
            .clean-card {{ padding: 15px 16px; }}
        }}
        </style>
        """
    )


# ==============================================================================
# 5. ĐỘNG CƠ DỊCH TỰ ĐỘNG NHẬN DIỆN NGỮ CẢNH + CHIA ĐOẠN + OCR VISION
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
        if re.search(pattern, text_lower) and w not in seen_words:
            detected.append(item)
            seen_words.add(w)
    return detected


def chunk_text_smart(text: str, max_chars: int = 1100) -> List[str]:
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

    try:
        req1 = urllib.request.Request(
            "https://translate.googleapis.com/translate_a/single?client=gtx&dt=t",
            data=post_body, headers=headers_form, method="POST",
        )
        with urllib.request.urlopen(req1, timeout=7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data and isinstance(data[0], list):
                chunks = [c[0] for c in data[0] if c and c[0]]
                if chunks:
                    return "".join(chunks)
    except Exception:
        pass

    try:
        req2 = urllib.request.Request(
            "https://translate.google.com/translate_a/single?client=at&dt=t&dj=1",
            data=post_body, headers=headers_form, method="POST",
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

    try:
        req3 = urllib.request.Request(
            "https://clients5.google.com/translate_a/t?client=dict-chrome-ex",
            data=post_body, headers=headers_form, method="POST",
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

    if len(cleaned) <= 480:
        try:
            src_mm = "ru" if src == "auto" else src
            mm_url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(cleaned)}&langpair={src_mm}|{tgt}"
            req4 = urllib.request.Request(mm_url, headers={"User-Agent": headers_form["User-Agent"]})
            with urllib.request.urlopen(req4, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                t = data.get("responseData", {}).get("translatedText", "")
                if t and "MYMEMORY WARNING" not in t.upper():
                    return t
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

    return "Máy chủ dịch miễn phí đang tạm bận. Vui lòng thử lại sau vài giây hoặc nhập Gemini API Key ở thanh bên."


def discover_available_gemini_models(api_key: str) -> List[str]:
    clean_k = clean_api_key(api_key)
    preferred = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"]
    if not clean_k:
        return preferred

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
                        if "gemini" in short_name and "embedding" not in short_name and short_name not in discovered:
                            discovered.append(short_name)
                if discovered:
                    break
        except Exception:
            pass

    if discovered:
        ordered = [p for p in preferred if p in discovered] + [d for d in discovered if d not in preferred]
        st.session_state[cache_name] = ordered
        return ordered
    return preferred


def call_gemini_multimodal_rest(
    api_key: str,
    parts: List[Dict[str, Any]],
    expect_json: bool = True,
    temperature: float = 0.2,
    timeout_sec: int = 25,
) -> Tuple[Optional[str], Optional[str]]:
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return None, "Empty API Key"

    last_error = ""
    for model_name in discover_available_gemini_models(clean_k)[:5]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={urllib.parse.quote(clean_k)}"
        gen_cfg: Dict[str, Any] = {"temperature": temperature}
        if expect_json:
            gen_cfg["responseMimeType"] = "application/json"

        payload = {"contents": [{"parts": parts}], "generationConfig": gen_cfg}
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
                            return resp_parts[0]["text"], None
            except urllib.error.HTTPError as http_err:
                err_body = ""
                try:
                    err_body = http_err.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                last_error = f"HTTP {http_err.code}"
                if "API_KEY_INVALID" in err_body:
                    return None, "Gemini API Key không hợp lệ."
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


def call_gemini_smart_translate(api_key: str, source_text: str, direction: str) -> Tuple[Optional[Dict], Optional[str]]:
    system_prompt = f"""
Bạn là chuyên gia dịch thuật Nga – Việt – Anh cho sinh viên Việt Nam đang học tập và sinh sống tại Nga.
Hãy TỰ ĐỘNG nhận diện ngữ cảnh văn bản (kỹ thuật/đóng tàu, bài giảng đại học, thủ tục hành chính/visa, hay tin nhắn đời thường/tiếng lóng sinh viên) và dịch theo chiều "{direction}".
CHỈ TRẢ VỀ đúng 1 đối tượng JSON hợp lệ:
{{
  "main_translation": "Bản dịch tự nhiên, chuẩn thuật ngữ và đúng ngữ cảnh nhất",
  "ru_version": "Bản tiếng Nga tương ứng",
  "vi_version": "Bản tiếng Việt tương ứng",
  "en_version": "Bản tiếng Anh đối chiếu",
  "slang_explanations": [
    {{"term": "Từ lóng/viết tắt (nếu có trong câu)", "full_form": "Dạng đầy đủ", "meaning_vi": "Giải nghĩa ngắn gọn"}}
  ],
  "vocabulary_table": [
    {{"ru_accent": "Từ khóa tiếng Nga có dấu trọng âm \\u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu tiếng Nga lịch sự ngôi «Вы» (gửi giảng viên / phòng khoa)",
    "formal_vy_vi_note": "Dịch nghĩa tiếng Việt ngắn gọn",
    "casual_ty": "Câu tiếng Nga tự nhiên ngôi «Ты» (nhắn bạn học)",
    "casual_ty_vi_note": "Dịch nghĩa tiếng Việt ngắn gọn"
  }},
  "context_note": "1-2 câu ghi chú ngắn gọn về ngữ pháp, sắc thái hoặc thuật ngữ quan trọng trong đoạn này."
}}
"""
    raw_text, err = call_gemini_multimodal_rest(
        api_key=api_key,
        parts=[{"text": f"{system_prompt}\n\n---\nVăn bản:\n{source_text}"}],
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
    api_key: str, image_bytes: bytes, mime_type: str, direction: str
) -> Tuple[Optional[Dict], Optional[str]]:
    b64_img = base64.b64encode(image_bytes).decode("utf-8")
    prompt = f"""
Bạn là trợ lý học thuật Nga – Việt – Anh cho sinh viên tại Nga.
Đọc chính xác toàn bộ chữ trong ảnh (slide bài giảng, bảng viết, tài liệu hoặc tin nhắn), tự nhận diện ngữ cảnh và dịch theo chiều "{direction}".
CHỈ TRẢ VỀ JSON:
{{
  "extracted_text": "Văn bản gốc đọc được từ ảnh",
  "main_translation": "Bản dịch tự nhiên, chuẩn xác",
  "ru_version": "Bản tiếng Nga",
  "vi_version": "Bản tiếng Việt",
  "en_version": "Bản tiếng Anh đối chiếu",
  "slang_explanations": [],
  "vocabulary_table": [
    {{"ru_accent": "Từ khóa tiếng Nga có dấu trọng âm \\u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu trao đổi lịch sự ngôi «Вы» liên quan đến nội dung ảnh",
    "formal_vy_vi_note": "Nghĩa tiếng Việt",
    "casual_ty": "Câu trao đổi ngắn gọn ngôi «Ты» với bạn học",
    "casual_ty_vi_note": "Nghĩa tiếng Việt"
  }},
  "context_note": "Tóm tắt ngắn 1-2 ý chính cần nhớ từ ảnh."
}}
"""
    raw_text, err = call_gemini_multimodal_rest(
        api_key=api_key,
        parts=[{"text": prompt}, {"inlineData": {"mimeType": mime_type, "data": b64_img}}],
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
            if not text:
                return None, "Tệp PDF này là ảnh scan. Hãy chụp ảnh trang cần dịch và tải vào mục Ảnh."
            return text, None
        except Exception as exc:
            return None, f"Lỗi đọc tệp .pdf: {exc}"

    return None, "Định dạng tệp chưa được hỗ trợ."


def fallback_smart_translate(source_text: str, direction: str) -> Dict:
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

    if direction == DIRECTION_OPTIONS[0]:
        formal_vy_full = "Здравствуйте! Спасибо за информацию, я обязательно всё учту и выполню вовремя."
        formal_note = "Xin chào! Cảm ơn vì thông tin, em nhất định sẽ lưu ý và hoàn thành đúng hạn."
        casual_ty_full = "Привет! Понял, спасибо за инфу!"
        casual_note = "Chào cậu! Mình hiểu rồi, cảm ơn vì thông tin nhé!"
    else:
        base_ru = ru_ver.strip()
        f_vy = re.sub(r"\bты\b", "Вы", base_ru, flags=re.IGNORECASE)
        f_vy = re.sub(r"\bтебя\b", "Вас", f_vy, flags=re.IGNORECASE)
        f_vy = re.sub(r"\bтебе\b", "Вам", f_vy, flags=re.IGNORECASE)
        f_vy = re.sub(r"\bпривет\b", "Здравствуйте", f_vy, flags=re.IGNORECASE)
        formal_vy_full = f_vy if f_vy.lower().startswith(("здравствуйте", "добрый день", "уважаем")) else f"Здравствуйте! {f_vy}"
        formal_note = "Dùng khi nhắn cho giảng viên, giáo sư hoặc văn phòng khoa (Деканат)."

        c_ty = re.sub(r"\bВы\b", "ты", base_ru)
        c_ty = re.sub(r"\bВас\b", "тебя", c_ty)
        c_ty = re.sub(r"\bВам\b", "тебе", c_ty)
        c_ty = re.sub(r"\bЗдравствуйте\b", "Привет", c_ty, flags=re.IGNORECASE)
        casual_ty_full = c_ty if c_ty.lower().startswith(("привет", "слушай")) else f"Привет! {c_ty}"
        casual_note = "Dùng khi nhắn cho bạn cùng lớp hoặc bạn cùng ký túc xá."

    vocab_list = [
        {"ru_accent": f"{s['accent']} ({s['full']})", "en": s["en"], "vi": s["vi"]}
        for s in detected_slang
    ]
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
        "context_note": "Mở thanh bên trái và dán Gemini API Key (miễn phí) để tự động trích xuất từ vựng chuyên ngành, ghi chú ngữ pháp và dịch ảnh slide.",
    }


# ==============================================================================
# 6. GIAO DIỆN NGHE GIẢNG REAL-TIME TỐI GIẢN (TRẮNG – ĐEN TƯƠNG PHẢN CAO)
# ==============================================================================
def build_realtime_lecture_component(gemini_api_key: str = "") -> str:
    safe_gemini_key = json.dumps(clean_api_key(gemini_api_key))

    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            * {{ box-sizing: border-box; font-family: 'Inter', -apple-system, sans-serif; }}
            body {{ margin: 0; padding: 2px; background: transparent; color: #18181B; }}
            .wrap {{
                background: #FFFFFF;
                border: 1px solid #E5E4DF;
                border-radius: 12px;
                padding: 16px 18px;
            }}
            .toolbar {{
                display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
                gap: 10px; padding-bottom: 12px; border-bottom: 1px solid #E5E4DF;
            }}
            .group {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }}
            select {{
                padding: 7px 10px; border-radius: 8px; border: 1px solid #D4D4D8;
                background: #FFFFFF; color: #18181B; font-size: 13px; font-weight: 500; cursor: pointer;
            }}
            .btn {{
                padding: 7px 13px; border-radius: 8px; font-size: 13px; font-weight: 500;
                border: 1px solid #D4D4D8; background: #FFFFFF; color: #18181B; cursor: pointer;
            }}
            .btn:hover:not(:disabled) {{ background: #F4F3EE; }}
            .btn-primary {{ background: #18181B; color: #FFFFFF; border-color: #18181B; }}
            .btn-primary:hover:not(:disabled) {{ background: #27272A; }}
            .btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
            .status-row {{
                display: flex; align-items: center; justify-content: space-between; gap: 10px;
                margin-top: 12px; padding: 9px 12px; background: #FAF9F6;
                border: 1px solid #E5E4DF; border-radius: 8px; font-size: 13px; color: #52525B;
            }}
            .status-left {{ display: flex; align-items: center; gap: 8px; }}
            .dot {{ width: 9px; height: 9px; border-radius: 50%; background: #A1A1AA; flex-shrink: 0; }}
            .dot.active {{ background: #16A34A; }}
            .live-box {{
                margin-top: 12px; padding: 12px 14px; background: #FAF9F6;
                border: 1px solid #D4D4D8; border-radius: 10px;
            }}
            .live-label {{ font-size: 12px; font-weight: 600; color: #52525B; margin-bottom: 6px; }}
            .live-text {{ font-size: 15px; font-weight: 500; color: #18181B; line-height: 1.5; min-height: 22px; }}
            .manual-input {{
                width: 100%; margin-top: 8px; padding: 7px 10px; border-radius: 8px;
                border: 1px solid #D4D4D8; background: #FFFFFF; color: #18181B; font-size: 13px; outline: none;
            }}
            .manual-input:focus {{ border-color: #18181B; }}
            .summary-box {{
                display: none; margin-top: 12px; padding: 14px 16px; background: #F4F3EE;
                border-left: 3px solid #18181B; border-radius: 0 8px 8px 0;
                font-size: 14px; color: #18181B; line-height: 1.6; white-space: pre-wrap;
                max-height: 210px; overflow-y: auto;
            }}
            .stream {{
                margin-top: 12px; height: 320px; overflow-y: auto;
                border: 1px solid #E5E4DF; border-radius: 10px; padding: 12px; background: #FFFFFF;
            }}
            .item {{
                padding: 12px 14px; border-bottom: 1px solid #E5E4DF;
            }}
            .item:last-child {{ border-bottom: none; }}
            .meta {{ font-size: 12px; color: #71717A; margin-bottom: 4px; }}
            .src {{ font-size: 14px; color: #18181B; line-height: 1.5; margin-bottom: 6px; }}
            .tgt {{ font-size: 15px; font-weight: 600; color: #18181B; background: #FAF9F6; padding: 8px 12px; border-radius: 8px; line-height: 1.5; }}
            .empty {{ text-align: center; color: #71717A; padding: 64px 16px; font-size: 14px; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="toolbar">
                <div class="group">
                    <select id="sourceLang">
                        <option value="ru-RU" selected>Nghe: Tiếng Nga</option>
                        <option value="vi-VN">Nghe: Tiếng Việt</option>
                        <option value="en-US">Nghe: Tiếng Anh</option>
                    </select>
                    <select id="targetLang">
                        <option value="vi" selected>Dịch sang: Tiếng Việt</option>
                        <option value="ru">Dịch sang: Tiếng Nga</option>
                        <option value="en">Dịch sang: Tiếng Anh</option>
                    </select>
                    <select id="captureModeSelect" onchange="onModeChange()">
                        <option value="webspeech" selected>Thu trực tiếp</option>
                        <option value="aidsp">AI Audio (Gemini)</option>
                    </select>
                </div>
                <div class="group">
                    <button id="btnStart" class="btn btn-primary" onclick="startRecognition()">Bắt đầu nghe</button>
                    <button id="btnPause" class="btn" onclick="stopRecognition()" disabled>Tạm dừng</button>
                    <button id="btnFlush" class="btn" onclick="forceCommitInterim()">Ngắt câu</button>
                    <button id="btnSummary" class="btn" onclick="summarizeLectureAI()">Tóm tắt AI</button>
                    <button id="btnCopyAll" class="btn" onclick="copyFullTranscript()">Sao chép</button>
                    <button id="btnDownload" class="btn" onclick="downloadTranscript()">Tải .txt</button>
                    <button id="btnClear" class="btn" onclick="clearTranscript()">Xóa</button>
                </div>
            </div>

            <div class="status-row">
                <div class="status-left">
                    <div id="statusDot" class="dot"></div>
                    <span id="statusText">Sẵn sàng. Chọn đúng ngôn ngữ giảng viên nói rồi bấm Bắt đầu nghe.</span>
                </div>
                <span id="countBadge">0 câu</span>
            </div>

            <div class="live-box">
                <div class="live-label">Đang nhận diện</div>
                <div id="interimText" class="live-text">...</div>
                <input type="text" id="manualSentenceInput" class="manual-input"
                    placeholder="Có thể sửa nhanh câu đang nghe hoặc gõ trực tiếp rồi bấm Enter..."
                    onkeydown="if(event.key === 'Enter') {{ event.preventDefault(); forceCommitInterim(); }}" />
            </div>

            <div id="aiSummaryPanel" class="summary-box"></div>

            <div id="subtitleStream" class="stream">
                <div id="emptyHint" class="empty">
                    Nội dung bài giảng và bản dịch theo ngữ cảnh sẽ hiển thị tại đây.<br/>
                    Khi kết thúc buổi học, bấm <b>Tóm tắt AI</b> hoặc <b>Tải .txt</b> để lưu lại ôn thi.
                </div>
            </div>
        </div>

        <script>
            try {{
                if (window.frameElement) window.frameElement.setAttribute("allow", "microphone *; autoplay *; clipboard-write *");
            }} catch (e) {{}}

            const GEMINI_API_KEY = {safe_gemini_key};
            const SLANG_MAP = {{
                "препод": "преподаватель", "курсач": "курсовая работа", "лаба": "лабораторная работа",
                "хвост": "академическая задолженность", "зачетка": "зачётная книжка",
                "общага": "общежитие", "стипуха": "стипендия", "инфа": "информация", "преза": "презентация"
            }};

            function escapeHtml(str) {{
                return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
            }}

            let recognition = null, isListening = false, lectureHistory = [];
            let committedResultIndex = 0, currentActiveSentence = "", latestResultsLength = 0;
            let lastCommittedNorm = "", lastCommitTs = 0, silenceTimer = null;
            let audioCtx = null, micStream = null, scriptProcessor = null;
            let pcmRingBuffer = [], vadActive = false, vadStart = 0, vadLast = 0, isTranscribing = false, noiseFloor = 0.008;
            let userScrolledUp = false;

            const statusDot = document.getElementById("statusDot");
            const statusText = document.getElementById("statusText");
            const countBadge = document.getElementById("countBadge");
            const interimText = document.getElementById("interimText");
            const manualInput = document.getElementById("manualSentenceInput");
            const streamEl = document.getElementById("subtitleStream");
            const btnStart = document.getElementById("btnStart");
            const btnPause = document.getElementById("btnPause");
            const srcLang = document.getElementById("sourceLang");
            const tgtLang = document.getElementById("targetLang");
            const modeSelect = document.getElementById("captureModeSelect");
            const summaryPanel = document.getElementById("aiSummaryPanel");

            manualInput.addEventListener("input", () => {{
                currentActiveSentence = manualInput.value;
                interimText.innerText = currentActiveSentence || "...";
            }});

            streamEl.addEventListener("scroll", () => {{
                userScrolledUp = (streamEl.scrollHeight - streamEl.scrollTop - streamEl.clientHeight) > 55;
            }});

            function onModeChange() {{
                if (isListening) {{ stopRecognition(); setTimeout(startRecognition, 180); }}
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

            function expandSlang(text, srcShort) {{
                if (srcShort !== "ru") return text;
                let out = text;
                Object.keys(SLANG_MAP).forEach(k => {{ out = out.replace(new RegExp("\\\\b" + k + "\\\\b", "gi"), SLANG_MAP[k]); }});
                return out;
            }}

            async function translateWithContext(sentence, srcCode, tgt) {{
                const srcShort = srcCode.split("-")[0];
                if (srcShort === tgt) return sentence;
                const clean = expandSlang(sentence.trim(), srcShort);
                const recent = lectureHistory.slice(-3);

                if (GEMINI_API_KEY && GEMINI_API_KEY.length > 10) {{
                    try {{
                        const ctx = recent.length ? recent.map((it, i) => `[${{i+1}}] ${{it.source}} -> ${{it.translated}}`).join("\\n") : "Câu mở đầu.";
                        const prompt = `Dịch câu bài giảng sau từ ${{srcShort}} sang ${{tgt}} tự nhiên, chuẩn xác theo ngữ cảnh các câu trước. Chỉ trả về câu dịch:\\nNgữ cảnh:\\n${{ctx}}\\nCâu mới: ${{clean}}`;
                        const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`, {{
                            method: "POST", headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({{ contents: [{{ parts: [{{ text: prompt }}] }}], generationConfig: {{ temperature: 0.15 }} }})
                        }});
                        if (res.ok) {{
                            const d = await res.json();
                            const out = d?.candidates?.[0]?.content?.parts?.[0]?.text;
                            if (out && out.trim()) return out.trim();
                        }}
                    }} catch (e) {{}}
                }}

                try {{
                    const res = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=${{srcShort}}&tl=${{tgt}}&dt=t&q=${{encodeURIComponent(clean)}}`);
                    const d = await res.json();
                    if (Array.isArray(d) && Array.isArray(d[0])) return d[0].map(it => it[0]).join("");
                }} catch (e) {{}}
                return "Đang chờ kết nối dịch...";
            }}

            function appendCard(original, srcCode, tgt) {{
                const cleanOrig = formatSentence(original);
                const norm = normalizeText(cleanOrig);
                if (!norm) return;
                const now = Date.now();
                if (norm === lastCommittedNorm && (now - lastCommitTs) < 7000) return;
                lastCommittedNorm = norm; lastCommitTs = now;

                const empty = document.getElementById("emptyHint");
                if (empty) empty.style.display = "none";

                const timeStr = new Date().toLocaleTimeString("vi-VN", {{ hour: "2-digit", minute: "2-digit", second: "2-digit" }});
                const idx = lectureHistory.length + 1;
                const id = "sub-" + now + "-" + Math.floor(Math.random() * 1000);

                const el = document.createElement("div");
                el.className = "item";
                el.innerHTML = `<div class="meta">#${{idx}} · ${{escapeHtml(timeStr)}}</div><div class="src">${{escapeHtml(cleanOrig)}}</div><div id="${{id}}" class="tgt">Đang dịch...</div>`;
                streamEl.appendChild(el);
                if (!userScrolledUp) streamEl.scrollTop = streamEl.scrollHeight;

                translateWithContext(cleanOrig, srcCode, tgt).then(tr => {{
                    const targetEl = document.getElementById(id);
                    if (targetEl) targetEl.innerText = tr;
                    lectureHistory.push({{ time: timeStr, source: cleanOrig, translated: tr }});
                    countBadge.innerText = lectureHistory.length + " câu";
                    if (!userScrolledUp) streamEl.scrollTop = streamEl.scrollHeight;
                }});
            }}

            function forceCommitInterim() {{
                if (silenceTimer) {{ clearTimeout(silenceTimer); silenceTimer = null; }}
                const cand = (manualInput.value || "").trim() || currentActiveSentence.trim();
                if (cand) {{
                    committedResultIndex = latestResultsLength;
                    currentActiveSentence = "";
                    manualInput.value = "";
                    interimText.innerText = "...";
                    appendCard(cand, srcLang.value, tgtLang.value);
                }} else {{
                    manualInput.focus();
                }}
            }}

            async function summarizeLectureAI() {{
                if (!lectureHistory.length) {{ alert("Chưa có nội dung để tóm tắt."); return; }}
                summaryPanel.style.display = "block";
                if (!GEMINI_API_KEY || GEMINI_API_KEY.length < 10) {{
                    summaryPanel.innerText = "Tính năng Tóm tắt AI cần nhập Gemini API Key (miễn phí) ở thanh bên trái.";
                    return;
                }}
                summaryPanel.innerText = "Đang tóm tắt bài giảng...";
                const joined = lectureHistory.map((it, i) => `${{i+1}}. ${{it.source}} (${{it.translated}})`).join("\\n");
                const prompt = `Tóm tắt bài giảng sau thành 3-5 ý chính bằng tiếng Việt và liệt kê tối đa 5 thuật ngữ Nga-Việt quan trọng nhất:\\n${{joined.slice(0, 12000)}}`;
                try {{
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`, {{
                        method: "POST", headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ contents: [{{ parts: [{{ text: prompt }}] }}], generationConfig: {{ temperature: 0.25 }} }})
                    }});
                    if (res.ok) {{
                        const d = await res.json();
                        summaryPanel.innerText = (d?.candidates?.[0]?.content?.parts?.[0]?.text || "Không tạo được tóm tắt.").trim();
                        return;
                    }}
                }} catch (e) {{}}
                summaryPanel.innerText = "Không thể kết nối Gemini AI lúc này.";
            }}

            function copyFullTranscript() {{
                if (!lectureHistory.length) return;
                const text = lectureHistory.map((it, i) => `[${{i+1}} - ${{it.time}}]\\n${{it.source}}\\n${{it.translated}}`).join("\\n\\n");
                navigator.clipboard?.writeText(text).then(() => {{
                    const b = document.getElementById("btnCopyAll");
                    b.innerText = "Đã sao chép";
                    setTimeout(() => b.innerText = "Sao chép", 1500);
                }});
            }}

            function encodeWavBase64(samples, inputRate) {{
                const targetRate = 16000, ratio = inputRate / targetRate;
                const outLen = Math.max(1, Math.floor(samples.length / ratio));
                const res = new Float32Array(outLen);
                let sumSq = 0;
                for (let i = 0; i < outLen; i++) {{
                    const s = samples[Math.min(samples.length - 1, Math.floor(i * ratio))];
                    res[i] = s; sumSq += s * s;
                }}
                const rms = Math.sqrt(sumSq / outLen);
                const gain = rms > 0.0005 ? Math.min(8.0, Math.max(1.0, 0.20 / rms)) : 2.0;
                const buf = new ArrayBuffer(44 + outLen * 2);
                const v = new DataView(buf);
                const ws = (o, s) => {{ for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); }};
                ws(0, "RIFF"); v.setUint32(4, 36 + outLen * 2, true); ws(8, "WAVE"); ws(12, "fmt ");
                v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
                v.setUint32(24, targetRate, true); v.setUint32(28, targetRate * 2, true);
                v.setUint16(32, 2, true); v.setUint16(34, 16, true); ws(36, "data"); v.setUint32(40, outLen * 2, true);
                let off = 44;
                for (let i = 0; i < outLen; i++) {{
                    let s = Math.tanh(res[i] * gain);
                    v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true); off += 2;
                }}
                const bytes = new Uint8Array(buf);
                let bin = "";
                for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
                return btoa(bin);
            }}

            async function handleAudioChunkAI(chunks, sampleRate) {{
                if (!GEMINI_API_KEY || GEMINI_API_KEY.length < 10) {{
                    interimText.innerText = "Chế độ AI Audio cần Gemini API Key ở thanh bên trái.";
                    return;
                }}
                const total = chunks.reduce((a, c) => a + c.length, 0);
                const merged = new Float32Array(total);
                let off = 0; chunks.forEach(c => {{ merged.set(c, off); off += c.length; }});
                isTranscribing = true;
                interimText.innerText = "Đang giải mã âm thanh...";
                try {{
                    const wavB64 = encodeWavBase64(merged, sampleRate);
                    const prompt = `Chép lại chính xác lời nói (${{srcLang.value}}). Nếu chỉ có im lặng/nhiễu, trả về chuỗi rỗng.`;
                    const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${{encodeURIComponent(GEMINI_API_KEY)}}`, {{
                        method: "POST", headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ contents: [{{ parts: [{{ text: prompt }}, {{ inlineData: {{ mimeType: "audio/wav", data: wavB64 }} }}] }}], generationConfig: {{ temperature: 0.1 }} }})
                    }});
                    if (res.ok) {{
                        const d = await res.json();
                        const text = (d?.candidates?.[0]?.content?.parts?.[0]?.text || "").trim().replace(/^["'«]|["'»]$/g, "");
                        if (text.length >= 2) appendCard(text, srcLang.value, tgtLang.value);
                    }}
                }} catch (e) {{}}
                interimText.innerText = "...";
                isTranscribing = false;
            }}

            async function initAudioDSP() {{
                try {{
                    if (!navigator.mediaDevices?.getUserMedia || micStream) return;
                    micStream = await navigator.mediaDevices.getUserMedia({{ audio: {{ echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 }} }});
                    const AC = window.AudioContext || window.webkitAudioContext;
                    audioCtx = new AC();
                    if (audioCtx.state === "suspended") await audioCtx.resume();
                    const src = audioCtx.createMediaStreamSource(micStream);
                    scriptProcessor = audioCtx.createScriptProcessor(2048, 1, 1);
                    const sink = audioCtx.createGain(); sink.gain.value = 0.0;
                    src.connect(scriptProcessor); scriptProcessor.connect(sink); sink.connect(audioCtx.destination);
                    scriptProcessor.onaudioprocess = (ev) => {{
                        if (!isListening) return;
                        const buf = ev.inputBuffer.getChannelData(0);
                        let sumSq = 0; for (let i = 0; i < buf.length; i++) sumSq += buf[i] * buf[i];
                        const rms = Math.sqrt(sumSq / buf.length);
                        noiseFloor = rms < noiseFloor ? noiseFloor * 0.94 + rms * 0.06 : noiseFloor * 0.995 + rms * 0.005;
                        const thresh = Math.max(0.018, Math.min(0.12, noiseFloor * 2.4));
                        const now = Date.now();
                        if (rms > thresh) {{
                            vadLast = now;
                            if (!vadActive) {{ vadActive = true; vadStart = now; }}
                        }}
                        if (vadActive) {{
                            pcmRingBuffer.push(new Float32Array(buf));
                            if ((now - vadLast > 950 && now - vadStart >= 600) || (now - vadStart >= 4200)) {{
                                vadActive = false;
                                const cap = pcmRingBuffer.slice(); pcmRingBuffer = [];
                                if (!isTranscribing && cap.length > 4) handleAudioChunkAI(cap, audioCtx.sampleRate);
                            }}
                        }}
                    }};
                }} catch (e) {{}}
            }}

            function stopAudioDSP() {{
                try {{
                    scriptProcessor?.disconnect(); scriptProcessor = null;
                    micStream?.getTracks().forEach(t => t.stop()); micStream = null;
                    audioCtx?.close(); audioCtx = null; pcmRingBuffer = []; vadActive = false;
                }} catch (e) {{}}
            }}

            function startRecognition() {{
                if (isListening) return;
                const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                isListening = true; committedResultIndex = 0; latestResultsLength = 0; currentActiveSentence = "";
                statusDot.classList.add("active"); btnStart.disabled = true; btnPause.disabled = false;

                if (modeSelect.value === "aidsp" || !SR) {{
                    statusText.innerText = "Đang thu âm bằng AI Audio...";
                    initAudioDSP(); return;
                }}

                stopAudioDSP();
                recognition = new SR();
                recognition.lang = srcLang.value;
                recognition.continuous = true; recognition.interimResults = true;
                recognition.onstart = () => {{ statusText.innerText = "Đang lắng nghe (" + srcLang.options[srcLang.selectedIndex].text + ")..."; }};
                recognition.onresult = (ev) => {{
                    latestResultsLength = ev.results.length;
                    let rebuilt = "";
                    for (let i = committedResultIndex; i < ev.results.length; i++) {{
                        const piece = (ev.results[i][0]?.transcript || "").trim();
                        if (piece) rebuilt = (rebuilt + " " + piece).trim();
                    }}
                    currentActiveSentence = rebuilt;
                    if (rebuilt) {{
                        interimText.innerText = rebuilt; manualInput.value = rebuilt;
                        if (silenceTimer) clearTimeout(silenceTimer);
                        silenceTimer = setTimeout(() => {{ if (currentActiveSentence.trim()) forceCommitInterim(); }}, 1550);
                    }}
                }};
                recognition.onerror = (ev) => {{
                    if (ev.error === "not-allowed") {{ statusText.innerText = "Trình duyệt đang chặn quyền Microphone."; stopRecognition(); }}
                    else if (ev.error === "network") {{ modeSelect.value = "aidsp"; initAudioDSP(); }}
                }};
                recognition.onend = () => {{
                    if (currentActiveSentence.trim()) forceCommitInterim();
                    committedResultIndex = 0; latestResultsLength = 0;
                    if (isListening && modeSelect.value === "webspeech") {{
                        setTimeout(() => {{ try {{ recognition.lang = srcLang.value; recognition.start(); }} catch (e) {{}} }}, 100);
                    }}
                }};
                recognition.start();
            }}

            function stopRecognition() {{
                isListening = false;
                if (silenceTimer) clearTimeout(silenceTimer);
                if (currentActiveSentence.trim()) forceCommitInterim();
                try {{ recognition?.stop(); }} catch (e) {{}}
                stopAudioDSP();
                statusDot.classList.remove("active");
                statusText.innerText = "Đã tạm dừng.";
                btnStart.disabled = false; btnPause.disabled = true;
            }}

            function clearTranscript() {{
                lectureHistory = []; currentActiveSentence = ""; manualInput.value = "";
                countBadge.innerText = "0 câu";
                summaryPanel.style.display = "none"; summaryPanel.innerText = "";
                streamEl.innerHTML = '<div id="emptyHint" class="empty">Đã xóa lịch sử. Bấm <b>Bắt đầu nghe</b> để ghi bài giảng mới.</div>';
                interimText.innerText = "...";
            }}

            function downloadTranscript() {{
                if (!lectureHistory.length) return;
                let content = "BẢN GHI BÀI GIẢNG — ANH MINH TRANSLATE\\n====================================\\n\\n";
                lectureHistory.forEach((it, i) => {{ content += `[${{i+1}} | ${{it.time}}]\\nGốc : ${{it.source}}\\nDịch: ${{it.translated}}\\n------------------------------------\\n`; }});
                const blob = new Blob([content], {{ type: "text/plain;charset=utf-8" }});
                const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
                a.download = `Bai_Giang_${{new Date().toISOString().slice(0,10)}}.txt`;
                a.click();
            }}
        </script>
    </body>
    </html>
    """


# ==============================================================================
# 7. XỬ LÝ AUDIO TỰ ĐỘNG (DSP RMS AUTO-GAIN X12 + MULTIMODAL ĐA ĐỊNH DẠNG)
# ==============================================================================
AUDIO_MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}


def boost_wav_audio_bytes(audio_bytes: bytes, max_gain_factor: float = 12.0) -> bytes:
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
            core = samples[skip : n - skip] if (n - 2 * skip) > 200 else samples
            rms = math.sqrt(sum((x - mean_val) ** 2 for x in core) / max(1, len(core)))
            auto_gain = min(max_gain_factor, max(1.8, 6500.0 / rms)) if rms > 1.0 else max_gain_factor

            prev = 0.0
            for i in range(n):
                cur = float(samples[i]) - mean_val
                boosted = (cur - 0.22 * prev) * auto_gain
                prev = cur
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


def transcribe_and_translate_audio_bytes(
    audio_bytes: bytes,
    source_lang_speech: str,
    target_lang_trans: str,
    gemini_api_key: str = "",
    file_ext: str = ".wav",
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    ext = file_ext.lower()
    mime_type = AUDIO_MIME_MAP.get(ext, "audio/wav")
    processed = boost_wav_audio_bytes(audio_bytes, max_gain_factor=12.0) if ext == ".wav" else audio_bytes

    if clean_api_key(gemini_api_key):
        b64_audio = base64.b64encode(processed).decode("utf-8")
        prompt = (
            f'Nghe file âm thanh (ngôn ngữ gốc: {source_lang_speech}), chép lại chính xác lời nói và dịch sang "{target_lang_trans}". '
            'Chỉ trả về JSON: {"transcript": "...", "translation": "..."}'
        )
        raw, _ = call_gemini_multimodal_rest(
            api_key=gemini_api_key,
            parts=[{"text": prompt}, {"inlineData": {"mimeType": mime_type, "data": b64_audio}}],
            expect_json=True, temperature=0.1, timeout_sec=30,
        )
        if raw:
            try:
                parsed = _parse_json_response(raw)
                if parsed and str(parsed.get("transcript", "")).strip():
                    tr = str(parsed["transcript"]).strip()
                    tl = str(parsed.get("translation", "")).strip() or fast_free_translate(tr, source_lang_speech.split("-")[0], target_lang_trans)
                    return tr, tl, None
            except Exception:
                pass

    if ext != ".wav":
        return None, None, f"Định dạng {ext} cần nhập Gemini API Key ở thanh bên trái, hoặc dùng nút thu âm trực tiếp."

    if sr is None:
        return None, None, "Thiếu thư viện SpeechRecognition trong requirements.txt."

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 20
    recognizer.dynamic_energy_threshold = False
    last_err = None
    for wav_data in (processed, audio_bytes):
        try:
            with sr.AudioFile(io.BytesIO(wav_data)) as source:
                audio_data = recognizer.record(source)
            tr = recognizer.recognize_google(audio_data, language=source_lang_speech)
            if tr and tr.strip():
                tl = fast_free_translate(tr, source_lang_speech.split("-")[0], target_lang_trans)
                return tr, tl, None
        except sr.UnknownValueError:
            last_err = "Không nhận diện được lời nói. Hãy nói gần Mic hơn hoặc thêm Gemini API Key."
        except Exception as exc:
            last_err = f"Không thể xử lý âm thanh: {exc}"
    return None, None, last_err


# ==============================================================================
# 8. SỔ TỪ VỰNG & XUẤT ANKI CSV
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
                {"ru_accent": ru_k, "en": str(it.get("en", "")).strip(), "vi": str(it.get("vi", "")).strip()},
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


# ==============================================================================
# 9. GIAO DIỆN CHÍNH TỐI GIẢN (SIDEBAR GỌN + 3 TAB CHẤT LƯỢNG)
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    rec_key, rec_prof = consume_bootstrap_query_params()
    if rec_key and not st.session_state["saved_gemini_api_key"]:
        st.session_state["saved_gemini_api_key"] = rec_key
    if rec_prof:
        st.session_state["confirmed_user_name"] = rec_prof["full_name"]
        st.session_state["confirmed_user_year"] = rec_prof["student_year"]
        st.session_state["confirmed_user_uni"] = rec_prof["university"]

    if not st.session_state.get("ls_sync_checked"):
        st.session_state["ls_sync_checked"] = True
        if not st.session_state.get("saved_gemini_api_key") or not st.session_state.get("confirmed_user_name"):
            inject_localstorage_sync(action="load_all")


def render_translation_result(res: Dict, used_ai: bool) -> None:
    engine_label = "Gemini AI" if used_ai else "Dịch nhanh"
    main_trans = res.get("main_translation", "")

    render_html(
        f"""
        <div class="clean-card">
            <div class="clean-label">
                <span>Bản dịch</span>
                <span>{esc(engine_label)}</span>
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

    # 2 phiên bản giao tiếp tiếng Nga (Вы / Ты)
    reply_variants = res.get("russian_reply_variants", {})
    if reply_variants and (reply_variants.get("formal_vy") or reply_variants.get("casual_ty")):
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            vy = reply_variants.get("formal_vy", "")
            vy_note = reply_variants.get("formal_vy_vi_note", "")
            render_html(
                f"""
                <div class="tone-card">
                    <div class="tone-heading">Trang trọng · Ngôi «Вы» (Giảng viên / Khoa)</div>
                    <div class="tone-body">{esc(vy)}</div>
                    <div class="tone-sub">{esc(vy_note)}</div>
                </div>
                """
            )
            if vy:
                vc1, vc2 = st.columns([1, 1])
                with vc1:
                    render_copy_button(vy, "Sao chép", "cp_vy")
                with vc2:
                    if st.button("Nghe «Вы»", key="tts_vy_btn", use_container_width=True):
                        ab = generate_tts_audio(vy, "ru")
                        if ab:
                            st.audio(ab, format="audio/mp3")

        with t_col2:
            ty = reply_variants.get("casual_ty", "")
            ty_note = reply_variants.get("casual_ty_vi_note", "")
            render_html(
                f"""
                <div class="tone-card">
                    <div class="tone-heading">Thân mật · Ngôi «Ты» (Bạn học / Nhóm lớp)</div>
                    <div class="tone-body">{esc(ty)}</div>
                    <div class="tone-sub">{esc(ty_note)}</div>
                </div>
                """
            )
            if ty:
                cc1, cc2 = st.columns([1, 1])
                with cc1:
                    render_copy_button(ty, "Sao chép", "cp_ty")
                with cc2:
                    if st.button("Nghe «Ты»", key="tts_ty_btn", use_container_width=True):
                        ab = generate_tts_audio(ty, "ru")
                        if ab:
                            st.audio(ab, format="audio/mp3")

    # Tiếng lóng phát hiện được (chỉ hiển thị khi thực sự có trong câu)
    slang_list = res.get("slang_explanations", [])
    if slang_list:
        slang_rows = "".join(
            f"<tr><td><b>{esc(s.get('term',''))}</b></td><td>{esc(s.get('full_form',''))}</td><td>{esc(s.get('meaning_vi',''))}</td></tr>"
            for s in slang_list
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Tiếng lóng & viết tắt trong câu</span></div>
                <table class="clean-table">
                    <thead><tr><th>Từ lóng</th><th>Dạng đầy đủ</th><th>Giải nghĩa</th></tr></thead>
                    <tbody>{slang_rows}</tbody>
                </table>
            </div>
            """
        )

    # Bảng từ vựng đáng chú ý
    vocab_table = res.get("vocabulary_table", [])
    if vocab_table:
        v_rows = "".join(
            f"<tr><td><b>{esc(r.get('ru_accent',''))}</b></td><td>{esc(r.get('vi',''))}</td><td>{esc(r.get('en',''))}</td></tr>"
            for r in vocab_table
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Từ vựng quan trọng (có dấu trọng âm)</span></div>
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

    # Ghi chú ngữ pháp / ngữ cảnh ngắn
    ctx_note = res.get("context_note", "")
    if ctx_note:
        render_html(f'<div class="note-callout">{esc(ctx_note)}</div>')

    # Đối chiếu 3 ngôn ngữ gọn trong expander
    with st.expander("Đối chiếu 3 ngôn ngữ (Nga · Việt · Anh)"):
        e1, e2, e3 = st.columns(3)
        with e1:
            st.caption("Tiếng Nga")
            st.write(res.get("ru_version", "—"))
        with e2:
            st.caption("Tiếng Việt")
            st.write(res.get("vi_version", "—"))
        with e3:
            st.caption("Tiếng Anh")
            st.write(res.get("en_version", "—"))


def main() -> None:
    init_session_state()
    inject_editorial_minimal_css(is_author_admin=st.session_state["is_author_admin"])

    # SIDEBAR TỐI GIẢN: CHỈ GIỮ CÀI ĐẶT THỰC SỰ CẦN
    with st.sidebar:
        st.markdown("### Cài đặt")

        saved_key_val = clean_api_key(st.session_state.get("saved_gemini_api_key", ""))
        gemini_api_key = st.text_input(
            "Gemini API Key (tùy chọn)",
            value=saved_key_val,
            type="password",
            placeholder="Dán key để bật AI dịch sâu & OCR ảnh",
        )
        st.markdown(f"[Lấy Gemini API Key miễn phí →]({GEMINI_API_KEY_URL})")

        clean_key_input = clean_api_key(gemini_api_key)
        if clean_key_input and clean_key_input != saved_key_val and clean_key_input not in st.session_state["declined_keys"]:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Lưu trên máy", type="primary", use_container_width=True):
                    st.session_state["saved_gemini_api_key"] = clean_key_input
                    inject_localstorage_sync(action="save_key", key_to_save=clean_key_input)
                    st.toast("Đã lưu API Key trên trình duyệt.")
                    st.rerun()
            with c2:
                if st.button("Chỉ phiên này", use_container_width=True):
                    st.session_state["declined_keys"].add(clean_key_input)
                    st.rerun()
        elif clean_key_input and clean_key_input == saved_key_val:
            st.caption("Trạng thái: Đã lưu API Key trên trình duyệt này.")
            if st.button("Xóa Key đã lưu", use_container_width=True):
                st.session_state["saved_gemini_api_key"] = ""
                inject_localstorage_sync(action="delete_key")
                st.rerun()
        else:
            st.caption("Đang dùng chế độ dịch nhanh miễn phí (không cần Key).")

        st.markdown("---")

        # Thông tin sinh viên (gọn gàng)
        if st.session_state.get("pending_profile_save"):
            prof = st.session_state.pop("pending_profile_save")
            inject_localstorage_sync(action="save_profile", student_profile=prof)

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
                        st.session_state["confirmed_user_name"] = u_name.strip()
                        st.session_state["confirmed_user_year"] = u_year
                        st.session_state["confirmed_user_uni"] = u_uni.strip()
                        send_user_notification_email(u_name.strip(), u_year, u_uni.strip())
                        st.session_state["pending_profile_save"] = {
                            "full_name": u_name.strip(), "student_year": u_year, "university": u_uni.strip()
                        }
                        st.toast("Đã lưu thông tin sinh viên.")
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

    # HEADER TỐI GIẢN 1 DÒNG
    render_html(
        """
        <div class="minimal-header">
            <h1 class="minimal-title">Anh Minh Translate</h1>
            <div class="minimal-meta">Dịch thuật Nga – Việt &amp; hỗ trợ học tập tại Nga · Mai Văn Minh (СПбГМТУ)</div>
        </div>
        """
    )

    tab1, tab2, tab3 = st.tabs(["Dịch văn bản & Tài liệu", "Nghe giảng & Ghi âm", "Từ vựng & Tiếng lóng"])

    # ==========================================================================
    # TAB 1: DỊCH VĂN BẢN, ẢNH SLIDE & TỆP TÀI LIỆU
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
            height=150,
            label_visibility="collapsed",
            placeholder="Nhập hoặc dán tin nhắn tiếng Nga, đoạn tài liệu chuyên ngành, hoặc câu tiếng Việt cần dịch...",
        )

        # Nút hành động chính trên 1 hàng gọn
        b1, b2, b3, b4 = st.columns([1.8, 1.4, 1.0, 2.8])
        with b1:
            translate_clicked = st.button("Dịch ngay", type="primary", use_container_width=True)
        with b2:
            tts_clicked = st.button("Nghe văn bản", type="secondary", use_container_width=True)
        with b3:
            if st.button("Xóa", type="secondary", use_container_width=True):
                st.session_state["input_text_area"] = ""
                st.rerun()
        with b4:
            if source_text.strip():
                st.caption(f"{len(source_text)} ký tự · {len(source_text.split())} từ")

        # Tải ảnh slide / file tài liệu gọn trong expander
        with st.expander("Dịch từ ảnh chụp slide / bảng viết hoặc tệp tài liệu (.txt, .docx, .pdf)"):
            u1, u2 = st.columns(2)
            with u1:
                uploaded_img = st.file_uploader("Ảnh chụp slide / bảng / tin nhắn", type=["png", "jpg", "jpeg", "webp"])
                if uploaded_img is not None:
                    st.image(uploaded_img, width=220)
                    if st.button("Quét chữ & dịch ảnh", type="primary", use_container_width=True):
                        if not clean_key_input:
                            st.warning("Cần nhập Gemini API Key (miễn phí) ở thanh bên trái để đọc chữ trong ảnh.")
                        else:
                            with st.spinner("Đang đọc chữ và dịch..."):
                                ocr_res, ocr_err = call_gemini_ocr_and_translate_image(
                                    clean_key_input, uploaded_img.getvalue(), uploaded_img.type or "image/jpeg", direction
                                )
                                if ocr_res:
                                    if ocr_res.get("extracted_text"):
                                        st.session_state["input_text_area"] = ocr_res["extracted_text"]
                                    st.session_state["last_translation_result"] = ocr_res
                                    st.session_state["last_used_ai"] = True
                                    st.rerun()
                                else:
                                    st.error(f"Không thể xử lý ảnh: {ocr_err}")
            with u2:
                uploaded_doc = st.file_uploader("Tệp tài liệu (.txt, .docx, .pdf)", type=["txt", "md", "docx", "pdf"])
                if uploaded_doc is not None:
                    if st.button("Đưa nội dung vào ô dịch", use_container_width=True):
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
                st.warning("Vui lòng nhập nội dung cần dịch.")
            else:
                result_data: Optional[Dict] = None
                used_ai = False
                if clean_key_input:
                    with st.spinner("Đang dịch..."):
                        result_data, g_err = call_gemini_smart_translate(clean_key_input, source_text, direction)
                        if result_data:
                            used_ai = True
                        elif g_err and "không hợp lệ" in g_err.lower():
                            st.warning("API Key không hợp lệ, đã tự động chuyển sang dịch nhanh.")

                if not result_data:
                    with st.spinner("Đang dịch..."):
                        result_data = fallback_smart_translate(source_text, direction)

                st.session_state["last_translation_result"] = result_data
                st.session_state["last_used_ai"] = used_ai
                st.session_state["translation_history"].insert(
                    0,
                    {
                        "time": datetime.now().strftime("%H:%M"),
                        "preview": source_text.strip()[:120],
                        "full_source": source_text.strip(),
                        "result": result_data,
                        "used_ai": used_ai,
                    },
                )
                st.session_state["translation_history"] = st.session_state["translation_history"][:MAX_HISTORY_ITEMS]

        if st.session_state.get("last_translation_result"):
            render_translation_result(
                st.session_state["last_translation_result"],
                st.session_state.get("last_used_ai", False),
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
                            st.session_state["last_used_ai"] = h["used_ai"]
                            st.rerun()

    # ==========================================================================
    # TAB 2: NGHE GIẢNG REAL-TIME & DỊCH FILE GHI ÂM
    # ==========================================================================
    with tab2:
        components.html(build_realtime_lecture_component(gemini_api_key=clean_key_input), height=610, scrolling=False)

        with st.expander("Thu âm nhanh hoặc tải tệp ghi âm (.wav, .mp3, .m4a, .ogg, .webm)"):
            ac1, ac2 = st.columns(2)
            with ac1:
                speech_lang = st.selectbox(
                    "Ngôn ngữ trong ghi âm",
                    options=[("ru-RU", "Tiếng Nga"), ("vi-VN", "Tiếng Việt"), ("en-US", "Tiếng Anh")],
                    format_func=lambda x: x[1],
                )[0]
                target_lang = st.selectbox(
                    "Dịch sang",
                    options=[("vi", "Tiếng Việt"), ("ru", "Tiếng Nga"), ("en", "Tiếng Anh")],
                    format_func=lambda x: x[1],
                )[0]
            with ac2:
                rec_audio = st.audio_input("Thu âm trực tiếp") if hasattr(st, "audio_input") else None
                up_audio = st.file_uploader("Hoặc tải tệp âm thanh", type=["wav", "mp3", "m4a", "ogg", "webm"])

            audio_bytes = rec_audio.getvalue() if rec_audio is not None else (up_audio.getvalue() if up_audio is not None else None)
            audio_ext = ".wav" if rec_audio is not None else (Path(up_audio.name).suffix.lower() if up_audio is not None else ".wav")

            if audio_bytes:
                with st.spinner("Đang nhận diện giọng nói và dịch..."):
                    tr_t, tl_t, err = transcribe_and_translate_audio_bytes(
                        audio_bytes=audio_bytes,
                        source_lang_speech=speech_lang,
                        target_lang_trans=target_lang,
                        gemini_api_key=clean_key_input,
                        file_ext=audio_ext,
                    )
                    if err:
                        st.error(err)
                    else:
                        render_html(
                            f"""
                            <div class="clean-card">
                                <div class="clean-label"><span>Lời nói gốc</span></div>
                                <div class="clean-result-text" style="font-size:0.98rem;margin-bottom:14px;">{esc(tr_t)}</div>
                                <div class="clean-label"><span>Bản dịch</span></div>
                                <div class="clean-result-text">{esc(tl_t)}</div>
                            </div>
                            """
                        )
                        st.download_button(
                            "Tải bản dịch (.txt)",
                            data=f"Lời gốc:\n{tr_t}\n\nBản dịch:\n{tl_t}\n".encode("utf-8"),
                            file_name="ban_dich_ghi_am.txt",
                            mime="text/plain",
                        )

    # ==========================================================================
    # TAB 3: SỔ TỪ VỰNG ĐÃ LƯU, FLASHCARDS & TRA CỨU TIẾNG LÓNG SINH VIÊN NGA
    # ==========================================================================
    with tab3:
        v_col1, v_col2 = st.columns([1.05, 1.0])

        with v_col1:
            st.markdown("#### Sổ từ vựng & Ôn thẻ nhanh")
            deck_mode = st.radio(
                "Nguồn thẻ ôn tập",
                options=["Từ đã lưu", "Tiếng lóng sinh viên Nga"],
                horizontal=True,
                label_visibility="collapsed",
            )
            active_deck = (
                st.session_state["saved_vocab_notebook"]
                if deck_mode == "Từ đã lưu"
                else [{"ru_accent": f"{x['accent']} ({x['full']})", "vi": x["vi"], "en": x["en"]} for x in RUSSIAN_SLANG_DICT]
            )

            if not active_deck:
                st.caption("Chưa có từ nào được lưu. Sau khi dịch ở Tab 1, bấm «Lưu từ vựng vào sổ ôn tập» để thêm vào đây.")
            else:
                idx = st.session_state["flashcard_index"] % len(active_deck)
                card = active_deck[idx]
                back_html = (
                    f'<div class="flashcard-back">{esc(card["vi"])}<div style="font-size:0.9rem;color:#52525B;font-weight:400;margin-top:4px;">{esc(card["en"])}</div></div>'
                    if st.session_state["flashcard_show_back"]
                    else '<div style="margin-top:12px;font-size:0.86rem;color:#71717A;">Bấm «Lật thẻ» để xem nghĩa</div>'
                )
                render_html(
                    f"""
                    <div class="flashcard-minimal">
                        <div style="font-size:0.8rem;color:#71717A;margin-bottom:8px;">{idx + 1} / {len(active_deck)}</div>
                        <div class="flashcard-word">{esc(card["ru_accent"])}</div>
                        {back_html}
                    </div>
                    """
                )
                fb1, fb2, fb3, fb4 = st.columns(4)
                with fb1:
                    if st.button("Trước", use_container_width=True):
                        st.session_state["flashcard_index"] = (idx - 1) % len(active_deck)
                        st.session_state["flashcard_show_back"] = False
                        st.rerun()
                with fb2:
                    if st.button("Lật thẻ", type="primary", use_container_width=True):
                        st.session_state["flashcard_show_back"] = not st.session_state["flashcard_show_back"]
                        st.rerun()
                with fb3:
                    if st.button("Phát âm", use_container_width=True):
                        ru_clean = card["ru_accent"].split("(")[0].replace("\u0301", "").strip()
                        ab = generate_tts_audio(ru_clean, "ru")
                        if ab:
                            st.audio(ab, format="audio/mp3")
                with fb4:
                    if st.button("Tiếp", use_container_width=True):
                        st.session_state["flashcard_index"] = (idx + 1) % len(active_deck)
                        st.session_state["flashcard_show_back"] = False
                        st.rerun()

                if st.session_state["saved_vocab_notebook"]:
                    st.download_button(
                        f"Xuất {len(st.session_state['saved_vocab_notebook'])} từ đã lưu ra CSV (Anki / Excel)",
                        data=export_vocab_to_anki_csv(st.session_state["saved_vocab_notebook"]),
                        file_name="tu_vung_anki.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

        with v_col2:
            st.markdown("#### Tra nhanh tiếng lóng sinh viên Nga")
            q_slang = st.text_input("Tìm từ lóng", placeholder="Ví dụ: препод, курсач, хвост, инфа...", label_visibility="collapsed")
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


if __name__ == "__main__":
    main()
