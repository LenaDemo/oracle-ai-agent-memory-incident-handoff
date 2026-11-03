"""Invented incident notes for a teaching demo, not real production telemetry."""
USER_ID = "incident-demo-user"
AGENT_ID = "incident-handoff-assistant"
INCIDENT_ID = "INC-104"
STORE_ID = "INC_HANDOFF"
AUTO_STORE_ID = "INC_AUTO"
THREAD_ID = "inc104-investigation"
QUERY = "What is the confirmed cause of INC-104, and what evidence supports that diagnosis?"
NOTES = [
    {"id": "INC104-HYPOTHESIS", "time": "09:05", "label": "Earlier hypothesis",
     "content": "INC-104, 09:05. Initial hypothesis from the on-call engineer: the database may be overloaded, causing checkout requests to time out. This is unconfirmed and needs a diagnostic test."},
    {"id": "INC104-DIAGNOSIS", "time": "09:22", "label": "Confirmed diagnosis",
     "content": "INC-104, 09:22. Confirmed cause from the incident lead: the application's database connection pool is too small for the current request concurrency. Requests time out waiting for an available application connection. This replaces the earlier database-overload hypothesis."},
    {"id": "INC104-EVIDENCE", "time": "09:18", "label": "Diagnostic evidence",
     "content": "INC-104, 09:18. Diagnostic test: all 10 application-pool connections are occupied and requests are waiting for a connection. Database CPU is 24%, and the sampled queries finish normally once they obtain a connection. The incident team records this as evidence for application-pool exhaustion."},
    {"id": "INC104-RECOVERY", "time": "09:30", "label": "Recovery check",
     "content": "INC-104, 09:30. Recovery check from the on-call engineer: after changing the application connection-pool limit from 10 to 30 in this simulation, the same test workload completes without connection-wait timeouts. Continue watching connection-wait time and timeout rate. This supports the application-pool diagnosis."},
]
LINKS = [
    ("INC104-DIAGNOSIS", "INC104-HYPOTHESIS", "supersedes"),
    ("INC104-EVIDENCE", "INC104-DIAGNOSIS", "supports"),
    ("INC104-RECOVERY", "INC104-DIAGNOSIS", "supports"),
]
