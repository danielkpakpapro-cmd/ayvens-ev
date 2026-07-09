"""
discover_api.py — Ayvens
==========================
Intercepte les appels réseau (XHR/fetch) faits par le site pendant le
chargement du catalogue, à la recherche de l'API interne qui liste les
marques (et peut-être directement leurs compteurs). Si on trouve cet
endpoint, le scraper final pourra l'appeler directement — plus besoin
d'une liste de marques codée en dur, tout reste à jour automatiquement.

USAGE
-----
    python discover_api.py

Résultat : sauvegarde toutes les réponses JSON candidates dans
discovered_ayvens.json, et affiche les plus prometteuses dans le terminal
(celles qui contiennent des noms de marques connus).
"""

import json

from playwright.sync_api import sync_playwright

URL = "https://used-cars.ayvens.com/fr-fr/catalog?financetype=leasing"

KNOWN_BRAND_HINTS = ["peugeot", "renault", "citroen", "volkswagen", "bmw", "make", "brand", "marque"]


def main():
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1400, "height": 1000}, locale="fr-FR")
        page = context.new_page()

        def handle_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "json" not in ct.lower():
                    return
                body = response.body()
                if len(body) < 200:
                    return
                text_lower = body.decode(errors="ignore").lower()
                if not any(hint in text_lower for hint in KNOWN_BRAND_HINTS):
                    return
                try:
                    parsed = json.loads(body)
                    preview = json.dumps(parsed, ensure_ascii=False)[:2000]
                except Exception:
                    preview = body[:2000].decode(errors="replace")

                candidates.append({
                    "url": response.url,
                    "method": response.request.method,
                    "size_bytes": len(body),
                    "preview": preview,
                })
                print(f"[+] Candidat trouvé ({len(body)} octets) : {response.url}")
            except Exception:
                pass

        page.on("response", handle_response)

        print(f"Ouverture de {URL} ...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        for label in ["Tout accepter", "Accepter", "J'accepte", "Accepter tout"]:
            try:
                btn = page.get_by_text(label, exact=False)
                if btn.count() > 0 and btn.first.is_visible():
                    btn.first.click(timeout=2000)
                    page.wait_for_timeout(1000)
                    break
            except Exception:
                pass

        # Scroll pour déclencher le chargement des filtres/marques
        for _ in range(10):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(500)

        page.wait_for_timeout(3000)
        browser.close()

    candidates.sort(key=lambda c: c["size_bytes"], reverse=True)

    with open("discovered_ayvens.json", "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)

    print(f"\n{len(candidates)} candidat(s) sauvegardé(s) dans discovered_ayvens.json")
    print("\n=== Les 3 plus gros candidats (probablement les bons) ===")
    for c in candidates[:3]:
        print(f"\nURL: {c['url']}")
        print(f"Taille: {c['size_bytes']} octets")
        print(f"Aperçu: {c['preview'][:500]}")


if __name__ == "__main__":
    main()
