"""
Anh Minh Translate — Các thành phần giao diện (CSS, thẻ kết quả dịch, ôn tập & cẩm nang)
Tác giả: Mai Văn Minh — Sinh viên năm 4, Chuyên ngành Đóng tàu, СПбГМТУ (Xanh-Petecbua)
"""

import base64
import csv
from datetime import datetime, timedelta
import hashlib
import html
import io
import json
from pathlib import Path
import random
import re
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from data import (
    FIXED_AUTHOR_AVATAR_BASE64_OR_URL,
    KNOWLEDGE_HUB_CONTENT,
    KNOWLEDGE_HUB_TOPICS,
    RUSSIAN_ALPHABET_SAMPLES,
    RUSSIAN_SLANG_DICT,
    SESSION_TOKEN_TTL_DAYS,
    STARTER_VOCAB_DECKS,
)
from services import (
    DEFAULT_AUTHOR_PASSWORD,
    _get_browser_cookie,
    _generate_quiz_question,
    add_vocab_items_to_notebook,
    apply_vocab_review_rating,
    create_admin_token,
    create_session_token,
    export_vocab_to_anki_csv,
    generate_tts_audio,
    is_vocab_due_today,
    sync_current_account_to_db,
    verify_admin_token,
)


def esc(text: Any) -> str:
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def render_html(html_str: str) -> None:
    cleaned_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    st.markdown("\n".join(cleaned_lines), unsafe_allow_html=True)


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


def save_remembered_login(username: str, token_version: int = 1) -> None:
    """Lưu ghi nhớ đăng nhập cục bộ trên trình duyệt bằng Cookie (am_rtok) và localStorage."""
    tok = create_session_token(username, token_version=token_version)
    safe_tok = json.dumps(tok)
    max_age = SESSION_TOKEN_TTL_DAYS * 86400
    components.html(
        f"""
        <script>
        (function() {{
            const t = {safe_tok};
            const isHttps = (location.protocol === "https:");
            const sec = isHttps ? "; Secure" : "";
            const c = "am_rtok=" + encodeURIComponent(t) + "; path=/; max-age={max_age}; SameSite=Lax" + sec;
            for (const w of [window.top, window.parent, window]) {{
                try {{ if (w && w.localStorage) w.localStorage.setItem("am_remember_token", t); }} catch (e) {{}}
                try {{ if (w && w.document) w.document.cookie = c; }} catch (e) {{}}
            }}
        }})();
        </script>
        """,
        height=0,
    )


def clear_remembered_login() -> None:
    components.html(
        """
        <script>
        (function() {
            const c = "am_rtok=; path=/; max-age=0; SameSite=Lax";
            const cSec = "am_rtok=; path=/; max-age=0; SameSite=Lax; Secure";
            for (const w of [window.top, window.parent, window]) {
                try { if (w && w.localStorage) w.localStorage.removeItem("am_remember_token"); } catch (e) {}
                try { if (w && w.document) { w.document.cookie = c; w.document.cookie = cSec; } } catch (e) {}
            }
        })();
        </script>
        """,
        height=0,
    )


def save_remembered_admin() -> None:
    """Lưu cố định quyền Tác giả trên thiết bị bằng Cookie (am_atok), localStorage và đồng bộ tài khoản."""
    if not DEFAULT_AUTHOR_PASSWORD:
        return
    atok = create_admin_token()
    try:
        if verify_admin_token(_get_browser_cookie("am_atok")):
            if "a" in st.query_params:
                del st.query_params["a"]
        else:
            st.query_params["a"] = atok
    except Exception:
        pass
    if st.session_state.get("auth_username"):
        sync_current_account_to_db()
    safe_atok = json.dumps(atok)
    components.html(
        f"""
        <script>
        (function() {{
            const a = {safe_atok};
            const isHttps = (location.protocol === "https:");
            const sec = isHttps ? "; Secure" : "";
            const c = "am_atok=" + encodeURIComponent(a) + "; path=/; max-age=31536000; SameSite=Lax" + sec;
            for (const w of [window.top, window.parent, window]) {{
                try {{ if (w && w.localStorage) w.localStorage.setItem("am_admin_token", a); }} catch (e) {{}}
                try {{ if (w && w.document) w.document.cookie = c; }} catch (e) {{}}
            }}
        }})();
        </script>
        """,
        height=0,
    )


def clear_remembered_admin() -> None:
    try:
        if "a" in st.query_params:
            del st.query_params["a"]
    except Exception:
        pass
    if st.session_state.get("auth_username"):
        sync_current_account_to_db()
    components.html(
        """
        <script>
        (function() {
            const c = "am_atok=; path=/; max-age=0; SameSite=Lax";
            const cSec = "am_atok=; path=/; max-age=0; SameSite=Lax; Secure";
            for (const w of [window.top, window.parent, window]) {
                try { if (w && w.localStorage) w.localStorage.removeItem("am_admin_token"); } catch (e) {}
                try { if (w && w.document) { w.document.cookie = c; w.document.cookie = cSec; } } catch (e) {}
            }
        })();
        </script>
        """,
        height=0,
    )


def bootstrap_remembered_tokens_js(need_user: bool = True, need_admin: bool = True) -> None:
    """Đọc lại token đăng nhập & token tác giả từ localStorage/Cookie khi mở lại link gốc."""
    components.html(
        f"""
        <script>
        (function() {{
            function readStore(key) {{
                for (const w of [window.top, window.parent, window]) {{
                    try {{
                        const v = w && w.localStorage && w.localStorage.getItem(key);
                        if (v) return v;
                    }} catch (e) {{}}
                }}
                return "";
            }}
            function readCookie(name) {{
                for (const w of [window.top, window.parent, window]) {{
                    try {{
                        const raw = (w && w.document && w.document.cookie) || "";
                        for (const part of raw.split(";")) {{
                            const kv = part.trim().split("=");
                            if (kv[0] === name && kv[1]) return decodeURIComponent(kv.slice(1).join("="));
                        }}
                    }} catch (e) {{}}
                }}
                return "";
            }}
            let targetWin = null;
            for (const w of [window.top, window.parent]) {{
                try {{ if (w && w.location && w.location.href) {{ targetWin = w; break; }} }} catch (e) {{}}
            }}
            if (!targetWin) return;
            try {{
                const url = new URL(targetWin.location.href);
                let changed = false;
                if ({'true' if need_user else 'false'}) {{
                    const t = readStore("am_remember_token") || readCookie("am_rtok");
                    if (t && t.includes(".") && url.searchParams.get("s") !== t) {{
                        url.searchParams.set("s", t);
                        changed = true;
                    }}
                }}
                if ({'true' if need_admin else 'false'}) {{
                    const a = readStore("am_admin_token") || readCookie("am_atok");
                    if (a && a.length >= 16 && url.searchParams.get("a") !== a) {{
                        url.searchParams.set("a", a);
                        changed = true;
                    }}
                }}
                const lastTry = parseInt(sessionStorage.getItem("am_tok_sync_ts") || "0", 10);
                if (changed && (Date.now() - lastTry > 2000)) {{
                    sessionStorage.setItem("am_tok_sync_ts", String(Date.now()));
                    targetWin.location.replace(url.toString());
                }}
            }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
    )


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
        text_sub = "#D4D4D8"
        text_muted = "#A1A1AA"
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

        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4,
        [data-testid="stMain"] p,
        [data-testid="stMain"] label,
        [data-testid="stMain"] span:not([data-testid="stIconMaterial"]),
        [data-testid="stMain"] li,
        [data-testid="stMain"] strong,
        [data-testid="stMain"] b,
        .main p, .main label, .main h1, .main h2, .main h3, .main h4,
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li,
        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] p,
        div[data-testid="stCheckbox"] label,
        div[data-testid="stCheckbox"] p {{
            color: {text_main} !important;
        }}

        [data-testid="stMain"] code,
        section[data-testid="stSidebar"] code {{
            background-color: {bg_subtle} !important;
            color: {text_main} !important;
            border: 1px solid {border_strong} !important;
            padding: 1px 5px !important;
            border-radius: 5px !important;
        }}

        div[data-testid="stAlert"],
        div[data-testid="stAlertContainer"],
        div[role="alert"],
        div[data-baseweb="notification"] {{
            background-color: {bg_subtle} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            color: {text_main} !important;
        }}
        div[data-testid="stAlert"] *,
        div[data-testid="stAlertContainer"] *,
        div[role="alert"] *,
        div[data-baseweb="notification"] * {{
            color: {text_main} !important;
        }}
        div[data-testid="stToast"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            color: {text_main} !important;
        }}
        div[data-testid="stToast"] * {{
            color: {text_main} !important;
        }}

        [data-testid="stMain"] a {{
            color: {link_color} !important;
        }}

        div[data-testid="stCaptionContainer"] p {{
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
        div[data-baseweb="input"] button,
        div[data-testid="stTextInput"] button {{
            background-color: {bg_surface} !important;
            color: {text_main} !important;
            border: none !important;
        }}
        div[data-baseweb="input"] button svg,
        div[data-testid="stTextInput"] button svg {{
            fill: {text_main} !important;
            color: {text_main} !important;
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
        div[data-testid="stFormSubmitButton"] button,
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
        div[data-testid="stFormSubmitButton"] button *,
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
            color: {text_main} !important;
        }}
        .sidebar-author-box div {{
            color: {text_main} !important;
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


def render_russian_knowledge_hub() -> None:
    topic = st.radio(
        "Chọn chuyên đề",
        options=KNOWLEDGE_HUB_TOPICS,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )
    html_content = KNOWLEDGE_HUB_CONTENT.get(topic, "")
    if html_content:
        render_html(html_content)

    if topic.startswith("0."):
        st.markdown("#### Nghe phát âm mẫu theo chữ cái & từ ví dụ")
        sample_labels = [
            f"{item['letter']} — {item['example']} (đọc: {item['sound']})"
            for item in RUSSIAN_ALPHABET_SAMPLES
        ]
        sc1, sc2 = st.columns([3.2, 1.4])
        with sc1:
            selected_lbl = st.selectbox(
                "Chọn chữ cái hoặc từ ví dụ",
                options=sample_labels,
                label_visibility="collapsed",
                key="alphabet_sample_select",
            )
        with sc2:
            if st.button("Nghe phát âm mẫu", key="btn_alphabet_tts", type="primary", use_container_width=True):
                sel_idx = sample_labels.index(selected_lbl)
                sample_item = RUSSIAN_ALPHABET_SAMPLES[sel_idx]
                ex_word = sample_item["example"].split("(")[0].replace("\u0301", "").strip()
                is_slow = bool(st.session_state.get("tts_slow_mode", False))
                ab = generate_tts_audio(ex_word, "ru", slow=is_slow)
                if ab:
                    st.audio(ab, format="audio/mp3")


def render_vocab_and_practice_tab() -> None:
    saved_list = st.session_state["saved_vocab_notebook"]
    mastered_cnt = sum(1 for v in saved_list if v.get("mastered"))
    due_today_cnt = sum(1 for v in saved_list if is_vocab_due_today(v))
    pct = int(round((mastered_cnt / len(saved_list)) * 100)) if saved_list else 0

    if not st.session_state.get("auth_username"):
        st.info("Đăng nhập hoặc tạo tài khoản ở thanh bên trái để lưu vĩnh viễn và đồng bộ Sổ từ vựng + Lịch sử trên mọi thiết bị.")

    render_html(
        f"""
        <div class="stat-grid">
            <div class="stat-box"><div class="stat-num">{len(saved_list)}</div><div class="stat-lbl">Tổng từ trong sổ</div></div>
            <div class="stat-box"><div class="stat-num">{mastered_cnt}</div><div class="stat-lbl">Đã thuộc ({pct}%)</div></div>
            <div class="stat-box"><div class="stat-num">{due_today_cnt}</div><div class="stat-lbl">Cần ôn hôm nay</div></div>
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
        {
            "ru_accent": f"{x['accent']} ({x['full']})",
            "vi": x["vi"],
            "en": x["en"],
            "example": x.get("example", ""),
            "mastered": False,
        }
        for x in RUSSIAN_SLANG_DICT
    ]
    starter_names = list(STARTER_VOCAB_DECKS.keys())
    is_slow_tts = bool(st.session_state.get("tts_slow_mode", False))

    if mode == "Thẻ ghi nhớ (Flashcards)":
        deck_options = ["Cần ôn hôm nay (Sổ cá nhân)", "Tất cả từ trong sổ"] + starter_names + ["30 từ lóng sinh viên Nga"]
        default_fc_deck = "Cần ôn hôm nay (Sổ cá nhân)" if due_today_cnt > 0 else starter_names[0]
        if st.session_state.get("selected_fc_deck") not in deck_options:
            st.session_state["selected_fc_deck"] = default_fc_deck

        st.caption("Chọn nhanh bộ từ vựng nhập môn A0–A1 (thực chiến):")
        q_cols = st.columns(4)
        for i_d, d_name in enumerate(starter_names):
            short_lbl = d_name.split(". ", 1)[-1]
            with q_cols[i_d]:
                btn_type = "primary" if st.session_state["selected_fc_deck"] == d_name else "secondary"
                if st.button(f"{short_lbl} ({len(STARTER_VOCAB_DECKS[d_name])})", key=f"quick_fc_{i_d}", type=btn_type, use_container_width=True):
                    st.session_state["selected_fc_deck"] = d_name
                    st.session_state["flashcard_index"] = 0
                    st.session_state["flashcard_show_back"] = False
                    st.rerun()

        fc1, fc2 = st.columns([2.2, 1])
        with fc1:
            deck_choice = st.selectbox(
                "Bộ thẻ",
                options=deck_options,
                index=deck_options.index(st.session_state["selected_fc_deck"]),
                label_visibility="collapsed",
            )
            st.session_state["selected_fc_deck"] = deck_choice
            if st.session_state.get("last_flashcard_deck") != deck_choice:
                st.session_state["last_flashcard_deck"] = deck_choice
                st.session_state["flashcard_index"] = 0
                st.session_state["flashcard_show_back"] = False
        with fc2:
            if st.button("Xáo trộn thẻ", use_container_width=True):
                if deck_choice in ("Cần ôn hôm nay (Sổ cá nhân)", "Tất cả từ trong sổ") and saved_list:
                    random.shuffle(saved_list)
                elif deck_choice in STARTER_VOCAB_DECKS:
                    random.shuffle(STARTER_VOCAB_DECKS[deck_choice])
                st.session_state["flashcard_index"] = 0
                st.session_state["flashcard_show_back"] = False
                st.rerun()

        is_personal_deck = deck_choice in ("Cần ôn hôm nay (Sổ cá nhân)", "Tất cả từ trong sổ")
        is_starter_deck = deck_choice in STARTER_VOCAB_DECKS

        if deck_choice == "Cần ôn hôm nay (Sổ cá nhân)":
            active_deck = [v for v in saved_list if is_vocab_due_today(v)]
        elif deck_choice == "Tất cả từ trong sổ":
            active_deck = saved_list
        elif is_starter_deck:
            active_deck = STARTER_VOCAB_DECKS[deck_choice]
        else:
            active_deck = slang_deck

        if not active_deck:
            if deck_choice == "Cần ôn hôm nay (Sổ cá nhân)" and saved_list:
                st.success("Bạn đã ôn hết toàn bộ từ đến hạn hôm nay! Hãy chọn 4 bộ nhập môn A0–A1 hoặc «Tất cả từ trong sổ» để học thêm.")
            else:
                st.info("Không có thẻ nào trong bộ này. Hãy lưu từ ở Tab 1 hoặc chọn một trong 4 bộ từ vựng nhập môn A0–A1.")
            return

        idx = st.session_state["flashcard_index"] % len(active_deck)
        card = active_deck[idx]
        lvl = int(card.get("level", 2 if card.get("mastered") else 0))
        lvl_label = {0: "Chưa nhớ", 1: "Nhớ mang máng", 2: "Thuộc kỹ"}.get(lvl, "")
        status_tag = f" · {lvl_label}" if is_personal_deck and lvl_label else ""

        pron_txt = str(card.get("pronunciation") or card.get("pronunciation_hint") or "").strip()
        pron_html = (
            f'<div style="font-size:0.9rem;opacity:0.78;font-weight:400;margin-top:4px;">Phiên âm: {esc(pron_txt)}</div>'
            if pron_txt
            else ""
        )
        en_html = (
            f'<div style="font-size:0.86rem;opacity:0.72;font-weight:400;margin-top:3px;">{esc(card.get("en", ""))}</div>'
            if card.get("en")
            else ""
        )
        ex_html = (
            f'<div style="font-size:0.88rem;opacity:0.84;font-weight:400;margin-top:8px;">VD: <i>{esc(card.get("example", ""))}</i></div>'
            if card.get("example")
            else ""
        )

        back_html = (
            f'<div class="flashcard-back">{esc(card["vi"])}{pron_html}{en_html}{ex_html}</div>'
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

        b1, b2, b3, b4 = st.columns(4)
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
                ab = generate_tts_audio(ru_clean, "ru", slow=is_slow_tts)
                if ab:
                    st.audio(ab, format="audio/mp3")
        with b4:
            if st.button("Tiếp", use_container_width=True):
                st.session_state["flashcard_index"] = (idx + 1) % len(active_deck)
                st.session_state["flashcard_show_back"] = False
                st.rerun()

        if is_personal_deck and st.session_state["flashcard_show_back"]:
            st.caption("Đánh giá mức độ nhớ để lên lịch nhắc ôn:")
            r1, r2, r3 = st.columns(3)
            with r1:
                if st.button("Chưa nhớ (Ôn lại)", key="rate_0", use_container_width=True):
                    apply_vocab_review_rating(card["ru_accent"], 0)
                    st.session_state["flashcard_show_back"] = False
                    st.rerun()
            with r2:
                if st.button("Nhớ mang máng (+1 ngày)", key="rate_1", use_container_width=True):
                    apply_vocab_review_rating(card["ru_accent"], 1)
                    st.session_state["flashcard_show_back"] = False
                    st.rerun()
            with r3:
                if st.button("Thuộc kỹ (+5 ngày)", key="rate_2", type="primary", use_container_width=True):
                    apply_vocab_review_rating(card["ru_accent"], 2)
                    st.session_state["flashcard_show_back"] = False
                    st.rerun()
        elif not is_personal_deck:
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("Lưu thẻ này vào sổ", key="btn_save_one_starter", use_container_width=True):
                    cnt = add_vocab_items_to_notebook([card])
                    st.toast("Đã lưu thẻ vào sổ cá nhân." if cnt else "Từ này đã có trong sổ.")
            with sc2:
                if is_starter_deck and st.button("Lưu cả bộ vào sổ", key="btn_save_all_starter", use_container_width=True):
                    cnt = add_vocab_items_to_notebook(active_deck)
                    st.toast(f"Đã lưu thêm {cnt} từ mới vào sổ cá nhân." if cnt else "Toàn bộ thẻ trong bộ này đã có trong sổ.")

    elif mode == "Trắc nghiệm (Quiz)":
        quiz_sources = ["Sổ cá nhân"] + starter_names + ["30 từ lóng sinh viên Nga"]
        default_quiz_src = "Sổ cá nhân" if len(saved_list) >= 4 else starter_names[0]
        if st.session_state.get("selected_quiz_src") not in quiz_sources:
            st.session_state["selected_quiz_src"] = default_quiz_src
        qs1, qs2 = st.columns([2, 1.5])
        with qs1:
            quiz_src = st.selectbox(
                "Nguồn câu hỏi",
                options=quiz_sources,
                index=quiz_sources.index(st.session_state["selected_quiz_src"]),
                label_visibility="collapsed",
            )
            st.session_state["selected_quiz_src"] = quiz_src
        with qs2:
            st.caption(f"Điểm: **{st.session_state['quiz_score']} / {st.session_state['quiz_total']}**")

        quiz_dir_label = st.radio(
            "Chiều kiểm tra",
            options=["Nga → Việt", "Việt → Nga", "Nghe âm thanh → Chọn nghĩa"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if quiz_dir_label == "Việt → Nga":
            q_dir = "vi_to_ru"
        elif quiz_dir_label == "Nghe âm thanh → Chọn nghĩa":
            q_dir = "audio_to_vi"
        else:
            q_dir = "ru_to_vi"

        if quiz_src == "Sổ cá nhân":
            due_pool = [v for v in saved_list if is_vocab_due_today(v)]
            pool = due_pool if len(due_pool) >= 4 else saved_list
        elif quiz_src in STARTER_VOCAB_DECKS:
            pool = STARTER_VOCAB_DECKS[quiz_src]
        else:
            pool = slang_deck

        if len(pool) < 4:
            st.info(f"Nguồn «{quiz_src}» hiện có {len(pool)} từ (cần ít nhất 4 từ để tạo trắc nghiệm). Hãy lưu thêm từ hoặc chọn một trong 4 bộ nhập môn A0–A1.")
            return

        if (
            st.session_state.get("current_quiz") is None
            or st.session_state.get("last_quiz_dir") != q_dir
            or st.session_state.get("last_quiz_src") != quiz_src
        ):
            st.session_state["last_quiz_dir"] = q_dir
            st.session_state["last_quiz_src"] = quiz_src
            st.session_state["current_quiz"] = _generate_quiz_question(pool, q_dir)

        q = st.session_state["current_quiz"]
        if q:
            if q.get("mode") == "audio_to_vi":
                render_html(
                    f"""
                    <div class="clean-card" style="text-align:center;padding:22px;">
                        <div style="font-size:0.86rem;opacity:0.78;margin-bottom:4px;">{esc(q['sub_hint'])}</div>
                        <div style="font-size:1.1rem;font-weight:600;opacity:0.85;">(Chữ tiếng Nga sẽ hiện sau khi bạn chọn đáp án)</div>
                    </div>
                    """
                )
                if st.button("Nghe từ cần đoán", key="btn_quiz_listen", type="primary", use_container_width=True):
                    ab = generate_tts_audio(q.get("audio_text", ""), "ru", slow=is_slow_tts)
                    if ab:
                        st.audio(ab, format="audio/mp3")
            else:
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
                if q.get("mode") == "audio_to_vi":
                    pron_reveal = f" ({q['reveal_pron']})" if q.get("reveal_pron") else ""
                    answer_summary = f"{q.get('reveal_ru', '')}{pron_reveal} = {q['correct']}"
                else:
                    answer_summary = f"{q['prompt']} = {q['correct']}"

                if q["answered"] == q["correct"]:
                    st.success(f"Chính xác: {answer_summary}")
                else:
                    st.error(f"Chưa đúng. Đáp án đúng là: {answer_summary}")
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

                per_page = 20
                total_filtered = len(filtered_my)
                total_pages = max(1, (total_filtered + per_page - 1) // per_page)
                cur_page = max(1, min(int(st.session_state.get("vocab_page", 1)), total_pages))
                st.session_state["vocab_page"] = cur_page
                start_i = (cur_page - 1) * per_page
                page_items = filtered_my[start_i : start_i + per_page]

                for orig_i, v in page_items:
                    rc1, rc2, rc3 = st.columns([3.6, 1.2, 0.7])
                    with rc1:
                        st.markdown(f"**{v['ru_accent']}** — {v['vi']}")
                    with rc2:
                        st_lbl = "Đã thuộc" if v.get("mastered") else "Chưa thuộc"
                        if st.button(st_lbl, key=f"tog_v_{orig_i}", use_container_width=True):
                            saved_list[orig_i]["mastered"] = not v.get("mastered", False)
                            saved_list[orig_i]["level"] = 2 if saved_list[orig_i]["mastered"] else 0
                            saved_list[orig_i]["next_review"] = (
                                (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                                if saved_list[orig_i]["mastered"]
                                else datetime.now().strftime("%Y-%m-%d")
                            )
                            sync_current_account_to_db()
                            st.rerun()
                    with rc3:
                        if st.button("×", key=f"del_v_{orig_i}", use_container_width=True):
                            saved_list.pop(orig_i)
                            sync_current_account_to_db()
                            st.rerun()

                if total_pages > 1:
                    pg1, pg2, pg3 = st.columns([1.2, 1.4, 1.2])
                    with pg1:
                        if st.button("← Trang trước", key="vocab_prev_page", disabled=cur_page <= 1, use_container_width=True):
                            st.session_state["vocab_page"] = cur_page - 1
                            st.rerun()
                    with pg2:
                        st.markdown(f"<div style='text-align:center;padding-top:6px;font-size:0.88rem;'>Trang {cur_page} / {total_pages}</div>", unsafe_allow_html=True)
                    with pg3:
                        if st.button("Trang sau →", key="vocab_next_page", disabled=cur_page >= total_pages, use_container_width=True):
                            st.session_state["vocab_page"] = cur_page + 1
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


def render_translation_result(res: Dict[str, Any], meta_badge: str, is_dark: bool = False) -> None:
    kind_labels = {"word": "Tra từ", "sentence": "Phân tích câu", "paragraph": "Dịch đoạn văn"}
    kind_text = kind_labels.get(res.get("input_kind", ""), "Bản dịch")
    eff_dir = res.get("effective_dir", "")
    header_left = f"{kind_text} · {eff_dir}" if eff_dir else kind_text
    main_trans = res.get("main_translation", "")
    pron_hint = str(res.get("pronunciation_hint", "") or "").strip()
    pron_html = (
        f'<div style="margin-top:8px;font-size:0.9rem;opacity:0.82;"><b>Cách đọc gần đúng:</b> {esc(pron_hint)}</div>'
        if pron_hint
        else ""
    )

    render_html(
        f"""
        <div class="clean-card">
            <div class="clean-label">
                <span>{esc(header_left)}</span>
                <span>{esc(meta_badge)}</span>
            </div>
            <div class="clean-result-text">{esc(main_trans)}</div>
            {pron_html}
        </div>
        """
    )

    morph = res.get("morphology") or {}
    is_word_input = res.get("input_kind") == "word"
    is_slow_tts = bool(st.session_state.get("tts_slow_mode", False))

    if is_word_input:
        c_act1, c_act2, c_act3, _ = st.columns([1.2, 1.35, 1.35, 3.1])
    else:
        c_act1, c_act2, _ = st.columns([1.2, 1.35, 4.45])
        c_act3 = None

    with c_act1:
        render_copy_button(main_trans, "Sao chép", "main_cp", is_dark=is_dark)
    with c_act2:
        tts_lang = "ru" if re.search(r"[а-яА-ЯёЁ]", main_trans) else "vi"
        if st.button("Nghe bản dịch", key="tts_main_btn", use_container_width=True):
            audio_b = generate_tts_audio(main_trans.replace("\u0301", ""), tts_lang, slow=is_slow_tts)
            if audio_b:
                st.audio(audio_b, format="audio/mp3")
    if is_word_input and c_act3 is not None:
        with c_act3:
            if st.button("+ Lưu từ này", key="btn_save_single_word", use_container_width=True):
                ru_word = str(morph.get("lemma") or "").strip() or str(res.get("ru_version") or "").strip()
                if not ru_word and re.search(r"[а-яА-ЯёЁ]", main_trans):
                    ru_word = main_trans.strip()
                vi_meaning = str(res.get("vi_version") or "").strip()
                if not vi_meaning and not re.search(r"[а-яА-ЯёЁ]", main_trans):
                    vi_meaning = main_trans.strip()
                en_meaning = str(res.get("en_version") or "").strip()
                if ru_word and vi_meaning:
                    added_cnt = add_vocab_items_to_notebook(
                        [
                            {
                                "ru_accent": ru_word,
                                "vi": vi_meaning,
                                "en": en_meaning,
                                "pronunciation_hint": pron_hint,
                            }
                        ]
                    )
                    st.toast("Đã lưu từ này vào sổ ôn tập." if added_cnt else "Từ này đã có trong sổ ôn tập.")
                else:
                    st.warning("Chưa đủ dữ liệu tiếng Nga/tiếng Việt để lưu từ này.")
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
                    ab = generate_tts_audio(ex["ru"].replace("\u0301", ""), "ru", slow=is_slow_tts)
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