import json
import os
import time

import requests
from dotenv import load_dotenv

from images import fetch_image

load_dotenv("/opt/ai-news-reader/.env", override=True)
KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

CATEGORIES = ["Maroc", "Sciences & Espace", "IA & Technologie",
              "Cybersécurité & Réseaux", "Monde & Économie", "Sport", "Tendances Reddit"]

PROMPT = """Tu es le rédacteur en chef d'un magazine quotidien en français, style magazine scientifique et d'actualité.
Voici des articles (id | source | [img] si une image existe | titre | extrait), en arabe, français ou anglais.

Construis l'édition du jour :
- "lead" : 1 article à la une (de préférence avec [img]), résumé de 6 à 8 phrases.
- "stories" : 14 articles importants, résumé de 3 à 4 phrases chacun.
- "briefs" : 14 autres articles, une seule phrase chacun.
- "top5" : 5 phrases courtes (15 mots maximum) résumant l'essentiel du jour.
- "fact" : un fait scientifique ou technique marquant (« Le saviez-vous ? »), 1 à 2 phrases, tiré d'un article, avec son id.

Règles :
- Équilibre : au moins 30 % Maroc ; au moins 3 articles Sciences & Espace ; le reste IA, cybersécurité/réseaux, monde. Maximum 2 articles de sport au total.
- Chaque id n'est utilisé qu'une seule fois dans toute l'édition. Pas de doublons de sujet.
- Les articles dont la source commence par « Reddit » vont TOUS dans la catégorie « Tendances Reddit » (au moins 4 au total) : présente-les comme des discussions populaires de la communauté, jamais comme des faits établis.
- Évite promos, tests de produits grand public et people.
- N'invente AUCUN fait : uniquement le titre et l'extrait fournis. Si l'extrait est court, reste bref plutôt que d'inventer.
- Catégories autorisées : {cats}.

Réponds uniquement par un objet JSON :
{{"top5": ["..."], "lead": {{"id": 0, "category": "...", "title_fr": "...", "summary_fr": "..."}},
"stories": [{{"id": 0, "category": "...", "title_fr": "...", "summary_fr": "...", "importance": 5}}],
"briefs": [{{"id": 0, "category": "...", "title_fr": "...", "summary_fr": "..."}}],
"fact": {{"id": 0, "text_fr": "..."}}}}

ARTICLES :
{items}
"""


def _call(prompt):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "temperature": 0.2, "maxOutputTokens": 20000},
    }
    for attempt in range(4):
        r = requests.post(URL, headers={"x-goog-api-key": KEY}, json=body, timeout=240)
        if r.status_code in (429, 500, 503):
            time.sleep(15 * (attempt + 1))
            continue
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        return json.loads(text)
    raise RuntimeError("Gemini unavailable after retries")


def summarize(articles, max_input=170):
    pool = articles[:max_input]
    items = "\n".join(
        f"{i} | {a['source']} |{' [img]' if a.get('image') else ''} | {a['title']} | {a['text'][:250]}"
        for i, a in enumerate(pool)
    )
    data = _call(PROMPT.format(cats=CATEGORIES, items=items))

    used, out = set(), []

    def add(item, tier):
        if not isinstance(item, dict):
            return
        i = item.get("id")
        if not isinstance(i, int) or not 0 <= i < len(pool) or i in used:
            return
        used.add(i)
        a = pool[i]  # URL, source and date always come from the real article
        cat = item.get("category")
        out.append({
            "tier": tier,
            "category": cat if cat in CATEGORIES else "Monde & Économie",
            "title": item.get("title_fr") or a["title"],
            "summary": item.get("summary_fr", ""),
            "importance": item.get("importance", 5),
            "source": a["source"],
            "url": a["url"],
            "published": a["published"],
            "image_url": a.get("image"),
        })

    add(data.get("lead"), "lead")
    for s in sorted(data.get("stories", []), key=lambda x: -(x.get("importance") or 0)):
        add(s, "story")
    for b in data.get("briefs", []):
        add(b, "brief")

    for e in out:
        e["image"] = fetch_image(e["image_url"]) if e["tier"] in ("lead", "story") else None
        e.pop("image_url", None)

    fact = None
    f = data.get("fact") or {}
    fi = f.get("id")
    if isinstance(fi, int) and 0 <= fi < len(pool) and f.get("text_fr"):
        fact = {"text": f["text_fr"], "source": pool[fi]["source"], "url": pool[fi]["url"]}

    return {"top5": [str(t) for t in data.get("top5", [])][:5], "fact": fact, "articles": out}
