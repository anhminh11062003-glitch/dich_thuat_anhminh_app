"""
Anh Minh Translate — Công cụ dịch thuật, ngữ pháp & hỗ trợ học tiếng Nga cho sinh viên Việt tại Nga
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


def get_author_monogram_svg_uri() -> str:
    """Ảnh đại diện tối giản dự phòng khi chưa đặt file avatar.jpg/png trong thư mục repo."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
      <rect width="120" height="120" rx="60" fill="#18181B"/>
      <text x="60" y="72" text-anchor="middle" font-family="Inter, -apple-system, sans-serif" font-size="42" font-weight="600" fill="#FAF9F6" letter-spacing="-1">MM</text>
    </svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


@st.cache_data(show_spinner=False)
def get_author_avatar_data_uri() -> str:
    """Tự động nạp ảnh thật của tác giả (avatar.jpg/png, minh.jpg/png...) hoặc dùng monogram tối giản."""
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
                if (!sessionStorage.getItem("anhminh_bootstrapped_v10")) {
                    sessionStorage.setItem("anhminh_bootstrapped_v10", "1");
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
# 3. TỪ ĐIỂN TIẾNG LÓNG SINH VIÊN NGA & BỘ CHIA 6 CÁCH / ĐỘNG TỪ CƠ BẢN
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


def fallback_russian_morphology(word_raw: str) -> Optional[Dict[str, Any]]:
    """
    Bộ chia 6 cách / chia động từ theo quy tắc chuẩn (dự phòng khi chưa nhập Gemini API Key).
    Áp dụng cho từ đơn tiếng Nga.
    """
    w = re.sub(r"[^а-яА-ЯёЁ\-]", "", word_raw.strip()).lower()
    if not w or len(w) < 2 or " " in word_raw.strip():
        return None

    # 1. Động từ nguyên thể (-ть / -ться)
    if w.endswith(("ать", "ять", "еть", "ить")):
        if w.endswith(("ать", "ять", "еть")):
            stem = w[:-2]
            return {
                "word_type": "Động từ (Глагол · Nhóm I cơ bản)",
                "lemma": w,
                "aspect_or_gender": "Cần Gemini AI để xác định chính xác ngoại lệ & cặp thể НСВ/СВ",
                "verb_conjugation": {
                    "я": stem + "ю",
                    "ты": stem + "ешь",
                    "он / она / оно": stem + "ет",
                    "мы": stem + "ем",
                    "вы": stem + "ете",
                    "они": stem + "ют",
                    "Quá khứ": f"{stem}л / {stem}ла / {stem}ло / {stem}ли",
                    "Mệnh lệnh": f"{stem}й / {stem}йте",
                },
            }
        stem = w[:-3]
        first_end = "у" if stem.endswith(("ж", "ш", "ч", "щ")) else "ю"
        third_pl = "ат" if stem.endswith(("ж", "ш", "ч", "щ")) else "ят"
        return {
            "word_type": "Động từ (Глагол · Nhóm II cơ bản)",
            "lemma": w,
            "aspect_or_gender": "Cần Gemini AI để xác định biến âm phụ âm & cặp thể НСВ/СВ",
            "verb_conjugation": {
                "я": stem + first_end,
                "ты": stem + "ишь",
                "он / она / оно": stem + "ит",
                "мы": stem + "им",
                "вы": stem + "ите",
                "они": stem + third_pl,
                "Quá khứ": f"{stem}ил / {stem}ила / {stem}ило / {stem}или",
                "Mệnh lệnh": f"{stem}и / {stem}ите",
            },
        }

    # 2. Tính từ (-ый / -ий / -ой)
    if w.endswith(("ый", "ий", "ой")) and len(w) >= 4:
        stem = w[:-2]
        soft = w.endswith("ий")
        return {
            "word_type": "Tính từ (Прилагательное)",
            "lemma": w,
            "aspect_or_gender": "Giống đực (số ít) / Số nhiều",
            "cases_table": [
                {"case": "1. Именительный (Ai? Cái gì?)", "singular": w, "plural": stem + ("ие" if soft else "ые")},
                {"case": "2. Родительный (Của ai? Không có gì?)", "singular": stem + ("его" if soft else "ого"), "plural": stem + ("их" if soft else "ых")},
                {"case": "3. Дательный (Cho ai? Tới đâu?)", "singular": stem + ("ему" if soft else "ому"), "plural": stem + ("им" if soft else "ым")},
                {"case": "4. Винительный (Thấy ai? Cái gì?)", "singular": w + " / " + stem + ("его" if soft else "ого"), "plural": stem + ("ие" if soft else "ые") + " / " + stem + ("их" if soft else "ых")},
                {"case": "5. Творительный (Với ai? Bằng gì?)", "singular": stem + ("им" if soft else "ым"), "plural": stem + ("ими" if soft else "ыми")},
                {"case": "6. Предложный (Ở đâu? Về cái gì?)", "singular": stem + ("ем" if soft else "ом"), "plural": stem + ("их" if soft else "ых")},
            ],
        }

    # 3. Danh từ giống cái (-а / -я), áp dụng quy tắc 7 chữ cái (г, к, х, ж, ч, ш, щ -> и)
    if w.endswith(("а", "я")) and len(w) >= 3:
        stem = w[:-1]
        is_ya = w.endswith("я")
        y_or_i = "и" if (is_ya or stem.endswith(("г", "к", "х", "ж", "ч", "ш", "щ"))) else "ы"
        return {
            "word_type": "Danh từ (Существительное)",
            "lemma": w,
            "aspect_or_gender": "Giống cái (Женский род)",
            "cases_table": [
                {"case": "1. Именительный (Cách 1 · Chủ ngữ)", "singular": w, "plural": stem + y_or_i},
                {"case": "2. Родительный (Cách 2 · Sở hữu / Нет)", "singular": stem + y_or_i, "plural": stem + ("ь" if is_ya else "")},
                {"case": "3. Дательный (Cách 3 · Cho ai / К)", "singular": stem + "е", "plural": stem + ("ям" if is_ya else "ам")},
                {"case": "4. Винительный (Cách 4 · Tân ngữ)", "singular": stem + ("ю" if is_ya else "у"), "plural": stem + y_or_i},
                {"case": "5. Творительный (Cách 5 · Với / Bằng)", "singular": stem + ("ей" if is_ya else "ой"), "plural": stem + ("ями" if is_ya else "ами")},
                {"case": "6. Предложный (Cách 6 · В / На / О)", "singular": stem + "е", "plural": stem + ("ях" if is_ya else "ах")},
            ],
        }

    # 4. Danh từ giống trung (-о / -е)
    if w.endswith(("о", "е")) and len(w) >= 3:
        stem = w[:-1]
        is_e = w.endswith("е")
        return {
            "word_type": "Danh từ (Существительное)",
            "lemma": w,
            "aspect_or_gender": "Giống trung (Средний род)",
            "cases_table": [
                {"case": "1. Именительный (Cách 1 · Chủ ngữ)", "singular": w, "plural": stem + ("я" if is_e else "а")},
                {"case": "2. Родительный (Cách 2 · Sở hữu / Нет)", "singular": stem + ("я" if is_e else "а"), "plural": stem + ("ей" if is_e else "")},
                {"case": "3. Дательный (Cách 3 · Cho ai / К)", "singular": stem + ("ю" if is_e else "у"), "plural": stem + ("ям" if is_e else "ам")},
                {"case": "4. Винительный (Cách 4 · Tân ngữ)", "singular": w, "plural": stem + ("я" if is_e else "а")},
                {"case": "5. Творительный (Cách 5 · Với / Bằng)", "singular": stem + ("ем" if is_e else "ом"), "plural": stem + ("ями" if is_e else "ами")},
                {"case": "6. Предложный (Cách 6 · В / На / О)", "singular": stem + "е", "plural": stem + ("ях" if is_e else "ах")},
            ],
        }

    # 5. Danh từ giống đực (kết thúc phụ âm), áp dụng quy tắc 7 chữ cái
    if w[-1] in "бвгджзклмнпрстфхцчшщ":
        pl_end = "и" if w[-1] in "гкхжчшщ" else "ы"
        return {
            "word_type": "Danh từ (Существительное)",
            "lemma": w,
            "aspect_or_gender": "Giống đực (Мужской род)",
            "cases_table": [
                {"case": "1. Именительный (Cách 1 · Chủ ngữ)", "singular": w, "plural": w + pl_end},
                {"case": "2. Родительный (Cách 2 · Sở hữu / Нет)", "singular": w + "а", "plural": w + "ов"},
                {"case": "3. Дательный (Cách 3 · Cho ai / К)", "singular": w + "у", "plural": w + "ам"},
                {"case": "4. Винительный (Cách 4 · Tân ngữ)", "singular": w + " (vật) / " + w + "а (người)", "plural": w + pl_end + " / " + w + "ов"},
                {"case": "5. Творительный (Cách 5 · Với / Bằng)", "singular": w + "ом", "plural": w + "ами"},
                {"case": "6. Предложный (Cách 6 · В / На / О)", "singular": w + "е", "plural": w + "ах"},
            ],
        }

    return None


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
            --bg-page: #FAF9F6;
            --bg-surface: #FFFFFF;
            --bg-subtle: #F4F3EE;
            --text-primary: #18181B;
            --text-secondary: #52525B;
            --text-muted: #71717A;
            --border-light: #E5E4DF;
            --border-strong: #D4D4D8;
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
            padding: 8px 15px !important;
            box-shadow: none !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] p {{
            color: #52525B !important;
            font-weight: 500 !important;
            font-size: 0.91rem !important;
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

        div[data-testid="stFileUploader"] section,
        div[data-testid="stAudioInput"] {{
            background-color: #FFFFFF !important;
            border-radius: 10px !important;
        }}
        div[data-testid="stFileUploader"] section {{
            border: 1px dashed #D4D4D8 !important;
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

        /* HEADER + THẺ TÁC GIẢ TỐI GIẢN */
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
        .minimal-sub {{
            font-size: 0.88rem;
            color: #52525B;
            margin-top: 3px;
        }}
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
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid #D4D4D8;
            flex-shrink: 0;
        }}
        .author-chip-name {{
            font-size: 0.86rem;
            font-weight: 600;
            color: #18181B;
            line-height: 1.25;
        }}
        .author-chip-role {{
            font-size: 0.76rem;
            color: #52525B;
            line-height: 1.25;
        }}
        .sidebar-author-box {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 14px;
        }}
        .sidebar-author-img {{
            width: 52px;
            height: 52px;
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid #D4D4D8;
            flex-shrink: 0;
        }}

        /* THẺ NỘI DUNG */
        .clean-card {{
            background-color: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 12px;
            padding: 18px 20px;
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
            flex-wrap: wrap;
            gap: 6px;
        }}
        .clean-result-text {{
            font-size: 1.07rem;
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
            padding: 15px 17px;
            height: 100%;
        }}
        .tone-heading {{ font-size: 0.83rem; font-weight: 600; color: #52525B; margin-bottom: 6px; }}
        .tone-body {{ font-size: 1.0rem; font-weight: 600; color: #18181B; line-height: 1.55; margin-bottom: 6px; }}
        .tone-sub {{ font-size: 0.85rem; color: #52525B; line-height: 1.5; }}

        .clean-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.91rem;
            margin-top: 6px;
        }}
        .clean-table th {{
            text-align: left;
            padding: 9px 12px;
            border-bottom: 1px solid #D4D4D8;
            color: #52525B;
            font-weight: 600;
            background-color: #FAF9F6;
        }}
        .clean-table td {{
            padding: 9px 12px;
            border-bottom: 1px solid #E5E4DF;
            color: #18181B;
            vertical-align: top;
            line-height: 1.5;
        }}

        .note-callout {{
            background-color: #F4F3EE;
            border-left: 3px solid #18181B;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-top: 12px;
            font-size: 0.91rem;
            color: #18181B;
            line-height: 1.62;
        }}

        .lecture-item {{
            background: #FFFFFF;
            border: 1px solid #E5E4DF;
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        .lecture-meta {{ font-size: 0.78rem; color: #71717A; margin-bottom: 5px; }}
        .lecture-src {{ font-size: 0.96rem; color: #18181B; margin-bottom: 8px; line-height: 1.55; }}
        .lecture-tgt {{ font-size: 1.0rem; font-weight: 600; color: #18181B; background: #FAF9F6; padding: 10px 12px; border-radius: 8px; line-height: 1.55; }}

        .flashcard-minimal {{
            background-color: #FFFFFF;
            border: 1px solid #D4D4D8;
            border-radius: 14px;
            padding: 36px 24px;
            text-align: center;
            margin: 12px 0;
        }}
        .flashcard-word {{ font-size: 1.7rem; font-weight: 700; color: #18181B; letter-spacing: -0.02em; }}
        .flashcard-back {{ margin-top: 16px; padding-top: 16px; border-top: 1px solid #E5E4DF; font-size: 1.1rem; font-weight: 600; color: #18181B; }}

        @media (max-width: 768px) {{
            .main .block-container {{ padding: 1rem 0.85rem 2.5rem 0.85rem !important; }}
            .minimal-title {{ font-size: 1.32rem; }}
            .clean-card {{ padding: 14px 15px; }}
        }}
        </style>
        """
    )


# ==============================================================================
# 5. ĐỘNG CƠ DỊCH + PHÂN TÍCH 6 CÁCH / CHIA ĐỘNG TỪ / NGỮ PHÁP CÂU DÀI
# ==============================================================================
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
    timeout_sec: int = 28,
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
Bạn là giáo sư ngôn ngữ học Nga – Việt và chuyên gia dịch thuật cho sinh viên Việt Nam tại Nga.
Hãy TỰ ĐỘNG nhận diện ngữ cảnh (kỹ thuật/đóng tàu, bài giảng đại học, thủ tục hành chính/visa, hay giao tiếp đời thường) và dịch theo chiều "{direction}".

ĐẶC BIỆT QUAN TRỌNG VỀ NGỮ PHÁP TIẾNG NGA:
1. Nếu đầu vào là **1 từ hoặc 1 cụm từ ngắn (1-3 từ)**:
   - Xác định rõ từ loại (`Danh từ`, `Tính từ`, `Động từ`, `Trạng từ`, `Đại từ`...).
   - Nếu là **Động từ**: điền đầy đủ bảng chia động từ `verb_conjugation` (я, ты, он/она/оно, мы, вы, они, Quá khứ, Mệnh lệnh, Cặp thể НСВ/СВ). Để `cases_table` là mảng rỗng `[]`.
   - Nếu là **Danh từ / Tính từ / Đại từ / Cụm danh từ**: điền đầy đủ bảng 6 cách tiếng Nga `cases_table` (đủ 6 cách: 1. Именительный, 2. Родительный, 3. Дательный, 4. Винительный, 5. Творительный, 6. Предложный — gồm cả Số ít `singular` và Số nhiều `plural`, có dấu trọng âm \\u0301). Để `verb_conjugation` là `{{}}`.
   - Nếu là **Trạng từ** (không biến cách): ghi rõ trong `morphology.usage_note` cách dùng, mức so sánh (nếu có) và từ đồng nghĩa/trái nghĩa.
2. Nếu đầu vào là **Câu hoặc đoạn văn dài (>= 4 từ)**:
   - Điền chi tiết `sentence_grammar` giải thích ngữ pháp trong câu tiếng Nga tương ứng: chỉ rõ từng cụm/từ đang chia ở **Cách mấy (Cách 1-6)** và tại sao (đi với giới từ hay động từ nào), động từ chính chia ở thể **НСВ/СВ** nào & thì gì.
   - Đồng thời có thể trích 1 danh từ hoặc động từ quan trọng nhất trong câu vào `morphology` (nếu hữu ích).

CHỈ TRẢ VỀ đúng 1 đối tượng JSON hợp lệ:
{{
  "main_translation": "Bản dịch tự nhiên, chuẩn xác nhất",
  "ru_version": "Bản tiếng Nga tương ứng (có thể kèm trọng âm khi là từ đơn)",
  "vi_version": "Bản tiếng Việt tương ứng",
  "en_version": "Bản tiếng Anh đối chiếu",
  "morphology": {{
    "word_type": "Từ loại (VD: Danh từ · Giống cái / Động từ · НСВ / Tính từ / Trạng từ)",
    "lemma": "Dạng nguyên thể tiếng Nga có dấu trọng âm \\u0301",
    "aspect_or_gender": "Giống đực/cái/trung hoặc cặp thể НСВ/СВ (VD: писать [НСВ] / написать [СВ])",
    "cases_table": [
      {{"case": "1. Именительный (Cách 1)", "singular": "...", "plural": "..."}},
      {{"case": "2. Родительный (Cách 2)", "singular": "...", "plural": "..."}},
      {{"case": "3. Дательный (Cách 3)", "singular": "...", "plural": "..."}},
      {{"case": "4. Винительный (Cách 4)", "singular": "...", "plural": "..."}},
      {{"case": "5. Творительный (Cách 5)", "singular": "...", "plural": "..."}},
      {{"case": "6. Предложный (Cách 6)", "singular": "...", "plural": "..."}}
    ],
    "verb_conjugation": {{
      "я": "...", "ты": "...", "он / она / оно": "...", "мы": "...", "вы": "...", "они": "...",
      "Quá khứ": "...", "Mệnh lệnh": "..."
    }},
    "usage_note": "Ghi chú cách dùng, giới từ đi kèm hoặc từ đồng nghĩa/trái nghĩa (nếu là trạng từ/từ đặc biệt)."
  }},
  "sentence_grammar": [
    {{"segment": "Từ hoặc cụm từ trong câu tiếng Nga", "grammar_tag": "Cách mấy / Thể động từ / Cấu trúc", "explanation": "Giải thích ngắn gọn dễ hiểu bằng tiếng Việt"}}
  ],
  "slang_explanations": [
    {{"term": "Từ lóng (nếu có)", "full_form": "Dạng đầy đủ", "meaning_vi": "Giải nghĩa"}}
  ],
  "vocabulary_table": [
    {{"ru_accent": "Từ khóa tiếng Nga có dấu trọng âm \\u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu tiếng Nga lịch sự ngôi «Вы»",
    "formal_vy_vi_note": "Nghĩa tiếng Việt",
    "casual_ty": "Câu tiếng Nga thân mật ngôi «Ты»",
    "casual_ty_vi_note": "Nghĩa tiếng Việt"
  }},
  "context_note": "1-2 câu tóm tắt ngữ pháp hoặc lưu ý giao tiếp quan trọng."
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
Bạn là trợ lý học thuật Nga – Việt cho sinh viên tại Nga.
Đọc chính xác toàn bộ chữ trong ảnh (slide bài giảng, bảng viết, tài liệu hoặc tin nhắn), dịch theo chiều "{direction}" và giải thích ngắn gọn ngữ pháp / từ vựng quan trọng.
CHỈ TRẢ VỀ JSON:
{{
  "extracted_text": "Văn bản gốc đọc được từ ảnh",
  "main_translation": "Bản dịch tự nhiên, chuẩn xác",
  "ru_version": "Bản tiếng Nga",
  "vi_version": "Bản tiếng Việt",
  "en_version": "Bản tiếng Anh đối chiếu",
  "sentence_grammar": [
    {{"segment": "Cụm từ quan trọng", "grammar_tag": "Cách / Ngữ pháp", "explanation": "Giải thích ngắn"}}
  ],
  "slang_explanations": [],
  "vocabulary_table": [
    {{"ru_accent": "Từ khóa tiếng Nga có dấu trọng âm \\u0301", "en": "Nghĩa tiếng Anh", "vi": "Nghĩa tiếng Việt"}}
  ],
  "russian_reply_variants": {{
    "formal_vy": "Câu hỏi/trao đổi ngôi «Вы»",
    "formal_vy_vi_note": "Nghĩa tiếng Việt",
    "casual_ty": "Câu trao đổi ngôi «Ты»",
    "casual_ty_vi_note": "Nghĩa tiếng Việt"
  }},
  "context_note": "Tóm tắt 1-2 ý chính cần nhớ từ ảnh."
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

    # Tự động chia 6 cách hoặc chia động từ cơ bản cho từ đơn tiếng Nga
    morph = fallback_russian_morphology(ru_ver if len(ru_ver.split()) == 1 else source_text)

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
        "morphology": morph or {},
        "sentence_grammar": [],
        "slang_explanations": slang_explanations,
        "vocabulary_table": vocab_list,
        "russian_reply_variants": {
            "formal_vy": formal_vy_full,
            "formal_vy_vi_note": formal_note,
            "casual_ty": casual_ty_full,
            "casual_ty_vi_note": casual_note,
        },
        "context_note": "Mở thanh bên trái và dán Gemini API Key (miễn phí) để xem bảng chia 6 cách chuẩn ngoại lệ, chia động từ đầy đủ thể НСВ/СВ và phân tích ngữ pháp chi tiết từng cụm trong câu dài.",
    }


# ==============================================================================
# 6. XỬ LÝ AUDIO NATIVE (ỔN ĐỊNH 100% TRÊN MỌI THIẾT BỊ) + TÓM TẮT BÀI GIẢNG AI
# ==============================================================================
AUDIO_MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}


def boost_wav_audio_bytes(audio_bytes: bytes, max_gain_factor: float = 12.0) -> bytes:
    """Chuẩn hóa âm lượng RMS Auto-Gain x12 + Pre-Emphasis giúp nghe rõ giọng giảng viên ở xa."""
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
    recent_context: Optional[List[Dict[str, str]]] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    ext = file_ext.lower()
    mime_type = AUDIO_MIME_MAP.get(ext, "audio/wav")
    processed = boost_wav_audio_bytes(audio_bytes, max_gain_factor=12.0) if ext == ".wav" else audio_bytes

    if clean_api_key(gemini_api_key):
        b64_audio = base64.b64encode(processed).decode("utf-8")
        ctx_str = ""
        if recent_context:
            ctx_lines = [f"- {c['source']} -> {c['translation']}" for c in recent_context[-3:]]
            ctx_str = "Ngữ cảnh các đoạn giảng ngay trước đó:\n" + "\n".join(ctx_lines) + "\n\n"
        prompt = (
            f"{ctx_str}"
            f'Nghe file âm thanh (ngôn ngữ gốc: {source_lang_speech}), chép lại chính xác toàn bộ lời nói '
            f'và dịch chuẩn xác, liền mạch theo ngữ cảnh sang "{target_lang_trans}". '
            'Chỉ trả về JSON: {"transcript": "...", "translation": "..."}'
        )
        raw, _ = call_gemini_multimodal_rest(
            api_key=gemini_api_key,
            parts=[{"text": prompt}, {"inlineData": {"mimeType": mime_type, "data": b64_audio}}],
            expect_json=True, temperature=0.1, timeout_sec=35,
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
        return None, None, f"Định dạng {ext} cần nhập Gemini API Key ở thanh bên trái, hoặc dùng nút Thu âm trực tiếp (định dạng WAV) ngay phía trên."

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
            last_err = "Chưa nghe rõ lời nói trong đoạn thu âm. Hãy nói gần Mic hơn, kiểm tra đúng ngôn ngữ đang chọn, hoặc thêm Gemini API Key để tăng độ nhạy."
        except Exception as exc:
            last_err = f"Không thể xử lý âm thanh: {exc}"
    return None, None, last_err


def summarize_lecture_notes_ai(api_key: str, notes: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[str]]:
    if not clean_api_key(api_key):
        return None, "Cần nhập Gemini API Key (miễn phí) ở thanh bên trái để tóm tắt bài giảng bằng AI."
    joined = "\n".join(f"{i+1}. {n['source']} ({n['translation']})" for i, n in enumerate(notes))
    prompt = (
        "Bạn là trợ lý học tập cho sinh viên Việt Nam tại Nga.\n"
        "Hãy tóm tắt nội dung bài giảng sau đây thật mạch lạc bằng tiếng Việt gồm:\n"
        "1. Các ý chính cốt lõi cần nhớ (gạch đầu dòng ngắn gọn).\n"
        "2. Danh sách thuật ngữ tiếng Nga – tiếng Việt quan trọng nhất xuất hiện trong bài.\n\n"
        f"Nội dung bài giảng:\n{joined[:14000]}"
    )
    return call_gemini_multimodal_rest(
        api_key=api_key,
        parts=[{"text": prompt}],
        expect_json=False,
        temperature=0.25,
        timeout_sec=30,
    )


def build_live_speech_fallback_component(gemini_api_key: str = "") -> str:
    """Chế độ nghe trực tiếp liên tục bằng Web Speech API (chỉ dùng trên trình duyệt cho phép mic trong iframe)."""
    safe_key = json.dumps(clean_api_key(gemini_api_key))
    return f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8" />
        <style>
            * {{ box-sizing: border-box; font-family: 'Inter', -apple-system, sans-serif; }}
            body {{ margin: 0; padding: 2px; background: transparent; color: #18181B; }}
            .box {{ background: #FFFFFF; border: 1px solid #E5E4DF; border-radius: 10px; padding: 14px; }}
            .row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px; }}
            select, button {{ padding: 6px 11px; border-radius: 8px; border: 1px solid #D4D4D8; background: #FFFFFF; color: #18181B; font-size: 13px; cursor: pointer; }}
            button.pri {{ background: #18181B; color: #FFFFFF; border-color: #18181B; font-weight: 600; }}
            .st {{ font-size: 13px; color: #52525B; margin-bottom: 8px; }}
            .out {{ max-height: 220px; overflow-y: auto; border: 1px solid #E5E4DF; border-radius: 8px; padding: 10px; background: #FAF9F6; font-size: 14px; line-height: 1.55; }}
        </style>
    </head>
    <body>
        <div class="box">
            <div class="row">
                <select id="sl"><option value="ru-RU">Tiếng Nga</option><option value="vi-VN">Tiếng Việt</option><option value="en-US">Tiếng Anh</option></select>
                <select id="tl"><option value="vi">→ Tiếng Việt</option><option value="ru">→ Tiếng Nga</option><option value="en">→ Tiếng Anh</option></select>
                <button class="pri" id="bStart" onclick="startLive()">Bắt đầu nghe liên tục</button>
                <button id="bStop" onclick="stopLive()" disabled>Dừng</button>
            </div>
            <div id="status" class="st">Sẵn sàng. Nếu trình duyệt chặn quyền Mic ở chế độ này, hãy dùng nút <b>Thu âm trực tiếp</b> ở ngay phía trên (hoạt động ổn định 100%).</div>
            <div id="out" class="out">Chưa có nội dung...</div>
        </div>
        <script>
            const KEY = {safe_key};
            let rec = null, on = false, lines = [];
            function escH(s) {{ return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }}
            async function trans(t, s, tg) {{
                const ss = s.split("-")[0];
                if (ss === tg) return t;
                try {{
                    const r = await fetch(`https://translate.googleapis.com/translate_a/single?client=gtx&sl=${{ss}}&tl=${{tg}}&dt=t&q=${{encodeURIComponent(t)}}`);
                    const d = await r.json();
                    if (Array.isArray(d) && Array.isArray(d[0])) return d[0].map(x => x[0]).join("");
                }} catch(e) {{}}
                return t;
            }}
            function startLive() {{
                const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SR) {{
                    document.getElementById("status").innerText = "Trình duyệt này không hỗ trợ Web Speech API. Vui lòng dùng nút Thu âm trực tiếp phía trên.";
                    return;
                }}
                on = true;
                document.getElementById("bStart").disabled = true;
                document.getElementById("bStop").disabled = false;
                rec = new SR();
                rec.lang = document.getElementById("sl").value;
                rec.continuous = true; rec.interimResults = false;
                rec.onstart = () => {{ document.getElementById("status").innerText = "Đang nghe trực tiếp..."; }};
                rec.onresult = async (ev) => {{
                    const txt = (ev.results[ev.results.length - 1][0]?.transcript || "").trim();
                    if (!txt) return;
                    const tr = await trans(txt, rec.lang, document.getElementById("tl").value);
                    lines.push(`<div><b>Gốc:</b> ${{escH(txt)}}<br/><b>Dịch:</b> ${{escH(tr)}}</div><hr style="border:none;border-top:1px solid #E5E4DF;margin:8px 0;"/>`);
                    const out = document.getElementById("out");
                    out.innerHTML = lines.join("");
                    out.scrollTop = out.scrollHeight;
                }};
                rec.onerror = (ev) => {{
                    document.getElementById("status").innerText = "Trình duyệt chặn Mic trong khung phụ (" + ev.error + "). Hãy dùng nút Thu âm trực tiếp ở ngay phía trên!";
                    stopLive();
                }};
                rec.onend = () => {{ if (on) {{ try {{ rec.start(); }} catch(e) {{}} }} }};
                try {{ rec.start(); }} catch(e) {{
                    document.getElementById("status").innerText = "Không mở được Mic trực tiếp. Hãy dùng nút Thu âm trực tiếp ở phía trên.";
                    stopLive();
                }}
            }}
            function stopLive() {{
                on = false;
                try {{ rec?.stop(); }} catch(e) {{}}
                document.getElementById("bStart").disabled = false;
                document.getElementById("bStop").disabled = true;
            }}
        </script>
    </body>
    </html>
    """


# ==============================================================================
# 7. CẨM NANG KIẾN THỨC HỌC TIẾNG NGA KHOA HỌC (TAB 3)
# ==============================================================================
def render_russian_knowledge_hub() -> None:
    topic = st.radio(
        "Chọn chuyên đề ngữ pháp",
        options=[
            "6 Cách (Падежи)",
            "Động từ & Thể (НСВ / СВ)",
            "Động từ chuyển động",
            "Giới từ В / НА & Thời gian",
            "Mẫu câu Đại học & Visa",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    if topic == "6 Cách (Падежи)":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Tổng quan 6 cách trong tiếng Nga (Падежи)</span><span>Nền tảng bắt buộc</span></div>
                <table class="clean-table">
                    <thead>
                        <tr><th>Cách</th><th>Câu hỏi</th><th>Chức năng chính</th><th>Giới từ hay gặp</th><th>Ví dụ (студе́нт / кни́га)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><b>1. Именительный</b><br/>(Nguyên cách)</td><td>Кто? Что?</td><td>Chủ ngữ của câu, dạng gốc trong từ điển</td><td>Không có giới từ</td><td><b>Студе́нт</b> чита́ет. <b>Кни́га</b> на столе́.</td></tr>
                        <tr><td><b>2. Родительный</b><br/>(Sở hữu cách)</td><td>Кого́? Чего́?</td><td>Sở hữu (của ai), phủ định (нет), số lượng (2,3,4,5), xuất phát (из/от)</td><td>у, без, до, из, с, от, о́коло, по́сле, для</td><td>Нет <b>студе́нта</b>. Страни́ца <b>кни́ги</b>.</td></tr>
                        <tr><td><b>3. Дательный</b><br/>(Tặng cách)</td><td>Кому́? Чему́?</td><td>Đối tượng nhận hành động (cho ai), tuổi tác, cảm xúc (мне холодно)</td><td>к, по</td><td>Я звоню́ <b>студе́нту</b>. Иду́ к <b>преподава́телю</b>.</td></tr>
                        <tr><td><b>4. Винительный</b><br/>(Đối cách)</td><td>Кого́? Что?</td><td>Tân ngữ trực tiếp (đọc gì, gặp ai), hướng chuyển động (куда?), thứ trong tuần</td><td>в, на (hướng đi), че́рез, за</td><td>Я чита́ю <b>кни́гу</b>. Я ви́жу <b>студе́нта</b>.</td></tr>
                        <tr><td><b>5. Творительный</b><br/>(Công cụ cách)</td><td>Кем? Чем?</td><td>Công cụ (bằng gì), đi cùng ai (с кем?), nghề nghiệp (быть/стать/работать)</td><td>с, над, под, пе́ред, за, ме́жду</td><td>Пишу́ <b>ру́чкой</b>. Разгова́риваю со <b>студе́нтом</b>.</td></tr>
                        <tr><td><b>6. Предложный</b><br/>(Giới cách)</td><td>О ком? О чём? Где?</td><td>Vị trí tĩnh (ở đâu?), chủ đề nói/nghĩ về ai/cái gì, phương tiện (на метро)</td><td>в, на (ở đâu), о (об), при</td><td>Учу́сь в <b>университе́те</b>. Ду́маю о <b>кни́ге</b>.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Bảng đuôi biến cách Danh từ số ít (Quy tắc nhanh)</span></div>
                <table class="clean-table">
                    <thead>
                        <tr><th>Cách</th><th>Giống đực (phụ âm / -й / -ь)</th><th>Giống cái (-а / -я / -ь)</th><th>Giống trung (-о / -е)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><b>Cách 1</b></td><td>ø / -й / -ь</td><td>-а / -я / -ь</td><td>-о / -е</td></tr>
                        <tr><td><b>Cách 2</b></td><td>-а / -я / -я</td><td>-ы (-и) / -и / -и</td><td>-а / -я</td></tr>
                        <tr><td><b>Cách 3</b></td><td>-у / -ю / -ю</td><td>-е / -е (-и với -ия) / -и</td><td>-у / -ю</td></tr>
                        <tr><td><b>Cách 4</b></td><td>Vật = C1 · Người = C2</td><td>-у / -ю / -ь</td><td>Giống Cách 1 (-о / -е)</td></tr>
                        <tr><td><b>Cách 5</b></td><td>-ом / -ем / -ем</td><td>-ой / -ей / -ью</td><td>-ом / -ем</td></tr>
                        <tr><td><b>Cách 6</b></td><td>-е (với -ий → -ии)</td><td>-е (với -ия/-ь → -ии/-и)</td><td>-е (với -ие → -ии)</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Quy tắc 7 chữ cái (г, к, х, ж, ч, ш, щ):</b> Sau 7 phụ âm này <b>không bao giờ viết «ы»</b> mà luôn đổi thành <b>«и»</b> (VD: кни́га → кни́ги, студе́нтка → студе́нтки).
                </div>
            </div>
            """
        )

    elif topic == "Động từ & Thể (НСВ / СВ)":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Hai nhóm chia động từ ở thì Hiện tại / Tương lai đơn</span></div>
                <table class="clean-table">
                    <thead>
                        <tr><th>Ngôi</th><th>Nhóm I (đa số -ать, -ять, -еть · VD: чита́ть)</th><th>Nhóm II (đa số -ить · VD: говори́ть)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><b>я</b> (tôi)</td><td>-у / -ю (чита́ю)</td><td>-у / -ю (говорю́)</td></tr>
                        <tr><td><b>ты</b> (bạn)</td><td>-ешь / -ёшь (чита́ешь)</td><td>-ишь (говори́шь)</td></tr>
                        <tr><td><b>он / она́ / оно́</b></td><td>-ет / -ёт (чита́ет)</td><td>-ит (говори́т)</td></tr>
                        <tr><td><b>мы</b> (chúng tôi)</td><td>-ем / -ём (чита́ем)</td><td>-им (говори́м)</td></tr>
                        <tr><td><b>вы</b> (ngài / các bạn)</td><td>-ете / -ёте (чита́ете)</td><td>-ите (говори́те)</td></tr>
                        <tr><td><b>они́</b> (họ)</td><td>-ут / -ют (чита́ют)</td><td>-ат / -ят (говоря́т)</td></tr>
                    </tbody>
                </table>
                <div class="note-callout">
                    <b>Thì quá khứ (rất dễ):</b> Bỏ <b>-ть</b>, thêm <b>-л</b> (giống đực), <b>-ла</b> (giống cái), <b>-ло</b> (giống trung), <b>-ли</b> (số nhiều). VD: чита́ть → чита́л, чита́ла, чита́ли.
                </div>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Phân biệt Thể Chưa Hoàn Thành (НСВ) và Thể Hoàn Thành (СВ)</span></div>
                <table class="clean-table">
                    <thead>
                        <tr><th>Tiêu chí</th><th>НСВ (Несовершенный вид)</th><th>СВ (Совершенный вид)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><b>Ý nghĩa cốt lõi</b></td><td>Quá trình đang diễn ra, hành động lặp lại nhiều lần, nêu sự kiện chung</td><td>Kết quả đã hoàn tất, hành động xảy ra 1 lần dứt điểm</td></tr>
                        <tr><td><b>Từ dấu hiệu</b></td><td>ка́ждый день, ча́сто, обы́чно, до́лго, всегда́</td><td>уже́, наконе́ц, вдруг, сра́зу, за (2 часа́)</td></tr>
                        <tr><td><b>Thì sử dụng</b></td><td>Quá khứ · Hiện tại · Tương lai (бу́ду + nguyên thể)</td><td>Quá khứ · Tương lai đơn (chia trực tiếp, <b>không có Hiện tại</b>)</td></tr>
                        <tr><td><b>Cặp sinh viên hay dùng</b></td><td>писа́ть, сдава́ть, учи́ть, реша́ть, понима́ть</td><td>написа́ть, сдать, вы́учить, реши́ть, поня́ть</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "Động từ chuyển động":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Động từ chuyển động (Глаголы движения)</span><span>Đi bộ & Phương tiện</span></div>
                <table class="clean-table">
                    <thead>
                        <tr><th>Nghĩa</th><th>Một hướng / Đang đi (1 chiều)</th><th>Khứ hồi / Lặp lại / Thói quen</th><th>Ví dụ</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><b>Đi bộ</b></td><td><b>идти́</b> (иду́, идёшь, иду́т)</td><td><b>ходи́ть</b> (хожу́, хо́дишь, хо́дят)</td><td>Сейча́с я <b>иду́</b> в корпус. Я ка́ждый день <b>хожу́</b> на па́ры.</td></tr>
                        <tr><td><b>Đi bằng xe / tàu</b></td><td><b>е́хать</b> (е́ду, е́дешь, е́дут)</td><td><b>е́здить</b> (е́зжу, е́здишь, е́здят)</td><td>Мы <b>е́дем</b> на метро́. Ле́том я <b>е́зжу</b> домо́й.</td></tr>
                        <tr><td><b>Mang theo (đi bộ)</b></td><td><b>нести́</b></td><td><b>носи́ть</b></td><td>Я <b>несу́</b> чертёж преподава́телю.</td></tr>
                        <tr><td><b>Bay</b></td><td><b>лете́ть</b></td><td><b>лета́ть</b></td><td>Самолёт <b>лети́т</b> в Москву́.</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Tiền tố hay gặp nhất với động từ chuyển động</span></div>
                <table class="clean-table">
                    <thead><tr><th>Tiền tố</th><th>Nghĩa</th><th>Ví dụ thực tế</th></tr></thead>
                    <tbody>
                        <tr><td><b>при-</b></td><td>Đến nơi</td><td>прийти́ / прие́хать (đến trường, đến Nga)</td></tr>
                        <tr><td><b>у-</b></td><td>Rời đi hẳn</td><td>уйти́ / уе́хать (rời khỏi phòng, về nước)</td></tr>
                        <tr><td><b>в- / во-</b></td><td>Đi vào trong</td><td>войти́ в аудито́рию (vào giảng đường)</td></tr>
                        <tr><td><b>вы-</b></td><td>Đi ra ngoài</td><td>вы́йти из метро́ (ra khỏi ga tàu điện ngầm)</td></tr>
                        <tr><td><b>пере-</b></td><td>Đi ngang qua / chuyển</td><td>перейти́ у́лицу (sang đường), перевести́ (dịch)</td></tr>
                        <tr><td><b>под-</b></td><td>Tiến lại gần</td><td>подойти́ к преподава́телю (lại gần giảng viên)</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    elif topic == "Giới từ В / НА & Thời gian":
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Cặp giới từ địa điểm bắt buộc nhớ</span></div>
                <table class="clean-table">
                    <thead><tr><th>Ở đâu? (Где? · Cách 6)</th><th>Đi đâu? (Куда? · Cách 4)</th><th>Từ đâu về? (Откуда? · Cách 2)</th><th>Áp dụng cho</th></tr></thead>
                    <tbody>
                        <tr><td><b>в</b> + Cách 6</td><td><b>в</b> + Cách 4</td><td><b>из</b> + Cách 2</td><td>Không gian kín, thành phố, quốc gia, tòa nhà (в униве́ре, в обща́ге, в Росси́и)</td></tr>
                        <tr><td><b>на</b> + Cách 6</td><td><b>на</b> + Cách 4</td><td><b>с</b> + Cách 2</td><td>Sự kiện, buổi học, khoa, đảo, không gian mở (на ле́кции, на факульте́те, на вокза́ле)</td></tr>
                        <tr><td><b>у</b> + Cách 2 (ở chỗ ai)</td><td><b>к</b> + Cách 3 (đến chỗ ai)</td><td><b>от</b> + Cách 2 (từ chỗ ai về)</td><td>Người (у преподава́теля, к врачу́, от дека́на)</td></tr>
                    </tbody>
                </table>
            </div>

            <div class="clean-card">
                <div class="clean-label"><span>Cách nói Thứ · Tháng · Giờ trong tiếng Nga</span></div>
                <table class="clean-table">
                    <thead><tr><th>Mục</th><th>Cấu trúc chuẩn</th><th>Ví dụ</th></tr></thead>
                    <tbody>
                        <tr><td><b>Vào thứ mấy?</b></td><td><b>в</b> + Cách 4</td><td>в понеде́льник, во вто́рник, в сре́ду, в четве́рг, в пя́тницу, в суббо́ту, в воскресе́нье</td></tr>
                        <tr><td><b>Vào tháng mấy?</b></td><td><b>в</b> + Cách 6</td><td>в январе́, в феврале́, в ма́рте, в сентябре́, в декабре́</td></tr>
                        <tr><td><b>Vào ngày mấy?</b></td><td>Số thứ tự giống trung + Tháng (đều <b>Cách 2</b>)</td><td>пе́рвого сентября́ (ngày 1/9), двадца́того мая (ngày 20/5)</td></tr>
                        <tr><td><b>Lúc mấy giờ?</b></td><td><b>в</b> + số giờ (Cách 4)</td><td>в час (1h), в два часа́ (2h), в пять часо́в (5h), в по́лтора часа́</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )

    else:
        render_html(
            """
            <div class="clean-card">
                <div class="clean-label"><span>Mẫu câu giao tiếp chuẩn mực tại Đại học & Phòng Visa (Ngôi «Вы»)</span></div>
                <table class="clean-table">
                    <thead><tr><th>Tình huống</th><th>Câu tiếng Nga chuẩn</th><th>Nghĩa tiếng Việt</th></tr></thead>
                    <tbody>
                        <tr><td><b>Xin nộp / duyệt đồ án</b></td><td>Здра́вствуйте! Мо́жно показа́ть Вам мою́ курсову́ю рабо́ту (чертёж) на прове́рку?</td><td>Em chào thầy/cô ạ! Em có thể gửi thầy/cô xem và kiểm tra đồ án (bản vẽ) được không ạ?</td></tr>
                        <tr><td><b>Hỏi lịch tư vấn / thi lại</b></td><td>Подскажи́те, пожа́луйста, когда́ у Вас бу́дет консульта́ция / пересда́ча?</td><td>Thầy/cô cho em hỏi khi nào thầy/cô có buổi giải đáp / thi lại ạ?</td></tr>
                        <tr><td><b>Xin giấy xác nhận ở Khoa</b></td><td>Здра́вствуйте! Мне нужна́ спра́вка об обуче́нии для продле́ния ви́зы.</td><td>Chào cô! Em cần xin giấy xác nhận đang theo học để gia hạn visa ạ.</td></tr>
                        <tr><td><b>Gia hạn Visa / Tạm trú</b></td><td>Подскажи́те, пожа́луйста, каки́е докуме́нты нужны́ для продле́ния ви́зы и регистра́ции?</td><td>Xin hỏi em cần chuẩn bị những giấy tờ gì để gia hạn visa và đăng ký tạm trú ạ?</td></tr>
                        <tr><td><b>Xin phép nghỉ có lý do</b></td><td>Извини́те, пожа́луйста, я сегодня́ не смогу́ прийти́ на па́ру по состоя́нию здоро́вья. Спра́вку принесу́.</td><td>Em xin lỗi, hôm nay em không thể đến lớp vì lý do sức khỏe. Em sẽ nộp giấy khám bệnh ạ.</td></tr>
                    </tbody>
                </table>
            </div>
            """
        )


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
# 9. HIỂN THỊ KẾT QUẢ DỊCH + 6 CÁCH + CHIA ĐỘNG TỪ + NGỮ PHÁP
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
        "lecture_notes": [],
        "lecture_ai_summary": "",
        "last_audio_hash": "",
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

    # PHẦN HÌNH THÁI HỌC: 6 CÁCH (DANH/TÍNH/ĐẠI TỪ) HOẶC CHIA ĐỘNG TỪ THEO NGÔI
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
                        <span>Chia động từ tiếng Nga theo các ngôi</span>
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

    # PHÂN TÍCH NGỮ PHÁP CÂU DÀI (CÁCH MẤY · THỂ ĐỘNG TỪ · CẤU TRÚC)
    sent_grammar = res.get("sentence_grammar") or []
    if sent_grammar:
        g_rows = "".join(
            f"<tr><td><b>{esc(g.get('segment',''))}</b></td><td>{esc(g.get('grammar_tag',''))}</td><td>{esc(g.get('explanation',''))}</td></tr>"
            for g in sent_grammar
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Giải thích ngữ pháp trong câu</span></div>
                <table class="clean-table">
                    <thead><tr><th>Cụm từ / Từ</th><th>Ngữ pháp (Cách / Thể)</th><th>Giải thích</th></tr></thead>
                    <tbody>{g_rows}</tbody>
                </table>
            </div>
            """
        )

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
                vc1, vc2 = st.columns(2)
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
                cc1, cc2 = st.columns(2)
                with cc1:
                    render_copy_button(ty, "Sao chép", "cp_ty")
                with cc2:
                    if st.button("Nghe «Ты»", key="tts_ty_btn", use_container_width=True):
                        ab = generate_tts_audio(ty, "ru")
                        if ab:
                            st.audio(ab, format="audio/mp3")

    slang_list = res.get("slang_explanations", [])
    if slang_list:
        slang_rows = "".join(
            f"<tr><td><b>{esc(s.get('term',''))}</b></td><td>{esc(s.get('full_form',''))}</td><td>{esc(s.get('meaning_vi',''))}</td></tr>"
            for s in slang_list
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span>Tiếng lóng &amp; viết tắt trong câu</span></div>
                <table class="clean-table">
                    <thead><tr><th>Từ lóng</th><th>Dạng đầy đủ</th><th>Giải nghĩa</th></tr></thead>
                    <tbody>{slang_rows}</tbody>
                </table>
            </div>
            """
        )

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

    ctx_note = res.get("context_note", "")
    if ctx_note:
        render_html(f'<div class="note-callout">{esc(ctx_note)}</div>')

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


# ==============================================================================
# 10. GIAO DIỆN CHÍNH (SIDEBAR + HEADER TÁC GIẢ + 4 TAB THỰC CHIẾN)
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

        st.markdown("#### Cài đặt")
        saved_key_val = clean_api_key(st.session_state.get("saved_gemini_api_key", ""))
        gemini_api_key = st.text_input(
            "Gemini API Key (tùy chọn)",
            value=saved_key_val,
            type="password",
            placeholder="Dán key để bật phân tích 6 cách AI & OCR",
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
            st.caption("Đã lưu API Key trên trình duyệt này.")
            if st.button("Xóa Key đã lưu", use_container_width=True):
                st.session_state["saved_gemini_api_key"] = ""
                inject_localstorage_sync(action="delete_key")
                st.rerun()
        else:
            st.caption("Đang dùng chế độ miễn phí (không cần Key).")

        st.markdown("---")

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

    # HEADER TỐI GIẢN KÈM THÔNG TIN & ẢNH TÁC GIẢ
    render_html(
        f"""
        <div class="minimal-header">
            <div>
                <h1 class="minimal-title">Anh Minh Translate</h1>
                <div class="minimal-sub">Dịch thuật Nga – Việt, chia 6 cách, ngữ pháp &amp; ghi chép bài giảng cho sinh viên tại Nga</div>
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

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Dịch & Ngữ pháp", "Nghe giảng & Thu âm", "Kiến thức tiếng Nga", "Từ vựng & Tiếng lóng"]
    )

    # ==========================================================================
    # TAB 1: DỊCH, CHIA 6 CÁCH, CHIA ĐỘNG TỪ, GIẢI THÍCH NGỮ PHÁP & OCR
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
            "Nội dung cần dịch hoặc tra ngữ pháp",
            key="input_text_area",
            height=145,
            label_visibility="collapsed",
            placeholder="Nhập 1 từ tiếng Nga để chia 6 cách / chia động từ theo ngôi, hoặc dán câu dài / đoạn tài liệu để dịch & giải thích ngữ pháp...",
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
                st.caption(f"{len(source_text)} ký tự · {len(source_text.split())} từ")

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
                st.warning("Vui lòng nhập từ hoặc câu cần dịch.")
            else:
                result_data: Optional[Dict] = None
                used_ai = False
                if clean_key_input:
                    with st.spinner("Đang dịch và phân tích ngữ pháp..."):
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
    # TAB 2: NGHE GIẢNG & THU ÂM (NATIVE AUDIO INPUT ỔN ĐỊNH 100% + GHI CHÉP)
    # ==========================================================================
    with tab2:
        st.caption("Bấm biểu tượng micro bên dưới để thu âm trực tiếp trên điện thoại hoặc máy tính. Hệ thống tự kích âm lượng (RMS x12), chép lời, dịch theo ngữ cảnh và lưu nối tiếp vào sổ bài giảng.")

        lc1, lc2 = st.columns(2)
        with lc1:
            speech_lang = st.selectbox(
                "Ngôn ngữ giảng viên nói",
                options=[("ru-RU", "Tiếng Nga (ru-RU)"), ("vi-VN", "Tiếng Việt (vi-VN)"), ("en-US", "Tiếng Anh (en-US)")],
                format_func=lambda x: x[1],
                key="lec_src_lang",
            )[0]
        with lc2:
            target_lang = st.selectbox(
                "Dịch sang",
                options=[("vi", "Tiếng Việt"), ("ru", "Tiếng Nga"), ("en", "Tiếng Anh")],
                format_func=lambda x: x[1],
                key="lec_tgt_lang",
            )[0]

        rec_col, up_col = st.columns([1.15, 1.0])
        with rec_col:
            recorded_audio = st.audio_input("Thu âm trực tiếp (Bấm để bắt đầu / dừng)", key="native_mic_input") if hasattr(st, "audio_input") else None
        with up_col:
            uploaded_audio = st.file_uploader(
                "Hoặc tải tệp ghi âm (.wav, .mp3, .m4a, .ogg, .webm)",
                type=["wav", "mp3", "m4a", "ogg", "webm"],
                key="lec_file_upload",
            )

        active_bytes: Optional[bytes] = None
        active_ext = ".wav"
        if recorded_audio is not None:
            active_bytes = recorded_audio.getvalue()
            active_ext = ".wav"
        elif uploaded_audio is not None:
            active_bytes = uploaded_audio.getvalue()
            active_ext = Path(uploaded_audio.name).suffix.lower() or ".wav"

        if active_bytes:
            audio_hash = hashlib.sha256(active_bytes).hexdigest()
            if audio_hash != st.session_state["last_audio_hash"]:
                with st.spinner("Đang lọc âm, nhận diện giọng nói và dịch..."):
                    tr_t, tl_t, err = transcribe_and_translate_audio_bytes(
                        audio_bytes=active_bytes,
                        source_lang_speech=speech_lang,
                        target_lang_trans=target_lang,
                        gemini_api_key=clean_key_input,
                        file_ext=active_ext,
                        recent_context=st.session_state["lecture_notes"],
                    )
                    st.session_state["last_audio_hash"] = audio_hash
                    if err:
                        st.error(err)
                    elif tr_t:
                        st.session_state["lecture_notes"].append(
                            {
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "source": tr_t,
                                "translation": tl_t or "",
                            }
                        )
                        st.toast("Đã ghi nhận và dịch xong đoạn vừa thu.")

        # Thanh công cụ Sổ Bài Giảng
        notes = st.session_state["lecture_notes"]
        if notes:
            tb1, tb2, tb3, tb4 = st.columns([1.6, 1.2, 1.4, 1.0])
            with tb1:
                if st.button("Tóm tắt bài giảng (AI)", type="primary", use_container_width=True):
                    with st.spinner("Đang tóm tắt bài giảng..."):
                        summary, s_err = summarize_lecture_notes_ai(clean_key_input, notes)
                        if s_err:
                            st.warning(s_err)
                        elif summary:
                            st.session_state["lecture_ai_summary"] = summary
            with tb2:
                full_txt = "\n\n".join(
                    f"[{i+1} · {n['time']}]\nGốc: {n['source']}\nDịch: {n['translation']}"
                    for i, n in enumerate(notes)
                )
                render_copy_button(full_txt, "Sao chép tất cả", "cp_lec_all")
            with tb3:
                st.download_button(
                    "Tải bản ghi (.txt)",
                    data=full_txt.encode("utf-8"),
                    file_name=f"bai_giang_{datetime.now().strftime('%Y-%m-%d')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            with tb4:
                if st.button("Xóa sổ", use_container_width=True):
                    st.session_state["lecture_notes"] = []
                    st.session_state["lecture_ai_summary"] = ""
                    st.session_state["last_audio_hash"] = ""
                    st.rerun()

            if st.session_state.get("lecture_ai_summary"):
                render_html(
                    f'<div class="note-callout"><b>Tóm tắt bài giảng (AI):</b><br/><div style="white-space:pre-wrap;margin-top:6px;">{esc(st.session_state["lecture_ai_summary"])}</div></div>'
                )

            st.markdown(f"#### Sổ bài giảng ({len(notes)} đoạn)")
            for idx, item in enumerate(reversed(notes), 1):
                real_num = len(notes) - idx + 1
                render_html(
                    f"""
                    <div class="lecture-item">
                        <div class="lecture-meta">Đoạn #{real_num} · {esc(item['time'])}</div>
                        <div class="lecture-src">{esc(item['source'])}</div>
                        <div class="lecture-tgt">{esc(item['translation'])}</div>
                    </div>
                    """
                )
        else:
            render_html(
                """
                <div class="clean-card" style="text-align:center;color:#71717A;padding:34px 20px;">
                    Chưa có đoạn ghi âm nào. Hãy bấm nút micro ở trên để thu âm câu giảng viên vừa nói — kết quả sẽ tự động nối tiếp thành sổ bài giảng tại đây.
                </div>
                """
            )

        with st.expander("Chế độ phụ: Nghe liên tục qua trình duyệt (Chrome/Edge trên máy tính)"):
            components.html(build_live_speech_fallback_component(gemini_api_key=clean_key_input), height=340, scrolling=False)

    # ==========================================================================
    # TAB 3: KIẾN THỨC HỌC TIẾNG NGA KHOA HỌC
    # ==========================================================================
    with tab3:
        render_russian_knowledge_hub()

    # ==========================================================================
    # TAB 4: SỔ TỪ VỰNG, FLASHCARDS & TRA CỨU TIẾNG LÓNG SINH VIÊN NGA
    # ==========================================================================
    with tab4:
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
