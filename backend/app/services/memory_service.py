import logging
from app.database import supabase_admin as supabase
from app.pipeline.memory_graph import extract_memory_chunk
# NEW: Import tracer
from opentelemetry import trace

logger = logging.getLogger(__name__)
# NEW: Get the tracer for this module
tracer = trace.get_tracer(__name__)

async def manage_session_memory(session_id: str, user_id: str, user_msg: str, ai_msg: str, topic_changed: bool = False):
    """Handles chat persistence and chunked semantic extraction."""
    # NEW: Wrap the entire execution in a span
    with tracer.start_as_current_span("manage_session_memory") as span:
        # Tag the span with attributes
        span.set_attribute("session.id", session_id)
        span.set_attribute("user.id", user_id)
        span.set_attribute("memory.topic_changed_flag", topic_changed)
        
        try:
            logger.info("Syncing chat state for session %s", session_id)
            
            # 1. Fetch current chat session
            session_res = supabase.table("chat_sessions").select("*").eq("session_id", session_id).execute()
            
            if not session_res.data:
                new_session = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "working_memory": [],
                    "episodic_memory": []
                }
                supabase.table("chat_sessions").insert(new_session).execute()
                session_data = new_session
            else:
                session_data = session_res.data[0]

            # 2. Append the newest message pair
            working_mem = session_data.get("working_memory", [])
            working_mem.append({"role": "human", "content": user_msg})
            working_mem.append({"role": "ai", "content": ai_msg})

            # 3. CHUNKED EVICTION LOGIC
            if len(working_mem) >= 16 or topic_changed:
                logger.info("Memory watermark reached. Triggering Chunked Eviction...")
                # Log an event in the span for visibility
                span.add_event("triggering_chunked_eviction")
                
                chunk_to_summarize = working_mem[:10]
                chunk_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chunk_to_summarize])
                
                profile_res = supabase.table("user_profiles").select("semantic_profile").eq("id", user_id).execute()
                current_semantic = profile_res.data[0].get("semantic_profile", {}) if profile_res.data else {}

                # Run extraction
                extracted_data = await extract_memory_chunk(chunk_text, current_semantic)
                
                # Tag span with extraction details
                span.set_attribute("memory.extracted.new_concepts_count", len(extracted_data.get("new_learned_concepts", [])))
                span.set_attribute("memory.extracted.portfolio_updates", bool(extracted_data.get("portfolio_updates")))

                # Patch User Profile
                if extracted_data["new_learned_concepts"] or extracted_data["portfolio_updates"]:
                    current_semantic["learned_concepts"] = list(set(current_semantic.get("learned_concepts", []) + extracted_data["new_learned_concepts"]))
                    if extracted_data["portfolio_updates"]:
                        current_semantic["latest_portfolio_note"] = extracted_data["portfolio_updates"]
                    
                    supabase.table("user_profiles").update({"semantic_profile": current_semantic}).eq("id", user_id).execute()
                    logger.info("Semantic Profile Patched.")

                # Update Session Data
                episodic = session_data.get("episodic_memory", [])
                episodic.append(extracted_data["episodic_summary"])
                working_mem = working_mem[10:]
                
                supabase.table("chat_sessions").update({
                    "working_memory": working_mem,
                    "episodic_memory": episodic
                }).eq("session_id", session_id).execute()
                
            else:
                # Standard fast-save
                span.add_event("fast_save_working_memory")
                supabase.table("chat_sessions").update({"working_memory": working_mem}).eq("session_id", session_id).execute()
                
            span.set_status(trace.Status(trace.StatusCode.OK))
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.error(f"Memory Service Error: {str(e)}")
            raise # Re-raise if necessary or handle

# Rough token estimate. Four characters per token is the usual English
# approximation and is close enough to keep a context window intact without
# pulling in a tokenizer dependency for a job that only needs a ceiling.
CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str) -> int:
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def trim_to_token_budget(messages: list[dict], budget_tokens: int) -> list[dict]:
    """Keeps the most recent messages that fit inside the budget.

    Audit finding NEW-LLM-03: history was capped by message count, so ten long
    turns could still overflow the window. Walks backwards so the newest turn is
    never the one dropped.
    """
    kept: list[dict] = []
    used = 0
    for message in reversed(messages or []):
        cost = _estimate_tokens(str(message.get("content", "")))
        if used + cost > budget_tokens and kept:
            break
        kept.append(message)
        used += cost
    kept.reverse()
    return kept


async def load_working_memory(session_id: str, budget_tokens: int = 2400) -> list[dict]:
    """Recent turns for one chat session, newest-last, within a token budget.

    Audit finding NEW-LLM-01: `manage_session_memory` has always written this
    column, but nothing ever read it back, so every tutor question was answered
    with no memory of the previous one. Returns [] on any failure: losing history
    degrades an answer, while raising here would break the whole reply.
    """
    if not session_id or not supabase:
        return []
    try:
        res = (
            supabase.table("chat_sessions")
            .select("working_memory")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            return []
        history = res.data[0].get("working_memory") or []
        usable = [
            m for m in history
            if isinstance(m, dict) and m.get("role") in ("human", "ai") and m.get("content")
        ]
        return trim_to_token_budget(usable, budget_tokens)
    except Exception as e:
        logger.warning("Could not load working memory for %s: %s", session_id, e)
        return []
