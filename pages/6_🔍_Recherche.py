import streamlit as st
from datetime import datetime
from collections import defaultdict

from database import (
    init_db, search_transactions, get_category_map,
    get_user_by_id, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Recherche — Budget", page_icon="🔍", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin",
           "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def format_date_fr(ds):
    try:
        d = datetime.strptime(ds, "%Y-%m-%d")
        return f"{d.day} {MOIS_FR[d.month]} {d.year}"
    except (ValueError, IndexError):
        return ds


st.markdown("# 🔍 Recherche")

query = st.text_input("Rechercher", placeholder="Carrefour, Netflix, #vacances…", key="search_q")

if query and len(query) >= 2:
    results = search_transactions(uid, query)
    cat_map = get_category_map(uid)

    if not results:
        st.info(f"Aucun résultat pour « {query} »")
    else:
        total_dep = sum(t["montant_total"] for t in results if t.get("type", "depense") == "depense")
        total_rev = sum(t["montant_total"] for t in results if t.get("type") == "revenu")

        st.markdown(f"""<div class="kpi-grid" style="grid-template-columns: repeat(3, 1fr)">
            <div class="kpi"><div class="kpi-label">Résultats</div><div class="kpi-val white">{len(results)}</div></div>
            <div class="kpi"><div class="kpi-label">Total dépenses</div><div class="kpi-val red">−{total_dep:.2f}€</div></div>
            <div class="kpi"><div class="kpi-label">Total revenus</div><div class="kpi-val green">+{total_rev:.2f}€</div></div>
        </div>""", unsafe_allow_html=True)

        # Group by month
        by_month = defaultdict(list)
        for t in results:
            m = t["date"][:7]
            by_month[m].append(t)

        for month in sorted(by_month.keys(), reverse=True):
            txs = by_month[month]
            m_dep = sum(t["montant_total"] for t in txs if t.get("type", "depense") == "depense")
            yr, mo = month.split("-")
            st.markdown(f'<div class="day-header"><span>{MOIS_FR[int(mo)].capitalize()} {yr}</span><span class="day-total"><span class="red">−{m_dep:.2f}€</span> ({len(txs)})</span></div>', unsafe_allow_html=True)

            for t in txs:
                ci = cat_map.get(t["categorie"], {})
                ic = ci.get("icon", "📁")
                ir = t.get("type") == "revenu"
                ac = "green" if ir else "red"
                sg = "+" if ir else "−"
                tag_s = ""
                if t.get("tags"):
                    tag_s = f'<span style="color:#818cf8;font-size:0.6rem;margin-left:0.3rem">{t["tags"]}</span>'
                st.markdown(f"""<div class="txn"><div class="txn-row"><div class="txn-left">
                    <span class="txn-icon">{ic}</span>
                    <div><div class="txn-ens">{t['enseigne']}{tag_s}</div>
                    <div class="txn-cat">{t['categorie']} · {format_date_fr(t['date'])}</div></div>
                    </div><span class="txn-amt {ac}">{sg}{t['montant_total']:.2f}€</span></div></div>""", unsafe_allow_html=True)
            st.markdown("")

elif query:
    st.caption("Tapez au moins 2 caractères.")
else:
    st.info("🔍 Recherchez une enseigne, catégorie ou tag dans tout votre historique.")
