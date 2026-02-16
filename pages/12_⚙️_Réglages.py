import streamlit as st
from database import (
    init_db, update_user_preference, get_user_by_id,
    ensure_user_has_categories, AVATAR_LIST,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Réglages — Budget", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

st.markdown("# ⚙️ Réglages")

# ─── Theme ───
st.markdown("#### 🎨 Apparence")
current_theme = user.get("theme", "dark")
theme = st.radio("Thème", ["dark", "light"], index=0 if current_theme == "dark" else 1,
                  format_func=lambda x: "🌙 Mode sombre" if x == "dark" else "☀️ Mode clair",
                  horizontal=True, key="pref_theme")
if theme != current_theme:
    update_user_preference(uid, "theme", theme)
    st.rerun()

# ─── Preferred page ───
st.markdown("#### 🏠 Page d'accueil")
PAGES = ["Dashboard", "Ajouter", "Récurrent", "Catégories", "Social", "Recherche", "Statistiques", "Budgets", "Calendrier", "Épargne", "Badges"]
current_page = user.get("preferred_page", "Dashboard")
idx = PAGES.index(current_page) if current_page in PAGES else 0
pref_page = st.selectbox("Page de démarrage après connexion", PAGES, index=idx, key="pref_page")
if pref_page != current_page:
    update_user_preference(uid, "preferred_page", pref_page)
    st.success(f"✅ Page d'accueil : {pref_page}")

# ─── Avatar ───
st.markdown("#### 😀 Avatar")
st.caption(f"Actuel : {user.get('avatar', '👤')}")
avatar_cols = st.columns(10)
for i, av in enumerate(AVATAR_LIST):
    with avatar_cols[i % 10]:
        if st.button(av, key=f"av_pref_{i}"):
            from database import get_connection
            conn = get_connection()
            conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (av, uid))
            conn.commit(); conn.close()
            st.session_state["user_avatar"] = av
            st.rerun()

# ─── App info ───
st.markdown("---")
st.markdown("#### ℹ️ À propos")
st.caption("Budget Tracker v3.0 — Gérez vos dépenses intelligemment")
st.caption("Built with ❤️ using Streamlit + Gemini")
