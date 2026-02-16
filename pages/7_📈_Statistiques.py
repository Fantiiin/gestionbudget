import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import defaultdict

from database import (
    init_db, get_all_transactions, get_monthly_totals,
    get_category_map, get_category_names, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Statistiques — Budget", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

MOIS_FR = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

st.markdown("# 📈 Statistiques")

all_tx = get_all_transactions(uid)
cat_map = get_category_map(uid)

if not all_tx:
    st.info("Pas encore de données. Ajoutez des transactions pour voir vos statistiques.")
    st.stop()

dep_tx = [t for t in all_tx if t.get("type", "depense") == "depense"]

# ─── Period selector ───
yrs = sorted(set(t["date"][:4] for t in all_tx))
sel_yr = st.selectbox("Année", ["Toutes"] + yrs, index=0)

if sel_yr != "Toutes":
    dep_tx = [t for t in dep_tx if t["date"][:4] == sel_yr]

# ═══ Monthly evolution chart ═══
st.markdown("#### 📊 Évolution mensuelle")
monthly = get_monthly_totals(uid)
if sel_yr != "Toutes":
    monthly = [m for m in monthly if m["mois"][:4] == sel_yr]

if monthly:
    months = [m["mois"] for m in monthly]
    deps = [m["depenses"] or 0 for m in monthly]
    revs = [m["revenus"] or 0 for m in monthly]
    bals = [r - d for r, d in zip(revs, deps)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=deps, name="Dépenses", marker_color="#f87171"))
    fig.add_trace(go.Bar(x=months, y=revs, name="Revenus", marker_color="#34d399"))
    fig.add_trace(go.Scatter(x=months, y=bals, name="Balance", line=dict(color="#818cf8", width=3), mode="lines+markers"))
    fig.update_layout(
        barmode="group", template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#e2e8f0"),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0), height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

# ═══ Category breakdown ═══
c1, c2 = st.columns(2)

with c1:
    st.markdown("#### 🎯 Top catégories")
    cat_totals = defaultdict(float)
    for t in dep_tx:
        cat_totals[t["categorie"]] += t["montant_total"]

    if cat_totals:
        cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        labels = [c[0] for c in cats]
        values = [c[1] for c in cats]
        colors = [cat_map.get(c, {}).get("color", "#a78bfa") for c in labels]

        fig2 = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.4,
            marker=dict(colors=colors),
            textinfo="label+percent", textposition="outside",
        )])
        fig2.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e2e8f0"),
            showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=350,
        )
        st.plotly_chart(fig2, use_container_width=True)

with c2:
    st.markdown("#### 📅 Jour le plus dépensier")
    day_totals = defaultdict(float)
    day_counts = defaultdict(int)
    for t in dep_tx:
        try:
            d = datetime.strptime(t["date"], "%Y-%m-%d")
            wd = d.weekday()
            day_totals[wd] += t["montant_total"]
            day_counts[wd] += 1
        except ValueError:
            pass

    if day_totals:
        days = list(range(7))
        avgs = [day_totals.get(d, 0) / max(day_counts.get(d, 1), 1) for d in days]
        totals = [day_totals.get(d, 0) for d in days]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=[JOURS_FR[d] for d in days], y=totals,
            name="Total", marker_color="#a78bfa",
        ))
        fig3.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#e2e8f0"),
            margin=dict(l=0, r=0, t=10, b=0), height=350,
        )
        st.plotly_chart(fig3, use_container_width=True)

# ═══ Category evolution over time ═══
st.markdown("#### 📈 Évolution par catégorie")
cat_monthly = defaultdict(lambda: defaultdict(float))
for t in dep_tx:
    m = t["date"][:7]
    cat_monthly[t["categorie"]][m] = cat_monthly[t["categorie"]].get(m, 0) + t["montant_total"]

if cat_monthly:
    all_months = sorted(set(m for cat in cat_monthly.values() for m in cat))
    fig4 = go.Figure()
    for cat_name in sorted(cat_monthly.keys()):
        vals = [cat_monthly[cat_name].get(m, 0) for m in all_months]
        color = cat_map.get(cat_name, {}).get("color", "#a78bfa")
        fig4.add_trace(go.Scatter(
            x=all_months, y=vals, name=cat_name,
            mode="lines+markers", line=dict(color=color, width=2),
        ))
    fig4.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#e2e8f0"),
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0), height=350,
    )
    st.plotly_chart(fig4, use_container_width=True)

# ═══ Top enseignes ═══
st.markdown("#### 🏪 Top enseignes")
ens_totals = defaultdict(float)
ens_counts = defaultdict(int)
for t in dep_tx:
    ens_totals[t["enseigne"]] += t["montant_total"]
    ens_counts[t["enseigne"]] += 1

if ens_totals:
    top = sorted(ens_totals.items(), key=lambda x: x[1], reverse=True)[:15]
    for i, (ens, total) in enumerate(top, 1):
        count = ens_counts[ens]
        avg = total / count
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
        st.markdown(f"""<div class="glass" style="padding:0.5rem 0.8rem;margin-bottom:0.2rem">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div><span style="font-size:0.85rem;margin-right:0.4rem">{medal}</span>
                <span style="font-weight:600;color:#e2e8f0">{ens}</span>
                <span style="color:#64748b;font-size:0.72rem;margin-left:0.3rem">{count}x · moy. {avg:.1f}€</span></div>
                <span class="red" style="font-weight:700">{total:.2f}€</span>
            </div>
        </div>""", unsafe_allow_html=True)
