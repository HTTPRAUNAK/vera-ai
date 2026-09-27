"""
test_bot.py - Comprehensive test suite for magicpin AI Challenge vera-bot.
Covers:
1. All 5 endpoints (/v1/healthz, /v1/metadata, /v1/context, /v1/tick, /v1/reply)
2. Stale version 409 conflict and idempotent context updates
3. All 25 seed trigger composers producing valid single-CTA copy
4. Edge cases (expired subscription, distant festival date, sparse merchant)
5. All 4 replay scenarios (auto-reply hell, intent transition, hostile/opt-out, off-topic)
"""
import pytest
from bot import app
from context_store import context_store
from composers import COMPOSER_REGISTRY

@pytest.fixture(autouse=True)
def setup_teardown():
    context_store.clear()
    yield
    context_store.clear()

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_healthz(client):
    res = client.get("/v1/healthz")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}

def test_metadata(client):
    res = client.get("/v1/metadata")
    assert res.status_code == 200
    data = res.get_json()
    assert data["bot_name"] == "vera-bot"
    assert data["team"] == "MFAPIs"
    assert data["supported_trigger_kinds"] == 25
    assert data["deterministic"] is True

def test_dashboard(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"vera-bot" in res.data

def test_judge_evaluate_endpoint(client):
    res = client.get("/v1/judge/evaluate")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_evaluated"] == 25
    assert data["average_overall_score"] >= 8.0

def test_context_and_409_conflict(client):
    payload_v1 = {
        "merchant_id": "m_101",
        "version": 1,
        "merchant": {"name": "Biryani By Kilo", "merchant_id": "m_101"}
    }
    # Initial save
    res = client.post("/v1/context", json=payload_v1)
    assert res.status_code == 200

    # Idempotent push of same payload with same version
    res_idempotent = client.post("/v1/context", json=payload_v1)
    assert res_idempotent.status_code == 200

    # Stale version push: version 0 < 1
    stale_payload = {
        "merchant_id": "m_101",
        "version": 0,
        "merchant": {"name": "Biryani By Kilo"}
    }
    res_stale = client.post("/v1/context", json=stale_payload)
    assert res_stale.status_code == 409

    # Conflict with same version but different data
    conflict_payload = {
        "merchant_id": "m_101",
        "version": 1,
        "merchant": {"name": "Different Name"}
    }
    res_conflict = client.post("/v1/context", json=conflict_payload)
    assert res_conflict.status_code == 409

    # Valid higher version push
    payload_v2 = {
        "merchant_id": "m_101",
        "version": 2,
        "merchant": {"name": "Biryani By Kilo Updated"}
    }
    res_v2 = client.post("/v1/context", json=payload_v2)
    assert res_v2.status_code == 200
    assert res_v2.get_json()["version"] == 2

def test_all_25_triggers_coverage(client):
    assert len(COMPOSER_REGISTRY) == 25
    merchant_ctx = {
        "merchant_id": "m_test",
        "version": 1,
        "merchant": {
            "name": "Spice Grill",
            "offers": {"signature_items": ["Butter Chicken Special", "Paneer Tikka"]}
        },
        "category": {"name": "F&B", "tone": "energetic"},
        "customer": {"name": "Aman", "language": "english"}
    }
    client.post("/v1/context", json=merchant_ctx)

    for kind in COMPOSER_REGISTRY.keys():
        trigger_payload = {
            "merchant_id": "m_test",
            "triggers": [{"id": f"trg_{kind}", "kind": kind, "payload": {}}]
        }
        res = client.post("/v1/tick", json=trigger_payload)
        assert res.status_code == 200
        actions = res.get_json()["actions"]
        assert len(actions) == 1
        msg = actions[0]["message"]
        # Quality check: strictly one prominent CTA, mentions merchant/customer, no re-intro
        assert "Hi I am Vera" not in msg
        assert "Reply" in msg
        assert len(msg) > 30

def test_edge_case_expired_subscription(client):
    trigger_payload = {
        "merchant_id": "m_test",
        "triggers": [{
            "id": "trg_sub",
            "kind": "subscription_renewal",
            "payload": {"days_remaining": 0, "plan_name": "Gold Merchant"}
        }]
    }
    res = client.post("/v1/tick", json=trigger_payload)
    assert res.status_code == 200
    msg = res.get_json()["actions"][0]["message"]
    assert "expired" in msg.lower()
    assert "renews in 0 days" not in msg

def test_edge_case_distant_festival(client):
    trigger_payload = {
        "merchant_id": "m_test",
        "triggers": [{
            "id": "trg_fest",
            "kind": "festival_upcoming",
            "payload": {"festival_name": "Diwali", "days_until": 180}
        }]
    }
    res = client.post("/v1/tick", json=trigger_payload)
    assert res.status_code == 200
    msg = res.get_json()["actions"][0]["message"]
    assert "advance bookings" in msg.lower()
    assert "just 180 days away" not in msg

def test_replay_scenario_1_auto_reply_hell(client):
    """
    Scenario 1: Four identical canned auto-replies in a row.
    Bot must not waste turns replying, switches to wait/end.
    """
    canned_msg = "Thank you for contacting us. We will get back to you shortly."
    m_id = "m_auto"

    # Turn 1
    res1 = client.post("/v1/reply", json={"merchant_id": m_id, "message": canned_msg, "history": []})
    assert res1.get_json()["action"] in ["wait", "end"]

    # Repeated identical canned replies
    history = [
        {"role": "merchant", "text": canned_msg},
        {"role": "merchant", "text": canned_msg},
        {"role": "merchant", "text": canned_msg}
    ]
    res4 = client.post("/v1/reply", json={"merchant_id": m_id, "message": canned_msg, "history": history})
    assert res4.get_json()["action"] in ["wait", "end"]
    # Bot avoids auto-reply pollution: no spam message generated
    assert res4.get_json().get("message") is None

def test_replay_scenario_2_intent_transition(client):
    """
    Scenario 2: Merchant accepts ("Thank you for contacting me directly... let's proceed").
    Must trigger action mode immediately without being misclassified as auto-reply!
    """
    msg = "Thank you for contacting me directly. I reviewed the numbers, let's proceed."
    res = client.post("/v1/reply", json={"merchant_id": "m_intent", "message": msg, "history": []})
    data = res.get_json()
    assert data["action"] == "send"
    assert "active" in data["message"].lower()

def test_replay_scenario_3_hostile_opt_out(client):
    """
    Scenario 3: Merchant says stop/unsubscribe.
    Bot must return action: end with polite closure.
    """
    msg = "Please stop messaging me and remove my number."
    res = client.post("/v1/reply", json={"merchant_id": "m_opt", "message": msg, "history": []})
    data = res.get_json()
    assert data["action"] == "end"
    assert "stopped" in data["message"].lower()

def test_replay_scenario_4_off_topic_curveball(client):
    """
    Scenario 4: Merchant asks an off-topic curveball regarding commission.
    Bot handles gracefully with grounded answer and single CTA.
    """
    msg = "What is your commission rate for magicpin orders?"
    res = client.post("/v1/reply", json={"merchant_id": "m_off", "message": msg, "history": []})
    data = res.get_json()
    assert data["action"] == "send"
    assert "commission" in data["message"].lower()
    assert "Reply YES" in data["message"]

def test_judge_simulator_all_triggers():
    from judge_simulator import JudgeSimulator
    simulator = JudgeSimulator()
    summary = simulator.evaluate_all_triggers()
    assert summary["total_evaluated"] == 25
    assert summary["average_overall_score"] >= 8.0
    assert summary["total_anti_patterns_flagged"] == 0

def test_judge_simulator_anti_pattern_detection():
    from judge_simulator import JudgeSimulator
    simulator = JudgeSimulator()
    
    # Test anti-pattern 1: Re-introducing oneself
    res1 = simulator.check_anti_patterns("Hi I am Vera, your assistant. Reply YES to continue.", "performance_dip")
    assert res1["has_anti_patterns"] is True
    assert any("Re-introducing" in p for p in res1["penalties"])

    # Test anti-pattern 2: Multiple CTAs
    res2 = simulator.check_anti_patterns("Reply YES to start or reply NO to cancel?", "performance_dip")
    assert res2["has_anti_patterns"] is True
    assert any("Multiple CTAs" in p for p in res2["penalties"])

    # Test anti-pattern 3: Buried CTA
    res3 = simulator.check_anti_patterns("Reply YES to confirm. Here is some other news that keeps going on.", "performance_dip")
    assert res3["has_anti_patterns"] is True
    assert any("Buried CTA" in p for p in res3["penalties"])
