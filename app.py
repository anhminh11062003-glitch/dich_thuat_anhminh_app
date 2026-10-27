from array import array
import base64
import io
import json
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
# 1. CẤU HÌNH TRANG & ẢNH CHÂN DUNG TÁC GIẢ CỐ ĐỊNH
# ==============================================================================
st.set_page_config(
    page_title="Anh Minh Translate | Mai Văn Minh - СПбГМТУ",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Link lấy Gemini API Key chính thức từ Google AI Studio
GEMINI_API_KEY_URL = "https://aistudio.google.com/app/apikey"

# Nếu bạn có link ảnh trực tiếp (URL hoặc chuỗi data:image/jpeg;base64,...),
# có thể dán vào biến dưới đây. Nếu để trống, hệ thống tự động đọc file avatar.png / avatar.jpg
# trong cùng thư mục GitHub của bạn hoặc dùng chân dung cố định bên dưới.
FIXED_AUTHOR_AVATAR_BASE64_OR_URL = ""


def render_html(html_str: str) -> None:
    cleaned_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(cleaned_lines), unsafe_allow_html=True)


def clean_api_key(raw_key: str) -> str:
    """Làm sạch mọi ký tự thừa, khoảng trắng, dấu nháy khi người dùng dán API Key."""
    if not raw_key:
        return ""
    return re.sub(r'[\s"\'\`]+', "", raw_key.strip())


def get_fixed_author_portrait_svg_uri() -> str:
    """
    Ảnh chân dung cố định của tác giả Mai Văn Minh (nam sinh viên tóc đen rẽ ngôi,
    đeo kính nửa viền thanh lịch, mặc áo thun trắng, nền trắng xám studio đúng theo ảnh gốc).
    """
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
# 4. CUSTOM CSS CHUYÊN NGHIỆP + TỐI ƯU GIAO DIỆN ĐIỆN THOẠI (MOBILE-FIRST)
# ==============================================================================
def inject_ocean_blue_css() -> None:
    render_html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@500;600&display=swap');

        :root {
            --ocean-primary: #0284C7;
            --ocean-secondary: #0369A1;
            --ocean-accent: #06B6D4;
            --ocean-bg: #F0F9FF;
            --ocean-card: #FFFFFF;
            --ocean-text: #0F172A;
            --ocean-muted: #334155;
            --ocean-border: #BAE6FD;
            color-scheme: light !important;
        }

        html, body, .stApp, div, p, label, h1, h2, h3, h4, h5, h6, button, input, textarea, table,
        span:not([data-testid="stIconMaterial"]):not(.material-icons) {
            font-family: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }

        span[data-testid="stIconMaterial"], .material-icons {
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
            font-weight: normal !important;
            font-style: normal !important;
        }

        .stApp {
            background-color: #F0F9FF !important;
            background-image:
                radial-gradient(at 12% 15%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 88% 80%, rgba(2, 132, 199, 0.12) 0px, transparent 50%),
                linear-gradient(to right, rgba(186, 230, 253, 0.35) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(186, 230, 253, 0.35) 1px, transparent 1px) !important;
            background-size: 100% 100%, 100% 100%, 36px 36px, 36px 36px !important;
            color: #0F172A !important;
        }

        .main .block-container {
            padding-top: 1.5rem !important;
        }

        .main .block-container label,
        .main .block-container p,
        .main .block-container h1,
        .main .block-container h2,
        .main .block-container h3,
        .main .block-container h4,
        .main .block-container h5,
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMarkdownContainer"] p {
            color: #0C4A6E !important;
            font-weight: 600 !important;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="textarea"] textarea,
        div[data-baseweb="base-input"] textarea,
        .main input[type="text"] {
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
        }
        div[data-testid="stTextArea"] textarea:focus,
        div[data-baseweb="textarea"] textarea:focus {
            border-color: #0284C7 !important;
            box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.2) !important;
            background-color: #FFFFFF !important;
        }
        div[data-testid="stTextArea"] textarea::placeholder {
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
            opacity: 1 !important;
        }

        .main div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #7DD3FC !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.06) !important;
        }
        .main div[data-baseweb="select"] span,
        .main div[data-baseweb="select"] div {
            color: #0C4A6E !important;
        }
        ul[data-testid="stSelectboxVirtualDropdown"],
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"] {
            background-color: #FFFFFF !important;
            border: 1px solid #7DD3FC !important;
            border-radius: 12px !important;
        }
        div[data-baseweb="popover"] li,
        div[data-baseweb="menu"] li {
            color: #0F172A !important;
            font-weight: 500 !important;
        }
        div[data-baseweb="popover"] li:hover {
            background-color: #E0F2FE !important;
            color: #0284C7 !important;
        }

        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 10px;
            border-bottom: 2px solid #BAE6FD !important;
            padding-bottom: 6px;
            flex-wrap: wrap;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"] {
            background-color: #FFFFFF !important;
            border-radius: 14px 14px 4px 4px !important;
            padding: 12px 20px !important;
            border: 2px solid #7DD3FC !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.07) !important;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"] p,
        div[data-testid="stTabs"] button[data-baseweb="tab"] span,
        div[data-testid="stTabs"] button[data-baseweb="tab"] div {
            color: #0369A1 !important;
            font-weight: 700 !important;
            font-size: 0.96rem !important;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            border-color: #0369A1 !important;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.28) !important;
        }
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p,
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] span,
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] div {
            color: #FFFFFF !important;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #061E33 0%, #0C4A6E 55%, #0369A1 100%) !important;
            border-right: 2px solid #38BDF8 !important;
        }
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] li,
        section[data-testid="stSidebar"] small {
            color: #F0F9FF !important;
        }
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="input"],
        section[data-testid="stSidebar"] .stTextInput div[data-baseweb="base-input"] {
            background-color: #FFFFFF !important;
            border: 2px solid #38BDF8 !important;
            border-radius: 10px !important;
        }
        section[data-testid="stSidebar"] .stTextInput input {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
            border: none !important;
            font-weight: 600 !important;
        }
        section[data-testid="stSidebar"] .stTextInput button {
            background-color: #FFFFFF !important;
            color: #0369A1 !important;
            border: none !important;
        }
        section[data-testid="stSidebar"] .stTextInput button span,
        section[data-testid="stSidebar"] .stTextInput button svg {
            color: #0369A1 !important;
            fill: #0369A1 !important;
        }
        section[data-testid="stSidebar"] .stTextInput input::placeholder {
            color: #64748B !important;
            -webkit-text-fill-color: #64748B !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 2px solid #38BDF8 !important;
            border-radius: 10px !important;
        }
        section[data-testid="stSidebar"] div[data-baseweb="select"] span,
        section[data-testid="stSidebar"] div[data-baseweb="select"] div {
            color: #0F172A !important;
            font-weight: 700 !important;
        }
        section[data-testid="stSidebar"] details {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(186, 230, 253, 0.35) !important;
            border-radius: 10px !important;
            margin-bottom: 6px !important;
        }

        /* NÚT LẤY GEMINI API KEY CHUYỂN TAB MỚI */
        .gemini-key-link-btn {
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
        }
        .gemini-key-link-btn:hover {
            background: linear-gradient(135deg, #06B6D4 0%, #0369A1 100%);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(6, 182, 212, 0.45);
        }

        /* THẺ GIỚI THIỆU TÁC GIẢ CỐ ĐỊNH Ở SIDEBAR */
        .author-sidebar-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.16) 0%, rgba(14, 116, 144, 0.35) 100%);
            border: 1.5px solid rgba(125, 211, 252, 0.6);
            border-radius: 18px;
            padding: 14px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 13px;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
            backdrop-filter: blur(8px);
        }
        .author-avatar-img {
            width: 68px;
            height: 68px;
            border-radius: 50%;
            object-fit: cover;
            border: 2.5px solid #38BDF8;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.45);
            background: #FFFFFF;
            flex-shrink: 0;
        }
        .author-info-name {
            font-size: 1.05rem;
            font-weight: 800;
            color: #FFFFFF !important;
            line-height: 1.25;
            margin-bottom: 3px;
        }
        .author-info-role {
            font-size: 0.78rem;
            font-weight: 600;
            color: #BAE6FD !important;
            line-height: 1.38;
        }
        .author-uni-badge {
            display: inline-block;
            margin-top: 5px;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(56, 189, 248, 0.25);
            border: 1px solid rgba(125, 211, 252, 0.5);
            font-size: 0.72rem;
            font-weight: 700;
            color: #E0F2FE !important;
        }

        /* THẺ TÁC GIẢ GÓC TRÁI TRÊN CÙNG BANNER CHÍNH */
        .author-hero-box {
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
        }
        .author-hero-avatar {
            width: 74px;
            height: 74px;
            border-radius: 16px;
            object-fit: cover;
            border: 2.5px solid #7DD3FC;
            background: #FFFFFF;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        /* HEADER BANNER NGHỆ THUẬT HÀNG HẢI */
        .am-hero-banner {
            background: linear-gradient(130deg, #082F49 0%, #0369A1 45%, #0284C7 80%, #06B6D4 100%);
            border-radius: 24px;
            padding: 22px 28px;
            color: #FFFFFF !important;
            box-shadow: 0 18px 38px rgba(3, 105, 161, 0.25);
            margin-bottom: 22px;
            position: relative;
            overflow: hidden;
            border: 2px solid rgba(125, 211, 252, 0.45);
        }
        .am-brand-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
            position: relative;
            z-index: 2;
        }
        .am-brand-left {
            display: flex;
            align-items: center;
            gap: 22px;
            flex: 1;
            flex-wrap: wrap;
            min-width: 280px;
        }
        .am-title {
            font-size: 1.95rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            margin: 0 !important;
            line-height: 1.2 !important;
            color: #FFFFFF !important;
        }
        .am-title span.highlight {
            color: #7DD3FC !important;
            text-shadow: 0 2px 10px rgba(6, 182, 212, 0.4);
        }
        .am-subtitle {
            font-size: 0.96rem !important;
            color: #E0F2FE !important;
            margin-top: 5px !important;
            font-weight: 500 !important;
        }
        .am-badges {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .am-badge {
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.38);
            padding: 5px 12px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            color: #FFFFFF !important;
            backdrop-filter: blur(4px);
        }
        .am-ship-art {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        /* THẺ CARD KHOA HỌC */
        .ocean-card {
            background: rgba(255, 255, 255, 0.96);
            border-radius: 20px;
            padding: 22px 26px;
            border: 1.5px solid #BAE6FD;
            box-shadow: 0 10px 28px rgba(2, 132, 199, 0.09);
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }
        .ocean-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid #E0F2FE;
            padding-bottom: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .ocean-card-title {
            font-size: 1.12rem !important;
            font-weight: 800 !important;
            color: #0369A1 !important;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .ocean-pill {
            background: linear-gradient(135deg, #E0F2FE 0%, #CFFAFE 100%);
            color: #0369A1 !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 5px 14px;
            border-radius: 999px;
            border: 1px solid #7DD3FC;
        }
        .translation-main-text {
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
        }

        .lang-card-header {
            font-size: 0.96rem !important;
            font-weight: 800 !important;
            color: #0C4A6E !important;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .lang-compare-box-ru {
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
        }
        .lang-compare-box-vi {
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
        }
        .lang-compare-box-en {
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
        }

        .tone-box-formal {
            background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
            border: 1.5px solid #7DD3FC;
            border-left: 6px solid #0369A1;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 8px;
        }
        .tone-box-casual {
            background: linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%);
            border: 1.5px solid #67E8F9;
            border-left: 6px solid #06B6D4;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 8px;
        }
        .tone-title {
            font-weight: 800;
            font-size: 0.96rem;
            color: #0C4A6E !important;
            margin-bottom: 8px;
        }
        .tone-ru {
            font-size: 1.1rem;
            font-weight: 700;
            color: #0F172A !important;
            margin-bottom: 8px;
            line-height: 1.55;
        }
        .tone-note {
            font-size: 0.88rem;
            color: #334155 !important;
            line-height: 1.5;
        }

        .vocab-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 0.96rem;
            border-radius: 12px;
            overflow: hidden;
        }
        .vocab-table th {
            background: linear-gradient(90deg, #0369A1 0%, #0284C7 100%);
            color: #FFFFFF !important;
            text-align: left;
            padding: 12px 16px;
            font-weight: 700;
        }
        .vocab-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #E2E8F0;
            color: #0F172A !important;
            font-weight: 500;
        }
        .vocab-table tr:nth-child(even) {
            background-color: #F0F9FF;
        }
        .vocab-table tr:hover {
            background-color: #E0F2FE;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.68rem 1.4rem !important;
            font-weight: 700 !important;
            font-size: 0.98rem !important;
            box-shadow: 0 8px 18px rgba(2, 132, 199, 0.28) !important;
        }
        div.stButton > button[kind="primary"] p,
        div.stButton > button[kind="primary"] span {
            color: #FFFFFF !important;
        }
        div.stButton > button[kind="secondary"] {
            border-radius: 12px !important;
            border: 2px solid #38BDF8 !important;
            background-color: #FFFFFF !important;
            color: #0369A1 !important;
            padding: 0.55rem 1.1rem !important;
            font-weight: 700 !important;
        }
        div.stButton > button[kind="secondary"] p,
        div.stButton > button[kind="secondary"] span {
            color: #0369A1 !important;
        }

        .slang-item {
            background: #F0F9FF;
            border: 1.5px solid #BAE6FD;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 10px;
            color: #0F172A !important;
        }
        .slang-word {
            font-weight: 800;
            color: #0284C7 !important;
            font-size: 1.04rem;
        }

        .nautical-divider {
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
        }
        .nautical-divider::before,
        .nautical-divider::after {
            content: "";
            flex: 1;
            height: 1.5px;
            background: linear-gradient(90deg, transparent, #7DD3FC, transparent);
        }

        /* TỐI ƯU RESPONSIVE CHO ĐIỆN THOẠI DI ĐỘNG */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
                padding-top: 1rem !important;
            }
            .am-hero-banner {
                padding: 16px 14px !important;
                border-radius: 18px !important;
            }
            .am-title {
                font-size: 1.45rem !important;
            }
            .author-hero-box {
                max-width: 100% !important;
                width: 100% !important;
                padding: 10px 12px !important;
            }
            .am-ship-art {
                display: none !important;
            }
            .ocean-card {
                padding: 15px 14px !important;
                border-radius: 16px !important;
            }
            div[data-testid="stTabs"] button[data-baseweb="tab"] {
                padding: 10px 12px !important;
                flex: 1 1 auto !important;
            }
            div[data-testid="stTabs"] button[data-baseweb="tab"] p {
                font-size: 0.84rem !important;
            }
            .vocab-table th, .vocab-table td {
                padding: 8px 10px !important;
                font-size: 0.85rem !important;
            }
        }
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
                            <span class="am-badge">🎙️ Mic Siêu Nhạy & Hỗ trợ Điện thoại</span>
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
    """
    Hệ thống 5 cổng dịch độc lập (dùng POST để không bị giới hạn độ dài văn bản
    và chống hoàn toàn lỗi TooManyRequests trên Streamlit Cloud).
    """
    headers_form = {
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    }
    post_body = urllib.parse.urlencode({"sl": src, "tl": tgt, "q": cleaned}).encode("utf-8")

    # Cổng 1: Google Translate GTX qua phương thức POST (chịu tải văn bản dài cực tốt)
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

    # Cổng 2: Google Translate Android App Endpoint (dj=1 trả về JSON sentences siêu sạch, quota riêng)
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

    # Cổng 3: Chrome Extension Dictionary Endpoint (clients5.google.com - IP limit tách biệt)
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

    # Cổng 4: Google Translate GET chia theo đoạn nếu văn bản ngắn
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

    # Cổng 5: MyMemory API dự phòng (miễn phí, không chặn IP Cloud)
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

    # Cổng 6: deep-translator (chỉ gọi cuối cùng nếu cả 5 cổng trên đều nghẽn)
    if GoogleTranslator is not None:
        try:
            res = GoogleTranslator(source=src, target=tgt).translate(cleaned)
            if res and "too many requests" not in res.lower():
                return res
        except Exception:
            pass

    return None


def fast_free_translate(text: str, src: str, tgt: str) -> str:
    """
    Dịch thuật tốc độ cao qua 5 cổng dự phòng + Bộ nhớ đệm thông minh
    (Chỉ lưu cache khi dịch thành công, tuyệt đối không cache lỗi).
    """
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
    """
    Tự động dò tất cả các model Gemini mà API Key của người dùng được phép gọi,
    đồng thời sắp xếp ưu tiên các model nhanh và ổn định nhất để Key nào cũng vào được.
    """
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
    """
    Hỗ trợ MỌI Gemini API Key (thử đa model từ 2.5-flash, 2.0-flash, 1.5-flash, 1.5-pro...
    và tự động chuyển đổi giữa JSON mode & Standard Prompt nếu model không hỗ trợ system_instruction).
    """
    clean_k = clean_api_key(api_key)
    if not clean_k:
        return None, "Empty API Key"

    models_to_try = discover_available_gemini_models(clean_k)
    last_error = ""

    combined_prompt = f"{system_prompt}\n\n---\nVăn bản cần xử lý:\n{user_text}"

    # Thử tối đa 6 model khác nhau để đảm bảo nếu 1 model hết quota (429) hoặc không hỗ trợ,
    # hệ thống tự nhảy sang model tiếp theo của Key đó ngay lập tức
    for model_name in models_to_try[:6]:
        # Chế độ 1: Gọi v1beta có JSON responseMimeType
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
            # Nếu lỗi 400 (model cũ không hỗ trợ responseMimeType), thử gọi lại không có responseMimeType
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
        # Trích xuất khối JSON nếu model trả kèm lời dẫn
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
    """
    Chế độ Dịch Đa Luồng GTX Siêu Tốc (5 Cổng POST dự phòng):
    Hoạt động mượt mà không cần API Key, không bị chặn bởi giới hạn IP của Streamlit Cloud.
    """
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
# 6. CUSTOM HTML/JS COMPONENT CHO REAL-TIME VOICE TRANSLATION (NÂNG CẤP ĐỘ NHẠY MIC CAO)
# ==============================================================================
def build_realtime_lecture_component(gemini_api_key: str = "", selected_domain: str = "") -> str:
    safe_domain = json.dumps(selected_domain)

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
                padding: 18px;
                box-shadow: 0 12px 30px rgba(2, 132, 199, 0.12);
            }}
            .rt-top-bar {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                padding-bottom: 12px;
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
                font-size: 0.85rem;
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
                font-size: 0.86rem;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            .btn-start {{
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                color: #FFFFFF;
                box-shadow: 0 6px 16px rgba(2, 132, 199, 0.3);
            }}
            .btn-flush {{
                background: #E0F2FE;
                color: #0369A1;
                border: 1.5px solid #38BDF8;
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
            .rt-sensitivity-bar {{
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: space-between;
                gap: 10px;
                margin-top: 10px;
                padding: 9px 14px;
                background: #E0F2FE;
                border-radius: 12px;
                border: 1px solid #7DD3FC;
                font-size: 0.83rem;
                color: #0C4A6E;
                font-weight: 600;
            }}
            .rt-visualizer-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
                background: #082F49;
                border-radius: 16px;
                padding: 12px 16px;
                margin-top: 12px;
                color: #E0F2FE;
                border: 1px solid #0284C7;
                flex-wrap: wrap;
            }}
            .status-indicator {{
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.88rem;
                font-weight: 600;
                flex: 1;
                min-width: 200px;
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
            @keyframes pulseGreen {{
                0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }}
                70% {{ box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
            }}
            #waveCanvas {{
                width: 200px;
                height: 36px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.06);
                flex-shrink: 0;
            }}
            .interim-box {{
                margin-top: 12px;
                background: #E0F2FE;
                border: 1.5px dashed #0284C7;
                border-radius: 12px;
                padding: 12px 16px;
                min-height: 60px;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }}
            .interim-top {{
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .interim-label {{
                background: #0284C7;
                color: #FFFFFF;
                font-size: 0.72rem;
                font-weight: 700;
                padding: 3px 10px;
                border-radius: 999px;
                white-space: nowrap;
            }}
            .interim-text {{
                color: #0C4A6E;
                font-size: 1.04rem;
                font-weight: 700;
            }}
            .interim-live-trans {{
                color: #0369A1;
                font-size: 0.94rem;
                font-weight: 600;
                padding-left: 8px;
                border-left: 3px solid #06B6D4;
            }}
            .subtitle-stream {{
                margin-top: 12px;
                height: 330px;
                overflow-y: auto;
                background: #FFFFFF;
                border: 1.5px solid #BAE6FD;
                border-radius: 16px;
                padding: 14px;
            }}
            .sub-item {{
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-left: 5px solid #0284C7;
                border-radius: 12px;
                padding: 12px 15px;
                margin-bottom: 12px;
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
                line-height: 1.48;
            }}
            .sub-target {{
                font-size: 1.04rem;
                font-weight: 700;
                color: #0369A1;
                background: #E0F2FE;
                padding: 9px 13px;
                border-radius: 10px;
                line-height: 1.5;
                border: 1px solid #BAE6FD;
            }}
            .empty-hint {{
                text-align: center;
                color: #475569;
                padding: 55px 16px;
                font-size: 0.93rem;
                line-height: 1.6;
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
                        <option value="vi-VN">🇻🇳 Tiếng Việt (Thử mic / Dịch sang Nga)</option>
                        <option value="en-US">🇬🇧 Tiếng Anh (Bài giảng Quốc tế)</option>
                    </select>

                    <label style="font-weight:700; color:#0369A1; font-size:0.85rem;">➔ Dịch:</label>
                    <select id="targetLang" class="rt-select">
                        <option value="vi" selected>🇻🇳 Tiếng Việt</option>
                        <option value="ru">🇷🇺 Tiếng Nga</option>
                        <option value="en">🇬🇧 Tiếng Anh</option>
                    </select>
                </div>

                <div class="rt-controls">
                    <button id="btnStart" class="rt-btn btn-start" onclick="startRecognition()">
                        🎙️ Bắt đầu nghe
                    </button>
                    <button id="btnFlush" class="rt-btn btn-flush" onclick="forceCommitInterim()" disabled title="Chốt câu đang nói dở xuống khung phụ đề">
                        ➕ Chốt câu
                    </button>
                    <button id="btnPause" class="rt-btn btn-pause" onclick="stopRecognition()" disabled>
                        ⏸️ Dừng
                    </button>
                    <button id="btnClear" class="rt-btn btn-clear" onclick="clearTranscript()">
                        🗑️ Xóa
                    </button>
                    <button id="btnDownload" class="rt-btn btn-download" onclick="downloadTranscript()">
                        📥 Tải (.txt)
                    </button>
                </div>
            </div>

            <div class="rt-sensitivity-bar">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    <span>🎚️ <b>Chế độ Độ nhạy Mic:</b></span>
                    <select id="micSensitivity" class="rt-select" onchange="updateSensitivitySettings()">
                        <option value="ultra" selected>🔥 Cực nhạy — Giảng đường rộng / Giảng viên đứng xa (Khuyên dùng)</option>
                        <option value="high">⚡ Nhạy cao — Phòng học tiêu chuẩn / Điện thoại</option>
                        <option value="normal">🛡️ Cân bằng — Môi trường nhiều tiếng ồn</option>
                    </select>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <label style="cursor:pointer; display:flex; align-items:center; gap:5px;">
                        <input type="checkbox" id="preAmpToggle" checked onchange="toggleAudioPreAmp()" />
                        <span>🔊 Khuếch đại giọng nói nhỏ (Gain Boost x3.0)</span>
                    </label>
                </div>
            </div>

            <div class="rt-visualizer-row">
                <div class="status-indicator">
                    <div id="statusDot" class="pulse-dot"></div>
                    <span id="statusText">Sẵn sàng (Độ nhạy: Cực cao) — Nhấn "🎙️ Bắt đầu nghe" và nói vào Mic.</span>
                </div>
                <canvas id="waveCanvas" width="200" height="36"></canvas>
            </div>

            <div class="interim-box">
                <div class="interim-top">
                    <span class="interim-label">⚡ BẮT ÂM TỨC THÌ</span>
                    <span id="interimText" class="interim-text">Hãy nhấn "Bắt đầu nghe" và nói thử (kể cả giọng nói nhỏ)...</span>
                </div>
                <div id="interimLiveTrans" class="interim-live-trans">🌊 Bản dịch trực tiếp sẽ chạy ngay lập tức khi bạn phát âm...</div>
            </div>

            <div id="subtitleStream" class="subtitle-stream">
                <div id="emptyHint" class="empty-hint">
                    🚢 <b>Phụ đề Giảng đường Độ Nhạy Cao (Ultra-Sensitive Mic Stream)</b><br/>
                    Đã nâng cấp bộ lọc dải tần giọng nói (85Hz–8000Hz), tăng 3 ứng viên nhận diện song song (maxAlternatives=3) và tự động nối âm không trễ (50ms) để bắt trọn mọi từ của giảng viên trên cả máy tính và điện thoại.
                </div>
            </div>
        </div>

        <script>
            try {{
                if (window.frameElement) {{
                    window.frameElement.setAttribute("allow", "microphone *; autoplay *; clipboard-write *");
                }}
            }} catch (e) {{}}

            const SELECTED_DOMAIN = {safe_domain};

            const SLANG_MAP = {{
                "препод": "преподаватель (giảng viên)",
                "курсач": "курсовая работа (đồ án môn học)",
                "лаба": "лабораторная работа (bài thí nghiệm lab)",
                "хвост": "академическая задолженность (nợ môn)",
                "зачетка": "зачётная книжка (sổ điểm)",
                "зачётка": "зачётная книжка (sổ điểm)",
                "автомат": "экзамен автоматом (miễn thi)",
                "общага": "общежитие (ký túc xá)",
                "стипуха": "стипендия (học bổng)",
                "сопромат": "сопротивление материалов (sức bền vật liệu)",
                "матан": "математический анализ (giải tích)"
            }};

            let recognition = null;
            let isListening = false;
            let lectureHistory = [];
            let currentInterimBuffer = "";
            let autoCommitTimer = null;
            let liveTranslateTimer = null;
            let lastSpeechActivity = 0;
            let waveAnimId = null;

            let silenceCommitMs = 1350;
            let maxWordsBeforeCommit = 14;
            let liveTranslateDelayMs = 200;

            let audioCtx = null;
            let micStream = null;
            let analyserNode = null;
            let gainNode = null;

            const statusDot = document.getElementById("statusDot");
            const statusText = document.getElementById("statusText");
            const interimText = document.getElementById("interimText");
            const interimLiveTrans = document.getElementById("interimLiveTrans");
            const subtitleStream = document.getElementById("subtitleStream");
            const btnStart = document.getElementById("btnStart");
            const btnFlush = document.getElementById("btnFlush");
            const btnPause = document.getElementById("btnPause");
            const sourceLangSelect = document.getElementById("sourceLang");
            const targetLangSelect = document.getElementById("targetLang");
            const micSensitivitySelect = document.getElementById("micSensitivity");
            const preAmpToggle = document.getElementById("preAmpToggle");

            function updateSensitivitySettings() {{
                const mode = micSensitivitySelect.value;
                if (mode === "ultra") {{
                    silenceCommitMs = 1300;
                    maxWordsBeforeCommit = 14;
                    liveTranslateDelayMs = 180;
                    if (gainNode) gainNode.gain.value = 3.2;
                }} else if (mode === "high") {{
                    silenceCommitMs = 1600;
                    maxWordsBeforeCommit = 16;
                    liveTranslateDelayMs = 260;
                    if (gainNode) gainNode.gain.value = 2.2;
                }} else {{
                    silenceCommitMs = 2000;
                    maxWordsBeforeCommit = 20;
                    liveTranslateDelayMs = 350;
                    if (gainNode) gainNode.gain.value = 1.4;
                }}
            }}

            async function initAudioPreAmp() {{
                if (!preAmpToggle.checked) return;
                const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
                if (isMobile) return;

                try {{
                    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
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
                    const source = audioCtx.createMediaStreamSource(micStream);

                    const highpass = audioCtx.createBiquadFilter();
                    highpass.type = "highpass";
                    highpass.frequency.value = 85;

                    const compressor = audioCtx.createDynamicsCompressor();
                    compressor.threshold.setValueAtTime(-50, audioCtx.currentTime);
                    compressor.knee.setValueAtTime(40, audioCtx.currentTime);
                    compressor.ratio.setValueAtTime(12, audioCtx.currentTime);
                    compressor.attack.setValueAtTime(0, audioCtx.currentTime);
                    compressor.release.setValueAtTime(0.25, audioCtx.currentTime);

                    gainNode = audioCtx.createGain();
                    gainNode.gain.value = 3.2;

                    analyserNode = audioCtx.createAnalyser();
                    analyserNode.fftSize = 64;
                    analyserNode.smoothingTimeConstant = 0.65;

                    source.connect(highpass);
                    highpass.connect(compressor);
                    compressor.connect(gainNode);
                    gainNode.connect(analyserNode);
                }} catch (e) {{}}
            }}

            function stopAudioPreAmp() {{
                try {{
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
                }} catch (e) {{}}
            }}

            function toggleAudioPreAmp() {{
                if (!isListening) return;
                if (preAmpToggle.checked) {{
                    initAudioPreAmp();
                }} else {{
                    stopAudioPreAmp();
                }}
            }}

            function startReactiveWave() {{
                const canvas = document.getElementById("waveCanvas");
                const ctx = canvas.getContext("2d");
                const bars = 24;
                const freqData = analyserNode ? new Uint8Array(analyserNode.frequencyBinCount) : null;

                function renderWave() {{
                    if (!isListening) {{
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        return;
                    }}
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    const barW = canvas.width / bars;

                    if (analyserNode && freqData) {{
                        analyserNode.getByteFrequencyData(freqData);
                        for (let i = 0; i < bars; i++) {{
                            const val = freqData[i % freqData.length] || 0;
                            const h = Math.max(4, Math.min(canvas.height - 2, (val / 255) * canvas.height * 1.25));
                            const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
                            grad.addColorStop(0, "#0284C7");
                            grad.addColorStop(1, "#67E8F9");
                            ctx.fillStyle = grad;
                            ctx.fillRect(i * barW + 1, canvas.height - h, barW - 3, h);
                        }}
                    }} else {{
                        const now = Date.now();
                        const isSpeakingNow = (now - lastSpeechActivity) < 650;
                        for (let i = 0; i < bars; i++) {{
                            const base = isSpeakingNow ? (Math.sin(now / 80 + i * 0.7) * 0.45 + 0.55) : 0.16;
                            const jitter = isSpeakingNow ? Math.random() * 0.35 : Math.random() * 0.08;
                            const h = Math.max(4, Math.min(canvas.height - 2, (base + jitter) * canvas.height));
                            const grad = ctx.createLinearGradient(0, canvas.height, 0, 0);
                            grad.addColorStop(0, "#0284C7");
                            grad.addColorStop(1, "#67E8F9");
                            ctx.fillStyle = grad;
                            ctx.fillRect(i * barW + 1, canvas.height - h, barW - 3, h);
                        }}
                    }}
                    waveAnimId = requestAnimationFrame(renderWave);
                }}
                renderWave();
            }}

            async function translateSentence(text, srcLangCode, tgtLang) {{
                const srcShort = srcLangCode.split("-")[0];
                if (srcShort === tgtLang) return text;

                let processedText = text;
                if (srcShort === "ru") {{
                    Object.keys(SLANG_MAP).forEach(slang => {{
                        const regex = new RegExp("\\\\b" + slang + "\\\\b", "gi");
                        processedText = processedText.replace(regex, SLANG_MAP[slang]);
                    }});
                }}

                try {{
                    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${{srcShort}}&tl=${{tgtLang}}&dt=t&q=${{encodeURIComponent(processedText)}}`;
                    const res = await fetch(url);
                    const data = await res.json();
                    if (Array.isArray(data) && Array.isArray(data[0])) {{
                        return data[0].map(item => item[0]).join("");
                    }}
                }} catch (err) {{
                    return "[Đang chờ kết nối dịch tự động...]";
                }}
                return "...";
            }}

            function appendSubtitleCard(originalText, srcLangCode, tgtLang) {{
                const cleanOrig = (originalText || "").trim();
                if (!cleanOrig) return;

                const hintEl = document.getElementById("emptyHint");
                if (hintEl) hintEl.style.display = "none";

                const now = new Date();
                const timeStr = now.toLocaleTimeString("vi-VN", {{ hour: "2-digit", minute: "2-digit", second: "2-digit" }});
                const itemId = "sub-" + Date.now() + "-" + Math.floor(Math.random() * 1000);

                const card = document.createElement("div");
                card.className = "sub-item";
                card.innerHTML = `
                    <div class="sub-meta">
                        <span>🕒 ${{timeStr}} • Nguồn: ${{srcLangCode}}</span>
                        <span>⚓ ${{SELECTED_DOMAIN}}</span>
                    </div>
                    <div class="sub-source">🗣️ ${{cleanOrig}}</div>
                    <div id="${{itemId}}" class="sub-target">⏳ Đang dịch tức thì...</div>
                `;
                subtitleStream.appendChild(card);
                subtitleStream.scrollTop = subtitleStream.scrollHeight;

                translateSentence(cleanOrig, srcLangCode, tgtLang).then(translated => {{
                    const targetEl = document.getElementById(itemId);
                    if (targetEl) {{
                        targetEl.innerHTML = `🌊 ${{translated}}`;
                    }}
                    lectureHistory.push({{
                        time: timeStr,
                        source: cleanOrig,
                        translated: translated
                    }});
                    subtitleStream.scrollTop = subtitleStream.scrollHeight;
                }});
            }}

            function forceCommitInterim() {{
                if (currentInterimBuffer.trim().length > 0) {{
                    const textToCommit = currentInterimBuffer.trim();
                    currentInterimBuffer = "";
                    interimText.innerText = "...";
                    interimLiveTrans.innerText = "🌊 Đang bắt âm câu tiếp theo...";
                    appendSubtitleCard(textToCommit, sourceLangSelect.value, targetLangSelect.value);
                    if (isListening && recognition) {{
                        try {{ recognition.stop(); }} catch (e) {{}}
                    }}
                }}
            }}

            function scheduleLiveInterimTranslation(text) {{
                if (liveTranslateTimer) clearTimeout(liveTranslateTimer);
                liveTranslateTimer = setTimeout(() => {{
                    if (!text || text.trim().length < 2) return;
                    translateSentence(text.trim(), sourceLangSelect.value, targetLangSelect.value).then(trans => {{
                        if (currentInterimBuffer.trim().length > 0) {{
                            interimLiveTrans.innerText = "🌊 Dịch trực tiếp: " + trans;
                        }}
                    }});
                }}, liveTranslateDelayMs);
            }}

            function pickBestTranscript(resultItem) {{
                if (!resultItem || resultItem.length === 0) return "";
                let bestText = resultItem[0].transcript || "";
                let bestScore = (resultItem[0].confidence || 0.5) * Math.max(1, bestText.trim().length);
                for (let k = 1; k < resultItem.length; k++) {{
                    const candText = resultItem[k].transcript || "";
                    const conf = resultItem[k].confidence || 0.5;
                    const score = conf * Math.max(1, candText.trim().length * 1.05);
                    if (candText.trim().length > bestText.trim().length && score >= bestScore * 0.85) {{
                        bestText = candText;
                        bestScore = score;
                    }}
                }}
                return bestText;
            }}

            async function startRecognition() {{
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {{
                    statusText.innerText = "⚠️ Trình duyệt chưa hỗ trợ Web Speech API. Hãy mở bằng Google Chrome hoặc Microsoft Edge (hoặc dùng mục Thu âm bên dưới)!";
                    return;
                }}

                if (isListening) return;
                updateSensitivitySettings();
                await initAudioPreAmp();

                try {{
                    recognition = new SpeechRecognition();
                    recognition.lang = sourceLangSelect.value;
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    recognition.maxAlternatives = 3;

                    recognition.onstart = () => {{
                        isListening = true;
                        statusDot.classList.add("active");
                        statusText.innerText = `🟢 Đang nghe độ nhạy cao (${{sourceLangSelect.options[sourceLangSelect.selectedIndex].text}}) — Hãy nói vào Mic...`;
                        btnStart.disabled = true;
                        btnFlush.disabled = false;
                        btnPause.disabled = false;
                        startReactiveWave();
                    }};

                    recognition.onresult = (event) => {{
                        lastSpeechActivity = Date.now();
                        let interimTranscript = "";

                        for (let i = event.resultIndex; i < event.results.length; ++i) {{
                            const transcript = pickBestTranscript(event.results[i]);
                            if (event.results[i].isFinal) {{
                                const finalSentence = transcript.trim();
                                if (finalSentence.length > 0) {{
                                    currentInterimBuffer = "";
                                    if (autoCommitTimer) clearTimeout(autoCommitTimer);
                                    appendSubtitleCard(finalSentence, sourceLangSelect.value, targetLangSelect.value);
                                }}
                                interimText.innerText = "...";
                                interimLiveTrans.innerText = "🌊 Đang nghe câu tiếp theo...";
                            }} else {{
                                interimTranscript += transcript;
                            }}
                        }}

                        if (interimTranscript.trim().length > 0) {{
                            currentInterimBuffer = interimTranscript.trim();
                            interimText.innerText = currentInterimBuffer;
                            scheduleLiveInterimTranslation(currentInterimBuffer);

                            if (autoCommitTimer) clearTimeout(autoCommitTimer);
                            const wordCount = currentInterimBuffer.split(/\\s+/).length;
                            if (wordCount >= maxWordsBeforeCommit) {{
                                forceCommitInterim();
                            }} else {{
                                autoCommitTimer = setTimeout(() => {{
                                    if (currentInterimBuffer.trim().length > 0) {{
                                        forceCommitInterim();
                                    }}
                                }}, silenceCommitMs);
                            }}
                        }}
                    }};

                    recognition.onerror = (event) => {{
                        if (event.error === "not-allowed" || event.error === "service-not-allowed") {{
                            statusText.innerText = "❌ Trình duyệt đang chặn quyền Microphone! Hãy bấm biểu tượng ổ khóa trên thanh địa chỉ web -> Cho phép Microphone.";
                            stopRecognition();
                        }} else if (event.error === "audio-capture") {{
                            statusText.innerText = "❌ Không tìm thấy thiết bị Microphone!";
                            stopRecognition();
                        }} else if (event.error === "no-speech") {{
                            statusText.innerText = "🟢 Mic đang mở ở chế độ Siêu Nhạy (Đang chờ phát hiện giọng nói...)";
                        }}
                    }};

                    recognition.onend = () => {{
                        if (currentInterimBuffer.trim().length > 0) {{
                            appendSubtitleCard(currentInterimBuffer.trim(), sourceLangSelect.value, targetLangSelect.value);
                            currentInterimBuffer = "";
                        }}
                        if (isListening) {{
                            setTimeout(() => {{
                                if (isListening && recognition) {{
                                    try {{
                                        recognition.lang = sourceLangSelect.value;
                                        recognition.start();
                                    }} catch (e) {{}}
                                }}
                            }}, 50);
                        }}
                    }};

                    sourceLangSelect.onchange = () => {{
                        if (isListening && recognition) {{
                            recognition.lang = sourceLangSelect.value;
                            try {{ recognition.stop(); }} catch (e) {{}}
                        }}
                    }};

                    recognition.start();
                }} catch (err) {{
                    statusText.innerText = "⚠️ Không thể khởi động bộ nhận diện giọng nói: " + err.message;
                }}
            }}

            function stopRecognition() {{
                isListening = false;
                if (autoCommitTimer) clearTimeout(autoCommitTimer);
                if (currentInterimBuffer.trim().length > 0) {{
                    appendSubtitleCard(currentInterimBuffer.trim(), sourceLangSelect.value, targetLangSelect.value);
                    currentInterimBuffer = "";
                }}
                if (recognition) {{
                    try {{ recognition.stop(); }} catch (e) {{}}
                }}
                stopAudioPreAmp();
                if (waveAnimId) cancelAnimationFrame(waveAnimId);
                statusDot.classList.remove("active");
                statusText.innerText = "⏸️ Đã tạm dừng thu âm. Bạn có thể tiếp tục hoặc tải bài giảng về máy.";
                btnStart.disabled = false;
                btnFlush.disabled = true;
                btnPause.disabled = true;
            }}

            function clearTranscript() {{
                lectureHistory = [];
                currentInterimBuffer = "";
                subtitleStream.innerHTML = `
                    <div id="emptyHint" class="empty-hint">
                        🚢 Đã xóa màn hình. Nhấn <b>Bắt đầu nghe</b> để ghi nhận bài giảng mới.
                    </div>
                `;
                interimText.innerText = "...";
                interimLiveTrans.innerText = "🌊 Bản dịch tạm thời sẽ hiện ngay tại đây...";
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
                    content += `[${{idx + 1}}] Thời gian: ${{item.time}}\\n`;
                    content += `🗣️ Lời giảng gốc : ${{item.source}}\\n`;
                    content += `🌊 Bản dịch      : ${{item.translated}}\\n`;
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
# 7. XỬ LÝ THU ÂM BẰNG PYTHON THUẦN (DÙNG ARRAY CHUẨN PYTHON 3.13)
# ==============================================================================
def boost_wav_audio_bytes(audio_bytes: bytes, gain_factor: float = 2.8) -> bytes:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            params = wf.getparams()
            frames = wf.readframes(params.nframes)
            if params.sampwidth != 2:
                return audio_bytes

            samples = array("h")
            samples.frombytes(frames)
            if not samples:
                return audio_bytes

            max_amp = max(abs(x) for x in samples)
            if max_amp > 0:
                auto_gain = min(gain_factor, max(1.2, 28500.0 / max_amp))
            else:
                auto_gain = gain_factor

            for i in range(len(samples)):
                val = int(samples[i] * auto_gain)
                if val > 32767:
                    val = 32767
                elif val < -32768:
                    val = -32768
                samples[i] = val

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
    sensitivity_gain: float = 2.8,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if sr is None:
        return None, None, "Thư viện SpeechRecognition chưa được cài đặt trong requirements.txt."

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 90
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.10
    recognizer.dynamic_energy_ratio = 1.15
    recognizer.pause_threshold = 0.85
    recognizer.non_speaking_duration = 0.4

    boosted_bytes = boost_wav_audio_bytes(audio_bytes, gain_factor=sensitivity_gain)

    try:
        with sr.AudioFile(io.BytesIO(boosted_bytes)) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.15)
            audio_data = recognizer.record(source)

        transcript = recognizer.recognize_google(audio_data, language=source_lang_speech)
        src_short = source_lang_speech.split("-")[0]
        translated = fast_free_translate(transcript, src_short, target_lang_trans)
        return transcript, translated, None
    except sr.UnknownValueError:
        return None, None, "Không nhận diện được lời nói trong đoạn âm thanh (hãy thử kéo thanh Khuếch đại Mic lên mức cao hơn)."
    except sr.RequestError as e:
        return None, None, f"Không thể kết nối tới dịch vụ nhận diện giọng nói: {e}"
    except Exception as e:
        return (
            None,
            None,
            f"Định dạng âm thanh chưa tương thích trực tiếp (hãy ưu tiên thu âm trực tiếp hoặc file .WAV). Chi tiết: {e}",
        )


# ==============================================================================
# 8. GIAO DIỆN CHÍNH (SIDEBAR + HEADER TÁC GIẢ CỐ ĐỊNH + 2 TAB CHỨC NĂNG)
# ==============================================================================
def main() -> None:
    inject_ocean_blue_css()

    if "input_text_area" not in st.session_state:
        st.session_state["input_text_area"] = ""

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

        render_html(
            f"""
            <div style="display:flex; align-items:center; gap:10px; margin-top:4px; margin-bottom:8px;">
                {STICKER_HELM_WHEEL}
                <span style="font-size:1.1rem; font-weight:800; color:#FFFFFF;">Buồng Lái Hệ Thống</span>
            </div>
            """
        )

        gemini_api_key = st.text_input(
            "🔑 Gemini API Key (Chấp nhận mọi Key):",
            type="password",
            placeholder="Dán bất kỳ Gemini API Key nào (hoặc để trống)",
            help="Hỗ trợ mọi loại Gemini API Key (2.5-flash, 2.0-flash, 1.5-flash, 1.5-pro...). Nếu để trống, ứng dụng tự động dùng chế độ Dịch Đa Luồng GTX Siêu Tốc 5 cổng miễn phí!",
        )

        render_html(
            f"""
            <a href="{GEMINI_API_KEY_URL}" target="_blank" rel="noopener noreferrer" class="gemini-key-link-btn">
                🔗 Lấy Gemini API Key miễn phí (Mở tab mới) ↗
            </a>
            """
        )

        clean_key_input = clean_api_key(gemini_api_key)
        if clean_key_input:
            avail_models = discover_available_gemini_models(clean_key_input)
            top_model = avail_models[0] if avail_models else "gemini-flash"
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

        with st.container(height=280):
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
        render_html(
            f"""
            <div style="text-align:center; font-size:0.82rem; padding: 8px; background: rgba(255,255,255,0.08); border-radius: 12px;">
                {STICKER_SAILBOAT_MINI}<br/>
                <b>Anh Minh Translate v5.2 (5-Port GTX & All-Gemini)</b><br/>
                Tác giả: <b>Mai Văn Minh</b><br/>
                <i>Đóng tàu — СПбГМТУ (Xanh-Petecbua)</i>
            </div>
            """
        )

    render_brand_header(avatar_uri)

    tab1, tab2 = st.tabs(
        [
            "📝 TAB 1: DỊCH VĂN BẢN & TIN NHẮN SIÊU TỐC",
            "🎙️ TAB 2: GIẢNG ĐƯỜNG — DỊCH GIỌNG NÓI (MIC SIÊU NHẠY)",
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

                # Nếu có bất kỳ Gemini API Key nào được nhập, thử gọi Gemini trước
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

                # Nếu không có Key hoặc Key tạm hết hạn mức -> Tự động dùng Dịch Đa Luồng GTX 5 cổng
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
        render_html(
            f"""
            <div class="ocean-card" style="padding: 18px 24px; margin-bottom: 14px;">
                <div class="ocean-card-header" style="margin-bottom: 8px; padding-bottom: 8px;">
                    <div class="ocean-card-title">{STICKER_COMPASS_3D} Trợ lý Nghe Giảng Trực Tiếp (Đã nâng cấp Mic Siêu Nhạy & Khuếch đại Âm)</div>
                    <span class="ocean-pill">🔥 Bắt âm giảng đường rộng • Hỗ trợ Mobile</span>
                </div>
                <div style="font-size:0.94rem; color:#1E293B; line-height:1.6;">
                    💡 <b>Tính năng mới:</b> Tích hợp bộ lọc dải tần giọng nói và chế độ <b>«🔥 Cực nhạy — Giảng đường rộng»</b> cùng tính năng <b>Khuếch đại giọng nói nhỏ (Gain Boost x3.0)</b> giúp bắt rõ lời giảng viên ngay cả khi ngồi bàn xa.
                </div>
            </div>
            """
        )

        realtime_html = build_realtime_lecture_component(
            gemini_api_key=clean_key_input,
            selected_domain=selected_domain,
        )
        components.html(realtime_html, height=680, scrolling=False)

        render_html(
            f'<div class="nautical-divider">{STICKER_ANCHOR_3D} THU ÂM ĐỘ NHẠY CAO CHO ĐIỆN THOẠI & MỌI TRÌNH DUYỆT {STICKER_ANCHOR_3D}</div>'
        )

        render_html(
            f"""
            <div class="ocean-card">
                <div class="ocean-card-header">
                    <div class="ocean-card-title">{STICKER_HELM_WHEEL} Thu Âm Trực Tiếp Có Khuếch Đại Biên Độ Âm (Tương thích 100% iOS / Android / Safari / Chrome)</div>
                    <span class="ocean-pill">Audio Pre-Amp + Python SpeechRecognition</span>
                </div>
                <div style="font-size:0.94rem; color:#334155;">
                    Khi dùng trên <b>điện thoại (iPhone/Android)</b> hoặc trong phòng lớn, bạn chỉ cần nhấn biểu tượng Micro bên dưới. Hệ thống sẽ tự động kích hoạt bộ khuếch đại biên độ âm thanh (Audio Gain Boost) để nhận diện chính xác cả những câu nói nhỏ:
                </div>
            </div>
            """
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

            mic_gain_level = st.slider(
                "🎚️ Độ nhạy & Khuếch đại âm lượng Mic (Gain Boost):",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5,
                help="Kéo lên 3.0 - 5.0 khi thu âm giảng viên đứng ở xa hoặc nói nhỏ.",
            )

        with up_col2:
            recorded_mic = None
            if hasattr(st, "audio_input"):
                recorded_mic = st.audio_input("🎙️ Nhấn vào Micro để thu âm trên Điện thoại / Máy tính (Tự động dịch ngay khi dừng):")
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
            with st.spinner(f"⏳ Đang khuếch đại âm thanh (x{mic_gain_level}) và dịch thuật siêu tốc..."):
                transcript_text, translated_text, err = transcribe_and_translate_audio_bytes(
                    audio_bytes=audio_source_bytes,
                    source_lang_speech=file_speech_lang,
                    target_lang_trans=file_target_lang,
                    sensitivity_gain=mic_gain_level,
                )
                if err:
                    st.error(f"⚠️ {err}")
                else:
                    render_html(
                        f"""
                        <div class="ocean-card">
                            <div class="ocean-card-header">
                                <div class="ocean-card-title">✅ Kết quả Nhận diện Giọng nói (Gain x{mic_gain_level}) & Dịch thuật</div>
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
