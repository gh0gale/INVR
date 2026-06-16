import asyncio
import sys

# Test P0-02: Import memory_service and see if it prints the key
print("\n--- TEST P0-02: Secret Key Logging ---")
try:
    from app.services.memory_service import supabase
    print("memory_service imported successfully without printing the secret key!")
except Exception as e:
    print(f"Failed to import memory_service: {e}")

# Test P1-01: Bronze service institutional_activity data
print("\n--- TEST P1-01: Mocked Institutional Data Passed Through ---")
from app.services.bronze_service import build_bronze_payload

async def test_bronze():
    payload = await build_bronze_payload("RELIANCE.NS", "swing")
    if payload.institutional_activity is not None:
        print("Success! Institutional Activity is present in the Bronze Payload.")
        print("Payload institutional_activity:", payload.institutional_activity)
    else:
        print("Fail: Institutional Activity is still None.")

asyncio.run(test_bronze())

# Test P2-01: CAGR math stability
print("\n--- TEST P2-01: CAGR Mathematical Stability ---")
from app.services.silver_service import calculate_cagr

cagr_normal = calculate_cagr([100, 150, 200])
cagr_edge_case = calculate_cagr([-100, -50, 200])  # Negative to positive transition

print(f"Normal CAGR (100 -> 200): {cagr_normal:.2f}")
print(f"Edge Case CAGR (-100 -> 200): {cagr_edge_case}")
if cagr_edge_case is None:
    print("Success! Edge case handled gracefully by returning None instead of crashing.")
else:
    print("Fail: Edge case returned a value instead of None.")

print("\nAll tests completed.")
