"""
Anh Minh Translate — Dịch thuật siêu tốc, ngữ pháp 6 cách & ôn tập tiếng Nga đồng bộ đa thiết bị
Tác giả: Mai Văn Minh — Sinh viên năm 4, Chuyên ngành Đóng tàu, СПбГМТУ (Xanh-Petecbua)
"""

from datetime import datetime
import re
import time
from typing import Any, Dict, Optional

import streamlit as st

st.set_page_config(
    page_title="Anh Minh Translate · Mai Văn Minh (СПбГМТУ)",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from data import (
    DIRECTION_OPTIONS,
    GEMINI_API_KEY_URL,
    MAX_HISTORY_ITEMS,
    PREFERRED_GEMINI_MODELS_FAST,
    PREFERRED_GEMINI_MODELS_QUALITY,
    STUDENT_YEAR_OPTIONS,
)
from services import (
    DAILY_DEMO_LIMIT,
    DEFAULT_AUTHOR_PASSWORD,
    SHARED_DEMO_GEMINI_KEY,
    _get_browser_cookie,
    _hash_password,
    _is_cloud_sync_enabled,
    _normalize_username,
    _verify_password,
    apply_user_payload_to_session,
    call_gemini_smart_translate,
    classify_input_type,
    clean_api_key,
    create_admin_token,
    create_session_token,
    db_get_user,
    db_list_all_users,
    db_save_user,
    discover_working_gemini_models,
    export_users_to_csv,
    consume_demo_quota,
    fallback_fast_translate,
    generate_tts_audio,
    get_remaining_demo_quota,
    resolve_effective_direction,
    send_user_notification_email,
    sync_current_account_to_db,
    verify_admin_token,
    verify_author_password,
    verify_session_token,
)
from ui_components import (
    bootstrap_remembered_tokens_js,
    clear_remembered_admin,
    clear_remembered_login,
    get_author_avatar_data_uri,
    get_cookie_manager,
    inject_theme_css,
    render_html,
    render_russian_knowledge_hub,
    render_translation_result,
    render_vocab_and_practice_tab,
    save_remembered_admin,
    save_remembered_login,
)


def init_session_state(cookie_manager: Any = None) -> None:
    defaults: Dict[str, Any] = {
        "auth_username": "",
        "auth_password_hash": "",
        "auth_created_at": "",
        "auth_last_login_at": "",
        "auth_login_count": 1,
        "auth_token_version": 1,
        "last_supabase_error": "",
        "input_text_area": "",
        "selected_direction": DIRECTION_OPTIONS[0],
        "is_author_admin": False,
        "saved_gemini_api_key": "",
        "theme_mode": "light",
        "ai_speed_mode": "fast",
        "tts_slow_mode": False,
        "learner_level": "beginner",
        "demo_usage": {"date": datetime.now().strftime("%Y-%m-%d"), "count": 0},
        "translation_history": [],
        "saved_vocab_notebook": [],
        "flashcard_index": 0,
        "vocab_page": 1,
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

    if "ask_remember_login" not in st.session_state:
        st.session_state["ask_remember_login"] = False
    if "is_login_remembered" not in st.session_state:
        st.session_state["is_login_remembered"] = False

    cookie_rtok = _get_browser_cookie("am_rtok")
    cookie_atok = _get_browser_cookie("am_atok")
    if cookie_manager is not None:
        try:
            all_cm = cookie_manager.get_all() or {}
            if not cookie_rtok and all_cm.get("am_rtok"):
                cookie_rtok = str(all_cm.get("am_rtok", "")).strip()
            if not cookie_atok and all_cm.get("am_atok"):
                cookie_atok = str(all_cm.get("am_atok", "")).strip()
        except Exception:
            pass
    cookie_user_verified = verify_session_token(cookie_rtok) if cookie_rtok else None
    has_valid_admin_cookie = verify_admin_token(cookie_atok) if cookie_atok else False

    # TỰ ĐỘNG KHÔI PHỤC TÀI KHOẢN CỤC BỘ TRÊN THIẾT BỊ (Cookie am_rtok / Query ?s= / localStorage)
    if not st.session_state["auth_username"]:
        restored = False
        # Lớp 1: Từ query param ?s=
        try:
            tok = str(st.query_params.get("s", "")).strip()
            if tok:
                verified = verify_session_token(tok)
                if verified:
                    uname, tok_tv = verified
                    user_payload = db_get_user(uname)
                    if user_payload and int(user_payload.get("token_version", 1)) == tok_tv:
                        apply_user_payload_to_session(uname, user_payload)
                        if cookie_user_verified == (uname, tok_tv):
                            st.session_state["is_login_remembered"] = True
                        restored = True
        except Exception:
            pass

        # Lớp 2: Từ Cookie trình duyệt (am_rtok) khi mở lại link gốc
        if not restored and cookie_user_verified:
            try:
                uname, tok_tv = cookie_user_verified
                user_payload = db_get_user(uname)
                if user_payload and int(user_payload.get("token_version", 1)) == tok_tv:
                    apply_user_payload_to_session(uname, user_payload)
                    st.session_state["is_login_remembered"] = True
                    restored = True
            except Exception:
                pass

    # KHÔI PHỤC QUYỀN TÁC GIẢ CỐ ĐỊNH (Query ?a= / Cookie am_atok)
    if not DEFAULT_AUTHOR_PASSWORD:
        st.session_state["is_author_admin"] = False
    else:
        if not st.session_state["is_author_admin"]:
            try:
                if verify_admin_token(str(st.query_params.get("a", ""))):
                    st.session_state["is_author_admin"] = True
            except Exception:
                pass
        if not st.session_state["is_author_admin"] and has_valid_admin_cookie:
            st.session_state["is_author_admin"] = True

    # Xóa ?s= và ?a= khỏi URL nếu trình duyệt đã có cookie để tránh lộ token; chỉ giữ trên URL khi chưa có cookie
    if st.session_state.get("auth_username"):
        cur_u = st.session_state["auth_username"]
        cur_tv = int(st.session_state.get("auth_token_version", 1))
        try:
            if cookie_user_verified == (cur_u, cur_tv):
                if "s" in st.query_params:
                    del st.query_params["s"]
            else:
                expected_s = create_session_token(cur_u, cur_tv)
                if st.query_params.get("s") != expected_s:
                    st.query_params["s"] = expected_s
        except Exception:
            pass
    if st.session_state.get("is_author_admin") and DEFAULT_AUTHOR_PASSWORD:
        try:
            if has_valid_admin_cookie:
                if "a" in st.query_params:
                    del st.query_params["a"]
            else:
                expected_a = create_admin_token()
                if st.query_params.get("a") != expected_a:
                    st.query_params["a"] = expected_a
        except Exception:
            pass

    # Lớp 3: Nếu vẫn chưa có phiên hoặc chưa có quyền tác giả -> đọc localStorage trình duyệt 1 lần
    need_u = not bool(st.session_state.get("auth_username"))
    need_a = bool(DEFAULT_AUTHOR_PASSWORD) and not bool(st.session_state.get("is_author_admin"))
    if (need_u or need_a) and not st.session_state.get("rtok_js_checked"):
        st.session_state["rtok_js_checked"] = True
        bootstrap_remembered_tokens_js(need_user=need_u, need_admin=need_a)


def main() -> None:
    cookie_manager = get_cookie_manager()
    init_session_state(cookie_manager=cookie_manager)
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
        if st.session_state.get("pending_remember_save"):
            save_remembered_login(
                st.session_state.pop("pending_remember_save"),
                token_version=int(st.session_state.get("auth_token_version", 1)),
                cookie_manager=cookie_manager,
            )
        if st.session_state.get("pending_remember_clear"):
            st.session_state.pop("pending_remember_clear")
            clear_remembered_login(cookie_manager=cookie_manager)
        if st.session_state.get("pending_admin_save"):
            st.session_state.pop("pending_admin_save")
            save_remembered_admin(cookie_manager=cookie_manager)
        if st.session_state.get("pending_admin_clear"):
            st.session_state.pop("pending_admin_clear")
            clear_remembered_admin(cookie_manager=cookie_manager)

        if st.session_state["auth_username"]:
            uname = st.session_state["auth_username"]
            sv_name = st.session_state.get("confirmed_user_name") or uname
            sv_uni = st.session_state.get("confirmed_user_uni") or ""
            st.success(f"Đang đăng nhập: **{sv_name}** (`@{uname}`)" + (f" · {sv_uni}" if sv_uni else ""))

            # Hỏi người dùng có muốn lưu đăng nhập cho các lần mở tab sau không
            if st.session_state.get("ask_remember_login") and not st.session_state.get("is_login_remembered"):
                st.info("Bạn có muốn **lưu đăng nhập** trên thiết bị này để các lần sau mở web vào thẳng tài khoản không?")
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Có, lưu luôn", key="btn_yes_remember", type="primary", use_container_width=True):
                        st.session_state["is_login_remembered"] = True
                        st.session_state["ask_remember_login"] = False
                        st.session_state["pending_remember_save"] = uname
                        st.toast("Đã lưu đăng nhập! Lần sau mở lại web sẽ tự vào tài khoản này.")
                        st.rerun()
                with rc2:
                    if st.button("Chỉ lần này", key="btn_no_remember", use_container_width=True):
                        st.session_state["ask_remember_login"] = False
                        st.rerun()
            elif st.session_state.get("is_login_remembered"):
                st.caption(f"Đồng bộ: {sync_badge} · Đã lưu đăng nhập tự động")
            else:
                st.caption(f"Đồng bộ: {sync_badge} · Phiên tạm thời")
                if st.button("Lưu đăng nhập trên thiết bị này", key="btn_save_remember_later", use_container_width=True):
                    st.session_state["is_login_remembered"] = True
                    st.session_state["pending_remember_save"] = uname
                    st.toast("Đã bật tự động đăng nhập cho các lần sau.")
                    st.rerun()

            if st.button("Đăng xuất", use_container_width=True):
                st.session_state["auth_token_version"] = int(st.session_state.get("auth_token_version", 1)) + 1
                sync_current_account_to_db()
                st.session_state["auth_username"] = ""
                st.session_state["auth_password_hash"] = ""
                st.session_state["auth_created_at"] = ""
                st.session_state["auth_last_login_at"] = ""
                st.session_state["auth_login_count"] = 1
                st.session_state["auth_token_version"] = 1
                st.session_state["saved_gemini_api_key"] = ""
                st.session_state["saved_vocab_notebook"] = []
                st.session_state["translation_history"] = []
                st.session_state["is_login_remembered"] = False
                st.session_state["ask_remember_login"] = False
                st.session_state["pending_remember_clear"] = True
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
                    l_remember = st.checkbox("Ghi nhớ đăng nhập trên thiết bị này", value=True)
                    if st.form_submit_button("Đăng nhập & Đồng bộ", type="primary", use_container_width=True):
                        u_clean = _normalize_username(l_user)
                        record = db_get_user(u_clean)
                        if record and _verify_password(l_pass, record.get("password_hash", "")):
                            record["login_count"] = int(record.get("login_count", 0)) + 1
                            record["last_login_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            record["token_version"] = int(record.get("token_version", 1))
                            db_save_user(u_clean, record)
                            apply_user_payload_to_session(u_clean, record)
                            if l_remember:
                                st.session_state["is_login_remembered"] = True
                                st.session_state["ask_remember_login"] = False
                                st.session_state["pending_remember_save"] = u_clean
                            else:
                                st.session_state["is_login_remembered"] = False
                                st.session_state["ask_remember_login"] = False
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
                    r_remember = st.checkbox("Ghi nhớ đăng nhập trên thiết bị này", value=True)
                    if st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True):
                        u_clean = _normalize_username(r_user)
                        if len(u_clean) < 3 or len(r_pass) < 4 or not r_name.strip() or not r_uni.strip():
                            st.warning("Nhập đủ tên đăng nhập (≥3 ký tự), mật khẩu (≥4 ký tự), họ tên và tên trường.")
                        elif db_get_user(u_clean) is not None:
                            st.error("Tên đăng nhập này đã tồn tại. Hãy chọn tên khác hoặc chuyển sang Đăng nhập.")
                        else:
                            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            new_payload = {
                                "password_hash": _hash_password(r_pass),
                                "created_at": now_ts,
                                "last_login_at": now_ts,
                                "login_count": 1,
                                "token_version": 1,
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
                            if r_remember:
                                st.session_state["is_login_remembered"] = True
                                st.session_state["ask_remember_login"] = False
                                st.session_state["pending_remember_save"] = u_clean
                            else:
                                st.session_state["is_login_remembered"] = False
                                st.session_state["ask_remember_login"] = False
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
                mode_lbl = st.radio(
                    "Chế độ model Gemini",
                    options=["Siêu tốc (3.5 Flash-Lite)", "Chất lượng cao (3.8 Flash)"],
                    index=0 if st.session_state.get("ai_speed_mode", "fast") == "fast" else 1,
                    horizontal=False,
                )
                new_ai_mode = "quality" if "3.8" in mode_lbl else "fast"
                if new_ai_mode != st.session_state.get("ai_speed_mode", "fast"):
                    st.session_state["ai_speed_mode"] = new_ai_mode
                    st.session_state.pop("pinned_gemini_model", None)
                    st.rerun()
                pref_now = PREFERRED_GEMINI_MODELS_QUALITY if new_ai_mode == "quality" else PREFERRED_GEMINI_MODELS_FAST
                best_m = next((m for m in pref_now if m in models_avail), models_avail[0] if models_avail else "gemini-3.5-flash-lite")
                top_m = st.session_state.get("pinned_gemini_model") or best_m
                st.caption(f"Sẵn sàng · Model: `{top_m}`")
        else:
            if st.session_state.get("auth_username") and SHARED_DEMO_GEMINI_KEY and DAILY_DEMO_LIMIT > 0:
                rem_quota = get_remaining_demo_quota()
                st.caption(f"Còn {rem_quota}/{DAILY_DEMO_LIMIT} lượt AI miễn phí hôm nay.")
            else:
                st.caption("Chưa có Key — đang dùng dịch cơ bản.")

        with st.expander("Hướng dẫn lấy API Key riêng miễn phí (30 giây)"):
            st.markdown(
                "1. Mở [Google AI Studio](https://aistudio.google.com/app/apikey) và đăng nhập bằng Gmail.\n"
                "2. Bấm **Create API key** để tạo khóa miễn phí.\n"
                "3. Sao chép khóa và dán vào ô **API Key cá nhân** ở trên để lưu vào tài khoản."
            )

        st.markdown("---")
        with st.expander("Dành cho tác giả"):
            if not DEFAULT_AUTHOR_PASSWORD:
                st.warning(
                    "Mục «Dành cho tác giả» đang bị khóa vì chưa cấu hình `AUTHOR_ADMIN_PASSWORD` "
                    "trong Streamlit Secrets (`.streamlit/secrets.toml`) hoặc biến môi trường."
                )
                if st.session_state.get("last_supabase_error"):
                    st.error(f"Lỗi Supabase gần nhất: {st.session_state['last_supabase_error']}")
            elif not st.session_state["is_author_admin"]:
                if st.session_state.get("last_supabase_error"):
                    st.error(f"Lỗi Supabase gần nhất: {st.session_state['last_supabase_error']}")
                pwd = st.text_input("Mật khẩu", type="password", key="author_pwd_in")
                if st.button("Mở khóa & Lưu cố định", use_container_width=True):
                    if verify_author_password(pwd):
                        st.session_state["is_author_admin"] = True
                        st.session_state["pending_admin_save"] = True
                        st.toast("Đã mở khóa và lưu cố định quyền Tác giả cho các lần sau!")
                        st.rerun()
                    else:
                        st.error("Mật khẩu không đúng.")
            else:
                st.caption(f"Đồng bộ Cloud: {'Đang bật Supabase' if _is_cloud_sync_enabled() else 'SQLite cục bộ'}")
                all_users = db_list_all_users()
                if st.session_state.get("last_supabase_error"):
                    st.error(f"Lỗi Supabase gần nhất: {st.session_state['last_supabase_error']}")
                st.markdown(f"**Tổng số tài khoản: {len(all_users)}**")
                if all_users:
                    st.download_button(
                        "Tải danh sách sinh viên (.CSV)",
                        data=export_users_to_csv(all_users),
                        file_name=f"danh_sach_nguoi_dung_{datetime.now().strftime('%Y-%m-%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                    with st.container(height=240):
                        for u in all_users:
                            st.markdown(
                                f"**{u['full_name']}** (`@{u['username']}`)<br/>"
                                f"<span style='font-size:0.78rem;opacity:0.8;'>"
                                f"{u['student_year']} · {u['university']}<br/>"
                                f"Đăng nhập: {u['login_count']} lần · Gần nhất: {u['last_login']}<br/>"
                                f"Từ vựng: {u['vocab_count']} · Lịch sử: {u['history_count']} · API Key: {u['has_api_key']}"
                                f"</span>",
                                unsafe_allow_html=True,
                            )
                            st.markdown("<hr style='margin:6px 0;opacity:0.25;'/>", unsafe_allow_html=True)

                with st.form("admin_reset_pwd_form", clear_on_submit=True):
                    st.caption("Hỗ trợ đặt lại mật khẩu (khi sinh viên quên):")
                    rp_user = st.text_input("Username cần đặt lại", placeholder="vd: minh_spb")
                    rp_new = st.text_input("Mật khẩu mới", type="password")
                    if st.form_submit_button("Đặt lại mật khẩu", use_container_width=True):
                        u_target = _normalize_username(rp_user)
                        rec = db_get_user(u_target)
                        if not rec:
                            st.error("Không tìm thấy tài khoản này.")
                        elif len(rp_new) < 4:
                            st.warning("Mật khẩu mới cần ít nhất 4 ký tự.")
                        else:
                            rec["password_hash"] = _hash_password(rp_new)
                            rec["token_version"] = int(rec.get("token_version", 1)) + 1
                            db_save_user(u_target, rec)
                            st.success(f"Đã đặt lại mật khẩu và vô hiệu hóa phiên cũ cho @{u_target}.")

                if st.button("Khóa lại (Hủy lưu quyền tác giả)", use_container_width=True):
                    st.session_state["is_author_admin"] = False
                    st.session_state["pending_admin_clear"] = True
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

        opt_c1, opt_c2 = st.columns([2.3, 1.5])
        with opt_c1:
            level_label = st.radio(
                "Chế độ giải thích",
                options=["Người mới (A0–A1)", "Chuyên sâu"],
                index=0 if st.session_state.get("learner_level", "beginner") == "beginner" else 1,
                horizontal=True,
                label_visibility="collapsed",
            )
            st.session_state["learner_level"] = "beginner" if "Người mới" in level_label else "advanced"
        with opt_c2:
            st.session_state["tts_slow_mode"] = st.checkbox(
                "Đọc chậm (A0–A1)",
                value=bool(st.session_state.get("tts_slow_mode", False)),
            )

        if "pending_input_text" in st.session_state:
            st.session_state["input_text_area"] = st.session_state.pop("pending_input_text")

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
                st.session_state["pending_input_text"] = ""
                st.rerun()
        with b4:
            if source_text.strip():
                k_map = {"word": "Từ / Cụm ngắn", "sentence": "Câu", "paragraph": "Đoạn văn"}
                eff_preview = resolve_effective_direction(source_text, direction)
                st.caption(f"{k_map[classify_input_type(source_text)]} · {eff_preview} · {len(source_text.split())} từ")

        if tts_clicked and source_text.strip():
            has_cyr = bool(re.search(r"[а-яА-ЯёЁ]", source_text))
            lang_tts = "ru" if has_cyr else "vi"
            audio_b = generate_tts_audio(source_text, lang_tts, slow=bool(st.session_state.get("tts_slow_mode", False)))
            if audio_b:
                st.audio(audio_b, format="audio/mp3")

        if translate_clicked:
            if not source_text.strip():
                st.warning("Vui lòng nhập từ, câu hoặc đoạn văn cần dịch.")
            else:
                effective_dir = resolve_effective_direction(source_text, direction)
                learner_lvl = st.session_state.get("learner_level", "beginner")
                result_data: Optional[Dict] = None
                meta_badge = "Dịch nhanh"
                active_ai_key = clean_key_input
                using_demo_key = False
                if not active_ai_key and st.session_state.get("auth_username") and SHARED_DEMO_GEMINI_KEY and get_remaining_demo_quota() > 0:
                    active_ai_key = SHARED_DEMO_GEMINI_KEY
                    using_demo_key = True

                if active_ai_key:
                    with st.spinner("Đang dịch và phân tích ngữ pháp bằng Gemini AI..."):
                        result_data, g_err, elapsed, model_used = call_gemini_smart_translate(
                            active_ai_key, source_text, effective_dir, learner_level=learner_lvl
                        )
                        if result_data:
                            if using_demo_key:
                                consume_demo_quota()
                                meta_badge = f"{model_used} (Dùng thử {get_remaining_demo_quota()}/{DAILY_DEMO_LIMIT}) · {elapsed:.2f}s"
                            else:
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
                            st.session_state["pending_input_text"] = h["full_source"]
                            st.session_state["last_translation_result"] = h["result"]
                            st.session_state["last_meta_badge"] = h["meta_badge"]
                            st.rerun()

    with tab2:
        render_vocab_and_practice_tab()

    with tab3:
        render_russian_knowledge_hub()


if __name__ == "__main__":
    main()