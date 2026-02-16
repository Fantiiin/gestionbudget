import streamlit as st
from datetime import datetime, date
from collections import defaultdict

from database import (
    init_db, get_all_transactions, get_transactions_by_month,
    get_transactions_by_range, get_monthly_totals,
    delete_transaction, apply_recurring_for_month,
    get_category_map, get_category_names, get_friends,
    get_user_by_id, ensure_user_has_categories,
    get_budgets, export_transactions_csv, update_transaction,
    get_transaction_by_id, duplicate_transaction, get_smart_budget_info,
    get_unique_enseignes, update_user_preference,
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


# ─── Undo delete logic ───
if "undo_txn" in st.session_state:
    undo = st.session_state["undo_txn"]
    c_undo1, c_undo2 = st.columns([4, 1])
    with c_undo1:
        st.warning(f"🗑️ Transaction « {undo['enseigne']} » supprimée")
    with c_undo2:
        if st.button("↩️ Annuler", key="undo_btn"):
            from database import insert_transaction
            insert_transaction(undo["user_id"], undo["date"], undo["enseigne"],
                               undo["montant_total"], undo["categorie"], "", [],
                               undo.get("type", "depense"), added_by=undo.get("added_by"))
            del st.session_state["undo_txn"]
            st.success("↩️ Restaurée"); st.rerun()
    # Auto-clear after one render
    if "undo_shown" in st.session_state:
        del st.session_state["undo_txn"]
        del st.session_state["undo_shown"]
    else:
        st.session_state["undo_shown"] = True

# ─── Top Bar ───
c_top1, c_top2, c_top3 = st.columns([3.5, 0.5, 0.5])
with c_top1:
    st.markdown(f"# {user['avatar']} Mon Budget")
with c_top2:
    current_theme = user.get("theme", "dark")
    theme_icon = "☀️" if current_theme == "dark" else "🌙"
    if st.button(theme_icon, key="theme_btn", help="Changer de thème"):
        new_theme = "light" if current_theme == "dark" else "dark"
        update_user_preference(uid, "theme", new_theme)
        st.rerun()
with c_top3:
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
PERIODES = ["Mois", "Trimestre", "Semestre", "Année", "Tout"]
c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 1.5])
yrs = sorted(set(t["date"][:4] for t in all_tx if t.get("date") and len(t["date"]) >= 4)) or [str(now.year)]
with c1: yr = st.selectbox("Année", yrs, index=len(yrs) - 1)
with c2: mo = st.selectbox("Mois", range(1, 13), index=now.month - 1, format_func=lambda x: MOIS_FR[x].capitalize())
with c3: periode = st.selectbox("Période", PERIODES, index=0)
with c4: view = st.selectbox("Affichage", ["📋 Timeline", "📊 Tableau", "📦 Compact"])
with c5: filt = st.multiselect("Filtre", view_cat_names, default=[], placeholder="Toutes")

# Apply recurring
if not viewing_readonly:
    applied = apply_recurring_for_month(uid, int(yr), mo)
    if applied > 0:
        st.toast(f"🔁 {applied} récurrent(s) ajouté(s)")

# Get transactions based on period
if periode == "Mois":
    txs = get_transactions_by_month(viewing_uid, int(yr), mo)
elif periode == "Trimestre":
    q_start = ((mo - 1) // 3) * 3 + 1
    d_from = f"{yr}-{q_start:02d}-01"
    q_end_m = q_start + 2
    import calendar
    _, ld = calendar.monthrange(int(yr), q_end_m)
    d_to = f"{yr}-{q_end_m:02d}-{ld}"
    txs = get_transactions_by_range(viewing_uid, d_from, d_to)
elif periode == "Semestre":
    s = 1 if mo <= 6 else 7
    d_from = f"{yr}-{s:02d}-01"
    e = 6 if s == 1 else 12
    import calendar
    _, ld = calendar.monthrange(int(yr), e)
    d_to = f"{yr}-{e:02d}-{ld}"
    txs = get_transactions_by_range(viewing_uid, d_from, d_to)
elif periode == "Année":
    txs = get_transactions_by_range(viewing_uid, f"{yr}-01-01", f"{yr}-12-31")
else:
    txs = all_tx

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

# ─── Smart Budget Card ───
if not viewing_readonly and periode == "Mois":
    smart = get_smart_budget_info(uid, int(yr), mo)
    if smart["has_budget"]:
        sc = {"over": "#ef4444", "behind": "#fbbf24", "on_track": "#34d399", "ahead": "#818cf8"}.get(smart["status"], "#94a3b8")
        pct = min((smart["spent"] / smart["total_budget"] * 100), 100) if smart["total_budget"] > 0 else 0
        st.markdown(f"""<div class="glass" style="padding:0.7rem 1rem;margin-bottom:0.8rem;border-left:3px solid {sc}">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div style="font-weight:700;color:{sc};font-size:0.9rem">🔥 {smart['message']}</div>
                    <div style="color:#94a3b8;font-size:0.72rem;margin-top:2px">
                        Jour {smart['days_elapsed']} · {smart['spent']:.0f}€/{smart['total_budget']:.0f}€ · Aujourd'hui: {smart['spent_today']:.0f}€
                    </div>
                </div>
                <div style="font-size:1.8rem;font-weight:800;color:{sc}">{smart['daily_allowance']:.0f}€<span style="font-size:0.7rem;font-weight:400">/jour</span></div>
            </div>
            <div class="cat-track" style="height:6px;margin-top:6px"><div class="cat-fill" style="width:{pct:.0f}%;background:{sc}"></div></div>
        </div>""", unsafe_allow_html=True)

# ─── Export ───
if not viewing_readonly:
    with st.expander("📤 Exporter"):
        csv_data = export_transactions_csv(uid, int(yr) if periode == "Mois" else None, mo if periode == "Mois" else None)
        st.download_button("📥 Télécharger CSV", csv_data, file_name=f"budget_{yr}_{mo:02d}.csv", mime="text/csv", use_container_width=True)

if not txs:
    st.info("Aucune transaction pour cette période.")
    st.stop()

# ─── Layout ───
col_side, col_main = st.columns([1, 2.5])

with col_side:
    st.markdown("#### 📊 Répartition")
    ct = defaultdict(float)
    for t in txs:
        if t.get("type", "depense") == "depense":
            ct[t["categorie"]] += t["montant_total"]

    budgets = get_budgets(viewing_uid)

    if ct:
        mx = max(ct.values())
        for cn, ca in sorted(ct.items(), key=lambda x: x[1], reverse=True):
            pct = (ca / dep * 100) if dep > 0 else 0
            ci = view_cat_map.get(cn, {})
            ic = ci.get("icon", "📁")
            co = ci.get("color", "#a78bfa")

            budget_max = budgets.get(cn)
            if budget_max and budget_max > 0:
                bp = min((ca / budget_max * 100), 100)
                over = ca > budget_max
                bar_color = "#ef4444" if over else co
                budget_label = f' / {budget_max:.0f}€ {"⚠️" if over else "✓"}'
            else:
                bp = (ca / mx * 100) if mx > 0 else 0
                bar_color = co
                budget_label = ""

            st.markdown(f"""<div class="cat-row">
                <div class="cat-header"><span class="cat-name">{ic} {cn}</span><span class="cat-amount">{ca:.2f}€{budget_label} ({pct:.0f}%)</span></div>
                <div class="cat-track"><div class="cat-fill" style="width:{bp:.0f}%;background:{bar_color}"></div></div>
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

    # ─── Edit dialog ───
    if "edit_txn_id" in st.session_state:
        txn = get_transaction_by_id(st.session_state["edit_txn_id"])
        if txn:
            st.markdown("#### ✏️ Modifier la transaction")
            with st.container():
                ec1, ec2 = st.columns(2)
                with ec1:
                    enseignes = get_unique_enseignes(uid)
                    e_ens = st.selectbox("Enseigne", enseignes + [txn["enseigne"]], index=len(enseignes) if txn["enseigne"] not in enseignes else enseignes.index(txn["enseigne"]), key="edit_ens")
                    e_date = st.date_input("Date", value=datetime.strptime(txn["date"], "%Y-%m-%d").date(), key="edit_date")
                    e_tags = st.text_input("Tags", value=txn.get("tags", ""), key="edit_tags", placeholder="#vacances, #pro")
                with ec2:
                    e_mt = st.number_input("Montant", value=txn["montant_total"], min_value=0.0, step=0.01, format="%.2f", key="edit_mt")
                    ci = view_cat_names.index(txn["categorie"]) if txn["categorie"] in view_cat_names else 0
                    e_cat = st.selectbox("Catégorie", view_cat_names, index=ci, key="edit_cat")
                    e_type = st.selectbox("Type", ["depense", "revenu"], index=0 if txn.get("type") == "depense" else 1, key="edit_type")
                e_comment = st.text_input("💬 Note", value=txn.get("comment", ""), key="edit_comment", placeholder="anniversaire 🎂, arnaque 😤…")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                        from database import get_connection
                        conn = get_connection()
                        conn.execute(
                            "UPDATE transactions SET date=?, enseigne=?, montant_total=?, categorie=?, type=?, tags=?, comment=? WHERE id=?",
                            (e_date.strftime("%Y-%m-%d"), e_ens, e_mt, e_cat, e_type, e_tags, e_comment, txn["id"])
                        )
                        conn.commit(); conn.close()
                        del st.session_state["edit_txn_id"]
                        st.success("✅ Modifiée"); st.rerun()
                with bc2:
                    if st.button("❌ Annuler", use_container_width=True):
                        del st.session_state["edit_txn_id"]
                        st.rerun()
            st.markdown("---")

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
                tag_s = ""
                if t.get("tags"):
                    tag_s = f'<span style="color:#818cf8;font-size:0.6rem;margin-left:0.3rem">{t["tags"]}</span>'
                comment_s = ""
                if t.get("comment"):
                    comment_s = f'<div style="color:#94a3b8;font-size:0.62rem;font-style:italic">💬 {t["comment"]}</div>'
                tc, dc, ec, fc = st.columns([5, 0.4, 0.4, 0.4])
                with tc:
                    st.markdown(f"""<div class="txn"><div class="txn-row"><div class="txn-left">
                        <span class="txn-icon">{ic}</span>
                        <div><div class="txn-ens">{t['enseigne']}{tag_s}</div><div class="txn-cat">{t['categorie']}</div>{comment_s}{abl}</div>
                        </div><span class="txn-amt {ac}">{sg}{t['montant_total']:.2f}€</span></div></div>""", unsafe_allow_html=True)
                if not viewing_readonly:
                    with dc:
                        if st.button("📋", key=f"dup{t['id']}", help="Dupliquer"):
                            duplicate_transaction(t["id"])
                            st.toast("📋 Dupliquée !"); st.rerun()
                    with ec:
                        if st.button("✏️", key=f"e{t['id']}"):
                            st.session_state["edit_txn_id"] = t["id"]; st.rerun()
                    with fc:
                        if st.button("🗑️", key=f"d{t['id']}"):
                            # Undo: save to session before deleting
                            st.session_state["undo_txn"] = {
                                "user_id": t.get("user_id", uid), "date": t["date"],
                                "enseigne": t["enseigne"], "montant_total": t["montant_total"],
                                "categorie": t["categorie"], "type": t.get("type", "depense"),
                                "added_by": t.get("added_by"),
                            }
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
            td.append({
                "Date": t["date"], "Enseigne": t["enseigne"],
                "Montant": f"{sg}{t['montant_total']:.2f}€",
                "Catégorie": f"{ci.get('icon','')} {t['categorie']}",
                "Type": "Revenu" if ir else "Dépense",
                "Tags": t.get("tags", ""),
                "Note": t.get("comment", ""),
            })
        sel = st.dataframe(td, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")
        sr = sel.selection.rows if sel.selection else []
        if sr and not viewing_readonly:
            stx = [txs[i] for i in sr]
            st.markdown(f"**{len(sr)} sélectionnée(s)** — {sum(t['montant_total'] for t in stx):.2f}€")
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button(f"🗑️ Supprimer ({len(sr)})", type="secondary"):
                    for t in stx: delete_transaction(t["id"])
                    st.rerun()
            with bc2:
                if len(sr) == 1:
                    if st.button("✏️ Modifier"):
                        st.session_state["edit_txn_id"] = stx[0]["id"]; st.rerun()

    # ═══ COMPACT ═══
    elif view == "📦 Compact":
        st.markdown("#### 📦 Compact")
        for t in txs:
            ci = view_cat_map.get(t["categorie"], {})
            ic = ci.get("icon", "📁")
            ir = t.get("type") == "revenu"
            sg = "+" if ir else "−"
            co = "#34d399" if ir else "#f87171"
            c1, c2, c3, c4, c5, c6, c7 = st.columns([0.3, 2, 1.2, 1, 0.3, 0.3, 0.3])
            with c1: st.markdown(f"<span style='font-size:1rem'>{ic}</span>", unsafe_allow_html=True)
            with c2: st.markdown(f"**{t['enseigne']}**")
            with c3: st.caption(format_date_fr(t["date"]))
            with c4: st.markdown(f"<span style='color:{co};font-weight:600'>{sg}{t['montant_total']:.2f}€</span>", unsafe_allow_html=True)
            if not viewing_readonly:
                with c5:
                    if st.button("📋", key=f"cdup{t['id']}"): duplicate_transaction(t["id"]); st.rerun()
                with c6:
                    if st.button("✏️", key=f"ce{t['id']}"): st.session_state["edit_txn_id"] = t["id"]; st.rerun()
                with c7:
                    if st.button("✕", key=f"cd{t['id']}"):
                        st.session_state["undo_txn"] = {
                            "user_id": t.get("user_id", uid), "date": t["date"],
                            "enseigne": t["enseigne"], "montant_total": t["montant_total"],
                            "categorie": t["categorie"], "type": t.get("type", "depense"),
                            "added_by": t.get("added_by"),
                        }
                        delete_transaction(t["id"]); st.rerun()
