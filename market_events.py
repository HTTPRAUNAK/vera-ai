"""
Market events composers:
- competitor_opening
- competitor_promo
- nearby_event
- festival_upcoming
- ipl_match
- payday_weekend
- rainy_day
"""

def compose_competitor_opening(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    competitor = payload.get("competitor_name", "A new competitor")
    distance = payload.get("distance", "250m")
    hero_item = payload.get("hero_item") or (merchant.get("offers", {}).get("signature_items") or ["Signature Combo"])[0]
    deal = payload.get("counter_deal", f"Special {hero_item} at ₹249 with free beverage")

    return (
        f"Hi {name}, {competitor} just opened {distance} from your outlet. "
        f"Retain your loyal regulars by featuring your {deal} on the magicpin homepage. "
        f"Reply YES to protect your local turf."
    )

def compose_competitor_promo(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    competitor = payload.get("competitor_name", "Nearby rival")
    comp_discount = payload.get("discount", "30% off")
    combo_name = payload.get("combo_name", "Premium Value Combo")
    combo_price = payload.get("combo_price", "₹349")

    return (
        f"Hi {name}, {competitor} is running an aggressive {comp_discount} campaign. "
        f"Instead of a price war, counter with your high-margin '{combo_name}' at {combo_price}. "
        f"Reply YES to launch this counter-promotion."
    )

def compose_nearby_event(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    event_name = payload.get("event_name", "a major college fest")
    venue = payload.get("venue", "nearby ground")
    expected_footfall = payload.get("expected_footfall", "5,000+ people")
    event_combo = payload.get("combo", "Grab & Go Snack Box at ₹149")

    return (
        f"Hi {name}, {event_name} is happening at {venue} drawing {expected_footfall}. "
        f"Capture event attendees with your '{event_combo}' promoted within a 2km radius. "
        f"Reply YES to target event visitors."
    )

def compose_festival_upcoming(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    festival = payload.get("festival_name", "the upcoming festival")
    days_until = int(payload.get("days_until", 3))
    offer = payload.get("festival_offer", "Festive Family Feast Box at ₹699")

    # Edge-case fix: If festival is far in the future (>30 days), don't say 'coming up in 2 days'
    if days_until > 30:
        return (
            f"Hi {name}, advance bookings for {festival} in {days_until} days are beginning. "
            f"Set up your early-bird menu now to lock in high-ticket catering and bulk orders. "
            f"Reply YES to open early festive bookings."
        )
    else:
        return (
            f"Hi {name}, {festival} is just {days_until} days away! "
            f"Launch your '{offer}' to capture the festive rush before slots fill up. "
            f"Reply YES to go live with the festive catalog."
        )

def compose_ipl_match(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    teams = payload.get("teams", "CSK vs RCB")
    match_time = payload.get("match_time", "7:30 PM")
    venue = payload.get("venue", "local stadium")
    match_combo = payload.get("match_combo", "Stadium Match Combo (Snacks + Drinks) at ₹299")

    return (
        f"Hi {name}, tonight's big match {teams} starts at {match_time} at {venue}. "
        f"Food delivery orders spike 60% during the second innings—feature your '{match_combo}' on the match day banner. "
        f"Reply YES to activate match hours."
    )

def compose_payday_weekend(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    weekend_dates = payload.get("dates", "this weekend")
    premium_pkg = payload.get("package", "Luxury Chef Tasting Menu at ₹999")

    return (
        f"Hi {name}, it is Payday Weekend ({weekend_dates}) and average dining spend is up 40%. "
        f"Showcase your premium '{premium_pkg}' to maximize average order value. "
        f"Reply YES to feature your premium menu."
    )

def compose_rainy_day(trigger: dict, merchant: dict, category: dict) -> str:
    name = merchant.get("name", "Partner")
    payload = trigger.get("payload", {})
    city_area = payload.get("area", "your neighborhood")
    rain_special = payload.get("special", "Hot Chai & Crispy Pakora Platter at ₹149")

    return (
        f"Hi {name}, heavy rain in {city_area} has triggered a surge in comfort food delivery searches. "
        f"Promote your '{rain_special}' on the homepage for fast delivery. "
        f"Reply YES to turn on the rainy day surge."
    )
