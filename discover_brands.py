"""
discover_brands.py — Ayvens
=============================
Découvre le code exact (slug d'URL) de chaque marque en lisant directement
les liens HTML du panneau de filtres — pas besoin de cliquer, donc
insensible aux problèmes de visibilité/scroll.

Structure découverte : <a href="/fr-fr/make/bmw?financetype=leasing">BMW</a>

USAGE
-----
    python discover_brands.py
"""

import re

from playwright.sync_api import sync_playwright

BASE_URL = "https://used-cars.ayvens.com/fr-fr/catalog?financetype=leasing"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1400, "height": 1000}, locale="fr-FR")
        page = context.new_page()

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
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

        # Le panneau de filtres charge les icônes de marque progressivement
        # au défilement (chargement différé) — on scrolle plusieurs fois et
        # on continue tant que de nouveaux liens apparaissent.
        first_link = page.locator("a[href*='/make/']").first
        try:
            first_link.hover(timeout=3000)
        except Exception:
            pass

        previous_count = -1
        for _ in range(30):
            current_count = page.locator("a[href*='/make/']").count()
            if current_count == previous_count:
                break
            previous_count = current_count
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(500)
        print(f"Défilement terminé, {previous_count} liens détectés avant lecture finale.\n")

        # Récupère tous les liens dont le href contient "/make/", visibles ou non.
        links = page.locator("a[href*='/make/']")
        count = links.count()
        print(f"{count} liens de marque trouvés.\n")

        results = {}
        for i in range(count):
            el = links.nth(i)
            href = el.get_attribute("href")
            name = el.inner_text().strip()
            m = re.search(r"/make/([^/?]+)", href or "")
            slug = m.group(1) if m else None
            if name and slug and name not in results:
                results[name] = slug
                print(f"{name:20s} -> {slug}")

        browser.close()

        print("\n=== Résumé (à copier) ===")
        for name, slug in results.items():
            print(f'    "{name}": "{slug}",')


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
