import asyncio
import os
import sys

# Inject src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from odab_note.server import query_notes, match_error_trace

async def main():
    print("🔍 [TEST 1] Query Notes with keyword 'SMC'...")
    res1 = query_notes(["SMC"])
    print(f"Result:\n{res1}\n")

    print("🔍 [TEST 2] Match Error Trace for SMC Timeout...")
    test_trace = "Critical failure: SMC timeout occurred during communication loop"
    res2 = match_error_trace(test_trace, target_model="claude-3.5-sonnet")
    print(f"Result:\n{res2}\n")

    print("🔍 [TEST 3] Match ZeroDivisionError Trace...")
    zero_trace = """
Traceback (most recent call last):
  File "buggy_script.py", line 6, in <module>
    print(calculate_ratio(10, 0))
ZeroDivisionError: division by zero
"""
    res3 = match_error_trace(zero_trace, target_model="all")
    print(f"Result:\n{res3}\n")

if __name__ == "__main__":
    asyncio.run(main())
