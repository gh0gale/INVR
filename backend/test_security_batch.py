import urllib.request
import json

def run_tests():
    payload = {
        "ticker": "RELIANCE",
        "timeframe": "long_term",
        "user_profile": {
            "experience_level": "advanced",
            "goal": "growth",
            "risk_tolerance": "high",
            "available_capital": 500000.0
        }
    }
    
    req2 = urllib.request.Request(
        "http://localhost:8000/api/v1/analytics/process", 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req2, timeout=60.0) as response:
            data = json.loads(response.read().decode())
            
            llm = data.get("llm_analysis", {})
            has_disclaimer = "regulatory_disclaimer" in llm
            
            print(f"Success: {data.get('success')}")
            print(f"Verdict: {data.get('verdict')}")
            print(f"Disclaimer Present: {has_disclaimer}")
            
            if has_disclaimer:
                print(f"Disclaimer Text: {llm['regulatory_disclaimer']}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run_tests()
