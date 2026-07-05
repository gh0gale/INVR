import logging
from langchain_ollama import OllamaEmbeddings
from app.database import supabase_admin

logger = logging.getLogger(__name__)

# We use the local model you already pulled to calculate the 768-dimensional vectors
embedder = OllamaEmbeddings(model="nomic-embed-text")

def upsert_ledger_to_vectorstore(log_id: str, ticker: str, timeframe: str, verdict: str, reasoning_list: list):
    """Generates an embedding locally and saves it to the Supabase pgvector table."""
    if not supabase_admin:
        logger.error("Supabase client offline. Skipping vector upsert.")
        return

    try:
        # Flatten the reasoning array into a single text block
        reasoning_text = " ".join(reasoning_list)
        
        # 1. Generate the vector array mathematically using your local Ollama
        embedding = embedder.embed_query(reasoning_text)
        
        # 2. Push to Supabase pgvector
        data = {
            "log_id": log_id,
            "ticker": ticker.upper(),
            "timeframe": timeframe,
            "verdict": verdict,
            "reasoning_text": reasoning_text,
            "embedding": embedding
        }
        supabase_admin.table("ledger_embeddings").insert(data).execute()
        logger.info(f"Successfully embedded prediction for {ticker} into Supabase Vector DB.")
        
    except Exception as e:
        logger.error(f"Failed to upsert vector to Supabase: {str(e)}")

async def query_ledger_history(ticker: str, n_results: int = 2) -> str:
    """Retrieves past algorithmic predictions for a specific ticker using cosine similarity."""
    if not supabase_admin:
        return "Historical database offline."

    try:
        # Embed the query
        query_text = f"Historical algorithmic analysis and predictions for {ticker}"
        query_embedding = await embedder.aembed_query(query_text)
        
        # Call the Supabase RPC (Remote Procedure Call) function we created in SQL
        response = supabase_admin.rpc(
            "match_ledger_embeddings",
            {
                "query_embedding": query_embedding,
                "match_ticker": ticker.upper(),
                "match_threshold": 0.3, # Adjust to make search more or less strict
                "match_count": n_results
            }
        ).execute()
        
        if not response.data:
            return "No historical ledger data found for this ticker."
            
        history_blocks = []
        for item in response.data:
            block = f"Timeframe: {item['timeframe']} | Verdict: {item['verdict']}\nReasoning: {item['reasoning_text']}"
            history_blocks.append(block)
            
        return "\n\n---\n\n".join(history_blocks)
        
    except Exception as e:
        logger.error(f"Supabase Vector Query Error: {str(e)}")
        return "Failed to retrieve historical data."