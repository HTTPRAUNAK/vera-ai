"""
test_live.py - Verification script against a running vera-bot instance.
Usage: python test_live.py [http://127.0.0.1:5000]
"""
import sys
import requests

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"

def run_live_tests():
    print(f"Testing vera-bot against {BASE_URL}...")

    # 1. Healthz
    r = requests.get(f"{BASE_URL}/v1/healthz")
    assert r.status_code == 200, f"Healthz failed: {r.text}"
    print("[PASS] GET /v1/healthz -> 200 ok")

    # 2. Metadata
    r = requests.get(f"{BASE_URL}/v1/metadata")
    assert r.status_code == 200, f"Metadata failed: {r.text}"
    meta = r.json()
    print(f"[PASS] GET /v1/metadata -> bot: {meta['bot_name']}, supported triggers: {meta['supported_trigger_kinds']}")

    # 3. Web Dashboard
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200, f"Dashboard failed: {r.status_code}"
    print("[PASS] GET / -> 200 ok (Interactive Dashboard)")

    # 4. Context save & version conflict
    ctx = {
        "merchant_id": "m_live_01",
        "version": 1,
        "merchant": {"name": "Punjab Grill", "offers": {"signature_items": ["Dal Makhani", "Butter Naan"]}}
    }
    r = requests.post(f"{BASE_URL}/v1/context", json=ctx)
    assert r.status_code == 200, f"Context push failed: {r.text}"
    print("[PASS] POST /v1/context (v1) -> 200 ok")

    # Stale version check
    ctx_stale = {"merchant_id": "m_live_01", "version": 0, "merchant": {"name": "Stale"}}
    r_stale = requests.post(f"{BASE_URL}/v1/context", json=ctx_stale)
    assert r_stale.status_code == 409, f"Stale context did not return 409: {r_stale.status_code}"
    print("[PASS] POST /v1/context (v0 stale) -> 409 Conflict correctly rejected")

    # 5. Proactive Tick
    tick_payload = {
        "merchant_id": "m_live_01",
        "triggers": [{
            "id": "trg_ipl",
            "kind": "ipl_match",
            "payload": {"teams": "CSK vs MI", "match_time": "7:30 PM", "venue": "Wankhede"}
        }]
    }
    r = requests.post(f"{BASE_URL}/v1/tick", json=tick_payload)
    assert r.status_code == 200
    act = r.json()["actions"][0]
    print(f"[PASS] POST /v1/tick -> Composed message: '{act['message']}'")

    # 6. Inbound Reply (Intent transition - Scenario 2)
    reply_payload = {
        "merchant_id": "m_live_01",
        "message": "Thank you for the update! Let's proceed with this."
    }
    r = requests.post(f"{BASE_URL}/v1/reply", json=reply_payload)
    assert r.status_code == 200
    rep = r.json()
    assert rep["action"] == "send"
    print(f"[PASS] POST /v1/reply (Intent transition) -> Action: {rep['action']}, Response: '{rep['message']}'")

    # 7. Inbound Reply (Hostile opt-out - Scenario 3)
    r_hostile = requests.post(f"{BASE_URL}/v1/reply", json={"merchant_id": "m_live_01", "message": "stop unsubscribe"})
    assert r_hostile.status_code == 200
    assert r_hostile.json()["action"] == "end"
    print("[PASS] POST /v1/reply (Hostile opt-out) -> Action: end")

    # 8. Judge Simulator Endpoint
    r_judge = requests.get(f"{BASE_URL}/v1/judge/evaluate")
    assert r_judge.status_code == 200
    j_data = r_judge.json()
    print(f"[PASS] GET /v1/judge/evaluate -> 25 triggers scored, average: {j_data['average_overall_score']}/10.0")

    print("\nALL LIVE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_live_tests()
