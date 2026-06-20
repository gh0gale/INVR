import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# --- 1. THE UNIFIED SCHEMA (Highly Token Efficient) ---
class MemoryUpdate(BaseModel):
    # Episodic Layer
    episodic_summary: str = Field(
        description="A dense, 2-sentence summary of the conversation chunk. Focus on the core asset and the user's main questions."
    )
    # Semantic Layer (Delta Updates Only to save tokens)
    new_learned_concepts: List[str] = Field(
        description="List of financial jargon the user demonstrably understood in this chunk (e.g., ['CAGR', 'RSI']). Empty list if none."
    )
    portfolio_updates: Optional[str] = Field(
        description="Any explicit changes the user mentioned regarding their holdings, capital, or risk. Return null if none."
    )

# --- 2. THE EXTRACTION NODE ---
async def extract_memory_chunk(chat_chunk: str, current_semantic_profile: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("Running background extraction (Unified Pass)...")
    
    # We use a lower temp (0.0) for strict data extraction
    llm = ChatOllama(model="llama3.1", temperature=0.0)
    structured_llm = llm.with_structured_output(MemoryUpdate)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an efficient background memory extractor. 
        Analyze the provided chunk of conversation.
        
        CURRENT KNOWLEDGE STATE:
        {current_semantic_profile}
        
        DIRECTIVES:
        1. Summarize the chunk strictly into 2 sentences.
        2. Identify any *new* financial concepts the user grasped that are NOT in the current knowledge state.
        3. Identify any explicit portfolio/risk changes.
        """),
        ("human", "CONVERSATION CHUNK:\n{chat_chunk}")
    ])
    
    chain = prompt | structured_llm
    
    # Single optimized async call
    result = await chain.ainvoke({
        "current_semantic_profile": current_semantic_profile,
        "chat_chunk": chat_chunk
    })
    
    return result.model_dump()
    