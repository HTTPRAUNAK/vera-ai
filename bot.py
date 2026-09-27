"""
bot.py - Flask server implementing all 5 endpoints for magicpin AI Challenge.
- GET  /v1/healthz
- GET  /v1/metadata
- POST /v1/context
- POST /v1/tick
- POST /v1/reply
"""
import os
from flask import Flask, request, jsonify, render_template
from context_store import context_store
from composers import compose_message, COMPOSER_REGISTRY
from reply_engine import reply_engine
from judge_simulator import JudgeSimulator

app = Flask(__name__, template_folder="templates")
judge = JudgeSimulator()

@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html")

@app.route("/v1/judge/evaluate", methods=["GET", "POST"])
def evaluate_rubric():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        kind = data.get("kind", "performance_dip")
        try:
            return jsonify(judge.evaluate_trigger(kind)), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        return jsonify(judge.evaluate_all_triggers()), 200

@app.route("/v1/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route("/v1/metadata", methods=["GET"])
def metadata():
    return jsonify({
        "bot_name": "vera-bot",
        "team": "MFAPIs",
        "version": "1.0.0",
        "description": "Deterministic proactive WhatsApp merchant assistant for magicpin AI Challenge",
        "rubric_alignment": {
            "specificity": "Uses exact prices, items, distances, dates, and metrics",
            "category_fit": "Domain vocabulary and allowed offers per business type",
            "merchant_fit": "Tied directly to merchant identity, owner, and review themes",
            "trigger_relevance": "Direct response to trigger events without generic filler",
            "engagement_compulsion": "Single prominent actionable CTA per message"
        },
        "supported_trigger_kinds": 25,
        "deterministic": True
    }), 200

@app.route("/v1/context", methods=["POST"])
def post_context():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    success, message, code = context_store.save_context(data)
    if not success:
        return jsonify({"error": message}), code

    merchant_id = data.get("merchant_id") or data.get("merchant", {}).get("merchant_id") or "default_merchant"
    return jsonify({
        "status": "ok",
        "message": message,
        "version": context_store.get_version(merchant_id)
    }), 200

@app.route("/v1/tick", methods=["POST"])
def post_tick():
    data = request.get_json(force=True, silent=True) or {}
    merchant_id = data.get("merchant_id") or "default_merchant"
    triggers = data.get("triggers", [])

    context = context_store.get_context(merchant_id) or {}
    if not triggers:
        triggers = context.get("triggers", [])

    actions = []
    for trigger in triggers:
        trigger_id = trigger.get("id") or trigger.get("trigger_id") or "trg_01"
        message = compose_message(trigger, context)
        actions.append({
            "type": "send",
            "trigger_id": trigger_id,
            "merchant_id": merchant_id,
            "message": message
        })

    return jsonify({"actions": actions}), 200

@app.route("/v1/reply", methods=["POST"])
def post_reply():
    data = request.get_json(force=True, silent=True) or {}
    merchant_id = data.get("merchant_id") or "default_merchant"
    inbound_message = data.get("message", "")
    history = data.get("history")

    if history is None:
        history = context_store.get_history(merchant_id)

    context = context_store.get_context(merchant_id) or {}
    merchant_name = context.get("merchant", {}).get("name", "Partner")

    # Record message in history
    context_store.add_history(merchant_id, "merchant", inbound_message)

    decision = reply_engine.process_reply(
        merchant_id=merchant_id,
        message=inbound_message,
        history=history,
        merchant_name=merchant_name
    )

    if decision.get("message"):
        context_store.add_history(merchant_id, "bot", decision["message"])

    return jsonify(decision), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    app.run(host=host, port=port, debug=False)
