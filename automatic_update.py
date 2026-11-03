"""One automatic extraction attempt in a separate store. Never adds manual links."""
import json
from oracleagentmemory.core import MemoryExtractionConfig, MemoryExtractionMode, MemoryLinkExtractionMode
from demo import connect, pack, pretty, save
from fixtures import AUTO_STORE_ID, AGENT_ID, NOTES, QUERY

AUTO_USER = "incident-automatic-demo-user"
AUTO_THREAD = "inc104-automatic-update"
MESSAGE = (
    "Correction to incident INC-104: the incident lead has confirmed that the application's "
    "database connection pool is too small for the workload. Requests time out while waiting "
    "for a connection. This confirmed diagnosis replaces our earlier database-overload hypothesis. "
    "Database overload is no longer our current diagnosis. Remember only the confirmed current diagnosis "
    "for the next engineer's handoff."
)


def run():
    config = MemoryExtractionConfig(
        extract_memories=True,
        extraction_mode=MemoryExtractionMode.INLINE,
        memory_extraction_frequency=1,
        memory_extraction_window=-1,
        enable_context_summary=False,
        memory_extraction_token_limit=12000,
        memory_link_extraction_token_limit=12000,
        memory_link_extraction_mode=MemoryLinkExtractionMode.POST_EXTRACTION,
        memory_extraction_custom_instructions=(
            "Extract exactly one fact from the latest message: the confirmed current incident diagnosis, "
            "including the incident ID. Do not also save it as a general memory, guideline, or preference. "
            "The previous database-overload hypothesis has been replaced; do not extract it as a current fact. "
            "Do not save the request to remember or create a handoff as a separate memory. "
            "The message describes a fictional incident and a human-confirmed finding."
        ),
        memory_link_extraction_custom_instructions=(
            "When a new human-confirmed incident diagnosis explicitly replaces an earlier hypothesis "
            "for the same incident, the new diagnosis supersedes the old hypothesis. "
            "Use the new fact as the source and the earlier hypothesis as the target. "
            "An unconfirmed disagreement alone would only contradict the earlier hypothesis."
        ),
    )
    with connect(AUTO_STORE_ID, create=True, extraction=config, with_llm=True) as (client, _, _):
        # Reset only the isolated auto-example user, making every invocation a declared fresh attempt.
        client.delete_user(AUTO_USER, cascade=True)
        thread = client.create_thread(thread_id=AUTO_THREAD, user_id=AUTO_USER, agent_id=AGENT_ID,
                                      metadata={"demo": True, "incident_id": "INC-104"})
        client.add_memory(NOTES[0]["content"], memory_type="fact", memory_id="AUTO-OLD-HYPOTHESIS",
                           user_id=AUTO_USER, agent_id=AGENT_ID, thread_id=AUTO_THREAD,
                           autonomous_linking=False, metadata={"demo": True, "incident_id": "INC-104"})
        thread.add_messages([{"role": "user", "content": MESSAGE}])
        results = client.search(QUERY, user_id=AUTO_USER, agent_id=AGENT_ID, max_results=20,
                                 record_types=["fact", "memory", "preference", "guideline"],
                                 include_invalid_results=True, num_hops=2, max_linked_results=20)
        packed = [pack(r) for r in results]
        links = set()
        def walk(record):
            for edge in record["linked"]:
                links.add((edge["source"], edge["target"], edge["relationship"]))
                walk(edge["result"])
        for record in packed:
            walk(record)
        data = {"message": MESSAGE, "results": packed, "stored_relationships": sorted(links),
                "manual_links_created": 0, "automatic_new_notes": sum(r.id != "AUTO-OLD-HYPOTHESIS" for r in results),
                "review_required": True}
        save("05_automatic.json", data)
        print(pretty(results))
        print("\nActual relationships:", json.dumps(sorted(links)))
        print("No manual links were added. Review the generated text and link direction.")


if __name__ == "__main__":
    run()
