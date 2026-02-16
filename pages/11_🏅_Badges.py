import streamlit as st
from database import (
    init_db, get_all_transactions, get_budgets, get_friends,
    get_savings_goals, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Badges — Budget", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

st.markdown("# 🏅 Succès & Badges")

# ─── Calculate user stats ───
all_tx = get_all_transactions(uid)
budgets = get_budgets(uid)
friends = get_friends(uid)
goals = get_savings_goals(uid)

total_txn = len(all_tx)
total_dep = sum(t["montant_total"] for t in all_tx if t.get("type", "depense") == "depense")
total_rev = sum(t["montant_total"] for t in all_tx if t.get("type") == "revenu")
unique_enseignes = len(set(t["enseigne"] for t in all_tx))
unique_cats = len(set(t["categorie"] for t in all_tx))
months_active = len(set(t["date"][:7] for t in all_tx))

# ─── Badge definitions ───
BADGES = [
    # Transactions
    {"icon": "🧾", "title": "Premier pas", "desc": "Ajouter sa première transaction", "check": total_txn >= 1},
    {"icon": "📝", "title": "Habitué", "desc": "10 transactions", "check": total_txn >= 10},
    {"icon": "📊", "title": "Organisé", "desc": "50 transactions", "check": total_txn >= 50},
    {"icon": "📈", "title": "Pro du suivi", "desc": "100 transactions", "check": total_txn >= 100},
    {"icon": "🏆", "title": "Comptable en herbe", "desc": "500 transactions", "check": total_txn >= 500},
    {"icon": "💫", "title": "Légende", "desc": "1000 transactions", "check": total_txn >= 1000},

    # Enseignes
    {"icon": "🛍️", "title": "Client fidèle", "desc": "Dépenser dans 5 enseignes différentes", "check": unique_enseignes >= 5},
    {"icon": "🌍", "title": "Globe-trotter", "desc": "Dépenser dans 20 enseignes différentes", "check": unique_enseignes >= 20},
    {"icon": "🗺️", "title": "Explorateur", "desc": "Dépenser dans 50 enseignes différentes", "check": unique_enseignes >= 50},

    # Categories
    {"icon": "🎨", "title": "Diversifié", "desc": "Utiliser 5 catégories différentes", "check": unique_cats >= 5},
    {"icon": "🌈", "title": "Arc-en-ciel", "desc": "Utiliser 10 catégories", "check": unique_cats >= 10},

    # Months
    {"icon": "📅", "title": "Régulier", "desc": "Tracker 3 mois consécutifs", "check": months_active >= 3},
    {"icon": "🗓️", "title": "Discipliné", "desc": "Tracker 6 mois", "check": months_active >= 6},
    {"icon": "🎂", "title": "1 an de suivi !", "desc": "Tracker pendant 12 mois", "check": months_active >= 12},

    # Revenue
    {"icon": "💰", "title": "Premier revenu", "desc": "Ajouter un revenu", "check": total_rev > 0},
    {"icon": "💎", "title": "Épargnant", "desc": "Plus de revenus que de dépenses", "check": total_rev > total_dep and total_rev > 0},

    # Budgets
    {"icon": "🎯", "title": "Budgétiste", "desc": "Créer son premier budget", "check": len(budgets) > 0},
    {"icon": "📏", "title": "Contrôleur", "desc": "Avoir 5+ budgets actifs", "check": len(budgets) >= 5},

    # Social
    {"icon": "👥", "title": "Social", "desc": "Ajouter un ami", "check": len(friends) >= 1},
    {"icon": "🤝", "title": "Populaire", "desc": "Avoir 5 amis", "check": len(friends) >= 5},

    # Savings
    {"icon": "🌱", "title": "Graines d'épargne", "desc": "Créer un objectif d'épargne", "check": len(goals) >= 1},
    {"icon": "🏆", "title": "Objectif atteint !", "desc": "Atteindre un objectif d'épargne", "check": any(g["current_amount"] >= g["target_amount"] for g in goals) if goals else False},

    # Spending milestones
    {"icon": "💸", "title": "100€ dépensés", "desc": "Dépenser 100€ au total", "check": total_dep >= 100},
    {"icon": "🏦", "title": "1 000€ tracké", "desc": "Dépenser 1000€ au total", "check": total_dep >= 1000},
    {"icon": "💳", "title": "10 000€ tracké", "desc": "Tracker 10000€ de dépenses", "check": total_dep >= 10000},
]

unlocked = [b for b in BADGES if b["check"]]
locked = [b for b in BADGES if not b["check"]]
pct = (len(unlocked) / len(BADGES) * 100) if BADGES else 0

# ─── KPIs ───
st.markdown(f"""<div class="kpi-grid">
    <div class="kpi"><div class="kpi-label">Débloqués</div><div class="kpi-val green">{len(unlocked)}/{len(BADGES)}</div></div>
    <div class="kpi"><div class="kpi-label">Progression</div><div class="kpi-val blue">{pct:.0f}%</div></div>
    <div class="kpi"><div class="kpi-label">Transactions</div><div class="kpi-val white">{total_txn}</div></div>
    <div class="kpi"><div class="kpi-label">Mois actifs</div><div class="kpi-val white">{months_active}</div></div>
</div>""", unsafe_allow_html=True)

# Progress bar
st.markdown(f"""<div class="cat-track" style="height:10px;margin-bottom:1rem">
    <div class="cat-fill" style="width:{pct:.0f}%;background:linear-gradient(90deg,#a78bfa,#34d399)"></div>
</div>""", unsafe_allow_html=True)

# ─── Unlocked ───
if unlocked:
    st.markdown("#### ✨ Débloqués")
    cols = st.columns(3)
    for i, b in enumerate(unlocked):
        with cols[i % 3]:
            st.markdown(f"""<div class="glass" style="padding:0.8rem;margin-bottom:0.4rem;text-align:center;border-color:rgba(52,211,153,0.2)">
                <div style="font-size:2rem">{b['icon']}</div>
                <div style="font-weight:700;color:#34d399;font-size:0.85rem;margin:4px 0">{b['title']}</div>
                <div style="color:#94a3b8;font-size:0.68rem">{b['desc']}</div>
            </div>""", unsafe_allow_html=True)

# ─── Locked ───
if locked:
    st.markdown("#### 🔒 À débloquer")
    cols = st.columns(3)
    for i, b in enumerate(locked):
        with cols[i % 3]:
            st.markdown(f"""<div class="glass" style="padding:0.8rem;margin-bottom:0.4rem;text-align:center;opacity:0.5">
                <div style="font-size:2rem;filter:grayscale(100%)">{b['icon']}</div>
                <div style="font-weight:600;color:#64748b;font-size:0.85rem;margin:4px 0">{b['title']}</div>
                <div style="color:#475569;font-size:0.68rem">{b['desc']}</div>
            </div>""", unsafe_allow_html=True)
