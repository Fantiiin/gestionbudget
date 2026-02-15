import hashlib
import secrets
import streamlit as st
from database import create_user, get_user_by_username, get_user_by_id, seed_default_categories, AVATAR_LIST


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored_hash: str) -> bool:
    if ":" not in stored_hash:
        return False
    salt, h = stored_hash.split(":", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def get_current_user_id() -> int | None:
    return st.session_state.get("user_id")


def get_current_user() -> dict | None:
    uid = get_current_user_id()
    if uid is None:
        return None
    return get_user_by_id(uid)


def require_auth():
    """Call at top of each page. Stops execution if not logged in."""
    if get_current_user_id() is None:
        st.switch_page("app.py")
        st.stop()


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def show_auth_page():
    """Display login/register. Returns True if authenticated."""
    if get_current_user_id() is not None:
        return True

    st.markdown("""
    <style>
        .auth-box {
            max-width: 420px; margin: 1.5rem auto; padding: 2rem;
            background: rgba(15, 15, 26, 0.7);
            backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(167, 139, 250, 0.15);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .auth-header {
            text-align: center; margin-bottom: 1.5rem;
        }
        .auth-header h2 {
            background: linear-gradient(135deg, #a78bfa, #818cf8, #06b6d4);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 2rem; font-weight: 800; margin: 0;
        }
        .auth-header p { color: #94a3b8; font-size: 0.9rem; margin-top: 0.3rem; }
        .avatar-grid {
            display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;
            margin: 0.5rem 0;
        }
        .avatar-option {
            font-size: 1.6rem; padding: 6px; cursor: pointer;
            border-radius: 10px; transition: all 0.2s;
            border: 2px solid transparent;
        }
        .avatar-option:hover { background: rgba(167,139,250,0.15); }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-header">
        <h2>🧾 Budget Tracker</h2>
        <p>Gérez vos dépenses intelligemment</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Connexion", "📝 Inscription"])

    with tab_login:
        username = st.text_input("Nom d'utilisateur", key="login_user", placeholder="ex: fanta")
        password = st.text_input("Mot de passe", type="password", key="login_pass")

        if st.button("Se connecter", type="primary", use_container_width=True, key="login_btn"):
            if not username or not password:
                st.warning("⚠️ Remplissez tous les champs.")
            else:
                user = get_user_by_username(username)
                if user and _verify_password(password, user["password_hash"]):
                    st.session_state["user_id"] = user["id"]
                    st.session_state["user_display_name"] = user["display_name"]
                    st.session_state["user_avatar"] = user.get("avatar", "👤")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects.")

    with tab_register:
        new_user = st.text_input("Nom d'utilisateur", key="reg_user", placeholder="ex: fanta")
        new_display = st.text_input("Prénom / surnom", key="reg_display", placeholder="Ex: Fantinou")

        st.markdown("**Choisissez votre avatar**")
        avatar_cols = st.columns(10)
        if "selected_avatar" not in st.session_state:
            st.session_state["selected_avatar"] = AVATAR_LIST[0]

        for i, av in enumerate(AVATAR_LIST):
            with avatar_cols[i % 10]:
                selected = st.session_state.get("selected_avatar") == av
                btn_type = "primary" if selected else "secondary"
                if st.button(av, key=f"av_{i}", type=btn_type):
                    st.session_state["selected_avatar"] = av
                    st.rerun()

        st.caption(f"Avatar sélectionné : {st.session_state.get('selected_avatar', '👤')}")

        new_pass = st.text_input("Mot de passe", type="password", key="reg_pass")
        new_pass2 = st.text_input("Confirmer", type="password", key="reg_pass2")

        if st.button("Créer mon compte", type="primary", use_container_width=True, key="reg_btn"):
            if not new_user or not new_display or not new_pass:
                st.warning("⚠️ Remplissez tous les champs.")
            elif len(new_pass) < 4:
                st.warning("⚠️ Mot de passe trop court (4 caractères min).")
            elif new_pass != new_pass2:
                st.error("❌ Les mots de passe ne correspondent pas.")
            elif get_user_by_username(new_user):
                st.error("❌ Nom d'utilisateur déjà pris.")
            else:
                try:
                    avatar = st.session_state.get("selected_avatar", "👤")
                    hashed = _hash_password(new_pass)
                    uid = create_user(new_user, hashed, new_display, avatar)
                    seed_default_categories(uid)
                    st.session_state["user_id"] = uid
                    st.session_state["user_display_name"] = new_display
                    st.session_state["user_avatar"] = avatar
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    return False
