import os
from dotenv import load_dotenv
from supabase import create_client, Client
from app.pipeline.memory_graph import extract_memory_chunk

# 1. Add override=True to force Python to ignore the old cached key
load_dotenv(override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# 2. The Sanity Check
# (Key logging removed for security)

# 3. Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async def manage_session_memory(session_id: str, user_id: str, user_msg: str, ai_msg: str, topic_changed: bool = False):
    """Handles chat persistence and chunked semantic extraction."""
    print(f"  [DB] Syncing chat state for session {session_id}...")
    
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
        print("  [Memory] Watermark reached. Triggering Chunked Eviction...")
        
        chunk_to_summarize = working_mem[:10]
        chunk_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in chunk_to_summarize])
        
        profile_res = supabase.table("user_profiles").select("semantic_profile").eq("id", user_id).execute()
        current_semantic = profile_res.data[0].get("semantic_profile", {}) if profile_res.data else {}

        # Run extraction
        extracted_data = await extract_memory_chunk(chunk_text, current_semantic)
        
        # Patch User Profile
        if extracted_data["new_learned_concepts"] or extracted_data["portfolio_updates"]:
            current_semantic["learned_concepts"] = list(set(current_semantic.get("learned_concepts", []) + extracted_data["new_learned_concepts"]))
            if extracted_data["portfolio_updates"]:
                current_semantic["latest_portfolio_note"] = extracted_data["portfolio_updates"]
            
            supabase.table("user_profiles").update({"semantic_profile": current_semantic}).eq("id", user_id).execute()
            print("  [DB] Semantic Profile Patched.")

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
        supabase.table("chat_sessions").update({"working_memory": working_mem}).eq("session_id", session_id).execute()