import logging
from langchain_ollama import OllamaEmbeddings
from app.database import supabase_admin
from app.config import settings

logger = logging.getLogger(__name__)

# We use the local model you already pulled to calculate the 768-dimensional vectors
embedder = OllamaEmbeddings(model="nomic-embed-text")

def upsert_ledger_to_vectorstore(log_id: str, ticker: str, timeframe: str, verdict: str, reasoning_list: list):
    """Generates an embedding locally and saves it to the Supabase pgvector table."""
    if not supabase_admin:
        logger.error("Supabase client offline. Skipping vector upsert.")
        return

    try:
        data_to_insert = []
        for reasoning_item in reasoning_list:
            if not reasoning_item.strip():
                continue
            
            # 1. Generate the vector array mathematically using your local Ollama
            embedding = embedder.embed_query(reasoning_item)
            
            # 2. Prepare for Supabase pgvector
            data_to_insert.append({
                "log_id": log_id,
                "ticker": ticker.upper(),
                "timeframe": timeframe,
                "verdict": verdict,
                "reasoning_text": reasoning_item,
                "embedding": embedding
            })
            
        if data_to_insert:
            supabase_admin.table("ledger_embeddings").insert(data_to_insert).execute()
            logger.info(f"Successfully embedded {len(data_to_insert)} prediction chunks for {ticker} into Supabase Vector DB.")
        
    except Exception as e:
        logger.error(f"Failed to upsert vector to Supabase: {str(e)}")

def upsert_static_content_to_vectorstore(source_type: str, content_list: list):
    """Generates embeddings for static content and saves them to the Supabase pgvector table under the STATIC ticker."""
    if not supabase_admin:
        logger.error("Supabase client offline. Skipping static vector upsert.")
        return

    try:
        data_to_insert = []
        for i, text in enumerate(content_list):
            if not text.strip():
                continue
            
            embedding = embedder.embed_query(text)
            
            data_to_insert.append({
                "log_id": f"static_{source_type}_{i}",
                "ticker": "STATIC",
                "timeframe": source_type, # e.g. "gate_threshold", "educational"
                "verdict": "N/A",
                "reasoning_text": text,
                "embedding": embedding
            })
            
        if data_to_insert:
            supabase_admin.table("ledger_embeddings").insert(data_to_insert).execute()
            logger.info(f"Successfully embedded {len(data_to_insert)} {source_type} chunks into Supabase Vector DB.")
        
    except Exception as e:
        logger.error(f"Failed to upsert static vector to Supabase: {str(e)}")

from opentelemetry import trace
async def query_ledger_history(ticker: str, n_results: int = None, routed_mode: str = None) -> str:
    """Retrieves past algorithmic predictions and static educational content using cosine similarity."""
    if not settings.USE_RETRIEVAL_RAG:
        return "Historical context retrieval is disabled via config."
        
    if not supabase_admin:
        return "Historical database offline."

    if n_results is None:
        n_results = settings.RETRIEVAL_TOP_K

    try:
        if routed_mode:
            query_text = f"Historical algorithmic analysis and predictions for {ticker} focusing on {routed_mode}"
        else:
            query_text = f"Historical algorithmic analysis and predictions for {ticker}"
            
        query_embedding = await embedder.aembed_query(query_text)
        
        queries_to_run = [{"match_ticker": ticker.upper(), "source_type": "ledger_history"}]
        if routed_mode == "scenario":
            queries_to_run.append({"match_ticker": "STATIC", "source_type": "gate_threshold"})
        elif routed_mode == "definition" or routed_mode == "fallback":
            queries_to_run.append({"match_ticker": "STATIC", "source_type": "educational"})
            
        combined_data = []
        actual_sources = []
        
        for q in queries_to_run:
            response = supabase_admin.rpc(
                "match_ledger_embeddings",
                {
                    "query_embedding": query_embedding,
                    "match_ticker": q["match_ticker"],
                    "match_threshold": 0.3,
                    "match_count": n_results
                }
            ).execute()
            if response.data:
                if q["match_ticker"] == "STATIC":
                    filtered_data = [item for item in response.data if item['timeframe'] == q["source_type"]]
                    combined_data.extend(filtered_data)
                    if filtered_data and q["source_type"] not in actual_sources:
                        actual_sources.append(q["source_type"])
                else:
                    combined_data.extend(response.data)
                    if q["source_type"] not in actual_sources:
                        actual_sources.append(q["source_type"])
                        
        span = trace.get_current_span()
        
        if not combined_data:
            if span and span.is_recording():
                span.set_attribute("retrieval.chunk_count", 0)
                span.set_attribute("retrieval.source_types", [])
            return "No historical ledger data found for this ticker."
            
        history_blocks = []
        for item in combined_data:
            block = f"Timeframe/Source: {item['timeframe']} | Verdict: {item['verdict']}\nReasoning/Content: {item['reasoning_text']}"
            history_blocks.append(block)
            
        if span and span.is_recording():
            span.set_attribute("retrieval.chunk_count", len(combined_data))
            span.set_attribute("retrieval.source_types", actual_sources)
            
        return "\n\n---\n\n".join(history_blocks)
        
    except Exception as e:
        logger.error(f"Supabase Vector Query Error: {str(e)}")
        return "Failed to retrieve historical data."