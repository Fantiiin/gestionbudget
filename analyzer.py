import google.generativeai as genai
import json
import re
import io
import platform
from datetime import date
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()

if platform.system() == "Windows":
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


def _get_categories_for_prompt(user_id: int):
    from database import get_all_categories
    cats = get_all_categories(user_id)
    cat_names = [c["nom"] for c in cats]
    hints = []
    for c in cats:
        kw = c.get("mots_cles", "").strip()
        if kw:
            hints.append(f"  * {kw} → {c['nom']}")
    return cat_names, hints


def _build_prompt(ocr_text: str, today_str: str, user_id: int) -> str:
    cat_names, cat_hints = _get_categories_for_prompt(user_id)
    categories_str = ", ".join(cat_names)
    hints_str = "\n".join(cat_hints) if cat_hints else "  (aucun indice)"

    return f"""Voici le texte brut extrait par OCR d'un ou plusieurs tickets / relevés.
Extrais CHAQUE dépense ou revenu comme une transaction séparée au format JSON.

Date d'aujourd'hui : {today_str}

Texte :
\"\"\"
{ocr_text}
\"\"\"

Catégories : {categories_str}

Indices (mot-clé → catégorie) :
{hints_str}

RÈGLES :
- Chaque ligne = une transaction SÉPARÉE avec sa catégorie.
- Utilise les indices ET le contexte du nom.
- Revenu (salaire, virement entrant) → type "revenu". Sinon → "depense".
- EXCLURE 0.00€ et remboursements internes.

JSON uniquement :
{{
  "transactions": [
    {{"enseigne": "Nom", "date": "YYYY-MM-DD", "montant": 0.00, "type": "depense ou revenu", "categorie": "exacte"}}
  ]
}}

Si date absente → {today_str}. Montant = décimal positif."""


def configure_gemini():
    import streamlit as st
    api_key = None
    # 1) Streamlit Cloud secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    # 2) Fallback: .env / environment variable
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("🔑 Clé API manquante. Ajoutez `GEMINI_API_KEY` dans Streamlit secrets ou `.env`")
    genai.configure(api_key=api_key)


def ocr_extract_text(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise ValueError("🖼️ Image illisible.")

    # 1) Try Tesseract (fast, local)
    try:
        import pytesseract
        text = pytesseract.image_to_string(image, lang="fra+eng")
        if text.strip():
            return text.strip()
        text = pytesseract.image_to_string(image, lang="eng")
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # 2) Fallback: EasyOCR (pure Python, works on Streamlit Cloud)
    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(["fr", "en"], gpu=False, verbose=False)
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0)
        text = "\n".join(results)
        if text.strip():
            return text.strip()
    except ImportError:
        raise RuntimeError("📦 Aucun OCR disponible. Installez `pytesseract` ou `easyocr`.")
    except Exception as e:
        raise RuntimeError(f"🔧 Erreur OCR : {str(e)[:200]}")

    raise ValueError("🖼️ Aucun texte détecté dans l'image.")


def ocr_extract_multiple(images: list[tuple[bytes, str]]) -> str:
    all_texts = []
    for i, (img_bytes, _) in enumerate(images, 1):
        text = ocr_extract_text(img_bytes)
        if text:
            all_texts.append(f"--- Ticket {i} ---\n{text}")
    if not all_texts:
        raise ValueError("🖼️ Aucun texte extrait. Vérifiez la qualité des photos.")
    return "\n\n".join(all_texts)


def analyze_receipts(images: list[tuple[bytes, str]], user_id: int) -> list[dict]:
    configure_gemini()
    model = genai.GenerativeModel("gemini-2.5-flash")
    today_str = date.today().strftime("%Y-%m-%d")

    combined_text = ocr_extract_multiple(images)
    if len(combined_text) < 10:
        raise ValueError("📄 Texte trop court.")

    prompt = _build_prompt(combined_text, today_str, user_id)

    try:
        response = model.generate_content(prompt)
    except Exception as e:
        err = str(e)
        if "429" in err:
            raise RuntimeError("⏳ Quota Gemini atteint. Réessayez dans quelques minutes.")
        if "403" in err:
            raise RuntimeError("🔒 Accès refusé. Vérifiez votre clé API.")
        if "404" in err:
            raise RuntimeError("❌ Modèle introuvable.")
        raise RuntimeError(f"❌ Erreur API : {err[:200]}")

    return parse_response(response.text, today_str, user_id)


def parse_response(text: str, default_date: str, user_id: int) -> list[dict]:
    from database import get_category_names
    valid_cats = get_category_names(user_id)

    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError("🤖 Réponse IA invalide. Réessayez.")
    if "transactions" not in data:
        raise ValueError("🤖 Format inattendu. Réessayez.")

    transactions = []
    for item in data["transactions"]:
        montant = 0.0
        try:
            montant = float(item.get("montant", 0))
        except (ValueError, TypeError):
            pass
        if montant <= 0:
            continue
        cat = item.get("categorie", valid_cats[0] if valid_cats else "Autre")
        if cat not in valid_cats:
            cat = _find_closest_category(cat, valid_cats)
        txn_type = item.get("type", "depense")
        if txn_type not in ("depense", "revenu"):
            txn_type = "depense"
        transactions.append({
            "enseigne": item.get("enseigne", "Inconnu"),
            "date": item.get("date", default_date) or default_date,
            "montant": montant, "categorie": cat, "type": txn_type,
        })
    if not transactions:
        raise ValueError("📄 Aucune transaction détectée.")
    return transactions


def _find_closest_category(category: str, valid_cats: list[str]) -> str:
    cl = category.lower()
    for cat in valid_cats:
        if cat.lower() in cl or cl in cat.lower():
            return cat
    return valid_cats[0] if valid_cats else "Autre"
