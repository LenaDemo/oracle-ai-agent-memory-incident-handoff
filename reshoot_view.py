"""Audience-facing views for the longer incident handoff walkthrough.

Results come from the existing demo commands. Importing this module does not
connect to the database, reset records, or call a model.
"""
from __future__ import annotations

import ast
import html
import json
import re
from pathlib import Path

from IPython.display import HTML, display
import notebook_view as original
from fixtures import NOTES, QUERY

ROOT = Path(__file__).resolve().parent
_completed = set()

STYLE = """<style>
.reshoot{font:17px/1.5 -apple-system,BlinkMacSystemFont,Arial,sans-serif;color:#202b34;background:#fff;padding:26px;border:1px solid #d9e0e5;border-radius:12px;box-sizing:border-box}
.reshoot *{box-sizing:border-box}.reshoot h2{font-size:27px;line-height:1.2;margin:4px 0 16px}.reshoot h3{font-size:19px;margin:0 0 10px}.reshoot p{margin:7px 0 12px}.reshoot .eyebrow{font-size:12px;letter-spacing:1px;color:#526776;text-transform:uppercase;margin-bottom:10px}.reshoot .muted{color:#526776;font-size:14px}.reshoot code{font:13px/1.4 ui-monospace,monospace;overflow-wrap:anywhere}.reshoot .cards{display:grid;grid-template-columns:1fr 1fr;gap:14px}.reshoot .note{padding:15px;border:1px solid #ccd7df;border-radius:8px;background:#f5f8fa}.reshoot .historical{background:#fff6e7}.reshoot .status{font-size:12px;font-weight:700;letter-spacing:.5px;text-transform:uppercase}.reshoot .three{display:grid;grid-template-columns:minmax(0,40fr) minmax(0,35fr) minmax(0,25fr);gap:20px;align-items:start}.reshoot .answer{font-size:16px;line-height:1.45}.reshoot .answer p{margin:0 0 12px}.reshoot .answer h4{font-size:16px;margin:14px 0 5px}.reshoot .answer h4:first-child{margin-top:0}.reshoot .source-list{font-size:14px;line-height:1.45}.reshoot .source-list .note{padding:11px;margin-bottom:10px}.reshoot .source-list p{margin-bottom:4px}.reshoot svg{display:block;width:100%;height:auto}.reshoot .question{padding:10px 14px;background:#edf4f9;border-left:4px solid #416c8d}.reshoot .pair{display:grid;grid-template-columns:1fr 1fr;gap:20px}.reshoot .pair .note{margin-bottom:12px}.reshoot .relation{font-size:13px;color:#415969;margin:8px 0}.reshoot .comparison{font-size:15px}.reshoot table{width:100%;border-collapse:collapse;font-size:15px}.reshoot td,.reshoot th{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #d8e0e6}.reshoot th{background:#f1f5f8}.reshoot pre{font:16px/1.5 ui-monospace,monospace;white-space:pre-wrap;background:#f1f5f8;padding:18px;border-radius:8px}.reshoot a{color:#315d7d}
</style>"""


def wrap(body):
    return STYLE + '<div class="reshoot"><div class="eyebrow">INC-104 | Fictional incident | Oracle AI Agent Memory 26.8</div>' + body + '</div>'


def show(body):
    display(HTML(wrap(body)))


def _read(name):
    return json.loads((ROOT / "results" / name).read_text())


def _need(action):
    if action not in _completed:
        raise RuntimeError(f"Run the {action} step in this notebook session before displaying its result.")


def begin_take():
    """Forget which display steps completed, without changing saved data."""
    _completed.clear()


def run_step(action):
    if action not in {"early", "evolve", "compare", "handoff"}:
        raise ValueError("Choose an audience-facing incident step.")
    # The original runner starts a subprocess and raises on failure. Never fall
    # back to a previous take's JSON when the new command has failed.
    downstream = {"early": {"early", "evolve", "compare", "handoff"},
                  "evolve": {"evolve", "compare", "handoff"},
                  "compare": {"compare", "handoff"}, "handoff": {"handoff"}}
    _completed.difference_update(downstream[action])
    original.run_step(action)
    _completed.add(action)


def _card(record, *, planned=False):
    status = "prepared input" if planned else str(record["status"])
    historical = status.lower() == "invalid"
    return ('<div class="note ' + ('historical' if historical else '') + '">'
            + '<code>' + html.escape(record["id"]) + '</code>'
            + '<p class="status">' + html.escape(status)
            + (' | historical' if historical else '') + '</p><p>'
            + html.escape(record["content"]) + '</p></div>')


def show_scenario():
    records = sorted(NOTES, key=lambda n: n["time"])
    show('<h2>One incident, four prepared notes</h2>'
         '<p>These invented inputs describe the investigation. They have not been saved by this cell.</p>'
         '<div class="cards">' + ''.join(_card(n, planned=True) for n in records) + '</div>')


def show_early():
    _need("early")
    show('<h2>The first search</h2><p class="question">' + html.escape(QUERY)
         + '</p>' + ''.join(_card(n) for n in _read("01_early.json"))
         + '<p class="muted">Valid means an active memory record. The note itself says the explanation is unconfirmed.</p>')


def show_evolved():
    _need("evolve")
    records = sorted(_read("02_evolved.json"), key=lambda n: n["metadata"]["event_time"])
    show('<h2>The saved investigation notes</h2>' + original.notes_table(records))


def _collect(records):
    notes, edges = {}, set()
    def visit(record):
        notes[record["id"]] = record
        for edge in record.get("linked", []):
            key = (edge["source"], edge["target"], edge["relationship"])
            if key not in edges:
                edges.add(key)
                visit(edge["result"])
    for record in records:
        visit(record)
    return notes, sorted(edges)


def graph_markup(records):
    notes, edges = _collect(records)
    positions = {"INC104-EVIDENCE": (10, 15), "INC104-RECOVERY": (250, 15),
                 "INC104-DIAGNOSIS": (130, 230), "INC104-HYPOTHESIS": (130, 440)}
    labels = {"INC104-EVIDENCE": "Diagnostic evidence", "INC104-RECOVERY": "Recovery check",
              "INC104-DIAGNOSIS": "Confirmed diagnosis", "INC104-HYPOTHESIS": "Earlier hypothesis"}
    if set(notes) - set(positions):
        raise ValueError("The retrieved graph contains an unexpected note. Review it before choosing a layout.")
    svg = ['<svg viewBox="0 0 480 560" role="img" aria-label="Actual retrieved incident relationships"><defs><marker id="reshoot-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#486475"/></marker></defs>']
    for source, target, kind in edges:
        sx, sy = positions[source]; tx, ty = positions[target]
        x1, y1, x2, y2 = sx + 110, sy + 90, tx + 110, ty - 5
        xm, ym = (x1+x2)/2, (y1+y2)/2
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#486475" stroke-width="2" marker-end="url(#reshoot-arrow)"/>')
        svg.append(f'<rect x="{xm-42}" y="{ym-12}" width="100" height="25" fill="white"/><text x="{xm-35}" y="{ym+6}" font-size="17" fill="#334d5e">{html.escape(kind)}</text>')
    for key, note in notes.items():
        x, y = positions[key]
        status = str(note["status"])
        fill = "#fff2db" if status.lower() == "invalid" else "#edf4f8"
        svg.append(f'<rect x="{x}" y="{y}" width="220" height="90" rx="9" fill="{fill}" stroke="#bfcfda"/>')
        for dy, size, text in [(25,17,labels[key]), (49,13,key), (72,14,status + (" | historical" if status.lower() == "invalid" else ""))]:
            svg.append(f'<text x="{x+12}" y="{y+dy}" font-size="{size}" fill="#203644">{html.escape(text)}</text>')
    svg.append('</svg>')
    return ''.join(svg)


def comparison_markup(data):
    right = []
    for record in data["linked"]:
        right.append(_card(record))
        for edge in record.get("linked", []):
            right.append('<p class="relation"><code>' + html.escape(edge["source"])
                         + '</code> <b>' + html.escape(edge["relationship"]) + '</b> <code>'
                         + html.escape(edge["target"]) + '</code></p>' + _card(edge["result"]))
    return ('<h2>The same question, two searches</h2><p class="question">' + html.escape(data["question"])
            + '</p><p class="muted">Same saved data, user, incident filter and one direct match. The right side follows one relationship from each direct match.</p>'
            + '<div class="pair comparison"><section><h3>Direct matches | 0 hops</h3>'
            + ''.join(_card(n) for n in data["direct"]) + '</section><section><h3>Connected context | 1 hop</h3>'
            + ''.join(right) + '</section></div>')


def show_comparison():
    _need("compare")
    show(comparison_markup(_read("03_comparison.json")))


def show_graph():
    _need("compare")
    show('<h2>What the stored relationships mean</h2><div style="max-width:610px;margin:auto">'
         + graph_markup(_read("03_comparison.json")["linked"]) + '</div>'
         + '<p class="muted">supports = provides evidence for | supersedes = replaces the earlier explanation</p>')


def show_control():
    _need("compare")
    show('<h2>Give ordinary search more room</h2><p>Up to four direct matches, with zero relationship hops.</p>'
         + original.notes_table(_read("03_comparison.json")["larger_direct_limit"])
         + '<p class="muted">Inspect the actual result. This comparison does not measure answer accuracy or latency.</p>')


def answer_markup(answer):
    # Preserve all model words; only collapse blank lines around its headings.
    parts = []
    for paragraph in re.split(r"\n\s*\n", answer.strip()):
        heading = re.fullmatch(r"\*\*([^*]+)\*\*", paragraph.strip())
        if heading:
            parts.append('<h4>' + html.escape(heading.group(1)) + '</h4>')
        else:
            parts.append('<p>' + original.format_answer(paragraph).replace('\n', '<br>') + '</p>')
    return ''.join(parts)


def handoff_markup(data):
    notes, _ = _collect(data["retrieved"])
    ordered = sorted(notes.values(), key=lambda n: n.get("metadata", {}).get("event_time", ""))
    return ('<h2>The next engineer takes over</h2><p class="question">' + html.escape(data["question"])
            + '</p><p class="muted">New conversation: <code>' + html.escape(data["thread_id"])
            + '</code> | Saved records retrieved without replaying the earlier chat.</p>'
            + '<div class="three"><section><h3>Actual handoff answer</h3><div class="answer">'
            + answer_markup(data["answer"]) + '</div></section><section class="source-list"><h3>Retrieved source notes</h3>'
            + ''.join(_card(n) for n in ordered) + '</section><section><h3>Retrieved relationships</h3>'
            + graph_markup(data["retrieved"])
            + '<p class="muted">supports: provides evidence<br>supersedes: replaces the earlier explanation</p></section></div>'
            + '<p class="muted">Check each statement against its cited record. IDs alone do not establish accuracy.</p>')


def show_handoff_board():
    _need("handoff")
    show(handoff_markup(_read("04_handoff.json")))


def show_cited_note(note_id):
    _need("handoff")
    data = _read("04_handoff.json")
    notes, _ = _collect(data["retrieved"])
    if note_id not in notes:
        raise ValueError("That note was not returned in this handoff retrieval.")
    show('<h2>Inspect a cited source</h2>' + _card(notes[note_id]))


def update_message():
    module = ast.parse((ROOT / "automatic_update.py").read_text())
    for node in module.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MESSAGE" for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("The automatic update message was not found.")


def show_update_message():
    show('<h2>A follow-up message in a separate memory store</h2><p>'
         + html.escape(update_message()) + '</p>'
         + '<p class="muted">The incident lead supplies the confirmed finding. The configured extractor and linker process this message.</p>')


def run_auto():
    _completed.discard("automatic")
    original.run_auto()
    _completed.add("automatic")


def show_takeaways():
    show('<h2>What this example shows</h2><div class="cards">'
         '<div class="note"><h3>Saved information survives a new conversation</h3><p>The application retrieves the diagnosis, evidence, recovery and earlier history.</p></div>'
         '<div class="note"><h3>Relationships describe the correction</h3><p>A confirmed diagnosis replaces the old hypothesis. Evidence supports the current explanation.</p></div>'
         '<div class="note"><h3>The incident findings were supplied</h3><p>This fictional example demonstrates memory handling. It does not test whether an assistant can diagnose an outage.</p></div>'
         '<div class="note"><h3>Automatic output needs review</h3><p>Check the extracted text, relationship type, direction and source evidence. A new guess alone does not justify replacing an established diagnosis.</p></div></div>')


def show_get_started():
    show('<h2>Try the incident handoff</h2><p>Oracle\'s release article and the runnable code are linked in the video description.</p>'
         '<pre>pip install oracleagentmemory</pre><p class="muted">Follow the repository setup instructions for the pinned demo version: 26.8.0.</p>')
