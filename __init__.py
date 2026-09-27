"""
Composer registry dispatch table.
Maps all 25 seed trigger kinds to dedicated composers.
"""
from composers.performance import (
    compose_performance_dip,
    compose_table_booking_dip,
    compose_high_cart_abandonment,
    compose_organic_traffic_spike,
)
from composers.market_events import (
    compose_competitor_opening,
    compose_competitor_promo,
    compose_nearby_event,
    compose_festival_upcoming,
    compose_ipl_match,
    compose_payday_weekend,
    compose_rainy_day,
)
from composers.operational import (
    compose_inventory_expiry,
    compose_batch_recall,
    compose_subscription_renewal,
    compose_happy_hour,
    compose_weekend_rush,
    compose_seasonal_menu_switch,
)
from composers.reviews_loyalty import (
    compose_review_negative,
    compose_review_positive,
    compose_loyalty_tier_upgrade,
    compose_new_dish_launch,
    compose_cashback_campaign,
    compose_voucher_drop,
)
from composers.customer_facing import (
    compose_customer_recall,
    compose_appointment_reminder,
)
from composers.fallback import compose_grounded_fallback

COMPOSER_REGISTRY = {
    # 1-4 Performance
    "performance_dip": compose_performance_dip,
    "table_booking_dip": compose_table_booking_dip,
    "high_cart_abandonment": compose_high_cart_abandonment,
    "organic_traffic_spike": compose_organic_traffic_spike,

    # 5-11 Market Events
    "competitor_opening": compose_competitor_opening,
    "competitor_promo": compose_competitor_promo,
    "nearby_event": compose_nearby_event,
    "festival_upcoming": compose_festival_upcoming,
    "ipl_match": compose_ipl_match,
    "payday_weekend": compose_payday_weekend,
    "rainy_day": compose_rainy_day,

    # 12-17 Operational
    "inventory_expiry": compose_inventory_expiry,
    "batch_recall": compose_batch_recall,
    "subscription_renewal": compose_subscription_renewal,
    "happy_hour": compose_happy_hour,
    "weekend_rush": compose_weekend_rush,
    "seasonal_menu_switch": compose_seasonal_menu_switch,

    # 18-23 Reviews & Loyalty
    "review_negative": compose_review_negative,
    "review_positive": compose_review_positive,
    "loyalty_tier_upgrade": compose_loyalty_tier_upgrade,
    "new_dish_launch": compose_new_dish_launch,
    "cashback_campaign": compose_cashback_campaign,
    "voucher_drop": compose_voucher_drop,

    # 24-25 Customer Facing
    "customer_recall": compose_customer_recall,
    "appointment_reminder": compose_appointment_reminder,
}

def compose_message(trigger: dict, context: dict) -> str:
    kind = trigger.get("kind", "")
    merchant = context.get("merchant", {})
    category = context.get("category", {})
    customer = context.get("customer", {})

    if kind in ["customer_recall", "appointment_reminder"]:
        composer_fn = COMPOSER_REGISTRY.get(kind)
        return composer_fn(trigger, merchant, customer)
    elif kind in COMPOSER_REGISTRY:
        composer_fn = COMPOSER_REGISTRY.get(kind)
        return composer_fn(trigger, merchant, category)
    else:
        return compose_grounded_fallback(trigger, merchant, category)
