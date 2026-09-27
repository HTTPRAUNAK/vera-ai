"""
Performance composers:
- performance_dip
- table_booking_dip
- high_cart_abandonment
- organic_traffic_spike
"""

def compose_performance_dip(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    dip_pct = payload.get("dip_percentage", "18%")
    timeframe = payload.get("timeframe", "this week")
    item = payload.get("hero_item") or (merchant.get("offers", {}).get("signature_items") or ["Special Thali"])[0]
    price = payload.get("promo_price", "₹199")

    return (
        f"Hi {name}, we noticed orders dipped {dip_pct} {timeframe}. "
        f"To quickly recover volume, spotlight your {item} at {price} with high visibility on magicpin today. "
        f"Reply YES to launch this flash promo."
    )

def compose_table_booking_dip(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    slot = payload.get("slot", "tonight's dinner shift")
    booked = payload.get("booked_tables", "2")
    total = payload.get("total_tables", "15")
    perk = payload.get("perk", "Complimentary Dessert on orders above ₹800")

    return (
        f"Hi {name}, table reservations for {slot} are low ({booked}/{total} booked). "
        f"Offer a '{perk}' to nearby diners to fill the remaining tables. "
        f"Reply YES to activate table rush mode."
    )

def compose_high_cart_abandonment(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    abandoned_count = payload.get("abandoned_count", "42 customers")
    time_window = payload.get("time_window", "the last 24 hours")
    recovery_deal = payload.get("recovery_deal", "Flat ₹75 off on orders above ₹399")

    return (
        f"Hi {name}, {abandoned_count} left items in their cart during {time_window}. "
        f"Sending a push with '{recovery_deal}' can convert up to 35% of these pending orders. "
        f"Reply YES to send the recovery nudge."
    )

def compose_organic_traffic_spike(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    spike_pct = payload.get("spike_percentage", "45%")
    views = payload.get("profile_views", "1,200")
    deal = payload.get("flash_deal", "Buy 1 Get 1 on beverages")

    return (
        f"Hi {name}, your magicpin page views surged {spike_pct} today ({views} views), but menu conversions are lagging. "
        f"Activate a '{deal}' flash deal to turn browsing footfall into paying customers. "
        f"Reply YES to turn on the flash banner."
    )
