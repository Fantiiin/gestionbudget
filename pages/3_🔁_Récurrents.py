import streamlit as st
from database import (
    init_db, insert_recurring, get_all_recurring, delete_recurring,
    get_category_names, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Récurrents — Budget", page_icon="🔁", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)
cat_names = get_category_names(uid)

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

st.markdown("# 🔁 Paiements récurrents")

# ─── Add ───
st.markdown("#### ➕ Nouveau récurrent")

c1, c2 = st.columns(2)
with c1:
    rce = st.text_input("Label", key="rce", placeholder="Loyer, Netflix…")
with c2:
    rcm = st.number_input("Montant €", value=0.0, min_value=0.0, step=0.01, format="%.2f", key="rcm")

c3, c4, c5 = st.columns(3)
with c3:
    rcc = st.selectbox("Catégorie", cat_names, key="rcc")
with c4:
    rct = st.selectbox("Type", ["Dépense", "Revenu"], key="rct")
    rct_val = "depense" if rct == "Dépense" else "revenu"
with c5:
    rcf = st.selectbox("Fréquence", ["Mensuel", "Hebdomadaire"], key="rcf")
    rcf_val = rcf.lower()

if rcf_val == "mensuel":
    rcj = st.number_input("Jour du mois", 1, 31, 1, key="rcj")
else:
    rcjl = st.selectbox("Jour de la semaine", JOURS_FR, key="rcjs")
    rcj = JOURS_FR.index(rcjl)

st.markdown("")
if st.button("➕ Ajouter ce récurrent", type="primary", use_container_width=True, key="rca"):
    if not rce or rcm <= 0:
        st.warning("⚠️ Label et montant requis.")
    else:
        insert_recurring(uid, rce, rcm, rcc, rct_val, rcf_val, rcj)
        st.success(f"✅ Récurrent '{rce}' ajouté")
        st.rerun()

# ─── List ───
st.markdown("---")
st.markdown("#### 📋 Vos récurrents actifs")

recs = get_all_recurring(uid)
if not recs:
    st.info("Aucun paiement récurrent configuré.")
else:
    for r in recs:
        if r["frequence"] == "mensuel":
            freq_label = f"le {r['jour']} du mois"
        else:
            freq_label = f"chaque {JOURS_FR[r['jour']]}"

        is_rev = r["type"] == "revenu"
        sign = "+" if is_rev else "−"
        color = "green" if is_rev else "red"
        type_label = "Revenu" if is_rev else "Dépense"

        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"""<div class="glass" style="padding:0.6rem 1rem;margin-bottom:0.3rem">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <div style="font-weight:600;color:#e2e8f0;font-size:0.9rem">{r['enseigne']}</div>
                        <div style="color:#64748b;font-size:0.72rem">{r['categorie']} · {freq_label} · {type_label}</div>
                    </div>
                    <span class="{color}" style="font-weight:700;font-size:1rem">{sign}{r['montant']:.2f}€</span>
                </div>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"dr_{r['id']}"):
                delete_recurring(r["id"])
                st.rerun()
