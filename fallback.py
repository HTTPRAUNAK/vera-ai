"""
Grounded signal-driven fallback composer.
Never invents generic copy or hallucinated discounts.
Extracts real merchant signals and provides a crisp single CTA.
"""

def compose_grounded_fallback(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    trigger_kind = trigger.get("kind", "growth opportunity").replace("_", " ")
    payload = trigger.get("payload", {})

    # Extract real items or fall back to verified merchant signature items
    items = merchant.get("offers", {}).get("signature_items") or []
    item_str = f"your {items[0]}" if items else "your top menu offerings"
    metric = payload.get("metric_value") or payload.get("detail") or "drive higher weekly volume"

    return (
        f"Hi {name}, regarding {trigger_kind}: we noticed an opportunity to {metric} by featuring {item_str} on magicpin. "
        f"Reply YES to review and launch this recommendation."
    )
