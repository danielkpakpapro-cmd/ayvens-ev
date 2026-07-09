"""
discover_brands2.py — Ayvens
==============================
Deuxième tentative de découverte automatique des marques : on liste TOUTES
les images de la page avec un attribut alt renseigné (les icônes de marque
en sont probablement, vu leur apparence dans les captures d'écran), après
avoir bien scrollé pour déclencher leur chargement.

USAGE
-----
    python discover_brands2.py
"""

from playwright.sync_api import sync_playwright

URL = "https://used-cars.ayvens.com/fr-fr/catalog?financetype=leasing"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1400, "height": 1000}, locale="fr-FR")
        page = context.new_page()

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

        # Scroll généreux pour charger tout le contenu de la page
        for _ in range(15):
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(300)
        page.wait_for_timeout(1500)

        print("\n=== Toutes les images avec attribut alt ===")
        imgs = page.locator("img[alt]")
        n = imgs.count()
        print(f"{n} images trouvées.\n")
        alt_texts = []
        for i in range(n):
            alt = imgs.nth(i).get_attribute("alt")
            if alt and alt.strip():
                alt_texts.append(alt.strip())
                print(f"  - {alt.strip()}")

        print("\n=== Tous les boutons/éléments cliquables avec aria-label ===")
        aria_els = page.locator("[aria-label]")
        n2 = aria_els.count()
        for i in range(n2):
            label = aria_els.nth(i).get_attribute("aria-label")
            if label and label.strip() and len(label) < 40:
                print(f"  - {label.strip()}")

        print(f"\nCapture d'écran sauvegardée : ayvens_page.png")
        page.screenshot(path="ayvens_page.png", full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
