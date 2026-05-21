import asyncio
import os
import sys

# Inject src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from mcp_mistake_guard.server import query_notes, match_error_trace

async def main():
    print("🔍 [TEST 1] Query Notes with keyword 'SMC'...")
    res1 = query_notes(["SMC"])
    print(f"Result:\n{res1}\n")

    print("🔍 [TEST 2] Match Error Trace for SMC Timeout...")
    test_trace = "Critical failure: SMC timeout occurred during communication loop"
    res2 = match_error_trace(test_trace, target_model="claude-3.5-sonnet")
    print(f"Result:\n{res2}\n")

if __name__ == "__main__":
    asyncio.run(main())
