import asyncio
import json
import httpx

# Mocking the payload that your frontend would automatically send
MOCK_ANALYSIS_CONTEXT = {
    "ticker": "RELIANCE.NS",
    "timeframe": "long_term",
    "verdict": "MONITOR",
    "llm_analysis": {
        "verdict": "MONITOR",
        "confidence_score": 72.5,
        "personalized_reasoning": [
            "INVESTMENT THESIS & PROFILE ALIGNMENT",
            "- Reliance Industries' long-term trajectory does not align with the user's goal of wealth growth, as evidenced by a revenue CAGR of only 0.0639% over the past five years.",
            "- The stock's risk profile is moderate, but its debt trajectory indicates leveraging, which may pose a threat to capital in the long term."
        ],
        "what_to_watch": [
            "Wait for structural recovery above the 200-week SMA (₹1304.17). -- Current: ₹1296.40. This level acts as a critical structural pivot because crossing it would indicate a reversal of the stock's downtrend.",
            "EPS compounding is too slow for a long-term hold. -- Current EPS growth rate: 0.0659% over the past five years, which is below the user's risk tolerance threshold.",
            "KEY RISK MONITOR: secular_trend -- The stock's secular trend is warning, indicating that the long-term trend may be weakening, threatening capital preservation."
        ]
    }
}

MOCK_USER_PROFILE = {
    "experience_level": "intermediate",
    "goal": "wealth growth",
    "risk_tolerance": "moderate",
    "portfolio": "100 shares of HDFCBANK, 50 shares of TCS"
}

async def test_tutor_stream(query: str):
    url = "http://127.0.0.1:8000/api/v1/tutor/chat/stream"
    
    payload = {
        "message": query,
        "session_id": "test_session_123",
        "analysis_context": MOCK_ANALYSIS_CONTEXT,
        "user_profile": MOCK_USER_PROFILE
    }
    
    print(f"\n[User]: {query}")
    print("[Tutor]: ", end="", flush=True)
    
    # We use a 60-second timeout because local LLM generation or news tools can take a moment to fire up
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                print(f"\nError: Server returned status code {response.status_code}")
                return
                
            # Iterate through the lines streamed over the network
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    
                    if data_str == "[DONE]":
                        print("\n\n--- Stream Completed ---")
                        break
                        
                    try:
                        data_json = json.loads(data_str)
                        if "token" in data_json:
                            # Print the token immediately without newline or spacing to simulate real-time typing
                            print(data_json["token"], end="", flush=True)
                        elif "error" in data_json:
                            print(f"\n[Backend Error]: {data_json['error']}")
                    except json.JSONDecodeError:
                        continue

if __name__ == "__main__":
    # Test cases targeting different semantic modes
    
    # Test Case 1: Mode 1 - Term Explainer
    asyncio.run(test_tutor_stream("any updates on reliance?"))
    
    # Test Case 2: Mode 4 - External Data/News Trigger
    # asyncio.run(test_tutor_stream("Is there any recent news on Reliance that impacts this layout?"))