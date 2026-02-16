import streamlit as st
from database import (
    init_db, get_all_categories, get_category_names,
    insert_category, delete_category, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Catégories — Budget", page_icon="🏷️", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

EMOJI_LIST = ["🛒", "🧴", "🎉", "🚗", "🏠", "🛍️", "💊", "💰", "🎮", "📚", "🍕", "☕",
              "🎵", "✈️", "🐕", "👶", "🏋️", "📱", "🎁", "🔧", "📁", "🥬", "🎫", "🍺",
              "💻", "🎬", "🏖️", "🧹", "🏦", "🎓"]

st.markdown("# 🏷️ Catégories")

# ─── Create ───
st.markdown("#### ➕ Nouvelle catégorie")

c1, c2 = st.columns(2)
with c1:
    nc_nom = st.text_input("Nom", key="nc_nom", placeholder="Ex: Shotgun, Légumes…")
with c2:
    nc_icon = st.selectbox("Icône", EMOJI_LIST, key="nc_icon")

c3, c4 = st.columns(2)
with c3:
    nc_color = st.color_picker("Couleur", value="#a78bfa", key="nc_color")
with c4:
    nc_kw = st.text_input("Mots-clés IA", key="nc_kw", placeholder="shotgun, billet…",
                           help="Séparés par virgules")

nc_sub = st.text_input("Sous-catégories (optionnel)", key="nc_sub",
                        placeholder="Ex: Courses, Restaurant, Boulangerie",
                        help="Séparées par virgules. Permet un suivi plus fin.")

# Preview
if nc_nom:
    sub_preview = f" · {nc_sub}" if nc_sub else ""
    st.markdown(f"""<div class="glass" style="padding:0.6rem 1rem;margin:0.5rem 0">
        <div style="display:flex;align-items:center;gap:0.5rem">
            <span style="font-size:1.5rem">{nc_icon}</span>
            <div>
                <div style="font-weight:600;color:#e2e8f0">{nc_nom}</div>
                <div style="color:#64748b;font-size:0.72rem">{nc_kw or 'Pas de mots-clés'}{sub_preview}</div>
            </div>
            <div style="margin-left:auto;width:16px;height:16px;border-radius:50%;background:{nc_color}"></div>
        </div>
    </div>""", unsafe_allow_html=True)

cat_names = get_category_names(uid)

if st.button("➕ Créer cette catégorie", type="primary", use_container_width=True, key="nc_save"):
    if not nc_nom:
        st.warning("⚠️ Nom requis.")
    elif nc_nom in cat_names:
        st.warning("⚠️ Cette catégorie existe déjà.")
    else:
        # We store sous_categories in the categories table directly
        from database import get_connection
        conn = get_connection()
        from datetime import datetime
        conn.execute(
            "INSERT INTO categories (user_id, nom, icon, color, mots_cles, sous_categories, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uid, nc_nom, nc_icon, nc_color, nc_kw, nc_sub, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Catégorie '{nc_nom}' créée !")
        st.rerun()

# ─── List ───
st.markdown("---")
st.markdown("#### 📋 Vos catégories")

cats = get_all_categories(uid)
if not cats:
    st.info("Aucune catégorie.")
else:
    for cat in cats:
        c1, c2 = st.columns([5, 1])
        with c1:
            kw = cat.get("mots_cles", "")
            sub = cat.get("sous_categories", "")
            details = []
            if kw: details.append(f"🔑 {kw}")
            if sub: details.append(f"📂 {sub}")
            detail_str = " · ".join(details) if details else "Pas de détails"
            color = cat.get("color", "#a78bfa")
            st.markdown(f"""<div class="glass" style="padding:0.55rem 1rem;margin-bottom:0.3rem">
                <div style="display:flex;align-items:center;gap:0.6rem">
                    <span style="font-size:1.2rem">{cat['icon']}</span>
                    <div>
                        <span style="font-weight:600;color:#e2e8f0">{cat['nom']}</span>
                        <div style="color:#64748b;font-size:0.7rem">{detail_str}</div>
                    </div>
                    <div style="margin-left:auto;width:12px;height:12px;border-radius:50%;background:{color}"></div>
                </div>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"dc_{cat['id']}"):
                delete_category(cat["id"])
                st.rerun()

    st.caption(f"{len(cats)} catégorie(s)")
