# Manual PDF: python3 tools/manual_pdf.py Manuals/gfx-xxx.html site/manual/gfx-xxx.pdf "Name"
import sys, pathlib
from playwright.sync_api import sync_playwright
src, out, name = sys.argv[1], sys.argv[2], sys.argv[3]
foot = ('<div style="font-family:Arial,sans-serif;font-size:8px;color:#555;width:100%;text-align:center;">'
        f'GFX - GFX {name} - manual - page <span class="pageNumber"></span> of <span class="totalPages"></span> - &copy; 2026 John Garden</div>')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto(pathlib.Path(src).resolve().as_uri()); pg.wait_for_load_state("networkidle")
    pg.pdf(path=out, format="A4", print_background=False, display_header_footer=True, header_template="<div></div>",
           footer_template=foot, margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
    b.close()
