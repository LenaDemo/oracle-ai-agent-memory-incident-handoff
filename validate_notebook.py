"""Run the full notebook against the real local database and save actual outputs."""
from pathlib import Path
import subprocess
import sys
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT = Path(__file__).resolve().parent
subprocess.run([sys.executable, "-m", "ipykernel", "install", "--sys-prefix",
                "--name", "oracle-incident-demo", "--display-name", "Oracle Incident Demo"], check=True)
subprocess.run([sys.executable, str(ROOT / "demo.py"), "reset"], cwd=ROOT, check=True)
notebook = nbformat.read(ROOT / "incident_handoff.ipynb", as_version=4)
runner = NotebookClient(notebook, timeout=300, kernel_name="oracle-incident-demo",
                        resources={"metadata": {"path": str(ROOT)}})
try:
    runner.execute()
finally:
    nbformat.write(notebook, ROOT / "results" / "incident_handoff.executed.ipynb")
html, _ = HTMLExporter().from_notebook_node(notebook)
(ROOT / "results" / "walkthrough.html").write_text(html)
print("Full notebook completed. Actual outputs saved in results/incident_handoff.executed.ipynb and walkthrough.html.")
