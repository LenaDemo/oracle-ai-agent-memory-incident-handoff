"""Readable notebook displays generated only from actual saved command results."""
import html
import json
import re
from pathlib import Path
import subprocess
import sys
from IPython.display import HTML, display

ROOT = Path(__file__).resolve().parent
CSS = """<style>
.inc-demo{font:16px/1.55 -apple-system,BlinkMacSystemFont,Arial,sans-serif;color:#1d252d;background:#fff;padding:24px;border:1px solid #dce1e5;border-radius:12px}
.inc-demo h2{font-size:24px;margin:0 0 18px}.inc-demo h3{font-size:19px;margin:0 0 10px}.inc-demo .eyebrow{color:#67727d;font-size:12px;text-transform:uppercase;letter-spacing:1.4px;margin-bottom:10px}
.inc-demo table{border-collapse:collapse;width:100%;font:inherit}.inc-demo th{text-align:left;background:#f0f3f5;font-size:13px}.inc-demo td,.inc-demo th{padding:12px;border-bottom:1px solid #dce1e5;vertical-align:top}.inc-demo code{font-size:12px;white-space:normal;overflow-wrap:anywhere}
.inc-demo .grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.inc-demo .card{border:1px solid #dce1e5;border-radius:8px;padding:16px;margin-bottom:12px}.inc-demo .historical{background:#faf5eb}.inc-demo .pill{font-size:11px;font-weight:700;letter-spacing:.5px;color:#4d6169}.inc-demo p{margin:8px 0}.inc-demo .answer{white-space:pre-wrap;font:inherit}.inc-demo .muted{font-size:13px;color:#66727e}.inc-demo svg{width:100%;height:auto}
</style>"""


def show(body):
    display(HTML(CSS + '<div class="inc-demo"><div class="eyebrow">INC-104 | Fictional incident | Oracle AI Agent Memory 26.8</div>' + body + '</div>'))


def read(name):
    return json.loads((ROOT / "results" / name).read_text())


def card(note):
    historic = str(note["status"]).lower() == "invalid"
    return (f'<div class="card {"historical" if historic else ""}"><code>{html.escape(note["id"])}</code>'
            f'<p class="pill">{html.escape(str(note["status"]))}{" | HISTORICAL" if historic else ""}</p>'
            f'<p>{html.escape(note["content"])}</p></div>')


def tree(note):
    body = card(note)
    for edge in note["linked"]:
        body += (f'<p class="muted">Stored relationship: <code>{html.escape(edge["source"])}</code> '
                 f'<b>{html.escape(edge["relationship"])}</b> <code>{html.escape(edge["target"])}</code></p>' + tree(edge["result"]))
    return body


def notes_table(records):
    rows = ''.join(f'<tr><td><code>{html.escape(n["id"])}</code></td><td>{html.escape(str(n["status"]))}</td><td>{html.escape(n["content"])}</td></tr>' for n in records)
    return '<table><tr><th>Note ID</th><th>Status</th><th>Saved note</th></tr>' + rows + '</table>'


def show_early():
    show('<h2>The first hypothesis</h2>' + ''.join(card(n) for n in read("01_early.json")))


def show_evolved():
    show('<h2>The investigation moves on</h2>' + notes_table(read("02_evolved.json")))


def show_comparison():
    data = read("03_comparison.json")
    show('<h2>Same question. Same notes.</h2><p>' + html.escape(data["question"]) + '</p>'
         '<p class="muted">One direct match in both searches. The right side also follows one relationship.</p>'
         '<div class="grid"><section><h3>Direct search | 0 hops</h3>' + ''.join(tree(n) for n in data["direct"]) +
         '</section><section><h3>Connected notes | 1 hop</h3>' + ''.join(tree(n) for n in data["linked"]) + '</section></div>')


def show_control():
    data = read("03_comparison.json")
    show('<h2>What if ordinary search has more room?</h2><p class="muted">Up to four direct matches; no relationship expansion.</p>' + notes_table(data["larger_direct_limit"]))


def show_graph():
    data = read("03_comparison.json")
    edges = {}
    def walk(node):
        for edge in node["linked"]:
            edges[(edge["source"],edge["target"],edge["relationship"])] = edge
            walk(edge["result"])
    for node in data["linked"]:
        walk(node)
    # The presentation layout is fixed, but edges are drawn only when returned by the real search.
    positions = {"INC104-EVIDENCE":(30,30), "INC104-RECOVERY":(530,30),
                 "INC104-DIAGNOSIS":(280,220), "INC104-HYPOTHESIS":(280,430)}
    labels = {"INC104-EVIDENCE":"Diagnostic test", "INC104-RECOVERY":"Recovery check",
              "INC104-DIAGNOSIS":"Confirmed diagnosis", "INC104-HYPOTHESIS":"Earlier hypothesis"}
    svg = '<svg viewBox="0 0 840 550" role="img" aria-label="Relationships returned by the database search"><defs><marker id="inc-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#4c6473"/></marker></defs>'
    for source,target,kind in edges:
        sx,sy = positions[source]; tx,ty = positions[target]
        x1,y1,x2,y2 = sx+140,sy+80,tx+140,ty-4
        svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#4c6473" stroke-width="2" marker-end="url(#inc-arrow)"/>'
        svg += f'<rect x="{(x1+x2)/2+8}" y="{(y1+y2)/2-18}" width="105" height="26" rx="4" fill="white"/>'
        svg += f'<text x="{(x1+x2)/2+12}" y="{(y1+y2)/2}" font-size="15" fill="#344651">{html.escape(kind)}</text>'
    for key,(x,y) in positions.items():
        fill = "#faf5eb" if key.endswith("HYPOTHESIS") else "#f0f4f6"
        svg += f'<rect x="{x}" y="{y}" width="280" height="80" rx="9" fill="{fill}" stroke="#ccd5dc"/>'
        svg += f'<text x="{x+16}" y="{y+31}" font-size="18" fill="#20313f">{labels[key]}</text><text x="{x+16}" y="{y+58}" font-size="12" fill="#67727d">{key}</text>'
    svg += '</svg>'
    show('<h2>How the saved notes relate</h2>' + svg + '<p class="muted">supports = provides evidence for | supersedes = replaces as the current explanation</p>')


def format_answer(answer):
    # Escape all model text before adding only simple presentation markup.
    escaped = html.escape(answer)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[(INC104-[A-Z]+)\]", r"<code>[\1]</code>", escaped)
    return escaped


def show_handoff():
    data = read("04_handoff.json")
    show('<h2>A new conversation</h2><p class="muted">' + html.escape(data["thread_id"]) + '</p><p><b>' + html.escape(data["question"]) + '</b></p><div class="card answer">' + format_answer(data["answer"]) + '</div><p class="muted">Actual model output. Check each statement against its cited note.</p>')


def run_step(action):
    if action not in {"early","evolve","compare","handoff","verify"}:
        raise ValueError("Unsupported notebook step")
    result = subprocess.run([sys.executable,str(ROOT / "demo.py"),action], cwd=ROOT, capture_output=True,text=True)
    (ROOT / "results" / f"{action}.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Step {action} failed. Inspect results/{action}.log before recording; no saved output displayed.")
    return result.stdout


def run_auto():
    result = subprocess.run([sys.executable,str(ROOT / "automatic_update.py")],cwd=ROOT,capture_output=True,text=True)
    (ROOT / "results" / "automatic.log").write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError("Automatic extraction failed. Inspect results/automatic.log; do not substitute a manual link.")
    show_automatic()


def show_automatic():
    data = read("05_automatic.json")
    links = ''.join('<p><code>' + html.escape(source) + '</code> <b>' + html.escape(kind) + '</b> <code>' + html.escape(target) + '</code></p>' for source, target, kind in data["stored_relationships"])
    new_count = data["automatic_new_notes"]
    link_count = len(data["stored_relationships"])
    count = f'{new_count} new note{"" if new_count == 1 else "s"} | {link_count} stored relationship{"" if link_count == 1 else "s"}'
    show('<h2>Automatic update | separate demo records</h2><p>' + html.escape(data["message"]) + '</p><h3>' + count + '</h3>' + ''.join(card(n) for n in data["results"]) + '<h3>Stored relationships</h3>' + (links or '<p>No relationship was created.</p>') + '<p class="muted">Each saved record appears once here. Model-generated relationships require review. No manual links were added in this example.</p>')
