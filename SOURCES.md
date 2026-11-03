# Official sources and demo choices

Checked November 3, 2026. Product references are Oracle sources. The fictional incident and presentation are original demo choices.

- [Oracle's release article on graph-aware memory, image memory, and enterprise controls](https://blogs.oracle.com/developers/whats-new-in-oracle-ai-agent-memory-graph-aware-retrieval-image-memory-and-enterprise-controls): release context.
- [Oracle's linked-memory guide](https://docs.oracle.com/en/database/oracle/agent-memory/26.8/guide/int-graph-memory.html): explicit and automatic relationships, lifecycle status, search hops, linked history, and formatting.
- [Oracle's agent-memory Python API](https://docs.oracle.com/en/database/oracle/agent-memory/26.8/guide/api/agentmemory.html): client, add_memory, link_records, search filters, new threads, extraction configuration, and scoped cleanup.
- [Oracle's thread API](https://docs.oracle.com/en/database/oracle/agent-memory/26.8/guide/api/thread.html): adding messages and extraction behavior.
- [Oracle's model adapter reference](https://docs.oracle.com/en/database/oracle/agent-memory/26.8/guide/api/models.html): configurable embedders and generation models. Our local model combination is a demo choice, not a claim that Oracle has validated that exact combination.
- [Oracle's local database setup guide](https://docs.oracle.com/en/database/oracle/agent-memory/26.8/guide/run-locally.html): official Free Lite container, dedicated application user, persistence, and connection setup.
- [Oracle AI Database Free](https://www.oracle.com/database/free/): free database offering. This demo runs locally; any optional hosted AI model charges are separate.
- [Oracle's memory-evolution reference notebook](https://github.com/oracle-devrel/oracle-ai-developer-hub/blob/main/notebooks/oracle_agent_memory_evolution.ipynb): concept reference. This demo implements its own incident story and explicitly disables automatic linking in the manual phase.

## Distinctions the demo preserves

- Stored `INVALID` is a lifecycle state. Our application presents the replaced hypothesis as historical.
- The SDK changes target status when a relationship called `supersedes` is recorded. Our code does not merely paint an "outdated" badge onto a still-current record.
- The ordinary and graph-expanded searches see the same updated database. Their one-result limit is disclosed. A larger-limit ordinary search is also shown.
- The graph display reads the relationships returned by search; it does not manufacture a graph from the planned links.
- The new conversation uses a separate Python process and database connection. It retrieves persisted notes and passes that context to a model. It does not replay the earlier transcript.
- The handoff prompt requests citations, but a citation-presence check cannot establish factual accuracy. Human review must compare the answer with the retrieved notes.
- Automatic extraction is a separate attempt in its own store. Its result is reported as observed, not guaranteed.
- Scope checks test this application's filters, not a complete multi-tenant security design.
- Pool sizes, CPU percentage, timestamps, and recovery details are invented teaching data. They are not a benchmark, measured outage, or database-tuning recommendation.
