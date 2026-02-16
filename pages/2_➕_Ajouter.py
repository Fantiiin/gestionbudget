import streamlit as st
from datetime import date, timedelta
import re

from database import (
    init_db, insert_transaction, get_category_names, get_all_categories,
    get_friends, get_user_by_id, ensure_user_has_categories, create_debt,
)
from analyzer import analyze_receipts
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Ajouter — Budget", page_icon="➕", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()
ensure_user_has_categories(uid)

JOURS_SEMAINE = {"lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4, "samedi": 5, "dimanche": 6}


def parse_date(raw: str) -> str:
    if not raw or not raw.strip(): return date.today().strftime("%Y-%m-%d")
    raw = raw.strip().lower()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw): return raw
    if re.match(r"^\d{2}/\d{2}/\d{4}$", raw):
        d, m, y = raw.split("/"); return f"{y}-{m}-{d}"
    if re.match(r"^\d{2}/\d{2}$", raw):
        d, m = raw.split("/"); return f"{date.today().year}-{m}-{d}"
    today = date.today()
    if raw in ("aujourd'hui", "aujourd hui", "today"): return today.strftime("%Y-%m-%d")
    if raw in ("hier", "yesterday"): return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    if raw in ("avant-hier", "avant hier"): return (today - timedelta(days=2)).strftime("%Y-%m-%d")
    for jour, wn in JOURS_SEMAINE.items():
        if raw == jour:
            da = (today.weekday() - wn) % 7
            if da == 0: da = 7
            return (today - timedelta(days=da)).strftime("%Y-%m-%d")
    return raw


def get_subcategories(uid, cat_name):
    cats = get_all_categories(uid)
    for c in cats:
        if c["nom"] == cat_name and c.get("sous_categories"):
            return [s.strip() for s in c["sous_categories"].split(",") if s.strip()]
    return []


# ─── Target users ───
friends = get_friends(uid)
target_map = {f"{user['avatar']} {user['display_name']} (moi)": uid}
for f in friends:
    target_map[f"{f['avatar']} {f['display_name']}"] = f["id"]

cat_names = get_category_names(uid)

st.markdown(f"# ➕ Ajouter")

tab_ia, tab_man, tab_rev, tab_split = st.tabs(["🤖 Analyse IA", "✍️ Dépense", "💰 Revenu", "✂️ Partagée"])

# ═══ IA TAB ═══
with tab_ia:
    st.markdown("#### 📸 Scanner un ticket")
    uploaded = st.file_uploader("Glissez vos photos de tickets", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="ia_upload")

    if uploaded:
        cols = st.columns(min(len(uploaded), 4))
        for i, f in enumerate(uploaded):
            with cols[i % 4]:
                st.image(f, caption=f.name, use_container_width=True)

        if st.button("🔍 Analyser avec l'IA", type="primary", use_container_width=True):
            with st.spinner("OCR + analyse IA en cours..."):
                try:
                    images = [(f.getvalue(), f.type or "image/jpeg") for f in uploaded]
                    txns = analyze_receipts(images, uid)
                    st.session_state["ai_txns"] = txns
                    st.success(f"✅ {len(txns)} transaction(s) détectée(s)")
                except Exception as e:
                    st.error(str(e))

    if "ai_txns" in st.session_state:
        txns = st.session_state["ai_txns"]
        st.markdown("---")
        st.markdown("#### ✏️ Vérifier et ajuster")

        if len(target_map) > 1:
            ai_target = st.selectbox("Ajouter au profil de", list(target_map.keys()), key="ai_target")
            ai_target_uid = target_map[ai_target]
        else:
            ai_target_uid = uid

        edited = []
        for i, txn in enumerate(txns):
            include = st.toggle(f"✅ Inclure", value=True, key=f"ai_inc_{i}")
            if include:
                c1, c2 = st.columns(2)
                with c1:
                    ens = st.text_input("Enseigne", value=txn["enseigne"], key=f"ai_e{i}")
                with c2:
                    mt = st.number_input("Montant €", value=txn["montant"], min_value=0.0, step=0.01, format="%.2f", key=f"ai_m{i}")
                c3, c4, c5 = st.columns(3)
                with c3:
                    dt = st.text_input("Date", value=txn["date"], key=f"ai_d{i}")
                with c4:
                    ci = cat_names.index(txn["categorie"]) if txn["categorie"] in cat_names else 0
                    cat = st.selectbox("Catégorie", cat_names, index=ci, key=f"ai_c{i}")
                with c5:
                    tags = st.text_input("Tags", value="", key=f"ai_tags{i}", placeholder="#vacances")
                edited.append({"enseigne": ens, "date": parse_date(dt), "montant": mt, "categorie": cat, "type": "depense", "tags": tags})
            st.markdown("---")

        if st.button(f"💾 Enregistrer {len(edited)} transaction(s)", type="primary", use_container_width=True, disabled=not edited):
            for t in edited:
                added_by = uid if ai_target_uid != uid else None
                insert_transaction(ai_target_uid, t["date"], t["enseigne"], t["montant"],
                                   t["categorie"], "", [], t["type"], added_by=added_by)
            st.session_state.pop("ai_txns", None)
            st.success(f"✅ {len(edited)} transaction(s) enregistrée(s)")
            st.balloons()

# ═══ MANUEL TAB ═══
with tab_man:
    st.markdown("#### ✍️ Ajouter une dépense")

    me = st.text_input("Enseigne", key="man_enseigne", placeholder="Ex: Carrefour")
    c1, c2 = st.columns(2)
    with c1:
        md_raw = st.text_input("Date", value=date.today().strftime("%Y-%m-%d"), key="man_date",
                                help="Formats: YYYY-MM-DD, DD/MM, hier, lundi…")
        md = parse_date(md_raw)
        if md_raw.strip().lower() != md:
            st.caption(f"📅 → {md}")
    with c2:
        mm = st.number_input("Montant €", value=0.0, min_value=0.0, step=0.01, format="%.2f", key="man_montant")

    c3, c4 = st.columns(2)
    with c3:
        mc = st.selectbox("Catégorie", cat_names, key="man_cat")
    with c4:
        subcats = get_subcategories(uid, mc)
        if subcats:
            msc = st.selectbox("Sous-catégorie", [""] + subcats, key="man_subcat")
        else:
            msc = ""

    c5, c6 = st.columns(2)
    with c5:
        man_tags = st.text_input("Tags", key="man_tags", placeholder="#vacances, #pro…")
    with c6:
        if len(target_map) > 1:
            man_target = st.selectbox("Pour", list(target_map.keys()), key="man_target")
            man_target_uid = target_map[man_target]
        else:
            man_target_uid = uid
            st.caption(f"Pour : {user['avatar']} {user['display_name']}")

    if st.button("💾 Enregistrer la dépense", type="primary", use_container_width=True, key="man_save"):
        if not me or mm <= 0:
            st.warning("⚠️ Remplissez l'enseigne et le montant.")
        else:
            added_by = uid if man_target_uid != uid else None
            insert_transaction(man_target_uid, md, me, mm, mc, "", [], "depense", added_by=added_by)
            st.success("✅ Dépense enregistrée")
            st.balloons()

# ═══ REVENU TAB ═══
with tab_rev:
    st.markdown("#### 💰 Ajouter un revenu")

    re_ = st.text_input("Source", key="rev_source", placeholder="Salaire, freelance…")
    c1, c2 = st.columns(2)
    with c1:
        rd_raw = st.text_input("Date", value=date.today().strftime("%Y-%m-%d"), key="rev_date")
        rd = parse_date(rd_raw)
    with c2:
        rm = st.number_input("Montant €", value=0.0, min_value=0.0, step=0.01, format="%.2f", key="rev_montant")

    if st.button("💾 Enregistrer le revenu", type="primary", use_container_width=True, key="rev_save"):
        if not re_ or rm <= 0:
            st.warning("⚠️ Remplissez la source et le montant.")
        else:
            insert_transaction(uid, rd, re_, rm, "Revenu", "", [], "revenu")
            st.success("✅ Revenu enregistré")
            st.balloons()

# ═══ SPLIT TAB ═══
with tab_split:
    st.markdown("#### ✂️ Dépense partagée")
    st.caption("Ajoutez une dépense et partagez-la avec un(e) ami(e). La dette est créée automatiquement.")

    if not friends:
        st.info("Ajoutez d'abord un(e) ami(e) dans la page 👥 Social.")
    else:
        sp_ens = st.text_input("Enseigne", key="sp_ens", placeholder="Restaurant, courses…")
        c1, c2 = st.columns(2)
        with c1:
            sp_date_raw = st.text_input("Date", value=date.today().strftime("%Y-%m-%d"), key="sp_date")
            sp_date = parse_date(sp_date_raw)
        with c2:
            sp_total = st.number_input("Montant total €", value=0.0, min_value=0.0, step=0.01, format="%.2f", key="sp_total")

        c3, c4 = st.columns(2)
        with c3:
            sp_cat = st.selectbox("Catégorie", cat_names, key="sp_cat")
        with c4:
            friend_map = {f"{f['avatar']} {f['display_name']}": f["id"] for f in friends}
            sp_friend_label = st.selectbox("Partager avec", list(friend_map.keys()), key="sp_friend")
            sp_friend_id = friend_map[sp_friend_label]

        c5, c6 = st.columns(2)
        with c5:
            sp_split = st.selectbox("Répartition", ["50/50", "Je paie tout", "L'autre paie tout", "Personnalisé"], key="sp_split")
        with c6:
            if sp_split == "Personnalisé":
                sp_my_share = st.number_input("Ma part €", value=sp_total / 2, min_value=0.0, step=0.01, format="%.2f", key="sp_my")
            elif sp_split == "50/50":
                sp_my_share = sp_total / 2
            elif sp_split == "Je paie tout":
                sp_my_share = sp_total
            else:
                sp_my_share = 0.0

        sp_other_share = sp_total - sp_my_share

        if sp_total > 0:
            st.markdown(f"""<div class="glass" style="padding:0.6rem 1rem;margin:0.5rem 0">
                <div style="display:flex;justify-content:space-between">
                    <span style="color:#e2e8f0">{user['avatar']} Moi : <b>{sp_my_share:.2f}€</b></span>
                    <span style="color:#e2e8f0">{sp_friend_label} : <b>{sp_other_share:.2f}€</b></span>
                </div>
            </div>""", unsafe_allow_html=True)

        if st.button("💾 Enregistrer + créer la dette", type="primary", use_container_width=True, key="sp_save"):
            if not sp_ens or sp_total <= 0:
                st.warning("⚠️ Remplissez l'enseigne et le montant.")
            else:
                # Create my transaction
                tid = insert_transaction(uid, sp_date, sp_ens, sp_my_share, sp_cat, "", [], "depense")

                # Create debt: other person owes their share
                if sp_split == "Je paie tout":
                    create_debt(sp_friend_id, uid, sp_other_share, f"Part de {sp_ens}", tid)
                elif sp_split == "L'autre paie tout":
                    create_debt(uid, sp_friend_id, sp_my_share, f"Part de {sp_ens}", tid)
                elif sp_other_share > 0 and sp_split in ("50/50", "Personnalisé"):
                    create_debt(sp_friend_id, uid, sp_other_share, f"Part de {sp_ens}", tid)

                st.success(f"✅ Dépense enregistrée, dette de {sp_other_share:.2f}€ créée")
                st.balloons()
