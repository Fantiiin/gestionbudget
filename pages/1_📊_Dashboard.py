import streamlit as st
from datetime import datetime, date
from collections import defaultdict

from database import (
    init_db, get_all_transactions, get_transactions_by_month, get_monthly_totals,
    delete_transaction, apply_recurring_for_month,
    get_category_map, get_category_names, get_friends,
    get_user_by_id, ensure_user_has_categories,
)
from auth import require_auth, get_current_user_id, get_current_user, logout
from styles import inject_css

st.set_page_config(page_title="Dashboard — Budget", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
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
        return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month]}"
    except (ValueError, IndexError):
        return ds


# ─── Top Bar ───
c_top1, c_top2 = st.columns([4, 1])
with c_top1:
    st.markdown(f"# {user['avatar']} Mon Budget")
with c_top2:
    if st.button("🚪", key="logout_btn", help="Déconnexion"):
        logout(); st.rerun()

# ─── Profile Selector ───
friends = get_friends(uid)
profile_map = {f"{user['avatar']} {user['display_name']} (moi)": uid}
for f in friends:
    profile_map[f"{f['avatar']} {f['display_name']}"] = f["id"]

viewing_uid = uid
viewing_readonly = False

if len(profile_map) > 1:
    sel = st.selectbox("👁️ Voir le profil de", list(profile_map.keys()), key="profile_sel")
    viewing_uid = profile_map[sel]
    viewing_readonly = (viewing_uid != uid)

view_cat_map = get_category_map(viewing_uid)
view_cat_names = get_category_names(viewing_uid)
now = datetime.now()
all_tx = get_all_transactions(viewing_uid)

# ─── Controls ───
c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
yrs = sorted(set(t["date"][:4] for t in all_tx if t.get("date") and len(t["date"]) >= 4)) or [str(now.year)]
with c1: yr = st.selectbox("Année", yrs, index=len(yrs) - 1)
with c2: mo = st.selectbox("Mois", range(1, 13), index=now.month - 1, format_func=lambda x: MOIS_FR[x].capitalize())
with c3: view = st.selectbox("Affichage", ["📋 Timeline", "📊 Tableau", "📦 Compact"])
with c4: filt = st.multiselect("Filtre", view_cat_names, default=[], placeholder="Toutes")

# Apply recurring
if not viewing_readonly:
    applied = apply_recurring_for_month(uid, int(yr), mo)
    if applied > 0:
        st.toast(f"🔁 {applied} récurrent(s) ajouté(s)")

txs = get_transactions_by_month(viewing_uid, int(yr), mo)
if filt:
    txs = [t for t in txs if t["categorie"] in filt]

# ─── KPIs ───
dep = sum(t["montant_total"] for t in txs if t.get("type", "depense") == "depense")
rev = sum(t["montant_total"] for t in txs if t.get("type") == "revenu")
bal = rev - dep
bc = "green" if bal >= 0 else "red"
bs = "+" if bal >= 0 else ""

if viewing_readonly:
    vu = get_user_by_id(viewing_uid)
    st.markdown(f'<div class="glass" style="padding:0.5rem 1rem;margin-bottom:0.6rem"><span style="color:#818cf8">👁️ Vue de {vu["display_name"]} — lecture seule</span></div>', unsafe_allow_html=True)

st.markdown(f"""<div class="kpi-grid">
    <div class="kpi"><div class="kpi-label">📉 Dépenses</div><div class="kpi-val red">−{dep:.2f}€</div></div>
    <div class="kpi"><div class="kpi-label">📈 Revenus</div><div class="kpi-val green">+{rev:.2f}€</div></div>
    <div class="kpi"><div class="kpi-label">⚖️ Balance</div><div class="kpi-val {bc}">{bs}{bal:.2f}€</div></div>
    <div class="kpi"><div class="kpi-label">🧾 Transactions</div><div class="kpi-val white">{len(txs)}</div></div>
</div>""", unsafe_allow_html=True)

if not txs:
    st.info("Aucune transaction. Allez dans ➕ **Ajouter** pour commencer.")
    st.stop()

# ─── Layout ───
col_side, col_main = st.columns([1, 2.5])

with col_side:
    st.markdown("#### 📊 Répartition")
    ct = defaultdict(float)
    for t in txs:
        if t.get("type", "depense") == "depense":
            ct[t["categorie"]] += t["montant_total"]
    if ct:
        mx = max(ct.values())
        for cn, ca in sorted(ct.items(), key=lambda x: x[1], reverse=True):
            pct = (ca / dep * 100) if dep > 0 else 0
            bp = (ca / mx * 100) if mx > 0 else 0
            ci = view_cat_map.get(cn, {})
            ic = ci.get("icon", "📁")
            co = ci.get("color", "#a78bfa")
            st.markdown(f"""<div class="cat-row">
                <div class="cat-header"><span class="cat-name">{ic} {cn}</span><span class="cat-amount">{ca:.2f}€ ({pct:.0f}%)</span></div>
                <div class="cat-track"><div class="cat-fill" style="width:{bp:.0f}%;background:{co}"></div></div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.markdown("#### 📈 Évolution")
    monthly = get_monthly_totals(viewing_uid)
    for m in (monthly[-6:] if monthly else []):
        md, mr = m["depenses"] or 0, m["revenus"] or 0
        mb = mr - md
        mc = "green" if mb >= 0 else "red"
        ms = "+" if mb >= 0 else ""
        st.markdown(f"""<div class="glass" style="padding:0.4rem 0.7rem;margin-bottom:0.25rem">
            <div style="font-size:0.78rem;font-weight:600;color:#e2e8f0">{m['mois']}</div>
            <div style="font-size:0.72rem"><span class="red">−{md:.0f}€</span> / <span class="green">+{mr:.0f}€</span> → <span class="{mc}">{ms}{mb:.0f}€</span></div>
        </div>""", unsafe_allow_html=True)

with col_main:
    def added_by_label(t):
        ab = t.get("added_by")
        if ab and ab != viewing_uid:
            u = get_user_by_id(ab)
            if u:
                return f'<div class="txn-added">{u.get("avatar","👤")} ajouté par {u["display_name"]}</div>'
        return ""

    # ═══ TIMELINE ═══
    if view == "📋 Timeline":
        st.markdown("#### 📋 Historique")
        days = defaultdict(list)
        for t in txs:
            days[t["date"]].append(t)
        for dd in sorted(days.keys(), reverse=True):
            dl = days[dd]
            dd_dep = sum(t["montant_total"] for t in dl if t.get("type", "depense") == "depense")
            dd_rev = sum(t["montant_total"] for t in dl if t.get("type") == "revenu")
            pts = []
            if dd_dep > 0: pts.append(f'<span class="red">−{dd_dep:.2f}€</span>')
            if dd_rev > 0: pts.append(f'<span class="green">+{dd_rev:.2f}€</span>')
            st.markdown(f'<div class="day-header"><span>{format_date_fr(dd)}</span><span class="day-total">{" ".join(pts)}</span></div>', unsafe_allow_html=True)
            for t in dl:
                ci = view_cat_map.get(t["categorie"], {})
                ic = ci.get("icon", "📁")
                ir = t.get("type") == "revenu"
                ac = "green" if ir else "red"
                sg = "+" if ir else "−"
                abl = added_by_label(t)
                tc, dc = st.columns([6, 1])
                with tc:
                    st.markdown(f"""<div class="txn"><div class="txn-row"><div class="txn-left">
                        <span class="txn-icon">{ic}</span>
                        <div><div class="txn-ens">{t['enseigne']}</div><div class="txn-cat">{t['categorie']}</div>{abl}</div>
                        </div><span class="txn-amt {ac}">{sg}{t['montant_total']:.2f}€</span></div></div>""", unsafe_allow_html=True)
                with dc:
                    if not viewing_readonly:
                        if st.button("🗑️", key=f"d{t['id']}"):
                            delete_transaction(t["id"]); st.rerun()
            st.markdown("")

    # ═══ TABLEAU ═══
    elif view == "📊 Tableau":
        st.markdown("#### 📊 Tableau")
        td = []
        for t in txs:
            ci = view_cat_map.get(t["categorie"], {})
            ir = t.get("type") == "revenu"
            sg = "+" if ir else "−"
            ab = ""
            if t.get("added_by") and t["added_by"] != viewing_uid:
                u = get_user_by_id(t["added_by"])
                if u: ab = f" (par {u['display_name']})"
            td.append({
                "Date": t["date"], "Enseigne": t["enseigne"] + ab,
                "Montant": f"{sg}{t['montant_total']:.2f}€",
                "Catégorie": f"{ci.get('icon','')} {t['categorie']}",
                "Type": "Revenu" if ir else "Dépense"
            })
        sel = st.dataframe(td, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        sr = sel.selection.rows if sel.selection else []
        if sr and not viewing_readonly:
            stx = [txs[i] for i in sr]
            st.markdown(f"**{len(sr)} sélectionnée(s)** — {sum(t['montant_total'] for t in stx):.2f}€")
            if st.button(f"🗑️ Supprimer ({len(sr)})", type="secondary"):
                for t in stx: delete_transaction(t["id"])
                st.success("✅"); st.rerun()

    # ═══ COMPACT ═══
    elif view == "📦 Compact":
        st.markdown("#### 📦 Compact")
        for t in txs:
            ci = view_cat_map.get(t["categorie"], {})
            ic = ci.get("icon", "📁")
            ir = t.get("type") == "revenu"
            sg = "+" if ir else "−"
            co = "#34d399" if ir else "#f87171"
            c1, c2, c3, c4, c5 = st.columns([0.4, 2.5, 1.5, 1.2, 0.4])
            with c1: st.markdown(f"<span style='font-size:1rem'>{ic}</span>", unsafe_allow_html=True)
            with c2: st.markdown(f"**{t['enseigne']}**")
            with c3: st.caption(format_date_fr(t["date"]))
            with c4: st.markdown(f"<span style='color:{co};font-weight:600'>{sg}{t['montant_total']:.2f}€</span>", unsafe_allow_html=True)
            with c5:
                if not viewing_readonly:
                    if st.button("✕", key=f"cd{t['id']}"): delete_transaction(t["id"]); st.rerun()
