import sqlite3
import json
from pathlib import Path
from datetime import datetime, date, timedelta

DB_PATH = Path(__file__).parent / "budget.db"

DEFAULT_CATEGORIES = [
    {"nom": "Alimentaire", "icon": "🛒", "color": "#22c55e", "mots_cles": "supermarché, carrefour, leclerc, auchan, lidl, monoprix, boulangerie, briocherie, boucherie, sodexo, café"},
    {"nom": "Hygiène & Soins", "icon": "🧴", "color": "#3b82f6", "mots_cles": "shampoing, savon, dentifrice, coiffeur, beauté"},
    {"nom": "Loisirs & Sorties", "icon": "🎉", "color": "#f59e0b", "mots_cles": "restaurant, bar, pub, club, boîte de nuit, cinéma, bowling, concert, burger, kebab, pizza"},
    {"nom": "Transport", "icon": "🚗", "color": "#ef4444", "mots_cles": "sncf, ratp, essence, parking, uber, taxi, péage, train, bus, métro"},
    {"nom": "Logement & Factures", "icon": "🏠", "color": "#8b5cf6", "mots_cles": "loyer, edf, free, orange, assurance, électricité, gaz, internet, téléphone"},
    {"nom": "Shopping", "icon": "🛍️", "color": "#ec4899", "mots_cles": "zara, h&m, amazon, fnac, vêtements, chaussures"},
    {"nom": "Santé", "icon": "💊", "color": "#06b6d4", "mots_cles": "pharmacie, médecin, docteur, hôpital, mutuelle"},
    {"nom": "Revenu", "icon": "💰", "color": "#10b981", "mots_cles": "salaire, freelance, virement, remboursement"},
]

AVATAR_LIST = ["😎", "🦊", "🐱", "🐶", "🦁", "🐼", "🦄", "🐸", "🦉", "🐧",
               "🌸", "🌊", "⚡", "🔥", "💎", "🎯", "🚀", "🎨", "🎸", "🌙",
               "👤", "👩", "👨", "🧑", "👸", "🤴", "🧙", "🦸", "🧛", "🤖"]


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar TEXT NOT NULL DEFAULT '👤',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            date TEXT NOT NULL,
            enseigne TEXT NOT NULL,
            montant_total REAL NOT NULL,
            categorie TEXT NOT NULL,
            chemin_image TEXT,
            articles TEXT,
            type TEXT NOT NULL DEFAULT 'depense',
            added_by INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS recurring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            enseigne TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'depense',
            frequence TEXT NOT NULL,
            jour INTEGER NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            nom TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '📁',
            color TEXT NOT NULL DEFAULT '#a78bfa',
            mots_cles TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_a INTEGER NOT NULL,
            user_b INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_a, user_b)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            categorie TEXT NOT NULL,
            montant_max REAL NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, categorie)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            montant REAL NOT NULL,
            description TEXT NOT NULL,
            settled INTEGER NOT NULL DEFAULT 0,
            transaction_id INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            categorie TEXT,
            montant_max REAL NOT NULL,
            date_debut TEXT NOT NULL,
            date_fin TEXT NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS challenge_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenge_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(challenge_id, user_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    # Migrations
    user_cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "avatar" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT NOT NULL DEFAULT '👤'")
    if "preferred_page" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN preferred_page TEXT NOT NULL DEFAULT 'Dashboard'")
    if "theme" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN theme TEXT NOT NULL DEFAULT 'dark'")

    tx_cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    if "type" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN type TEXT NOT NULL DEFAULT 'depense'")
    if "user_id" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    if "added_by" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN added_by INTEGER")
    if "tags" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN tags TEXT NOT NULL DEFAULT ''")
    if "sous_categorie" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN sous_categorie TEXT NOT NULL DEFAULT ''")
    if "comment" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN comment TEXT NOT NULL DEFAULT ''")

    rec_cols = [r[1] for r in conn.execute("PRAGMA table_info(recurring)").fetchall()]
    if "user_id" not in rec_cols:
        conn.execute("ALTER TABLE recurring ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")

    cat_cols = [r[1] for r in conn.execute("PRAGMA table_info(categories)").fetchall()]
    if "user_id" not in cat_cols:
        conn.execute("ALTER TABLE categories ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    if "sous_categories" not in cat_cols:
        conn.execute("ALTER TABLE categories ADD COLUMN sous_categories TEXT NOT NULL DEFAULT ''")

    conn.commit()
    conn.close()


def seed_default_categories(user_id: int):
    conn = get_connection()
    existing = conn.execute("SELECT COUNT(*) as c FROM categories WHERE user_id = ?", (user_id,)).fetchone()["c"]
    if existing == 0:
        for cat in DEFAULT_CATEGORIES:
            conn.execute(
                "INSERT INTO categories (user_id, nom, icon, color, mots_cles, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, cat["nom"], cat["icon"], cat["color"], cat["mots_cles"], datetime.now().isoformat())
            )
    conn.commit()
    conn.close()


def ensure_user_has_categories(user_id: int):
    """Call this on each page load to fix the bug where users have no categories."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM categories WHERE user_id = ?", (user_id,)).fetchone()["c"]
    conn.close()
    if count == 0:
        seed_default_categories(user_id)


# ─── Users ───

def create_user(username: str, password_hash: str, display_name: str, avatar: str = "👤") -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, display_name, avatar, created_at) VALUES (?, ?, ?, ?, ?)",
            (username.lower().strip(), password_hash, display_name.strip(), avatar, datetime.now().isoformat())
        )
        conn.commit()
        uid = cursor.lastrowid
    finally:
        conn.close()
    return uid


def get_user_by_username(username: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username.lower().strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT id, username, display_name, avatar FROM users ORDER BY display_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Friendships ───

def send_friend_request(from_id: int, to_id: int) -> bool:
    if from_id == to_id:
        return False
    a, b = min(from_id, to_id), max(from_id, to_id)
    conn = get_connection()
    existing = conn.execute("SELECT * FROM friendships WHERE user_a = ? AND user_b = ?", (a, b)).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute(
        "INSERT INTO friendships (user_a, user_b, status, requested_by, created_at) VALUES (?, ?, 'pending', ?, ?)",
        (a, b, from_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return True


def accept_friend_request(friendship_id: int):
    conn = get_connection()
    conn.execute("UPDATE friendships SET status = 'accepted' WHERE id = ?", (friendship_id,))
    conn.commit()
    conn.close()


def reject_friend_request(friendship_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM friendships WHERE id = ?", (friendship_id,))
    conn.commit()
    conn.close()


def remove_friend(friendship_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM friendships WHERE id = ?", (friendship_id,))
    conn.commit()
    conn.close()


def get_friends(user_id: int) -> list[dict]:
    """Return accepted friends with their user info."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.id as friendship_id, u.id, u.username, u.display_name, u.avatar
        FROM friendships f
        JOIN users u ON (u.id = CASE WHEN f.user_a = ? THEN f.user_b ELSE f.user_a END)
        WHERE (f.user_a = ? OR f.user_b = ?) AND f.status = 'accepted'
    """, (user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_requests_for_me(user_id: int) -> list[dict]:
    """Friend requests TO me that I haven't accepted."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.id as friendship_id, u.id as user_id, u.username, u.display_name, u.avatar
        FROM friendships f
        JOIN users u ON u.id = f.requested_by
        WHERE ((f.user_a = ? OR f.user_b = ?) AND f.requested_by != ? AND f.status = 'pending')
    """, (user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_requests_from_me(user_id: int) -> list[dict]:
    """Friend requests I sent that are still pending."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.id as friendship_id, u.id as user_id, u.username, u.display_name, u.avatar
        FROM friendships f
        JOIN users u ON (u.id = CASE WHEN f.user_a = ? THEN f.user_b ELSE f.user_a END)
        WHERE (f.user_a = ? OR f.user_b = ?) AND f.requested_by = ? AND f.status = 'pending'
    """, (user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_friend_ids(user_id: int) -> list[int]:
    """Just the IDs of accepted friends."""
    return [f["id"] for f in get_friends(user_id)]


# ─── Categories (per user) ───

def get_all_categories(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories WHERE user_id = ? ORDER BY nom", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_names(user_id: int) -> list[str]:
    return [c["nom"] for c in get_all_categories(user_id)]


def get_category_map(user_id: int) -> dict:
    cats = get_all_categories(user_id)
    return {c["nom"]: {"icon": c["icon"], "color": c["color"], "mots_cles": c["mots_cles"]} for c in cats}


def insert_category(user_id: int, nom: str, icon: str, color: str, mots_cles: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO categories (user_id, nom, icon, color, mots_cles, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, nom, icon, color, mots_cles, datetime.now().isoformat())
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


def delete_category(cat_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


# ─── Transactions (per user) ───

def insert_transaction(user_id: int, date: str, enseigne: str, montant_total: float,
                       categorie: str, chemin_image: str, articles: list,
                       txn_type: str = "depense", added_by: int | None = None) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO transactions (user_id, date, enseigne, montant_total, categorie, chemin_image, articles, type, added_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, date, enseigne, montant_total, categorie, chemin_image,
         json.dumps(articles, ensure_ascii=False), txn_type, added_by, datetime.now().isoformat())
    )
    conn.commit()
    tid = cursor.lastrowid
    conn.close()
    return tid


def get_transactions_by_month(user_id: int, year: int, month: int) -> list[dict]:
    month_str = f"{year}-{month:02d}"
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND date LIKE ? ORDER BY date DESC",
        (user_id, f"{month_str}%")
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_all_transactions(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC", (user_id,)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_monthly_totals(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT substr(date, 1, 7) as mois,
               SUM(CASE WHEN type = 'depense' THEN montant_total ELSE 0 END) as depenses,
               SUM(CASE WHEN type = 'revenu' THEN montant_total ELSE 0 END) as revenus
        FROM transactions WHERE user_id = ?
        GROUP BY mois ORDER BY mois
    """, (user_id,)).fetchall()
    conn.close()
    return [{"mois": r["mois"], "depenses": r["depenses"], "revenus": r["revenus"]} for r in rows]


def delete_transaction(transaction_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_unique_enseignes(user_id: int) -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT enseigne FROM transactions WHERE user_id = ? ORDER BY enseigne",
        (user_id,)
    ).fetchall()
    conn.close()
    return [r["enseigne"] for r in rows]


def duplicate_transaction(txn_id: int) -> int | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
    if not row:
        conn.close()
        return None
    t = dict(row)
    cursor = conn.execute(
        """INSERT INTO transactions (user_id, date, enseigne, montant_total, categorie, chemin_image, articles, type, added_by, tags, sous_categorie, comment, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (t["user_id"], date.today().strftime("%Y-%m-%d"), t["enseigne"], t["montant_total"],
         t["categorie"], t.get("chemin_image", ""), t.get("articles", "[]") if isinstance(t.get("articles"), str) else json.dumps(t.get("articles", [])),
         t.get("type", "depense"), t.get("added_by"), t.get("tags", ""), t.get("sous_categorie", ""),
         t.get("comment", ""), datetime.now().isoformat())
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_user_preference(user_id: int, key: str, value: str):
    conn = get_connection()
    conn.execute(f"UPDATE users SET {key} = ? WHERE id = ?", (value, user_id))
    conn.commit()
    conn.close()


# ─── Recurring (per user) ───

def insert_recurring(user_id: int, enseigne: str, montant: float, categorie: str,
                     txn_type: str, frequence: str, jour: int) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO recurring (user_id, enseigne, montant, categorie, type, frequence, jour, actif, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
        (user_id, enseigne, montant, categorie, txn_type, frequence, jour, datetime.now().isoformat())
    )
    conn.commit()
    rid = cursor.lastrowid
    conn.close()
    return rid


def get_all_recurring(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM recurring WHERE user_id = ? AND actif = 1 ORDER BY id", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_recurring(recurring_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM recurring WHERE id = ?", (recurring_id,))
    conn.commit()
    conn.close()


def apply_recurring_for_month(user_id: int, year: int, month: int):
    import calendar
    recurrings = get_all_recurring(user_id)
    if not recurrings:
        return 0
    conn = get_connection()
    count = 0
    _, last_day = calendar.monthrange(year, month)
    for rec in recurrings:
        dates = []
        if rec["frequence"] == "mensuel":
            d = date(year, month, min(rec["jour"], last_day))
            if d <= date.today(): dates.append(d)
        elif rec["frequence"] == "hebdomadaire":
            d = date(year, month, 1)
            while d.month == month:
                if d.weekday() == rec["jour"] and d <= date.today(): dates.append(d)
                d += timedelta(days=1)
        for d in dates:
            ds = d.strftime("%Y-%m-%d")
            ex = conn.execute(
                "SELECT id FROM transactions WHERE user_id=? AND date=? AND enseigne=? AND montant_total=? AND type=?",
                (user_id, ds, rec["enseigne"], rec["montant"], rec["type"])
            ).fetchone()
            if not ex:
                conn.execute(
                    "INSERT INTO transactions (user_id, date, enseigne, montant_total, categorie, chemin_image, articles, type, created_at) VALUES (?,?,?,?,?,'','[]',?,?)",
                    (user_id, ds, rec["enseigne"], rec["montant"], rec["categorie"], rec["type"], datetime.now().isoformat())
                )
                count += 1
    conn.commit()
    conn.close()
    return count


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("articles"):
        try: d["articles"] = json.loads(d["articles"])
        except json.JSONDecodeError: d["articles"] = []
    else:
        d["articles"] = []
    if "type" not in d: d["type"] = "depense"
    return d


# ─── Budgets ───

def set_budget(user_id: int, categorie: str, montant_max: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO budgets (user_id, categorie, montant_max, created_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(user_id, categorie) DO UPDATE SET montant_max = ?",
        (user_id, categorie, montant_max, datetime.now().isoformat(), montant_max)
    )
    conn.commit()
    conn.close()


def get_budgets(user_id: int) -> dict:
    conn = get_connection()
    rows = conn.execute("SELECT categorie, montant_max FROM budgets WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return {r["categorie"]: r["montant_max"] for r in rows}


def delete_budget(user_id: int, categorie: str):
    conn = get_connection()
    conn.execute("DELETE FROM budgets WHERE user_id = ? AND categorie = ?", (user_id, categorie))
    conn.commit()
    conn.close()


# ─── Edit Transaction ───

def update_transaction(txn_id: int, date: str, enseigne: str, montant_total: float,
                       categorie: str, txn_type: str, tags: str = "", sous_categorie: str = ""):
    conn = get_connection()
    conn.execute(
        """UPDATE transactions SET date=?, enseigne=?, montant_total=?, categorie=?, type=?, tags=?, sous_categorie=?
           WHERE id=?""",
        (date, enseigne, montant_total, categorie, txn_type, tags, sous_categorie, txn_id)
    )
    conn.commit()
    conn.close()


def get_transaction_by_id(txn_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


# ─── Search ───

def search_transactions(user_id: int, query: str, limit: int = 100) -> list[dict]:
    conn = get_connection()
    q = f"%{query}%"
    rows = conn.execute(
        """SELECT * FROM transactions WHERE user_id = ?
           AND (enseigne LIKE ? OR categorie LIKE ? OR tags LIKE ? OR sous_categorie LIKE ?)
           ORDER BY date DESC LIMIT ?""",
        (user_id, q, q, q, q, limit)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ─── Multi-month ───

def get_transactions_by_range(user_id: int, date_from: str, date_to: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date DESC",
        (user_id, date_from, date_to)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ─── Export ───

def export_transactions_csv(user_id: int, year: int = None, month: int = None) -> str:
    if year and month:
        txs = get_transactions_by_month(user_id, year, month)
    else:
        txs = get_all_transactions(user_id)
    lines = ["Date,Enseigne,Montant,Catégorie,Sous-catégorie,Type,Tags"]
    for t in txs:
        tags = t.get("tags", "")
        sc = t.get("sous_categorie", "")
        ens = t["enseigne"].replace(",", ";")
        lines.append(f'{t["date"]},{ens},{t["montant_total"]:.2f},{t["categorie"]},{sc},{t.get("type","depense")},{tags}')
    return "\n".join(lines)


# ─── Debts ───

def create_debt(from_user: int, to_user: int, montant: float, description: str, transaction_id: int = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO debts (from_user, to_user, montant, description, settled, transaction_id, created_at) VALUES (?,?,?,?,0,?,?)",
        (from_user, to_user, montant, description, transaction_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def settle_debt(debt_id: int):
    conn = get_connection()
    conn.execute("UPDATE debts SET settled = 1 WHERE id = ?", (debt_id,))
    conn.commit()
    conn.close()


def get_debts_between(user_a: int, user_b: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM debts WHERE
           ((from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?))
           ORDER BY created_at DESC""",
        (user_a, user_b, user_b, user_a)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_debt_balance(user_id: int, friend_id: int) -> float:
    """Positive = friend owes user, Negative = user owes friend."""
    conn = get_connection()
    owed_to_me = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) as s FROM debts WHERE from_user = ? AND to_user = ? AND settled = 0",
        (friend_id, user_id)
    ).fetchone()["s"]
    i_owe = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) as s FROM debts WHERE from_user = ? AND to_user = ? AND settled = 0",
        (user_id, friend_id)
    ).fetchone()["s"]
    conn.close()
    return owed_to_me - i_owe


def get_all_unsettled_debts(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM debts WHERE (from_user = ? OR to_user = ?) AND settled = 0 ORDER BY created_at DESC",
        (user_id, user_id)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Challenges ───

def create_challenge(creator_id: int, title: str, categorie: str, montant_max: float,
                     date_debut: str, date_fin: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO challenges (creator_id, title, categorie, montant_max, date_debut, date_fin, actif, created_at) VALUES (?,?,?,?,?,?,1,?)",
        (creator_id, title, categorie, montant_max, date_debut, date_fin, datetime.now().isoformat())
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.execute("INSERT INTO challenge_participants (challenge_id, user_id) VALUES (?, ?)", (cid, creator_id))
    conn.commit()
    conn.close()
    return cid


def join_challenge(challenge_id: int, user_id: int):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO challenge_participants (challenge_id, user_id) VALUES (?, ?)",
                 (challenge_id, user_id))
    conn.commit()
    conn.close()


def get_active_challenges(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.* FROM challenges c
        JOIN challenge_participants cp ON cp.challenge_id = c.id
        WHERE cp.user_id = ? AND c.actif = 1
        ORDER BY c.date_fin
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_challenge_participants(challenge_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.username, u.display_name, u.avatar FROM challenge_participants cp
        JOIN users u ON u.id = cp.user_id
        WHERE cp.challenge_id = ?
    """, (challenge_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_challenge_scores(challenge_id: int) -> list[dict]:
    conn = get_connection()
    ch = conn.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,)).fetchone()
    if not ch:
        conn.close()
        return []
    ch = dict(ch)
    participants = get_challenge_participants(challenge_id)
    scores = []
    for p in participants:
        cat_filter = "AND categorie = ?" if ch["categorie"] else ""
        params = [p["id"], ch["date_debut"], ch["date_fin"]]
        if ch["categorie"]:
            params.append(ch["categorie"])
        total = conn.execute(
            f"SELECT COALESCE(SUM(montant_total), 0) as s FROM transactions WHERE user_id=? AND date>=? AND date<=? AND type='depense' {cat_filter}",
            params
        ).fetchone()["s"]
        scores.append({**p, "total": total, "max": ch["montant_max"]})
    conn.close()
    scores.sort(key=lambda x: x["total"])
    return scores


def delete_challenge(challenge_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM challenge_participants WHERE challenge_id = ?", (challenge_id,))
    conn.execute("DELETE FROM challenges WHERE id = ?", (challenge_id,))
    conn.commit()
    conn.close()


# ─── Savings Goals ───

def create_savings_goal(user_id: int, title: str, target_amount: float) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO savings_goals (user_id, title, target_amount, current_amount, created_at) VALUES (?,?,?,0,?)",
        (user_id, title, target_amount, datetime.now().isoformat())
    )
    conn.commit()
    gid = cursor.lastrowid
    conn.close()
    return gid


def update_savings_goal(goal_id: int, current_amount: float):
    conn = get_connection()
    conn.execute("UPDATE savings_goals SET current_amount = ? WHERE id = ?", (current_amount, goal_id))
    conn.commit()
    conn.close()


def get_savings_goals(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM savings_goals WHERE user_id = ? ORDER BY id", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_savings_goal(goal_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()


# ─── Smart Budget ───

def get_smart_budget_info(user_id: int, year: int, month: int) -> dict:
    """Calculate daily allowance based on total budget, days passed, and spending so far."""
    import calendar
    budgets = get_budgets(user_id)
    total_budget = sum(budgets.values())
    if total_budget <= 0:
        return {"has_budget": False}

    _, last_day = calendar.monthrange(year, month)
    today = date.today()

    if today.year == year and today.month == month:
        day_of_month = today.day
    else:
        day_of_month = last_day

    days_remaining = last_day - day_of_month
    days_elapsed = day_of_month

    # Get spending so far this month
    txs = get_transactions_by_month(user_id, year, month)
    spent = sum(t["montant_total"] for t in txs if t.get("type", "depense") == "depense")

    remaining = total_budget - spent
    daily_ideal = total_budget / last_day
    daily_allowance = remaining / max(days_remaining, 1) if days_remaining > 0 else 0

    # Spent today
    today_str = today.strftime("%Y-%m-%d")
    spent_today = sum(t["montant_total"] for t in txs if t["date"] == today_str and t.get("type", "depense") == "depense")

    # Status
    if remaining <= 0:
        status = "over"
        message = f"⚠️ Budget dépassé de {abs(remaining):.0f}€"
    elif daily_allowance >= daily_ideal * 1.2:
        status = "ahead"
        advance = (daily_allowance - daily_ideal) * days_remaining
        message = f"🎉 {advance:.0f}€ d'avance ! Tu peux dépenser {daily_allowance:.0f}€/jour"
    elif daily_allowance >= daily_ideal * 0.8:
        status = "on_track"
        message = f"✅ En bonne voie — {daily_allowance:.0f}€/jour restant"
    else:
        status = "behind"
        message = f"⚡ Attention — seulement {daily_allowance:.0f}€/jour restant"

    return {
        "has_budget": True,
        "total_budget": total_budget,
        "spent": spent,
        "remaining": remaining,
        "days_remaining": days_remaining,
        "days_elapsed": days_elapsed,
        "daily_ideal": daily_ideal,
        "daily_allowance": daily_allowance,
        "spent_today": spent_today,
        "status": status,
        "message": message,
    }

