import streamlit as st
from database import (
    init_db, create_savings_goal, get_savings_goals,
    update_savings_goal, delete_savings_goal, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Épargne — Budget", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

st.markdown("# 🎯 Objectifs d'épargne")

# ─── Create ───
st.markdown("#### ➕ Nouvel objectif")
c1, c2 = st.columns(2)
with c1:
    g_title = st.text_input("Objectif", key="g_title", placeholder="Ex: Voyage au Japon 🗾")
with c2:
    g_target = st.number_input("Montant cible €", min_value=0.0, step=10.0, format="%.0f", key="g_target")

if st.button("🎯 Créer l'objectif", type="primary", use_container_width=True, key="g_create"):
    if not g_title or g_target <= 0:
        st.warning("⚠️ Remplissez le nom et le montant.")
    else:
        create_savings_goal(uid, g_title, g_target)
        st.success(f"✅ Objectif '{g_title}' créé !"); st.rerun()

# ─── List ───
st.markdown("---")
goals = get_savings_goals(uid)

if not goals:
    st.info("🎯 Aucun objectif d'épargne. Créez-en un ci-dessus !")
else:
    total_saved = sum(g["current_amount"] for g in goals)
    total_target = sum(g["target_amount"] for g in goals)
    overall_pct = (total_saved / total_target * 100) if total_target > 0 else 0

    st.markdown(f"""<div class="kpi-grid">
        <div class="kpi"><div class="kpi-label">Objectifs</div><div class="kpi-val blue">{len(goals)}</div></div>
        <div class="kpi"><div class="kpi-label">Total épargné</div><div class="kpi-val green">{total_saved:.0f}€</div></div>
        <div class="kpi"><div class="kpi-label">Total cible</div><div class="kpi-val white">{total_target:.0f}€</div></div>
        <div class="kpi"><div class="kpi-label">Progression</div><div class="kpi-val {'green' if overall_pct >= 100 else 'blue'}">{overall_pct:.0f}%</div></div>
    </div>""", unsafe_allow_html=True)

    for g in goals:
        pct = (g["current_amount"] / g["target_amount"] * 100) if g["target_amount"] > 0 else 0
        remaining = max(g["target_amount"] - g["current_amount"], 0)
        completed = pct >= 100

        if completed:
            status_icon = "🏆"
            bar_color = "#34d399"
        elif pct >= 50:
            status_icon = "🔥"
            bar_color = "#818cf8"
        elif pct >= 25:
            status_icon = "📈"
            bar_color = "#fbbf24"
        else:
            status_icon = "🌱"
            bar_color = "#94a3b8"

        st.markdown(f"""<div class="glass" style="padding:0.8rem 1rem;margin-bottom:0.5rem">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <div>
                    <span style="font-weight:700;color:#e2e8f0;font-size:0.92rem">{status_icon} {g['title']}</span>
                    {'<span style="color:#34d399;font-size:0.72rem;margin-left:0.5rem">✅ Atteint !</span>' if completed else ''}
                </div>
                <span style="color:{bar_color};font-weight:700;font-size:1rem">{g['current_amount']:.0f}€ / {g['target_amount']:.0f}€</span>
            </div>
            <div class="cat-track" style="height:8px"><div class="cat-fill" style="width:{min(pct, 100):.0f}%;background:{bar_color}"></div></div>
            <div style="display:flex;justify-content:space-between;margin-top:4px">
                <span style="color:#64748b;font-size:0.68rem">{pct:.0f}%</span>
                <span style="color:#64748b;font-size:0.68rem">Reste {remaining:.0f}€</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # Actions
        c1, c2, c3 = st.columns([2, 1, 0.5])
        with c1:
            add_amount = st.number_input("Ajouter €", min_value=0.0, step=5.0, format="%.0f",
                                          key=f"gadd_{g['id']}", label_visibility="collapsed")
        with c2:
            if st.button("💰 Ajouter", key=f"gsave_{g['id']}", use_container_width=True):
                if add_amount > 0:
                    new_total = g["current_amount"] + add_amount
                    update_savings_goal(g["id"], new_total)
                    if new_total >= g["target_amount"]:
                        st.balloons()
                    st.rerun()
        with c3:
            if st.button("🗑️", key=f"gdel_{g['id']}"):
                delete_savings_goal(g["id"]); st.rerun()
