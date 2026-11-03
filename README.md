# Incident handoff with Oracle AI Agent Memory

A runnable notebook showing how an assistant can retrieve a corrected incident explanation, its evidence, and the history behind it in a new conversation. Built with **Oracle AI Agent Memory 26.8.0** and a free local Oracle database.

The story uses four invented notes about incident INC-104. The team first suspects database overload, then confirms that the application's connection pool is too small. The demo saves those findings, connects related notes, and retrieves them for the next engineer. It does not investigate a real outage.

## What you will see

1. Save an initial, unconfirmed hypothesis.
2. Save the confirmed explanation and two pieces of evidence. Create a relationship called `supersedes`, meaning the confirmed explanation replaces the old one, and relationships called `supports`, meaning these notes provide evidence for the explanation.
3. Compare direct retrieval with retrieval that follows one relationship from each direct match. Both searches use the same question, filters, and one-result limit.
4. Run a larger direct search as a control. Ordinary retrieval may already find enough current notes to answer.
5. Start a new conversation in a fresh Python process, retrieve the persisted notes, and generate a handoff without replaying the previous chat.
6. Run a separate example in which a model extracts an updated fact and proposes a relationship automatically.

The graph display is drawn from actual returned relationships. Generated answers and automatic relationships need to be checked against the saved notes.

## Requirements and cost

- Python 3.13.
- Docker Desktop or a compatible Docker installation.
- Ollama running locally.
- Enough disk and memory for the database, models, and notebook. The complete walkthrough was tested on an Apple Silicon Mac with 48 GB of RAM; this is a tested configuration, not a minimum requirement.

**The database is free.** The local models selected below do not require paid API calls. If you choose hosted AI models, their usage may incur separate charges. This project does not provision paid cloud infrastructure.

The tested stack uses Oracle AI Database 26ai Free 23.26.3.0.0 (arm64), Python 3.13.2, and Oracle AI Agent Memory 26.8.0. The image digest below is the tested image. Other platforms have not been verified with this exact setup. `requirements-lock.txt` records the full Python environment used for validation.

## Setup

Run these commands from the repository directory:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m ipykernel install --sys-prefix --name oracle-incident-demo --display-name "Oracle Incident Demo"
```

Start Docker and download the database image and local models:

```bash
docker pull container-registry.oracle.com/database/free@sha256:cf540c3fa190d7cffad08c491652ac07fc70314e510f6b87890449517d565e94
ollama pull nomic-embed-text
ollama pull llama3.2:3b
ollama create incident-demo-chat -f Modelfile
```

The local alias `incident-demo-chat` sets a 16,384-token context window, temperature 0, and seed 42. These are demo model choices, not required Oracle models. Start `ollama serve` if the model server is not already running.

Create the local configuration and start the dedicated database container:

```bash
.venv/bin/python setup_local.py start
docker logs -f oracle-incident-demo
```

Wait for `DATABASE IS READY TO USE!`, then press Ctrl-C to stop following the logs. The database keeps running. Create the dedicated application user:

```bash
.venv/bin/python setup_local.py user
```

The helper generates passwords in an owner-readable `.env` file. The repository excludes that file. The container listens on `127.0.0.1:1522` and stores data in its own Docker volume, `oracle-incident-demo-data`. The application uses the `incident_demo` database user and `INCIDENT_DEMO_TS` tablespace with a 500 MB limit. The setup creates this tablespace because the Free Lite image does not include a `USERS` tablespace.

## Run the notebook

Reset this demo's main dataset, then open the notebook:

```bash
.venv/bin/python demo.py reset
.venv/bin/python -m jupyterlab incident_handoff.ipynb
```

Choose the **Oracle Incident Demo** kernel and run the cells in order. Each step launches a fresh Python process. A failed command stops the cell instead of displaying old saved results.

The reset removes only this demo user's records in the main `INC_HANDOFF` memory store. It does not delete a database schema, container, or volume. Run it before repeating the complete walkthrough; the initial-data step refuses to overwrite an existing dataset.

## Run from the command line

As an alternative to the notebook, run:

```bash
.venv/bin/python demo.py reset
.venv/bin/python demo.py early
.venv/bin/python demo.py evolve
.venv/bin/python demo.py compare
.venv/bin/python demo.py handoff
.venv/bin/python automatic_update.py
.venv/bin/python demo.py verify
```

Actual outputs are written to the ignored `results/` directory. The automatic example uses a separate `INC_AUTO` store and resets only its own demo user each time. A missing or unexpected automatic link should be inspected as an actual model outcome.

To execute the whole notebook and save its outputs and an HTML copy:

```bash
.venv/bin/python validate_notebook.py
```

This command first resets the main demo dataset. To produce a readable HTML view of an already completed run without making new database or model calls:

```bash
.venv/bin/python render_results.py
```

The resulting `results/review_preview.html` is explicitly labeled as saved output.

## Files

| File | Purpose |
| --- | --- |
| `incident_handoff.ipynb` | Step-by-step walkthrough with result tables, a relationship diagram, and a handoff card |
| `demo.py` | Database writes, explicit relationships, searches, fresh conversation, and verification |
| `fixtures.py` | Four fictional notes and the intended relationship directions |
| `automatic_update.py` | Separate automatic extraction and relationship example |
| `notebook_view.py` | Displays the actual saved results |
| `setup_local.py` | Dedicated local database and application-user setup |
| `validate_notebook.py` | Runs the complete notebook against the database and saves actual outputs |
| `render_results.py` | Displays a completed run without rerunning it |
| `SOURCES.md` | Official documentation and boundaries of the example |

## Verification and limits

The complete notebook passed locally on November 3, 2026. Eight checks covered persisted records, lifecycle status, retrieval filters, recovery context, and relationship types and directions. The handoff and automatic update were also reviewed against their retrieved records. This repository includes a clean notebook; rerun it to produce your own outputs.

The replaced hypothesis is stored with an invalid lifecycle status and can still appear as connected history. It is excluded from the direct matches in the demonstrated search. The comparison caps each search at one direct match to make relationship traversal visible; it is not a retrieval-quality, speed, or cost benchmark. The larger direct-search control makes that limitation visible.

Model-generated text and automatic relationships can vary. Check the explanation, evidence, historical context, recovery status, and citations against the returned notes. A citation alone does not establish factual accuracy. The user and incident filters are application checks, not a complete multi-tenant security design. All measurements in the incident story are fictional teaching data.

## Stop and resume

```bash
docker stop oracle-incident-demo
docker start oracle-incident-demo
```

The named volume retains the data. Wait for database readiness after restarting. Reset the demo records only when starting another complete run.

## Troubleshooting

- **Cannot connect:** confirm Docker is running, the database is ready, and Ollama is listening locally.
- **Existing demo records:** run the documented reset before repeating the walkthrough.
- **Different retrieval order:** inspect `results/03_comparison.json`. Compare the actual direct match and connected notes, keeping the question, filters, and limit identical.
- **Missing historical text:** keep both `include_invalid_results` and `show_status` enabled in the formatter.
- **Unexpected automatic relationship or answer:** inspect the saved output and logs, adjust the instructions if needed, and rerun. Do not replace model output by hand and present it as automatic.
- **Different embedding model:** review query/document prefixes and vector dimensions. Use a new dedicated memory store rather than mixing embeddings from different models. The reset removes records, not the store schema.

See [the official sources](SOURCES.md) for the Oracle APIs used in this demonstration.
