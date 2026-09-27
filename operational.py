"""
Operational composers:
- inventory_expiry
- batch_recall
- subscription_renewal
- happy_hour
- weekend_rush
- seasonal_menu_switch
"""

def compose_inventory_expiry(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    item = payload.get("item_name", "perishable ingredients")
    units = payload.get("units_remaining", "25 units")
    days_left = payload.get("days_to_expiry", "2 days")
    clearance_price = payload.get("clearance_price", "₹120")

    return (
        f"Hi {name}, you have {units} of {item} expiring in {days_left}. "
        f"Run a flash clearance special at {clearance_price} to liquidate inventory and prevent dead-stock loss. "
        f"Reply YES to start the flash clearance."
    )

def compose_batch_recall(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    batch_no = payload.get("batch_number", "BATCH-8921")
    product = payload.get("product_name", "Dairy Creamer 1L")
    supplier = payload.get("supplier", "Apex Distro")

    return (
        f"URGENT for {name}: Supplier {supplier} issued a quality recall for {product} under {batch_no}. "
        f"Please quarantine all units of this batch from your shelves immediately. "
        f"Reply YES to confirm {batch_no} is isolated."
    )

def compose_subscription_renewal(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    days_remaining = int(payload.get("days_remaining", 0))
    plan_name = payload.get("plan_name", "magicpin Gold Merchant")
    renewal_fee = payload.get("renewal_fee", "₹1,999/yr")

    # Edge-case fix: If days_remaining <= 0, gracefully handle expired state, never 'renews in 0 days'!
    if days_remaining <= 0:
        return (
            f"Hi {name}, your {plan_name} membership expired. "
            f"Renew now for {renewal_fee} to immediately restore your top listing badge and priority customer support. "
            f"Reply YES to renew your membership now."
        )
    else:
        return (
            f"Hi {name}, your {plan_name} membership renews in {days_remaining} days. "
            f"Lock in your early renewal at {renewal_fee} and receive 500 bonus promotional credits. "
            f"Reply YES to confirm your renewal."
        )

def compose_happy_hour(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    hours = payload.get("hours", "2:00 PM – 5:00 PM")
    deal = payload.get("deal", "Flat 50% off on second beverage")

    return (
        f"Hi {name}, footfall drops significantly during weekday afternoons ({hours}). "
        f"Activate a '{deal}' offer to attract remote workers and college students during slow hours. "
        f"Reply YES to turn on weekday Happy Hours."
    )

def compose_weekend_rush(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    projected_orders = payload.get("projected_orders", "180+ orders")
    rush_combo = payload.get("rush_combo", "Weekend Family Feast Box at ₹499")

    return (
        f"Hi {name}, weekend orders are projected to surge ({projected_orders} expected). "
        f"Pre-batch your inventory and highlight your '{rush_combo}' to expedite kitchen prep and maximize turnover. "
        f"Reply YES to queue this weekend special."
    )

def compose_seasonal_menu_switch(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    season = payload.get("season", "Summer")
    special_item = payload.get("special_item", "Cold Brew Mango Mojito at ₹189")

    return (
        f"Hi {name}, as {season} approaches, demand for seasonal refreshments is up 50%. "
        f"Feature your new '{special_item}' on the top banner to kickstart seasonal sales. "
        f"Reply YES to showcase your seasonal special."
    )
