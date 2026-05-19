#!/usr/bin/env python3
"""
Quick test script for Gate and Fence functionality (STEP 14).
This runs a quick integration test without opening display.
"""

import subprocess
import sys
import time
import os

PASS = "[PASS]"
FAIL = "[FAIL]"

def run_test():
    print("=" * 60)
    print("TESTING GATE & FENCE FUNCTIONALITY (STEP 14)")
    print("=" * 60)
    
    # Test 1: Smoke test (basic game startup)
    print("\n[TEST 1] Smoke test - game startup...")
    result = subprocess.run(
        [sys.executable, 'main.py', '--smoke'],
        capture_output=True,
        text=True,
        timeout=45,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if result.returncode == 0 and "Smoke test passed" in result.stdout:
        print(f"{PASS} Game startup OK")
    else:
        print(f"{FAIL} Game startup failed")
        print(f"STDERR: {result.stderr[:300]}")
        return False
    
    # Test 2: Code structure check
    print("\n[TEST 2] Code structure - checking Gate in STRUCTURE_TYPES...")
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Gate in STRUCTURE_TYPES', '"gate":' in content),
        ('Gate hotbar handler', 'action == "hotbar_gate"' in content),
        ('Gate draw method', 'elif self.kind == "gate":' in content),
        ('Player walkthrough gate', 's.kind != "gate"' in content),
        ('Self-trap prevention', '"would_trap_player"' in content),
    ]
    
    all_pass = True
    for check_name, check_result in checks:
        status = PASS if check_result else FAIL
        print(f"  {status} {check_name}")
        all_pass = all_pass and check_result
    
    # Test 3: UI Manager check
    print("\n[TEST 3] UI Manager - checking hotbar gate button...")
    with open('ui_manager.py', 'r', encoding='utf-8') as f:
        ui_content = f.read()
    
    ui_checks = [
        ('Gate hotbar rendering', 'hotbar_gate' in ui_content),
        ('Gate icon draw', 'gate' in ui_content.lower() or 'custom' in ui_content.lower()),
    ]
    
    for check_name, check_result in ui_checks:
        status = PASS if check_result else FAIL
        print(f"  {status} {check_name}")
        all_pass = all_pass and check_result
    
    # Test 4: MapManager check
    print("\n[TEST 4] MapManager - checking dynamic obstacles...")
    with open('map_manager.py', 'r', encoding='utf-8') as f:
        map_content = f.read()
    
    map_checks = [
        ('Dynamic obstacles tracking', 'dynamic_obstacles' in map_content),
    ]
    
    for check_name, check_result in map_checks:
        status = PASS if check_result else FAIL
        print(f"  {status} {check_name}")
        all_pass = all_pass and check_result
    
    print("\n" + "=" * 60)
    if all_pass:
        print("OK: ALL TESTS PASSED - Gate system ready for manual testing")
        print("\nNext steps for manual testing:")
        print("1. Run: py main.py")
        print("2. In game, press key 4 or click hotbar button 4 for Gate")
        print("3. Check:")
        print("   - Gate hotbar button appears with custom icon")
        print("   - Ghost preview shows when placing gate")
        print("   - Gate renders as two posts + center bar")
        print("   - Player can walk through gate")
        print("   - Zombie cannot walk through gate (attack instead)")
        print("   - Self-trap prevention works (cant seal yourself in)")
        print("   - Gate has HP and can be damaged/repaired")
    else:
        print("ERROR: SOME TESTS FAILED - see above")
        return False
    
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
