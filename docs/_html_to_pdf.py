import os
from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:8778/_readme_render.html"
SAIDA = os.path.join(AQUI, "README.pdf")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_selector(".mermaid svg", timeout=30000)
    page.wait_for_timeout(1500)
    page.pdf(
        path=SAIDA,
        format="A4",
        print_background=True,
        margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
    )
    browser.close()

print("OK:", SAIDA)
