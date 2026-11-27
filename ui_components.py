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

try:
    import extra_streamlit_components as stx
except Exception:
    stx = None

from data import (
    ALL_VOCAB_DECKS,
    FIXED_AUTHOR_AVATAR_BASE64_OR_URL,
    KNOWLEDGE_HUB_CONTENT,
    KNOWLEDGE_HUB_TOPICS,
    RUSSIAN_ALPHABET_SAMPLES,
    RUSSIAN_SLANG_DICT,
    SESSION_TOKEN_TTL_DAYS,
    STARTER_VOCAB_DECKS,
    VOCAB_DECK_CATEGORIES,
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


_SVG_ICONS: Dict[str, str] = {
    "compass": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>',
    "languages": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/></svg>',
    "book": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>',
    "sparkles": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
    "layers": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "volume": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
    "check_circle": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "clock": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "user": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "info": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    "search": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
}


def svg_icon(name: str) -> str:
    return f'<span class="ui-ico" aria-hidden="true">{_SVG_ICONS.get(name, "")}</span>'


def get_author_monogram_svg_uri() -> str:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
      <rect width="120" height="120" rx="60" fill="#1D4ED8"/>
      <text x="60" y="72" text-anchor="middle" font-family="Inter, -apple-system, sans-serif" font-size="42" font-weight="600" fill="#FFFFFF" letter-spacing="-1">MM</text>
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
    bg = "#131720" if is_dark else "#FFFFFF"
    fg = "#F3F4F6" if is_dark else "#111827"
    bd = "#374151" if is_dark else "#D1D5DB"
    hover_bg = "#1B202C" if is_dark else "#F1F3F6"
    done_bg = "#065F46" if is_dark else "#ECFDF5"
    done_fg = "#34D399" if is_dark else "#047857"
    done_bd = "#059669" if is_dark else "#A7F3D0"
    copy_svg = (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">'
        '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
        '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>'
    )
    check_svg = (
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;">'
        '<polyline points="20 6 9 17 4 12"/></svg>'
    )
    components.html(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            * {{ box-sizing: border-box; }}
            html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; height: 40px; }}
            .cp-btn {{
                width: 100%;
                height: 38px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: {bg};
                color: {fg};
                border: 1px solid {bd};
                border-radius: 9px;
                padding: 0 12px;
                font-size: 14px;
                font-weight: 500;
                line-height: 1;
                cursor: pointer;
                white-space: nowrap;
                transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease;
            }}
            .cp-btn:hover {{
                background: {hover_bg};
            }}
            .cp-btn:focus-visible {{
                outline: 2px solid #3B82F6;
                outline-offset: 1px;
            }}
        </style>
        </head>
        <body>
            <button id="{btn_id}" class="cp-btn" onclick="copyNow()" type="button">
                {copy_svg}<span>{safe_label}</span>
            </button>
            <script>
            const defaultInner = {json.dumps(copy_svg + "<span>" + safe_label + "</span>", ensure_ascii=False)};
            const doneInner = {json.dumps(check_svg + "<span>Đã sao chép</span>", ensure_ascii=False)};
            function copyNow() {{
                const text = {safe_js_text};
                const btn = document.getElementById("{btn_id}");
                const done = () => {{
                    btn.innerHTML = doneInner;
                    btn.style.background = "{done_bg}";
                    btn.style.color = "{done_fg}";
                    btn.style.borderColor = "{done_bd}";
                    setTimeout(() => {{
                        btn.innerHTML = defaultInner;
                        btn.style.background = "{bg}";
                        btn.style.color = "{fg}";
                        btn.style.borderColor = "{bd}";
                    }}, 1600);
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
        height=40,
    )


def get_cookie_manager() -> Any:
    """Khởi tạo CookieManager (extra-streamlit-components) để đọc/ghi Cookie thật trên Streamlit Cloud."""
    if stx is None:
        return None
    try:
        return stx.CookieManager(key="am_cookie_mgr")
    except Exception:
        return None


def save_remembered_login(username: str, token_version: int = 1, cookie_manager: Any = None) -> None:
    """Lưu ghi nhớ đăng nhập cục bộ trên trình duyệt bằng Cookie thật (am_rtok) + fallback localStorage."""
    tok = create_session_token(username, token_version=token_version)
    if cookie_manager is not None:
        try:
            cookie_manager.set(
                "am_rtok",
                tok,
                expires_at=datetime.now() + timedelta(days=SESSION_TOKEN_TTL_DAYS),
                key="set_am_rtok",
            )
        except Exception:
            pass
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


def clear_remembered_login(cookie_manager: Any = None) -> None:
    if cookie_manager is not None:
        try:
            cookie_manager.delete("am_rtok", key="del_am_rtok")
        except Exception:
            pass
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


def save_remembered_admin(cookie_manager: Any = None) -> None:
    """Lưu cố định quyền Tác giả trên thiết bị bằng Cookie thật (am_atok), localStorage và đồng bộ tài khoản."""
    if not DEFAULT_AUTHOR_PASSWORD:
        return
    atok = create_admin_token()
    if cookie_manager is not None:
        try:
            cookie_manager.set(
                "am_atok",
                atok,
                expires_at=datetime.now() + timedelta(days=365),
                key="set_am_atok",
            )
        except Exception:
            pass
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


def clear_remembered_admin(cookie_manager: Any = None) -> None:
    if cookie_manager is not None:
        try:
            cookie_manager.delete("am_atok", key="del_am_atok")
        except Exception:
            pass
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
        bg_page = "#0B0E14"
        bg_surface = "#131720"
        bg_subtle = "#1B202C"
        bg_sidebar = "#0F131B"
        text_main = "#F3F4F6"
        text_sub = "#9CA3AF"
        text_muted = "#6B7280"
        border_light = "#1F2937"
        border_strong = "#374151"
        accent = "#3B82F6"
        accent_hover = "#2563EB"
        accent_soft = "rgba(59, 130, 246, 0.14)"
        accent_border = "rgba(59, 130, 246, 0.38)"
        accent_text = "#93C5FD"
        btn_pri_bg = "#2563EB"
        btn_pri_fg = "#FFFFFF"
        btn_pri_hover = "#1D4ED8"
        btn_sec_bg = "#131720"
        btn_sec_fg = "#F3F4F6"
        btn_sec_hover = "#1B202C"
        link_color = "#60A5FA"
        success_fg = "#34D399"
        success_bg = "rgba(16, 185, 129, 0.12)"
        success_bd = "rgba(16, 185, 129, 0.30)"
        warn_fg = "#FBBF24"
        warn_bg = "rgba(245, 158, 11, 0.12)"
        warn_bd = "rgba(245, 158, 11, 0.30)"
        err_fg = "#F87171"
        err_bg = "rgba(239, 68, 68, 0.12)"
        err_bd = "rgba(239, 68, 68, 0.30)"
        focus_ring = "rgba(59, 130, 246, 0.25)"
        card_shadow = "0 1px 2px rgba(0, 0, 0, 0.35)"
    else:
        c_scheme = "light"
        bg_page = "#F7F8FA"
        bg_surface = "#FFFFFF"
        bg_subtle = "#F1F3F6"
        bg_sidebar = "#F2F4F7"
        text_main = "#111827"
        text_sub = "#4B5563"
        text_muted = "#6B7280"
        border_light = "#E5E7EB"
        border_strong = "#D1D5DB"
        accent = "#1D4ED8"
        accent_hover = "#1E40AF"
        accent_soft = "#EFF6FF"
        accent_border = "#BFDBFE"
        accent_text = "#1E40AF"
        btn_pri_bg = "#1D4ED8"
        btn_pri_fg = "#FFFFFF"
        btn_pri_hover = "#1E40AF"
        btn_sec_bg = "#FFFFFF"
        btn_sec_fg = "#111827"
        btn_sec_hover = "#F1F3F6"
        link_color = "#1D4ED8"
        success_fg = "#047857"
        success_bg = "#ECFDF5"
        success_bd = "#A7F3D0"
        warn_fg = "#B45309"
        warn_bg = "#FFFBEB"
        warn_bd = "#FDE68A"
        err_fg = "#B91C1C"
        err_bg = "#FEF2F2"
        err_bd = "#FECACA"
        focus_ring = "rgba(29, 78, 216, 0.16)"
        card_shadow = "0 1px 2px rgba(17, 24, 39, 0.04)"

    render_html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        {hide_admin_chrome}

        :root {{
            color-scheme: {c_scheme} !important;
            --bg-page: {bg_page};
            --bg-surface: {bg_surface};
            --bg-subtle: {bg_subtle};
            --bg-sidebar: {bg_sidebar};
            --text-main: {text_main};
            --text-sub: {text_sub};
            --text-muted: {text_muted};
            --border-light: {border_light};
            --border-strong: {border_strong};
            --accent: {accent};
            --accent-hover: {accent_hover};
            --accent-soft: {accent_soft};
            --accent-border: {accent_border};
            --accent-text: {accent_text};
        }}

        @keyframes amFadeSlide {{
            from {{ opacity: 0; transform: translateY(4px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @media (prefers-reduced-motion: reduce) {{
            *, *::before, *::after {{ animation: none !important; transition-duration: 0.01ms !important; }}
        }}

        html, body, .stApp, [data-testid="stAppViewContainer"] {{
            background-color: {bg_page} !important;
            color: {text_main} !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }}

        [data-testid="stHeader"] {{
            background-color: {bg_page} !important;
            border-bottom: none !important;
        }}

        /* Sửa nút mở/đóng Sidebar (>> và <<) luôn hiển thị sắc nét ở cả Light & Dark */
        [data-testid="stHeader"] button,
        [data-testid="collapsedControl"],
        [data-testid="collapsedControl"] button,
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapseButton"] button {{
            color: {text_main} !important;
            background-color: transparent !important;
            border-radius: 8px !important;
        }}
        [data-testid="stHeader"] button:hover,
        [data-testid="collapsedControl"] button:hover,
        [data-testid="stExpandSidebarButton"]:hover,
        [data-testid="stSidebarCollapseButton"] button:hover {{
            background-color: {bg_subtle} !important;
        }}
        [data-testid="stHeader"] button svg,
        [data-testid="collapsedControl"] svg,
        [data-testid="stExpandSidebarButton"] svg,
        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="stHeader"] span[data-testid="stIconMaterial"],
        [data-testid="stExpandSidebarButton"] span[data-testid="stIconMaterial"],
        [data-testid="stSidebarCollapseButton"] span[data-testid="stIconMaterial"] {{
            color: {text_main} !important;
            fill: {text_main} !important;
        }}

        span:not([data-testid="stIconMaterial"]):not(.material-icons):not(.mono),
        p, div, label, li, td, th, h1, h2, h3, h4, h5, h6 {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }}
        code, pre, .mono {{
            font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace !important;
        }}
        span[data-testid="stIconMaterial"], .material-icons {{
            font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        }}

        .main .block-container {{
            max-width: 1080px !important;
            padding: 1.25rem 2rem 3rem 2rem !important;
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
        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stMarkdownContainer"] p,
        div[data-testid="stMarkdownContainer"] li {{
            color: {text_main};
        }}

        [data-testid="stMain"] code,
        section[data-testid="stSidebar"] code {{
            background-color: {bg_subtle} !important;
            color: {text_main} !important;
            border: 1px solid {border_light} !important;
            padding: 1px 6px !important;
            border-radius: 6px !important;
            font-size: 0.85em !important;
        }}

        /* Alerts theo đúng ngữ nghĩa màu sắc */
        div[data-testid="stAlert"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            padding: 0.65rem 0.9rem !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) {{
            background-color: {accent_soft} !important;
            border-color: {accent_border} !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {{
            background-color: {success_bg} !important;
            border-color: {success_bd} !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {{
            background-color: {warn_bg} !important;
            border-color: {warn_bd} !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {{
            background-color: {err_bg} !important;
            border-color: {err_bd} !important;
        }}
        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] strong {{
            color: {text_main} !important;
        }}

        div[data-testid="stToast"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            box-shadow: {card_shadow} !important;
            color: {text_main} !important;
        }}
        div[data-testid="stToast"] * {{ color: {text_main} !important; }}

        [data-testid="stMain"] a,
        section[data-testid="stSidebar"] a {{
            color: {link_color} !important;
            text-decoration: none !important;
            font-weight: 500;
        }}
        [data-testid="stMain"] a:hover,
        section[data-testid="stSidebar"] a:hover {{
            text-decoration: underline !important;
        }}

        div[data-testid="stCaptionContainer"] p {{
            color: {text_sub} !important;
            font-size: 0.84rem !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {border_light} !important;
        }}
        section[data-testid="stSidebar"] > div:first-child {{
            padding-top: 1rem !important;
        }}
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] span:not([data-testid="stIconMaterial"]),
        section[data-testid="stSidebar"] li {{
            color: {text_main} !important;
        }}
        section[data-testid="stSidebar"] hr {{
            margin: 0.85rem 0 !important;
            border-color: {border_light} !important;
        }}

        /* Inputs & Textareas */
        textarea, input[type="text"], input[type="password"] {{
            background-color: {bg_surface} !important;
            color: {text_main} !important;
            -webkit-text-fill-color: {text_main} !important;
            caret-color: {accent} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            font-size: 0.96rem !important;
            line-height: 1.6 !important;
            transition: border-color 150ms ease, box-shadow 150ms ease !important;
        }}
        textarea:focus, input[type="text"]:focus, input[type="password"]:focus {{
            border-color: {accent} !important;
            box-shadow: 0 0 0 3px {focus_ring} !important;
            outline: none !important;
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
        /* Nút con mắt password & clear input: xóa nền đen đặc */
        div[data-baseweb="input"] button,
        div[data-testid="stTextInput"] button {{
            background-color: transparent !important;
            color: {text_sub} !important;
            border: none !important;
        }}
        div[data-baseweb="input"] button:hover,
        div[data-testid="stTextInput"] button:hover {{
            background-color: {bg_subtle} !important;
            color: {text_main} !important;
        }}
        div[data-baseweb="input"] button svg,
        div[data-testid="stTextInput"] button svg {{
            fill: currentColor !important;
            color: {text_sub} !important;
        }}

        /* Selectbox: không còn khối đen bên phải */
        div[data-baseweb="select"] > div {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            color: {text_main} !important;
            min-height: 40px !important;
        }}
        div[data-baseweb="select"] > div:hover {{
            border-color: {accent} !important;
        }}
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] input {{
            color: {text_main} !important;
            background-color: transparent !important;
        }}
        div[data-baseweb="select"] svg {{
            color: {text_sub} !important;
            fill: {text_sub} !important;
            background-color: transparent !important;
        }}
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"],
        ul[data-testid="stSelectboxVirtualDropdown"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_strong} !important;
            border-radius: 10px !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
        }}
        div[data-baseweb="popover"] li,
        div[data-baseweb="menu"] li {{
            background-color: {bg_surface} !important;
            color: {text_main} !important;
        }}
        div[data-baseweb="popover"] li:hover,
        div[data-baseweb="menu"] li:hover,
        div[data-baseweb="popover"] li[aria-selected="true"] {{
            background-color: {bg_subtle} !important;
        }}

        /* Radio & Checkbox: sạch, không tô đen đặc ô chưa chọn */
        div[data-testid="stRadio"] div[role="radiogroup"] {{
            gap: 10px !important;
        }}
        div[data-testid="stRadio"] label,
        div[data-testid="stCheckbox"] label {{
            color: {text_main} !important;
            cursor: pointer;
        }}
        div[data-testid="stRadio"] label > div:first-child {{
            background-color: {bg_surface} !important;
            border: 1.75px solid {border_strong} !important;
        }}
        div[data-testid="stRadio"] label:has(input:checked) > div:first-child {{
            border-color: {accent} !important;
            background-color: {accent} !important;
        }}
        div[data-testid="stRadio"] label:has(input:checked) > div:first-child > div {{
            background-color: #FFFFFF !important;
        }}
        div[data-testid="stCheckbox"] label > span:first-of-type {{
            background-color: {bg_surface} !important;
            border: 1.75px solid {border_strong} !important;
            border-radius: 5px !important;
        }}
        div[data-testid="stCheckbox"] label:has(input:checked) > span:first-of-type {{
            background-color: {accent} !important;
            border-color: {accent} !important;
        }}
        div[data-testid="stCheckbox"] label:has(input:checked) > span:first-of-type svg {{
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
        }}

        /* Pills & Segmented Control */
        div[data-testid="stSegmentedControl"] > div {{
            background-color: {bg_subtle} !important;
            border: 1px solid {border_light} !important;
            border-radius: 10px !important;
            padding: 3px !important;
            gap: 4px !important;
        }}
        button[data-testid="stBaseButton-segmented_control"],
        button[data-testid="stBaseButton-pills"] {{
            background-color: {bg_surface} !important;
            color: {text_sub} !important;
            border: 1px solid {border_light} !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 150ms ease !important;
        }}
        button[data-testid="stBaseButton-segmented_control"] {{
            background-color: transparent !important;
            border-color: transparent !important;
        }}
        button[data-testid="stBaseButton-segmented_control"]:hover,
        button[data-testid="stBaseButton-pills"]:hover {{
            background-color: {bg_subtle} !important;
            color: {text_main} !important;
            border-color: {border_strong} !important;
        }}
        button[data-testid="stBaseButton-segmented_controlActive"],
        button[data-testid="stBaseButton-pillsActive"] {{
            background-color: {accent} !important;
            color: #FFFFFF !important;
            border: 1px solid {accent} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        button[data-testid="stBaseButton-segmented_controlActive"] *,
        button[data-testid="stBaseButton-pillsActive"] * {{
            color: #FFFFFF !important;
        }}
        button[data-testid="stBaseButton-segmented_control"] *,
        button[data-testid="stBaseButton-pills"] * {{
            color: inherit !important;
        }}

        /* Buttons */
        div.stButton > button,
        div.stDownloadButton > button,
        div.stFormSubmitButton > button {{
            min-height: 38px !important;
            border-radius: 9px !important;
            transition: background-color 150ms ease, border-color 150ms ease, transform 120ms ease !important;
        }}
        div.stButton > button:focus-visible,
        div.stDownloadButton > button:focus-visible,
        div.stFormSubmitButton > button:focus-visible {{
            outline: 2px solid {accent} !important;
            outline-offset: 2px !important;
        }}
        div.stButton > button[kind="primary"],
        div.stFormSubmitButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button,
        div.stDownloadButton > button[kind="primary"] {{
            background-color: {btn_pri_bg} !important;
            color: {btn_pri_fg} !important;
            border: 1px solid {btn_pri_bg} !important;
            padding: 0.48rem 1rem !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            box-shadow: none !important;
        }}
        div.stButton > button[kind="primary"] *,
        div.stFormSubmitButton > button[kind="primary"] *,
        div[data-testid="stFormSubmitButton"] button *,
        div.stDownloadButton > button[kind="primary"] * {{
            color: {btn_pri_fg} !important;
        }}
        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button:hover {{
            background-color: {btn_pri_hover} !important;
            border-color: {btn_pri_hover} !important;
        }}

        div.stButton > button[kind="secondary"],
        div.stDownloadButton > button[kind="secondary"],
        div.stFormSubmitButton > button[kind="secondary"] {{
            background-color: {btn_sec_bg} !important;
            color: {btn_sec_fg} !important;
            border: 1px solid {border_strong} !important;
            padding: 0.46rem 0.9rem !important;
            font-weight: 500 !important;
            font-size: 0.88rem !important;
            box-shadow: none !important;
        }}
        div.stButton > button[kind="secondary"] *,
        div.stDownloadButton > button[kind="secondary"] * {{
            color: {btn_sec_fg} !important;
        }}
        div.stButton > button[kind="secondary"]:hover,
        div.stDownloadButton > button[kind="secondary"]:hover {{
            background-color: {btn_sec_hover} !important;
            border-color: {text_sub} !important;
        }}

        /* Tabs: gọn 1 hàng, dùng soft Cobalt pill hiện đại */
        div[data-testid="stTabs"] div[role="tablist"] {{
            gap: 6px;
            border-bottom: 1px solid {border_light} !important;
            padding-bottom: 10px;
            margin-bottom: 6px;
            flex-wrap: nowrap;
            overflow-x: auto;
            scrollbar-width: none;
        }}
        div[data-testid="stTabs"] div[role="tablist"]::-webkit-scrollbar {{ display: none; }}
        div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {{ display: none !important; }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] {{
            background-color: transparent !important;
            border: 1px solid transparent !important;
            border-radius: 9px !important;
            padding: 7px 14px !important;
            white-space: nowrap !important;
            flex-shrink: 0 !important;
            box-shadow: none !important;
            transition: background-color 150ms ease, border-color 150ms ease !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"] p {{
            color: {text_sub} !important;
            font-weight: 500 !important;
            font-size: 0.91rem !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {{
            background-color: {bg_subtle} !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {{
            background-color: {accent_soft} !important;
            border-color: {accent_border} !important;
        }}
        div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p {{
            color: {accent_text} !important;
            font-weight: 600 !important;
        }}

        /* Expander & File Uploader */
        div[data-testid="stExpander"] {{
            background-color: {bg_surface} !important;
            border: 1px solid {border_light} !important;
            border-radius: 10px !important;
            overflow: hidden;
        }}
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] details[open] > summary {{
            background-color: {bg_surface} !important;
            color: {text_main} !important;
        }}
        div[data-testid="stExpander"] summary:hover {{
            background-color: {bg_subtle} !important;
        }}
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span,
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

        /* Custom Components */
        .ui-ico {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: {accent_text};
            flex-shrink: 0;
        }}

        .brand-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .brand-left {{
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }}
        .brand-mark {{
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: {accent};
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.98rem;
            letter-spacing: -0.02em;
            flex-shrink: 0;
        }}
        .minimal-title {{
            font-size: 1.42rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            color: {text_main};
            margin: 0;
            line-height: 1.2;
        }}
        .minimal-sub {{
            font-size: 0.85rem;
            color: {text_sub};
            margin-top: 2px;
        }}
        .header-divider {{
            height: 1px;
            width: 100%;
            background: {border_light};
            margin: 12px 0 14px 0;
        }}

        .author-chip {{
            display: inline-flex;
            align-items: center;
            gap: 9px;
            background: {bg_surface};
            border: 1px solid {border_light};
            border-radius: 999px;
            padding: 4px 12px 4px 5px;
        }}
        .author-chip-img {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid {border_strong};
            flex-shrink: 0;
        }}
        .author-chip-name {{ font-size: 0.82rem; font-weight: 600; color: {text_main}; line-height: 1.2; }}
        .author-chip-role {{ font-size: 0.72rem; color: {text_sub}; line-height: 1.2; }}

        .sidebar-brand-strip {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 10px;
            margin-bottom: 10px;
            background: {bg_surface};
            border: 1px solid {border_light};
            border-radius: 10px;
        }}
        .sidebar-brand-img {{
            width: 34px;
            height: 34px;
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid {border_strong};
            flex-shrink: 0;
        }}

        .clean-card {{
            background-color: {bg_surface};
            border: 1px solid {border_light};
            border-radius: 12px;
            padding: 16px 18px;
            margin-top: 12px;
            margin-bottom: 12px;
            box-shadow: {card_shadow};
            animation: amFadeSlide 180ms ease-out;
        }}
        .result-hero-card {{
            border-left: 3px solid {accent};
        }}
        .clean-label {{
            font-size: 0.81rem;
            font-weight: 600;
            color: {text_sub};
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .label-title {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: {text_sub};
        }}
        .label-badge {{
            display: inline-flex;
            align-items: center;
            font-size: 0.75rem;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 6px;
            background: {bg_subtle};
            border: 1px solid {border_light};
            color: {text_sub};
            font-family: 'JetBrains Mono', monospace !important;
        }}
        .clean-result-text {{
            font-size: 1.14rem;
            line-height: 1.7;
            color: {text_main};
            font-weight: 500;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .pron-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            padding: 5px 10px;
            background: {bg_subtle};
            border: 1px solid {border_light};
            border-radius: 8px;
            font-size: 0.86rem;
            color: {text_sub};
        }}

        .meta-pill {{
            display: inline-flex;
            align-items: center;
            justify-content: flex-end;
            gap: 6px;
            min-height: 38px;
            width: 100%;
            font-size: 0.82rem;
            color: {text_sub};
        }}
        .meta-pill-tag {{
            background: {bg_subtle};
            border: 1px solid {border_light};
            border-radius: 8px;
            padding: 5px 10px;
            color: {text_sub};
            font-weight: 500;
            white-space: nowrap;
        }}

        .inline-banner {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            margin-bottom: 10px;
            background: {accent_soft};
            border: 1px solid {accent_border};
            border-radius: 9px;
            font-size: 0.84rem;
            color: {text_main};
        }}

        .empty-state-box {{
            background: {bg_surface};
            border: 1px dashed {border_strong};
            border-radius: 12px;
            padding: 18px 20px;
            margin-top: 12px;
        }}
        .empty-state-title {{
            font-size: 0.92rem;
            font-weight: 600;
            color: {text_main};
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 7px;
        }}
        .empty-state-sub {{
            font-size: 0.84rem;
            color: {text_sub};
            margin-bottom: 10px;
        }}

        .example-row {{ padding: 10px 0; border-bottom: 1px solid {border_light}; }}
        .example-row:last-child {{ border-bottom: none; padding-bottom: 2px; }}
        .example-ru {{ font-size: 0.99rem; font-weight: 600; color: {text_main}; line-height: 1.5; }}
        .example-vi {{ font-size: 0.89rem; color: {text_sub}; margin-top: 3px; line-height: 1.5; }}
        .example-tag {{
            display: inline-block; font-size: 0.73rem; font-weight: 500; color: {accent_text};
            background: {accent_soft}; border: 1px solid {accent_border};
            padding: 1px 8px; border-radius: 6px; margin-bottom: 4px;
        }}

        .syn-ant-item {{
            padding: 7px 0; border-bottom: 1px solid {border_light};
            font-size: 0.91rem; color: {text_main}; line-height: 1.45;
        }}
        .syn-ant-item:last-child {{ border-bottom: none; }}

        .table-wrap {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        .clean-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.89rem;
            margin-top: 4px;
        }}
        .clean-table th {{
            text-align: left;
            padding: 8px 11px;
            border-bottom: 1px solid {border_strong};
            color: {text_sub};
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            font-weight: 600;
            background-color: {bg_subtle};
        }}
        .clean-table td {{
            padding: 8px 11px;
            border-bottom: 1px solid {border_light};
            color: {text_main};
            vertical-align: top;
            line-height: 1.52;
        }}
        .clean-table tbody tr:hover td {{
            background-color: {bg_subtle};
        }}
        .clean-table tr.table-group-row td {{
            background-color: {accent_soft} !important;
            color: {accent_text} !important;
            font-weight: 600;
            font-size: 0.82rem;
            padding: 7px 11px;
            border-top: 1px solid {border_light};
            border-bottom: 1px solid {accent_border};
        }}

        .note-callout {{
            background-color: {bg_subtle};
            border-left: 3px solid {accent};
            border-radius: 0 8px 8px 0;
            padding: 11px 14px;
            margin-top: 12px;
            font-size: 0.89rem;
            color: {text_main};
            line-height: 1.62;
        }}

        /* Flashcard */
        .flashcard-minimal {{
            background-color: {bg_surface};
            border: 1px solid {border_strong};
            border-radius: 14px;
            padding: 24px 24px 28px 24px;
            text-align: center;
            margin: 10px 0 12px 0;
            box-shadow: {card_shadow};
            animation: amFadeSlide 180ms ease-out;
        }}
        .flashcard-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            font-size: 0.78rem;
            color: {text_sub};
        }}
        .flashcard-word {{
            font-size: 1.82rem;
            font-weight: 700;
            color: {text_main};
            letter-spacing: -0.02em;
            line-height: 1.3;
        }}
        .flashcard-hint {{
            margin-top: 10px;
            font-size: 0.84rem;
            color: {text_muted};
        }}
        .flashcard-back {{
            margin-top: 18px;
            padding-top: 16px;
            border-top: 1px solid {border_light};
            font-size: 1.15rem;
            font-weight: 600;
            color: {accent_text};
        }}
        .flashcard-pron {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.88rem;
            color: {text_sub};
            font-weight: 400;
            margin-top: 6px;
        }}
        .flashcard-en {{
            font-size: 0.85rem;
            color: {text_muted};
            font-weight: 400;
            margin-top: 3px;
        }}
        .flashcard-ex {{
            font-size: 0.89rem;
            color: {text_main};
            font-weight: 400;
            margin: 12px auto 0 auto;
            max-width: 560px;
            padding: 8px 12px;
            background: {bg_subtle};
            border-radius: 8px;
        }}

        /* Stat strip gọn */
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 4px 0 12px 0;
        }}
        .stat-box {{
            background: {bg_surface};
            border: 1px solid {border_light};
            border-radius: 10px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }}
        .stat-num {{ font-size: 1.2rem; font-weight: 700; color: {text_main}; line-height: 1.2; }}
        .stat-lbl {{ font-size: 0.77rem; color: {text_sub}; margin-top: 2px; }}

        .deck-bar-label {{
            display: flex;
            align-items: center;
            min-height: 38px;
            font-size: 0.86rem;
            color: {text_sub};
        }}

        @media (max-width: 768px) {{
            .main .block-container {{
                padding: 0.75rem 0.85rem 2.2rem 0.85rem !important;
            }}
            .minimal-title {{ font-size: 1.22rem; }}
            .minimal-sub {{ font-size: 0.78rem; }}
            .brand-mark {{ width: 32px; height: 32px; font-size: 0.86rem; }}
            .author-chip {{ display: none; }}
            .header-divider {{ margin: 8px 0 10px 0; }}
            .clean-card {{ padding: 13px 14px; }}
            .stat-grid {{ grid-template-columns: 1fr; gap: 6px; }}
            .stat-box {{ padding: 8px 12px; }}
            .flashcard-minimal {{ padding: 18px 14px 20px 14px; }}
            .flashcard-word {{ font-size: 1.48rem; }}
            .meta-pill {{ justify-content: flex-start; min-height: auto; }}
        }}
        </style>
        """
    )


def render_russian_knowledge_hub() -> None:
    if "kh_active_topic" not in st.session_state or st.session_state["kh_active_topic"] not in KNOWLEDGE_HUB_TOPICS:
        st.session_state["kh_active_topic"] = KNOWLEDGE_HUB_TOPICS[0]
    if st.session_state.get("kh_topic_pills") is None:
        st.session_state["kh_topic_pills"] = st.session_state["kh_active_topic"]

    picked_topic = st.pills(
        "Chọn chuyên đề",
        options=KNOWLEDGE_HUB_TOPICS,
        selection_mode="single",
        label_visibility="collapsed",
        key="kh_topic_pills",
    )
    if picked_topic:
        st.session_state["kh_active_topic"] = picked_topic
    topic = st.session_state["kh_active_topic"]

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
    total_library_words = sum(len(v) for v in ALL_VOCAB_DECKS.values()) + len(RUSSIAN_SLANG_DICT)

    if not st.session_state.get("auth_username"):
        render_html(
            f"""
            <div class="inline-banner">
                {svg_icon("info")}
                <span>Đăng nhập hoặc tạo tài khoản ở thanh bên trái để lưu vĩnh viễn và đồng bộ Sổ từ vựng + Lịch sử trên mọi thiết bị.</span>
            </div>
            """
        )

    render_html(
        f"""
        <div class="stat-grid">
            <div class="stat-box">
                <div><div class="stat-num">{len(saved_list)}</div><div class="stat-lbl">Từ trong sổ cá nhân</div></div>
                {svg_icon("book")}
            </div>
            <div class="stat-box">
                <div><div class="stat-num">{mastered_cnt} <span style="font-size:0.85rem;font-weight:500;opacity:0.75;">({pct}%)</span></div><div class="stat-lbl">Đã thuộc kỹ</div></div>
                {svg_icon("check_circle")}
            </div>
            <div class="stat-box">
                <div><div class="stat-num">{due_today_cnt}</div><div class="stat-lbl">Cần ôn hôm nay · Kho {total_library_words} từ</div></div>
                {svg_icon("clock")}
            </div>
        </div>
        """
    )

    mode_options = ["Thẻ ghi nhớ (Flashcards)", "Trắc nghiệm (Quiz)", "Quản lý sổ & Kho từ СПбГМТУ"]
    if st.session_state.get("vocab_practice_mode") not in mode_options:
        st.session_state["vocab_practice_mode"] = mode_options[0]
    if st.session_state.get("vocab_mode_seg") is None:
        st.session_state["vocab_mode_seg"] = st.session_state["vocab_practice_mode"]

    mode_pick = st.segmented_control(
        "Chế độ học từ vựng",
        options=mode_options,
        selection_mode="single",
        label_visibility="collapsed",
        key="vocab_mode_seg",
    )
    if mode_pick:
        st.session_state["vocab_practice_mode"] = mode_pick
    mode = st.session_state["vocab_practice_mode"]

    slang_deck = [
        {
            "ru_accent": f"{x['accent']} ({x['full']})",
            "pronunciation": "",
            "vi": x["vi"],
            "en": x["en"],
            "example": x.get("example", ""),
            "mastered": False,
        }
        for x in RUSSIAN_SLANG_DICT
    ]
    all_deck_names = list(ALL_VOCAB_DECKS.keys())
    is_slow_tts = bool(st.session_state.get("tts_slow_mode", False))

    if mode == "Thẻ ghi nhớ (Flashcards)":
        cat_options = ["Sổ cá nhân", "Nhập môn A0–A1", "Toán · Lý · Hóa", "Chuyên ngành СПбГМТУ", "30 từ lóng SV"]
        default_cat = "Sổ cá nhân" if due_today_cnt > 0 else "Chuyên ngành СПбГМТУ"
        if st.session_state.get("fc_category") not in cat_options:
            st.session_state["fc_category"] = default_cat
        if st.session_state.get("fc_cat_pills") is None:
            st.session_state["fc_cat_pills"] = st.session_state["fc_category"]

        selected_cat_pick = st.pills(
            "Nhóm chủ đề",
            options=cat_options,
            selection_mode="single",
            label_visibility="collapsed",
            key="fc_cat_pills",
        )
        if selected_cat_pick and selected_cat_pick != st.session_state["fc_category"]:
            st.session_state["fc_category"] = selected_cat_pick
            st.session_state["flashcard_index"] = 0
            st.session_state["flashcard_show_back"] = False
            st.session_state.pop("fc_subdeck_pills", None)
        selected_cat = st.session_state["fc_category"]

        if selected_cat == "Sổ cá nhân":
            sub_decks = ["Cần ôn hôm nay (Sổ cá nhân)", "Tất cả từ trong sổ"]
        elif selected_cat == "30 từ lóng SV":
            sub_decks = ["30 từ lóng sinh viên Nga"]
        else:
            sub_decks = VOCAB_DECK_CATEGORIES[selected_cat]

        if st.session_state.get("selected_fc_deck") not in sub_decks:
            st.session_state["selected_fc_deck"] = sub_decks[0]

        if len(sub_decks) > 1:
            if st.session_state.get("fc_subdeck_pills") not in sub_decks:
                st.session_state["fc_subdeck_pills"] = st.session_state["selected_fc_deck"]

            def _fmt_deck(d_name: str) -> str:
                short_lbl = d_name.split(". ", 1)[-1]
                count_d = (
                    due_today_cnt if d_name.startswith("Cần ôn")
                    else len(saved_list) if d_name.startswith("Tất cả")
                    else len(ALL_VOCAB_DECKS[d_name])
                )
                return f"{short_lbl} ({count_d})"

            sub_pick = st.pills(
                "Chọn bộ thẻ",
                options=sub_decks,
                selection_mode="single",
                format_func=_fmt_deck,
                label_visibility="collapsed",
                key="fc_subdeck_pills",
            )
            if sub_pick and sub_pick != st.session_state["selected_fc_deck"]:
                st.session_state["selected_fc_deck"] = sub_pick
                st.session_state["flashcard_index"] = 0
                st.session_state["flashcard_show_back"] = False

        deck_choice = st.session_state["selected_fc_deck"]
        fc1, fc2 = st.columns([3.0, 1.0])
        with fc1:
            render_html(f'<div class="deck-bar-label">Đang học bộ:&nbsp;<b>{esc(deck_choice)}</b></div>')
        with fc2:
            if st.button("Xáo trộn thẻ", use_container_width=True):
                if deck_choice in ("Cần ôn hôm nay (Sổ cá nhân)", "Tất cả từ trong sổ") and saved_list:
                    random.shuffle(saved_list)
                elif deck_choice in ALL_VOCAB_DECKS:
                    random.shuffle(ALL_VOCAB_DECKS[deck_choice])
                st.session_state["flashcard_index"] = 0
                st.session_state["flashcard_show_back"] = False
                st.rerun()

        is_personal_deck = deck_choice in ("Cần ôn hôm nay (Sổ cá nhân)", "Tất cả từ trong sổ")
        is_library_deck = deck_choice in ALL_VOCAB_DECKS

        if deck_choice == "Cần ôn hôm nay (Sổ cá nhân)":
            active_deck = [v for v in saved_list if is_vocab_due_today(v)]
        elif deck_choice == "Tất cả từ trong sổ":
            active_deck = saved_list
        elif is_library_deck:
            active_deck = ALL_VOCAB_DECKS[deck_choice]
        else:
            active_deck = slang_deck

        if not active_deck:
            if deck_choice == "Cần ôn hôm nay (Sổ cá nhân)" and saved_list:
                st.success("Bạn đã ôn hết toàn bộ từ đến hạn hôm nay! Hãy chuyển sang nhóm «Toán · Lý · Hóa» hoặc «Chuyên ngành СПбГМТУ» để học thêm.")
            else:
                render_html(
                    f"""
                    <div class="empty-state-box">
                        <div class="empty-state-title">{svg_icon("layers")}<span>Sổ cá nhân chưa có thẻ cần ôn</span></div>
                        <div class="empty-state-sub" style="margin-bottom:0;">Hãy chọn các nhóm <b>Nhập môn A0–A1</b>, <b>Toán · Lý · Hóa</b> hoặc <b>Chuyên ngành СПбГМТУ</b> ở trên để học và lưu từ vào sổ ngay.</div>
                    </div>
                    """
                )
            return

        idx = st.session_state["flashcard_index"] % len(active_deck)
        card = active_deck[idx]
        lvl = int(card.get("level", 2 if card.get("mastered") else 0))
        lvl_label = {0: "Chưa nhớ", 1: "Nhớ mang máng", 2: "Thuộc kỹ"}.get(lvl, "")
        status_pill = f'<span class="label-badge">{esc(lvl_label)}</span>' if is_personal_deck and lvl_label else ""

        pron_txt = str(card.get("pronunciation") or card.get("pronunciation_hint") or "").strip()
        pron_html = f'<div class="flashcard-pron">/{esc(pron_txt)}/</div>' if pron_txt else ""
        en_html = f'<div class="flashcard-en">{esc(card.get("en", ""))}</div>' if card.get("en") else ""
        ex_html = (
            f'<div class="flashcard-ex"><b>Ví dụ:</b> <i>{esc(card.get("example", ""))}</i></div>'
            if card.get("example")
            else ""
        )

        back_html = (
            f'<div class="flashcard-back">{esc(card["vi"])}{pron_html}{en_html}{ex_html}</div>'
            if st.session_state["flashcard_show_back"]
            else '<div class="flashcard-hint">Bấm «Lật thẻ» để xem nghĩa tiếng Việt, phiên âm &amp; ví dụ</div>'
        )
        render_html(
            f"""
            <div class="flashcard-minimal">
                <div class="flashcard-top">
                    <span class="label-badge">Thẻ {idx + 1} / {len(active_deck)}</span>
                    {status_pill}
                </div>
                <div class="flashcard-word">{esc(card["ru_accent"])}</div>
                {back_html}
            </div>
            """
        )

        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("← Trước", use_container_width=True):
                st.session_state["flashcard_index"] = (idx - 1) % len(active_deck)
                st.session_state["flashcard_show_back"] = False
                st.rerun()
        with b2:
            flip_txt = "Ẩn mặt sau" if st.session_state["flashcard_show_back"] else "Lật thẻ"
            if st.button(flip_txt, type="primary", use_container_width=True):
                st.session_state["flashcard_show_back"] = not st.session_state["flashcard_show_back"]
                st.rerun()
        with b3:
            if st.button("Phát âm", use_container_width=True):
                ru_clean = card["ru_accent"].split("(")[0].replace("\u0301", "").strip()
                ab = generate_tts_audio(ru_clean, "ru", slow=is_slow_tts)
                if ab:
                    st.audio(ab, format="audio/mp3")
        with b4:
            if st.button("Tiếp →", use_container_width=True):
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
                if st.button("+ Lưu thẻ này vào sổ", key="btn_save_one_starter", use_container_width=True):
                    cnt = add_vocab_items_to_notebook([card])
                    st.toast("Đã lưu thẻ vào sổ cá nhân." if cnt else "Từ này đã có trong sổ.")
            with sc2:
                if is_library_deck and st.button(f"Lưu cả bộ ({len(active_deck)} từ) vào sổ", key="btn_save_all_starter", use_container_width=True):
                    cnt = add_vocab_items_to_notebook(active_deck)
                    st.toast(f"Đã lưu thêm {cnt} từ mới vào sổ cá nhân." if cnt else "Toàn bộ thẻ trong bộ này đã có trong sổ.")

        with st.expander(f"Xem bảng danh sách đầy đủ bộ này ({len(active_deck)} từ)"):
            rows_preview = "".join(
                f"<tr><td><b>{esc(it.get('ru_accent',''))}</b>"
                + (f"<br/><span style='font-size:0.78rem;opacity:0.78;'>{esc(it.get('pronunciation') or it.get('pronunciation_hint') or '')}</span>" if (it.get("pronunciation") or it.get("pronunciation_hint")) else "")
                + f"</td><td>{esc(it.get('vi',''))}</td><td><i>{esc(it.get('example',''))}</i></td></tr>"
                for it in active_deck
            )
            render_html(
                f"""
                <div class="clean-card" style="padding:0;max-height:360px;overflow-y:auto;margin:4px 0;">
                    <div class="table-wrap">
                        <table class="clean-table" style="margin-top:0;">
                            <thead><tr><th>Tiếng Nga &amp; Phiên âm</th><th>Nghĩa tiếng Việt</th><th>Ví dụ áp dụng</th></tr></thead>
                            <tbody>{rows_preview}</tbody>
                        </table>
                    </div>
                </div>
                """
            )
            st.download_button(
                f"Tải bộ này ra CSV ({len(active_deck)} từ)",
                data=export_vocab_to_anki_csv(active_deck),
                file_name="bo_tu_vung_spbgmtu.csv",
                mime="text/csv",
                use_container_width=True,
            )

    elif mode == "Trắc nghiệm (Quiz)":
        quiz_sources = ["Sổ cá nhân"] + all_deck_names + ["30 từ lóng sinh viên Nga"]
        default_quiz_src = "Sổ cá nhân" if len(saved_list) >= 4 else "9. Kết cấu & Lý thuyết tàu (Кораблестроение)"
        if st.session_state.get("selected_quiz_src") not in quiz_sources:
            st.session_state["selected_quiz_src"] = default_quiz_src

        qs1, qs2, qs3 = st.columns([2.4, 1.0, 0.85])
        with qs1:
            quiz_src = st.selectbox(
                "Nguồn câu hỏi",
                options=quiz_sources,
                index=quiz_sources.index(st.session_state["selected_quiz_src"]),
                label_visibility="collapsed",
            )
            st.session_state["selected_quiz_src"] = quiz_src
        with qs2:
            q_tot = st.session_state["quiz_total"]
            q_sc = st.session_state["quiz_score"]
            acc = int(round((q_sc / q_tot) * 100)) if q_tot else 0
            render_html(f'<div class="meta-pill"><span class="meta-pill-tag">Điểm: <b>{q_sc}/{q_tot}</b> ({acc}%)</span></div>')
        with qs3:
            if st.button("Đặt lại", key="btn_reset_quiz", use_container_width=True):
                st.session_state["quiz_score"] = 0
                st.session_state["quiz_total"] = 0
                st.session_state["current_quiz"] = None
                st.rerun()

        quiz_dir_opts = ["Nga → Việt", "Việt → Nga", "Nghe âm thanh → Chọn nghĩa"]
        if st.session_state.get("quiz_dir_pills") is None:
            st.session_state["quiz_dir_pills"] = quiz_dir_opts[0]
        quiz_dir_label = st.pills(
            "Chiều kiểm tra",
            options=quiz_dir_opts,
            selection_mode="single",
            label_visibility="collapsed",
            key="quiz_dir_pills",
        ) or quiz_dir_opts[0]

        if quiz_dir_label == "Việt → Nga":
            q_dir = "vi_to_ru"
        elif quiz_dir_label == "Nghe âm thanh → Chọn nghĩa":
            q_dir = "audio_to_vi"
        else:
            q_dir = "ru_to_vi"

        if quiz_src == "Sổ cá nhân":
            due_pool = [v for v in saved_list if is_vocab_due_today(v)]
            pool = due_pool if len(due_pool) >= 4 else saved_list
        elif quiz_src in ALL_VOCAB_DECKS:
            pool = ALL_VOCAB_DECKS[quiz_src]
        else:
            pool = slang_deck

        if len(pool) < 4:
            st.info(f"Nguồn «{quiz_src}» hiện có {len(pool)} từ (cần ít nhất 4 từ để tạo trắc nghiệm). Hãy chọn một bộ trong 11 chủ đề Toán · Lý · Hóa · СПбГМТУ ở trên.")
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
                        <div style="font-size:0.84rem;color:var(--text-sub);margin-bottom:6px;">{esc(q['sub_hint'])}</div>
                        <div style="font-size:1.05rem;font-weight:600;">Bấm nút bên dưới để nghe và chọn nghĩa đúng</div>
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
                        <div style="font-size:0.82rem;color:var(--text-sub);margin-bottom:6px;">{esc(q['sub_hint'])}</div>
                        <div style="font-size:1.6rem;font-weight:700;letter-spacing:-0.01em;">{esc(q['prompt'])}</div>
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
                if st.button("Câu tiếp theo →", type="primary"):
                    st.session_state["current_quiz"] = _generate_quiz_question(pool, q_dir)
                    st.rerun()

    else:
        col_left, col_right = st.columns([1.05, 1.15])
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
                f_c1, f_c2 = st.columns([1.6, 1.1])
                with f_c1:
                    q_my = st.text_input("Tìm trong sổ của bạn", placeholder="Gõ tiếng Nga hoặc tiếng Việt...", label_visibility="collapsed")
                with f_c2:
                    my_filter = st.selectbox("Lọc", ["Tất cả", "Cần ôn hôm nay", "Đã thuộc"], label_visibility="collapsed")

                filtered_my = []
                for i, v in enumerate(saved_list):
                    if my_filter == "Cần ôn hôm nay" and not is_vocab_due_today(v):
                        continue
                    if my_filter == "Đã thuộc" and not v.get("mastered"):
                        continue
                    if q_my.strip() and q_my.lower() not in v["ru_accent"].lower() and q_my.lower() not in v["vi"].lower():
                        continue
                    filtered_my.append((i, v))

                st.download_button(
                    f"Xuất {len(saved_list)} từ ra CSV (Anki / Excel)",
                    data=export_vocab_to_anki_csv(saved_list),
                    file_name="tu_vung_anki.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

                if not filtered_my:
                    st.caption("Không có từ nào khớp bộ lọc hiện tại.")
                else:
                    per_page = 20
                    total_filtered = len(filtered_my)
                    total_pages = max(1, (total_filtered + per_page - 1) // per_page)
                    cur_page = max(1, min(int(st.session_state.get("vocab_page", 1)), total_pages))
                    st.session_state["vocab_page"] = cur_page
                    start_i = (cur_page - 1) * per_page
                    page_items = filtered_my[start_i : start_i + per_page]

                    for orig_i, v in page_items:
                        rc1, rc2, rc3 = st.columns([3.5, 1.25, 0.65])
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
                render_html(
                    f"""
                    <div class="empty-state-box">
                        <div class="empty-state-title">{svg_icon("book")}<span>Sổ từ vựng cá nhân đang trống</span></div>
                        <div class="empty-state-sub" style="margin-bottom:0;">Lưu từ sau khi tra ở tab <b>Dịch &amp; Ngữ pháp</b>, lưu từ bộ <b>Flashcards</b>, hoặc bấm thêm từ thủ công ở trên.</div>
                    </div>
                    """
                )

        with col_right:
            st.markdown(f"#### Tra nhanh kho từ vựng ({total_library_words} từ)")
            lib_filter_opts = ["Tất cả 11 bộ + Tiếng lóng"] + all_deck_names + ["30 từ lóng sinh viên Nga"]
            lib_src = st.selectbox("Chọn chủ đề tra nhanh", options=lib_filter_opts, label_visibility="collapsed", key="lib_browse_src")
            q_lib = st.text_input("Tìm thuật ngữ Nga / Việt / Anh", placeholder="VD: остойчивость, tích phân, thân tàu, препод...", label_visibility="collapsed", key="lib_search_q")

            if lib_src == "Tất cả 11 bộ + Tiếng lóng":
                browse_items = [it for d in ALL_VOCAB_DECKS.values() for it in d] + slang_deck
            elif lib_src in ALL_VOCAB_DECKS:
                browse_items = ALL_VOCAB_DECKS[lib_src]
            else:
                browse_items = slang_deck

            ql = q_lib.strip().lower()
            matched_lib = [
                x for x in browse_items
                if not ql
                or ql in str(x.get("ru_accent", "")).lower()
                or ql in str(x.get("vi", "")).lower()
                or ql in str(x.get("en", "")).lower()
                or ql in str(x.get("pronunciation", "")).lower()
            ]
            st.caption(f"Hiển thị {min(len(matched_lib), 60)} / {len(matched_lib)} thuật ngữ khớp")
            if not matched_lib:
                render_html(
                    f"""
                    <div class="empty-state-box">
                        <div class="empty-state-title">{svg_icon("search")}<span>Không tìm thấy thuật ngữ phù hợp</span></div>
                        <div class="empty-state-sub" style="margin-bottom:0;">Thử tìm với từ khóa ngắn hơn hoặc chuyển sang mục «Tất cả 11 bộ + Tiếng lóng».</div>
                    </div>
                    """
                )
            else:
                rows = "".join(
                    f"<tr><td><b>{esc(x.get('ru_accent',''))}</b>"
                    + (f"<br/><span class='mono' style='font-size:0.76rem;opacity:0.78;'>{esc(x.get('pronunciation',''))}</span>" if x.get("pronunciation") else "")
                    + f"</td><td>{esc(x.get('vi',''))}</td></tr>"
                    for x in matched_lib[:60]
                )
                render_html(
                    f"""
                    <div class="clean-card" style="padding:0;max-height:440px;overflow-y:auto;">
                        <div class="table-wrap">
                            <table class="clean-table" style="margin-top:0;">
                                <thead><tr><th>Tiếng Nga &amp; Phiên âm</th><th>Nghĩa tiếng Việt</th></tr></thead>
                                <tbody>{rows}</tbody>
                            </table>
                        </div>
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
        f'<div class="pron-pill">{svg_icon("volume")}<span><b>Cách đọc gần đúng:</b> {esc(pron_hint)}</span></div>'
        if pron_hint
        else ""
    )

    render_html(
        f"""
        <div class="clean-card result-hero-card">
            <div class="clean-label">
                <span class="label-title">{svg_icon("languages")}<span>{esc(header_left)}</span></span>
                <span class="label-badge">{esc(meta_badge)}</span>
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
        c_act1, c_act2, c_act3, _ = st.columns([1.25, 1.45, 1.45, 2.85])
    else:
        c_act1, c_act2, _ = st.columns([1.25, 1.45, 4.30])
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
                        <span class="label-title">{svg_icon("layers")}<span>Chia động từ theo các ngôi</span></span>
                        <span class="label-badge">{esc(meta_line)}</span>
                    </div>
                    <div class="table-wrap">
                        <table class="clean-table">
                            <thead><tr><th>Ngôi / Thì</th><th>Dạng chia</th></tr></thead>
                            <tbody>{v_rows}</tbody>
                        </table>
                    </div>
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
                        <span class="label-title">{svg_icon("layers")}<span>Biến cách theo 6 cách tiếng Nga</span></span>
                        <span class="label-badge">{esc(meta_line)}</span>
                    </div>
                    <div class="table-wrap">
                        <table class="clean-table">
                            <thead><tr><th>6 Cách (Падежи)</th><th>Số ít (Ед. ч.)</th><th>Số nhiều (Мн. ч.)</th></tr></thead>
                            <tbody>{c_rows}</tbody>
                        </table>
                    </div>
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
                render_html(f'<div class="clean-card" style="margin-top:8px;"><div class="clean-label"><span class="label-title">{svg_icon("sparkles")}<span>Từ đồng nghĩa (Синонимы)</span></span></div>{s_items}</div>')
        with sa_c2:
            if antonyms:
                a_items = "".join(f"<div class='syn-ant-item'><b>{esc(a['ru'])}</b> — {esc(a['vi'])}</div>" for a in antonyms)
                render_html(f'<div class="clean-card" style="margin-top:8px;"><div class="clean-label"><span class="label-title">{svg_icon("layers")}<span>Từ trái nghĩa (Антонимы)</span></span></div>{a_items}</div>')

    sent_grammar = res.get("sentence_grammar") or []
    if sent_grammar:
        g_rows = "".join(
            f"<tr><td><b>{esc(g.get('segment',''))}</b></td><td>{esc(g.get('grammar_tag',''))}</td><td>{esc(g.get('explanation',''))}</td></tr>"
            for g in sent_grammar
        )
        render_html(
            f"""
            <div class="clean-card">
                <div class="clean-label"><span class="label-title">{svg_icon("book")}<span>Giải thích ngữ pháp</span></span></div>
                <div class="table-wrap">
                    <table class="clean-table">
                        <thead><tr><th>Cụm từ / Từ</th><th>Ngữ pháp (Cách / Thể)</th><th>Giải thích</th></tr></thead>
                        <tbody>{g_rows}</tbody>
                    </table>
                </div>
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
        render_html(f'<div class="clean-card"><div class="clean-label"><span class="label-title">{svg_icon("sparkles")}<span>Ví dụ áp dụng theo ngữ cảnh</span></span></div>{ex_html}</div>')
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
                <div class="clean-label"><span class="label-title">{svg_icon("info")}<span>Tiếng lóng &amp; viết tắt</span></span></div>
                <div class="table-wrap">
                    <table class="clean-table">
                        <thead><tr><th>Từ lóng</th><th>Dạng đầy đủ</th><th>Giải nghĩa</th></tr></thead>
                        <tbody>{slang_rows}</tbody>
                    </table>
                </div>
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
                <div class="clean-label"><span class="label-title">{svg_icon("book")}<span>Từ vựng đáng chú ý (có dấu trọng âm)</span></span></div>
                <div class="table-wrap">
                    <table class="clean-table">
                        <thead><tr><th>Tiếng Nga</th><th>Tiếng Việt</th><th>Tiếng Anh</th></tr></thead>
                        <tbody>{v_rows}</tbody>
                    </table>
                </div>
            </div>
            """
        )
        if st.button("+ Lưu từ vựng vào sổ ôn tập", key="btn_save_vocab"):
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