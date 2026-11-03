"""Render saved, actual results for review. Does not run database or model calls."""
from pathlib import Path
import notebook_view
from notebook_view import show_early, show_evolved, show_comparison, show_graph, show_control, show_handoff, show_automatic

root = Path(__file__).resolve().parent
parts = []
notebook_view.display = lambda item: parts.append(item.data)
for show in [show_early, show_evolved, show_comparison, show_graph, show_control, show_handoff, show_automatic]:
    show()
assert len(parts) == 7, "Every saved result section must be rendered."
page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Incident handoff: saved results</title><style>body{margin:0;background:#f5f6f7;padding:30px;font-family:Arial,sans-serif}main{max-width:1320px;margin:auto}.inc-demo{margin-bottom:24px}header{margin-bottom:24px}header p{color:#586776}</style></head><body><main><header><h1>Incident handoff: saved results</h1><p>Review of the verified local run. These are recorded outputs; run the notebook for a fresh demonstration.</p></header>''' + ''.join(parts) + '</main></body></html>'
(root / 'results/review_preview.html').write_text(page)
print('Saved results/review_preview.html. No database or model calls were made.')
