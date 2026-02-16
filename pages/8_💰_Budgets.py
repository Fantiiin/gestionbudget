import streamlit as st
from database import (
    init_db, get_budgets, set_budget, delete_budget,
    get_category_names, get_category_map, get_transactions_by_month,
    ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css
from datetime import datetime
from collections import defaultdict

st.set_page_config(page_title="Budgets — Budget", page_icon="💰", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

cat_names = get_category_names(uid)
cat_map = get_category_map(uid)
budgets = get_budgets(uid)

st.markdown("# 💰 Budgets mensuels")

# ─── Set budget ───
st.markdown("#### ➕ Définir un plafond")
c1, c2 = st.columns(2)
with c1:
    b_cat = st.selectbox("Catégorie", [c for c in cat_names if c != "Revenu"], key="b_cat")
with c2:
    current = budgets.get(b_cat, 0.0)
    b_max = st.number_input("Plafond mensuel €", value=current, min_value=0.0, step=10.0, format="%.0f", key="b_max")

if st.button("💾 Enregistrer le plafond", type="primary", use_container_width=True):
    if b_max > 0:
        set_budget(uid, b_cat, b_max)
        st.success(f"✅ Budget {b_cat} = {b_max:.0f}€/mois")
        st.rerun()
    else:
        st.warning("⚠️ Le plafond doit être supérieur à 0€.")

# ─── Current month gauges ───
st.markdown("---")
now = datetime.now()
st.markdown(f"#### 📊 État du mois — {now.strftime('%B %Y')}")

txs = get_transactions_by_month(uid, now.year, now.month)
cat_spent = defaultdict(float)
for t in txs:
    if t.get("type", "depense") == "depense":
        cat_spent[t["categorie"]] += t["montant_total"]

budgets = get_budgets(uid)  # Refresh

if not budgets:
    st.info("Aucun budget défini. Ajoutez un plafond ci-dessus.")
else:
    for cat, max_val in sorted(budgets.items()):
        spent = cat_spent.get(cat, 0)
        pct = min((spent / max_val * 100), 100) if max_val > 0 else 0
        remaining = max_val - spent
        over = spent > max_val
        ci = cat_map.get(cat, {})
        ic = ci.get("icon", "📁")
        co = ci.get("color", "#a78bfa")

        if over:
            bar_color = "#ef4444"
            status = f"⚠️ Dépassé de {abs(remaining):.0f}€"
            status_color = "#ef4444"
        elif pct >= 80:
            bar_color = "#fbbf24"
            status = f"⚡ Reste {remaining:.0f}€"
            status_color = "#fbbf24"
        else:
            bar_color = co
            status = f"✓ Reste {remaining:.0f}€"
            status_color = "#34d399"

        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"""<div class="glass" style="padding:0.7rem 1rem;margin-bottom:0.35rem">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                    <span style="font-weight:600;color:#e2e8f0">{ic} {cat}</span>
                    <span style="font-size:0.82rem"><span style="color:#e2e8f0;font-weight:600">{spent:.0f}€</span> <span style="color:#64748b">/ {max_val:.0f}€</span></span>
                </div>
                <div class="cat-track" style="height:8px">
                    <div class="cat-fill" style="width:{pct:.0f}%;background:{bar_color}"></div>
                </div>
                <div style="font-size:0.7rem;color:{status_color};margin-top:3px">{status}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"db_{cat}"):
                delete_budget(uid, cat)
                st.rerun()
