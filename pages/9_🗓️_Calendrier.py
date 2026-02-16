import streamlit as st
import calendar
from datetime import date, datetime
from collections import defaultdict

from database import (
    init_db, get_transactions_by_month, get_budgets,
    get_category_map, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Calendrier — Budget", page_icon="🗓️", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

MOIS_FR = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
           "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
JOURS_FR_SHORT = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

st.markdown("# 🗓️ Calendrier")

now = date.today()
c1, c2 = st.columns(2)
with c1:
    yr = st.selectbox("Année", range(now.year - 2, now.year + 2), index=2, key="cal_yr")
with c2:
    mo = st.selectbox("Mois", range(1, 13), index=now.month - 1, format_func=lambda x: MOIS_FR[x], key="cal_mo")

txs = get_transactions_by_month(uid, yr, mo)
budgets = get_budgets(uid)
total_budget = sum(budgets.values())
cat_map = get_category_map(uid)

# Group by day
by_day = defaultdict(float)
by_day_count = defaultdict(int)
for t in txs:
    if t.get("type", "depense") == "depense":
        day = int(t["date"].split("-")[2])
        by_day[day] += t["montant_total"]
        by_day_count[day] += 1

# Calculate daily budget & color scale
_, last_day = calendar.monthrange(yr, mo)
daily_budget = total_budget / last_day if total_budget > 0 else 0

# Build calendar grid
first_weekday, _ = calendar.monthrange(yr, mo)

# Header
header_html = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px;margin-bottom:4px">'
for d in JOURS_FR_SHORT:
    header_html += f'<div style="text-align:center;color:#94a3b8;font-size:0.72rem;font-weight:600;padding:4px">{d}</div>'
header_html += '</div>'
st.markdown(header_html, unsafe_allow_html=True)

# Calendar grid
grid_html = '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px">'

# Empty cells before first day
for _ in range(first_weekday):
    grid_html += '<div style="padding:0.4rem;border-radius:10px;min-height:60px"></div>'

for day in range(1, last_day + 1):
    spent = by_day.get(day, 0)
    count = by_day_count.get(day, 0)
    is_today = (yr == now.year and mo == now.month and day == now.day)

    # Color based on budget proportion
    if total_budget <= 0:
        # No budget → gray scale based on spending
        if spent == 0:
            bg = "rgba(15,15,26,0.4)"
            text_color = "#64748b"
        elif spent < 20:
            bg = "rgba(129,140,248,0.1)"
            text_color = "#818cf8"
        elif spent < 50:
            bg = "rgba(129,140,248,0.2)"
            text_color = "#818cf8"
        else:
            bg = "rgba(129,140,248,0.35)"
            text_color = "#a78bfa"
    else:
        ratio = spent / daily_budget if daily_budget > 0 else 0
        if spent == 0:
            bg = "rgba(52,211,153,0.08)"
            text_color = "#34d399"
        elif ratio <= 0.5:
            bg = "rgba(52,211,153,0.15)"
            text_color = "#34d399"
        elif ratio <= 0.8:
            bg = "rgba(52,211,153,0.25)"
            text_color = "#34d399"
        elif ratio <= 1.0:
            bg = "rgba(251,191,36,0.2)"
            text_color = "#fbbf24"
        elif ratio <= 1.5:
            bg = "rgba(248,113,113,0.2)"
            text_color = "#f87171"
        else:
            bg = "rgba(239,68,68,0.35)"
            text_color = "#ef4444"

    border = "border:2px solid #a78bfa;" if is_today else "border:1px solid rgba(255,255,255,0.04);"
    amount_html = f'<div style="font-size:0.68rem;color:{text_color};font-weight:600">{spent:.0f}€</div>' if spent > 0 else ""
    count_html = f'<div style="font-size:0.55rem;color:#64748b">{count} txn{"s" if count > 1 else ""}</div>' if count > 0 else ""

    grid_html += f'''<div style="background:{bg};{border}border-radius:10px;padding:0.35rem;min-height:60px;text-align:center;transition:all 0.2s">
        <div style="font-size:0.78rem;font-weight:{'700' if is_today else '500'};color:{'#a78bfa' if is_today else '#e2e8f0'}">{day}</div>
        {amount_html}
        {count_html}
    </div>'''

grid_html += '</div>'
st.markdown(grid_html, unsafe_allow_html=True)

# ─── Legend ───
st.markdown("---")
if total_budget > 0:
    st.markdown(f"**Budget quotidien :** {daily_budget:.0f}€/jour ({total_budget:.0f}€ total)")
    st.markdown("""<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:0.3rem">
        <span style="font-size:0.72rem"><span style="color:#34d399">🟢</span> Sous budget</span>
        <span style="font-size:0.72rem"><span style="color:#fbbf24">🟡</span> Proche du budget</span>
        <span style="font-size:0.72rem"><span style="color:#ef4444">🔴</span> Au dessus du budget</span>
    </div>""", unsafe_allow_html=True)
else:
    st.caption("💡 Définissez des budgets dans la page 💰 Budgets pour voir les couleurs proportionnelles.")

# ─── Monthly summary ───
total_dep = sum(by_day.values())
avg_daily = total_dep / max(len([d for d in by_day if by_day[d] > 0]), 1)
max_day = max(by_day.items(), key=lambda x: x[1]) if by_day else (0, 0)

st.markdown(f"""<div class="kpi-grid" style="margin-top:0.8rem">
    <div class="kpi"><div class="kpi-label">Total dépensé</div><div class="kpi-val red">{total_dep:.0f}€</div></div>
    <div class="kpi"><div class="kpi-label">Moyenne/jour</div><div class="kpi-val white">{avg_daily:.0f}€</div></div>
    <div class="kpi"><div class="kpi-label">Jours actifs</div><div class="kpi-val blue">{len([d for d in by_day if by_day[d] > 0])}</div></div>
    <div class="kpi"><div class="kpi-label">Jour le + cher</div><div class="kpi-val red">{max_day[0]} ({max_day[1]:.0f}€)</div></div>
</div>""", unsafe_allow_html=True)
